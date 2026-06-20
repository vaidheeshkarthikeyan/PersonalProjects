"""
Unit tests for database models — ApplicationLog and BotRun.

Uses an in-memory SQLite database for fast, isolated tests.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, ApplicationLog, BotRun


@pytest.fixture
def session():
    """Create an in-memory SQLite database and return a session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestApplicationLog:
    """Tests for the ApplicationLog model."""

    def test_create_success_entry(self, session):
        entry = ApplicationLog(
            company="Google",
            job_title="AI Engineer",
            job_url="https://linkedin.com/jobs/123",
            status="SUCCESS",
            search_query="AI Engineer",
            run_id=1,
        )
        session.add(entry)
        session.commit()

        result = session.query(ApplicationLog).first()
        assert result is not None
        assert result.company == "Google"
        assert result.job_title == "AI Engineer"
        assert result.status == "SUCCESS"
        assert result.failure_reason is None
        assert result.timestamp is not None

    def test_create_failed_entry_with_reason(self, session):
        entry = ApplicationLog(
            company="Meta",
            job_title="ML Engineer",
            status="FAILED",
            failure_reason="Timeout during modal processing",
        )
        session.add(entry)
        session.commit()

        result = session.query(ApplicationLog).first()
        assert result.status == "FAILED"
        assert result.failure_reason == "Timeout during modal processing"

    def test_create_skipped_entry(self, session):
        entry = ApplicationLog(
            company="Apple",
            job_title="Senior AI Researcher",
            status="SKIPPED",
            failure_reason="No Easy Apply button",
        )
        session.add(entry)
        session.commit()

        result = session.query(ApplicationLog).first()
        assert result.status == "SKIPPED"
        assert result.failure_reason == "No Easy Apply button"

    def test_multiple_entries(self, session):
        entries = [
            ApplicationLog(company="Co1", job_title="J1", status="SUCCESS"),
            ApplicationLog(company="Co2", job_title="J2", status="SKIPPED"),
            ApplicationLog(company="Co3", job_title="J3", status="FAILED"),
        ]
        session.add_all(entries)
        session.commit()

        assert session.query(ApplicationLog).count() == 3
        assert session.query(ApplicationLog).filter_by(status="SUCCESS").count() == 1

    def test_default_company(self, session):
        entry = ApplicationLog(status="SUCCESS")
        session.add(entry)
        session.commit()

        result = session.query(ApplicationLog).first()
        assert result.company == "Unknown"
        assert result.job_title == "Unknown"

    def test_repr(self, session):
        entry = ApplicationLog(company="TestCo", job_title="TestJob", status="SUCCESS")
        session.add(entry)
        session.commit()

        result = session.query(ApplicationLog).first()
        r = repr(result)
        assert "TestCo" in r
        assert "SUCCESS" in r


class TestBotRun:
    """Tests for the BotRun model."""

    def test_create_running_entry(self, session):
        run = BotRun(
            status="RUNNING",
            search_query="AI Engineer",
        )
        session.add(run)
        session.commit()

        result = session.query(BotRun).first()
        assert result is not None
        assert result.status == "RUNNING"
        assert result.ended_at is None
        assert result.total_processed == 0
        assert result.total_applied == 0

    def test_complete_run(self, session):
        run = BotRun(status="RUNNING", search_query="ML Engineer")
        session.add(run)
        session.commit()

        # Simulate completion
        run.status = "COMPLETED"
        run.ended_at = datetime.now(timezone.utc)
        run.total_processed = 25
        run.total_applied = 15
        run.total_skipped = 7
        run.total_failed = 3
        session.commit()

        result = session.query(BotRun).first()
        assert result.status == "COMPLETED"
        assert result.ended_at is not None
        assert result.total_processed == 25
        assert result.total_applied == 15

    def test_errored_run(self, session):
        run = BotRun(
            status="ERRORED",
            error_message="Connection refused",
            search_query="AI Engineer",
        )
        session.add(run)
        session.commit()

        result = session.query(BotRun).first()
        assert result.status == "ERRORED"
        assert result.error_message == "Connection refused"

    def test_repr(self, session):
        run = BotRun(status="RUNNING", search_query="Test")
        session.add(run)
        session.commit()

        r = repr(session.query(BotRun).first())
        assert "RUNNING" in r
