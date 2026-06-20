# LinkedIn AutoApply — AI Job Automation Pipeline

An automated LinkedIn job application system targeting AI/ML engineering roles, with a real-time monitoring dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Dashboard                         │
│  KPI Cards │ Volume Chart │ App Table │ Control Panel       │
│                    ↕ Axios (REST)                           │
├─────────────────────────────────────────────────────────────┤
│                     Flask API                               │
│  /api/dashboard/* (KPIs, volume, logs)                      │
│  /api/bot/* (start, stop, status)                           │
│                    ↕ SQLAlchemy                              │
├─────────────────────────────────────────────────────────────┤
│                   SQLite / PostgreSQL                        │
│  ApplicationLog │ BotRun                                    │
├─────────────────────────────────────────────────────────────┤
│                  Playwright Engine                           │
│  Browser → Auth → Navigator → Applicant → QuestionSolver   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your LinkedIn credentials, SMTP settings, etc.
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
playwright install chromium

# Run the Flask API
flask --app backend.wsgi run --debug
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Open Dashboard

Navigate to `http://localhost:5173` to access the monitoring dashboard.

## Tech Stack

| Layer          | Technology            |
|----------------|-----------------------|
| Automation     | Playwright (sync API) |
| Backend API    | Flask + Flask-CORS    |
| Database       | SQLAlchemy (SQLite)   |
| Frontend       | React 18 + Vite       |
| Charts         | Recharts              |
| Serialization  | Marshmallow           |
| Question AI    | Rule-based + OpenAI   |
| Email Alerts   | SMTP (smtplib)        |

## Project Structure

```
job_automation_project/
├── .env.example              # Environment template
├── backend/
│   ├── app.py                # Flask app factory
│   ├── config.py             # Centralised configuration
│   ├── wsgi.py               # WSGI entry point
│   ├── api/                  # REST API routes
│   ├── database/             # ORM models & connection
│   ├── engine/               # Playwright automation
│   └── tests/                # pytest suite
└── frontend/
    ├── src/
    │   ├── api/              # Axios client
    │   ├── components/       # React components
    │   └── pages/            # Dashboard page
    └── package.json
```

## Running Tests

```bash
# From the project root
pytest backend/tests/ -v
```

## Important Notes

- **Never commit** your `.env` file — it contains LinkedIn credentials.
- Edit `backend/engine/developer_profile.json` with your real professional profile.
- First run in **headed mode** (`HEADLESS=false`) to handle any CAPTCHA/2FA manually.
- The saved session state (`storage_state.json`) allows subsequent headless runs.

## License

Private — for personal use only.
