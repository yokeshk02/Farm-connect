import pytest
from app.models.user import User, ProviderProfile
from app.models.machinery import Machinery, MachineryRate
from app.models.booking import Booking
from app.models.otp import OTPVerification
from app.extensions import db


def set_user_session(client, user):
    """Helper establishing an active authenticated session for a user."""
    with client.session_transaction() as sess:
        sess["user_id"] = str(user.id)
        sess["user_role"] = user.role
        sess["user_phone"] = user.phone
        sess["user_name"] = user.full_name


# ==============================================================================
# 1. SEPARATE REGISTRATION OPTIONS TESTS
# ==============================================================================

def test_register_selection_screen_renders_three_columns(client):
    """Verify unified role-selection page displays Farmer, Provider, and Admin as three separate columns."""
    for url in ["/auth/register", "/roles", "/portal"]:
        res = client.get(url)
        assert res.status_code == 200
        html = res.data.decode("utf-8")

        # Layout grid class
        assert "roles-columns-grid" in html

        # 1. Farmer Column
        assert "cardFarmer" in html or "cardRegisterFarmer" in html
        assert "Farmer" in html
        assert "🧑‍🌾" in html
        assert "Search Machinery" in html
        assert "View Rental Prices" in html
        assert "My Bookings" in html
        assert "My Profile" in html
        assert "Register as Farmer" in html
        assert "Sign In as Farmer" in html
        assert "/auth/register/farmer" in html
        assert "role=farmer" in html

        # 2. Machinery Provider / Renter Column
        assert "cardProvider" in html or "cardRegisterProvider" in html
        assert "Machinery Provider" in html or "Provider" in html
        assert "🚜" in html
        assert "Add Machinery" in html
        assert "Manage My Machinery" in html
        assert "Set Rental Prices" in html
        assert "Incoming Booking Requests" in html
        assert "Register as Provider" in html
        assert "Sign In as Provider" in html
        assert "/auth/register/provider" in html
        assert "role=provider" in html

        # 3. Admin Column
        assert "cardAdmin" in html
        assert "Admin" in html
        assert "⚙️" in html
        assert "Manage Users" in html
        assert "Review Listings" in html
        assert "Monitor Bookings" in html
        assert "Manage Enquiries" in html
        assert "Admin Sign In" in html
        assert "role=admin" in html
        assert "Authorized Accounts Only" in html


def test_login_screen_role_indication(client):
    """Verify /auth/login clearly indicates the selected role when role parameter is passed."""
    # Farmer role indication
    res_farmer = client.get("/auth/login?role=farmer")
    assert res_farmer.status_code == 200
    html_farmer = res_farmer.data.decode("utf-8")
    assert "role-banner-farmer" in html_farmer
    assert "Signing in as Farmer" in html_farmer

    # Provider role indication
    res_provider = client.get("/auth/login?role=provider")
    assert res_provider.status_code == 200
    html_provider = res_provider.data.decode("utf-8")
    assert "role-banner-provider" in html_provider
    assert "Signing in as Machinery Provider" in html_provider

    # Admin role indication (defaults to password tab)
    res_admin = client.get("/auth/login?role=admin")
    assert res_admin.status_code == 200
    html_admin = res_admin.data.decode("utf-8")
    assert "role-banner-admin" in html_admin
    assert "Signing in as System Administrator" in html_admin
    assert 'id="passLoginForm"' in html_admin


def test_farmer_registration_form_rendering(client):
    """Verify dedicated Farmer registration form renders with pre-set role FARMER."""
    # Test both /auth/register/farmer and /auth/register?role=farmer
    for url in ["/auth/register/farmer", "/auth/register?role=farmer"]:
        res = client.get(url)
        assert res.status_code == 200
        html = res.data.decode("utf-8")

        assert "Farmer Registration" in html or "Create Farmer Account" in html
        # Hidden role input set to FARMER
        assert 'name="role" value="FARMER"' in html or "FARMER" in html
        # Must NOT show role dropdown with Provider or Admin
        assert '<option value="PROVIDER">' not in html
        assert '<option value="ADMIN">' not in html
        # Form inputs
        assert 'name="full_name"' in html
        assert 'name="phone"' in html
        assert 'name="preferred_language"' in html
        assert 'name="password"' in html
        assert 'name="confirm_password"' in html
        assert "Continue to Phone Verification" in html


def test_provider_registration_form_rendering(client):
    """Verify dedicated Machinery Provider registration form renders with pre-set role PROVIDER."""
    for url in ["/auth/register/provider", "/auth/register?role=provider"]:
        res = client.get(url)
        assert res.status_code == 200
        html = res.data.decode("utf-8")

        assert "Machinery Provider Registration" in html
        # Hidden role input set to PROVIDER
        assert 'name="role" value="PROVIDER"' in html or "PROVIDER" in html
        # Must NOT show role dropdown with Farmer or Admin
        assert '<option value="FARMER">' not in html
        assert '<option value="ADMIN">' not in html
        # Form inputs
        assert 'name="full_name"' in html
        assert 'name="phone"' in html
        assert 'name="preferred_language"' in html
        assert 'name="password"' in html
        assert "Continue to Phone Verification" in html


def test_separate_farmer_registration_otp_flow(client, db_session):
    """Verify submitting dedicated farmer registration triggers OTP and creates FARMER account."""
    reg_data = {
        "full_name": "Kandasamy Farmer",
        "phone": "9876512345",
        "role": "FARMER",
        "action": "verify_otp",
    }
    res = client.post("/auth/register/farmer", data=reg_data, follow_redirects=True)
    assert res.status_code == 200
    assert "verify-otp" in res.request.path

    phone = "+919876512345"
    otp_record = OTPVerification.query.filter_by(phone=phone).first()
    assert otp_record is not None

    from werkzeug.security import generate_password_hash
    otp_record.otp_hash = generate_password_hash("123456")
    db_session.commit()

    res_verify = client.post("/auth/verify-otp", data={"otp_code": "123456"}, follow_redirects=True)
    assert res_verify.status_code == 200

    user = User.query.filter_by(phone=phone).first()
    assert user is not None
    assert user.role == "FARMER"
    assert user.full_name == "Kandasamy Farmer"
    assert user.is_phone_verified is True


def test_separate_provider_registration_otp_flow(client, db_session):
    """Verify submitting dedicated provider registration triggers OTP, creates PROVIDER and ProviderProfile."""
    reg_data = {
        "full_name": "Dhandapani Owner",
        "phone": "9876523456",
        "role": "PROVIDER",
        "action": "verify_otp",
    }
    res = client.post("/auth/register/provider", data=reg_data, follow_redirects=True)
    assert res.status_code == 200
    assert "verify-otp" in res.request.path

    phone = "+919876523456"
    otp_record = OTPVerification.query.filter_by(phone=phone).first()
    assert otp_record is not None

    from werkzeug.security import generate_password_hash
    otp_record.otp_hash = generate_password_hash("654321")
    db_session.commit()

    res_verify = client.post("/auth/verify-otp", data={"otp_code": "654321"}, follow_redirects=True)
    assert res_verify.status_code == 200

    user = User.query.filter_by(phone=phone).first()
    assert user is not None
    assert user.role == "PROVIDER"
    assert user.provider_profile is not None
    assert "Dhandapani" in user.provider_profile.business_name


def test_public_registration_blocks_admin_tampering(client, db_session):
    """Verify tampering with role to ADMIN on registration endpoints is blocked and defaults to FARMER."""
    tampered_data = {
        "full_name": "Privilege Escalator",
        "phone": "9876534567",
        "role": "ADMIN",  # Tampered role
        "action": "verify_otp",
    }
    client.post("/auth/register", data=tampered_data, follow_redirects=True)
    phone = "+919876534567"

    otp_record = OTPVerification.query.filter_by(phone=phone).first()
    from werkzeug.security import generate_password_hash
    otp_record.otp_hash = generate_password_hash("111222")
    db_session.commit()

    client.post("/auth/verify-otp", data={"otp_code": "111222"}, follow_redirects=True)

    user = User.query.filter_by(phone=phone).first()
    assert user is not None
    assert user.role != "ADMIN"
    assert user.role == "FARMER"


# ==============================================================================
# 2. SEPARATE DASHBOARDS TESTS
# ==============================================================================

def test_farmer_dashboard_displays_all_five_farmer_features(client, db_session):
    """Verify Farmer dashboard displays Search, Browse Listings, View Rental Prices, My Bookings, My Profile."""
    farmer = User(phone="+919876501001", full_name="Marimuthu Farmer", role="FARMER", is_phone_verified=True)
    db_session.add(farmer)
    db_session.commit()

    set_user_session(client, farmer)

    res = client.get("/farmer/dashboard")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Welcome greeting
    assert "Marimuthu Farmer" in html
    assert "Farmer Dashboard" in html

    # Feature 1: Search Machinery
    assert "Search Machinery" in html
    assert 'name="district"' in html
    assert 'name="category"' in html
    assert 'name="q"' in html

    # Feature 2: Browse Machinery Listings
    assert "Browse Machinery Listings" in html or "Browse Listings" in html
    assert "Tractors" in html
    assert "Combine Harvesters" in html

    # Feature 3: View Rental Prices
    assert "View Rental Prices" in html or "Rental Prices" in html
    assert "Machine Only" in html
    assert "Machine + Operator" in html
    assert "Fuel Included" in html

    # Feature 4: My Bookings
    assert "My Bookings" in html
    assert "btnViewAllBookings" in html or "View All" in html

    # Feature 5: My Profile
    assert "My Profile" in html
    assert "+919876501001" in html
    assert "Edit Profile &amp; Settings" in html or "Edit Profile & Settings" in html

    # MUST NOT show provider-specific management options to Farmers
    assert "Add Machinery" not in html
    assert "Incoming Booking Requests" not in html
    assert "Incoming Requests" not in html
    assert "Manage Rental Prices" not in html


def test_provider_dashboard_displays_all_provider_features(client, db_session):
    """Verify Provider dashboard displays Provider Dashboard, My Machinery, Add Machinery, Manage Rental Prices, Incoming Booking Requests, My Profile."""
    provider_user = User(phone="+919876502001", full_name="Periyasamy Owner", role="PROVIDER", is_phone_verified=True)
    db_session.add(provider_user)
    db_session.commit()

    profile = ProviderProfile(
        user_id=provider_user.id,
        business_name="Periyasamy Tractors",
        verification_status="VERIFIED",
    )
    db_session.add(profile)
    db_session.commit()

    set_user_session(client, provider_user)

    res = client.get("/provider/dashboard")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # 1. Provider Dashboard (Overview & statistics)
    assert "Provider Dashboard" in html
    assert "Total Machinery" in html
    assert "Pending Requests" in html
    assert "Active Bookings" in html
    assert "Completed Bookings" in html

    # 2. My Machinery
    assert "My Machinery" in html

    # 3. Add Machinery
    assert "Add Machinery" in html

    # 4. Manage Rental Prices
    assert "Manage Rental Prices" in html

    # 5. Incoming Booking Requests
    assert "Incoming Booking Requests" in html or "Booking Requests" in html

    # 6. My Profile
    assert "My Profile" in html

    # MUST NOT show farmer-specific options on Provider dashboard
    assert "Compare Lowest Rates" not in html
    assert "Find Machinery to Rent" not in html


def test_provider_cannot_access_farmer_dashboard(client, db_session):
    """Verify that a Provider entering /farmer/dashboard directly receives 403 Forbidden."""
    provider_user = User(phone="+919876503001", full_name="Strict Provider", role="PROVIDER", is_phone_verified=True)
    db_session.add(provider_user)
    db_session.commit()

    set_user_session(client, provider_user)

    res = client.get("/farmer/dashboard")
    assert res.status_code == 403


def test_farmer_cannot_access_provider_dashboard(client, db_session):
    """Verify that a Farmer entering /provider/dashboard directly receives 403 Forbidden."""
    farmer = User(phone="+919876503002", full_name="Strict Farmer", role="FARMER", is_phone_verified=True)
    db_session.add(farmer)
    db_session.commit()

    set_user_session(client, farmer)

    res = client.get("/provider/dashboard")
    assert res.status_code == 403


# ==============================================================================
# 3. ADMIN ACCESS CONTROL TESTS
# ==============================================================================

def test_admin_dashboard_accessible_to_authorized_admin(client, db_session):
    """Verify authorized Admin account can access /admin/dashboard and sees governance metrics."""
    admin_user = User(phone="+919876504001", full_name="Master Admin", role="ADMIN", is_phone_verified=True)
    db_session.add(admin_user)
    db_session.commit()

    set_user_session(client, admin_user)

    res = client.get("/admin/dashboard")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    assert "Admin Dashboard" in html
    assert "Registered Farmers" in html
    assert "Machinery Providers" in html
    assert "Active Machinery" in html
    assert "Total Bookings" in html


def test_admin_dashboard_displays_provider_machinery_counts(client, db_session):
    """Verify admin dashboard loads without AppenderQuery error and displays correct provider machinery counts."""
    # 1. Create Admin
    admin_user = User(phone="+919876504099", full_name="Super Admin", role="ADMIN", is_phone_verified=True)
    db_session.add(admin_user)

    # 2. Create Provider A with 2 machines
    provider_user_a = User(phone="+919876504088", full_name="Anand Provider", role="PROVIDER", is_phone_verified=True)
    db_session.add(provider_user_a)
    db_session.flush()

    profile_a = ProviderProfile(
        user_id=provider_user_a.id,
        business_name="Kovai Agro Fleet",
        verification_status="VERIFIED",
    )
    db_session.add(profile_a)
    db_session.flush()

    m1 = Machinery(
        provider_id=profile_a.id,
        name_en="Mahindra 575 DI",
        category="TRACTOR",
        village_or_town="Pollachi",
        district="Coimbatore",
        pincode="642001",
        is_active=True,
    )
    m2 = Machinery(
        provider_id=profile_a.id,
        name_en="John Deere 5050 D",
        category="TRACTOR",
        village_or_town="Sulur",
        district="Coimbatore",
        pincode="641402",
        is_active=True,
    )
    db_session.add_all([m1, m2])

    # 3. Create Provider B with 0 machines
    provider_user_b = User(phone="+919876504077", full_name="Bala Provider", role="PROVIDER", is_phone_verified=True)
    db_session.add(provider_user_b)
    db_session.flush()

    profile_b = ProviderProfile(
        user_id=provider_user_b.id,
        business_name="Salem Tractor Hub",
        verification_status="PENDING",
    )
    db_session.add(profile_b)
    db_session.commit()

    # 4. Sign in as Admin and load dashboard
    set_user_session(client, admin_user)
    res = client.get("/admin/dashboard")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Verify both providers are rendered
    assert "Kovai Agro Fleet" in html
    assert "Salem Tractor Hub" in html

    # Verify correct machinery counts are displayed for each
    assert "2 units" in html
    assert "0 units" in html

    # Verify model helper property as well
    assert profile_a.machinery_count == 2
    assert profile_b.machinery_count == 0


def test_farmer_cannot_access_admin_pages_directly(client, db_session):
    """Verify Farmer entering /admin/dashboard URL directly receives 403 Forbidden."""
    farmer = User(phone="+919876505001", full_name="Sneaky Farmer", role="FARMER", is_phone_verified=True)
    db_session.add(farmer)
    db_session.commit()

    set_user_session(client, farmer)

    res = client.get("/admin/dashboard")
    assert res.status_code == 403

    res_root = client.get("/admin/")
    assert res_root.status_code == 403


def test_provider_cannot_access_admin_pages_directly(client, db_session):
    """Verify Provider entering /admin/dashboard URL directly receives 403 Forbidden."""
    provider_user = User(phone="+919876505002", full_name="Sneaky Provider", role="PROVIDER", is_phone_verified=True)
    db_session.add(provider_user)
    db_session.commit()

    set_user_session(client, provider_user)

    res = client.get("/admin/dashboard")
    assert res.status_code == 403

    res_root = client.get("/admin/")
    assert res_root.status_code == 403


def test_unauthenticated_cannot_access_admin_pages(client):
    """Verify unauthenticated visitor entering /admin/dashboard redirects to /auth/login."""
    res = client.get("/admin/dashboard")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_unauthenticated_cannot_access_farmer_dashboard(client):
    """Verify unauthenticated visitor entering /farmer/dashboard redirects to /auth/login."""
    res = client.get("/farmer/dashboard")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]
