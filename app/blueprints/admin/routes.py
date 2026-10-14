from flask import render_template
from sqlalchemy import func
from app.blueprints.admin import admin_bp
from app.extensions import db
from app.models.user import User, ProviderProfile
from app.models.machinery import Machinery
from app.models.booking import Booking
from app.models.enquiry import ContactEnquiry
from app.utils.security import login_required, role_required, get_current_user


@admin_bp.route("/", methods=["GET"])
@admin_bp.route("/dashboard", methods=["GET"])
@login_required
@role_required("ADMIN")
def dashboard():
    """Admin governance dashboard showing platform-wide metrics and enquiries."""
    user = get_current_user()

    # Aggregate platform metrics
    total_farmers = User.query.filter_by(role="FARMER").count()
    total_providers = User.query.filter_by(role="PROVIDER").count()
    total_machinery = Machinery.query.count()
    active_machinery = Machinery.query.filter_by(is_active=True).count()
    total_bookings = Booking.query.count()
    total_enquiries = ContactEnquiry.query.count()

    recent_enquiries = ContactEnquiry.query.order_by(ContactEnquiry.created_at.desc()).limit(5).all()
    providers_list = ProviderProfile.query.order_by(ProviderProfile.created_at.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()

    # Calculate machinery count for each provider using SQLAlchemy aggregation
    provider_ids = [p.id for p in providers_list]
    if provider_ids:
        counts_map = dict(
            db.session.query(Machinery.provider_id, func.count(Machinery.id))
            .filter(Machinery.provider_id.in_(provider_ids))
            .group_by(Machinery.provider_id)
            .all()
        )
    else:
        counts_map = {}

    provider_machinery_counts = {p.id: counts_map.get(p.id, 0) for p in providers_list}
    for p in providers_list:
        p.machinery_count = provider_machinery_counts[p.id]

    total_users = total_farmers + total_providers + (1 if user and user.role == "ADMIN" else 0)

    return render_template(
        "admin/dashboard.html",
        user=user,
        total_users=total_users,
        total_farmers=total_farmers,
        total_providers=total_providers,
        total_machinery=total_machinery,
        active_machinery=active_machinery,
        total_bookings=total_bookings,
        total_enquiries=total_enquiries,
        recent_enquiries=recent_enquiries,
        recent_bookings=recent_bookings,
        providers_list=providers_list,
        provider_machinery_counts=provider_machinery_counts,
    )
