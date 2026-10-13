import pytest
from app.utils.i18n import t, TRANSLATIONS


def test_translation_helper_fallback():
    """Verify translation helper returns correct strings for English, Tamil, and fallbacks."""
    assert t("nav.home", "en") == "Home"
    assert t("nav.home", "ta") == "முகப்பு"

    # Unknown key returns the key itself
    assert t("unknown.key.demo", "en") == "unknown.key.demo"
    assert t("unknown.key.demo", "ta") == "unknown.key.demo"


def test_all_translation_keys_have_en_and_ta():
    """Verify that every translation key has non-empty English and Tamil values."""
    for key, item in TRANSLATIONS.items():
        assert "en" in item, f"Missing 'en' for key: {key}"
        assert "ta" in item, f"Missing 'ta' for key: {key}"
        assert len(item["en"].strip()) > 0, f"Empty 'en' for key: {key}"
        assert len(item["ta"].strip()) > 0, f"Empty 'ta' for key: {key}"


def test_language_switch_and_persistence(client):
    """Verify language switching persists across page navigation."""
    # 1. Default load should be English
    res_en = client.get("/")
    assert res_en.status_code == 200
    html_en = res_en.get_data(as_text=True)
    assert 'lang="en"' in html_en
    assert "Home" in html_en

    # 2. Switch to Tamil
    res_switch = client.get("/set-language/ta", follow_redirects=True)
    assert res_switch.status_code == 200
    html_ta = res_switch.get_data(as_text=True)
    assert 'lang="ta"' in html_ta
    assert "முகப்பு" in html_ta
    assert "இயந்திரங்கள்" in html_ta

    # 3. Navigate to another page (e.g., login) and verify Tamil persists
    res_login = client.get("/auth/login")
    assert res_login.status_code == 200
    html_login = res_login.get_data(as_text=True)
    assert 'lang="ta"' in html_login
    assert "உள்நுழைக" in html_login

    # 4. Switch back to English
    res_back = client.get("/set-language/en", follow_redirects=True)
    assert res_back.status_code == 200
    html_back = res_back.get_data(as_text=True)
    assert 'lang="en"' in html_back
    assert "Home" in html_back
