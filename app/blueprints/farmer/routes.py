from flask import render_template, request, redirect, url_for
from app.blueprints.farmer import farmer_bp
from app.models.booking import Booking
from app.models.machinery import Machinery
from app.blueprints.machinery.routes import get_starting_rate, get_primary_photo_url
from app.utils.geo import TAMIL_NADU_DISTRICTS, MACHINERY_CATEGORIES
from app.utils.security import login_required, role_required, get_current_user


@farmer_bp.route("/", methods=["GET"])
@farmer_bp.route("/dashboard", methods=["GET"])
@login_required
@role_required("FARMER")
def dashboard():
    """Farmer dashboard showcasing Search, Browse Listings, Rental Prices, Bookings, and Profile."""
    user = get_current_user()

    # Query all bookings placed by this farmer
    user_bookings = (
        Booking.query.filter_by(farmer_id=user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    # Booking counts
    active_count = sum(
        1 for b in user_bookings if b.status in [Booking.STATUS_APPROVED, Booking.STATUS_IN_PROGRESS]
    )
    pending_count = sum(1 for b in user_bookings if b.status == Booking.STATUS_PENDING)
    completed_count = sum(1 for b in user_bookings if b.status == Booking.STATUS_COMPLETED)
    total_bookings = len(user_bookings)

    recent_bookings = user_bookings[:5]

    # Query available active machinery listings for the browsing preview
    machinery_items = (
        Machinery.query.filter_by(is_active=True)
        .order_by(Machinery.created_at.desc())
        .limit(6)
        .all()
    )

    featured_machinery = []
    for m in machinery_items:
        rate_val, rate_unit = get_starting_rate(m)
        photo_url = get_primary_photo_url(m)
        featured_machinery.append({
            "machinery": m,
            "starting_rate": rate_val,
            "starting_unit": rate_unit,
            "primary_photo_url": photo_url,
        })

    return render_template(
        "farmer/dashboard.html",
        user=user,
        active_count=active_count,
        pending_count=pending_count,
        completed_count=completed_count,
        total_bookings=total_bookings,
        recent_bookings=recent_bookings,
        featured_machinery=featured_machinery,
        districts=TAMIL_NADU_DISTRICTS,
        categories=MACHINERY_CATEGORIES,
    )
