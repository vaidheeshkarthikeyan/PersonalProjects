"""
Integration tests for Flask API endpoints.

Uses Flask's test client with a temporary in-memory SQLite database.
Seeds test data and verifies response shapes, status codes, and pagination.
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from backend.database.models import Base, ApplicationLog, BotRun


@pytest.fixture
def app():
    """Create a Flask test app with an in-memory database."""
    from flask import Flask
    from flask_cors import CORS
    from backend.api.routes_dashboard import dashboard_bp
    from backend.api.routes_bot import bot_bp
    from backend.database import connection as db_conn

    # Override the database connection for testing
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)
    test_session_factory = sessionmaker(bind=test_engine)
    test_scoped = scoped_session(test_session_factory)

    # Monkey-patch the connection module
    db_conn.engine = test_engine
    db_conn.SessionFactory = test_session_factory
    db_conn.ScopedSession = test_scoped

    app = Flask(__name__)
    app.secret_key = "test-secret"
    CORS(app)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(bot_bp)
    app.teardown_appcontext(db_conn.shutdown_session)

    yield app

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def seeded_app(app):
    """Seed the test database with sample data."""
    from backend.database.connection import get_session

    session = get_session()
    now = datetime.now(timezone.utc)

    # Seed ApplicationLog entries across several days
    for i in range(30):
        day_offset = i % 7
        statuses = ["SUCCESS", "SKIPPED", "FAILED"]
        status = statuses[i % 3]
        session.add(ApplicationLog(
            company=f"Company_{i}",
            job_title=f"AI Engineer {i}",
            job_url=f"https://linkedin.com/jobs/{i}",
            status=status,
            failure_reason=f"Reason {i}" if status != "SUCCESS" else None,
            search_query="AI Engineer",
            run_id=1,
            timestamp=now - timedelta(days=day_offset, hours=i),
        ))

    # Seed a BotRun
    session.add(BotRun(
        status="COMPLETED",
        search_query="AI Engineer",
        started_at=now - timedelta(hours=2),
        ended_at=now - timedelta(hours=1),
        total_processed=30,
        total_applied=10,
        total_skipped=10,
        total_failed=10,
    ))

    session.commit()
    session.close()
    return app


@pytest.fixture
def seeded_client(seeded_app):
    return seeded_app.test_client()


class TestDashboardKpis:
    def test_kpis_empty(self, client):
        resp = client.get("/api/dashboard/kpis")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_processed"] == 0
        assert data["total_applied"] == 0

    def test_kpis_with_data(self, seeded_client):
        resp = seeded_client.get("/api/dashboard/kpis")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_processed"] == 30
        assert data["total_applied"] == 10
        assert data["total_skipped"] == 10
        assert data["total_failed"] == 10


class TestDashboardVolume:
    def test_volume_returns_7_days(self, seeded_client):
        resp = seeded_client.get("/api/dashboard/volume")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        # The 7-day window may span 7 or 8 calendar dates depending on
        # UTC boundary alignment, but should always be in that range
        assert 7 <= len(data) <= 8
        # Each entry should have date, total, applied, skipped, failed
        for entry in data:
            assert "date" in entry
            assert "total" in entry
            assert "applied" in entry

    def test_volume_empty(self, client):
        resp = client.get("/api/dashboard/volume")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 7
        # All zeros
        for entry in data:
            assert entry["total"] == 0


class TestDashboardLogs:
    def test_logs_default_pagination(self, seeded_client):
        resp = seeded_client.get("/api/dashboard/logs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert data["total"] == 30
        assert data["page"] == 1
        assert len(data["items"]) <= 20

    def test_logs_custom_pagination(self, seeded_client):
        resp = seeded_client.get("/api/dashboard/logs?page=2&per_page=10")
        data = resp.get_json()
        assert data["page"] == 2
        assert len(data["items"]) == 10

    def test_logs_status_filter(self, seeded_client):
        resp = seeded_client.get("/api/dashboard/logs?status=SUCCESS")
        data = resp.get_json()
        assert data["total"] == 10
        for item in data["items"]:
            assert item["status"] == "SUCCESS"

    def test_logs_search_filter(self, seeded_client):
        resp = seeded_client.get("/api/dashboard/logs?search=Company_1")
        data = resp.get_json()
        # Should match Company_1, Company_10, Company_11, etc.
        assert data["total"] > 0
        for item in data["items"]:
            assert "Company_1" in item["company"]

    def test_logs_empty(self, client):
        resp = client.get("/api/dashboard/logs")
        data = resp.get_json()
        assert data["total"] == 0
        assert data["items"] == []


class TestBotStatus:
    def test_status_idle(self, client):
        resp = client.get("/api/bot/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["bot_status"] == "IDLE"


class TestHealthCheck:
    def test_health(self, app):
        # Register health endpoint
        @app.route("/api/health")
        def health():
            return {"status": "ok"}

        client = app.test_client()
        resp = client.get("/api/health")
        assert resp.status_code == 200
