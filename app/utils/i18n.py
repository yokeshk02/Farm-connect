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
    "cat.TRACTOR": {
        "en": "Tractor",
        "ta": "டிராக்டர்",
    },
    "cat.HARVESTER": {
        "en": "Harvester",
        "ta": "அறுவடை இயந்திரம்",
    },
    "cat.TILLER": {
        "en": "Power Tiller",
        "ta": "உழவு இயந்திரம்",
    },
    "cat.SPRAYER": {
        "en": "Sprayer",
        "ta": "தெளிப்பான்",
    },
    "cat.BALER": {
        "en": "Baler",
        "ta": "வைக்கோல் கட்டும் இயந்திரம்",
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
