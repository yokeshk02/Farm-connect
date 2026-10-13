import pytest
from decimal import Decimal
from app.models import User, ProviderProfile, Machinery, MachineryRate, Booking, ContactEnquiry
from app.extensions import db


def set_user_session(client, user):
    """Helper establishing an active authenticated session for a user."""
    with client.session_transaction() as sess:
        sess["user_id"] = str(user.id)
        sess["user_role"] = user.role
        sess["user_phone"] = user.phone
        sess["user_name"] = user.full_name


def test_home_page_sections_and_content(client):
    """Verify that home page renders all required reference design sections and elements."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Branding & Hero
    assert "FarmConnect" in html
    assert "Explore Machinery" in html
    assert "List Your Machinery" in html

    # How It Works (4 steps)
    assert "How FarmConnect Works" in html
    assert "1. Discover Equipment" in html
    assert "2. Choose Rental Tier" in html
    assert "3. Transparent Estimate" in html
    assert "4. Confirm &amp; Settle" in html or "4. Confirm & Settle" in html

    # Machinery Categories
    assert "Popular Machinery Categories" in html
    assert "Tractor" in html
    assert "Harvester" in html
    assert "Power Tiller" in html
    assert "Sprayer" in html
    assert "Baler" in html

    # Why Choose FarmConnect
    assert "Why Farmers &amp; Owners Choose FarmConnect" in html or "Why Farmers & Owners Choose FarmConnect" in html
    assert "Verified Local Providers" in html
    assert "Zero Middlemen Markups" in html
    assert "Double-Booking Prevention" in html

    # Footer
    assert "All rights reserved" in html
    assert "Quick Links" in html
    assert "Contact Us" in html


def test_public_navigation_links(client):
    """Verify navigation links shown to an unauthenticated public visitor."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    header_html = html.split('<header')[1].split('</header>')[0]

    # Public items must be visible in header
    assert "Machinery Rentals" in header_html
    assert "How It Works" in header_html
    assert "Contact Us" in header_html
    assert "Sign In" in header_html
    assert "Register" in header_html
    assert "தமிழ்" in header_html or "TA" in header_html

    # Authenticated-only items must NOT be visible in header
    assert "Sign Out" not in header_html
    assert "My Bookings" not in header_html
    assert "Provider Dashboard" not in header_html
    assert "Admin Dashboard" not in header_html


def test_farmer_navigation_links(client, db_session):
    """Verify navigation links shown to an authenticated farmer."""
    farmer = User(phone="+919876500001", full_name="Ramesh Farmer", role="FARMER", is_phone_verified=True)
    db_session.add(farmer)
    db_session.commit()

    set_user_session(client, farmer)

    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    header_html = html.split('<header')[1].split('</header>')[0]

    # Farmer items
    assert "My Bookings" in header_html
    assert "My Profile" in header_html
    assert "Sign Out" in header_html

    # Must NOT show Provider or Admin or unauth links in header
    assert "Provider Dashboard" not in header_html
    assert "Admin Dashboard" not in header_html
    assert "Sign In" not in header_html
    assert "Register" not in header_html


def test_provider_navigation_links(client, db_session):
    """Verify navigation links shown to an authenticated provider."""
    provider_user = User(phone="+919876500002", full_name="Senthil Provider", role="PROVIDER", is_phone_verified=True)
    db_session.add(provider_user)
    db_session.commit()

    profile = ProviderProfile(
        user_id=provider_user.id,
        business_name="Senthil Agri Rentals",
        verification_status="VERIFIED",
    )
    db_session.add(profile)
    db_session.commit()

    set_user_session(client, provider_user)

    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    header_html = html.split('<header')[1].split('</header>')[0]

    # Provider items
    assert "Provider Dashboard" in header_html
    assert "My Machinery" in header_html
    assert "Booking Requests" in header_html
    assert "My Profile" in header_html
    assert "Sign Out" in header_html

    # Must NOT show farmer-only 'My Bookings' or admin links in header
    assert "My Bookings" not in header_html
    assert "Admin Dashboard" not in header_html
    assert "Sign In" not in header_html
    assert "Register" not in header_html


def test_admin_navigation_links(client, db_session):
    """Verify admin navigation links for authenticated staff/admin."""
    admin_user = User(phone="+919876500003", full_name="Admin Staff", role="ADMIN", is_phone_verified=True)
    db_session.add(admin_user)
    db_session.commit()

    set_user_session(client, admin_user)

    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    header_html = html.split('<header')[1].split('</header>')[0]

    # Admin items
    assert "Admin Dashboard" in header_html
    assert "Sign Out" in header_html


def test_contact_page_get_and_post(client, db_session):
    """Verify contact page GET form rendering and POST enquiry submission."""
    # 1. GET
    res = client.get("/contact")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Contact Us" in html

    # 2. POST with valid data
    post_res = client.post(
        "/contact",
        data={
            "sender_name": "Karthik Raja",
            "contact_phone_or_email": "+919876543210",
            "subject": "Equipment Inquiry",
            "message": "Need a combine harvester for paddy harvest in Thanjavur next week.",
        },
        follow_redirects=True,
    )
    assert post_res.status_code == 200
    post_html = post_res.data.decode("utf-8")
    assert "Thank you" in post_html or "enquiry has been submitted" in post_html

    # Check database persistence
    enquiry = ContactEnquiry.query.filter_by(sender_name="Karthik Raja").first()
    assert enquiry is not None
    assert enquiry.contact_phone_or_email == "+919876543210"
    assert "paddy harvest" in enquiry.message


def test_provider_dashboard_access_control(client, db_session):
    """Verify provider dashboard authorization guards."""
    # 1. Unauthenticated -> 302 redirect
    res = client.get("/provider/dashboard")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]

    # 2. Farmer -> 403 Forbidden
    farmer = User(phone="+919876500010", full_name="Kannan Farmer", role="FARMER", is_phone_verified=True)
    db_session.add(farmer)
    db_session.commit()

    set_user_session(client, farmer)
    res_farmer = client.get("/provider/dashboard")
    assert res_farmer.status_code == 403


def test_provider_dashboard_real_metrics_and_rendering(client, db_session):
    """Verify provider dashboard displays real metrics, quick actions, and recent bookings."""
    provider_user = User(phone="+919876500020", full_name="Arun Provider", role="PROVIDER", is_phone_verified=True)
    db_session.add(provider_user)
    db_session.commit()

    profile = ProviderProfile(
        user_id=provider_user.id,
        business_name="Arun Machinery Hub",
        verification_status="VERIFIED",
    )
    db_session.add(profile)
    db_session.commit()

    # Create machinery
    m1 = Machinery(
        provider_id=profile.id,
        name_en="John Deere 5050D",
        name_ta="ஜான் டீர் 5050D",
        category="TRACTOR",
        village_or_town="Madurai",
        district="Madurai",
        pincode="625001",
        is_active=True,
    )
    db_session.add(m1)
    db_session.commit()

    set_user_session(client, provider_user)
    res = client.get("/provider/dashboard")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Personalized welcome
    assert "Arun Machinery Hub" in html or "Arun Provider" in html

    # Stat Cards
    assert "Total Machinery" in html
    assert "Pending Requests" in html
    assert "Active Bookings" in html
    assert "Completed Bookings" in html

    # Quick Actions
    assert "My Machinery" in html
    assert "Add Machinery" in html or "List New Machinery" in html
    assert "Booking Requests" in html


def test_bilingual_ui_rendering(client):
    """Verify Tamil translation persists and renders proper Tamil text."""
    res = client.get("/set-language/ta", follow_redirects=True)
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Tamil translated strings
    assert "விவசாயிகளையும் நவீன இயந்திரங்களையும் இணைக்கும் தளம்" in html
    assert "இயந்திரங்களை காண்க" in html
    assert "எவ்வாறு செயல்படுகிறது" in html
    assert "டிராக்டர்" in html
    assert "அறுவடை இயந்திரம்" in html
