import uuid
from datetime import datetime
from sqlalchemy import Uuid, String, DateTime, Numeric, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.extensions import db


class Booking(db.Model):
    """Rental booking request and contract placed by a farmer."""

    __tablename__ = "bookings"

    # Status enum constants
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_REJECTED = "REJECTED"

    VALID_STATUSES = {
        STATUS_PENDING,
        STATUS_APPROVED,
        STATUS_IN_PROGRESS,
        STATUS_COMPLETED,
        STATUS_CANCELLED,
        STATUS_REJECTED,
    }

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_reference = db.Column(String(30), unique=True, nullable=False, index=True)
    farmer_id = db.Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    machinery_id = db.Column(
        Uuid(as_uuid=True),
        ForeignKey("machinery.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rental_option_type = db.Column(
        String(50), nullable=False
    )  # MACHINE_ONLY, MACHINE_OPERATOR, MACHINE_OPERATOR_LABOUR
    start_time = db.Column(DateTime, nullable=False, index=True)
    end_time = db.Column(DateTime, nullable=False, index=True)
    estimated_total_cost = db.Column(Numeric(10, 2), nullable=False)
    status = db.Column(
        String(20), nullable=False, default=STATUS_PENDING, index=True
    )  # PENDING, APPROVED, IN_PROGRESS, COMPLETED, CANCELLED, REJECTED
    delivery_address = db.Column(Text, nullable=True)
    contact_phone_snapshot = db.Column(String(15), nullable=True)
    notes = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite index for conflict checks
    __table_args__ = (
        Index("idx_bookings_machine_dates", "machinery_id", "start_time", "end_time", "status"),
    )

    # Relationships
    farmer = relationship("User", back_populates="bookings", foreign_keys=[farmer_id])
    machinery = relationship("Machinery", back_populates="bookings")
    status_history = relationship(
        "BookingStatusHistory",
        back_populates="booking",
        cascade="all, delete-orphan",
        order_by="BookingStatusHistory.changed_at",
    )

    def __repr__(self) -> str:
        return f"<Booking ref={self.booking_reference} status={self.status} machine_id={self.machinery_id}>"


class BookingStatusHistory(db.Model):
    """Audit trail tracking each state transition in the booking lifecycle."""

    __tablename__ = "booking_status_history"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = db.Column(
        Uuid(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status = db.Column(String(20), nullable=True)
    to_status = db.Column(String(20), nullable=False)
    changed_by_user_id = db.Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason_or_comment = db.Column(Text, nullable=True)
    changed_at = db.Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    booking = relationship("Booking", back_populates="status_history")
    changed_by = relationship("User")

    def __repr__(self) -> str:
        return f"<BookingStatusHistory booking_id={self.booking_id} {self.from_status} -> {self.to_status}>"
