"""
Telemetry writer — records application results to the database.

Thread-safe: designed to be called from the Playwright engine running
in a background thread while the Flask API reads from the same DB.
"""

from datetime import datetime, timezone
from backend.database.connection import get_session
from backend.database.models import ApplicationLog, BotRun


class TelemetryWriter:
    """
    Writes application telemetry to the SQL database.

    Each method manages its own session lifecycle for thread safety.
    """

    # ----- Application Log -----

    @staticmethod
    def log_application(
        company: str,
        job_title: str,
        job_url: str | None,
        status: str,
        failure_reason: str | None = None,
        search_query: str | None = None,
        run_id: int | None = None,
    ) -> int:
        """
        Record a single application attempt.

        Parameters
        ----------
        company : str
            Employer name.
        job_title : str
            Position title.
        job_url : str | None
            Direct link to the listing.
        status : str
            One of ``SUCCESS``, ``SKIPPED``, ``FAILED``.
        failure_reason : str | None
            Populated when status is SKIPPED or FAILED.
        search_query : str | None
            The query that surfaced this job.
        run_id : int | None
            The BotRun.id for this session.

        Returns
        -------
        int
            The ID of the newly created ApplicationLog row.
        """
        session = get_session()
        try:
            entry = ApplicationLog(
                company=company,
                job_title=job_title,
                job_url=job_url,
                status=status,
                failure_reason=failure_reason,
                search_query=search_query,
                run_id=run_id,
            )
            session.add(entry)
            session.commit()
            log_id = entry.id
            print(
                f"[Telemetry] Logged: {status} — {company} / {job_title} "
                f"(id={log_id})"
            )
            return log_id
        except Exception as e:
            session.rollback()
            print(f"[Telemetry] ERROR writing application log: {e}")
            raise
        finally:
            session.close()

    # ----- Bot Run lifecycle -----

    @staticmethod
    def start_run(search_query: str) -> int:
        """
        Create a new BotRun row with status RUNNING.

        Parameters
        ----------
        search_query : str
            The LinkedIn search query for this run.

        Returns
        -------
        int
            The ID of the new BotRun row.
        """
        session = get_session()
        try:
            run = BotRun(
                status="RUNNING",
                search_query=search_query,
            )
            session.add(run)
            session.commit()
            run_id = run.id
            print(f"[Telemetry] Bot run started (id={run_id}, query='{search_query}')")
            return run_id
        except Exception as e:
            session.rollback()
            print(f"[Telemetry] ERROR starting bot run: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def update_run_counters(
        run_id: int,
        total_processed: int,
        total_applied: int,
        total_skipped: int,
        total_failed: int,
    ) -> None:
        """Update the running counters on an active BotRun."""
        session = get_session()
        try:
            run = session.query(BotRun).filter_by(id=run_id).first()
            if run:
                run.total_processed = total_processed
                run.total_applied = total_applied
                run.total_skipped = total_skipped
                run.total_failed = total_failed
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"[Telemetry] ERROR updating run counters: {e}")
        finally:
            session.close()

    @staticmethod
    def end_run(
        run_id: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """
        Mark a BotRun as finished.

        Parameters
        ----------
        run_id : int
            The BotRun to update.
        status : str
            Final status: ``COMPLETED``, ``STOPPED``, or ``ERRORED``.
        error_message : str | None
            Exception message if status is ERRORED.
        """
        session = get_session()
        try:
            run = session.query(BotRun).filter_by(id=run_id).first()
            if run:
                run.ended_at = datetime.now(timezone.utc)
                run.status = status
                run.error_message = error_message
                session.commit()
                print(
                    f"[Telemetry] Bot run ended (id={run_id}, status={status})"
                )
        except Exception as e:
            session.rollback()
            print(f"[Telemetry] ERROR ending bot run: {e}")
        finally:
            session.close()
