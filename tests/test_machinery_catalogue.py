import pytest
from decimal import Decimal
from app.models.user import User, ProviderProfile
from app.models.machinery import Machinery, MachineryPhoto, MachineryRate
from app.extensions import db


@pytest.fixture
def sample_catalogue_data(db_session):
    """Seed test data for public machinery catalogue tests."""
    # 1. Provider User & Profile
    provider_user = User(
        phone="+919876543210",
        full_name="Murugan Services",
        role="PROVIDER",
        is_phone_verified=True,
    )
    db_session.add(provider_user)
    db_session.flush()

    profile = ProviderProfile(
        user_id=provider_user.id,
        business_name="Murugan Agri Rentals",
        verification_status="VERIFIED",
        whatsapp_enabled=True,
        whatsapp_number="+919876543210",
    )
    db_session.add(profile)
    db_session.flush()

    # 2. Machinery 1: Active Tractor in Salem
    m1 = Machinery(
        provider_id=profile.id,
        name_en="Mahindra 575 DI Tractor",
        name_ta="மஹிந்திரா 575 DI டிராக்டர்",
        category="TRACTOR",
        make_model="Mahindra 575 DI",
        model_year=2022,
        horsepower=45,
        description_en="Well-maintained 45HP tractor with rotary tiller.",
        description_ta="நன்கு பராமரிக்கப்பட்ட 45HP டிராக்டர் ரோட்டாவேட்டருடன்.",
        village_or_town="Attur",
        district="Salem",
        pincode="636102",
        latitude=Decimal("11.5975"),
        longitude=Decimal("78.6012"),
        is_active=True,
    )
    db_session.add(m1)
    db_session.flush()

    r1_only = MachineryRate(
        machinery_id=m1.id,
        rental_option_type="MACHINE_ONLY",
        rate_per_hour=Decimal("600.00"),
        rate_per_day=Decimal("4000.00"),
        min_booking_duration_hours=2,
        security_deposit=Decimal("1000.00"),
    )
    r1_op = MachineryRate(
        machinery_id=m1.id,
        rental_option_type="MACHINE_OPERATOR",
        rate_per_hour=Decimal("850.00"),
        rate_per_day=Decimal("5500.00"),
        min_booking_duration_hours=2,
        security_deposit=Decimal("500.00"),
    )
    p1 = MachineryPhoto(
        machinery_id=m1.id,
        photo_url="/static/uploads/machinery/demo_tractor.jpg",
        is_primary=True,
        display_order=0,
    )
    db_session.add_all([r1_only, r1_op, p1])

    # 3. Machinery 2: Active Harvester in Thanjavur
    m2 = Machinery(
        provider_id=profile.id,
        name_en="Kubota Paddy Harvester",
        name_ta="குபோடா நெல் அறுவடை இயந்திரம்",
        category="HARVESTER",
        make_model="Kubota DC-68G",
        model_year=2023,
        horsepower=68,
        description_en="High capacity paddy harvester with operator.",
        village_or_town="Kumbakonam",
        district="Thanjavur",
        pincode="612001",
        latitude=Decimal("10.9602"),
        longitude=Decimal("79.3845"),
        is_active=True,
    )
    db_session.add(m2)
    db_session.flush()

    r2 = MachineryRate(
        machinery_id=m2.id,
        rental_option_type="MACHINE_OPERATOR_LABOUR",
        rate_per_hour=Decimal("1800.00"),
        rate_per_day=Decimal("12000.00"),
        min_booking_duration_hours=3,
        security_deposit=Decimal("2000.00"),
    )
    db_session.add(r2)

    # 4. Machinery 3: Inactive Tiller (should be hidden publicly)
    m3_inactive = Machinery(
        provider_id=profile.id,
        name_en="VST Shakti Power Tiller",
        name_ta="VST சக்தி பவர் டில்லர்",
        category="TILLER",
        village_or_town="Salem Town",
        district="Salem",
        pincode="636001",
        is_active=False,
    )
    db_session.add(m3_inactive)
    db_session.flush()

    r3 = MachineryRate(
        machinery_id=m3_inactive.id,
        rental_option_type="MACHINE_ONLY",
        rate_per_hour=Decimal("350.00"),
    )
    db_session.add(r3)

    db_session.commit()
    return {
        "m1_id": str(m1.id),
        "m2_id": str(m2.id),
        "m3_inactive_id": str(m3_inactive.id),
        "provider_id": str(profile.id),
    }


def test_public_catalogue_rendering_and_default_list(client, sample_catalogue_data):
    """Verify that public catalogue renders active machinery and shows starting prices."""
    res = client.get("/machinery/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Active machinery should be present
    assert "Mahindra 575 DI Tractor" in html
    assert "Kubota Paddy Harvester" in html
    assert "Salem" in html
    assert "Thanjavur" in html

    # Inactive machinery must NOT be visible
    assert "VST Shakti Power Tiller" not in html

    # Starting prices should appear
    assert "₹600" in html


def test_public_catalogue_filter_by_district(client, sample_catalogue_data):
    """Verify filtering by district returns only matching listings."""
    # Filter by Salem
    res_salem = client.get("/machinery/?district=Salem")
    assert res_salem.status_code == 200
    html_salem = res_salem.get_data(as_text=True)
    assert "Mahindra 575 DI Tractor" in html_salem
    assert "Kubota Paddy Harvester" not in html_salem

    # Filter by Thanjavur
    res_thanjavur = client.get("/machinery/?district=Thanjavur")
    assert res_thanjavur.status_code == 200
    html_thanjavur = res_thanjavur.get_data(as_text=True)
    assert "Kubota Paddy Harvester" in html_thanjavur
    assert "Mahindra 575 DI Tractor" not in html_thanjavur


def test_public_catalogue_filter_by_category_and_package(client, sample_catalogue_data):
    """Verify filtering by category and rental package tier."""
    # Category: HARVESTER
    res_cat = client.get("/machinery/?category=HARVESTER")
    assert res_cat.status_code == 200
    html_cat = res_cat.get_data(as_text=True)
    assert "Kubota Paddy Harvester" in html_cat
    assert "Mahindra 575 DI Tractor" not in html_cat

    # Rental Package: MACHINE_OPERATOR_LABOUR
    res_pkg = client.get("/machinery/?package=MACHINE_OPERATOR_LABOUR")
    assert res_pkg.status_code == 200
    html_pkg = res_pkg.get_data(as_text=True)
    assert "Kubota Paddy Harvester" in html_pkg
    assert "Mahindra 575 DI Tractor" not in html_pkg


def test_public_catalogue_bilingual_rendering(client, sample_catalogue_data):
    """Verify machinery names and labels render in Tamil when language is switched."""
    # Switch to Tamil
    client.get("/set-language/ta")
    res = client.get("/machinery/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Tamil names should appear prominently
    assert "மஹிந்திரா 575 DI டிராக்டர்" in html
    assert "குபோடா நெல் அறுவடை இயந்திரம்" in html
    assert "டிராக்டர்" in html
    assert "அறுவடை இயந்திரம்" in html


def test_machinery_detail_view_active_listing(client, sample_catalogue_data):
    """Verify detailed specifications, photo, rates, and provider info appear on detail page."""
    m1_id = sample_catalogue_data["m1_id"]
    res = client.get(f"/machinery/{m1_id}")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    assert "Mahindra 575 DI Tractor" in html
    assert "45 HP" in html
    assert "2022" in html
    assert "Murugan Agri Rentals" in html
    assert "Machine Only" in html
    assert "Machine + Operator" in html
    assert "₹600" in html
    assert "₹850" in html


def test_inactive_machinery_returns_404_publicly(client, sample_catalogue_data):
    """Verify inactive machinery returns 404 Not Found for public visitors."""
    m3_id = sample_catalogue_data["m3_inactive_id"]
    res = client.get(f"/machinery/{m3_id}")
    assert res.status_code == 404
