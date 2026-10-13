import os
from app import create_app

import click
from app.extensions import db
from app.models.user import User
from app.utils.security import normalize_phone_number

# Instantiate the Flask application using environment settings
app = create_app()


@app.cli.command("create-admin")
@click.option("--phone", default="9999999999", help="Admin phone number (10 digits)")
@click.option("--password", default="Admin@12345", help="Admin password")
@click.option("--name", default="System Administrator", help="Admin full name")
def create_admin_cmd(phone, password, name):
    """Create or update a local Administrator account."""
    norm_phone = normalize_phone_number(phone)
    user = User.query.filter_by(phone=norm_phone).first()
    if not user:
        user = User(
            phone=norm_phone,
            full_name=name,
            role="ADMIN",
            is_phone_verified=True,
            is_active=True,
        )
        db.session.add(user)
    else:
        user.role = "ADMIN"
        user.is_phone_verified = True
        user.is_active = True
    user.set_password(password)
    db.session.commit()
    click.echo(f"Admin account configured for {norm_phone} with role {user.role}.")


if __name__ == "__main__":
    # Support direct execution with python run.py
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug = app.config.get("DEBUG", False)
    app.run(host=host, port=port, debug=debug)
