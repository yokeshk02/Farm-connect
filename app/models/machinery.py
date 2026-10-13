import uuid
from datetime import datetime
from sqlalchemy import Uuid, String, Boolean, DateTime, Numeric, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.extensions import db


class Machinery(db.Model):
    """Agricultural equipment listing owned and managed by a provider."""

    __tablename__ = "machinery"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = db.Column(
        Uuid(as_uuid=True),
        ForeignKey("provider_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name_en = db.Column(String(150), nullable=False)
    name_ta = db.Column(String(150), nullable=True)
    category = db.Column(
        String(50), nullable=False, index=True
    )  # TRACTOR, HARVESTER, TILLER, SPRAYER, BALER, OTHER
    make_model = db.Column(String(100), nullable=True)
    model_year = db.Column(Integer, nullable=True)
    horsepower = db.Column(Integer, nullable=True)
    description_en = db.Column(Text, nullable=True)
    description_ta = db.Column(Text, nullable=True)

    # Base operating location
    village_or_town = db.Column(String(100), nullable=False, index=True)
    district = db.Column(String(100), nullable=False, index=True)
    pincode = db.Column(String(10), nullable=False, index=True)
    latitude = db.Column(Numeric(10, 7), nullable=True)
    longitude = db.Column(Numeric(10, 7), nullable=True)

    is_active = db.Column(Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite index for search filtering
    __table_args__ = (
        Index("idx_machinery_search", "district", "category", "is_active"),
    )

    # Relationships
    provider = relationship("ProviderProfile", back_populates="machinery")
    photos = relationship(
        "MachineryPhoto",
        back_populates="machinery",
        cascade="all, delete-orphan",
        order_by="MachineryPhoto.display_order",
    )
    rates = relationship(
        "MachineryRate",
        back_populates="machinery",
        cascade="all, delete-orphan",
    )
    availabilities = relationship(
        "MachineryAvailability",
        back_populates="machinery",
        cascade="all, delete-orphan",
    )
    bookings = relationship(
        "Booking",
        back_populates="machinery",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Machinery id={self.id} name={self.name_en} category={self.category} district={self.district}>"


class MachineryPhoto(db.Model):
    """Photographs of listed machinery."""

    __tablename__ = "machinery_photos"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machinery_id = db.Column(
        Uuid(as_uuid=True),
        ForeignKey("machinery.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    photo_url = db.Column(String(500), nullable=False)
    is_primary = db.Column(Boolean, nullable=False, default=False)
    display_order = db.Column(Integer, nullable=False, default=0)
    created_at = db.Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    machinery = relationship("Machinery", back_populates="photos")

    def __repr__(self) -> str:
        return f"<MachineryPhoto id={self.id} machinery_id={self.machinery_id} is_primary={self.is_primary}>"


class MachineryRate(db.Model):
    """Pricing configuration for a machinery package option (hourly and daily)."""

    __tablename__ = "machinery_rates"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machinery_id = db.Column(
        Uuid(as_uuid=True),
        ForeignKey("machinery.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rental_option_type = db.Column(
        String(50), nullable=False
    )  # MACHINE_ONLY, MACHINE_OPERATOR, MACHINE_OPERATOR_LABOUR
    rate_per_hour = db.Column(Numeric(10, 2), nullable=True)
    rate_per_day = db.Column(Numeric(10, 2), nullable=True)
    min_booking_duration_hours = db.Column(Integer, nullable=False, default=1)
    security_deposit = db.Column(Numeric(10, 2), nullable=False, default=0.00)
    created_at = db.Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    machinery = relationship("Machinery", back_populates="rates")

    def __repr__(self) -> str:
        return f"<MachineryRate id={self.id} option={self.rental_option_type} rate_day={self.rate_per_day}>"


class MachineryAvailability(db.Model):
    """Custom blackout or unavailable date/time windows for equipment."""

    __tablename__ = "machinery_availability"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machinery_id = db.Column(
        Uuid(as_uuid=True),
        ForeignKey("machinery.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unavailable_from = db.Column(DateTime, nullable=False)
    unavailable_to = db.Column(DateTime, nullable=False)
    reason = db.Column(String(100), nullable=False, default="MAINTENANCE")  # MAINTENANCE, PERSONAL_USE, SEASONAL_OFF
    created_at = db.Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    machinery = relationship("Machinery", back_populates="availabilities")

    def __repr__(self) -> str:
        return f"<MachineryAvailability id={self.id} from={self.unavailable_from} to={self.unavailable_to}>"
