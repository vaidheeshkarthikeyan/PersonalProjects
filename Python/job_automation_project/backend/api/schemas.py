"""
Marshmallow serialization schemas for API responses.

Defines how database models and computed results are serialized
into clean JSON for the React frontend.
"""

from marshmallow import Schema, fields


class ApplicationLogSchema(Schema):
    """Serializes an ApplicationLog row for the /logs endpoint."""
    id = fields.Int(dump_only=True)
    timestamp = fields.DateTime(format="iso", dump_only=True)
    company = fields.Str()
    job_title = fields.Str()
    job_url = fields.Str(allow_none=True)
    status = fields.Str()
    failure_reason = fields.Str(allow_none=True)
    search_query = fields.Str(allow_none=True)
    run_id = fields.Int(allow_none=True)


class BotRunSchema(Schema):
    """Serializes a BotRun row for the /status endpoint."""
    id = fields.Int(dump_only=True)
    started_at = fields.DateTime(format="iso", dump_only=True)
    ended_at = fields.DateTime(format="iso", allow_none=True, dump_only=True)
    status = fields.Str()
    total_processed = fields.Int()
    total_applied = fields.Int()
    total_skipped = fields.Int()
    total_failed = fields.Int()
    search_query = fields.Str(allow_none=True)
    error_message = fields.Str(allow_none=True)


class KpiSchema(Schema):
    """Serializes lifetime KPI summary."""
    total_processed = fields.Int()
    total_applied = fields.Int()
    total_skipped = fields.Int()
    total_failed = fields.Int()


class DailyVolumeSchema(Schema):
    """Serializes a single day's application volume for the chart."""
    date = fields.Str()  # "YYYY-MM-DD"
    total = fields.Int()
    applied = fields.Int()
    skipped = fields.Int()
    failed = fields.Int()


class PaginatedLogsSchema(Schema):
    """Wraps a paginated list of ApplicationLog entries."""
    items = fields.List(fields.Nested(ApplicationLogSchema))
    total = fields.Int()
    page = fields.Int()
    per_page = fields.Int()
    pages = fields.Int()
