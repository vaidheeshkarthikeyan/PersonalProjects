"""
Database connection factory.

Provides a SQLAlchemy engine and scoped session factory.
Swap between SQLite and PostgreSQL by changing DATABASE_URL in .env.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from backend.config import DATABASE_URL

# ---------------------------------------------------------------------------
# Engine — single connection pool shared across the application
# ---------------------------------------------------------------------------
# check_same_thread=False is required for SQLite when used with Flask's
# threaded request handling.  It has no effect on PostgreSQL.
_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    echo=False,  # Set True to log all SQL statements (noisy but useful for debugging)
    pool_pre_ping=True,  # Reconnect stale connections automatically
)

# ---------------------------------------------------------------------------
# Session factory — use get_session() in request handlers and engine code
# ---------------------------------------------------------------------------
SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
ScopedSession = scoped_session(SessionFactory)


def get_session():
    """
    Return a new database session.

    Usage::

        session = get_session()
        try:
            # ... work ...
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    """
    return ScopedSession()


def init_db():
    """
    Create all tables that don't yet exist.

    Call this once at application startup (e.g., in the Flask app factory).
    Importing models first ensures SQLAlchemy's Base.metadata knows about them.
    """
    from backend.database.models import Base  # noqa: F811 — imported for side-effect

    Base.metadata.create_all(bind=engine)
    print("[DB] Tables created / verified.")


def shutdown_session(exception=None):
    """
    Remove the scoped session at the end of a request.

    Register this with Flask::

        app.teardown_appcontext(shutdown_session)
    """
    ScopedSession.remove()
