"""
Dashboard API routes — read-only endpoints for the React frontend.

Endpoints
---------
GET /api/dashboard/kpis     → Lifetime KPI summary
GET /api/dashboard/volume   → 7-day trailing application volume
GET /api/dashboard/logs     → Paginated + filterable application log
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import func, case, cast, Date

from backend.database.connection import get_session
from backend.database.models import ApplicationLog
from backend.api.schemas import (
    KpiSchema,
    DailyVolumeSchema,
    PaginatedLogsSchema,
    ApplicationLogSchema,
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


# ===================================================================
# GET /api/dashboard/kpis
# ===================================================================
@dashboard_bp.route("/kpis", methods=["GET"])
def get_kpis():
    """Return lifetime KPI counts: total, applied, skipped, failed."""
    session = get_session()
    try:
        result = session.query(
            func.count(ApplicationLog.id).label("total_processed"),
            func.sum(
                case((ApplicationLog.status == "SUCCESS", 1), else_=0)
            ).label("total_applied"),
            func.sum(
                case((ApplicationLog.status == "SKIPPED", 1), else_=0)
            ).label("total_skipped"),
            func.sum(
                case((ApplicationLog.status == "FAILED", 1), else_=0)
            ).label("total_failed"),
        ).one()

        kpis = {
            "total_processed": result.total_processed or 0,
            "total_applied": int(result.total_applied or 0),
            "total_skipped": int(result.total_skipped or 0),
            "total_failed": int(result.total_failed or 0),
        }
        return jsonify(KpiSchema().dump(kpis))

    finally:
        session.close()


# ===================================================================
# GET /api/dashboard/volume
# ===================================================================
@dashboard_bp.route("/volume", methods=["GET"])
def get_volume():
    """
    Return daily application counts for the trailing 7 days.

    Each day includes total, applied, skipped, and failed counts
    for the stacked bar chart.
    """
    session = get_session()
    try:
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        # Query daily counts grouped by date and status
        # Use func.date() for SQLite compatibility (cast to Date can fail)
        rows = (
            session.query(
                func.date(ApplicationLog.timestamp).label("date"),
                ApplicationLog.status,
                func.count(ApplicationLog.id).label("count"),
            )
            .filter(ApplicationLog.timestamp >= seven_days_ago)
            .group_by(func.date(ApplicationLog.timestamp), ApplicationLog.status)
            .all()
        )

        # Build a dict keyed by date string
        volume_map: dict[str, dict] = {}
        for i in range(7):
            day = (now - timedelta(days=6 - i)).strftime("%Y-%m-%d")
            volume_map[day] = {"date": day, "total": 0, "applied": 0, "skipped": 0, "failed": 0}

        for row in rows:
            day_str = row.date.strftime("%Y-%m-%d") if hasattr(row.date, "strftime") else str(row.date)
            if day_str not in volume_map:
                volume_map[day_str] = {"date": day_str, "total": 0, "applied": 0, "skipped": 0, "failed": 0}
            volume_map[day_str]["total"] += row.count
            status_key = row.status.lower()  # SUCCESS → applied, etc.
            if status_key == "success":
                volume_map[day_str]["applied"] += row.count
            elif status_key == "skipped":
                volume_map[day_str]["skipped"] += row.count
            elif status_key == "failed":
                volume_map[day_str]["failed"] += row.count

        # Return sorted by date — plain dicts, no schema needed
        volume_list = sorted(volume_map.values(), key=lambda x: x["date"])
        return jsonify(volume_list)

    finally:
        session.close()


# ===================================================================
# GET /api/dashboard/logs
# ===================================================================
@dashboard_bp.route("/logs", methods=["GET"])
def get_logs():
    """
    Return a paginated, filterable list of application log entries.

    Query Parameters
    ----------------
    page : int (default 1)
    per_page : int (default 20, max 100)
    status : str (optional) — filter by status (SUCCESS, SKIPPED, FAILED)
    search : str (optional) — search company or job_title (case-insensitive)
    """
    session = get_session()
    try:
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        status_filter = request.args.get("status", None)
        search_filter = request.args.get("search", None)

        query = session.query(ApplicationLog)

        # Apply filters
        if status_filter and status_filter.upper() in ("SUCCESS", "SKIPPED", "FAILED"):
            query = query.filter(ApplicationLog.status == status_filter.upper())

        if search_filter:
            like_pattern = f"%{search_filter}%"
            query = query.filter(
                (ApplicationLog.company.ilike(like_pattern))
                | (ApplicationLog.job_title.ilike(like_pattern))
            )

        # Count total results (before pagination)
        total = query.count()

        # Order by newest first + paginate
        items = (
            query.order_by(ApplicationLog.timestamp.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        total_pages = (total + per_page - 1) // per_page  # ceiling division

        # Serialize items manually to avoid Marshmallow DateTime issues
        # with SQLite string timestamps
        serialized_items = []
        for item in items:
            ts = item.timestamp
            if hasattr(ts, 'isoformat'):
                ts_str = ts.isoformat()
            else:
                ts_str = str(ts) if ts else None

            serialized_items.append({
                "id": item.id,
                "timestamp": ts_str,
                "company": item.company,
                "job_title": item.job_title,
                "job_url": item.job_url,
                "status": item.status,
                "failure_reason": item.failure_reason,
                "search_query": item.search_query,
                "run_id": item.run_id,
            })

        result = {
            "items": serialized_items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": total_pages,
        }
        return jsonify(result)

    finally:
        session.close()
