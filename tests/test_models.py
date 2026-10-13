import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from app.models import (
    User,
    UserLocation,
    ProviderProfile,
    Machinery,
    MachineryPhoto,
    MachineryRate,
    MachineryAvailability,
    Booking,
    BookingStatusHistory,
    ContactEnquiry,
)


def test_user_password_hashing_and_defaults(db_session):
    """Test User password hashing and default values."""
    user = User(
        phone="+919876543210",
        full_name="Murugan Farmer",
        preferred_language="ta",
    )
    user.set_password("SecureFarmPass123!")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.role == "FARMER"
    assert user.preferred_language == "ta"
    assert user.is_active is True
    assert user.is_phone_verified is False
    assert user.check_password("SecureFarmPass123!") is True
    assert user.check_password("WrongPassword") is False


def test_user_locations_relationship(db_session):
    """Test User to UserLocation 1:N relationship."""
    user = User(phone="+919876543211", full_name="Senthil Kumar")
    db_session.add(user)
    db_session.commit()

    location = UserLocation(
        user_id=user.id,
        address_line="Main Road",
        village_or_town="Kumbakonam",
        district="Thanjavur",
        pincode="612001",
        latitude=Decimal("10.9602000"),
        longitude=Decimal("79.3845000"),
        is_primary=True,
    )
    db_session.add(location)
    db_session.commit()

    assert len(user.locations) == 1
    assert user.locations[0].village_or_town == "Kumbakonam"
    assert user.locations[0].district == "Thanjavur"


def test_provider_profile_and_machinery_hierarchy(db_session):
    """Test User -> ProviderProfile -> Machinery -> Rates & Photos relationships."""
    provider_user = User(phone="+919876543212", full_name="Raja Provider", role="PROVIDER")
    db_session.add(provider_user)
    db_session.commit()

    profile = ProviderProfile(
        user_id=provider_user.id,
        business_name="Cauvery Agri Rentals",
        whatsapp_enabled=True,
        whatsapp_number="+919876543212",
        verification_status="VERIFIED",
    )
    db_session.add(profile)
    db_session.commit()

    assert provider_user.provider_profile.business_name == "Cauvery Agri Rentals"

    # Add Machinery
    tractor = Machinery(
        provider_id=profile.id,
        name_en="Mahindra 575 DI Tractor",
        name_ta="மகிந்திரா 575 டிராக்டர்",
        category="TRACTOR",
        make_model="Mahindra 575 DI",
        horsepower=45,
        village_or_town="Papanasam",
        district="Thanjavur",
        pincode="614205",
        is_active=True,
    )
    db_session.add(tractor)
    db_session.commit()

    # Add Photo
    photo = MachineryPhoto(
        machinery_id=tractor.id,
        photo_url="/static/uploads/machinery/tractor_1.jpg",
        is_primary=True,
    )
    db_session.add(photo)

    # Add 3 Rental Package Rates
    rate1 = MachineryRate(
        machinery_id=tractor.id,
        rental_option_type="MACHINE_ONLY",
        rate_per_hour=Decimal("600.00"),
        rate_per_day=Decimal("4500.00"),
    )
    rate2 = MachineryRate(
        machinery_id=tractor.id,
        rental_option_type="MACHINE_OPERATOR",
        rate_per_hour=Decimal("800.00"),
        rate_per_day=Decimal("6000.00"),
    )
    rate3 = MachineryRate(
        machinery_id=tractor.id,
        rental_option_type="MACHINE_OPERATOR_LABOUR",
        rate_per_hour=Decimal("1200.00"),
        rate_per_day=Decimal("9000.00"),
    )
    db_session.add_all([rate1, rate2, rate3])

    # Add Blackout Window
    now = datetime.utcnow()
    blackout = MachineryAvailability(
        machinery_id=tractor.id,
        unavailable_from=now + timedelta(days=10),
        unavailable_to=now + timedelta(days=12),
        reason="MAINTENANCE",
    )
    db_session.add(blackout)
    db_session.commit()

    assert tractor.photos[0].photo_url == "/static/uploads/machinery/tractor_1.jpg"
    assert len(tractor.rates) == 3
    assert len(tractor.availabilities) == 1


def test_booking_and_status_history_lifecycle(db_session):
    """Test Booking creation, relationships, and status history audit records."""
    farmer = User(phone="+919876543213", full_name="Kavitha Farmer")
    provider = User(phone="+919876543214", full_name="Velu Rentals", role="PROVIDER")
    db_session.add_all([farmer, provider])
    db_session.commit()

    profile = ProviderProfile(user_id=provider.id, business_name="Velu Farm Equipment")
    db_session.add(profile)
    db_session.commit()

    machine = Machinery(
        provider_id=profile.id,
        name_en="John Deere Harvester",
        category="HARVESTER",
        village_or_town="Mannargudi",
        district="Tiruvarur",
        pincode="614001",
    )
    db_session.add(machine)
    db_session.commit()

    now = datetime.utcnow()
    booking = Booking(
        booking_reference="FC-2026-TEST-001",
        farmer_id=farmer.id,
        machinery_id=machine.id,
        rental_option_type="MACHINE_OPERATOR",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=3),
        estimated_total_cost=Decimal("7500.00"),
        status=Booking.STATUS_PENDING,
    )
    db_session.add(booking)
    db_session.commit()

    assert booking.status == Booking.STATUS_PENDING
    assert booking.farmer.full_name == "Kavitha Farmer"
    assert booking.machinery.name_en == "John Deere Harvester"

    # Record status transition to APPROVED
    history_entry = BookingStatusHistory(
        booking_id=booking.id,
        from_status=Booking.STATUS_PENDING,
        to_status=Booking.STATUS_APPROVED,
        changed_by_user_id=provider.id,
        reason_or_comment="Accepted by equipment owner",
    )
    booking.status = Booking.STATUS_APPROVED
    db_session.add(history_entry)
    db_session.commit()

    assert len(booking.status_history) == 1
    assert booking.status_history[0].to_status == Booking.STATUS_APPROVED
    assert booking.status_history[0].changed_by.full_name == "Velu Rentals"


def test_contact_enquiry_lifecycle(db_session):
    """Test ContactEnquiry submission and status updating."""
    enquiry = ContactEnquiry(
        sender_name="Mani V",
        contact_phone_or_email="mani@example.com",
        subject="Harvester Availability Query",
        message="Is harvester service available in Nagapattinam?",
        status=ContactEnquiry.STATUS_NEW,
    )
    db_session.add(enquiry)
    db_session.commit()

    assert enquiry.id is not None
    assert enquiry.status == "NEW"

    enquiry.status = ContactEnquiry.STATUS_RESOLVED
    enquiry.admin_notes = "Answered via telephone."
    db_session.commit()

    refetched = db_session.get(ContactEnquiry, enquiry.id)
    assert refetched.status == "RESOLVED"
    assert refetched.admin_notes == "Answered via telephone."
