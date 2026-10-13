from datetime import datetime
from flask import render_template, request, session, redirect, url_for, flash
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

        # Public registration cannot assign ADMIN role
        if role not in ("FARMER", "PROVIDER"):
            role = "FARMER"

        try:
            phone = normalize_phone_number(raw_phone)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("auth/register.html")

        # Check if phone is already registered and verified
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user and existing_user.is_phone_verified:
            flash("This mobile number is already registered. Please sign in.", "info")
            return redirect(url_for("auth.login"))

        # Request OTP
        success, msg = otp_service.request_otp(phone, purpose="REGISTER")
        if not success:
            flash(msg, "warning")
            return render_template("auth/register.html")

        # Save pending registration details into session for post-verification creation
        session["pending_registration"] = {
            "full_name": full_name,
            "phone": phone,
            "role": role,
            "preferred_language": preferred_language,
        }
        session.pop("pending_login_phone", None)

        flash(msg, "info")
        return redirect(url_for("auth.verify_otp"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Sign-in route supporting OTP (Farmers & Providers) and password (Admin/Staff)."""
    if session.get("user_id"):
        return redirect(url_for("auth.profile"))

    if request.method == "POST":
        login_type = request.form.get("login_type", "otp")
        raw_phone = request.form.get("phone")

        try:
            phone = normalize_phone_number(raw_phone)
        except ValueError as e:
            flash(str(e), "error")
            return render_template("auth/login.html")

        if login_type == "password":
            password = request.form.get("password") or ""
            user = User.query.filter_by(phone=phone).first()
            if user and user.check_password(password):
                if not user.is_active:
                    flash("This account is currently suspended. Please contact support.", "error")
                    return render_template("auth/login.html")
                user.last_login_at = datetime.utcnow()
                db.session.commit()
                login_user_session(user)
                flash(f"Welcome back, {user.full_name or 'Farmer'}!", "success")
                next_url = request.args.get("next")
                if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                    return redirect(next_url)
                return redirect(url_for("auth.profile"))
            else:
                flash("Invalid mobile number or password.", "error")
                return render_template("auth/login.html")

        # Default OTP login flow
        success, msg = otp_service.request_otp(phone, purpose="LOGIN")
        if not success:
            flash(msg, "warning")
            return render_template("auth/login.html")

        session["pending_login_phone"] = phone
        session.pop("pending_registration", None)
        flash(msg, "info")
        return redirect(url_for("auth.verify_otp"))

    return render_template("auth/login.html")


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
