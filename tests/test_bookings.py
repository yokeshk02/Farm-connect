import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from flask import url_for

from app.models import User, ProviderProfile, Machinery, MachineryRate, MachineryAvailability, Booking, BookingStatusHistory
from app.services.booking_service import (
    calculate_pricing,
    validate_booking_request,
    create_booking_request,
    transition_booking_status,
    check_conflicting_confirmed_bookings,
    BookingValidationError,
    BookingConflictError,
    BookingStateError,
    BookingAuthorizationError,
)


def create_sample_machinery_and_users(db_session):
    """Helper to set up a sample provider, farmer, and machinery with rates and blackout."""
    farmer = User(phone="+919876543101", full_name="Murugan Farmer", role="FARMER")
    provider_user = User(phone="+919876543102", full_name="Velu Provider", role="PROVIDER")
    other_provider_user = User(phone="+919876543103", full_name="Other Provider", role="PROVIDER")
    db_session.add_all([farmer, provider_user, other_provider_user])
    db_session.commit()

    profile = ProviderProfile(
        user_id=provider_user.id,
        business_name="Velu Agri Rentals",
        verification_status="VERIFIED",
    )
    other_profile = ProviderProfile(
        user_id=other_provider_user.id,
        business_name="Other Agri Rentals",
        verification_status="VERIFIED",
    )
    db_session.add_all([profile, other_profile])
    db_session.commit()

    tractor = Machinery(
        provider_id=profile.id,
        name_en="Mahindra 575 DI",
        name_ta="மகிந்திரா 575 DI",
        category="TRACTOR",
        village_or_town="Kumbakonam",
        district="Thanjavur",
        pincode="612001",
        is_active=True,
    )
    db_session.add(tractor)
    db_session.commit()

    # Add rates
    rate_machine_only = MachineryRate(
        machinery_id=tractor.id,
        rental_option_type="MACHINE_ONLY",
        rate_per_hour=Decimal("600.00"),
        rate_per_day=Decimal("4500.00"),
        min_booking_duration_hours=2,
        security_deposit=Decimal("2000.00"),
    )
    rate_operator = MachineryRate(
        machinery_id=tractor.id,
        rental_option_type="MACHINE_OPERATOR",
        rate_per_hour=Decimal("800.00"),
        rate_per_day=Decimal("6000.00"),
        min_booking_duration_hours=1,
        security_deposit=Decimal("0.00"),
    )
    db_session.add_all([rate_machine_only, rate_operator])

    # Blackout window for tractor: next month 10th to 12th
    now = datetime.utcnow()
    blackout = MachineryAvailability(
        machinery_id=tractor.id,
        unavailable_from=now + timedelta(days=30),
        unavailable_to=now + timedelta(days=32),
        reason="MAINTENANCE",
    )
    db_session.add(blackout)
    db_session.commit()

    return farmer, provider_user, other_provider_user, tractor


def test_pricing_calculation_hourly_and_daily(db_session):
    """Test pricing calculations across hourly, capped daily, multi-day spans, and minimum duration."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    start = datetime(2026, 11, 1, 9, 0)

    # 1. Minimum duration enforcement (booked 1 hour, min is 2 hours for MACHINE_ONLY)
    end_1hr = datetime(2026, 11, 1, 10, 0)
    p1 = calculate_pricing(tractor, "MACHINE_ONLY", start, end_1hr)
    assert p1["actual_hours"] == 1
    assert p1["billable_hours"] == 2  # min_booking_duration_hours enforced
    assert p1["total_estimated_cost"] == 1200.0  # 2 hrs * 600
    assert p1["security_deposit"] == 2000.0

    # 2. Daily cap protection (booked 8 hours: 8 * 600 = 4800 > day rate 4500 -> capped at 4500)
    end_8hr = datetime(2026, 11, 1, 17, 0)
    p2 = calculate_pricing(tractor, "MACHINE_ONLY", start, end_8hr)
    assert p2["billable_hours"] == 8
    assert p2["total_estimated_cost"] == 4500.0

    # 3. Multi-day span: 28 hours (1 full day + 4 remaining hours)
    # 1 * 4500 + 4 * 600 = 4500 + 2400 = 6900
    end_28hr = start + timedelta(hours=28)
    p3 = calculate_pricing(tractor, "MACHINE_ONLY", start, end_28hr)
    assert p3["full_days"] == 1
    assert p3["remaining_hours"] == 4
    assert p3["daily_cost"] == 4500.0
    assert p3["hourly_cost"] == 2400.0
    assert p3["total_estimated_cost"] == 6900.0


def test_pricing_validation_errors(db_session):
    """Test validation errors for invalid dates, past times, unconfigured packages, and blackouts."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    # End before start
    with pytest.raises(BookingValidationError, match="after start time"):
        validate_booking_request(
            tractor,
            "MACHINE_ONLY",
            datetime(2026, 11, 2, 10, 0),
            datetime(2026, 11, 2, 9, 0),
        )

    # Unconfigured package
    with pytest.raises(BookingValidationError, match="not configured"):
        validate_booking_request(
            tractor,
            "MACHINE_OPERATOR_LABOUR",
            datetime(2026, 11, 2, 9, 0),
            datetime(2026, 11, 2, 12, 0),
        )

    # Past dates
    past_start = datetime(2020, 1, 1, 9, 0)
    past_end = datetime(2020, 1, 1, 12, 0)
    with pytest.raises(BookingValidationError, match="must be in the future"):
        validate_booking_request(
            tractor,
            "MACHINE_ONLY",
            past_start,
            past_end,
            check_future=True,
        )

    # Overlapping blackout window
    now = datetime.utcnow()
    blackout_start = now + timedelta(days=30, hours=2)
    blackout_end = now + timedelta(days=31)
    with pytest.raises(BookingValidationError, match="MAINTENANCE"):
        validate_booking_request(
            tractor,
            "MACHINE_ONLY",
            blackout_start,
            blackout_end,
            check_future=False,
        )


def test_create_booking_request_success(db_session):
    """Test creating a valid booking request generates unique reference and initial status history."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    start = datetime(2026, 11, 5, 9, 0)
    end = datetime(2026, 11, 5, 13, 0)

    booking = create_booking_request(
        farmer=farmer,
        machinery=tractor,
        package_type="MACHINE_OPERATOR",
        start_time=start,
        end_time=end,
        delivery_address="North Field, Papanasam",
        notes="Paddy field plowing",
    )

    assert booking.id is not None
    assert booking.booking_reference.startswith("FC-BK-")
    assert booking.status == Booking.STATUS_PENDING
    assert booking.rental_option_type == "MACHINE_OPERATOR"
    assert booking.estimated_total_cost == Decimal("3200.00")  # 4 hrs * 800
    assert booking.delivery_address == "North Field, Papanasam"

    # Status history check
    assert len(booking.status_history) == 1
    history = booking.status_history[0]
    assert history.from_status is None
    assert history.to_status == Booking.STATUS_PENDING
    assert history.changed_by_user_id == farmer.id


def test_farmer_booking_flow_integration(client, db_session):
    """Test submitting a booking request through HTTP route and viewing in My Bookings."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    # Sign in as farmer
    with client.session_transaction() as sess:
        sess["user_id"] = str(farmer.id)
        sess["user_role"] = "FARMER"
        sess["user_name"] = farmer.full_name
        sess["lang"] = "en"

    # Submit booking request
    start_str = "2026-11-05T09:00"
    end_str = "2026-11-05T13:00"
    resp = client.post(
        f"/bookings/machinery/{tractor.id}",
        data={
            "rental_option_type": "MACHINE_ONLY",
            "start_time": start_str,
            "end_time": end_str,
            "delivery_address": "Test Village Road",
            "notes": "Need early morning delivery",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert "FC-BK-" in content
    assert "Mahindra 575 DI" in content

    # View My Bookings list
    list_resp = client.get("/bookings/")
    assert list_resp.status_code == 200
    list_content = list_resp.data.decode("utf-8")
    assert "FC-BK-" in list_content
    assert "Pending" in list_content


def test_farmer_cancellation_allowed_and_rejected(client, db_session):
    """Test farmer can cancel PENDING booking, but cannot cancel COMPLETED booking or another farmer's booking."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)
    other_farmer = User(phone="+919876543199", full_name="Other Farmer", role="FARMER")
    db_session.add(other_farmer)
    db_session.commit()

    start = datetime(2026, 11, 5, 9, 0)
    end = datetime(2026, 11, 5, 13, 0)
    booking = create_booking_request(
        farmer=farmer,
        machinery=tractor,
        package_type="MACHINE_ONLY",
        start_time=start,
        end_time=end,
    )

    # 1. Other farmer attempts to cancel -> 403 Forbidden
    with client.session_transaction() as sess:
        sess["user_id"] = str(other_farmer.id)
        sess["user_role"] = "FARMER"

    forbidden_resp = client.post(f"/bookings/{booking.id}/cancel")
    assert forbidden_resp.status_code == 403

    # 2. Owner farmer cancels -> Success
    with client.session_transaction() as sess:
        sess["user_id"] = str(farmer.id)
        sess["user_role"] = "FARMER"

    cancel_resp = client.post(
        f"/bookings/{booking.id}/cancel",
        data={"cancel_reason": "Change of plans"},
        follow_redirects=True,
    )
    assert cancel_resp.status_code == 200
    refetched = db_session.get(Booking, booking.id)
    assert refetched.status == Booking.STATUS_CANCELLED
    assert len(refetched.status_history) == 2
    assert refetched.status_history[1].to_status == Booking.STATUS_CANCELLED


def test_provider_booking_approval_and_conflict_rejection(db_session):
    """Test provider approves pending booking, and a conflicting overlapping booking is rejected."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    start = datetime(2026, 11, 10, 9, 0)
    end = datetime(2026, 11, 10, 17, 0)

    # Request 1
    booking1 = create_booking_request(
        farmer=farmer,
        machinery=tractor,
        package_type="MACHINE_ONLY",
        start_time=start,
        end_time=end,
    )

    # Request 2 overlaps Request 1 (12:00 to 20:00)
    booking2 = create_booking_request(
        farmer=farmer,
        machinery=tractor,
        package_type="MACHINE_ONLY",
        start_time=datetime(2026, 11, 10, 12, 0),
        end_time=datetime(2026, 11, 10, 20, 0),
    )

    # Provider approves booking1 -> Success
    transition_booking_status(booking1, Booking.STATUS_APPROVED, provider_user)
    assert booking1.status == Booking.STATUS_APPROVED

    # Provider attempts to approve booking2 -> Overlap conflict
    with pytest.raises(BookingConflictError, match="already booked"):
        transition_booking_status(booking2, Booking.STATUS_APPROVED, provider_user)

    # Booking 2 state remains PENDING
    assert booking2.status == Booking.STATUS_PENDING


def test_adjacent_non_overlapping_intervals_allowed(db_session):
    """Verify adjacent bookings [09:00, 13:00) and [13:00, 17:00) do NOT conflict."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    b1_start = datetime(2026, 12, 15, 9, 0)
    b1_end = datetime(2026, 12, 15, 13, 0)

    b2_start = datetime(2026, 12, 15, 13, 0)  # Starts exactly when b1 ends
    b2_end = datetime(2026, 12, 15, 17, 0)

    booking1 = create_booking_request(
        farmer=farmer, machinery=tractor, package_type="MACHINE_ONLY",
        start_time=b1_start, end_time=b1_end
    )
    booking2 = create_booking_request(
        farmer=farmer, machinery=tractor, package_type="MACHINE_ONLY",
        start_time=b2_start, end_time=b2_end
    )

    # Both approvals should succeed
    transition_booking_status(booking1, Booking.STATUS_APPROVED, provider_user)
    transition_booking_status(booking2, Booking.STATUS_APPROVED, provider_user)

    assert booking1.status == Booking.STATUS_APPROVED
    assert booking2.status == Booking.STATUS_APPROVED


def test_provider_rejection_requires_reason(db_session):
    """Verify that declining a booking requires a non-empty rejection reason."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    booking = create_booking_request(
        farmer=farmer, machinery=tractor, package_type="MACHINE_ONLY",
        start_time=datetime(2026, 11, 20, 9, 0), end_time=datetime(2026, 11, 20, 13, 0)
    )

    # Rejection without reason fails
    with pytest.raises(BookingValidationError, match="rejection reason is required"):
        transition_booking_status(booking, Booking.STATUS_REJECTED, provider_user, reason="")

    # Rejection with reason succeeds
    transition_booking_status(
        booking, Booking.STATUS_REJECTED, provider_user, reason="Operator unavailable"
    )
    assert booking.status == Booking.STATUS_REJECTED
    assert booking.status_history[-1].reason_or_comment == "Operator unavailable"


def test_lifecycle_flow_to_completion(db_session):
    """Verify complete 4-step canonical lifecycle: PENDING -> APPROVED -> IN_PROGRESS -> COMPLETED."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    booking = create_booking_request(
        farmer=farmer, machinery=tractor, package_type="MACHINE_ONLY",
        start_time=datetime(2026, 11, 25, 9, 0), end_time=datetime(2026, 11, 25, 17, 0)
    )
    assert booking.status == Booking.STATUS_PENDING

    # Step 1: Approve
    transition_booking_status(booking, Booking.STATUS_APPROVED, provider_user)
    assert booking.status == Booking.STATUS_APPROVED

    # Step 2: Start
    transition_booking_status(booking, Booking.STATUS_IN_PROGRESS, provider_user)
    assert booking.status == Booking.STATUS_IN_PROGRESS

    # Step 3: Complete
    transition_booking_status(booking, Booking.STATUS_COMPLETED, provider_user)
    assert booking.status == Booking.STATUS_COMPLETED

    # Step 4: Verify cannot transition after terminal COMPLETED
    with pytest.raises(BookingStateError):
        transition_booking_status(booking, Booking.STATUS_CANCELLED, provider_user)

    assert len(booking.status_history) == 4


def test_cross_provider_access_denied(client, db_session):
    """Verify Provider B cannot view, approve, or reject Provider A's booking."""
    farmer, provider_user, other_provider_user, tractor = create_sample_machinery_and_users(db_session)

    booking = create_booking_request(
        farmer=farmer, machinery=tractor, package_type="MACHINE_ONLY",
        start_time=datetime(2026, 11, 28, 9, 0), end_time=datetime(2026, 11, 28, 13, 0)
    )

    # Sign in as other provider
    with client.session_transaction() as sess:
        sess["user_id"] = str(other_provider_user.id)
        sess["user_role"] = "PROVIDER"

    # Attempt to view details
    view_resp = client.get(f"/provider/bookings/{booking.id}")
    assert view_resp.status_code == 403

    # Attempt to approve
    approve_resp = client.post(f"/provider/bookings/{booking.id}/approve")
    assert approve_resp.status_code == 403

    # Attempt to reject
    reject_resp = client.post(f"/provider/bookings/{booking.id}/reject", data={"rejection_reason": "No reason"})
    assert reject_resp.status_code == 403


def test_booking_details_duration_and_currency_display(client, db_session):
    """Verify that booking details correctly distinguish numeric duration from monetary amounts.
    Duration must NEVER be prefixed with a rupee symbol (₹).
    Rental rate, security deposit, and total must have correct currency and units."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    # 4-hour booking: 09:00 to 13:00 (MACHINE_ONLY rate: 600/hr, deposit: 2000)
    # Estimated rental price = 4 * 600 = 2400
    # Security deposit = 2000
    # Total = 4400
    start = datetime(2026, 11, 28, 9, 0)
    end = datetime(2026, 11, 28, 13, 0)

    booking = create_booking_request(
        farmer=farmer,
        machinery=tractor,
        package_type="MACHINE_ONLY",
        start_time=start,
        end_time=end,
    )

    with client.session_transaction() as sess:
        sess["user_id"] = str(farmer.id)
        sess["user_role"] = "FARMER"
        sess["user_phone"] = farmer.phone
        sess["user_name"] = farmer.full_name

    # 1. Booking Details Page
    resp = client.get(f"/bookings/{booking.id}")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    # Duration must display measured in hours WITHOUT rupee symbol
    assert "4 hours" in html or "4 hour" in html
    assert "₹4 hours" not in html
    assert "₹4 hour" not in html
    assert "₹ 4 hours" not in html

    # Rental Rate must display with currency and /hour unit
    assert "₹600/hour" in html or "₹600.00/hour" in html or "600/hour" in html

    # Estimated Rental Price, Security Deposit, and Total Amount must have ₹
    assert "₹2400.00" in html or "₹2,400.00" in html
    assert "₹2000.00" in html or "₹2,000.00" in html

    # 2. My Bookings Card
    my_resp = client.get("/bookings/my")
    assert my_resp.status_code == 200
    my_html = my_resp.data.decode("utf-8")
    assert "4 hours" in my_html
    assert "₹4 hours" not in my_html
    assert "₹2400.00" in my_html

    # 3. Farmer Dashboard
    dash_resp = client.get("/farmer/dashboard")
    assert dash_resp.status_code == 200
    dash_html = dash_resp.data.decode("utf-8")
    assert "4 hours" in dash_html
    assert "₹4 hours" not in dash_html
    assert "₹2400.00" in dash_html


def test_provider_booking_details_rate_vs_cost_display(client, db_session):
    """Verify provider booking details clearly distinguishes hourly rate from hourly cost."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    start = datetime(2026, 11, 28, 9, 0)
    end = datetime(2026, 11, 28, 13, 0)

    booking = create_booking_request(
        farmer=farmer,
        machinery=tractor,
        package_type="MACHINE_ONLY",
        start_time=start,
        end_time=end,
    )

    with client.session_transaction() as sess:
        sess["user_id"] = str(provider_user.id)
        sess["user_role"] = "PROVIDER"
        sess["user_phone"] = provider_user.phone
        sess["user_name"] = provider_user.full_name

    resp = client.get(f"/provider/bookings/{booking.id}")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    # Billable duration without ₹
    assert "4 billable hour(s)" in html
    assert "₹4 billable hour" not in html

    # Hourly Rate: ₹600.00/hour
    assert "₹600.00/hour" in html

    # Hourly Cost: 4 hrs × ₹600.00 = ₹2400.00
    assert "4 hrs × ₹600.00 = ₹2400.00" in html

    # Total estimate with ₹
    assert "₹2400.00" in html


def test_bilingual_booking_units_and_category(client, db_session):
    """Verify Tamil translation displays correct units, labels, and category translations."""
    farmer, provider_user, _, tractor = create_sample_machinery_and_users(db_session)

    booking = create_booking_request(
        farmer=farmer,
        machinery=tractor,
        package_type="MACHINE_ONLY",
        start_time=datetime(2026, 11, 28, 9, 0),
        end_time=datetime(2026, 11, 28, 13, 0),
    )

    with client.session_transaction() as sess:
        sess["user_id"] = str(farmer.id)
        sess["user_role"] = "FARMER"

    # Switch to Tamil
    lang_resp = client.get("/set-language/ta", follow_redirects=True)
    assert lang_resp.status_code == 200

    resp = client.get(f"/bookings/{booking.id}")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    # Tamil labels for booking details
    assert "கால அளவு" in html  # Duration
    assert "வாடகைத் தொகுப்பு" in html  # Rental Package
    assert "இயந்திரம் மட்டும்" in html  # Machine Only
    assert "வாடகைக் கட்டணம்" in html  # Rental Rate
    assert "மதிப்பிடப்பட்ட வாடகைக் கட்டணம்" in html  # Estimated Rental Price
    assert "மொத்தத் தொகை" in html  # Total Amount
    assert "முன்பதிவு விவரங்கள்" in html  # Booking Details

