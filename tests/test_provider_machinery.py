import io
import pytest
from PIL import Image
from decimal import Decimal
from app.models.user import User, ProviderProfile
from app.models.machinery import Machinery, MachineryPhoto, MachineryRate
from app.extensions import db


def create_in_memory_image(img_format="JPEG", size=(80, 80), color="green"):
    """Helper creating a valid in-memory image stream for upload tests."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=img_format)
    buf.seek(0)
    ext = "jpg" if img_format == "JPEG" else img_format.lower()
    return buf, f"test_img.{ext}"


@pytest.fixture
def provider_auth_setup(client, db_session):
    """Seed two distinct provider users and one farmer user."""
    # Provider 1
    p1_user = User(phone="+919876500001", full_name="Provider One", role="PROVIDER", is_phone_verified=True)
    db_session.add(p1_user)
    db_session.flush()
    p1_profile = ProviderProfile(user_id=p1_user.id, business_name="Provider One Farm Equips")
    db_session.add(p1_profile)

    # Provider 2
    p2_user = User(phone="+919876500002", full_name="Provider Two", role="PROVIDER", is_phone_verified=True)
    db_session.add(p2_user)
    db_session.flush()
    p2_profile = ProviderProfile(user_id=p2_user.id, business_name="Provider Two Rentals")
    db_session.add(p2_profile)

    # Farmer User
    farmer = User(phone="+919876500003", full_name="Raju Farmer", role="FARMER", is_phone_verified=True)
    db_session.add(farmer)

    # Seed one machinery owned by Provider 1
    m1 = Machinery(
        provider_id=p1_profile.id,
        name_en="Swaraj 744 FE",
        category="TRACTOR",
        village_or_town="Attur",
        district="Salem",
        pincode="636102",
        is_active=True,
    )
    db_session.add(m1)
    db_session.flush()
    r1 = MachineryRate(
        machinery_id=m1.id,
        rental_option_type="MACHINE_ONLY",
        rate_per_hour=Decimal("500.00"),
    )
    db_session.add(r1)
    db_session.commit()

    return {
        "p1_user": p1_user,
        "p1_profile": p1_profile,
        "p2_user": p2_user,
        "p2_profile": p2_profile,
        "farmer": farmer,
        "m1": m1,
    }


def login_session(client, user):
    """Helper establishing an active authenticated session for a user."""
    with client.session_transaction() as sess:
        sess["user_id"] = str(user.id)
        sess["user_role"] = user.role
        sess["user_phone"] = user.phone
        sess["user_name"] = user.full_name


def test_unauthenticated_access_redirects_to_login(client):
    """Verify accessing provider machinery routes without login redirects to /auth/login."""
    res = client.get("/provider/machinery/")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_farmer_role_denied_access_to_provider_routes(client, provider_auth_setup):
    """Verify that a FARMER role receives 403 Forbidden when accessing provider management."""
    login_session(client, provider_auth_setup["farmer"])
    res = client.get("/provider/machinery/")
    assert res.status_code == 403


def test_provider_dashboard_lists_owned_machinery(client, provider_auth_setup):
    """Verify provider dashboard lists only the equipment owned by that provider."""
    login_session(client, provider_auth_setup["p1_user"])
    res = client.get("/provider/machinery/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Swaraj 744 FE" in html
    assert "Active" in html


def test_create_machinery_listing_success(client, provider_auth_setup):
    """Verify creating a new machinery listing with rates and valid image upload."""
    login_session(client, provider_auth_setup["p1_user"])

    img_stream, img_name = create_in_memory_image(img_format="JPEG")
    data = {
        "name_en": "New Holland 3630 TX",
        "name_ta": "நியூ ஹாலந்து டிராக்டர்",
        "category": "TRACTOR",
        "make_model": "3630 TX Super",
        "model_year": "2023",
        "horsepower": "55",
        "village_or_town": "Omalur",
        "district": "Salem",
        "pincode": "636455",
        "machine_only_hour": "700",
        "machine_only_day": "4500",
        "machine_only_min_hours": "1",
        "machine_only_deposit": "500",
        "photos": (img_stream, img_name),
    }

    res = client.post("/provider/machinery/new", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert res.status_code == 200
    assert "Machinery listing created successfully!" in res.get_data(as_text=True)

    # Check database record
    created = Machinery.query.filter_by(name_en="New Holland 3630 TX").first()
    assert created is not None
    assert created.category == "TRACTOR"
    assert created.horsepower == 55
    assert len(created.rates) == 1
    assert created.rates[0].rate_per_hour == Decimal("700.00")
    assert len(created.photos) == 1
    assert created.photos[0].is_primary is True


def test_create_machinery_validation_rejects_missing_fields_and_negative_rates(client, provider_auth_setup):
    """Verify validation rejects missing required fields and negative rental rates."""
    login_session(client, provider_auth_setup["p1_user"])

    # 1. Missing name_en
    bad_data1 = {
        "name_en": "",
        "category": "TRACTOR",
        "village_or_town": "Attur",
        "district": "Salem",
        "pincode": "636102",
        "machine_only_hour": "500",
    }
    res1 = client.post("/provider/machinery/new", data=bad_data1, follow_redirects=True)
    assert "Equipment name in English is required" in res1.get_data(as_text=True)

    # 2. Negative rate
    bad_data2 = {
        "name_en": "Valid Name",
        "category": "TRACTOR",
        "village_or_town": "Attur",
        "district": "Salem",
        "pincode": "636102",
        "machine_only_hour": "-50",
    }
    res2 = client.post("/provider/machinery/new", data=bad_data2, follow_redirects=True)
    assert "cannot be negative" in res2.get_data(as_text=True)

    # 3. Invalid PIN code
    bad_data3 = {
        "name_en": "Valid Name",
        "category": "TRACTOR",
        "village_or_town": "Attur",
        "district": "Salem",
        "pincode": "123",  # Invalid
        "machine_only_hour": "500",
    }
    res3 = client.post("/provider/machinery/new", data=bad_data3, follow_redirects=True)
    assert "PIN Code must be a 6-digit number" in res3.get_data(as_text=True)


def test_photo_upload_rejects_non_image_file(client, provider_auth_setup):
    """Verify upload validation rejects files with non-image contents."""
    login_session(client, provider_auth_setup["p1_user"])

    fake_file = io.BytesIO(b"<?php echo 'malicious'; ?>")
    data = {
        "name_en": "Tiller Test",
        "category": "TILLER",
        "village_or_town": "Attur",
        "district": "Salem",
        "pincode": "636102",
        "machine_only_hour": "400",
        "photos": (fake_file, "exploit.jpg"),
    }
    res = client.post("/provider/machinery/new", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert "Corrupt or invalid image file" in res.get_data(as_text=True)


def test_photo_upload_rejects_more_than_five_photos(client, provider_auth_setup):
    """Verify upload rejects more than 5 photos."""
    login_session(client, provider_auth_setup["p1_user"])

    # Build 6 valid images
    images = []
    for i in range(6):
        s, name = create_in_memory_image()
        images.append((s, f"img_{i}.jpg"))

    data = {
        "name_en": "Tractor Five Plus",
        "category": "TRACTOR",
        "village_or_town": "Attur",
        "district": "Salem",
        "pincode": "636102",
        "machine_only_hour": "500",
        "photos": images,
    }
    res = client.post("/provider/machinery/new", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert "maximum of 5 photos" in res.get_data(as_text=True)


def test_cross_provider_cannot_edit_another_providers_listing(client, provider_auth_setup):
    """Verify Provider 2 receives 403 Forbidden when attempting to edit Provider 1's machinery."""
    # Login as Provider 2
    login_session(client, provider_auth_setup["p2_user"])
    m1_id = provider_auth_setup["m1"].id

    # Attempt GET edit
    res_get = client.get(f"/provider/machinery/{m1_id}/edit")
    assert res_get.status_code == 403

    # Attempt POST edit
    res_post = client.post(f"/provider/machinery/{m1_id}/edit", data={"name_en": "Hacked Name"})
    assert res_post.status_code == 403


def test_toggle_machinery_active_status(client, provider_auth_setup):
    """Verify owner can deactivate and activate listing without deleting data."""
    login_session(client, provider_auth_setup["p1_user"])
    m1 = provider_auth_setup["m1"]
    assert m1.is_active is True

    # Deactivate
    res_deact = client.post(f"/provider/machinery/{m1.id}/toggle-status", follow_redirects=True)
    assert res_deact.status_code == 200
    db.session.refresh(m1)
    assert m1.is_active is False
    assert "deactivated" in res_deact.get_data(as_text=True)

    # Reactivate
    res_act = client.post(f"/provider/machinery/{m1.id}/toggle-status", follow_redirects=True)
    assert res_act.status_code == 200
    db.session.refresh(m1)
    assert m1.is_active is True
    assert "activated" in res_act.get_data(as_text=True)
