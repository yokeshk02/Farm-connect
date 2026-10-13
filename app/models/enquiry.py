import uuid
from datetime import datetime
from sqlalchemy import Uuid, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.extensions import db


class ContactEnquiry(db.Model):
    """Customer support, feedback, and general contact enquiries."""

    __tablename__ = "contact_enquiries"

    STATUS_NEW = "NEW"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_RESOLVED = "RESOLVED"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sender_name = db.Column(String(100), nullable=False)
    contact_phone_or_email = db.Column(String(100), nullable=False)
    subject = db.Column(String(150), nullable=False)
    message = db.Column(Text, nullable=False)
    status = db.Column(String(20), nullable=False, default=STATUS_NEW, index=True)  # NEW, IN_PROGRESS, RESOLVED
    admin_notes = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="enquiries")

    def __repr__(self) -> str:
        return f"<ContactEnquiry id={self.id} subject={self.subject} status={self.status}>"
