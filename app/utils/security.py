import re
from functools import wraps
from flask import session, redirect, url_for, request, abort, flash
from app.models.user import User


def normalize_phone_number(raw_phone: str | None) -> str:
    """Normalize and validate Indian phone number to E.164 (+91XXXXXXXXXX) format.
    
    Accepts:
    - 9876543210 (10 digits starting with 6-9)
    - +919876543210
    - 919876543210
    - 09876543210
    
    Raises:
    - ValueError if the format is invalid or not a 10-digit mobile number.
    """
    if not raw_phone:
        raise ValueError("Phone number is required.")

    # Remove all whitespace, hyphens, parentheses, and dots
    cleaned = re.sub(r"[\s\-\(\)\.]", "", str(raw_phone).strip())

    # Strip leading +
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]

    # Remove leading 0 if present (e.g., STD-style 09876543210)
    if cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]

    # Strip country code 91 if 12 digits
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]

    # Must now be exactly 10 digits starting with 6, 7, 8, or 9
    if not re.match(r"^[6-9]\d{9}$", cleaned):
        raise ValueError("Enter a valid 10-digit Indian mobile number (starting with 6, 7, 8, or 9).")

    return f"+91{cleaned}"


def login_user_session(user: User) -> None:
    """Establish a secure, authenticated Flask session for a verified user."""
    # Prevent session fixation by resetting and storing session identity
    session.clear()
    session["user_id"] = str(user.id)
    session["user_role"] = user.role
    session["user_phone"] = user.phone
    session["user_name"] = user.full_name or "Farmer"
    session["lang"] = user.preferred_language or session.get("lang", "en")


def logout_user_session() -> None:
    """Clear session data on logout while preserving language preference."""
    saved_lang = session.get("lang", "en")
    session.clear()
    session["lang"] = saved_lang


import uuid
from app.extensions import db


def get_current_user() -> User | None:
    """Retrieve the currently authenticated User instance from session, if any."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    try:
        uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, AttributeError):
        return None
    return db.session.get(User, uid)


def login_required(f):
    """View decorator to enforce authenticated user session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def role_required(allowed_roles: list[str] | set[str] | str):
    """View decorator to enforce role-based access control (FARMER, PROVIDER, ADMIN)."""
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    allowed_set = set(allowed_roles)

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for("auth.login", next=request.path))
            
            user_role = session.get("user_role")
            if user_role not in allowed_set:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
