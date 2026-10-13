from flask import render_template, request, session, redirect, url_for, flash
from app.blueprints.main import main_bp
from app.utils.security import get_current_user
from app.extensions import db
from app.models.enquiry import ContactEnquiry
from app.utils.i18n import t


@main_bp.route("/")
def index():
    """FarmConnect landing page with agricultural branding and CTAs."""
    return render_template("main/index.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Public Contact & Support enquiry form."""
    user = get_current_user()
    if request.method == "POST":
        sender_name = (request.form.get("sender_name") or "").strip()
        contact_info = (request.form.get("contact_phone_or_email") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        message = (request.form.get("message") or "").strip()

        errors = []
        if not sender_name:
            errors.append("Please enter your name.")
        if not contact_info:
            errors.append("Please enter your phone number or email address.")
        if not subject:
            errors.append("Please specify a subject for your enquiry.")
        if not message:
            errors.append("Please enter your message.")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("main/contact.html", form_data=request.form)

        enquiry = ContactEnquiry(
            user_id=user.id if user else None,
            sender_name=sender_name,
            contact_phone_or_email=contact_info,
            subject=subject,
            message=message,
            status=ContactEnquiry.STATUS_NEW,
        )
        db.session.add(enquiry)
        db.session.commit()

        flash(t("contact.success", lang=session.get("lang", "en")), "success")
        return redirect(url_for("main.contact"))

    return render_template("main/contact.html", form_data={})


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
