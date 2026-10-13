from flask import Flask, jsonify, session
from config import get_config
from app.extensions import db, migrate, csrf
from app.utils.i18n import t


def create_app(config_name: str | None = None) -> Flask:
    """Application factory for FarmConnect."""
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # Load and validate configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Import models to ensure registration with SQLAlchemy metadata
    from app import models as _models  # noqa: F401

    # Inject bilingual translation helper and language into all templates
    @app.context_processor
    def inject_i18n():
        lang = session.get("lang", "en")
        return {
            "_t": lambda key, **kwargs: t(key, lang=lang, **kwargs),
            "current_lang": lang,
        }

    # Register Blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.machinery import machinery_bp
    from app.blueprints.provider import provider_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(machinery_bp)
    app.register_blueprint(provider_bp)

    # Base healthcheck route for startup and monitoring
    @app.route("/api/health")
    def health_check():
        return jsonify({
            "status": "healthy",
            "app": "FarmConnect",
            "env": app.config.get("APP_ENV"),
            "mock_otp_enabled": app.config.get("MOCK_OTP_ENABLED"),
        })

    return app
