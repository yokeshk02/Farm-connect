import os
from app import create_app

# Instantiate the Flask application using environment settings
app = create_app()

if __name__ == "__main__":
    # Support direct execution with python run.py
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug = app.config.get("DEBUG", False)
    app.run(host=host, port=port, debug=debug)
