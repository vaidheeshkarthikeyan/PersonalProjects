"""
Flask application factory.

Creates and configures the Flask app with CORS, database lifecycle
hooks, and API blueprint registration.
"""

from flask import Flask
from flask_cors import CORS

from backend.database.connection import init_db, shutdown_session


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Returns
    -------
    Flask
        The configured Flask app instance.
    """
    app = Flask(__name__)

    # Load configuration
    from backend import config
    app.secret_key = config.FLASK_SECRET_KEY
    app.config["DEBUG"] = config.FLASK_DEBUG

    # CORS — allow the React dev server
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
        }
    })

    # Database teardown — clean up sessions after each request
    app.teardown_appcontext(shutdown_session)

    # Initialise database tables
    with app.app_context():
        init_db()

    # Register API blueprints
    from backend.api.routes_dashboard import dashboard_bp
    from backend.api.routes_bot import bot_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(bot_bp)

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health():
        return {"status": "ok", "service": "linkedin-job-automation"}

    print("[App] Flask application created successfully.")
    return app
