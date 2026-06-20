"""
SQLAlchemy ORM models for the job automation pipeline.

Tables
------
- **ApplicationLog**: One row per job application attempt (success, skip, or failure).
- **BotRun**: One row per automation session (start → stop lifecycle).
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    func,
)
from sqlalchemy.orm import DeclarativeBase


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Shared declarative base for all models."""
    pass


# ---------------------------------------------------------------------------
# ApplicationLog
# ---------------------------------------------------------------------------
class ApplicationLog(Base):
    """
    Records a single job-application attempt.

    Attributes
    ----------
    id : int
        Auto-incrementing primary key.
    timestamp : datetime
        UTC timestamp of when the application was processed.
    company : str
        Employer / company name scraped from the job card.
    job_title : str
        Position title scraped from the job card.
    job_url : str
        Direct URL to the LinkedIn job listing.
    status : str
        One of ``SUCCESS``, ``SKIPPED``, or ``FAILED``.
    failure_reason : str | None
        Human-readable reason when status is SKIPPED or FAILED.
    search_query : str
        The search keyword or URL that surfaced this job.
    run_id : int | None
        Foreign-key-style link to the BotRun that processed this job.
        Kept as a plain integer (not a formal FK) for simplicity.
    """

    __tablename__ = "application_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    company = Column(String(256), nullable=False, default="Unknown")
    job_title = Column(String(256), nullable=False, default="Unknown")
    job_url = Column(String(1024), nullable=True)
    status = Column(String(32), nullable=False, index=True)  # SUCCESS | SKIPPED | FAILED
    failure_reason = Column(Text, nullable=True)
    search_query = Column(String(256), nullable=True)
    run_id = Column(Integer, nullable=True, index=True)

    def __repr__(self) -> str:
        return (
            f"<ApplicationLog(id={self.id}, company='{self.company}', "
            f"status='{self.status}')>"
        )


# ---------------------------------------------------------------------------
# BotRun
# ---------------------------------------------------------------------------
class BotRun(Base):
    """
    Tracks a single automation session lifecycle.

    A run starts when the user clicks "Start" on the dashboard and ends
    when the bot finishes, is stopped manually, or crashes.

    Attributes
    ----------
    id : int
        Auto-incrementing primary key.
    started_at : datetime
        UTC timestamp of when the run began.
    ended_at : datetime | None
        UTC timestamp of when the run finished.  ``None`` while running.
    status : str
        One of ``RUNNING``, ``COMPLETED``, ``STOPPED``, ``ERRORED``.
    total_processed : int
        Total number of job cards inspected during this run.
    total_applied : int
        Number of successful applications submitted.
    total_skipped : int
        Number of jobs skipped (no Easy Apply, already applied, etc.).
    total_failed : int
        Number of jobs where the apply attempt failed.
    search_query : str
        The LinkedIn search query / URL used for this run.
    error_message : str | None
        If status is ERRORED, the exception message.
    """

    __tablename__ = "bot_run"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, default="RUNNING", index=True)
    total_processed = Column(Integer, nullable=False, default=0)
    total_applied = Column(Integer, nullable=False, default=0)
    total_skipped = Column(Integer, nullable=False, default=0)
    total_failed = Column(Integer, nullable=False, default=0)
    search_query = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<BotRun(id={self.id}, status='{self.status}', "
            f"applied={self.total_applied})>"
        )
