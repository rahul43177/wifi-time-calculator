# DailyFour

**Track Your Daily 4-Hour Work Goal**

DailyFour is a local-first FastAPI application that tracks office presence by detecting Wi-Fi connectivity, managing office sessions, and calculating target completion time (work duration + buffer).  
It uses MongoDB-backed daily aggregation with a browser dashboard for live status and analytics.

## Current Status

**✅ Production Ready - All Core Features Implemented**

Phases 1-12 Complete:
- ✅ Wi-Fi detection with dual fallback (networksetup → system_profiler)
- ✅ Session lifecycle management with state machine
- ✅ Timer engine with configurable buffer and test mode
- ✅ Browser and macOS notifications
- ✅ Dashboard UI with live timer, today's sessions
- ✅ Weekly analytics with Chart.js visualization
- ✅ Monthly analytics with Chart.js visualization
- ✅ **Auto-start on login (launchd integration)**
- ✅ Professional UI polish (emoji-free interface, dark-mode contrast fixes, refined chart/table/card styling)
- ✅ Documented design system (`docs/DESIGN_SYSTEM.md`)

**Current Test Baseline:** 520 passed, 101 skipped (`venv/bin/python -m pytest -q`)

**Next:** Optional product enhancements (exports, mobile, advanced reporting)

For exact phase/task status, see `docs/action-plan.md`.

## Core Features

- Automatic office session tracking from Wi-Fi SSID transitions
- Session recovery after restart
- Timer tracking with configurable buffer and optional short test mode
- Single dashboard with live status, today’s sessions, and weekly analytics
- Browser and macOS notification support
- MongoDB-backed daily session tracking (no SQL database)

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- Pydantic / pydantic-settings
- Jinja2 templates
- Vanilla JavaScript + Chart.js (CDN)
- Pytest

## Project Layout

```text
app/
  main.py              FastAPI app and endpoints
  config.py            Environment-backed settings
  wifi_detector.py     SSID detection and polling
  session_manager.py   Session state machine and validation
  timer_engine.py      Timer calculations and polling loop
  notifier.py          macOS notification integration
  file_store.py        JSONL persistence and rotation
  analytics.py         Weekly/monthly aggregation helpers

templates/
  index.html           Dashboard template

static/
  style.css            Dashboard styles
  app.js               Dashboard client logic

tests/
  test_phase_*.py      Phase-driven backend and integration tests
```

## Quick Start

### 1. Setup

```bash
cd /Users/rahulmishra/Desktop/Personal/wifi-tracking
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Minimum required edit in `.env`:

```env
OFFICE_WIFI_NAME=YourActualOfficeWiFiName
```

### 3. Run

```bash
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8787 --reload
```

Open:
- Dashboard: http://127.0.0.1:8787/
- Health: http://127.0.0.1:8787/health

### 4. (Optional) Enable Auto-Start on Login

To have the tracker start automatically when you log in:

```bash
./scripts/install-autostart.sh
```

This installs a launchd service that:
- ✅ Starts automatically when you log in
- ✅ Restarts if it crashes (KeepAlive)
- ✅ Logs to `logs/stdout.log` and `logs/stderr.log`

**Verify it's running:**
```bash
launchctl list | grep officetracker
curl http://127.0.0.1:8787/health
```

**To uninstall auto-start:**
```bash
./scripts/uninstall-autostart.sh
```

**Full documentation:** See `docs/PHASE_6_AUTO_START_GUIDE.md`

## Configuration Reference

Key environment variables (see `.env.example` for full list):

- `OFFICE_WIFI_NAME`: office SSID to track
- `SERVER_HOST`, `SERVER_PORT`: web server bind settings
- `WORK_DURATION_HOURS`: base target duration
- `BUFFER_MINUTES`: extra minutes added to target
- `WIFI_CHECK_INTERVAL_SECONDS`: Wi-Fi polling interval
- `TIMER_CHECK_INTERVAL_SECONDS`: timer polling interval
- `TEST_MODE`: when `true`, uses short duration target
- `TEST_DURATION_MINUTES`: target duration used in test mode
- `LOG_TO_FILE`, `LOG_FILE_PATH`, `LOG_LEVEL`: logging behavior
- `DATA_DIR`, `ARCHIVE_DIR`: storage locations

## API Endpoints

- `GET /health`: service health metadata
- `GET /api/status`: live connection/session/timer snapshot
- `GET /api/today`: today’s sessions and totals
- `GET /api/weekly?week=YYYY-Www`: weekly day-by-day aggregation
- `GET /api/monthly?month=YYYY-MM`: monthly week-by-week aggregation

## Data Storage

Session data is stored as JSON Lines under `data/` with file names:

```text
sessions_DD-MM-YYYY.log
```

Example entry:

```json
{"date":"13-02-2026","ssid":"OfficeWifi","start_time":"09:42:10","end_time":"13:48:55","duration_minutes":246,"completed_4h":true}
```

## Testing

Run all tests:

```bash
source venv/bin/activate
pytest tests/ -v
```

Run only monthly aggregation tests:

```bash
pytest tests/test_phase_5_2.py -v
```

## Operational Notes

- The app is local-first and does not require external services.
- Backend tracking continues even when the dashboard tab is closed.
- Frontend timer display is a view layer; authoritative state remains in backend APIs.

## Documentation

- Requirements: `docs/requirements.md`
- Phase plan and status: `docs/action-plan.md`
- Development context and implementation log: `docs/dev-context.md`
