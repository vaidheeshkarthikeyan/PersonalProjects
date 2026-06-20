"""
WSGI entry point for the Flask application.

Run locally:
    flask --app backend.wsgi run --debug

Run with Gunicorn (production):
    gunicorn backend.wsgi:app
"""

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
