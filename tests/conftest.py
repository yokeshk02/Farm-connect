import os
import pytest
from app import create_app
from app.extensions import db


@pytest.fixture(scope="session")
def app():
    """Create a Flask application instance configured for testing."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for HTTP request simulation."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Provide a transactional database session for each test with clean table teardown."""
    with app.app_context():
        yield db.session
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture(scope="session")
def pg_app():
    """Create an application instance connected to PostgreSQL if DATABASE_URL is available."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "postgresql" not in db_url:
        pytest.skip("PostgreSQL DATABASE_URL not configured")
    
    app_instance = create_app("development")
    yield app_instance
