import pytest
import sqlalchemy as sa
from sqlalchemy import text
from app.extensions import db


def test_postgresql_live_connection(pg_app):
    """Verify live connectivity and query execution against PostgreSQL database."""
    with pg_app.app_context():
        result = db.session.execute(text("SELECT 1 AS alive")).scalar()
        assert result == 1

        version_str = db.session.execute(text("SELECT version()")).scalar()
        assert "PostgreSQL" in version_str


def test_postgresql_expected_tables_exist(pg_app):
    """Verify all 10 application tables and alembic_version exist in PostgreSQL."""
    expected_tables = {
        "users",
        "user_locations",
        "provider_profiles",
        "machinery",
        "machinery_photos",
        "machinery_rates",
        "machinery_availability",
        "bookings",
        "booking_status_history",
        "contact_enquiries",
        "otp_verifications",
        "alembic_version",
    }

    with pg_app.app_context():
        inspector = sa.inspect(db.engine)
        actual_tables = set(inspector.get_table_names())
        missing_tables = expected_tables - actual_tables
        assert not missing_tables, f"Missing tables in PostgreSQL: {missing_tables}"


def test_postgresql_btree_gist_extension_installed(pg_app):
    """Verify that btree_gist extension is installed for double-booking exclusion constraints."""
    with pg_app.app_context():
        installed_extensions = db.session.execute(
            text("SELECT extname FROM pg_extension")
        ).scalars().all()
        assert "btree_gist" in installed_extensions


def test_postgresql_overlapping_booking_exclusion_constraint(pg_app):
    """Verify that PostgreSQL rejects overlapping APPROVED bookings for the same machine."""
    import uuid
    from datetime import datetime, timedelta
    from decimal import Decimal
    from sqlalchemy.exc import IntegrityError
    from app.models import User, ProviderProfile, Machinery, Booking

    with pg_app.app_context():
        try:
            # Create test provider and farmer
            p_user = User(phone="+919876543991", full_name="Test Provider")
            f_user = User(phone="+919876543992", full_name="Test Farmer")
            db.session.add_all([p_user, f_user])
            db.session.flush()

            profile = ProviderProfile(user_id=p_user.id, business_name="Constraint Test Agri")
            db.session.add(profile)
            db.session.flush()

            machine = Machinery(
                provider_id=profile.id,
                name_en="Constraint Test Tractor",
                category="TRACTOR",
                village_or_town="Test Town",
                district="Thanjavur",
                pincode="612001",
            )
            db.session.add(machine)
            db.session.flush()

            start1 = datetime(2026, 11, 1, 9, 0, 0)
            end1 = datetime(2026, 11, 1, 17, 0, 0)

            # First confirmed booking
            booking1 = Booking(
                booking_reference="FC-EXCLUDE-001",
                farmer_id=f_user.id,
                machinery_id=machine.id,
                rental_option_type="MACHINE_ONLY",
                start_time=start1,
                end_time=end1,
                estimated_total_cost=Decimal("3000.00"),
                status=Booking.STATUS_APPROVED,
            )
            db.session.add(booking1)
            db.session.commit()

            # Second overlapping confirmed booking (12:00 to 20:00 on the same date)
            start2 = datetime(2026, 11, 1, 12, 0, 0)
            end2 = datetime(2026, 11, 1, 20, 0, 0)
            booking2 = Booking(
                booking_reference="FC-EXCLUDE-002",
                farmer_id=f_user.id,
                machinery_id=machine.id,
                rental_option_type="MACHINE_ONLY",
                start_time=start2,
                end_time=end2,
                estimated_total_cost=Decimal("3000.00"),
                status=Booking.STATUS_APPROVED,
            )
            db.session.add(booking2)

            with pytest.raises(IntegrityError):
                db.session.commit()

        finally:
            db.session.rollback()
            # Cleanup test records
            Booking.query.filter(Booking.booking_reference.like("FC-EXCLUDE-%")).delete()
            Machinery.query.filter_by(name_en="Constraint Test Tractor").delete()
            ProviderProfile.query.filter_by(business_name="Constraint Test Agri").delete()
            User.query.filter(User.phone.in_(["+919876543991", "+919876543992"])).delete()
            db.session.commit()

