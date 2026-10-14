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


def test_login_page_renders_otp_and_password_options(client):
    """Verify login page displays both Login with OTP and Login with Password tabs and controls."""
    res = client.get("/auth/login")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Verify both tabs exist
    assert "Login with OTP" in html
    assert "Login with Password" in html
    assert "tabOtpLink" in html
    assert "tabPassLink" in html

    # Verify password input and show/hide control
    assert "passwordInput" in html
    assert "togglePasswordBtn" in html

    # Verify guidance message for users without a password
    assert "auth-guidance-box" in html
    assert "Haven't set a password yet" in html or "Login with OTP" in html


def test_registration_with_password_creation(client, db_session):
    """Verify that registering with a password stores only a secure hash and never plaintext."""
    phone = "9876566666"
    reg_data = {
        "full_name": "Ravi Farmer",
        "phone": phone,
        "role": "FARMER",
        "preferred_language": "en",
        "password": "RaviSecurePassword#1",
        "confirm_password": "RaviSecurePassword#1",
    }
    res = client.post("/auth/register", data=reg_data, follow_redirects=True)
    assert res.status_code == 200
    assert "verify-otp" in res.request.path

    # Simulate OTP verification
    formatted_phone = "+919876566666"
    otp_record = OTPVerification.query.filter_by(phone=formatted_phone).first()
    assert otp_record is not None
    from werkzeug.security import generate_password_hash
    otp_record.otp_hash = generate_password_hash("998877")
    db_session.commit()

    res_verify = client.post("/auth/verify-otp", data={"otp_code": "998877"}, follow_redirects=True)
    assert res_verify.status_code == 200

    user = User.query.filter_by(phone=formatted_phone).first()
    assert user is not None
    # Password must be hashed and never stored in plaintext
    assert user.password_hash is not None
    assert user.password_hash != "RaviSecurePassword#1"
    assert user.check_password("RaviSecurePassword#1") is True
    assert user.check_password("WrongPassword") is False


def test_registration_password_validation(client):
    """Verify password length and confirmation checks during registration."""
    # 1. Short password (< 6 chars)
    res_short = client.post("/auth/register", data={
        "full_name": "Test Short",
        "phone": "9876577777",
        "role": "FARMER",
        "password": "123",
        "confirm_password": "123",
    })
    assert res_short.status_code == 200
    assert "at least 6 characters" in res_short.data.decode("utf-8")

    # 2. Mismatched passwords
    res_mismatch = client.post("/auth/register", data={
        "full_name": "Test Mismatch",
        "phone": "9876577777",
        "role": "FARMER",
        "password": "Password1",
        "confirm_password": "Password2",
    })
    assert res_mismatch.status_code == 200
    assert "do not match" in res_mismatch.data.decode("utf-8")


def test_password_login_for_farmer_and_provider(client, db_session):
    """Verify that eligible farmers and providers can sign in using phone and password."""
    # Farmer
    farmer_phone = "+919876588888"
    farmer = User(phone=farmer_phone, full_name="Farmer Babu", role="FARMER", is_phone_verified=True)
    farmer.set_password("FarmerSecretPass1")
    db_session.add(farmer)

    # Provider
    provider_phone = "+919876599999"
    provider_user = User(phone=provider_phone, full_name="Provider Rajan", role="PROVIDER", is_phone_verified=True)
    provider_user.set_password("ProviderSecretPass1")
    db_session.add(provider_user)
    db_session.commit()

    # Provider profile
    profile = ProviderProfile(user_id=provider_user.id, business_name="Rajan Motors")
    db_session.add(profile)
    db_session.commit()

    # 1. Farmer password login
    res_farmer = client.post("/auth/login", data={
        "login_type": "password",
        "phone": farmer_phone,
        "password": "FarmerSecretPass1",
    }, follow_redirects=True)
    assert res_farmer.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get("user_id") == str(farmer.id)
        assert sess.get("user_role") == "FARMER"

    # Logout
    client.post("/auth/logout", follow_redirects=True)

    # 2. Provider password login
    res_provider = client.post("/auth/login", data={
        "login_type": "password",
        "phone": provider_phone,
        "password": "ProviderSecretPass1",
    }, follow_redirects=True)
    assert res_provider.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get("user_id") == str(provider_user.id)
        assert sess.get("user_role") == "PROVIDER"


def test_password_login_generic_failure_messages(client, db_session):
    """Verify login failure returns generic message without revealing account existence or password status."""
    # 1. Unknown phone number
    res_unknown = client.post("/auth/login", data={
        "login_type": "password",
        "phone": "9876501234",
        "password": "SomePassword123",
    })
    assert res_unknown.status_code == 200
    assert "Invalid mobile number or password." in res_unknown.data.decode("utf-8")

    # 2. Existing user with wrong password
    phone = "+919876501111"
    user_with_pass = User(phone=phone, full_name="User With Pass", role="FARMER", is_phone_verified=True)
    user_with_pass.set_password("CorrectPassword123")
    db_session.add(user_with_pass)
    db_session.commit()

    res_wrong = client.post("/auth/login", data={
        "login_type": "password",
        "phone": phone,
        "password": "WrongPassword123",
    })
    assert res_wrong.status_code == 200
    assert "Invalid mobile number or password." in res_wrong.data.decode("utf-8")

    # 3. Existing user who has NO password set (OTP only)
    otp_phone = "+919876502222"
    otp_user = User(phone=otp_phone, full_name="OTP Only User", role="FARMER", is_phone_verified=True)
    # password_hash is None
    db_session.add(otp_user)
    db_session.commit()

    res_no_pass = client.post("/auth/login", data={
        "login_type": "password",
        "phone": otp_phone,
        "password": "AnyPassword123",
    })
    assert res_no_pass.status_code == 200
    # Must be the exact same generic message
    assert "Invalid mobile number or password." in res_no_pass.data.decode("utf-8")


def test_users_without_password_hash_can_still_use_otp_login(client, db_session):
    """Verify that users without a password hash can seamlessly sign in via OTP."""
    phone = "+919876503333"
    otp_user = User(phone=phone, full_name="Traditional Farmer", role="FARMER", is_phone_verified=True)
    assert otp_user.password_hash is None
    db_session.add(otp_user)
    db_session.commit()

    # Request OTP
    res_req = client.post("/auth/login", data={"login_type": "otp", "phone": phone}, follow_redirects=True)
    assert res_req.status_code == 200
    assert "verify-otp" in res_req.request.path

    # Set mock OTP hash
    otp_record = OTPVerification.query.filter_by(phone=phone).first()
    from werkzeug.security import generate_password_hash
    otp_record.otp_hash = generate_password_hash("445566")
    db_session.commit()

    # Verify OTP
    res_ver = client.post("/auth/verify-otp", data={"otp_code": "445566"}, follow_redirects=True)
    assert res_ver.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get("user_id") == str(otp_user.id)


def test_authenticated_user_can_set_and_change_password(client, db_session):
    """Verify that an authenticated user can set a new password, and subsequently update it."""
    phone = "+919876504444"
    user = User(phone=phone, full_name="Setup Pass User", role="FARMER", is_phone_verified=True)
    db_session.add(user)
    db_session.commit()

    # 1. Log in user via session
    with client.session_transaction() as sess:
        sess["user_id"] = str(user.id)
        sess["user_role"] = user.role

    # 2. Set password for the first time
    res_set = client.post("/auth/set-password", data={
        "new_password": "InitialPassword123",
        "confirm_password": "InitialPassword123",
    }, follow_redirects=True)
    assert res_set.status_code == 200
    assert "Password updated successfully" in res_set.data.decode("utf-8")

    db_session.refresh(user)
    assert user.password_hash is not None
    assert user.check_password("InitialPassword123") is True

    # 3. Change password with wrong current password -> rejected
    res_wrong_current = client.post("/auth/set-password", data={
        "current_password": "WrongPassword999",
        "new_password": "BrandNewPassword456",
        "confirm_password": "BrandNewPassword456",
    }, follow_redirects=True)
    assert res_wrong_current.status_code == 200
    assert "Current password is incorrect" in res_wrong_current.data.decode("utf-8")

    # 4. Change password with correct current password -> succeeds
    res_update = client.post("/auth/set-password", data={
        "current_password": "InitialPassword123",
        "new_password": "BrandNewPassword456",
        "confirm_password": "BrandNewPassword456",
    }, follow_redirects=True)
    assert res_update.status_code == 200
    assert "Password updated successfully" in res_update.data.decode("utf-8")

    db_session.refresh(user)
    assert user.check_password("BrandNewPassword456") is True


def test_unauthenticated_set_password_rejected(client):
    """Verify that unauthenticated attempts to set/change password redirect to login."""
    res = client.post("/auth/set-password", data={
        "new_password": "SecretPass123",
        "confirm_password": "SecretPass123",
    })
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_password_login_rate_limiting(client, db_session):
    """Verify that excessive failed password login attempts trigger rate limiting."""
    from app.utils.security import clear_password_failures
    phone = "+919876505555"
    clear_password_failures(phone)

    user = User(phone=phone, full_name="Rate Limit User", role="FARMER", is_phone_verified=True)
    user.set_password("ValidPassword123")
    db_session.add(user)
    db_session.commit()

    # Fail 5 times
    for _ in range(5):
        res = client.post("/auth/login", data={
            "login_type": "password",
            "phone": phone,
            "password": "WrongPassword!",
        })
        assert res.status_code == 200

    # 6th attempt should be rate limited
    res_blocked = client.post("/auth/login", data={
        "login_type": "password",
        "phone": phone,
        "password": "ValidPassword123",
    })
    assert res_blocked.status_code == 200
    assert "Too many failed login attempts" in res_blocked.data.decode("utf-8")

    # OTP login for the same phone is NOT blocked and continues to work
    res_otp = client.post("/auth/login", data={
        "login_type": "otp",
        "phone": phone,
    }, follow_redirects=True)
    assert res_otp.status_code == 200
    assert "verify-otp" in res_otp.request.path

    clear_password_failures(phone)


def test_safe_redirect_prevents_open_redirect(client, db_session):
    """Verify that open redirect URLs are rejected and sanitized to safe local routes."""
    phone = "+919876506666"
    user = User(phone=phone, full_name="Redirect User", role="FARMER", is_phone_verified=True)
    user.set_password("SecurePass123")
    db_session.add(user)
    db_session.commit()

    # Submit login with malicious external redirect
    res = client.post("/auth/login?next=https://evil-phishing-site.com", data={
        "login_type": "password",
        "phone": phone,
        "password": "SecurePass123",
    })
    assert res.status_code == 302
    # Must redirect locally to /auth/profile, NOT external URL
    assert "evil-phishing-site.com" not in res.headers["Location"]
    assert res.headers["Location"].startswith("/auth/profile")


def test_safe_redirect_with_legitimate_next_url(client, db_session):
    """Verify that valid relative next URLs redirect the user directly to the requested page."""
    phone = "+919876507777"
    user = User(phone=phone, full_name="Next URL User", role="FARMER", is_phone_verified=True)
    user.set_password("SecurePass123")
    db_session.add(user)
    db_session.commit()

    # Password sign-in with legitimate next URL
    res = client.post("/auth/login?next=/bookings/my", data={
        "login_type": "password",
        "phone": phone,
        "password": "SecurePass123",
    })
    assert res.status_code == 302
    assert res.headers["Location"] == "/bookings/my"

    client.post("/auth/logout", follow_redirects=True)

    # OTP sign-in with legitimate next URL
    res_otp_req = client.post("/auth/login?next=/bookings/my", data={
        "login_type": "otp",
        "phone": phone,
    }, follow_redirects=True)
    assert res_otp_req.status_code == 200

    otp_record = OTPVerification.query.filter_by(phone=phone).first()
    from werkzeug.security import generate_password_hash
    otp_record.otp_hash = generate_password_hash("778899")
    db_session.commit()

    res_verify = client.post("/auth/verify-otp", data={"otp_code": "778899"})
    assert res_verify.status_code == 302
    assert res_verify.headers["Location"] == "/bookings/my"


