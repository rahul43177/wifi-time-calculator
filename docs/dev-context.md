# Office Wi-Fi 4-Hour Tracker — Development Context

**Purpose:** This file captures the complete development context, working style, conventions, and progress so that any AI coding agent can pick up where we left off.

**How to use:** Paste these three files to any AI coding session:
1. `@docs/requirements.md` — Source of truth for what we're building
2. `@docs/action-plan.md` — Phase-by-phase task breakdown with completion status
3. `@docs/dev-context.md` — This file (working style, conventions, progress, file inventory)

---

## 1. Project Summary

A **fully automatic local application** that:
- Detects when laptop connects to **office Wi-Fi**
- Starts a **4-hour work timer**
- Shows **live remaining time** via local web UI
- Sends **alert when 4 hours complete**
- Stores **daily proof logs** locally for HR reference
- Uses **NO database** — only local JSON Lines files
- Runs **automatically in background** on macOS

**Target:** Single user, personal macOS laptop. No Windows support needed.

---

## 2. Development Style & Conventions

### 2.1 Phase-by-Phase Development

We follow a strict **incremental phase-by-phase** approach:

1. **Read the phase requirements** from `action-plan.md`
2. **Implement ONE sub-task at a time** (e.g., Task 2.1, not all of Phase 2)
3. **Write tests immediately** after implementing each sub-task
4. **Run the FULL test suite** after every change (`pytest tests/ -v`)
5. **Ensure 0 failures and 0 warnings** before moving to the next task
6. **Update `action-plan.md`** with completion status, checkboxes, and implementation notes
7. **Never skip testing** — every phase must have its own test file

### 2.2 Test File Naming

Each sub-task gets its own test file:
```
tests/test_phase_1_1.py  → Phase 1, Task 1.1
tests/test_phase_1_2.py  → Phase 1, Task 1.2
tests/test_phase_2_1.py  → Phase 2, Task 2.1
```

### 2.3 Test Writing Rules

- Use `pytest` + `pytest-asyncio` + `httpx` for testing
- Mock external dependencies (subprocess calls, settings, file paths)
- Use `tempfile.TemporaryDirectory()` for file I/O tests
- Use `unittest.mock.patch` to isolate units
- Test happy path, error cases, edge cases, and concurrency where relevant
- All tests must pass in isolation AND together (`pytest tests/ -v`)

### 2.4 Code Quality Rules

- **No over-engineering** — only build what the current task requires
- **No database** — JSON Lines files only
- **No unnecessary abstractions** — keep it simple
- **Proper error handling** — graceful failures, never crash
- **Thread-safe file writes** — use `threading.Lock`
- **Async background tasks** — use `asyncio.create_task()`, cancel on shutdown
- **Logging everywhere** — use `logging.getLogger(__name__)`
- **Type hints** on all function signatures
- **Docstrings** on all public functions
- Use `pydantic-settings` with `ConfigDict` (NOT deprecated `class Config`)

### 2.5 Date Format Convention

**DD-MM-YYYY** (Indian standard) — explicitly chosen for all file naming and date display.
```
sessions_12-02-2026.log   (correct)
sessions_2026-02-12.log   (wrong — requirements.md has this but we override it)
```

### 2.6 Port

Server runs on **port 8787** (not 8000, to avoid conflict with developer's work projects).

### 2.7 macOS Only

No Windows support. Removed from Phase 1 early on. Wi-Fi detection uses:
1. **Primary:** `networksetup -getairportnetwork en0` (fast, ~0.1s)
2. **Fallback:** `system_profiler SPAirPortDataType` (slower ~1-2s, more reliable)

The `airport -I` command is **deprecated** on modern macOS and doesn't work.

---

## 3. Implementation Progress

### Completed

| Phase | Task | Description | Tests | Status |
|-------|------|-------------|-------|--------|
| 0 | 0.1 | Environment setup (Python 3.12.1, venv) | — | DONE |
| 0 | 0.2 | Project structure creation | — | DONE |
| 0 | 0.3 | Dependencies installation | — | DONE |
| 0 | 0.4 | Configuration setup (.env, config.py) | — | DONE |
| 1 | 1.1 | SSID detection for macOS | 11 tests | DONE |
| 1 | 1.2 | Background Wi-Fi polling loop | 5 tests | DONE |
| 1 | 1.3 | Integrate with FastAPI lifespan | 3 tests | DONE |
| 1 | 1.4 | Logging configuration | 10 tests | DONE |
| 2 | 2.1 | File storage module (JSON Lines) | 13 tests | DONE |
| 2 | 2.2 | Session state machine (IDLE/IN_OFFICE_SESSION/COMPLETED) | 12 tests | DONE |
| 2 | 2.3 | Integrate session manager with Wi-Fi detector | 7 tests | DONE |
| 2 | 2.4 | File rotation logic (>5MB → archive) | 8 tests | DONE |
| 2 | 2.5 | Session recovery on restart | 13 tests | DONE |
| 2 | 2.6 | Data validation with Pydantic models | 6 tests | DONE |
| 3 | 3.1 | Timer calculation logic (elapsed/remaining/buffer/format/completion) | 14 tests | DONE |
| 3 | 3.2 | Background timer loop (polling/logging/completion detection) | 9 tests | DONE |
| 3 | 3.3 | Notification system (macOS osascript integration) | 27 tests | DONE |
| 3 | 3.4 | Completion flag persistence in session logs | 8 tests | DONE |
| 3 | 3.5 | Timer integration with FastAPI lifespan | 7 tests | DONE |
| 3 | 3.6 | Testing mode (short duration target override) | 7 tests | DONE |
| 4 | 4.1 | Dashboard status/today API endpoints | 10 tests | DONE |
| 4 | 4.2 | Jinja2 dashboard template scaffold | 6 tests | DONE |
| 4 | 4.3 | CSS styling (external stylesheet + static mount) | 10 tests | DONE |
| 4 | 4.4 | Live timer JavaScript + backend sync loop | 9 tests | DONE |

**Total: 195 tests, all passing, 0 warnings**

### Next Up

| Phase | Task | Description | Status |
|-------|------|-------------|--------|
| 4 | 4.5 | Browser notifications | IN PROGRESS |
| 5 | 5.1-5.4 | Analytics & Charts (weekly/monthly + Chart.js) | NOT STARTED |
| 6 | 6.1-6.5 | Auto-start on boot (launchd) | NOT STARTED |

---

## 4. File Inventory

### Implemented Files (production code)

```
app/
├── __init__.py          — Package init
├── config.py            — Settings via pydantic-settings (ConfigDict)
├── wifi_detector.py     — SSID detection + polling + session transition routing
├── main.py              — FastAPI app, lifespan, APIs, Jinja dashboard route
├── file_store.py        — JSON Lines storage + 5MB rotation + archive support
├── session_manager.py   — Session state machine + persistence hooks
├── timer_engine.py      — Timer helpers + background polling loop for active sessions
└── notifier.py          — macOS notification system (osascript integration)

templates/
└── index.html           — Dashboard shell template with status/timer/table placeholders

static/
├── style.css            — Dashboard stylesheet (externalized in Task 4.3)
└── app.js               — Live timer updates + backend sync loop (Task 4.4)
```

### Test Files

```
tests/
├── __init__.py
├── test_phase_1_1.py    — 11 tests: SSID detection (networksetup, system_profiler, fallback)
├── test_phase_1_2.py    — 5 tests: Polling loop (change detection, callback, error survival)
├── test_phase_1_3.py    — 3 tests: FastAPI lifespan (health, root, task lifecycle)
├── test_phase_1_4.py    — 10 tests: Logging (console, file, levels, duplicates, directory)
├── test_phase_2_1.py    — 13 tests: File storage (naming, append, read, unicode, concurrency)
├── test_phase_2_2.py    — 12 tests: Session state machine transitions + edge cases
├── test_phase_2_3.py    — 7 tests: Wi-Fi/session integration + persistence flow + exception resilience
├── test_phase_2_4.py    — 8 tests: File rotation + archive integrity + collision/error handling
├── test_phase_2_5.py    — 13 tests: Session recovery (resume/close/edge cases/persist warning/lifespan/fresh session)
├── test_phase_2_6.py    — 6 tests: Session data validation (persist/reject/error clarity/edge cases)
├── test_phase_3_1.py    — 14 tests: Timer calculations + buffer + formatting + timezone + invalid states
├── test_phase_3_2.py    — 9 tests: Background timer loop behavior + edge-case resilience
├── test_phase_3_3.py    — 27 tests: Notification system (platform gating, escaping, failures)
├── test_phase_3_4.py    — 8 tests: Completion flag persistence (file update + timer-loop integration)
├── test_phase_3_5.py    — 7 tests: Timer integration with FastAPI (lifespan, concurrency, shutdown)
├── test_phase_3_6.py    — 7 tests: Testing mode target override (toggle + integration checks)
├── test_phase_4_1.py    — 10 tests: Dashboard API status/today schema + edge-case handling
├── test_phase_4_2.py    — 6 tests: Dashboard template rendering + placeholders/context wiring + default hidden completion banner
├── test_phase_4_3.py    — 10 tests: CSS extraction/static serving/tokens/responsive/utility validation
└── test_phase_4_4.py    — 9 tests: app.js polling/tick/completion/table-refresh/failure-fallback hooks
```

### Configuration & Docs

```
.env.example             — Template with all config keys
.env                     — Actual config (gitignored)
.gitignore               — Standard Python + data/logs exclusions
requirements.txt         — Dependencies (fastapi, uvicorn, pydantic-settings, pytest, etc.)
docs/
├── requirements.md      — Single source of truth for what to build
├── action-plan.md       — Phase-by-phase tasks with completion tracking
└── dev-context.md       — This file
```

### Directories

```
data/                    — Session log files (gitignored)
data/archive/            — Rotated files (future)
templates/               — HTML templates (includes dashboard `index.html`)
static/                  — CSS, JS (Phase 4)
logs/                    — Application logs (gitignored)
venv/                    — Python virtual environment
```

---

## 5. Key Implementation Details

### 5.1 config.py — Settings

```python
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    office_wifi_name: str = "YourOfficeWiFiName"
    server_host: str = "127.0.0.1"
    server_port: int = 8787
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file_path: str = "logs/app.log"
    work_duration_hours: int = 4
    buffer_minutes: int = 10
    wifi_check_interval_seconds: int = 30
    timer_check_interval_seconds: int = 60
    test_mode: bool = False
    test_duration_minutes: int = 2
    data_dir: str = "data"
    archive_dir: str = "data/archive"

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False,
    )

settings = Settings()
```

### 5.2 wifi_detector.py — Key Functions

- `get_current_ssid() -> Optional[str]` — Two-method fallback (networksetup → system_profiler)
- `get_session_manager() -> SessionManager` — Shared lazy-initialized session manager for integration
- `process_ssid_change(old_ssid, new_ssid)` — Maps SSID transitions to `start_session()` / `end_session()`
- `wifi_polling_loop(on_change=None)` — Async infinite loop; on SSID change, updates session state and triggers optional callback

### 5.3 main.py — App Structure

- `setup_logging()` — Console + optional RotatingFileHandler, guarded by `_logging_configured` flag
- `lifespan(app)` — Creates `wifi_polling_loop` as asyncio task, cancels on shutdown via `asyncio.gather(..., return_exceptions=True)`
- `_background_tasks: list[asyncio.Task]` — Holds references for graceful shutdown
- Endpoints:
  - `GET /` (Jinja2 dashboard template)
  - `GET /health` (JSON status)
  - `GET /api/status` (live session/timer status for dashboard)
  - `GET /api/today` (today's sessions + total minutes/display)

### 5.4 file_store.py — Storage Module

- `get_log_path(date=None) -> Path` — Returns `data/sessions_DD-MM-YYYY.log`
- `append_session(session_dict) -> bool` — Thread-safe append with pre-write 5MB rotation
- `read_sessions(date=None) -> list[dict]` — Reads base/part logs from data + archive, skips corrupted lines
- `update_session(...) -> bool` — Thread-safe in-place update of the latest matching active session line
- All file operations use `encoding="utf-8"` and `ensure_ascii=False` for unicode support

### 5.5 session_manager.py — Current State

Implements Task 2.2 state machine + Task 2.5 recovery + Task 2.6 validation:
- `SessionState` enum: IDLE, IN_OFFICE_SESSION, COMPLETED
- `SessionLog` Pydantic model: validated persistence schema
- `Session` model: backward-compatible in-memory snapshot model
- `SessionManager` class with:
  - `start_session(ssid)` for IDLE → IN_OFFICE_SESSION
  - `mark_session_completed()` for IN_OFFICE_SESSION → COMPLETED
  - `end_session()` for IN_OFFICE_SESSION/COMPLETED → IDLE
  - `recover_session(current_ssid)` — reads today's log, resumes or closes incomplete sessions
  - `_persist_state(session)` — validates using `SessionLog` before persisting
  - persistence hooks via `file_store.append_session`
  - Injectable `read_sessions_func` for deterministic testing of recovery

### 5.6 timer_engine.py — Current State

Implements Task 3.1 + Task 3.2 + Task 3.4 + Task 3.5 + Task 3.6 timer logic:
- `get_elapsed_time(start_time, now=None)` — elapsed duration with timezone-awareness and safe clamping
- `get_remaining_time(start_time, target_hours, buffer_minutes, now=None)` — target minus elapsed, can be negative
- `format_time_display(td)` — HH:MM:SS output including negative durations
- `is_completed(start_time, target_hours, buffer_minutes, now=None)` — completion check at target boundary
- `timer_polling_loop()` — async periodic timer checks for active sessions with remaining/overtime logs and completion detection
- Completion detection now persists `completed_4h=True` immediately via `file_store.update_session(...)`
- Timer loop now also runs via FastAPI lifespan startup/shutdown integration (`app.main`)
- Test mode support: when `TEST_MODE=true`, effective target is `TEST_DURATION_MINUTES`

### 5.7 Frontend Dashboard (Phase 4.4)

- `templates/index.html` now loads:
  - `/static/style.css`
  - `/static/app.js` (deferred)
- `static/app.js` behavior:
  - 30-second backend sync via `/api/status` and `/api/today`
  - 1-second client tick between syncs for timer/progress updates
  - Completion/overtime mode switches timer display to total elapsed
  - Rebuilds today's sessions table from latest backend payload
  - Handles fetch failures gracefully with "last known data" indicator

---

## 6. Bugs Fixed & Lessons Learned

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| `airport -I` returns no data | Deprecated on modern macOS | Use `networksetup` + `system_profiler` fallback |
| pytest sees own LogCaptureHandler | `if root_logger.handlers: return` caught pytest handler | Use `_logging_configured` flag instead |
| `isinstance(h, FileHandler)` catches pytest handler | pytest uses `_FileHandler(/dev/null)` internally | Check `type(h) is RotatingFileHandler` (exact match) |
| `class Config` deprecation warning | Pydantic v2 deprecated inner `Config` class | Use `model_config = ConfigDict(...)` |
| urllib blocks async event loop | `urllib.request.urlopen` is synchronous | Use `asyncio.to_thread()` in tests |
| ASGITransport doesn't trigger lifespan mock | Transport doesn't call lifespan the same way | Call `lifespan(app)` directly in test |

---

## 7. Tech Stack & Versions

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12.1 | Runtime |
| FastAPI | 0.109.0 | Web server |
| Uvicorn | 0.27.0 | ASGI server |
| Pydantic | 2.5.0 | Data validation |
| pydantic-settings | 2.1.0 | .env config loading |
| Jinja2 | 3.1.3 | HTML templates (Phase 4) |
| APScheduler | 3.10.4 | Background scheduling |
| pytest | 9.0.2 | Testing framework |
| pytest-asyncio | 1.3.0 | Async test support |
| httpx | 0.27.0+ | HTTP client for testing |

---

## 8. Running the Project

```bash
# Activate virtual environment
cd /Users/rahulmishra/Desktop/Personal/wifi-tracking
source venv/bin/activate

# Run the server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8787 --reload

# Run all tests
pytest tests/ -v

# Run tests for a specific phase
pytest tests/test_phase_2_1.py -v

# Check test count and warnings
pytest tests/ -v --tb=short
```

---

## 9. Instructions for AI Coding Agent

When continuing development:

1. **Read this file + requirements.md + action-plan.md** first
2. **Check current progress** in the progress table above (Section 3)
3. **Pick the next incomplete task** from action-plan.md
4. **Implement ONE task at a time** — do not batch multiple tasks
5. **Write tests in a new file** named `tests/test_phase_X_Y.py`
6. **Run the full test suite** after implementation: `pytest tests/ -v`
7. **Ensure 0 failures, 0 warnings** before moving on
8. **Update action-plan.md** — mark task as DONE, add implementation notes
9. **Update this file** — add the task to the progress table, update file inventory
10. **Do NOT modify existing passing tests** unless there's a regression to fix

### Quality Bar
- Every function must have type hints and a docstring
- Every error path must be handled (no unhandled exceptions)
- Every test file must be independently runnable
- Full suite must stay green at all times
- No pydantic deprecation warnings
- Thread-safe file operations
- Graceful async task cancellation

---
## STRICT EXECUTION CONTRACT (MANDATORY)

Any AI agent continuing this project MUST:

1. Work on ONLY one task at a time.
2. Never jump phases.
3. Never refactor unrelated code.
4. Always write tests for the current task.
5. Run the FULL test suite after every change.
6. Ensure:
   - 0 failures
   - 0 warnings
   - 0 regressions
7. Update documentation after task completion.

If any rule above is violated,
the implementation is considered INVALID.
