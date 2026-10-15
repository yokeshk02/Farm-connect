from flask import Flask, jsonify, session, request, render_template
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

    # Apply ProxyFix in production for proper client IP and scheme detection behind reverse proxies
    if app.config.get("APP_ENV") == "production":
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

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

    # Defensive Security Response Headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # Register Blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.machinery import machinery_bp
    from app.blueprints.provider import provider_bp
    from app.blueprints.bookings import bookings_bp
    from app.blueprints.farmer import farmer_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(machinery_bp)
    app.register_blueprint(provider_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(admin_bp)

    # Base healthcheck route for startup and monitoring
    @app.route("/api/health")
    def health_check():
        db_status = "connected"
        status_code = 200
        try:
            import sqlalchemy as sa
            db.session.execute(sa.text("SELECT 1"))
        except Exception as e:
            app.logger.error(f"Healthcheck database ping failed: {e}")
            db_status = "disconnected"
            status_code = 503

        return jsonify({
            "status": "healthy" if status_code == 200 else "unhealthy",
            "database": db_status,
            "app": "FarmConnect",
            "env": app.config.get("APP_ENV"),
            "mock_otp_enabled": app.config.get("MOCK_OTP_ENABLED"),
        }), status_code

    # Custom Error Handlers
    @app.errorhandler(400)
    def handle_bad_request(error):
        error_msg = getattr(error, "description", str(error))
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Bad Request", "message": error_msg}), 400
        return render_template(
            "errors/error.html",
            error_code=400,
            error_title="Bad Request",
            error_message=f"Bad Request: {error_msg}",
        ), 400

    @app.errorhandler(403)
    def handle_forbidden(error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Forbidden", "message": "Access denied."}), 403
        return render_template(
            "errors/error.html",
            error_code=403,
            error_title="Access Forbidden",
            error_message="You do not have permission to access this page or resource.",
        ), 403

    @app.errorhandler(404)
    def handle_not_found(error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Not Found", "message": "Resource not found."}), 404
        return render_template(
            "errors/error.html",
            error_code=404,
            error_title="Page Not Found",
            error_message="The page, machinery listing, or booking record you requested does not exist.",
        ), 404

    @app.errorhandler(500)
    def handle_internal_server_error(error):
        db.session.rollback()
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500
        return render_template(
            "errors/error.html",
            error_code=500,
            error_title="Server Error",
            error_message="An internal server error occurred. Please try again later.",
        ), 500

    return app
