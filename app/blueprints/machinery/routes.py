import math
from flask import render_template, request, abort, session
from sqlalchemy import or_

from app.blueprints.machinery import machinery_bp
from app.extensions import db
from app.models.machinery import Machinery, MachineryPhoto, MachineryRate
from app.utils.geo import TAMIL_NADU_DISTRICTS, MACHINERY_CATEGORIES, RENTAL_OPTIONS, haversine_distance
from app.utils.security import get_current_user


def get_starting_rate(machinery: Machinery):
    """Calculate the lowest available rate for display on cards."""
    hourly_rates = [float(r.rate_per_hour) for r in machinery.rates if r.rate_per_hour is not None]
    if hourly_rates:
        return min(hourly_rates), "hr"
    daily_rates = [float(r.rate_per_day) for r in machinery.rates if r.rate_per_day is not None]
    if daily_rates:
        return min(daily_rates), "day"
    return None, None


def get_primary_photo_url(machinery: Machinery) -> str:
    """Return the primary photo URL or first available photo, else fallback placeholder."""
    for photo in machinery.photos:
        if photo.is_primary:
            return photo.photo_url
    if machinery.photos:
        return machinery.photos[0].photo_url
    return "/static/images/placeholder_machinery.svg"


@machinery_bp.route("/", methods=["GET"])
def catalogue():
    """Public agricultural equipment catalogue with search, location filters, and optional GPS."""
    # Query parameters
    search_query = (request.args.get("q") or "").strip()
    selected_district = (request.args.get("district") or "").strip()
    selected_village = (request.args.get("village") or "").strip()
    selected_pincode = (request.args.get("pincode") or "").strip()
    selected_category = (request.args.get("category") or "").strip().upper()
    selected_package = (request.args.get("package") or "").strip().upper()
    sort_by = (request.args.get("sort") or "newest").strip().lower()

    # User coordinates from optional browser GPS
    user_lat = request.args.get("lat", type=float)
    user_lng = request.args.get("lng", type=float)

    # Base query: only active listings
    query = Machinery.query.filter(Machinery.is_active.is_(True))

    # Text search
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                Machinery.name_en.ilike(search_pattern),
                Machinery.name_ta.ilike(search_pattern),
                Machinery.make_model.ilike(search_pattern),
                Machinery.description_en.ilike(search_pattern),
                Machinery.description_ta.ilike(search_pattern),
            )
        )

    # Location filters
    if selected_district:
        query = query.filter(Machinery.district.ilike(selected_district))

    if selected_village:
        query = query.filter(Machinery.village_or_town.ilike(f"%{selected_village}%"))

    if selected_pincode:
        query = query.filter(Machinery.pincode == selected_pincode)

    # Category filter
    if selected_category and selected_category in MACHINERY_CATEGORIES:
        query = query.filter(Machinery.category == selected_category)

    # Package filter
    if selected_package and selected_package in RENTAL_OPTIONS:
        query = query.filter(Machinery.rates.any(MachineryRate.rental_option_type == selected_package))

    items = query.all()

    # Decorate items with presentation properties
    decorated_items = []
    has_gps = user_lat is not None and user_lng is not None

    for item in items:
        rate_val, rate_unit = get_starting_rate(item)
        photo_url = get_primary_photo_url(item)

        distance_km = None
        if has_gps and item.latitude is not None and item.longitude is not None:
            distance_km = haversine_distance(user_lat, user_lng, float(item.latitude), float(item.longitude))

        decorated_items.append({
            "machinery": item,
            "starting_rate": rate_val,
            "starting_unit": rate_unit,
            "primary_photo_url": photo_url,
            "distance_km": distance_km,
        })

    # Sorting
    if sort_by == "distance" and has_gps:
        decorated_items.sort(key=lambda x: (x["distance_km"] is None, x["distance_km"] or 999999))
    elif sort_by == "price_asc":
        decorated_items.sort(key=lambda x: (x["starting_rate"] is None, x["starting_rate"] or 999999))
    elif sort_by == "price_desc":
        decorated_items.sort(key=lambda x: (x["starting_rate"] is None, -(x["starting_rate"] or 0)))
    else:
        # Default newest first
        decorated_items.sort(key=lambda x: x["machinery"].created_at, reverse=True)

    # Pagination
    page = max(1, request.args.get("page", 1, type=int))
    per_page = 9
    total_count = len(decorated_items)
    total_pages = max(1, math.ceil(total_count / per_page))
    if page > total_pages:
        page = total_pages

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paged_items = decorated_items[start_idx:end_idx]

    pagination = {
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1,
        "next_page": page + 1,
    }

    return render_template(
        "machinery/index.html",
        items=paged_items,
        pagination=pagination,
        districts=TAMIL_NADU_DISTRICTS,
        categories=MACHINERY_CATEGORIES,
        packages=RENTAL_OPTIONS,
        q=search_query,
        district=selected_district,
        village=selected_village,
        pincode=selected_pincode,
        category=selected_category,
        package=selected_package,
        sort=sort_by,
        user_lat=user_lat,
        user_lng=user_lng,
    )


@machinery_bp.route("/<uuid:machinery_id>", methods=["GET"])
def detail(machinery_id):
    """Machinery listing details page with specifications, gallery, rate tiers, and provider info."""
    machinery = db.session.get(Machinery, machinery_id)
    if not machinery:
        abort(404)

    # If inactive, only the owner can preview it
    if not machinery.is_active:
        user = get_current_user()
        is_owner = (
            user
            and user.role == "PROVIDER"
            and user.provider_profile
            and user.provider_profile.id == machinery.provider_id
        )
        if not is_owner:
            abort(404)

    # Organize rate tiers
    rates_by_type = {rate.rental_option_type: rate for rate in machinery.rates}

    return render_template(
        "machinery/detail.html",
        machinery=machinery,
        provider=machinery.provider,
        rates_by_type=rates_by_type,
        photos=machinery.photos,
    )
