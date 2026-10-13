from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from app.blueprints.bookings import bookings_bp
from app.extensions import db
from app.models.booking import Booking
from app.models.machinery import Machinery
from app.services.booking_service import (
    calculate_pricing,
    validate_booking_request,
    create_booking_request,
    transition_booking_status,
    BookingValidationError,
    BookingConflictError,
    BookingStateError,
    BookingAuthorizationError,
)
from app.utils.security import login_required, role_required, get_current_user


def parse_datetime_input(dt_str: str | None) -> datetime | None:
    """Safely parse HTML5 datetime-local or ISO formatted input string."""
    if not dt_str or not dt_str.strip():
        return None
    cleaned = dt_str.strip().replace(" ", "T")
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        raise ValueError(f"Invalid date/time format: '{dt_str}'. Expected YYYY-MM-DDTHH:MM.")


@bookings_bp.route("/estimate", methods=["POST"])
def estimate_price():
    """Calculate and return price breakdown JSON for selected package and dates."""
    data = request.get_json(silent=True) or request.form
    machinery_id_raw = data.get("machinery_id")
    package_type = (data.get("rental_option_type") or "").strip().upper()
    start_str = data.get("start_time")
    end_str = data.get("end_time")

    if not machinery_id_raw or not package_type or not start_str or not end_str:
        return jsonify({
            "success": False,
            "error": "All fields (machinery, package, start time, end time) are required.",
        }), 400

    try:
        machinery = db.session.get(Machinery, machinery_id_raw)
        if not machinery:
            return jsonify({"success": False, "error": "Machinery not found."}), 404

        start_dt = parse_datetime_input(start_str)
        end_dt = parse_datetime_input(end_str)

        price_info = validate_booking_request(
            machinery=machinery,
            package_type=package_type,
            start_time=start_dt,
            end_time=end_dt,
            check_future=False,  # Estimate endpoint can quote without strictly enforcing future clock
        )

        return jsonify({"success": True, "data": price_info})

    except (BookingValidationError, ValueError) as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to calculate estimate: {str(e)}"}), 500


@bookings_bp.route("/machinery/<uuid:machinery_id>", methods=["POST"])
@login_required
def submit_booking(machinery_id):
    """Submit a new machinery booking request from the machinery detail page."""
    user = get_current_user()
    if user.role not in ["FARMER", "ADMIN"]:
        flash("Machinery rentals must be booked using a Farmer account.", "warning")
        return redirect(url_for("machinery.detail", machinery_id=machinery_id))

    machinery = db.session.get(Machinery, machinery_id)
    if not machinery or not machinery.is_active:
        abort(404)

    package_type = (request.form.get("rental_option_type") or "").strip().upper()
    start_str = request.form.get("start_time")
    end_str = request.form.get("end_time")
    delivery_address = request.form.get("delivery_address")
    notes = request.form.get("notes")
    contact_phone = request.form.get("contact_phone")

    try:
        start_dt = parse_datetime_input(start_str)
        end_dt = parse_datetime_input(end_str)

        booking = create_booking_request(
            farmer=user,
            machinery=machinery,
            package_type=package_type,
            start_time=start_dt,
            end_time=end_dt,
            delivery_address=delivery_address,
            notes=notes,
            contact_phone=contact_phone,
        )

        flash(f"Booking request submitted successfully! Reference: {booking.booking_reference}", "success")
        return redirect(url_for("bookings.booking_detail", booking_id=booking.id))

    except (BookingValidationError, BookingConflictError, ValueError) as e:
        flash(str(e), "error")
        return redirect(url_for("machinery.detail", machinery_id=machinery_id))
    except Exception as e:
        flash(f"Error submitting booking: {str(e)}", "error")
        return redirect(url_for("machinery.detail", machinery_id=machinery_id))


@bookings_bp.route("/", methods=["GET"])
@login_required
def my_bookings():
    """List all booking requests placed by the logged-in farmer."""
    user = get_current_user()
    if user.role == "PROVIDER":
        # Redirect providers to their incoming requests dashboard
        return redirect(url_for("provider.bookings_list"))

    bookings = (
        Booking.query.filter_by(farmer_id=user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    return render_template("bookings/my_bookings.html", bookings=bookings)


@bookings_bp.route("/<uuid:booking_id>", methods=["GET"])
@login_required
def booking_detail(booking_id):
    """View details, status timeline, and cost breakdown of a booking."""
    user = get_current_user()
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)

    # Ownership check: Must be the farmer, owner provider, or admin
    is_farmer = booking.farmer_id == user.id
    is_owner_provider = (
        user.role == "PROVIDER"
        and user.provider_profile
        and booking.machinery.provider_id == user.provider_profile.id
    )
    is_admin = user.role == "ADMIN"

    if not (is_farmer or is_owner_provider or is_admin):
        abort(403)

    # Calculate pricing breakdown
    pricing_breakdown = None
    try:
        pricing_breakdown = calculate_pricing(
            machinery=booking.machinery,
            package_type=booking.rental_option_type,
            start_time=booking.start_time,
            end_time=booking.end_time,
        )
    except Exception:
        pass

    return render_template(
        "bookings/detail.html",
        booking=booking,
        pricing=pricing_breakdown,
        is_farmer=is_farmer,
        is_owner_provider=is_owner_provider,
        can_cancel=(
            is_farmer
            and booking.status in [Booking.STATUS_PENDING, Booking.STATUS_APPROVED]
            and (booking.status == Booking.STATUS_PENDING or booking.start_time > datetime.utcnow())
        ),
    )


@bookings_bp.route("/<uuid:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    """Allow farmer to cancel their pending or approved booking (before start time)."""
    user = get_current_user()
    booking = db.session.get(Booking, booking_id)
    if not booking:
        abort(404)

    if booking.farmer_id != user.id and user.role != "ADMIN":
        abort(403)

    reason = request.form.get("cancel_reason") or "Cancelled by farmer"

    try:
        transition_booking_status(
            booking=booking,
            new_status=Booking.STATUS_CANCELLED,
            actor_user=user,
            reason=reason,
        )
        flash("Booking request has been cancelled.", "info")
    except (BookingStateError, BookingValidationError, BookingAuthorizationError) as e:
        flash(str(e), "error")
    except Exception as e:
        flash(f"Error cancelling booking: {str(e)}", "error")

    return redirect(url_for("bookings.booking_detail", booking_id=booking.id))
