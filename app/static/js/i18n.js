/**
 * FarmConnect Client-Side Internationalization (i18n) Module
 * Supports seamless switching and persistence between English ('en') and Tamil ('ta').
 */

const translations = {
    en: {
        "nav.home": "Home",
        "nav.machinery": "Machinery Rentals",
        "nav.login": "Sign In",
        "nav.register": "Register",
        "nav.profile": "My Profile",
        "nav.logout": "Sign Out",
        "nav.language": "Language",
        "hero.cta_browse": "Explore Machinery",
        "hero.cta_register": "Join as Farmer / Provider",
        "auth.btn_send_otp": "Send OTP Code",
        "auth.btn_verify": "Verify & Sign In",
        "auth.btn_resend": "Resend OTP",
        "nav.my_machinery": "My Machinery",
        "nav.add_machinery": "Add Machinery",
        "catalogue.use_gps": "Use My Location",
        "catalogue.gps_locating": "Locating...",
        "catalogue.gps_denied": "Location permission denied or unavailable.",
        "msg.wait_cooldown": "Please wait before resending OTP.",
        "msg.invalid_phone": "Please enter a valid 10-digit mobile number.",
        "msg.invalid_otp": "Please enter a 6-digit OTP code."
    },
    ta: {
        "nav.home": "முகப்பு",
        "nav.machinery": "இயந்திரங்கள்",
        "nav.login": "உள்நுழைக",
        "nav.register": "பதிவு செய்க",
        "nav.profile": "என் சுயவிவரம்",
        "nav.logout": "வெளியேறு",
        "nav.language": "மொழி",
        "nav.my_machinery": "என் இயந்திரங்கள்",
        "nav.add_machinery": "புதிய இயந்திரம்",
        "catalogue.use_gps": "என் இருப்பிடம்",
        "catalogue.gps_locating": "கண்டறியப்படுகிறது...",
        "catalogue.gps_denied": "இருப்பிட அனுமதி மறுக்கப்பட்டது அல்லது கிடைக்கவில்லை.",
        "hero.cta_browse": "இயந்திரங்களை காண்க",
        "hero.cta_register": "விவசாயி / உரிமையாளராக இணையுங்கள்",
        "auth.btn_send_otp": "OTP குறியீடு அனுப்புக",
        "auth.btn_verify": "சரிபார்த்து உள்நுழைக",
        "auth.btn_resend": "மீண்டும் OTP அனுப்புக",
        "msg.wait_cooldown": "மீண்டும் அனுப்ப சிறிது நேரம் காத்திருக்கவும்.",
        "msg.invalid_phone": "சரியான 10 இலக்க மொபைல் எண்ணை உள்ளிடவும்.",
        "msg.invalid_otp": "6 இலக்க OTP குறியீட்டை உள்ளிடவும்."
    }
};

/**
 * Get active language preference.
 */
function getCurrentLanguage() {
    return document.documentElement.lang || 'en';
}

/**
 * Translate key with fallback.
 */
function t(key) {
    const lang = getCurrentLanguage();
    if (translations[lang] && translations[lang][key]) {
        return translations[lang][key];
    }
    if (translations['en'] && translations['en'][key]) {
        return translations['en'][key];
    }
    return key;
}

/**
 * Change language preference by redirecting to server endpoint.
 */
function switchLanguage(lang) {
    if (lang !== 'en' && lang !== 'ta') return;
    const currentPath = window.location.pathname;
    window.location.href = `/set-language/${lang}?next=${encodeURIComponent(currentPath)}`;
}

document.addEventListener('DOMContentLoaded', () => {
    // Attach language switcher buttons if present
    document.querySelectorAll('[data-switch-lang]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const targetLang = button.getAttribute('data-switch-lang');
            switchLanguage(targetLang);
        });
    });
});
