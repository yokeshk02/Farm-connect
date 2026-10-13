from flask import Blueprint

machinery_bp = Blueprint("machinery", __name__, url_prefix="/machinery")

from app.blueprints.machinery import routes  # noqa: E402, F401
