import pytest
from app import create_app
from config import get_config, ProductionConfig


def test_app_creation_testing_mode():
    """Verify application factory creates an app in testing mode."""
    app = create_app("testing")
    assert app.config["TESTING"] is True
    assert app.config["APP_ENV"] == "testing"


def test_health_check_endpoint(client):
    """Verify the /api/health endpoint returns 200 OK and valid JSON."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["app"] == "FarmConnect"
    assert "env" in data
    assert "mock_otp_enabled" in data


def test_production_rejects_mock_otp(monkeypatch):
    """Verify that MOCK_OTP_ENABLED=True in production raises a RuntimeError."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("MOCK_OTP_ENABLED", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    with pytest.raises(RuntimeError, match="MOCK_OTP_ENABLED cannot be True in production"):
        create_app("production")


def test_production_requires_database_url(monkeypatch):
    """Verify that missing DATABASE_URL in production raises a RuntimeError."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("MOCK_OTP_ENABLED", "false")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL must be configured"):
        ProductionConfig.SQLALCHEMY_DATABASE_URI = None
        ProductionConfig.validate_environment()
