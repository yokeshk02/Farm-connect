import uuid
from datetime import datetime
from sqlalchemy import Uuid, String, DateTime, Integer
from app.extensions import db


class OTPVerification(db.Model):
    """Secure, hashed verification token records for phone-based authentication."""

    __tablename__ = "otp_verifications"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = db.Column(String(15), nullable=False, index=True)
    otp_hash = db.Column(String(255), nullable=False)
    purpose = db.Column(String(20), nullable=False, default="LOGIN")  # LOGIN, REGISTER
    attempts = db.Column(Integer, nullable=False, default=0)
    max_attempts = db.Column(Integer, nullable=False, default=3)
    expires_at = db.Column(DateTime, nullable=False, index=True)
    created_at = db.Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    consumed_at = db.Column(DateTime, nullable=True)

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def is_consumed(self) -> bool:
        return self.consumed_at is not None

    def is_locked(self) -> bool:
        return self.attempts >= self.max_attempts

    def __repr__(self) -> str:
        return f"<OTPVerification id={self.id} phone={self.phone} purpose={self.purpose} attempts={self.attempts}>"
