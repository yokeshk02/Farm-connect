from flask import render_template, request, session, redirect, url_for
from app.blueprints.main import main_bp
from app.utils.security import get_current_user
from app.extensions import db


@main_bp.route("/")
def index():
    """FarmConnect landing page with agricultural branding and CTAs."""
    return render_template("main/index.html")


@main_bp.route("/set-language/<lang>")
def set_language(lang: str):
    """Switch language preference ('en' or 'ta') and persist across navigation."""
    if lang in ("en", "ta"):
        session["lang"] = lang
        user = get_current_user()
        if user:
            user.preferred_language = lang
            db.session.commit()

    # Redirect to previous page or index
    next_url = request.args.get("next") or request.referrer or url_for("main.index")
    # Prevent open redirect vulnerability
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("main.index")
    return redirect(next_url)
