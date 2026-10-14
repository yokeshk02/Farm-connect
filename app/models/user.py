import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Uuid, String, Boolean, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.extensions import db


class User(db.Model):
    """User entity supporting Farmers, Providers, and Administrators."""

    __tablename__ = "users"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = db.Column(String(15), unique=True, nullable=False, index=True)
    role = db.Column(String(20), nullable=False, default="FARMER", index=True)  # FARMER, PROVIDER, ADMIN
    full_name = db.Column(String(100), nullable=True)
    password_hash = db.Column(String(255), nullable=True)  # Nullable for OTP-only users; required for Admin
    preferred_language = db.Column(String(5), nullable=False, default="en")  # 'en' or 'ta'
    is_active = db.Column(Boolean, nullable=False, default=True)
    is_phone_verified = db.Column(Boolean, nullable=False, default=False)
    last_login_at = db.Column(DateTime, nullable=True)
    created_at = db.Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    locations = relationship(
        "UserLocation",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(UserLocation.is_primary)",
    )
    provider_profile = relationship(
        "ProviderProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    bookings = relationship(
        "Booking",
        back_populates="farmer",
        foreign_keys="Booking.farmer_id",
        lazy="dynamic",
    )
    enquiries = relationship(
        "ContactEnquiry",
        back_populates="user",
        lazy="dynamic",
    )

    def set_password(self, password: str) -> None:
        """Hash and persist user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User id={self.id} phone={self.phone} role={self.role}>"


class UserLocation(db.Model):
    """Location and address details for users (village, town, district, PIN code, optional GPS)."""

    __tablename__ = "user_locations"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    address_line = db.Column(String(255), nullable=True)
    village_or_town = db.Column(String(100), nullable=False, index=True)
    district = db.Column(String(100), nullable=False, index=True)
    state = db.Column(String(100), nullable=False, default="Tamil Nadu")
    pincode = db.Column(String(10), nullable=False, index=True)
    latitude = db.Column(Numeric(10, 7), nullable=True)
    longitude = db.Column(Numeric(10, 7), nullable=True)
    is_primary = db.Column(Boolean, nullable=False, default=True)
    created_at = db.Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="locations")

    def __repr__(self) -> str:
        return f"<UserLocation id={self.id} district={self.district} pincode={self.pincode}>"


class ProviderProfile(db.Model):
    """Business and profile details for machinery rental service providers."""

    __tablename__ = "provider_profiles"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), unique=True, nullable=False)
    business_name = db.Column(String(150), nullable=True)
    alternate_phone = db.Column(String(15), nullable=True)
    whatsapp_enabled = db.Column(Boolean, nullable=False, default=False)
    whatsapp_number = db.Column(String(15), nullable=True)
    verification_status = db.Column(
        String(20), nullable=False, default="PENDING", index=True
    )  # PENDING, VERIFIED, SUSPENDED
    bio_description = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="provider_profile")
    machinery = relationship("Machinery", back_populates="provider", lazy="dynamic")

    @property
    def machinery_count(self) -> int:
        """Total number of machinery units owned by this provider."""
        if hasattr(self, "_cached_machinery_count") and self._cached_machinery_count is not None:
            return self._cached_machinery_count
        return self.machinery.count()

    @machinery_count.setter
    def machinery_count(self, value: int):
        self._cached_machinery_count = value

    def __repr__(self) -> str:
        return f"<ProviderProfile id={self.id} business_name={self.business_name} status={self.verification_status}>"
