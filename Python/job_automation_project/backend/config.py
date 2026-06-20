"""
Centralised application configuration.

Loads all settings from environment variables via python-dotenv.
Validates that critical variables are present at import time.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from the project root (one level above /backend)
# ---------------------------------------------------------------------------
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(dotenv_path=_env_path)


def _require_env(key: str) -> str:
    """Return the value of an environment variable or abort with a clear message."""
    value = os.getenv(key)
    if not value:
        print(
            f"[FATAL] Required environment variable '{key}' is not set. "
            f"Please add it to your .env file at: {_env_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    return value


# ===================================================================
# LinkedIn Credentials (REQUIRED)
# ===================================================================
LI_EMAIL: str = _require_env("LI_EMAIL")
LI_PASSWORD: str = _require_env("LI_PASSWORD")
LI_PHONE: str = os.getenv("LI_PHONE", "")

# ===================================================================
# Search Configuration
# ===================================================================
SEARCH_KEYWORDS: list[str] = [
    kw.strip()
    for kw in os.getenv("SEARCH_KEYWORDS", "AI Engineer,Machine Learning Engineer").split(",")
]
DATE_POSTED: str = os.getenv("DATE_POSTED", "r604800")  # past week
EXPERIENCE_LEVEL: str = os.getenv("EXPERIENCE_LEVEL", "2,3,4")

# ===================================================================
# Database
# ===================================================================
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{_project_root / 'job_automation.db'}",
)

# ===================================================================
# Flask
# ===================================================================
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "true").lower() in ("true", "1", "yes")

# ===================================================================
# Playwright
# ===================================================================
HEADLESS: bool = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")

# Path to persist browser session state (cookies, localStorage)
STORAGE_STATE_PATH: str = str(_project_root / "storage_state.json")

# ===================================================================
# OpenAI (Optional — fallback question solver)
# ===================================================================
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ===================================================================
# Email Alerts (Optional)
# ===================================================================
SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL_TO: str = os.getenv("ALERT_EMAIL_TO", "")

# Convenience flag: True if all SMTP settings are configured
EMAIL_ALERTS_ENABLED: bool = all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO])

# ===================================================================
# Developer Profile (for question solver)
# ===================================================================
DEVELOPER_PROFILE_PATH: str = str(
    Path(__file__).resolve().parent / "engine" / "developer_profile.json"
)
