import pytest
from app.models.user import User, ProviderProfile
from app.models.otp import OTPVerification
from app.services.otp_service import otp_service
from app.extensions import db


def test_registration_and_otp_verification_flow(client, db_session):
    """Test full registration flow from form submit to OTP verification and session creation."""
    # 1. Submit Registration form
    reg_data = {
        "full_name": "Karthi Vel",
        "phone": "9876511111",
        "role": "FARMER",
        "preferred_language": "ta",
    }
    response = client.post("/auth/register", data=reg_data, follow_redirects=True)
    assert response.status_code == 200
    assert "verify-otp" in response.request.path

    # Check OTP record created in DB
    phone = "+919876511111"
    otp_record = OTPVerification.query.filter_by(phone=phone).first()
    assert otp_record is not None

    # Retrieve raw code via test helper
    raw_code = otp_service.generate_otp_code()
    from werkzeug.security import generate_password_hash
    otp_record.otp_hash = generate_password_hash(raw_code)
    db_session.commit()

    # 2. Submit OTP
    res_verify = client.post("/auth/verify-otp", data={"otp_code": raw_code}, follow_redirects=True)
    assert res_verify.status_code == 200

    # User must now exist in DB and be verified
    user = User.query.filter_by(phone=phone).first()
    assert user is not None
    assert user.full_name == "Karthi Vel"
    assert user.role == "FARMER"
    assert user.preferred_language == "ta"
    assert user.is_phone_verified is True

    # Authenticated session must be set
    with client.session_transaction() as sess:
        assert sess.get("user_id") == str(user.id)
        assert sess.get("user_role") == "FARMER"


def test_provider_registration_creates_profile(client, db_session):
    """Test registering as PROVIDER automatically initializes a ProviderProfile."""
    reg_data = {
        "full_name": "Selvam Tractor Owner",
        "phone": "9876522222",
        "role": "PROVIDER",
        "preferred_language": "en",
    }
    client.post("/auth/register", data=reg_data, follow_redirects=True)
    phone = "+919876522222"

    otp_record = OTPVerification.query.filter_by(phone=phone).first()
    raw_code = "654321"
    from werkzeug.security import generate_password_hash
    otp_record.otp_hash = generate_password_hash(raw_code)
    db_session.commit()

    client.post("/auth/verify-otp", data={"otp_code": raw_code}, follow_redirects=True)

    user = User.query.filter_by(phone=phone).first()
    assert user.role == "PROVIDER"
    assert user.provider_profile is not None
    assert "Selvam Tractor Owner" in user.provider_profile.business_name


def test_public_registration_cannot_grant_admin(client, db_session):
    """Verify that tampering role to ADMIN in registration is blocked."""
    reg_data = {
        "full_name": "Hacker",
        "phone": "9876533333",
        "role": "ADMIN",  # Attempt privilege escalation
    }
    client.post("/auth/register", data=reg_data, follow_redirects=True)
    phone = "+919876533333"

    otp_record = OTPVerification.query.filter_by(phone=phone).first()
    from werkzeug.security import generate_password_hash
    otp_record.otp_hash = generate_password_hash("112233")
    db_session.commit()

    client.post("/auth/verify-otp", data={"otp_code": "112233"}, follow_redirects=True)
    user = User.query.filter_by(phone=phone).first()
    assert user.role != "ADMIN"
    assert user.role == "FARMER"


def test_password_login_for_admin_or_staff(client, db_session):
    """Verify password sign-in for users with a password_hash."""
    phone = "+919876544444"
    admin = User(phone=phone, full_name="System Admin", role="ADMIN", is_phone_verified=True)
    admin.set_password("AdminSecurePass!99")
    db_session.add(admin)
    db_session.commit()

    # Submit password login
    res = client.post("/auth/login", data={
        "login_type": "password",
        "phone": phone,
        "password": "AdminSecurePass!99",
    }, follow_redirects=True)
    assert res.status_code == 200

    with client.session_transaction() as sess:
        assert sess.get("user_id") == str(admin.id)
        assert sess.get("user_role") == "ADMIN"


def test_logout_clears_session_via_post(client, db_session):
    """Verify POST /auth/logout terminates user session while preserving language preference."""
    phone = "+919876555555"
    user = User(phone=phone, full_name="Logout Test User", is_phone_verified=True)
    db_session.add(user)
    db_session.commit()

    # Log in user via session
    with client.session_transaction() as sess:
        sess["user_id"] = str(user.id)
        sess["user_role"] = user.role
        sess["lang"] = "ta"

    # POST logout
    res = client.post("/auth/logout", follow_redirects=True)
    assert res.status_code == 200

    with client.session_transaction() as sess:
        assert "user_id" not in sess
        assert sess.get("lang") == "ta"


def test_logout_rejects_get_method(client):
    """Verify GET /auth/logout is rejected with 405 Method Not Allowed."""
    res = client.get("/auth/logout")
    assert res.status_code == 405


def test_protected_profile_route_requires_login(client):
    """Verify unauthenticated access to /auth/profile redirects to /auth/login."""
    res = client.get("/auth/profile")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_csrf_protection_when_enabled(app, monkeypatch):
    """Verify that when WTF_CSRF_ENABLED is True, POST without CSRF token is rejected with 400."""
    with app.app_context():
        monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
        test_client = app.test_client()

        # POST login without CSRF token
        response_login = test_client.post("/auth/login", data={"phone": "9876500000"})
        assert response_login.status_code == 400
        assert "CSRF" in response_login.get_data(as_text=True)

        # POST logout without CSRF token
        response_logout = test_client.post("/auth/logout")
        assert response_logout.status_code == 400
        assert "CSRF" in response_logout.get_data(as_text=True)
