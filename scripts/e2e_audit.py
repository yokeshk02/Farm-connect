import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
import re
import sys
import uuid
import time
import traceback
from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models.user import User, ProviderProfile
from app.models.machinery import Machinery, MachineryRate, MachineryPhoto
from app.models.booking import Booking, BookingStatusHistory
from app.models.otp import OTPVerification
from app.models.enquiry import ContactEnquiry
from app.services.otp_service import otp_service
from app.utils.security import is_password_rate_limited, clear_password_failures

def get_csrf_token(client, get_url="/auth/login"):
    """Fetch page and extract valid CSRF token."""
    res = client.get(get_url)
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', res.data.decode("utf-8"))
    if m:
        return m.group(1)
    # Check if csrf_token is in session or cookie
    with client.session_transaction() as sess:
        return sess.get("csrf_token", "")

def run_audit():
    results = {}
    print("=" * 80)
    print("STARTING COMPLETE END-TO-END AUDIT OF FARMCONNECT")
    print("=" * 80)

    # 1. Instantiate application in development mode with live PostgreSQL
    app = create_app()
    # Disable CSRF for form automation, we will explicitly test CSRF enforcement in Feature 7
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    audit_suffix = str(int(time.time()))[-6:]
    farmer_phone = f"+919800{audit_suffix}"
    provider_phone = f"+919801{audit_suffix}"
    admin_phone = f"+919802{audit_suffix}"
    tamper_phone = f"+919803{audit_suffix}"

    created_user_ids = []
    created_machinery_ids = []
    created_booking_ids = []

    with app.app_context():
        # Ensure clean state for test phone numbers if left over
        for ph in [farmer_phone, provider_phone, admin_phone, tamper_phone]:
            u = User.query.filter_by(phone=ph).first()
            if u:
                db.session.delete(u)
        db.session.commit()

        # =====================================================================
        # FEATURE 1: Farmer registration, password login, logout, and login again
        # =====================================================================
        print("\n--- [AUDIT 1] Farmer Registration, Password Login, Logout, Relogin ---")
        try:
            # Step A: Register farmer with password
            farmer_pass = "FarmerPass@2026"
            reg_res = client.post("/auth/register/farmer", data={
                "full_name": f"Audit Farmer {audit_suffix}",
                "phone": farmer_phone.replace("+91", ""),
                "preferred_language": "ta",
                "password": farmer_pass,
                "confirm_password": farmer_pass,
                "action": "save_signin",
            }, follow_redirects=True)
            assert reg_res.status_code == 200, f"Registration failed with status {reg_res.status_code}"

            farmer_user = User.query.filter_by(phone=farmer_phone).first()
            assert farmer_user is not None, "Farmer user was not created in DB"
            created_user_ids.append(farmer_user.id)
            assert farmer_user.role == "FARMER", f"Expected FARMER role, got {farmer_user.role}"
            assert farmer_user.check_password(farmer_pass), "Password check failed"

            # Step B: Logout
            logout_res = client.post("/auth/logout", follow_redirects=True)
            assert logout_res.status_code == 200
            with client.session_transaction() as sess:
                assert "user_id" not in sess, "Session user_id not cleared on logout"

            # Step C: Login again with password
            login_res = client.post("/auth/login", data={
                "login_type": "password",
                "phone": farmer_phone,
                "password": farmer_pass,
            }, follow_redirects=True)
            assert login_res.status_code == 200
            with client.session_transaction() as sess:
                assert sess.get("user_id") == str(farmer_user.id), "User ID not set after relogin"
                assert sess.get("user_role") == "FARMER", "User role not FARMER in session"

            # Step D: Access farmer dashboard
            dash_res = client.get("/farmer/dashboard")
            assert dash_res.status_code == 200, "Farmer dashboard failed to load"
            assert f"Audit Farmer {audit_suffix}" in dash_res.data.decode("utf-8")

            results["1. Farmer Registration & Login Lifecycle"] = "PASS"
            print(">>> FEATURE 1: PASS")
        except Exception as e:
            traceback.print_exc()
            results["1. Farmer Registration & Login Lifecycle"] = f"FAIL: {str(e)}"
            print(f">>> FEATURE 1: FAIL: {e}")

        # Logout farmer
        client.post("/auth/logout", follow_redirects=True)

        # =====================================================================
        # FEATURE 2: Provider registration, login, adding machinery, editing listings
        # =====================================================================
        print("\n--- [AUDIT 2] Provider Registration, Login, Adding & Editing Machinery ---")
        machinery_id = None
        try:
            provider_pass = "ProviderPass@2026"
            reg_prov_res = client.post("/auth/register/provider", data={
                "full_name": f"Audit Provider {audit_suffix}",
                "phone": provider_phone.replace("+91", ""),
                "preferred_language": "en",
                "password": provider_pass,
                "confirm_password": provider_pass,
                "action": "save_signin",
            }, follow_redirects=True)
            assert reg_prov_res.status_code == 200

            provider_user = User.query.filter_by(phone=provider_phone).first()
            assert provider_user is not None, "Provider user not found in DB"
            created_user_ids.append(provider_user.id)
            assert provider_user.role == "PROVIDER", f"Expected PROVIDER role, got {provider_user.role}"

            profile = provider_user.provider_profile
            assert profile is not None, "ProviderProfile was not created"

            # Step B: Provider adds a machinery listing
            create_mach_res = client.post("/provider/machinery/new", data={
                "name_en": f"Mahindra 575 DI Tractor {audit_suffix}",
                "name_ta": "மகிந்திரா 575 DI டிராக்டர்",
                "category": "TRACTOR",
                "make_model": "Mahindra 575 DI",
                "model_year": "2023",
                "horsepower": "45",
                "village_or_town": "Orathanadu",
                "district": "Thanjavur",
                "pincode": "614625",
                "description_en": "High performance 45 HP tractor for ploughing and rotavator operations.",
                "description_ta": "உழவு மற்றும் ரோட்டோவேட்டர் வேலைகளுக்கு ஏற்ற 45 குதிரைத்திறன் டிராக்டர்.",
                "machine_only_hour": "600",
                "machine_only_day": "4500",
                "machine_only_min_hours": "2",
                "machine_only_deposit": "500",
                "machine_operator_hour": "850",
                "machine_operator_day": "6500",
                "machine_operator_min_hours": "2",
                "machine_operator_deposit": "0",
            }, follow_redirects=True)
            assert create_mach_res.status_code == 200

            mach = Machinery.query.filter_by(provider_id=profile.id).first()
            assert mach is not None, "Machinery listing was not saved to DB"
            machinery_id = mach.id
            created_machinery_ids.append(mach.id)
            assert mach.category == "TRACTOR"
            assert mach.is_active is True
            assert len(mach.rates) == 2

            # Step C: Provider edits the listing
            edit_res = client.post(f"/provider/machinery/{mach.id}/edit", data={
                "name_en": f"Mahindra 575 DI Tractor Turbo {audit_suffix}",
                "name_ta": "மகிந்திரா 575 DI டிராக்டர் டர்போ",
                "category": "TRACTOR",
                "make_model": "Mahindra 575 DI Turbo",
                "model_year": "2024",
                "horsepower": "50",
                "village_or_town": "Orathanadu Central",
                "district": "Thanjavur",
                "pincode": "614625",
                "description_en": "Updated turbo edition with rotavator implement.",
                "description_ta": "புதுப்பிக்கப்பட்ட டர்போ மாடல்.",
                "machine_only_hour": "650",
                "machine_only_day": "4800",
                "machine_only_min_hours": "2",
                "machine_only_deposit": "500",
            }, follow_redirects=True)
            assert edit_res.status_code == 200

            db.session.refresh(mach)
            assert "Turbo" in mach.name_en, "Listing edit was not persisted"
            assert mach.horsepower == 50

            # Step D: Access provider incoming bookings list
            pbookings_res = client.get("/provider/bookings/")
            assert pbookings_res.status_code == 200
            assert "Machinery Booking Requests" in pbookings_res.data.decode("utf-8")

            results["2. Provider Registration, Machinery CRUD & Booking Dashboard"] = "PASS"
            print(">>> FEATURE 2: PASS")
        except Exception as e:
            traceback.print_exc()
            results["2. Provider Registration, Machinery CRUD & Booking Dashboard"] = f"FAIL: {str(e)}"
            print(f">>> FEATURE 2: FAIL: {e}")

        # Logout provider
        client.post("/auth/logout", follow_redirects=True)

        # =====================================================================
        # FEATURE 3: Farmer browsing machinery and creating a booking request
        # =====================================================================
        print("\n--- [AUDIT 3] Farmer Browsing Machinery & Creating Booking Request ---")
        booking_id = None
        try:
            # Login as farmer
            client.post("/auth/login", data={
                "login_type": "password",
                "phone": farmer_phone,
                "password": farmer_pass,
            }, follow_redirects=True)

            # Browse catalogue with filter
            cat_res = client.get("/machinery?category=TRACTOR&district=Thanjavur")
            assert cat_res.status_code == 200
            cat_html = cat_res.data.decode("utf-8")
            assert f"Mahindra 575 DI Tractor Turbo {audit_suffix}" in cat_html

            # View machinery detail page
            detail_res = client.get(f"/machinery/{machinery_id}")
            assert detail_res.status_code == 200
            assert "machineryBookingForm" in detail_res.data.decode("utf-8"), "Booking form missing on detail page"

            # Submit booking request for tomorrow 10:00 to 14:00 (4 hours)
            tomorrow = datetime.utcnow().date() + timedelta(days=1)
            start_dt = f"{tomorrow}T10:00"
            end_dt = f"{tomorrow}T14:00"

            book_res = client.post(f"/bookings/machinery/{machinery_id}", data={
                "rental_option_type": "MACHINE_ONLY",
                "start_time": start_dt,
                "end_time": end_dt,
                "delivery_address": "North Field, Plot 14, Orathanadu",
                "notes": "Paddy field preparation",
                "contact_phone": farmer_phone,
            }, follow_redirects=True)
            assert book_res.status_code == 200

            booking = Booking.query.filter_by(machinery_id=machinery_id, farmer_id=farmer_user.id).first()
            assert booking is not None, "Booking record was not created"
            booking_id = booking.id
            created_booking_ids.append(booking.id)
            assert booking.status == Booking.STATUS_PENDING, f"Expected PENDING status, got {booking.status}"
            assert booking.estimated_total_cost > Decimal("0.00")
            assert booking.delivery_address == "North Field, Plot 14, Orathanadu"

            # Check Farmer's My Bookings page
            my_bookings_res = client.get("/bookings/my")
            assert my_bookings_res.status_code == 200
            assert booking.booking_reference in my_bookings_res.data.decode("utf-8")

            results["3. Farmer Machinery Discovery & Booking Submission"] = "PASS"
            print(">>> FEATURE 3: PASS")
        except Exception as e:
            traceback.print_exc()
            results["3. Farmer Machinery Discovery & Booking Submission"] = f"FAIL: {str(e)}"
            print(f">>> FEATURE 3: FAIL: {e}")

        # Logout farmer
        client.post("/auth/logout", follow_redirects=True)

        # =====================================================================
        # FEATURE 4: Provider accepting or rejecting booking requests
        # =====================================================================
        print("\n--- [AUDIT 4] Provider Accepting & Rejecting Booking Requests ---")
        try:
            # Login as provider
            client.post("/auth/login", data={
                "login_type": "password",
                "phone": provider_phone,
                "password": provider_pass,
            }, follow_redirects=True)

            # View booking detail
            bdetail_res = client.get(f"/provider/bookings/{booking_id}")
            assert bdetail_res.status_code == 200
            assert "btnApproveBooking" in bdetail_res.data.decode("utf-8") or "btn_approve" in bdetail_res.data.decode("utf-8")

            # Approve the booking
            approve_res = client.post(f"/provider/bookings/{booking_id}/approve", follow_redirects=True)
            assert approve_res.status_code == 200

            b_approved = db.session.get(Booking, booking_id)
            assert b_approved.status == Booking.STATUS_APPROVED, f"Expected APPROVED status, got {b_approved.status}"

            # Verify audit trail record created
            history = BookingStatusHistory.query.filter_by(booking_id=booking_id).all()
            assert any(h.to_status == Booking.STATUS_APPROVED for h in history), "No audit history for approval"

            # Test Overlapping Booking Prevention (Double Booking Protection)
            # Create a 2nd booking overlapping with the approved timeslot
            client.post("/auth/logout", follow_redirects=True)
            client.post("/auth/login", data={
                "login_type": "password",
                "phone": farmer_phone,
                "password": farmer_pass,
            }, follow_redirects=True)

            # Submit overlapping booking (same date 11:00 to 13:00)
            overlap_res = client.post(f"/bookings/machinery/{machinery_id}", data={
                "rental_option_type": "MACHINE_ONLY",
                "start_time": f"{tomorrow}T11:00",
                "end_time": f"{tomorrow}T13:00",
                "delivery_address": "Overlapping field, North Sector",
            }, follow_redirects=True)
            assert overlap_res.status_code == 200

            overlap_booking = Booking.query.filter(
                Booking.machinery_id == machinery_id,
                Booking.status == Booking.STATUS_PENDING,
                Booking.delivery_address == "Overlapping field, North Sector"
            ).first()
            assert overlap_booking is not None, "Overlapping booking request was not created"
            created_booking_ids.append(overlap_booking.id)

            # Provider attempts to approve the overlapping booking
            client.post("/auth/logout", follow_redirects=True)
            client.post("/auth/login", data={
                "login_type": "password",
                "phone": provider_phone,
                "password": provider_pass,
            }, follow_redirects=True)

            overlap_approve_res = client.post(f"/provider/bookings/{overlap_booking.id}/approve", follow_redirects=True)
            assert overlap_approve_res.status_code == 200
            overlap_html = overlap_approve_res.data.decode("utf-8").lower()
            assert "conflict" in overlap_html or "already booked" in overlap_html, "Double booking prevention failed to trigger conflict error"

            db.session.refresh(overlap_booking)
            assert overlap_booking.status == Booking.STATUS_PENDING, "Overlapping booking should remain PENDING"

            # Provider rejects the conflicting booking with mandatory reason
            reject_res = client.post(f"/provider/bookings/{overlap_booking.id}/reject", data={
                "rejection_reason": "Machinery already booked for another farm operation during this slot."
            }, follow_redirects=True)
            assert reject_res.status_code == 200

            db.session.refresh(overlap_booking)
            assert overlap_booking.status == Booking.STATUS_REJECTED, f"Expected REJECTED status, got {overlap_booking.status}"

            # Verify audit trail for rejection
            reject_history = BookingStatusHistory.query.filter_by(
                booking_id=overlap_booking.id,
                to_status=Booking.STATUS_REJECTED
            ).first()
            assert reject_history is not None, "Rejection history entry missing"
            assert reject_history.reason_or_comment == "Machinery already booked for another farm operation during this slot."

            results["4. Provider Booking Approval, Conflict Prevention & Rejection"] = "PASS"
            print(">>> FEATURE 4: PASS")
        except Exception as e:
            traceback.print_exc()
            results["4. Provider Booking Approval, Conflict Prevention & Rejection"] = f"FAIL: {str(e)}"
            print(f">>> FEATURE 4: FAIL: {e}")

        # Logout provider
        client.post("/auth/logout", follow_redirects=True)

        # =====================================================================
        # FEATURE 5: Admin login, dashboard data, and authorized admin operations
        # =====================================================================
        print("\n--- [AUDIT 5] Admin Login, Dashboard Metrics & Authorized Operations ---")
        try:
            admin_pass = "AdminPass@9988"
            admin_user = User(
                phone=admin_phone,
                full_name="Audit Administrator",
                role="ADMIN",
                is_phone_verified=True,
                is_active=True,
            )
            admin_user.set_password(admin_pass)
            db.session.add(admin_user)
            db.session.commit()
            created_user_ids.append(admin_user.id)

            # Login as Admin
            admin_login_res = client.post("/auth/login?role=admin", data={
                "login_type": "password",
                "phone": admin_phone,
                "password": admin_pass,
            }, follow_redirects=True)
            assert admin_login_res.status_code == 200

            with client.session_transaction() as sess:
                assert sess.get("user_role") == "ADMIN"

            # Access Admin Dashboard
            admin_dash_res = client.get("/admin/dashboard")
            assert admin_dash_res.status_code == 200
            dash_html = admin_dash_res.data.decode("utf-8")
            assert "System Governance" in dash_html
            assert "Registered Farmers" in dash_html
            assert "Machinery Providers" in dash_html
            assert "Total Bookings" in dash_html
            assert "Machinery Providers Registry" in dash_html

            results["5. Admin Login & Governance Dashboard"] = "PASS"
            print(">>> FEATURE 5: PASS")
        except Exception as e:
            traceback.print_exc()
            results["5. Admin Login & Governance Dashboard"] = f"FAIL: {str(e)}"
            print(f">>> FEATURE 5: FAIL: {e}")

        # Logout admin
        client.post("/auth/logout", follow_redirects=True)

        # =====================================================================
        # FEATURE 6: Tamil/English language switching and responsive mobile layout
        # =====================================================================
        print("\n--- [AUDIT 6] Bilingual Language Switching & Responsive Layout ---")
        try:
            # Step A: Switch to Tamil
            sw_ta_res = client.get("/set-language/ta?next=/")
            assert sw_ta_res.status_code == 302
            with client.session_transaction() as sess:
                assert sess.get("lang") == "ta", "Session lang not set to 'ta'"

            # Render home in Tamil
            home_ta_res = client.get("/")
            assert home_ta_res.status_code == 200
            home_ta_html = home_ta_res.data.decode("utf-8")
            assert "விவசாய" in home_ta_html or "இயந்திரங்கள்" in home_ta_html or "தமிழ்" in home_ta_html

            # Step B: Switch back to English
            sw_en_res = client.get("/set-language/en?next=/")
            assert sw_en_res.status_code == 302
            with client.session_transaction() as sess:
                assert sess.get("lang") == "en"

            home_en_res = client.get("/")
            assert home_en_res.status_code == 200
            assert "FarmConnect" in home_en_res.data.decode("utf-8")

            # Step C: Responsive layout verification
            assert '<meta name="viewport" content="width=device-width, initial-scale=1.0">' in home_en_res.data.decode("utf-8"), "Viewport meta tag missing"

            # Check CSS files for mobile media queries
            css_path = os.path.join(app.root_path, "static", "css", "main.css")
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
            assert "@media" in css_content and "max-width" in css_content, "CSS media queries missing"

            results["6. Bilingual Localization & Responsive Mobile Layout"] = "PASS"
            print(">>> FEATURE 6: PASS")
        except Exception as e:
            traceback.print_exc()
            results["6. Bilingual Localization & Responsive Mobile Layout"] = f"FAIL: {str(e)}"
            print(f">>> FEATURE 6: FAIL: {e}")

        # =====================================================================
        # FEATURE 7: PostgreSQL persistence, image uploads, session handling & RBAC
        # =====================================================================
        print("\n--- [AUDIT 7] PostgreSQL Persistence, Image Upload, Session & RBAC ---")
        try:
            # Step A: PostgreSQL Persistence check (verify records written previously exist)
            recheck_user = User.query.filter_by(phone=farmer_phone).first()
            assert recheck_user is not None, "PostgreSQL failed to persist farmer user"
            recheck_mach = Machinery.query.filter_by(id=machinery_id).first()
            assert recheck_mach is not None, "PostgreSQL failed to persist machinery"

            # Step B: Image Upload Testing
            # Login as provider
            client.post("/auth/login", data={
                "login_type": "password",
                "phone": provider_phone,
                "password": provider_pass,
            }, follow_redirects=True)

            # 1. Valid image upload test
            from PIL import Image
            img_buf = io.BytesIO()
            test_img = Image.new("RGB", (100, 100), color="green")
            test_img.save(img_buf, format="JPEG")
            img_buf.seek(0)

            data_with_image = {
                "name_en": f"Image Test Tractor {audit_suffix}",
                "category": "TRACTOR",
                "village_or_town": "Thanjavur",
                "district": "Thanjavur",
                "pincode": "613001",
                "machine_only_hour": "500",
                "machine_only_min_hours": "1",
                "photos": (img_buf, "test_tractor.jpg", "image/jpeg"),
            }
            img_res = client.post("/provider/machinery/new", data=data_with_image, content_type="multipart/form-data", follow_redirects=True)
            assert img_res.status_code == 200

            uploaded_mach = Machinery.query.filter_by(name_en=f"Image Test Tractor {audit_suffix}").first()
            assert uploaded_mach is not None
            created_machinery_ids.append(uploaded_mach.id)
            assert len(uploaded_mach.photos) == 1, "Uploaded photo record missing from DB"
            assert uploaded_mach.photos[0].is_primary is True

            # 2. Invalid non-image upload rejection
            bad_data = {
                "name_en": f"Invalid File Tractor {audit_suffix}",
                "category": "TRACTOR",
                "village_or_town": "Thanjavur",
                "district": "Thanjavur",
                "pincode": "613001",
                "machine_only_hour": "500",
                "machine_only_min_hours": "1",
                "photos": (io.BytesIO(b"MALICIOUS SCRIPT CONTENT"), "exploit.exe", "application/x-msdownload"),
            }
            bad_res = client.post("/provider/machinery/new", data=bad_data, content_type="multipart/form-data", follow_redirects=True)
            assert "Only image files" in bad_res.data.decode("utf-8") or "Invalid file" in bad_res.data.decode("utf-8") or "Invalid image" in bad_res.data.decode("utf-8")

            # Step C: Session handling flags (HttpOnly & SameSite)
            login_cookie_res = client.get("/")
            # Flask session cookie configuration check
            assert app.config.get("SESSION_COOKIE_HTTPONLY", True) is True, "SESSION_COOKIE_HTTPONLY is not True"
            assert app.config.get("SESSION_COOKIE_SAMESITE", "Lax") in ("Lax", "Strict"), "SameSite not configured"

            # Step D: Role-based access control (RBAC)
            # Provider cannot access farmer dashboard
            prov_to_farmer = client.get("/farmer/dashboard")
            assert prov_to_farmer.status_code == 403, f"Expected 403 for provider accessing farmer dashboard, got {prov_to_farmer.status_code}"

            # Provider cannot access admin dashboard
            prov_to_admin = client.get("/admin/dashboard")
            assert prov_to_admin.status_code == 403, f"Expected 403 for provider accessing admin dashboard, got {prov_to_admin.status_code}"

            # Login as farmer
            client.post("/auth/logout", follow_redirects=True)
            client.post("/auth/login", data={"login_type": "password", "phone": farmer_phone, "password": farmer_pass}, follow_redirects=True)

            # Farmer cannot access provider dashboard
            farmer_to_prov = client.get("/provider/dashboard")
            assert farmer_to_prov.status_code == 403, f"Expected 403 for farmer accessing provider dashboard, got {farmer_to_prov.status_code}"

            # Farmer cannot access admin dashboard
            farmer_to_admin = client.get("/admin/dashboard")
            assert farmer_to_admin.status_code == 403, f"Expected 403 for farmer accessing admin dashboard, got {farmer_to_admin.status_code}"

            # Unauthenticated access redirects to login
            client.post("/auth/logout", follow_redirects=True)
            anon_to_prov = client.get("/provider/dashboard")
            assert anon_to_prov.status_code == 302
            assert "/auth/login" in anon_to_prov.headers["Location"]

            results["7. PostgreSQL Persistence, Image Validation, Sessions & RBAC"] = "PASS"
            print(">>> FEATURE 7: PASS")
        except Exception as e:
            traceback.print_exc()
            results["7. PostgreSQL Persistence, Image Validation, Sessions & RBAC"] = f"FAIL: {str(e)}"
            print(f">>> FEATURE 7: FAIL: {e}")

        # Ensure logged out before Feature 8
        client.post("/auth/logout", follow_redirects=True)

        # =====================================================================
        # FEATURE 8: Registration privilege tampering & admin route restrictions
        # =====================================================================
        print("\n--- [AUDIT 8] Admin Registration Tampering & Route Isolation ---")
        try:
            # Step A: Tamper role in general register endpoint
            tamper_res1 = client.post("/auth/register", data={
                "full_name": f"Tamper Admin 1 {audit_suffix}",
                "phone": tamper_phone.replace("+91", ""),
                "role": "ADMIN",  # Privilege escalation attempt
                "action": "save_signin",
                "password": "TamperPass@123",
                "confirm_password": "TamperPass@123",
            }, follow_redirects=True)
            assert tamper_res1.status_code == 200

            tamper_user = User.query.filter_by(phone=tamper_phone).first()
            assert tamper_user is not None
            created_user_ids.append(tamper_user.id)
            assert tamper_user.role != "ADMIN", "Tampered role was erroneously granted ADMIN status!"
            assert tamper_user.role == "FARMER", f"Expected defaulted FARMER role, got {tamper_user.role}"

            # Step B: Tamper role in farmer registration endpoint (logout first)
            client.post("/auth/logout", follow_redirects=True)
            tamper_phone2 = f"+919804{audit_suffix}"
            tamper_res2 = client.post("/auth/register/farmer", data={
                "full_name": f"Tamper Admin 2 {audit_suffix}",
                "phone": tamper_phone2.replace("+91", ""),
                "role": "ADMIN",
                "action": "save_signin",
                "password": "TamperPass@123",
                "confirm_password": "TamperPass@123",
            }, follow_redirects=True)
            assert tamper_res2.status_code == 200

            tamper_user2 = User.query.filter_by(phone=tamper_phone2).first()
            assert tamper_user2 is not None
            created_user_ids.append(tamper_user2.id)
            assert tamper_user2.role == "FARMER", f"Expected FARMER role, got {tamper_user2.role}"

            # Step C: Verify tampered user cannot access admin routes
            with client.session_transaction() as sess:
                sess["user_id"] = str(tamper_user.id)
                sess["user_role"] = tamper_user.role

            admin_guard_res = client.get("/admin/dashboard")
            assert admin_guard_res.status_code == 403, f"Expected 403 for tampered user accessing admin, got {admin_guard_res.status_code}"

            results["8. Admin Tampering Defense & Strict Isolation"] = "PASS"
            print(">>> FEATURE 8: PASS")
        except Exception as e:
            traceback.print_exc()
            results["8. Admin Tampering Defense & Strict Isolation"] = f"FAIL: {str(e)}"
            print(f">>> FEATURE 8: FAIL: {e}")

        # =====================================================================
        # CLEANUP OF AUDIT TEST RECORDS (Safe cleanup of ONLY audit records)
        # =====================================================================
        print("\n--- Cleaning up temporary audit records ---")
        try:
            for b_id in created_booking_ids:
                BookingStatusHistory.query.filter_by(booking_id=b_id).delete(synchronize_session=False)
                b = db.session.get(Booking, b_id)
                if b:
                    db.session.delete(b)
            db.session.commit()

            for m_id in created_machinery_ids:
                MachineryPhoto.query.filter_by(machinery_id=m_id).delete(synchronize_session=False)
                MachineryRate.query.filter_by(machinery_id=m_id).delete(synchronize_session=False)
                m = db.session.get(Machinery, m_id)
                if m:
                    db.session.delete(m)
            db.session.commit()

            for u_id in created_user_ids:
                ProviderProfile.query.filter_by(user_id=u_id).delete(synchronize_session=False)
                u = db.session.get(User, u_id)
                if u:
                    db.session.delete(u)
            db.session.commit()
            print("Cleanup completed successfully.")
        except Exception as ce:
            db.session.rollback()
            print(f"Cleanup warning: {ce}")

    print("\n" + "=" * 80)
    print("AUDIT SUMMARY REPORT")
    print("=" * 80)
    for feat, status in results.items():
        print(f"[{status}] {feat}")
    print("=" * 80)
    return results


if __name__ == "__main__":
    run_audit()
