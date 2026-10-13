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
    "hero.title": {
        "en": "Find & Rent Agricultural Machinery Nearby",
        "ta": "உங்களுக்கு அருகிலுள்ள விவசாய இயந்திரங்களை வாடகைக்கு பெறுங்கள்",
    },
    "hero.subtitle": {
        "en": "Connect directly with verified equipment owners across Tamil Nadu. Rent tractors, harvesters, tillers, and sprayers with or without operators.",
        "ta": "தமிழ்நாடு முழுவதும் உள்ள சரிபார்க்கப்பட்ட இயந்திர உரிமையாளர்களுடன் நேரடியாக இணையுங்கள். டிராக்டர்கள், அறுவடை இயந்திரங்கள் மற்றும் உழவு இயந்திரங்களை உடனடியாக வாடகைக்கு எடுங்கள்.",
    },
    "hero.cta_browse": {
        "en": "Explore Machinery",
        "ta": "இயந்திரங்களை காண்க",
    },
    "hero.cta_register": {
        "en": "Join as Farmer / Provider",
        "ta": "விவசாயி / உரிமையாளராக இணையுங்கள்",
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
        "en": "Password Sign In (Admin / Staff)",
        "ta": "கடவுச்சொல் உள்நுழைவு (நிர்வாகம்)",
    },
    "auth.otp_login_tab": {
        "en": "Phone OTP Sign In (Farmer / Provider)",
        "ta": "மொபைல் OTP உள்நுழைவு (விவசாயி / உரிமையாளர்)",
    },
    "auth.password_label": {
        "en": "Password",
        "ta": "கடவுச்சொல்",
    },
    "auth.btn_login_password": {
        "en": "Sign In with Password",
        "ta": "கடவுச்சொல் மூலம் உள்நுழைக",
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
