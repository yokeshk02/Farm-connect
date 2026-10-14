import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent

# Load .env file if it exists
load_dotenv(BASE_DIR / ".env")


def normalize_db_url(url: str | None) -> str | None:
    """Normalize legacy postgres:// URLs to postgresql:// for SQLAlchemy."""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class BaseConfig:
    """Base application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "farmconnect-insecure-default-key-change-me")
    APP_ENV = os.getenv("APP_ENV", "production").lower()
    DEBUG = False
    TESTING = False

    # Database configuration
    SQLALCHEMY_DATABASE_URI = normalize_db_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Mock OTP configuration
    MOCK_OTP_ENABLED = os.getenv("MOCK_OTP_ENABLED", "false").lower() in ("true", "1", "yes")

    # CSRF Protection
    WTF_CSRF_ENABLED = True

    # Session Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # File Uploads
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max request payload


    @classmethod
    def validate_environment(cls):
        """Validate security constraints across environments."""
        env = (os.getenv("APP_ENV") or cls.APP_ENV).lower()
        if "MOCK_OTP_ENABLED" in os.environ:
            mock_otp = os.getenv("MOCK_OTP_ENABLED", "false").lower() in ("true", "1", "yes")
        else:
            mock_otp = cls.MOCK_OTP_ENABLED

        if env == "production":
            if mock_otp:
                raise RuntimeError(
                    "CRITICAL SECURITY ERROR: MOCK_OTP_ENABLED cannot be True in production (APP_ENV=production)!"
                )
            if "DATABASE_URL" in os.environ:
                db_uri = os.getenv("DATABASE_URL")
            else:
                db_uri = cls.SQLALCHEMY_DATABASE_URI
            if not db_uri:
                raise RuntimeError(
                    "CRITICAL CONFIGURATION ERROR: DATABASE_URL must be configured in production!"
                )


class DevelopmentConfig(BaseConfig):
    """Local development configuration."""

    DEBUG = True
    APP_ENV = "development"
    MOCK_OTP_ENABLED = True


class TestingConfig(BaseConfig):
    """Automated testing configuration."""

    TESTING = True
    DEBUG = True
    APP_ENV = "testing"
    MOCK_OTP_ENABLED = True
    WTF_CSRF_ENABLED = False
    # Use TEST_DATABASE_URL if provided, else fallback to in-memory SQLite for fast isolated testing
    SQLALCHEMY_DATABASE_URI = normalize_db_url(
        os.getenv("TEST_DATABASE_URL")
    ) or "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Production configuration with strict security defaults."""

    DEBUG = False
    APP_ENV = "production"
    MOCK_OTP_ENABLED = False


# Map environment names to configuration classes
CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env_name: str | None = None) -> type[BaseConfig]:
    """Retrieve the appropriate config class based on APP_ENV or explicit parameter."""
    resolved_env = (env_name or os.getenv("APP_ENV", "development")).lower()
    config_class = CONFIG_MAP.get(resolved_env, ProductionConfig)
    config_class.validate_environment()
    return config_class


