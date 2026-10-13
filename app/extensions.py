from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Initialize core database, migration, and CSRF extensions
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
