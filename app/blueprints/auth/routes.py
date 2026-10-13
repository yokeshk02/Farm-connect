from datetime import datetime
from flask import render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from app.blueprints.auth import auth_bp
from app.extensions import db
from app.models.user import User, ProviderProfile
from app.services.otp_service import otp_service
from app.utils.security import (
    normalize_phone_number,
    login_user_session,
    logout_user_session,
    get_current_user,
    login_required,
    validate_password_strength,
    record_password_failure,
    is_password_rate_limited,
    clear_password_failures,
    is_safe_redirect_url,
)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration flow for Farmers and Machinery Providers."""
    if session.get("user_id"):
        return redirect(url_for("auth.profile"))

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        raw_phone = request.form.get("phone")
        role = (request.form.get("role") or "FARMER").upper()
        preferred_language = request.form.get("preferred_language") or session.get("lang", "en")
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        # Public registration cannot assign ADMIN role
        if role not in ("FARMER", "PROVIDER"):
            role = "FARMER"

        try:
            phone = normalize_phone_number(raw_phone)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("auth/register.html", form_data=request.form)

        # Password validation if provided
        password_hash = None
        if password or confirm_password:
            valid, err = validate_password_strength(password)
            if not valid:
                flash(err, "error")
                return render_template("auth/register.html", form_data=request.form)
            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return render_template("auth/register.html", form_data=request.form)
            password_hash = generate_password_hash(password)

        # Check if phone is already registered and verified
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user and existing_user.is_phone_verified:
            flash("This mobile number is already registered. Please sign in.", "info")
            return redirect(url_for("auth.login"))

        action = request.form.get("action", "verify_otp")

        if action == "save_signin":
            if not password:
                flash("Please provide a password to save and sign in directly.", "error")
                return render_template("auth/register.html", form_data=request.form)

            # Direct password creation: Account is created with is_phone_verified=False
            if existing_user:
                user = existing_user
                user.full_name = full_name
                user.role = role
                user.preferred_language = preferred_language
                user.password_hash = password_hash
            else:
                user = User(
                    phone=phone,
                    full_name=full_name,
                    role=role,
                    preferred_language=preferred_language,
                    password_hash=password_hash,
                    is_phone_verified=False,
                )
                db.session.add(user)
                db.session.flush()

                if role == "PROVIDER":
                    profile = ProviderProfile(
                        user_id=user.id,
                        business_name=f"{full_name}'s Equipment Services",
                        verification_status="PENDING",
                    )
                    db.session.add(profile)

            db.session.commit()
            login_user_session(user)
            flash("Account registered successfully! Note: Mobile verification is required for rental bookings and machinery management.", "info")
            if user.role == "PROVIDER":
                return redirect(url_for("provider.dashboard"))
            return redirect(url_for("auth.profile"))

        # Default: Continue to Phone Verification (OTP)
        success, msg = otp_service.request_otp(phone, purpose="REGISTER")
        if not success:
            flash(msg, "warning")
            return render_template("auth/register.html", form_data=request.form)

        # Save pending registration details into session for post-verification creation
        session["pending_registration"] = {
            "full_name": full_name,
            "phone": phone,
            "role": role,
            "preferred_language": preferred_language,
            "password_hash": password_hash,
        }
        session.pop("pending_login_phone", None)

        flash(msg, "info")
        return redirect(url_for("auth.verify_otp"))

    return render_template("auth/register.html", form_data={})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Sign-in route supporting OTP and password authentication."""
    if session.get("user_id"):
        return redirect(url_for("auth.profile"))

    active_tab = request.args.get("tab") or "otp"
    phone_val = ""

    if request.method == "POST":
        login_type = request.form.get("login_type", "otp")
        active_tab = login_type
        raw_phone = request.form.get("phone")
        phone_val = raw_phone or ""

        try:
            phone = normalize_phone_number(raw_phone)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("auth/login.html", active_tab=active_tab, phone=phone_val)

        if login_type == "password":
            if is_password_rate_limited(phone):
                flash("Too many failed login attempts. Please wait 15 minutes or sign in using OTP.", "error")
                return render_template("auth/login.html", active_tab="password", phone=phone_val)

            password = request.form.get("password") or ""
            user = User.query.filter_by(phone=phone).first()

            if user and user.password_hash and user.check_password(password):
                if not user.is_active:
                    flash("This account is currently suspended. Please contact support.", "error")
                    return render_template("auth/login.html", active_tab="password", phone=phone_val)

                clear_password_failures(phone)
                user.last_login_at = datetime.utcnow()
                db.session.commit()
                login_user_session(user)
                flash(f"Welcome back, {user.full_name or 'Farmer'}!", "success")

                next_url = request.args.get("next") or request.form.get("next")
                if is_safe_redirect_url(next_url):
                    return redirect(next_url)
                if user.role == "PROVIDER":
                    return redirect(url_for("provider.dashboard"))
                return redirect(url_for("auth.profile"))
            else:
                record_password_failure(phone)
                flash("Invalid mobile number or password.", "error")
                return render_template("auth/login.html", active_tab="password", phone=phone_val)

        # Default OTP login flow
        success, msg = otp_service.request_otp(phone, purpose="LOGIN")
        if not success:
            flash(msg, "warning")
            return render_template("auth/login.html", active_tab="otp", phone=phone_val)

        session["pending_login_phone"] = phone
        session.pop("pending_registration", None)
        flash(msg, "info")
        return redirect(url_for("auth.verify_otp"))

    return render_template("auth/login.html", active_tab=active_tab, phone=phone_val)


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    """Submit and validate the 6-digit OTP code."""
    # Determine pending phone from either registration or login context
    pending_reg = session.get("pending_registration")
    pending_phone = pending_reg.get("phone") if pending_reg else session.get("pending_login_phone")

    if not pending_phone:
        flash("No active verification request found. Please start by signing in.", "info")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        otp_code = request.form.get("otp_code", "").strip()

        success, msg = otp_service.verify_otp(pending_phone, otp_code)
        if not success:
            flash(msg, "error")
            return render_template("auth/verify_otp.html", pending_phone=pending_phone)

        # Successful verification: finalize registration or login
        if pending_reg:
            user = User.query.filter_by(phone=pending_phone).first()
            if not user:
                user = User(
                    phone=pending_phone,
                    full_name=pending_reg.get("full_name"),
                    role=pending_reg.get("role", "FARMER"),
                    preferred_language=pending_reg.get("preferred_language", "en"),
                    password_hash=pending_reg.get("password_hash"),
                    is_phone_verified=True,
                    is_active=True,
                    last_login_at=datetime.utcnow(),
                )
                db.session.add(user)
                db.session.flush()

                # If registering as provider, initialize provider profile
                if user.role == "PROVIDER":
                    profile = ProviderProfile(
                        user_id=user.id,
                        business_name=f"{user.full_name}'s Equipment Services",
                        whatsapp_enabled=False,
                    )
                    db.session.add(profile)
            else:
                user.full_name = pending_reg.get("full_name") or user.full_name
                user.role = pending_reg.get("role") or user.role
                if pending_reg.get("password_hash"):
                    user.password_hash = pending_reg.get("password_hash")
                user.is_phone_verified = True
                user.last_login_at = datetime.utcnow()

            db.session.commit()
            session.pop("pending_registration", None)
            login_user_session(user)
            flash("Phone verification successful! Welcome to FarmConnect.", "success")
            return redirect(url_for("auth.profile"))

        else:
            # Login verification
            user = User.query.filter_by(phone=pending_phone).first()
            if not user:
                # First-time OTP sign in defaults to Farmer
                user = User(
                    phone=pending_phone,
                    role="FARMER",
                    is_phone_verified=True,
                    is_active=True,
                    last_login_at=datetime.utcnow(),
                )
                db.session.add(user)
            else:
                user.is_phone_verified = True
                user.last_login_at = datetime.utcnow()

            db.session.commit()
            session.pop("pending_login_phone", None)
            login_user_session(user)
            flash("Signed in successfully!", "success")
            return redirect(url_for("auth.profile"))

    return render_template("auth/verify_otp.html", pending_phone=pending_phone)


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    """Resend a new OTP token subject to cooldown and rate limiting."""
    pending_reg = session.get("pending_registration")
    pending_phone = pending_reg.get("phone") if pending_reg else session.get("pending_login_phone")

    if not pending_phone:
        flash("No active session to resend OTP. Please sign in.", "warning")
        return redirect(url_for("auth.login"))

    purpose = "REGISTER" if pending_reg else "LOGIN"
    success, msg = otp_service.request_otp(pending_phone, purpose=purpose)
    if success:
        flash(msg, "info")
    else:
        flash(msg, "warning")

    return redirect(url_for("auth.verify_otp"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """End the user session via POST with CSRF validation."""
    logout_user_session()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile page allowing review and update of display name and language."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        preferred_language = request.form.get("preferred_language") or "en"

        if full_name:
            user.full_name = full_name
        if preferred_language in ("en", "ta"):
            user.preferred_language = preferred_language
            session["lang"] = preferred_language

        db.session.commit()
        session["user_name"] = user.full_name
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", user=user)


@auth_bp.route("/set-password", methods=["POST"])
@login_required
def set_password():
    """Allow authenticated users to establish or update their account password."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    # If user already has a password, current password must match
    if user.password_hash:
        if not current_password or not user.check_password(current_password):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("auth.profile"))

    # Validate new password
    valid, err = validate_password_strength(new_password)
    if not valid:
        flash(err, "error")
        return redirect(url_for("auth.profile"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for("auth.profile"))

    user.set_password(new_password)
    db.session.commit()
    flash("Password updated successfully! You can now use it to sign in.", "success")
    return redirect(url_for("auth.profile"))

