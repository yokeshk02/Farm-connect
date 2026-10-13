import os
from decimal import Decimal, InvalidOperation
from flask import render_template, request, redirect, url_for, flash, abort, current_app
from app.blueprints.provider import provider_bp
from app.extensions import db
from app.models.machinery import Machinery, MachineryPhoto, MachineryRate
from app.models.user import ProviderProfile
from app.services.image_service import validate_and_save_photo, MAX_PHOTOS_PER_MACHINERY
from app.utils.geo import TAMIL_NADU_DISTRICTS, MACHINERY_CATEGORIES, RENTAL_OPTIONS
from app.utils.security import login_required, role_required, get_current_user


def get_or_create_provider_profile(user) -> ProviderProfile:
    """Ensure the authenticated provider user has an initialized ProviderProfile record."""
    if not user.provider_profile:
        profile = ProviderProfile(
            user_id=user.id,
            business_name=f"{user.full_name or 'Farmer'}'s Equipment Services",
            verification_status="PENDING",
            whatsapp_enabled=False,
        )
        db.session.add(profile)
        db.session.commit()
        return profile
    return user.provider_profile


def parse_decimal_safe(val: str | None, default=None):
    """Safely parse input string to Decimal or None."""
    if val is None or str(val).strip() == "":
        return default
    try:
        dec = Decimal(str(val).strip())
        return dec
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid monetary rate value: '{val}'.")


@provider_bp.route("/machinery/", methods=["GET"])
@login_required
@role_required("PROVIDER")
def machinery_list():
    """Provider equipment dashboard listing all owned machinery."""
    user = get_current_user()
    profile = get_or_create_provider_profile(user)

    my_machinery = (
        Machinery.query.filter_by(provider_id=profile.id)
        .order_by(Machinery.created_at.desc())
        .all()
    )

    return render_template(
        "provider/machinery_list.html",
        machinery_list=my_machinery,
        profile=profile,
    )


@provider_bp.route("/machinery/new", methods=["GET", "POST"])
@login_required
@role_required("PROVIDER")
def machinery_new():
    """Create a new machinery listing with specifications, rate tiers, and photos."""
    user = get_current_user()
    profile = get_or_create_provider_profile(user)

    if request.method == "POST":
        name_en = (request.form.get("name_en") or "").strip()
        name_ta = (request.form.get("name_ta") or "").strip()
        category = (request.form.get("category") or "").strip().upper()
        make_model = (request.form.get("make_model") or "").strip()
        model_year_raw = (request.form.get("model_year") or "").strip()
        horsepower_raw = (request.form.get("horsepower") or "").strip()
        desc_en = (request.form.get("description_en") or "").strip()
        desc_ta = (request.form.get("description_ta") or "").strip()

        village = (request.form.get("village_or_town") or "").strip()
        district = (request.form.get("district") or "").strip()
        pincode = (request.form.get("pincode") or "").strip()

        # Input validations
        errors = []
        if not name_en or len(name_en) < 2:
            errors.append("Equipment name in English is required (at least 2 characters).")

        if not category or category not in MACHINERY_CATEGORIES:
            errors.append(f"Please select a valid category from {', '.join(MACHINERY_CATEGORIES)}.")

        if not village:
            errors.append("Village or Town is required.")

        if not district or district not in TAMIL_NADU_DISTRICTS:
            errors.append("Please select a valid District from Tamil Nadu.")

        if not pincode or len(pincode) != 6 or not pincode.isdigit():
            errors.append("PIN Code must be a 6-digit number.")

        model_year = None
        if model_year_raw:
            try:
                model_year = int(model_year_raw)
                if model_year < 1950 or model_year > 2035:
                    errors.append("Model year must be between 1950 and 2035.")
            except ValueError:
                errors.append("Model year must be a valid integer.")

        horsepower = None
        if horsepower_raw:
            try:
                horsepower = int(horsepower_raw)
                if horsepower <= 0:
                    errors.append("Horsepower must be a positive integer.")
            except ValueError:
                errors.append("Horsepower must be a valid integer.")

        # Rate packages extraction and validation
        rates_to_create = []
        has_at_least_one_valid_package = False

        for opt in RENTAL_OPTIONS:
            prefix = opt.lower()
            hr_rate_str = request.form.get(f"{prefix}_hour")
            day_rate_str = request.form.get(f"{prefix}_day")
            min_hrs_str = request.form.get(f"{prefix}_min_hours") or "1"
            deposit_str = request.form.get(f"{prefix}_deposit") or "0"

            if hr_rate_str or day_rate_str:
                try:
                    hr_rate = parse_decimal_safe(hr_rate_str)
                    day_rate = parse_decimal_safe(day_rate_str)
                    min_hrs = int(min_hrs_str)
                    deposit = parse_decimal_safe(deposit_str, default=Decimal("0.00"))

                    if hr_rate is not None and hr_rate < 0:
                        errors.append(f"Hourly rate for {opt} cannot be negative.")
                    if day_rate is not None and day_rate < 0:
                        errors.append(f"Daily rate for {opt} cannot be negative.")
                    if min_hrs < 1:
                        errors.append(f"Minimum booking duration for {opt} must be at least 1 hour.")
                    if deposit is not None and deposit < 0:
                        errors.append(f"Security deposit for {opt} cannot be negative.")

                    if (hr_rate is not None and hr_rate > 0) or (day_rate is not None and day_rate > 0):
                        has_at_least_one_valid_package = True
                        rates_to_create.append({
                            "type": opt,
                            "hr": hr_rate,
                            "day": day_rate,
                            "min_hrs": min_hrs,
                            "deposit": deposit or Decimal("0.00"),
                        })
                except ValueError as ve:
                    errors.append(str(ve))

        if not has_at_least_one_valid_package:
            errors.append("Please configure at least one rental package with a positive hourly or daily rate.")

        # Photos validation
        uploaded_files = request.files.getlist("photos")
        valid_files = [f for f in uploaded_files if f and f.filename]
        if len(valid_files) > MAX_PHOTOS_PER_MACHINERY:
            errors.append(f"You can upload a maximum of {MAX_PHOTOS_PER_MACHINERY} photos.")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template(
                "provider/machinery_form.html",
                is_edit=False,
                districts=TAMIL_NADU_DISTRICTS,
                categories=MACHINERY_CATEGORIES,
                form_data=request.form,
            )

        # Create machinery listing in transaction
        try:
            machinery = Machinery(
                provider_id=profile.id,
                name_en=name_en,
                name_ta=name_ta or None,
                category=category,
                make_model=make_model or None,
                model_year=model_year,
                horsepower=horsepower,
                description_en=desc_en or None,
                description_ta=desc_ta or None,
                village_or_town=village,
                district=district,
                pincode=pincode,
                is_active=True,
            )
            db.session.add(machinery)
            db.session.flush()

            # Attach rates
            for rdata in rates_to_create:
                mrate = MachineryRate(
                    machinery_id=machinery.id,
                    rental_option_type=rdata["type"],
                    rate_per_hour=rdata["hr"],
                    rate_per_day=rdata["day"],
                    min_booking_duration_hours=rdata["min_hrs"],
                    security_deposit=rdata["deposit"],
                )
                db.session.add(mrate)

            # Process photo uploads
            upload_dir = os.path.join(current_app.root_path, "static", "uploads", "machinery")
            for idx, file_obj in enumerate(valid_files):
                photo_url = validate_and_save_photo(file_obj, upload_dir)
                photo_rec = MachineryPhoto(
                    machinery_id=machinery.id,
                    photo_url=photo_url,
                    is_primary=(idx == 0),
                    display_order=idx,
                )
                db.session.add(photo_rec)

            db.session.commit()
            flash("Machinery listing created successfully!", "success")
            return redirect(url_for("provider.machinery_list"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create machinery listing: {e}")
            flash(f"Error saving listing: {str(e)}", "error")
            return render_template(
                "provider/machinery_form.html",
                is_edit=False,
                districts=TAMIL_NADU_DISTRICTS,
                categories=MACHINERY_CATEGORIES,
                form_data=request.form,
            )

    return render_template(
        "provider/machinery_form.html",
        is_edit=False,
        districts=TAMIL_NADU_DISTRICTS,
        categories=MACHINERY_CATEGORIES,
        form_data={},
    )


@provider_bp.route("/machinery/<uuid:machinery_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("PROVIDER")
def machinery_edit(machinery_id):
    """Edit an existing machinery listing owned by the authenticated provider."""
    user = get_current_user()
    profile = get_or_create_provider_profile(user)

    machinery = db.session.get(Machinery, machinery_id)
    if not machinery:
        abort(404)

    # Resource ownership check: Provider can only edit their own listings
    if machinery.provider_id != profile.id:
        abort(403)

    if request.method == "POST":
        name_en = (request.form.get("name_en") or "").strip()
        name_ta = (request.form.get("name_ta") or "").strip()
        category = (request.form.get("category") or "").strip().upper()
        make_model = (request.form.get("make_model") or "").strip()
        model_year_raw = (request.form.get("model_year") or "").strip()
        horsepower_raw = (request.form.get("horsepower") or "").strip()
        desc_en = (request.form.get("description_en") or "").strip()
        desc_ta = (request.form.get("description_ta") or "").strip()

        village = (request.form.get("village_or_town") or "").strip()
        district = (request.form.get("district") or "").strip()
        pincode = (request.form.get("pincode") or "").strip()

        errors = []
        if not name_en or len(name_en) < 2:
            errors.append("Equipment name in English is required (at least 2 characters).")

        if not category or category not in MACHINERY_CATEGORIES:
            errors.append(f"Please select a valid category from {', '.join(MACHINERY_CATEGORIES)}.")

        if not village:
            errors.append("Village or Town is required.")

        if not district or district not in TAMIL_NADU_DISTRICTS:
            errors.append("Please select a valid District from Tamil Nadu.")

        if not pincode or len(pincode) != 6 or not pincode.isdigit():
            errors.append("PIN Code must be a 6-digit number.")

        model_year = None
        if model_year_raw:
            try:
                model_year = int(model_year_raw)
                if model_year < 1950 or model_year > 2035:
                    errors.append("Model year must be between 1950 and 2035.")
            except ValueError:
                errors.append("Model year must be a valid integer.")

        horsepower = None
        if horsepower_raw:
            try:
                horsepower = int(horsepower_raw)
                if horsepower <= 0:
                    errors.append("Horsepower must be a positive integer.")
            except ValueError:
                errors.append("Horsepower must be a valid integer.")

        # Rate packages extraction and validation
        rates_to_update = []
        has_at_least_one_valid_package = False

        for opt in RENTAL_OPTIONS:
            prefix = opt.lower()
            hr_rate_str = request.form.get(f"{prefix}_hour")
            day_rate_str = request.form.get(f"{prefix}_day")
            min_hrs_str = request.form.get(f"{prefix}_min_hours") or "1"
            deposit_str = request.form.get(f"{prefix}_deposit") or "0"

            if hr_rate_str or day_rate_str:
                try:
                    hr_rate = parse_decimal_safe(hr_rate_str)
                    day_rate = parse_decimal_safe(day_rate_str)
                    min_hrs = int(min_hrs_str)
                    deposit = parse_decimal_safe(deposit_str, default=Decimal("0.00"))

                    if hr_rate is not None and hr_rate < 0:
                        errors.append(f"Hourly rate for {opt} cannot be negative.")
                    if day_rate is not None and day_rate < 0:
                        errors.append(f"Daily rate for {opt} cannot be negative.")
                    if min_hrs < 1:
                        errors.append(f"Minimum booking duration for {opt} must be at least 1 hour.")
                    if deposit is not None and deposit < 0:
                        errors.append(f"Security deposit for {opt} cannot be negative.")

                    if (hr_rate is not None and hr_rate > 0) or (day_rate is not None and day_rate > 0):
                        has_at_least_one_valid_package = True
                        rates_to_update.append({
                            "type": opt,
                            "hr": hr_rate,
                            "day": day_rate,
                            "min_hrs": min_hrs,
                            "deposit": deposit or Decimal("0.00"),
                        })
                except ValueError as ve:
                    errors.append(str(ve))

        if not has_at_least_one_valid_package:
            errors.append("Please configure at least one rental package with a positive hourly or daily rate.")

        # Photos count check (existing + new <= 5)
        new_files = [f for f in request.files.getlist("photos") if f and f.filename]
        existing_photos_count = len(machinery.photos)
        if existing_photos_count + len(new_files) > MAX_PHOTOS_PER_MACHINERY:
            errors.append(
                f"Total photos cannot exceed {MAX_PHOTOS_PER_MACHINERY}. "
                f"You currently have {existing_photos_count} photo(s)."
            )

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template(
                "provider/machinery_form.html",
                is_edit=True,
                machinery=machinery,
                districts=TAMIL_NADU_DISTRICTS,
                categories=MACHINERY_CATEGORIES,
                form_data=request.form,
            )

        try:
            # Update basic attributes
            machinery.name_en = name_en
            machinery.name_ta = name_ta or None
            machinery.category = category
            machinery.make_model = make_model or None
            machinery.model_year = model_year
            machinery.horsepower = horsepower
            machinery.description_en = desc_en or None
            machinery.description_ta = desc_ta or None
            machinery.village_or_town = village
            machinery.district = district
            machinery.pincode = pincode

            # Replace or update rates
            MachineryRate.query.filter_by(machinery_id=machinery.id).delete()
            for rdata in rates_to_update:
                mrate = MachineryRate(
                    machinery_id=machinery.id,
                    rental_option_type=rdata["type"],
                    rate_per_hour=rdata["hr"],
                    rate_per_day=rdata["day"],
                    min_booking_duration_hours=rdata["min_hrs"],
                    security_deposit=rdata["deposit"],
                )
                db.session.add(mrate)

            # Save new photos if any
            upload_dir = os.path.join(current_app.root_path, "static", "uploads", "machinery")
            start_order = existing_photos_count
            for idx, file_obj in enumerate(new_files):
                photo_url = validate_and_save_photo(file_obj, upload_dir)
                photo_rec = MachineryPhoto(
                    machinery_id=machinery.id,
                    photo_url=photo_url,
                    is_primary=(existing_photos_count == 0 and idx == 0),
                    display_order=start_order + idx,
                )
                db.session.add(photo_rec)

            db.session.commit()
            flash("Machinery listing updated successfully!", "success")
            return redirect(url_for("provider.machinery_list"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to update machinery listing: {e}")
            flash(f"Error updating listing: {str(e)}", "error")

    # Prepare form_data from existing machinery
    existing_rates = {r.rental_option_type: r for r in machinery.rates}
    form_data = {
        "name_en": machinery.name_en,
        "name_ta": machinery.name_ta or "",
        "category": machinery.category,
        "make_model": machinery.make_model or "",
        "model_year": machinery.model_year or "",
        "horsepower": machinery.horsepower or "",
        "description_en": machinery.description_en or "",
        "description_ta": machinery.description_ta or "",
        "village_or_town": machinery.village_or_town,
        "district": machinery.district,
        "pincode": machinery.pincode,
    }
    for opt in RENTAL_OPTIONS:
        prefix = opt.lower()
        rate_obj = existing_rates.get(opt)
        if rate_obj:
            form_data[f"{prefix}_hour"] = rate_obj.rate_per_hour or ""
            form_data[f"{prefix}_day"] = rate_obj.rate_per_day or ""
            form_data[f"{prefix}_min_hours"] = rate_obj.min_booking_duration_hours
            form_data[f"{prefix}_deposit"] = rate_obj.security_deposit

    return render_template(
        "provider/machinery_form.html",
        is_edit=True,
        machinery=machinery,
        districts=TAMIL_NADU_DISTRICTS,
        categories=MACHINERY_CATEGORIES,
        form_data=form_data,
    )


@provider_bp.route("/machinery/<uuid:machinery_id>/toggle-status", methods=["POST"])
@login_required
@role_required("PROVIDER")
def machinery_toggle_status(machinery_id):
    """Toggle listing between active and inactive without permanently deleting data."""
    user = get_current_user()
    profile = get_or_create_provider_profile(user)

    machinery = db.session.get(Machinery, machinery_id)
    if not machinery:
        abort(404)

    # Ownership check
    if machinery.provider_id != profile.id:
        abort(403)

    machinery.is_active = not machinery.is_active
    db.session.commit()

    status_str = "activated" if machinery.is_active else "deactivated"
    flash(f"Listing '{machinery.name_en}' has been {status_str}.", "info")
    return redirect(url_for("provider.machinery_list"))


@provider_bp.route("/machinery/<uuid:machinery_id>/photos/<uuid:photo_id>/delete", methods=["POST"])
@login_required
@role_required("PROVIDER")
def machinery_photo_delete(machinery_id, photo_id):
    """Delete a photo from a machinery listing owned by the provider."""
    user = get_current_user()
    profile = get_or_create_provider_profile(user)

    machinery = db.session.get(Machinery, machinery_id)
    if not machinery:
        abort(404)

    if machinery.provider_id != profile.id:
        abort(403)

    photo = db.session.get(MachineryPhoto, photo_id)
    if not photo or photo.machinery_id != machinery.id:
        abort(404)

    # Try removing file from filesystem
    try:
        if photo.photo_url.startswith("/static/"):
            rel_path = photo.photo_url.lstrip("/")
            full_path = os.path.join(current_app.root_path, rel_path)
            if os.path.exists(full_path):
                os.remove(full_path)
    except Exception as e:
        current_app.logger.warning(f"Could not remove image file from disk: {e}")

    db.session.delete(photo)
    db.session.commit()

    # If deleted photo was primary, assign primary to first remaining photo
    remaining = MachineryPhoto.query.filter_by(machinery_id=machinery.id).order_by(MachineryPhoto.display_order).first()
    if remaining and not any(p.is_primary for p in machinery.photos):
        remaining.is_primary = True
        db.session.commit()

    flash("Photo deleted successfully.", "info")
    return redirect(url_for("provider.machinery_edit", machinery_id=machinery.id))
