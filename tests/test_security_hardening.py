import pytest
from flask import session
from app import create_app
from app.models.user import User
from app.extensions import db
from app.services.otp_service import MockDevSMSProvider, SMSGatewayProvider, get_default_sms_provider
from config import BaseConfig, ProductionConfig, get_config


def test_deactivated_user_lockout_in_login_required(client, app):
    """Test that deactivated users cannot access login_required endpoints."""
    with app.app_context():
        # Create an inactive farmer user
        inactive_user = User(
            phone="+919999900010",
            full_name="Deactivated Farmer",
            role="FARMER",
            is_active=False,
        )
        inactive_user.set_password("SecurePass123!")
        db.session.add(inactive_user)
        db.session.commit()

        # Simulate existing session cookie
        with client.session_transaction() as sess:
            sess["user_id"] = str(inactive_user.id)
            sess["user_role"] = "FARMER"

        # Attempt to access protected dashboard
        response = client.get("/farmer/dashboard", follow_redirects=False)
        # Should redirect to login
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

        # Session should be invalidated
        with client.session_transaction() as sess:
            assert sess.get("user_id") is None


def test_deactivated_user_lockout_in_role_required(client, app):
    """Test that deactivated users cannot access role_required endpoints."""
    with app.app_context():
        inactive_provider = User(
            phone="+919999900011",
            full_name="Deactivated Provider",
            role="PROVIDER",
            is_active=False,
        )
        inactive_provider.set_password("SecurePass123!")
        db.session.add(inactive_provider)
        db.session.commit()

        with client.session_transaction() as sess:
            sess["user_id"] = str(inactive_provider.id)
            sess["user_role"] = "PROVIDER"

        response = client.get("/provider/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]


def test_production_config_rejects_insecure_secret_key(monkeypatch):
    """Verify that ProductionConfig rejects insecure default or empty secret keys."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
    monkeypatch.setenv("MOCK_OTP_ENABLED", "false")

    # Insecure default key
    monkeypatch.setenv("SECRET_KEY", "farmconnect-insecure-default-key-change-me")
    with pytest.raises(RuntimeError, match="secure, unique SECRET_KEY"):
        get_config("production")

    # Empty key
    monkeypatch.setenv("SECRET_KEY", "")
    with pytest.raises(RuntimeError, match="secure, unique SECRET_KEY"):
        get_config("production")

    # Valid production key
    monkeypatch.setenv("SECRET_KEY", "prod-super-secure-random-token-xyz-1234567890")
    cfg = get_config("production")
    assert cfg.SECRET_KEY == "prod-super-secure-random-token-xyz-1234567890"
    assert cfg.SESSION_COOKIE_SECURE is True


def test_production_config_rejects_mock_otp(monkeypatch):
    """Verify that ProductionConfig rejects MOCK_OTP_ENABLED=True."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
    monkeypatch.setenv("SECRET_KEY", "valid-prod-key-1234567890")
    monkeypatch.setenv("MOCK_OTP_ENABLED", "true")

    with pytest.raises(RuntimeError, match="MOCK_OTP_ENABLED cannot be True in production"):
        get_config("production")


def test_defensive_security_headers(client):
    """Verify presence of defensive HTTP security headers on responses."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"


def test_healthcheck_endpoint(client):
    """Verify /api/health returns 200 and healthy status when database is reachable."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["app"] == "FarmConnect"


def test_open_redirect_protection_in_set_language(client):
    """Verify set_language rejects external/malicious redirect targets."""
    # Attempt redirect to external domain
    response = client.get("/set-language/en?next=https://evil.com", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    # Attempt protocol-relative redirect
    response = client.get("/set-language/en?next=//evil.com", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    # Valid internal redirect
    response = client.get("/set-language/en?next=/machinery/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == "/machinery/"


def test_custom_error_handlers(client):
    """Verify 404 returns user-friendly error page, and API returns JSON."""
    # Web 404
    response = client.get("/nonexistent-page-url-12345")
    assert response.status_code == 404
    assert "Page Not Found" in response.get_data(as_text=True)

    # API 404
    api_response = client.get("/api/nonexistent-route")
    assert api_response.status_code == 404
    data = api_response.get_json()
    assert data["error"] == "Not Found"


def test_sms_gateway_provider_error_handling(app, monkeypatch):
    """Verify that MockDevSMSProvider is blocked in production and SMSGatewayProvider handles missing API keys."""
    with app.app_context():
        # Mock SMS provider blocked in production
        monkeypatch.setitem(app.config, "APP_ENV", "production")
        mock_provider = MockDevSMSProvider()
        with pytest.raises(RuntimeError, match="CRITICAL SECURITY ERROR"):
            mock_provider.send_otp("+919876543210", "123456")

        # Gateway provider requires API key
        gateway = SMSGatewayProvider(provider_name="twilio", api_key=None)
        with pytest.raises(RuntimeError, match="requires SMS_API_KEY"):
            gateway.send_otp("+919876543210", "123456")

        # Gateway provider with configured API key succeeds
        gateway_configured = SMSGatewayProvider(provider_name="fast2sms", api_key="dummy-test-key")
        assert gateway_configured.send_otp("+919876543210", "123456") is True


def test_local_storage_backend_save_and_delete(tmp_path, app):
    """Verify LocalStorageBackend creates files, verifies existence, and cleans up on delete."""
    from io import BytesIO
    from app.services.storage_service import LocalStorageBackend

    with app.app_context():
        backend = LocalStorageBackend(base_dir=tmp_path, url_prefix="/static/uploads/machinery")
        data = BytesIO(b"fake-image-bytes-content")
        url = backend.save(data, "test_tractor.jpg", "image/jpeg")

        assert url == "/static/uploads/machinery/test_tractor.jpg"
        assert backend.exists(url) is True
        assert (tmp_path / "test_tractor.jpg").exists()

        # Delete
        assert backend.delete(url) is True
        assert backend.exists(url) is False
        assert not (tmp_path / "test_tractor.jpg").exists()


def test_s3_storage_backend_configuration(app, monkeypatch):
    """Verify S3StorageBackend configuration enforcement and factory behavior."""
    from app.services.storage_service import get_storage_backend, S3StorageBackend

    with app.app_context():
        monkeypatch.setitem(app.config, "STORAGE_BACKEND", "s3")
        monkeypatch.delitem(app.config, "S3_BUCKET_NAME", raising=False)
        monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

        with pytest.raises(RuntimeError, match="requires 'S3_BUCKET_NAME'"):
            get_storage_backend()

        # Valid S3 configuration returns S3StorageBackend
        monkeypatch.setitem(app.config, "S3_BUCKET_NAME", "farmconnect-prod-photos")
        monkeypatch.setitem(app.config, "S3_ENDPOINT_URL", "https://r2.cloudflarestorage.com")
        backend = get_storage_backend()
        assert isinstance(backend, S3StorageBackend)
        assert backend.bucket_name == "farmconnect-prod-photos"

