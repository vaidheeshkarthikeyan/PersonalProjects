"""
Bot control API routes — start, stop, and check status of the automation engine.

Endpoints
---------
POST /api/bot/start    → Start the Playwright engine in a background thread
POST /api/bot/stop     → Signal the engine to stop gracefully
GET  /api/bot/status   → Current bot state + active run stats
"""

import threading
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from backend.database.connection import get_session
from backend.database.models import BotRun
from backend.api.schemas import BotRunSchema
from backend.api.email_alerts import send_run_complete_email
from backend import config

bot_bp = Blueprint("bot", __name__, url_prefix="/api/bot")


# ===================================================================
# Bot Controller Singleton
# ===================================================================

class BotController:
    """
    Manages the lifecycle of the automation engine thread.

    Only one bot instance can run at a time.  Uses a threading.Event
    to signal graceful shutdown.
    """

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._current_run_id: int | None = None
        self._status: str = "IDLE"  # IDLE, RUNNING, STOPPING
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def status(self) -> str:
        with self._lock:
            if self._status == "RUNNING" and not self.is_running:
                self._status = "IDLE"
            return self._status

    @property
    def current_run_id(self) -> int | None:
        return self._current_run_id

    def start(self, search_query: str) -> int:
        """
        Launch the automation engine in a background thread.

        Returns the new BotRun ID.

        Raises
        ------
        RuntimeError
            If a bot instance is already running.
        """
        with self._lock:
            if self.is_running:
                raise RuntimeError("Bot is already running.")

            self._stop_event.clear()
            self._status = "RUNNING"

        # Create the BotRun record
        from backend.engine.telemetry import TelemetryWriter
        run_id = TelemetryWriter.start_run(search_query)
        self._current_run_id = run_id

        # Launch in background thread
        self._thread = threading.Thread(
            target=self._run_engine,
            args=(run_id, search_query),
            daemon=True,
            name=f"bot-run-{run_id}",
        )
        self._thread.start()
        return run_id

    def stop(self) -> None:
        """Signal the engine to stop gracefully."""
        with self._lock:
            if not self.is_running:
                return
            self._status = "STOPPING"
        self._stop_event.set()
        print("[BotController] Stop signal sent.")

    def _run_engine(self, run_id: int, search_query: str) -> None:
        """
        The actual engine execution — runs in a background thread.

        Orchestrates: browser → auth → navigate → apply loop → teardown.
        """
        from backend.engine.browser import BrowserManager
        from backend.engine.auth import Authenticator
        from backend.engine.navigator import JobNavigator
        from backend.engine.applicant import JobApplicant
        from backend.engine.question_solver import RuleBasedSolver, OpenAISolver
        from backend.engine.telemetry import TelemetryWriter

        start_time = time.time()
        total_processed = 0
        total_applied = 0
        total_skipped = 0
        total_failed = 0
        error_message = None
        final_status = "COMPLETED"

        try:
            with BrowserManager(
                headless=config.HEADLESS,
                storage_state_path=config.STORAGE_STATE_PATH,
            ) as bm:
                page = bm.page

                # Authenticate
                auth = Authenticator(page, config.LI_EMAIL, config.LI_PASSWORD)
                auth.ensure_authenticated()

                # Set up question solver
                openai_solver = OpenAISolver(
                    api_key=config.OPENAI_API_KEY,
                    model=config.OPENAI_MODEL,
                    profile=None,  # Will be loaded by RuleBasedSolver
                )
                solver = RuleBasedSolver(
                    profile_path=config.DEVELOPER_PROFILE_PATH,
                    fallback_solver=openai_solver,
                )
                # Share the loaded profile with OpenAI solver
                openai_solver.profile = solver.profile

                # Navigate and process each keyword
                keywords = [kw.strip() for kw in search_query.split(",")]
                navigator = JobNavigator(
                    page=page,
                    keywords=keywords,
                    date_posted=config.DATE_POSTED,
                    experience_level=config.EXPERIENCE_LEVEL,
                )

                for keyword in keywords:
                    if self._stop_event.is_set():
                        final_status = "STOPPED"
                        break

                    print(f"\n[Engine] Processing keyword: '{keyword}'")
                    navigator.navigate_to_search(keyword)
                    cards = navigator.scroll_job_list()

                    applicant = JobApplicant(
                        page=page,
                        question_solver=solver,
                        phone_number=config.LI_PHONE,
                        stop_event=self._stop_event,
                        run_id=run_id,
                        search_query=keyword,
                    )

                    result = applicant.process_all(cards)
                    total_processed += result["processed"]
                    total_applied += result["applied"]
                    total_skipped += result["skipped"]
                    total_failed += result["failed"]

                if self._stop_event.is_set() and final_status != "STOPPED":
                    final_status = "STOPPED"

        except Exception as e:
            final_status = "ERRORED"
            error_message = str(e)
            print(f"[Engine] Fatal error: {e}")

        finally:
            # Finalize the run record
            duration = time.time() - start_time
            TelemetryWriter.update_run_counters(
                run_id, total_processed, total_applied, total_skipped, total_failed
            )
            TelemetryWriter.end_run(run_id, final_status, error_message)

            # Send email alert
            send_run_complete_email(
                run_id=run_id,
                status=final_status,
                total_processed=total_processed,
                total_applied=total_applied,
                total_skipped=total_skipped,
                total_failed=total_failed,
                search_query=search_query,
                error_message=error_message,
                duration_seconds=duration,
            )

            with self._lock:
                self._status = "IDLE"

            print(f"[Engine] Run #{run_id} finished: {final_status} in {duration:.1f}s")


# Module-level singleton
_controller = BotController()


# ===================================================================
# Route handlers
# ===================================================================

@bot_bp.route("/start", methods=["POST"])
def start_bot():
    """
    Start the Playwright automation engine.

    Request Body
    ------------
    {
        "search_query": "AI Engineer,Machine Learning Engineer"  (optional)
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    search_query = data.get(
        "search_query",
        ",".join(config.SEARCH_KEYWORDS),
    )

    try:
        run_id = _controller.start(search_query)
        return jsonify({
            "status": "started",
            "run_id": run_id,
            "search_query": search_query,
        }), 202
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 409


@bot_bp.route("/stop", methods=["POST"])
def stop_bot():
    """Signal the bot to stop gracefully after the current card."""
    _controller.stop()
    return jsonify({"status": "stop_signal_sent"}), 200


@bot_bp.route("/status", methods=["GET"])
def bot_status():
    """
    Return the current bot state and active run details.

    Response
    --------
    {
        "bot_status": "IDLE" | "RUNNING" | "STOPPING",
        "current_run": { ... BotRun fields ... } | null
    }
    """
    current_run = None
    if _controller.current_run_id:
        session = get_session()
        try:
            run = session.query(BotRun).filter_by(id=_controller.current_run_id).first()
            if run:
                current_run = BotRunSchema().dump(run)
        finally:
            session.close()

    return jsonify({
        "bot_status": _controller.status,
        "current_run": current_run,
    })
