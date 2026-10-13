import math
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.booking import Booking, BookingStatusHistory
from app.models.machinery import Machinery, MachineryRate, MachineryAvailability
from app.models.user import User


class BookingServiceError(Exception):
    """Base exception for booking operations."""
    pass


class BookingValidationError(BookingServiceError):
    """Raised when booking request data fails validation."""
    pass


class BookingConflictError(BookingServiceError):
    """Raised when an approval conflicts with an existing confirmed booking or blackout window."""
    pass


class BookingStateError(BookingServiceError):
    """Raised when an illegal status transition is requested."""
    pass


class BookingAuthorizationError(BookingServiceError):
    """Raised when an actor lacks permission to manage a booking."""
    pass


ALLOWED_TRANSITIONS = {
    Booking.STATUS_PENDING: {
        Booking.STATUS_APPROVED: ["PROVIDER", "ADMIN"],
        Booking.STATUS_REJECTED: ["PROVIDER", "ADMIN"],
        Booking.STATUS_CANCELLED: ["FARMER", "ADMIN"],
    },
    Booking.STATUS_APPROVED: {
        Booking.STATUS_IN_PROGRESS: ["PROVIDER", "ADMIN"],
        Booking.STATUS_CANCELLED: ["FARMER", "PROVIDER", "ADMIN"],
    },
    Booking.STATUS_IN_PROGRESS: {
        Booking.STATUS_COMPLETED: ["PROVIDER", "ADMIN"],
    },
    Booking.STATUS_COMPLETED: {},
    Booking.STATUS_CANCELLED: {},
    Booking.STATUS_REJECTED: {},
}


def generate_booking_reference() -> str:
    """Generate a unique human-friendly booking reference (e.g. FC-BK-20261014-A1B2C3)."""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_str = uuid.uuid4().hex[:6].upper()
    return f"FC-BK-{date_str}-{random_str}"


def calculate_pricing(
    machinery: Machinery,
    package_type: str,
    start_time: datetime,
    end_time: datetime,
) -> dict:
    """Calculate estimated rental pricing for machinery package option.
    
    Billing Rules:
    1. Billable duration is calculated in hours rounded up to the nearest whole hour:
       billable_hours = ceil((end_time - start_time).total_seconds() / 3600).
    2. Minimum booking duration (min_booking_duration_hours) is enforced:
       effective_hours = max(billable_hours, min_booking_duration_hours).
    3. Multi-day rentals (>= 24 hours):
       - If daily rate exists:
         full_days = effective_hours // 24
         remaining_hours = effective_hours % 24
         day_portion = full_days * rate_per_day
         extra_hour_portion = remaining_hours * rate_per_hour (capped at rate_per_day).
         If hourly rate is not configured, remaining hours are billed as a full day.
       - If only hourly rate exists:
         total = effective_hours * rate_per_hour.
    4. Sub-24-hour rentals (< 24 hours):
       - If hourly rate exists, billed as effective_hours * rate_per_hour.
       - If daily rate also exists, capped at rate_per_day for best-price protection.
       - If only daily rate exists, billed at rate_per_day.
    5. Security deposit is reported separately as an advisory offline deposit amount.
       Hourly and daily rates are never double-charged for the same duration.
    """
    if not start_time or not end_time:
        raise BookingValidationError("Start time and end time are required.")

    if end_time <= start_time:
        raise BookingValidationError("Rental end time must be strictly after start time.")

    rate = next((r for r in machinery.rates if r.rental_option_type == package_type), None)
    if not rate:
        raise BookingValidationError(
            f"Rental package '{package_type}' is not configured for this machinery listing."
        )

    has_hr = rate.rate_per_hour is not None and rate.rate_per_hour > 0
    has_day = rate.rate_per_day is not None and rate.rate_per_day > 0

    if not has_hr and not has_day:
        raise BookingValidationError(
            f"No valid pricing rates are configured for package '{package_type}'."
        )

    total_seconds = (end_time - start_time).total_seconds()
    actual_hours = max(1, math.ceil(total_seconds / 3600.0))
    min_hours = max(1, rate.min_booking_duration_hours or 1)
    billable_hours = max(actual_hours, min_hours)

    rate_hr = Decimal(str(rate.rate_per_hour)) if has_hr else None
    rate_day = Decimal(str(rate.rate_per_day)) if has_day else None
    deposit = Decimal(str(rate.security_deposit or "0.00"))

    full_days = 0
    remaining_hours = 0
    hourly_cost = Decimal("0.00")
    daily_cost = Decimal("0.00")
    total_cost = Decimal("0.00")

    if has_day and billable_hours >= 24:
        full_days = billable_hours // 24
        remaining_hours = billable_hours % 24
        daily_cost = Decimal(str(full_days)) * rate_day

        if remaining_hours > 0:
            if has_hr:
                hour_portion = Decimal(str(remaining_hours)) * rate_hr
                # Best price cap: extra hours shouldn't exceed 1 more day
                if hour_portion > rate_day:
                    hour_portion = rate_day
                hourly_cost = hour_portion
            else:
                # No hourly rate: extra hours round up to a full day
                hourly_cost = rate_day
        total_cost = daily_cost + hourly_cost
    else:
        # Less than 24 hours (or day rate not configured)
        if has_hr:
            raw_hour_cost = Decimal(str(billable_hours)) * rate_hr
            if has_day and raw_hour_cost > rate_day:
                # Cap single day at day rate
                daily_cost = rate_day
                hourly_cost = Decimal("0.00")
                total_cost = rate_day
            else:
                hourly_cost = raw_hour_cost
                total_cost = raw_hour_cost
        else:
            # Only daily rate configured
            daily_cost = rate_day
            total_cost = rate_day

    # Quantize to 2 decimal places
    total_cost = total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "package_type": package_type,
        "actual_hours": actual_hours,
        "billable_hours": billable_hours,
        "min_duration_hours": min_hours,
        "full_days": full_days,
        "remaining_hours": remaining_hours,
        "rate_per_hour": float(rate_hr) if rate_hr else None,
        "rate_per_day": float(rate_day) if rate_day else None,
        "security_deposit": float(deposit),
        "daily_cost": float(daily_cost),
        "hourly_cost": float(hourly_cost),
        "total_estimated_cost": float(total_cost),
    }


def check_conflicting_confirmed_bookings(
    machinery_id: uuid.UUID,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: uuid.UUID | None = None,
) -> list[Booking]:
    """Find approved or in-progress bookings that overlap [start_time, end_time).
    
    Using half-open interval semantics: [s1, e1) and [s2, e2) overlap if and only if
    s1 < e2 and e1 > s2. Adjacent intervals (e.g. e1 == s2) do not overlap.
    """
    query = Booking.query.filter(
        Booking.machinery_id == machinery_id,
        Booking.status.in_([Booking.STATUS_APPROVED, Booking.STATUS_IN_PROGRESS]),
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    )
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    return query.all()


def check_blackout_conflicts(
    machinery_id: uuid.UUID,
    start_time: datetime,
    end_time: datetime,
) -> list[MachineryAvailability]:
    """Find provider declared blackout windows that overlap [start_time, end_time)."""
    return MachineryAvailability.query.filter(
        MachineryAvailability.machinery_id == machinery_id,
        MachineryAvailability.unavailable_from < end_time,
        MachineryAvailability.unavailable_to > start_time,
    ).all()


def validate_booking_request(
    machinery: Machinery,
    package_type: str,
    start_time: datetime,
    end_time: datetime,
    check_future: bool = True,
) -> dict:
    """Validate all booking parameters, calculate pricing, and check availability."""
    if not machinery.is_active:
        raise BookingValidationError("This machinery listing is currently inactive and not available for booking.")

    if not start_time or not end_time:
        raise BookingValidationError("Both start time and end time must be specified.")

    if end_time <= start_time:
        raise BookingValidationError("Rental end time must be strictly after start time.")

    # Grace window of 5 minutes in the past to allow for clock skew during submission
    if check_future and start_time < datetime.utcnow() - timedelta(minutes=5):
        raise BookingValidationError("Rental start time must be in the future.")

    # Minimum booking duration of at least 30 minutes
    if (end_time - start_time).total_seconds() < 1800:
        raise BookingValidationError("Rental duration must be at least 30 minutes.")

    # Blackout window check
    blackouts = check_blackout_conflicts(machinery.id, start_time, end_time)
    if blackouts:
        reasons = ", ".join(set(b.reason for b in blackouts))
        raise BookingValidationError(
            f"Machinery is unavailable during the requested time window due to: {reasons}."
        )

    # Calculate pricing
    price_info = calculate_pricing(machinery, package_type, start_time, end_time)
    return price_info


def create_booking_request(
    farmer: User,
    machinery: Machinery,
    package_type: str,
    start_time: datetime,
    end_time: datetime,
    delivery_address: str | None = None,
    notes: str | None = None,
    contact_phone: str | None = None,
) -> Booking:
    """Create a new booking request in PENDING status.
    
    Pending requests are unconfirmed advisory requests and do not lock the timeslot
    until approved by the provider.
    """
    if farmer.role not in ["FARMER", "ADMIN"]:
        raise BookingAuthorizationError("Only farmers can place machinery booking requests.")

    # Validate parameters & calculate price
    price_info = validate_booking_request(
        machinery=machinery,
        package_type=package_type,
        start_time=start_time,
        end_time=end_time,
        check_future=True,
    )

    phone_snapshot = contact_phone or farmer.phone

    # Generate unique reference
    for _ in range(5):
        ref = generate_booking_reference()
        if not Booking.query.filter_by(booking_reference=ref).first():
            break
    else:
        ref = f"FC-BK-{uuid.uuid4().hex[:12].upper()}"

    booking = Booking(
        booking_reference=ref,
        farmer_id=farmer.id,
        machinery_id=machinery.id,
        rental_option_type=package_type,
        start_time=start_time,
        end_time=end_time,
        estimated_total_cost=Decimal(str(price_info["total_estimated_cost"])),
        status=Booking.STATUS_PENDING,
        delivery_address=(delivery_address or "").strip() or None,
        contact_phone_snapshot=phone_snapshot,
        notes=(notes or "").strip() or None,
    )
    db.session.add(booking)
    db.session.flush()

    # Record initial audit entry
    history = BookingStatusHistory(
        booking_id=booking.id,
        from_status=None,
        to_status=Booking.STATUS_PENDING,
        changed_by_user_id=farmer.id,
        reason_or_comment="Initial booking request submitted by farmer",
    )
    db.session.add(history)
    db.session.commit()

    return booking


def transition_booking_status(
    booking: Booking,
    new_status: str,
    actor_user: User,
    reason: str | None = None,
) -> Booking:
    """Execute a validated lifecycle state transition on a booking with audit recording.
    
    Enforces:
    - Canonical state transitions.
    - Role authorization.
    - Rejection reasons.
    - Double-booking prevention with concurrency safety upon approval.
    """
    current_status = booking.status
    if current_status == new_status:
        return booking

    # Check valid transition
    allowed_for_state = ALLOWED_TRANSITIONS.get(current_status, {})
    if new_status not in allowed_for_state:
        raise BookingStateError(
            f"Cannot transition booking from {current_status} to {new_status}."
        )

    # Check actor role
    allowed_roles = allowed_for_state[new_status]
    if actor_user.role not in allowed_roles:
        raise BookingAuthorizationError(
            f"Role '{actor_user.role}' is not authorized to transition booking to {new_status}."
        )

    # Check ownership
    is_admin = actor_user.role == "ADMIN"
    if actor_user.role == "PROVIDER":
        provider_profile = actor_user.provider_profile
        if not provider_profile or booking.machinery.provider_id != provider_profile.id:
            raise BookingAuthorizationError(
                "You cannot modify a booking for machinery owned by another provider."
            )
    elif actor_user.role == "FARMER":
        if booking.farmer_id != actor_user.id:
            raise BookingAuthorizationError("You cannot modify another farmer's booking.")

    # Validation specific to transitions
    if new_status == Booking.STATUS_REJECTED:
        clean_reason = (reason or "").strip()
        if not clean_reason:
            raise BookingValidationError("A rejection reason is required when declining a booking.")
        reason = clean_reason

    if new_status == Booking.STATUS_CANCELLED:
        # If farmer cancels an approved booking, verify it has not already started
        if current_status == Booking.STATUS_APPROVED and actor_user.role == "FARMER":
            if booking.start_time <= datetime.utcnow():
                raise BookingValidationError(
                    "Cannot cancel an approved booking after the scheduled start time."
                )

    # Double-booking check when approving
    if new_status == Booking.STATUS_APPROVED:
        # Check blackout conflicts
        blackouts = check_blackout_conflicts(booking.machinery_id, booking.start_time, booking.end_time)
        if blackouts:
            raise BookingConflictError(
                "Cannot approve booking: Machinery has scheduled maintenance/blackout during this window."
            )

        # Concurrency safety: lock machinery row if PostgreSQL
        try:
            bind = db.session.get_bind()
            if bind.dialect.name == "postgresql":
                db.session.query(Machinery).filter_by(id=booking.machinery_id).with_for_update().first()
        except Exception:
            pass

        # Check existing confirmed overlaps
        conflicts = check_conflicting_confirmed_bookings(
            machinery_id=booking.machinery_id,
            start_time=booking.start_time,
            end_time=booking.end_time,
            exclude_booking_id=booking.id,
        )
        if conflicts:
            conflict_ref = conflicts[0].booking_reference
            raise BookingConflictError(
                f"Cannot approve: Machinery is already booked (Conflicting Reference: {conflict_ref})."
            )

    # Apply status change
    try:
        booking.status = new_status
        history = BookingStatusHistory(
            booking_id=booking.id,
            from_status=current_status,
            to_status=new_status,
            changed_by_user_id=actor_user.id,
            reason_or_comment=(reason or "").strip() or None,
        )
        db.session.add(history)
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        # In case the PostgreSQL exclusion constraint was triggered concurrently
        if "exclude_overlapping_confirmed_bookings" in str(ie):
            raise BookingConflictError(
                "Cannot approve booking: Another confirmed booking overlaps with this time slot."
            )
        raise BookingServiceError(f"Database constraint violation: {ie}")
    except Exception as e:
        db.session.rollback()
        raise BookingServiceError(f"Failed to update booking status: {e}")

    return booking
