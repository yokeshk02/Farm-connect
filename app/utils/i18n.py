from flask import session

# Bilingual Translations Dictionary for English (en) and Tamil (ta)
TRANSLATIONS = {
    # Brand and Header Navigation
    "app.name": {
        "en": "FarmConnect",
        "ta": "விவசாய இணைப்பு (FarmConnect)",
    },
    "app.tagline": {
        "en": "Smart Machinery Rentals for Farmers",
        "ta": "விவசாயிகளுக்கான நவீன இயந்திர வாடகை தளம்",
    },
    "nav.home": {
        "en": "Home",
        "ta": "முகப்பு",
    },
    "nav.machinery": {
        "en": "Machinery Rentals",
        "ta": "இயந்திரங்கள்",
    },
    "nav.how_it_works": {
        "en": "How It Works",
        "ta": "எப்படி செயல்படுகிறது",
    },
    "nav.contact": {
        "en": "Contact Us",
        "ta": "தொடர்புக்கு",
    },
    "nav.provider_dashboard": {
        "en": "Provider Dashboard",
        "ta": "கட்டுப்பாட்டகம்",
    },
    "nav.admin_dashboard": {
        "en": "Admin Dashboard",
        "ta": "நிர்வாகக் கட்டுப்பாட்டகம்",
    },
    "nav.my_bookings": {
        "en": "My Bookings",
        "ta": "என் முன்பதிவுகள்",
    },
    "nav.login": {
        "en": "Sign In",
        "ta": "உள்நுழைக",
    },
    "nav.register": {
        "en": "Register",
        "ta": "பதிவு செய்க",
    },
    "nav.profile": {
        "en": "My Profile",
        "ta": "என் சுயவிவரம்",
    },
    "nav.logout": {
        "en": "Sign Out",
        "ta": "வெளியேறு",
    },
    "nav.language": {
        "en": "Language",
        "ta": "மொழி",
    },

    # Landing Page Hero and Content
    "hero.badge": {
        "en": "Smart Agricultural Equipment Rental Platform",
        "ta": "நவீன விவசாய இயந்திர வாடகை தளம்",
    },
    "hero.title": {
        "en": "Modern Machinery for a Stronger Agriculture",
        "ta": "உங்கள் பண்ணைக்கான சரியான விவசாய இயந்திரங்களை கண்டறியுங்கள்",
    },
    "hero.subtitle": {
        "en": "Rent agricultural machinery easily, Increase productivity, Connect with trusted providers. Grow together.",
        "ta": "விவசாய இயந்திரங்களை எளிதாகவும் மலிவாகவும் வாடகைக்கு பெறுங்கள். உங்கள் அருகில் உள்ள உரிமையாளர்களிடம் இருந்து இயந்திரங்களை ஆராயுங்கள்.",
    },
    "hero.cta_browse": {
        "en": "Explore Machinery",
        "ta": "இயந்திரங்களை ஆராய்க",
    },
    "hero.cta_list": {
        "en": "List Your Machinery",
        "ta": "உங்கள் இயந்திரத்தை பட்டியலிடுங்கள்",
    },
    "hero.cta_register": {
        "en": "Join as Farmer / Provider",
        "ta": "விவசாயி / உரிமையாளராக இணையுங்கள்",
    },

    # 4-Step How It Works Section
    "how_it_works.pill": {
        "en": "Simple 4-Step Process",
        "ta": "4 எளிய படிகள்",
    },
    "how_it_works.title": {
        "en": "How FarmConnect Works",
        "ta": "எவ்வாறு செயல்படுகிறது",
    },
    "how_it_works.subtitle": {
        "en": "Four simple steps to find, book, and deploy machinery on your farm.",
        "ta": "இயந்திரங்களை எளிதில் கண்டறிந்து வாடகைக்கு பெற நான்கு எளிய படிகள்.",
    },
    "how_it_works.step1_title": {
        "en": "1. Search",
        "ta": "1. தேடுங்கள்",
    },
    "how_it_works.step1_desc": {
        "en": "Find machinery by location and category near your village or district.",
        "ta": "இருப்பிடம் மற்றும் வகை மூலம் அருகில் உள்ள இயந்திரங்களைக் கண்டறியவும்.",
    },
    "how_it_works.step2_title": {
        "en": "2. Compare",
        "ta": "2. ஒப்பிடுங்கள்",
    },
    "how_it_works.step2_desc": {
        "en": "Review photos, specifications, rental tiers, and verified owner rates.",
        "ta": "புகைப்படங்கள், விவரங்கள் மற்றும் வாடகை கட்டணங்களை சரிபார்க்கவும்.",
    },
    "how_it_works.step3_title": {
        "en": "3. Request Booking",
        "ta": "3. முன்பதிவு செய்க",
    },
    "how_it_works.step3_desc": {
        "en": "Submit a rental request with transparent upfront price estimates.",
        "ta": "வெளிப்படையான வாடகை மதிப்பீட்டுடன் முன்பதிவு கோரிக்கையை சமர்ப்பிக்கவும்.",
    },
    "how_it_works.step4_title": {
        "en": "4. Track Booking",
        "ta": "4. கண்காணிக்கவும்",
    },
    "how_it_works.step4_desc": {
        "en": "Review status, lock in dates, and view updates in My Bookings.",
        "ta": "என் முன்பதிவுகள் பக்கத்தில் நிலை மற்றும் வரலாற்றை சரிபார்க்கவும்.",
    },

    # Popular Machinery Categories
    "categories.pill": {
        "en": "Machinery Categories",
        "ta": "இயந்திர வகைகள்",
    },
    "categories.title": {
        "en": "Popular Machinery Categories",
        "ta": "பிரபலமான இயந்திர வகைகள்",
    },
    "categories.subtitle": {
        "en": "Browse mechanized equipment tailored for every farming requirement.",
        "ta": "உங்கள் விவசாயத் தேவைக்கேற்ப சிறந்த இயந்திரங்களைத் தேர்வு செய்யுங்கள்.",
    },

    # Why Choose FarmConnect Section
    "why_choose.pill": {
        "en": "Trust & Transparency",
        "ta": "நம்பகத்தன்மை & வெளிப்படைத்தன்மை",
    },
    "why_choose.title": {
        "en": "Why Choose FarmConnect?",
        "ta": "ஏன் ஃபார்ம்கனெக்ட்டை தேர்வு செய்ய வேண்டும்?",
    },
    "why_choose.subtitle": {
        "en": "Empowering rural communities with transparent equipment sharing.",
        "ta": "வெளிப்படையான இயந்திர பகிர்வு மூலம் கிராமப்புற விவசாயத்தை மேம்படுத்துகிறோம்.",
    },
    "why_choose.b1_title": {
        "en": "Wide Range of Machinery",
        "ta": "பல்வேறு வகையான இயந்திரங்கள்",
    },
    "why_choose.b1_desc": {
        "en": "Access tractors, harvesters, rotavators, tillers, and specialized farm equipment across Tamil Nadu.",
        "ta": "டிராக்டர்கள், அறுவடை இயந்திரங்கள், உழவு இயந்திரங்கள் மற்றும் பிற விவசாய உபகரணங்களை எளிதில் வாடகைக்கு பெறுங்கள்.",
    },
    "why_choose.b2_title": {
        "en": "Location-Based Search",
        "ta": "இருப்பிடம் சார்ந்த எளிதான தேடல்",
    },
    "why_choose.b2_desc": {
        "en": "Locate available machinery closest to your farmland by district, village, PIN code or GPS.",
        "ta": "உங்கள் நிலத்திற்கு மிக அருகில் உள்ள இயந்திரங்களை மாவட்டம், கிராமம் அல்லது ஜிபிஎஸ் மூலம் கண்டறியவும்.",
    },
    "why_choose.b3_title": {
        "en": "Direct Provider Contact",
        "ta": "உரிமையாளருடன் நேரடி தொடர்பு",
    },
    "why_choose.b3_desc": {
        "en": "Direct coordination with verified local equipment providers via phone and WhatsApp with zero middleman fee.",
        "ta": "இடைத்தரகர் கட்டணங்கள் இன்றி உள்ளூர் இயந்திர உரிமையாளர்களுடன் தொலைபேசி மற்றும் வாட்ஸ்அப் மூலம் தொடர்பு கொள்ளுங்கள்.",
    },
    "why_choose.b4_title": {
        "en": "Safe & Transparent Booking",
        "ta": "பாதுகாப்பான & வெளிப்படையான முன்பதிவு",
    },
    "why_choose.b4_desc": {
        "en": "Transparent hourly and daily estimates with automated scheduling conflict protection.",
        "ta": "வெளிப்படையான வாடகை மதிப்பீடு மற்றும் கால அட்டவணை முரண்பாடுகளை தடுக்கும் பாதுகாப்பான தொழில்நுட்ப அமைப்பு.",
    },

    # Stepper
    "stepper.step1": {
        "en": "Package",
        "ta": "தொகுப்பு",
    },
    "stepper.step2": {
        "en": "Schedule",
        "ta": "தேதிகள்",
    },
    "stepper.step3": {
        "en": "Estimate",
        "ta": "கட்டணம்",
    },
    "stepper.step4": {
        "en": "Confirm",
        "ta": "உறுதிசெய்க",
    },

    # Provider Dashboard
    "dashboard.welcome": {
        "en": "Welcome Back",
        "ta": "மீண்டும் வருக",
    },
    "dashboard.subtitle": {
        "en": "Manage your agricultural machinery fleet, incoming booking requests, and rental earnings.",
        "ta": "உங்கள் இயந்திரங்கள், பெறப்பட்ட வாடகைக் கோரிக்கைகள் மற்றும் வருவாயை நிர்வகிக்கவும்.",
    },
    "dashboard.total_machinery": {
        "en": "Total Machinery",
        "ta": "மொத்த இயந்திரங்கள்",
    },
    "dashboard.pending_requests": {
        "en": "Pending Requests",
        "ta": "நிலுவைக் கோரிக்கைகள்",
    },
    "dashboard.active_bookings": {
        "en": "Active Bookings",
        "ta": "நடப்பு முன்பதிவுகள்",
    },
    "dashboard.completed_bookings": {
        "en": "Completed Bookings",
        "ta": "நிறைவடைந்த முன்பதிவுகள்",
    },
    "dashboard.quick_actions": {
        "en": "Quick Actions",
        "ta": "விரைவுச் செயல்கள்",
    },
    "dashboard.action_my_machinery": {
        "en": "My Machinery Fleet",
        "ta": "என் இயந்திரங்கள்",
    },
    "dashboard.action_my_machinery_desc": {
        "en": "View, edit, or adjust pricing for listed equipment.",
        "ta": "இயந்திரங்களின் விவரங்கள் மற்றும் வாடகையை திருத்தவும்.",
    },
    "dashboard.action_add_machinery": {
        "en": "Add Machinery",
        "ta": "புதிய இயந்திரம் சேர்க்க",
    },
    "dashboard.action_add_machinery_desc": {
        "en": "Add a tractor, harvester, or tiller for rent.",
        "ta": "வாடகைக்கு புதிய இயந்திரத்தை சேர்க்கவும்.",
    },
    "dashboard.action_requests": {
        "en": "Booking Requests",
        "ta": "முன்பதிவுக் கோரிக்கைகள்",
    },
    "dashboard.action_requests_desc": {
        "en": "Approve, start, or manage incoming rental orders.",
        "ta": "பெறப்பட்ட வாடகை முன்பதிவுகளை நிர்வகிக்கவும்.",
    },
    "dashboard.recent_requests": {
        "en": "Recent Booking Requests",
        "ta": "சமீபத்திய முன்பதிவுக் கோரிக்கைகள்",
    },
    "dashboard.view_all": {
        "en": "View All Requests",
        "ta": "அனைத்தையும் காண்க",
    },

    # Contact Us Page
    "contact.title": {
        "en": "Contact FarmConnect Support",
        "ta": "உதவி மையத்தைத் தொடர்பு கொள்க",
    },
    "contact.subtitle": {
        "en": "Have questions, feedback, or need assistance? Our rural agricultural support team is here to help.",
        "ta": "கேள்விகள் அல்லது உதவி தேவையா? எங்கள் குழு உங்களுக்கு உதவ தயாராக உள்ளது.",
    },
    "contact.name": {
        "en": "Your Full Name",
        "ta": "உங்கள் முழுப் பெயர்",
    },
    "contact.phone_or_email": {
        "en": "Phone Number or Email Address",
        "ta": "மொபைல் எண் அல்லது மின்னஞ்சல்",
    },
    "contact.subject": {
        "en": "Subject / Topic",
        "ta": "பொருள் / தலைப்பு",
    },
    "contact.message": {
        "en": "Message",
        "ta": "உங்கள் செய்தி",
    },
    "contact.submit": {
        "en": "Submit Enquiry",
        "ta": "செய்தியை அனுப்புக",
    },
    "contact.success": {
        "en": "Thank you! Your enquiry has been received. Our team will contact you shortly.",
        "ta": "நன்றி! உங்கள் செய்தி பெறப்பட்டது. எங்கள் குழு விரைவில் தொடர்பு கொள்ளும்.",
    },
    "features.title": {
        "en": "Why Choose FarmConnect?",
        "ta": "விவசாய இணைப்பை ஏன் தேர்வு செய்ய வேண்டும்?",
    },
    "features.nearby_title": {
        "en": "Local Discovery",
        "ta": "உள்ளூர் தேடல்",
    },
    "features.nearby_desc": {
        "en": "Search equipment by your village, town, district, or PIN code with optional GPS support.",
        "ta": "கிராமம், வட்டம், மாவட்டம் அல்லது அஞ்சல் குறியீடு மூலம் அருகில் உள்ள உபகரணங்களை எளிதில் கண்டறியுங்கள்.",
    },
    "features.flexible_title": {
        "en": "3 Flexible Rental Tiers",
        "ta": "3 வகையான வாடகை விருப்பங்கள்",
    },
    "features.flexible_desc": {
        "en": "Choose Machine Only, Machine + Operator, or Machine + Operator + Field Labour.",
        "ta": "இயந்திரம் மட்டும், இயந்திரம் + ஓட்டுநர், அல்லது இயந்திரம் + ஓட்டுநர் + களப்பணியாளர் விருப்பங்களை தேர்வு செய்யலாம்.",
    },
    "features.direct_title": {
        "en": "Direct Connect",
        "ta": "நேரடி தொடர்பு",
    },
    "features.direct_desc": {
        "en": "Instant telephonic Call or WhatsApp chat directly with verified equipment owners.",
        "ta": "சரிபார்க்கப்பட்ட இயந்திர உரிமையாளர்களுடன் தொலைபேசி அழைப்பு அல்லது வாட்ஸ்அப் மூலம் உடனடியாக பேசுங்கள்.",
    },

    # Authentication - Login
    "auth.login_title": {
        "en": "Welcome Back to FarmConnect",
        "ta": "விவசாய இணைப்புக்கு மீண்டும் வருக",
    },
    "auth.login_subtitle": {
        "en": "Enter your mobile number to receive a secure OTP verification code.",
        "ta": "பாதுகாப்பான OTP குறியீட்டைப் பெற உங்கள் மொபைல் எண்ணை உள்ளிடவும்.",
    },
    "auth.phone_label": {
        "en": "Mobile Phone Number",
        "ta": "மொபைல் எண்",
    },
    "auth.phone_placeholder": {
        "en": "e.g. 9876543210 or +919876543210",
        "ta": "உதா: 9876543210",
    },
    "auth.btn_send_otp": {
        "en": "Send OTP Code",
        "ta": "OTP குறியீடு அனுப்புக",
    },
    "auth.no_account": {
        "en": "Don't have an account?",
        "ta": "கணக்கு இல்லையா?",
    },
    "auth.register_now": {
        "en": "Register Now",
        "ta": "இப்போதே பதிவு செய்க",
    },
    "auth.admin_login_tab": {
        "en": "Login with Password",
        "ta": "கடவுச்சொல் மூலம் உள்நுழைக",
    },
    "auth.password_login_tab": {
        "en": "Login with Password",
        "ta": "கடவுச்சொல் மூலம் உள்நுழைக",
    },
    "auth.otp_login_tab": {
        "en": "Login with OTP",
        "ta": "OTP மூலம் உள்நுழைக",
    },
    "auth.password_label": {
        "en": "Password",
        "ta": "கடவுச்சொல்",
    },
    "auth.btn_login_password": {
        "en": "Sign In with Password",
        "ta": "கடவுச்சொல் மூலம் உள்நுழைக",
    },
    "auth.show_password": {
        "en": "Show",
        "ta": "காட்டு",
    },
    "auth.hide_password": {
        "en": "Hide",
        "ta": "மறை",
    },
    "auth.password_help_message": {
        "en": "Haven't set a password yet or forgot it? Switch to the Login with OTP tab to sign in with your phone number, then set your password anytime in your profile settings.",
        "ta": "கடவுச்சொல் அமைக்கவில்லையா அல்லது மறந்துவிட்டதா? உங்கள் மொபைல் எண்ணைக் கொண்டு உள்நுழைய OTP மூலம் உள்நுழைக தாவலுக்கு மாறவும், பின்னர் உங்கள் சுயவிவர அமைப்புகளில் கடவுச்சொல்லை அமைக்கலாம்.",
    },

    # Authentication - Register
    "auth.register_title": {
        "en": "Create Your FarmConnect Account",
        "ta": "விவசாய இணைப்பு கணக்கை உருவாக்கவும்",
    },
    "auth.register_subtitle": {
        "en": "Sign up with your phone number to rent or list agricultural machinery.",
        "ta": "இயந்திரங்களை வாடகைக்கு எடுக்க அல்லது வாடகைக்கு விட பதிவு செய்யுங்கள்.",
    },
    "auth.name_label": {
        "en": "Full Name",
        "ta": "முழு பெயர்",
    },
    "auth.name_placeholder": {
        "en": "Enter your full name",
        "ta": "உங்கள் பெயரை உள்ளிடவும்",
    },
    "auth.role_label": {
        "en": "I want to register as:",
        "ta": "நான் பதிவு செய்ய விரும்புவது:",
    },
    "auth.role_farmer": {
        "en": "Farmer (Looking to rent machinery)",
        "ta": "விவசாயி (இயந்திரங்களை வாடகைக்கு எடுக்க)",
    },
    "auth.role_provider": {
        "en": "Equipment Provider (Have machinery to rent out)",
        "ta": "உபகரண உரிமையாளர் (இயந்திரங்களை வாடகைக்கு விட)",
    },
    "auth.preferred_lang_label": {
        "en": "Preferred Language",
        "ta": "விருப்பமான மொழி",
    },
    "auth.password_optional": {
        "en": "Create Password (Optional - for Password Login)",
        "ta": "கடவுச்சொல் அமைத்தல் (விருப்பத்தேர்வு)",
    },
    "auth.confirm_password_label": {
        "en": "Confirm Password",
        "ta": "கடவுச்சொல்லை உறுதிசெய்க",
    },
    "auth.password_rules_tip": {
        "en": "Password must be at least 6 characters long.",
        "ta": "குறைந்தது 6 எழுத்துக்கள் இருக்க வேண்டும்.",
    },
    "auth.btn_register": {
        "en": "Continue to Phone Verification",
        "ta": "மொபைல் சரிபார்ப்புக்கு தொடரவும்",
    },
    "auth.have_account": {
        "en": "Already have an account?",
        "ta": "ஏற்கனவே கணக்கு உள்ளதா?",
    },
    "auth.login_link": {
        "en": "Sign In here",
        "ta": "இங்கு உள்நுழையவும்",
    },

    # Authentication - OTP Verification
    "auth.verify_title": {
        "en": "Enter Verification Code",
        "ta": "சரிபார்ப்புக் குறியீட்டை உள்ளிடவும்",
    },
    "auth.verify_subtitle": {
        "en": "We have sent a 6-digit OTP code to your phone number:",
        "ta": "உங்கள் மொபைல் எண்ணிற்கு 6 இலக்க OTP குறியீடு அனுப்பப்பட்டுள்ளது:",
    },
    "auth.otp_label": {
        "en": "6-Digit OTP Code",
        "ta": "6 இலக்க OTP குறியீடு",
    },
    "auth.otp_placeholder": {
        "en": "123456",
        "ta": "123456",
    },
    "auth.btn_verify": {
        "en": "Verify & Sign In",
        "ta": "சரிபார்த்து உள்நுழைக",
    },
    "auth.resend_text": {
        "en": "Didn't receive code?",
        "ta": "குறியீடு வரவில்லையா?",
    },
    "auth.btn_resend": {
        "en": "Resend OTP",
        "ta": "மீண்டும் OTP அனுப்புக",
    },
    "auth.dev_tip": {
        "en": "Local Development Tip: Check your local server terminal console to view the mock OTP code.",
        "ta": "உள்ளூர் சோதனை குறிப்பு: சர்வர் டெர்மினல் கன்சோலில் மாதிரி OTP குறியீட்டைக் காணவும்.",
    },

    # Profile Page
    "profile.title": {
        "en": "My Profile",
        "ta": "என் சுயவிவரம்",
    },
    "profile.phone": {
        "en": "Phone Number",
        "ta": "மொபைல் எண்",
    },
    "profile.role": {
        "en": "Account Role",
        "ta": "கணக்கு வகை",
    },
    "profile.status": {
        "en": "Verification Status",
        "ta": "சரிபார்ப்பு நிலை",
    },
    "profile.verified": {
        "en": "Phone Verified",
        "ta": "மொபைல் எண் சரிபார்க்கப்பட்டது",
    },
    "profile.save": {
        "en": "Save Changes",
        "ta": "மாற்றங்களைச் சேமிக்கவும்",
    },
    "profile.password_section_title": {
        "en": "Security & Password Management",
        "ta": "பாதுகாப்பு & கடவுச்சொல் மேலாண்மை",
    },
    "profile.set_password_title": {
        "en": "Set Account Password",
        "ta": "கணக்கு கடவுச்சொல் அமைத்தல்",
    },
    "profile.set_password_desc": {
        "en": "Create a password to sign in directly with your phone number and password without waiting for OTP SMS.",
        "ta": "OTP குறுஞ்செய்திக்காக காத்திருக்காமல் உங்கள் மொபைல் எண் மற்றும் கடவுச்சொல் மூலம் நேரடியாக உள்நுழைய கடவுச்சொல்லை அமைக்கவும்.",
    },
    "profile.change_password_title": {
        "en": "Change Account Password",
        "ta": "கடவுச்சொல்லை மாற்றுதல்",
    },
    "profile.change_password_desc": {
        "en": "Update your current account password to keep your account secure.",
        "ta": "உங்கள் கணக்கைப் பாதுகாக்க தற்போதைய கடவுச்சொல்லை மாற்றவும்.",
    },
    "profile.current_password": {
        "en": "Current Password",
        "ta": "தற்போதைய கடவுச்சொல்",
    },
    "profile.new_password": {
        "en": "New Password",
        "ta": "புதிய கடவுச்சொல்",
    },
    "profile.confirm_new_password": {
        "en": "Confirm New Password",
        "ta": "புதிய கடவுச்சொல்லை உறுதிசெய்க",
    },
    "profile.btn_set_password": {
        "en": "Set Password",
        "ta": "கடவுச்சொல்லை சேமி",
    },
    "profile.btn_change_password": {
        "en": "Update Password",
        "ta": "கடவுச்சொல்லை புதுப்பி",
    },
    "profile.password_status_active": {
        "en": "Password is active. You can log in using either OTP or your Password.",
        "ta": "கடவுச்சொல் அமைக்கப்பட்டுள்ளது. நீங்கள் OTP அல்லது கடவுச்சொல் மூலம் உள்நுழையலாம்.",
    },
    "profile.password_status_none": {
        "en": "No password set yet. You currently sign in using phone OTP.",
        "ta": "இன்னும் கடவுச்சொல் அமைக்கப்படவில்லை. தற்போது நீங்கள் மொபைல் OTP மூலம் உள்நுழைகிறீர்கள்.",
    },

    # Footer
    "footer.about": {
        "en": "FarmConnect is committed to modernizing Indian agriculture through cooperative machinery sharing and digital accessibility.",
        "ta": "விவசாய இணைப்பு கூட்டு இயந்திரப் பகிர்வு மற்றும் டிஜிட்டல் அணுகல் மூலம் இந்திய விவசாயத்தை நவீனமயமாக்க உதவுகிறது.",
    },
    "footer.quick_links": {
        "en": "Quick Links",
        "ta": "முக்கிய இணைப்புகள்",
    },
    "footer.rights": {
        "en": "All rights reserved.",
        "ta": "அனைத்து உரிமைகளும் பாதுகாக்கப்பட்டவை.",
    },

    # Navigation additions
    "nav.my_machinery": {
        "en": "My Machinery",
        "ta": "என் இயந்திரங்கள்",
    },
    "nav.add_machinery": {
        "en": "Add Machinery",
        "ta": "புதிய இயந்திரம்",
    },

    # Categories
    "cat.ALL": {
        "en": "All Categories",
        "ta": "அனைத்தும்",
    },
    "cat.TRACTOR": {
        "en": "Tractors",
        "ta": "டிராக்டர்கள்",
    },
    "cat.HARVESTER": {
        "en": "Harvesters",
        "ta": "அறுவடை இயந்திரங்கள்",
    },
    "cat.TILLER": {
        "en": "Power Tillers",
        "ta": "உழவு இயந்திரங்கள்",
    },
    "cat.ROTAVATOR": {
        "en": "Rotavators",
        "ta": "ரோட்டாவேட்டர்கள்",
    },
    "cat.BACKHOE": {
        "en": "Backhoes",
        "ta": "பேக்ஹோ / ஜேசிபி",
    },
    "cat.THRESHER": {
        "en": "Threshers",
        "ta": "கதிர் அடிக்கும் இயந்திரங்கள்",
    },
    "cat.SPRAYER": {
        "en": "Sprayers",
        "ta": "தெளிப்பான்கள்",
    },
    "cat.BALER": {
        "en": "Balers",
        "ta": "வைக்கோல் கட்டும் இயந்திரங்கள்",
    },
    "cat.CULTIVATOR": {
        "en": "Cultivators",
        "ta": "களப்பைகள் / கल्टीவேட்டர்கள்",
    },
    "cat.OTHER": {
        "en": "Other Equipment",
        "ta": "பிற உபகரணங்கள்",
    },

    # Rental Packages
    "pkg.MACHINE_ONLY": {
        "en": "Machine Only",
        "ta": "இயந்திரம் மட்டும்",
    },
    "pkg.MACHINE_OPERATOR": {
        "en": "Machine + Operator",
        "ta": "இயந்திரம் + ஓட்டுநர்",
    },
    "pkg.MACHINE_OPERATOR_LABOUR": {
        "en": "Machine + Operator + Labour",
        "ta": "இயந்திரம் + ஓட்டுநர் + களப்பணியாளர்",
    },

    # Public Catalogue
    "catalogue.title": {
        "en": "Agricultural Machinery Catalogue",
        "ta": "விவசாய இயந்திரங்கள் பட்டியல்",
    },
    "catalogue.subtitle": {
        "en": "Browse and rent verified machinery across Tamil Nadu.",
        "ta": "தமிழ்நாடு முழுவதும் சரிபார்க்கப்பட்ட விவசாய இயந்திரங்களை வாடகைக்கு எடுக்கவும்.",
    },
    "catalogue.search_placeholder": {
        "en": "Search by machine name, make, or model...",
        "ta": "இயந்திரத்தின் பெயர் அல்லது மாடல் மூலம் தேடவும்...",
    },
    "catalogue.filter_district": {
        "en": "District",
        "ta": "மாவட்டம்",
    },
    "catalogue.all_districts": {
        "en": "All Districts",
        "ta": "அனைத்து மாவட்டங்கள்",
    },
    "catalogue.filter_category": {
        "en": "Category",
        "ta": "வகை",
    },
    "catalogue.all_categories": {
        "en": "All Categories",
        "ta": "அனைத்து வகைகள்",
    },
    "catalogue.filter_package": {
        "en": "Rental Package",
        "ta": "வாடகை தொகுப்பு",
    },
    "catalogue.all_packages": {
        "en": "All Packages",
        "ta": "அனைத்து தொகுப்புகள்",
    },
    "catalogue.filter_village": {
        "en": "Village / Town",
        "ta": "கிராமம் / நகரம்",
    },
    "catalogue.filter_pincode": {
        "en": "PIN Code",
        "ta": "அஞ்சல் குறியீடு",
    },
    "catalogue.btn_filter": {
        "en": "Filter",
        "ta": "வடிகட்டுக",
    },
    "catalogue.btn_reset": {
        "en": "Reset",
        "ta": "மீட்டமை",
    },
    "catalogue.use_gps": {
        "en": "Use My Location",
        "ta": "என் இருப்பிடம்",
    },
    "catalogue.gps_locating": {
        "en": "Locating...",
        "ta": "கண்டறியப்படுகிறது...",
    },
    "catalogue.gps_denied": {
        "en": "Location permission denied or unavailable.",
        "ta": "இருப்பிட அனுமதி மறுக்கப்பட்டது அல்லது கிடைக்கவில்லை.",
    },
    "catalogue.sort_by": {
        "en": "Sort By",
        "ta": "வரிசைப்படுத்து",
    },
    "catalogue.sort_newest": {
        "en": "Newest First",
        "ta": "புதியவை முதலில்",
    },
    "catalogue.sort_price_asc": {
        "en": "Price: Low to High",
        "ta": "விலை: குறைவிலிருந்து அதிகம்",
    },
    "catalogue.sort_price_desc": {
        "en": "Price: High to Low",
        "ta": "விலை: அதிகத்திலிருந்து குறைவு",
    },
    "catalogue.sort_distance": {
        "en": "Nearest First (GPS)",
        "ta": "அருகிலுள்ளவை (GPS)",
    },
    "catalogue.starts_from": {
        "en": "Starts from",
        "ta": "தொடக்க விலை",
    },
    "catalogue.per_hour": {
        "en": "/ hr",
        "ta": "/ மணிநேரம்",
    },
    "catalogue.per_day": {
        "en": "/ day",
        "ta": "/ நாள்",
    },
    "catalogue.view_details": {
        "en": "View Details",
        "ta": "விவரங்களைக் காண்க",
    },
    "catalogue.no_results_title": {
        "en": "No Machinery Found",
        "ta": "இயந்திரங்கள் எதுவும் கிடைக்கவில்லை",
    },
    "catalogue.no_results_desc": {
        "en": "No machinery matches your current search filters. Try clearing or broadening your search criteria.",
        "ta": "உங்கள் தேடலுக்குரிய இயந்திரங்கள் எதுவும் இல்லை. வடிகட்டிகளை மாற்றி மீண்டும் முயற்சிக்கவும்.",
    },
    "catalogue.results_count": {
        "en": "Found {count} listing(s)",
        "ta": "{count} இயந்திரங்கள் உள்ளன",
    },
    "catalogue.prev": {
        "en": "Previous",
        "ta": "முந்தைய",
    },
    "catalogue.next": {
        "en": "Next",
        "ta": "அடுத்த",
    },
    "catalogue.page_info": {
        "en": "Page {current} of {total}",
        "ta": "பக்கம் {current} / {total}",
    },

    # Machinery Detail Page
    "detail.title": {
        "en": "Machinery Details",
        "ta": "இயந்திர விவரங்கள்",
    },
    "detail.specifications": {
        "en": "Specifications",
        "ta": "தொழில்நுட்ப விவரங்கள்",
    },
    "detail.make_model": {
        "en": "Make & Model",
        "ta": "பிராண்டு & மாடல்",
    },
    "detail.year": {
        "en": "Year",
        "ta": "ஆண்டு",
    },
    "detail.hp": {
        "en": "Horsepower",
        "ta": "குதிரைத்திறன் (HP)",
    },
    "detail.location": {
        "en": "Base Location",
        "ta": "இயங்கும் இடம்",
    },
    "detail.description": {
        "en": "Equipment Description",
        "ta": "விளக்கம்",
    },
    "detail.rates_packages": {
        "en": "Available Rental Options & Pricing",
        "ta": "வாடகை விருப்பங்கள் & கட்டணம்",
    },
    "detail.min_duration": {
        "en": "Min Duration",
        "ta": "குறைந்தபட்ச காலம்",
    },
    "detail.security_deposit": {
        "en": "Security Deposit",
        "ta": "பாதுகாப்பு வைப்புத்தொகை",
    },
    "detail.hours": {
        "en": "hours",
        "ta": "மணிநேரம்",
    },
    "detail.provider_info": {
        "en": "Owner & Provider Details",
        "ta": "உரிமையாளர் விவரங்கள்",
    },
    "detail.verified": {
        "en": "Verified Equipment Owner",
        "ta": "சரிபார்க்கப்பட்ட உரிமையாளர்",
    },
    "detail.call_owner": {
        "en": "Call Equipment Owner",
        "ta": "உரிமையாளரை அழைக்கவும்",
    },
    "detail.whatsapp_owner": {
        "en": "Chat on WhatsApp",
        "ta": "வாட்ஸ்அப்பில் பேசுக",
    },
    "detail.booking_soon": {
        "en": "Direct online booking engine will be activated in the next milestone.",
        "ta": "ஆன்லைன் முன்பதிவு வசதி அடுத்த கட்டத்தில் தொடங்கப்படும்.",
    },
    "detail.back_catalogue": {
        "en": "Back to Catalogue",
        "ta": "பட்டியலுக்குத் திரும்பு",
    },

    # Provider Machinery Management
    "provider.my_machinery": {
        "en": "My Machinery Listings",
        "ta": "என் இயந்திரங்கள் பட்டியல்",
    },
    "provider.my_machinery_subtitle": {
        "en": "Manage your listed agricultural equipment, pricing packages, and availability.",
        "ta": "உங்கள் விவசாய இயந்திரங்கள், கட்டண தொகுப்புகள் மற்றும் இருப்பு நிலையை நிர்வகிக்கவும்.",
    },
    "provider.add_new": {
        "en": "Add Machinery",
        "ta": "புதிய இயந்திரத்தைச் சேர்",
    },
    "provider.no_machinery_title": {
        "en": "No Machinery Listed Yet",
        "ta": "இன்னும் இயந்திரங்கள் சேர்க்கப்படவில்லை",
    },
    "provider.no_machinery_desc": {
        "en": "Start earning by listing your tractors, harvesters, or tillers for rent.",
        "ta": "உங்கள் டிராக்டர்கள் அல்லது அறுவடை இயந்திரங்களை வாடகைக்கு பட்டியலிடுங்கள்.",
    },
    "provider.status_active": {
        "en": "Active",
        "ta": "செயல்பாட்டில் உள்ளது",
    },
    "provider.status_inactive": {
        "en": "Inactive (Hidden)",
        "ta": "முடக்கப்பட்டது (மறைக்கப்பட்டது)",
    },
    "provider.btn_deactivate": {
        "en": "Deactivate",
        "ta": "முடக்குக",
    },
    "provider.btn_activate": {
        "en": "Activate",
        "ta": "செயல்படுத்துக",
    },
    "provider.btn_edit": {
        "en": "Edit Listing",
        "ta": "திருத்து",
    },
    "provider.btn_view_public": {
        "en": "View Public Listing",
        "ta": "பொதுப் பக்கத்தைக் காண்க",
    },
    "provider.rates_count": {
        "en": "{count} package(s) configured",
        "ta": "{count} தொகுப்புகள் அமைக்கப்பட்டுள்ளன",
    },

    # Provider Listing Form
    "provider.form_new_title": {
        "en": "Add Agricultural Machinery",
        "ta": "புதிய விவசாய இயந்திரத்தைச் சேர்",
    },
    "provider.form_edit_title": {
        "en": "Edit Machinery Listing",
        "ta": "இயந்திரப் பட்டியலைத் திருத்து",
    },
    "provider.form_subtitle": {
        "en": "Provide specifications, rental tiers, and photos for farmers to discover your equipment.",
        "ta": "விவசாயிகள் கண்டறிய உங்கள் இயந்திரத்தின் விவரங்கள், வாடகை மற்றும் படங்களை உள்ளிடவும்.",
    },
    "provider.sec_basic": {
        "en": "1. Basic Equipment Information",
        "ta": "1. அடிப்படை விவரங்கள்",
    },
    "provider.sec_location": {
        "en": "2. Base Location",
        "ta": "2. இயக்க மையம் & இருப்பிடம்",
    },
    "provider.sec_rates": {
        "en": "3. Rental Options & Pricing",
        "ta": "3. வாடகை விருப்பங்கள் & கட்டணங்கள்",
    },
    "provider.sec_photos": {
        "en": "4. Photos (Up to 5 images)",
        "ta": "4. புகைப்படங்கள் (அதிகபட்சம் 5 படங்கள்)",
    },
    "provider.name_en": {
        "en": "Equipment Name (English)",
        "ta": "இயந்திரத்தின் பெயர் (ஆங்கிலம்)",
    },
    "provider.name_ta": {
        "en": "Equipment Name (Tamil)",
        "ta": "இயந்திரத்தின் பெயர் (தமிழ்)",
    },
    "provider.category": {
        "en": "Category",
        "ta": "வகை",
    },
    "provider.select_category": {
        "en": "-- Select Category --",
        "ta": "-- வகையைத் தேர்ந்தெடுக்கவும் --",
    },
    "provider.make_model": {
        "en": "Make / Model (e.g. Mahindra 575 DI)",
        "ta": "பிராண்டு / மாடல் (உதா: மஹிந்திரா 575 DI)",
    },
    "provider.year": {
        "en": "Model Year",
        "ta": "தயாரிப்பு ஆண்டு",
    },
    "provider.hp": {
        "en": "Horsepower (HP)",
        "ta": "குதிரைத்திறன் (HP)",
    },
    "provider.desc_en": {
        "en": "Description (English)",
        "ta": "விளக்கம் (ஆங்கிலம்)",
    },
    "provider.desc_ta": {
        "en": "Description (Tamil)",
        "ta": "விளக்கம் (தமிழ்)",
    },
    "provider.village": {
        "en": "Village / Town",
        "ta": "கிராமம் / நகரம்",
    },
    "provider.district": {
        "en": "District",
        "ta": "மாவட்டம்",
    },
    "provider.select_district": {
        "en": "-- Select District --",
        "ta": "-- மாவட்டத்தைத் தேர்ந்தெடுக்கவும் --",
    },
    "provider.pincode": {
        "en": "PIN Code (6 Digits)",
        "ta": "அஞ்சல் குறியீடு (6 இலக்கங்கள்)",
    },
    "provider.opt_machine_only": {
        "en": "Package 1: Machine Only",
        "ta": "விருப்பம் 1: இயந்திரம் மட்டும்",
    },
    "provider.opt_machine_operator": {
        "en": "Package 2: Machine + Operator",
        "ta": "விருப்பம் 2: இயந்திரம் + ஓட்டுநர்",
    },
    "provider.opt_machine_operator_labour": {
        "en": "Package 3: Machine + Operator + Field Labour",
        "ta": "விருப்பம் 3: இயந்திரம் + ஓட்டுநர் + களப்பணியாளர்",
    },
    "provider.rate_hour": {
        "en": "Rate per Hour (₹)",
        "ta": "மணிநேரக் கட்டணம் (₹)",
    },
    "provider.rate_day": {
        "en": "Rate per Day (₹)",
        "ta": "நாள் கட்டணம் (₹)",
    },
    "provider.min_hours": {
        "en": "Min Duration (Hours)",
        "ta": "குறைந்தபட்ச காலம் (மணிநேரம்)",
    },
    "provider.deposit": {
        "en": "Security Deposit (₹)",
        "ta": "பாதுகாப்பு வைப்பு (₹)",
    },
    "provider.upload_photos": {
        "en": "Upload Equipment Photos",
        "ta": "புகைப்படங்களை பதிவேற்றவும்",
    },
    "provider.photos_tip": {
        "en": "Max 5 photos in total. Supported formats: PNG, JPG, WEBP (Max 5MB each).",
        "ta": "அதிகபட்சம் 5 புகைப்படங்கள். அனுமதிக்கப்பட்ட வடிவங்கள்: PNG, JPG, WEBP (தலா 5MB வரை).",
    },
    "provider.current_photos": {
        "en": "Current Uploaded Photos",
        "ta": "தற்போதுள்ள புகைப்படங்கள்",
    },
    "provider.delete_photo": {
        "en": "Delete",
        "ta": "நீக்குக",
    },
    "provider.btn_save": {
        "en": "Create Machinery Listing",
        "ta": "இயந்திரப் பட்டியலை உருவாக்கு",
    },
    "provider.btn_update": {
        "en": "Save Changes",
        "ta": "மாற்றங்களைச் சேமி",
    },
    "provider.btn_cancel": {
        "en": "Cancel",
        "ta": "ரத்து செய்க",
    },

    # Canonical Booking Statuses
    "status.PENDING": {
        "en": "Pending",
        "ta": "நிலுவையில் உள்ளது",
    },
    "status.APPROVED": {
        "en": "Approved",
        "ta": "அங்கீகரிக்கப்பட்டது",
    },
    "status.IN_PROGRESS": {
        "en": "In Progress",
        "ta": "பயன்பாட்டில் உள்ளது",
    },
    "status.COMPLETED": {
        "en": "Completed",
        "ta": "நிறைவடைந்தது",
    },
    "status.CANCELLED": {
        "en": "Cancelled",
        "ta": "ரத்து செய்யப்பட்டது",
    },
    "status.REJECTED": {
        "en": "Declined",
        "ta": "நிராகரிக்கப்பட்டது",
    },

    # Booking Form & Estimate
    "booking.book_title": {
        "en": "Book this Machinery",
        "ta": "இந்த இயந்திரத்தை முன்பதிவு செய்க",
    },
    "booking.book_subtitle": {
        "en": "Select a package, pick your rental dates, and request this equipment.",
        "ta": "வாடகைத் தொகுப்பைத் தேர்ந்தெடுத்து, தேதிகளைக் குறிப்பிட்டு முன்பதிவு கோரவும்.",
    },
    "booking.select_package": {
        "en": "Select Rental Package",
        "ta": "வாடகைத் தொகுப்பைத் தேர்ந்தெடுக்கவும்",
    },
    "booking.start_time": {
        "en": "Rental Start Date & Time",
        "ta": "வாடகை தொடங்கும் நாள் & நேரம்",
    },
    "booking.end_time": {
        "en": "Rental End Date & Time",
        "ta": "வாடகை முடியும் நாள் & நேரம்",
    },
    "booking.delivery_address": {
        "en": "Farm / Delivery Location",
        "ta": "பண்ணை / வயல் இருப்பிடம்",
    },
    "booking.delivery_address_placeholder": {
        "en": "e.g., North Street field, near temple, Kumbakonam",
        "ta": "உதா: வடக்குத் தெரு வயல், கோவில் அருகில், கும்பகோணம்",
    },
    "booking.notes": {
        "en": "Booking Notes & Crop Details (Optional)",
        "ta": "கூடுதல் விவரங்கள் & பயிர் விபரம் (விருப்பத்தேர்வு)",
    },
    "booking.notes_placeholder": {
        "en": "e.g., Need for paddy harvesting across 3 acres",
        "ta": "உதா: 3 ஏக்கர் நெல் அறுவடைக்கு தேவைப்படுகிறது",
    },
    "booking.btn_estimate": {
        "en": "Check Price Estimate",
        "ta": "கட்டண மதிப்பீட்டைக் காண்க",
    },
    "booking.btn_submit": {
        "en": "Request Booking Now",
        "ta": "முன்பதிவு கோரிக்கை அனுப்பு",
    },
    "booking.estimated_cost": {
        "en": "Estimated Rental Cost",
        "ta": "உத்தேச வாடகைக் கட்டணம்",
    },
    "booking.deposit_note": {
        "en": "Security Deposit (Payable directly to provider)",
        "ta": "பாதுகாப்பு வைப்பு (உரிமையாளரிடம் நேரடியாக செலுத்தப்பட வேண்டும்)",
    },
    "booking.offline_notice": {
        "en": "No online payment required now. Settlement is done directly between farmer and equipment owner upon job completion.",
        "ta": "ஆன்லைன் கட்டணம் எதுவும் செலுத்தத் தேவையில்லை. பணி நிறைவடைந்ததும் கட்டணம் நேரடியாக உரிமையாளரிடம் செலுத்தப்படும்.",
    },
    "booking.login_to_book": {
        "en": "Sign In as Farmer to Book",
        "ta": "முன்பதிவு செய்ய விவசாயியாக உள்நுழையவும்",
    },
    "booking.provider_account_notice": {
        "en": "You are currently signed in with a Provider account. Machinery rentals must be booked using a Farmer account.",
        "ta": "நீங்கள் உரிமையாளர் கணக்கில் உள்நுழைந்துள்ளீர்கள். இயந்திரங்களை முன்பதிவு செய்ய விவசாயி கணக்கைப் பயன்படுத்தவும்.",
    },

    # Farmer My Bookings & Details
    "booking.my_bookings_title": {
        "en": "My Machinery Bookings",
        "ta": "எனது இயந்திர முன்பதிவுகள்",
    },
    "booking.my_bookings_subtitle": {
        "en": "Track the status of your equipment rental requests and bookings.",
        "ta": "உங்கள் இயந்திர வாடகை முன்பதிவுகளின் நிலையை இங்கு கண்காணிக்கலாம்.",
    },
    "booking.ref": {
        "en": "Booking Ref",
        "ta": "முன்பதிவு எண்",
    },
    "booking.machinery": {
        "en": "Machinery",
        "ta": "இயந்திரம்",
    },
    "booking.package": {
        "en": "Package",
        "ta": "தொகுப்பு",
    },
    "booking.status": {
        "en": "Status",
        "ta": "நிலை",
    },
    "booking.dates": {
        "en": "Rental Window",
        "ta": "வாடகைக்காலம்",
    },
    "booking.total_cost": {
        "en": "Estimated Total",
        "ta": "உத்தேச கட்டணம்",
    },
    "booking.actions": {
        "en": "Actions",
        "ta": "செயல்கள்",
    },
    "booking.view_details": {
        "en": "View Details",
        "ta": "விவரங்களைக் காண்க",
    },
    "booking.btn_cancel": {
        "en": "Cancel Booking",
        "ta": "முன்பதிவை ரத்து செய்க",
    },
    "booking.cancel_confirm": {
        "en": "Are you sure you want to cancel this booking request?",
        "ta": "இந்த முன்பதிவுக் கோரிக்கையை ரத்து செய்ய விரும்புகிறீர்களா?",
    },
    "booking.no_bookings": {
        "en": "You have not made any machinery booking requests yet.",
        "ta": "நீங்கள் இதுவரை எந்த இயந்திர முன்பதிவுக் கோரிக்கையும் செய்யவில்லை.",
    },
    "booking.explore_btn": {
        "en": "Explore Machinery Catalogue",
        "ta": "இயந்திரப் பட்டியலை உலாவுக",
    },
    "booking.detail_title": {
        "en": "Booking Details",
        "ta": "முன்பதிவு விவரங்கள்",
    },
    "booking.detail_subtitle": {
        "en": "Complete timeline, cost breakdown, and equipment details.",
        "ta": "முழு காலவரிசை, கட்டண விபரம் மற்றும் இயந்திர விவரங்கள்.",
    },
    "booking.date_time": {
        "en": "Date & Time",
        "ta": "தேதி & நேரம்",
    },
    "booking.duration": {
        "en": "Duration",
        "ta": "கால அளவு",
    },
    "booking.rental_package": {
        "en": "Rental Package",
        "ta": "வாடகைத் தொகுப்பு",
    },
    "booking.rental_rate": {
        "en": "Rental Rate",
        "ta": "வாடகைக் கட்டணம்",
    },
    "booking.estimated_price": {
        "en": "Estimated Rental Price",
        "ta": "மதிப்பிடப்பட்ட வாடகைக் கட்டணம்",
    },
    "booking.total_amount": {
        "en": "Total Amount",
        "ta": "மொத்தத் தொகை",
    },
    "booking.status_history": {
        "en": "Booking Status History",
        "ta": "முன்பதிவு நிலை வரலாறு",
    },
    "booking.back_my_bookings": {
        "en": "← Back to My Bookings",
        "ta": "← என் முன்பதிவுகளுக்குத் திரும்பு",
    },
    "booking.back_incoming": {
        "en": "← Back to Incoming Bookings",
        "ta": "← முன்பதிவுக் கோரிக்கைகளுக்குத் திரும்பு",
    },
    "booking.offline_settlement_note": {
        "en": "Offline Settlement: Payment is collected directly by the provider upon equipment inspection.",
        "ta": "நேரடி தீர்வு: உபகரண ஆய்வின் போது கட்டணம் நேரடியாக உரிமையாளரால் பெறப்படும்.",
    },
    "booking.timeline": {
        "en": "Status Audit Timeline",
        "ta": "முன்பதிவு நிலை காலவரிசை",
    },
    "booking.price_breakdown": {
        "en": "Rental Price Breakdown",
        "ta": "கட்டண விவரம்",
    },
    "booking.billable_duration": {
        "en": "Billable Duration",
        "ta": "கணக்கிடப்பட்ட காலம்",
    },
    "booking.equipment_info": {
        "en": "Equipment Information",
        "ta": "இயந்திர விவரங்கள்",
    },
    "booking.provider_info": {
        "en": "Equipment Provider",
        "ta": "இயந்திர உரிமையாளர்",
    },
    "booking.farmer_info": {
        "en": "Farmer / Customer",
        "ta": "விவசாயி விவரங்கள்",
    },

    # Provider Bookings Dashboard
    "provider.nav_bookings": {
        "en": "Booking Requests",
        "ta": "முன்பதிவுக் கோரிக்கைகள்",
    },
    "provider.bookings_title": {
        "en": "Machinery Booking Requests",
        "ta": "இயந்திர முன்பதிவுக் கோரிக்கைகள்",
    },
    "provider.bookings_subtitle": {
        "en": "Review, approve, and manage rental requests for your machinery listings.",
        "ta": "உங்கள் இயந்திரங்களுக்கான வாடகைக் கோரிக்கைகளை மதிப்பாய்வு செய்து நிர்வகிக்கவும்.",
    },
    "provider.tab_all": {
        "en": "All",
        "ta": "அனைத்தும்",
    },
    "provider.tab_pending": {
        "en": "Pending",
        "ta": "நிலுவையில்",
    },
    "provider.tab_approved": {
        "en": "Approved",
        "ta": "அங்கீகரிக்கப்பட்டவை",
    },
    "provider.tab_in_progress": {
        "en": "In Progress",
        "ta": "பயன்பாட்டில்",
    },
    "provider.tab_completed": {
        "en": "Completed",
        "ta": "நிறைவடைந்தவை",
    },
    "provider.btn_approve": {
        "en": "Approve Request",
        "ta": "கோரிக்கையை ஏற்கவும்",
    },
    "provider.btn_reject": {
        "en": "Decline Request",
        "ta": "நிராகரிக்கவும்",
    },
    "provider.btn_start": {
        "en": "Mark In Progress",
        "ta": "பணியைத் தொடங்கு",
    },
    "provider.btn_complete": {
        "en": "Mark Completed",
        "ta": "நிறைவடைந்ததாகக் குறி",
    },
    "provider.reject_reason_prompt": {
        "en": "Please provide a reason for declining this request (Required):",
        "ta": "இந்த கோரிக்கையை நிராகரிப்பதற்கான காரணத்தைக் குறிப்பிடவும் (கட்டாயம்):",
    },
    "provider.reject_reason_placeholder": {
        "en": "e.g., Scheduled maintenance, operator unavailable, etc.",
        "ta": "உதா: இயந்திரப் பராமரிப்பு, ஓட்டுநர் விடுப்பு, முதலியன.",
    },
    "provider.no_requests": {
        "en": "No booking requests found for this filter.",
        "ta": "இந்தப் பிரிவில் முன்பதிவுக் கோரிக்கைகள் எதுவும் இல்லை.",
    },
    "provider.approve_confirm": {
        "en": "Approve this booking? This will lock the timeslot and prevent conflicting bookings.",
        "ta": "இந்த முன்பதிவை அங்கீகரிக்கவா? இது கால அட்டவணையை உறுதிசெய்யும்.",
    },
    "provider.start_confirm": {
        "en": "Mark this rental as In Progress (equipment dispatched/deployed)?",
        "ta": "இந்த வாடகையை பயன்பாட்டில் உள்ளதாக மாற்றவா?",
    },
    "provider.complete_confirm": {
        "en": "Mark this rental as Completed and payment settled offline?",
        "ta": "பணி நிறைவடைந்து வாடகை பெறப்பட்டதாகக் குறிக்கவா?",
    },

    # Separate Registration Options
    "auth.select_role_title": {
        "en": "Join FarmConnect Agricultural Community",
        "ta": "விவசாய இணைப்பு சமூகத்தில் இணையுங்கள்",
    },
    "auth.select_role_subtitle": {
        "en": "Choose your registration option to get started with verified agricultural rentals across Tamil Nadu.",
        "ta": "தமிழ்நாடு முழுவதும் சரிபார்க்கப்பட்ட விவசாய வாடகைகளைத் தொடங்க உங்கள் பதிவு விருப்பத்தைத் தேர்வுசெய்யவும்.",
    },
    "auth.role_card_farmer_title": {
        "en": "Register as Farmer",
        "ta": "விவசாயியாக பதிவு செய்க",
    },
    "auth.role_card_farmer_subtitle": {
        "en": "Rent verified tractors, harvesters, and implements near your village at fair rates with zero middleman markups.",
        "ta": "உங்கள் கிராமத்திற்கு அருகில் உள்ள டிராக்டர்கள் மற்றும் அறுவடை இயந்திரங்களை தரகர்கள் இன்றி வாடகைக்கு எடுங்கள்.",
    },
    "auth.role_card_farmer_btn": {
        "en": "Register as Farmer →",
        "ta": "விவசாயியாக பதிவு செய்க →",
    },
    "auth.role_card_provider_title": {
        "en": "Register as Machinery Provider",
        "ta": "இயந்திர உரிமையாளராக பதிவு செய்க",
    },
    "auth.role_card_provider_subtitle": {
        "en": "List your equipment, set hourly & daily rental packages, and receive direct booking requests from local farmers.",
        "ta": "உங்கள் இயந்திரங்களை பட்டியலிட்டு, வாடகை கட்டணங்களை நிர்ணயித்து, விவசாயிகளிடமிருந்து முன்பதிவுகளைப் பெறுங்கள்.",
    },
    "auth.role_card_provider_btn": {
        "en": "Register as Machinery Provider →",
        "ta": "இயந்திர உரிமையாளராக பதிவு செய்க →",
    },
    "auth.register_farmer_title": {
        "en": "Farmer Registration",
        "ta": "விவசாயி பதிவு",
    },
    "auth.register_farmer_subtitle": {
        "en": "Create your Farmer account to discover, compare, and book verified agricultural equipment near you.",
        "ta": "உங்களுக்கு அருகிலுள்ள விவசாய இயந்திரங்களை கண்டறிந்து முன்பதிவு செய்ய விவசாயி கணக்கை உருவாக்கவும்.",
    },
    "auth.register_provider_title": {
        "en": "Machinery Provider Registration",
        "ta": "இயந்திர உரிமையாளர் பதிவு",
    },
    "auth.register_provider_subtitle": {
        "en": "Create your Provider account to list machinery, manage rental rates, and grow your agricultural rental business.",
        "ta": "இயந்திரங்களை பட்டியலிட, வாடகை கட்டணங்களை நிர்வகிக்க உரிமையாளர் கணக்கை உருவாக்கவும்.",
    },
    "auth.switch_role_link": {
        "en": "← Choose a different registration option",
        "ta": "← வேறு பதிவு விருப்பத்தைத் தேர்வுசெய்க",
    },

    # Role Dashboards
    "nav.farmer_dashboard": {
        "en": "Farmer Dashboard",
        "ta": "விவசாயி கட்டுப்பாட்டகம்",
    },
    "dashboard.farmer_welcome": {
        "en": "Farmer Dashboard",
        "ta": "விவசாயி கட்டுப்பாட்டகம்",
    },
    "dashboard.farmer_subtitle": {
        "en": "Discover nearby machinery, compare rental prices, and manage all your farm bookings.",
        "ta": "அருகிலுள்ள இயந்திரங்களைக் கண்டறியுங்கள், வாடகைக் கட்டணங்களை ஒப்பிடுங்கள், உங்கள் முன்பதிவுகளை நிர்வகியுங்கள்.",
    },
    "dashboard.search_machinery": {
        "en": "Search Machinery",
        "ta": "இயந்திரங்களைத் தேடுக",
    },
    "dashboard.browse_listings": {
        "en": "Browse Machinery Listings",
        "ta": "இயந்திரங்களை காண்க",
    },
    "dashboard.view_prices": {
        "en": "View Rental Prices",
        "ta": "வாடகை கட்டணங்கள்",
    },
    "dashboard.manage_rental_prices": {
        "en": "Manage Rental Prices",
        "ta": "வாடகை கட்டணங்களை நிர்வகிக்க",
    },
    "dashboard.manage_rental_prices_desc": {
        "en": "Configure hourly, daily, and operator package rates for your listed machinery.",
        "ta": "உங்கள் இயந்திரங்களுக்கான மணிநேர, தினசரி மற்றும் ஓட்டுனர் கட்டணங்களை மாற்றியமைக்கவும்.",
    },
    "dashboard.incoming_requests": {
        "en": "Incoming Booking Requests",
        "ta": "வந்த முன்பதிவு கோரிக்கைகள்",
    },
    "dashboard.farmer_profile_desc": {
        "en": "Review account details, contact number, preferred language, and security settings.",
        "ta": "கணக்கு விவரங்கள், தொடர்பு எண், விருப்ப மொழி மற்றும் பாதுகாப்பு அமைப்புகளைப் பார்வையிடுங்கள்.",
    },
    "dashboard.active_rentals": {
        "en": "Active Rentals",
        "ta": "செயலில் உள்ள வாடகைகள்",
    },
    "dashboard.pending_bookings": {
        "en": "Pending Requests",
        "ta": "காத்திருக்கும் கோரிக்கைகள்",
    },
    "dashboard.completed_rentals": {
        "en": "Completed Rentals",
        "ta": "நிறைவடைந்த வாடகைகள்",
    },
    "dashboard.total_bookings": {
        "en": "Total Bookings",
        "ta": "மொத்த முன்பதிவுகள்",
    },

    # Three-Column Unified Role Portal
    "portal.title": {
        "en": "FarmConnect Community Portals",
        "ta": "விவசாய இணைப்பு பாத்திரங்கள்",
    },
    "portal.subtitle": {
        "en": "Select your portal to access relevant actions, services, and secure authentication.",
        "ta": "உங்கள் பாத்திரத்தைத் தேர்வுசெய்து அதற்கான சேவைகள் மற்றும் உள்நுழைவை அணுகுங்கள்.",
    },
    "portal.farmer_title": {
        "en": "Farmer",
        "ta": "விவசாயி",
    },
    "portal.farmer_desc": {
        "en": "Rent verified agricultural machinery near your village with transparent pricing and zero middleman markups.",
        "ta": "கிராமத்தில் உள்ள டிராக்டர்கள் மற்றும் உபகரணங்களை நியாயமான வாடகையில் முன்பதிவு செய்யுங்கள்.",
    },
    "portal.provider_title": {
        "en": "Machinery Provider / Renter",
        "ta": "இயந்திர உரிமையாளர் / வழங்குநர்",
    },
    "portal.provider_desc": {
        "en": "List your tractors & implements, manage rental pricing, and approve booking requests from local farmers.",
        "ta": "உங்கள் இயந்திரங்களை பட்டியலிட்டு, வாடகை நிர்ணயித்து, விவசாயிகளிடம் முன்பதிவு பெறுங்கள்.",
    },
    "portal.admin_title": {
        "en": "Admin",
        "ta": "நிர்வாகி",
    },
    "portal.admin_desc": {
        "en": "System governance, equipment provider oversight, platform booking monitoring, and support enquiry triage.",
        "ta": "கணினி மேலாண்மை, பயனர் சரிபார்ப்பு, இயந்திரங்கள் மற்றும் விசாரணைகள் மேலாண்மை.",
    },
    "portal.action_search_machinery": {
        "en": "Search Machinery",
        "ta": "இயந்திரங்களைத் தேடுக",
    },
    "portal.action_view_prices": {
        "en": "View Rental Prices",
        "ta": "வாடகை கட்டணங்கள்",
    },
    "portal.action_my_bookings": {
        "en": "My Bookings",
        "ta": "என் முன்பதிவுகள்",
    },
    "portal.action_my_profile": {
        "en": "My Profile",
        "ta": "என் சுயவிவரம்",
    },
    "portal.action_add_machinery": {
        "en": "Add Machinery",
        "ta": "இயந்திரம் சேர்க்க",
    },
    "portal.action_manage_machinery": {
        "en": "Manage My Machinery",
        "ta": "என் இயந்திரங்கள் மேலாண்மை",
    },
    "portal.action_set_prices": {
        "en": "Set Rental Prices",
        "ta": "வாடகைக் கட்டணம் நிர்ணயித்தல்",
    },
    "portal.action_incoming_requests": {
        "en": "Incoming Booking Requests",
        "ta": "வந்த முன்பதிவுக் கோரிக்கைகள்",
    },
    "portal.action_manage_users": {
        "en": "Manage Users",
        "ta": "பயனர்கள் மேலாண்மை",
    },
    "portal.action_review_listings": {
        "en": "Review Listings",
        "ta": "இயந்திரங்கள் சரிபார்ப்பு",
    },
    "portal.action_monitor_bookings": {
        "en": "Monitor Bookings",
        "ta": "முன்பதிவுகள் கண்காணிப்பு",
    },
    "portal.action_manage_enquiries": {
        "en": "Manage Enquiries",
        "ta": "விசாரணைகள் மேலாண்மை",
    },
    "portal.btn_register_farmer": {
        "en": "Register as Farmer",
        "ta": "விவசாயியாக பதிவு செய்க",
    },
    "portal.btn_login_farmer": {
        "en": "Sign In as Farmer",
        "ta": "விவசாயியாக உள்நுழைக",
    },
    "portal.btn_register_provider": {
        "en": "Register as Provider",
        "ta": "உரிமையாளராக பதிவு செய்க",
    },
    "portal.btn_login_provider": {
        "en": "Sign In as Provider",
        "ta": "உரிமையாளராக உள்நுழைக",
    },
    "portal.btn_admin_login": {
        "en": "Admin Sign In",
        "ta": "நிர்வாகி உள்நுழைவு",
    },
    "portal.badge_admin_restricted": {
        "en": "Authorized Accounts Only",
        "ta": "அங்கீகரிக்கப்பட்ட ஊழியர்களுக்கு மட்டும்",
    },
    "portal.admin_registration_closed": {
        "en": "Public Registration Closed",
        "ta": "பொதுப் பதிவு முடக்கப்பட்டுள்ளது",
    },
    "portal.btn_request_admin": {
        "en": "Request Access",
        "ta": "அணுகல் கோருக",
    },
    "auth.role_indicator_farmer": {
        "en": "Signing in as Farmer",
        "ta": "விவசாயியாக உள்நுழைகிறீர்கள்",
    },
    "auth.role_indicator_farmer_sub": {
        "en": "Search machinery, compare rates, and manage bookings",
        "ta": "இயந்திரங்களைத் தேடி, வாடகை ஒப்பீடு செய்து முன்பதிவுகளை நிர்வகியுங்கள்",
    },
    "auth.role_indicator_provider": {
        "en": "Signing in as Machinery Provider / Renter",
        "ta": "இயந்திர வழங்குநராக உள்நுழைகிறீர்கள்",
    },
    "auth.role_indicator_provider_sub": {
        "en": "Manage machinery listings, set rental rates, and approve bookings",
        "ta": "இயந்திரங்கள், வாடகை கட்டணங்கள் மற்றும் முன்பதிவுகளை நிர்வகியுங்கள்",
    },
    "auth.role_indicator_admin": {
        "en": "Signing in as System Administrator",
        "ta": "கணினி நிர்வாகியாக உள்நுழைகிறீர்கள்",
    },
    "auth.role_indicator_admin_sub": {
        "en": "Authorized system governance, reviews, and monitoring",
        "ta": "கணினி நிர்வாகம், சரிபார்ப்பு மற்றும் கண்காணிப்பு",
    },
    "auth.switch_role": {
        "en": "Switch Role",
        "ta": "பாத்திரத்தை மாற்ற",
    },
    "nav.roles_portal": {
        "en": "Role Portals",
        "ta": "பாத்திரங்கள்",
    },
    "auth.admin_login_link": {
        "en": "Admin Login",
        "ta": "நிர்வாகி உள்நுழைவு",
    },
    "auth.regular_login_link": {
        "en": "Regular User Login",
        "ta": "வழக்கமான பயனர் உள்நுழைவு",
    },
    "auth.admin_access_denied": {
        "en": "Access denied: This account does not have administrator privileges.",
        "ta": "அணுகல் மறுக்கப்பட்டது: இந்தக் கணக்கிற்கு நிர்வாகி அனுமதிகள் இல்லை.",
    },
    "auth.role_tab_farmer": {
        "en": "Farmer",
        "ta": "விவசாயி",
    },
    "auth.role_tab_provider": {
        "en": "Machinery Provider",
        "ta": "இயந்திர உரிமையாளர்",
    },
    "auth.role_switch_to_farmer": {
        "en": "Switch to Farmer",
        "ta": "விவசாயிக்கு மாறுக",
    },
    "auth.role_switch_to_provider": {
        "en": "Switch to Provider",
        "ta": "உரிமையாளருக்கு மாறுக",
    },
    "auth.role_farmer": {
        "en": "Farmer",
        "ta": "விவசாயி",
    },
    "auth.role_provider": {
        "en": "Machinery Provider",
        "ta": "இயந்திர உரிமையாளர்",
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Retrieve localized string by key and language, falling back to English."""
    normalized_lang = "ta" if lang == "ta" else "en"
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key

    val = entry.get(normalized_lang) or entry.get("en", key)
    if kwargs:
        try:
            return val.format(**kwargs)
        except Exception:
            return val
    return val


def get_current_language() -> str:
    """Return the active language code from session (defaults to 'en')."""
    return session.get("lang", "en")
