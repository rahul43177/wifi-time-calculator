# Office Wi-Fi 4-Hour Tracker — Action Plan

**Project Start Date:** February 12, 2026  
**Estimated MVP Completion:** 2-3 days of focused development  
**Target User:** Personal productivity + HR audit trail

---

## Table of Contents

1. [Pre-Development Setup](#pre-development-setup)
2. [Phase 1: Wi-Fi Detection System](#phase-1-wifi-detection-system)
3. [Phase 2: File-Based Session Storage](#phase-2-file-based-session-storage)
4. [Phase 3: Timer Engine & Notifications](#phase-3-timer-engine--notifications)
5. [Phase 4: Live Dashboard UI](#phase-4-live-dashboard-ui)
6. [Phase 5: Analytics & Charts](#phase-5-analytics--charts)
7. [Phase 6: Auto-Start on Boot](#phase-6-auto-start-on-boot)
8. [Testing & Validation](#testing--validation)
9. [Timeline & Milestones](#timeline--milestones)
10. [Troubleshooting Guide](#troubleshooting-guide)

---

## 🚀 Pre-Development Setup

**Estimated Time:** 15-30 minutes

### Task 0.1: Environment Preparation ✅ DONE
**Description:** Set up development environment and project structure
**Dependencies:** None
**Acceptance Criteria:**
- [x] Python 3.11+ installed and verified (Python 3.12.1)
- [x] Virtual environment created (venv/)


**Steps:**
```bash
cd /Users/rahulmishra/Desktop/Personal/wifi-tracking
python3 --version  # Verify 3.11+
python3 -m venv venv
source venv/bin/activate
```

---

### Task 0.2: Project Structure Creation ✅ DONE
**Description:** Create all necessary folders and files
**Dependencies:** Task 0.1
**Acceptance Criteria:**
- [x] All folders exist as per spec
- [x] Basic files created with placeholder content

**Steps:**
```bash
mkdir -p app data data/archive templates static docs
touch app/__init__.py app/main.py app/wifi_detector.py
touch app/session_manager.py app/timer_engine.py 
touch app/notifier.py app/file_store.py app/config.py
touch requirements.txt README.md .gitignore
```

**File Structure:**
```
office-wifi-tracker/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── wifi_detector.py     # SSID detection logic
│   ├── session_manager.py   # State machine for sessions
│   ├── timer_engine.py      # 4-hour countdown logic
│   ├── notifier.py          # Alert system
│   ├── file_store.py        # JSON Lines file operations
│   └── config.py            # Configuration settings
├── data/                    # Session log files (gitignored)
│   └── archive/             # Old rotated files
├── templates/               # HTML templates
│   └── index.html
├── static/                  # CSS, JS, images
│   ├── style.css
│   └── app.js
├── docs/                    # Documentation
│   ├── requirements.md
│   └── action-plan.md
├── requirements.txt
├── README.md
├── .gitignore
└── .env                     # Environment variables
```

---

### Task 0.3: Dependencies Installation ✅ DONE
**Description:** Install all required Python packages
**Dependencies:** Task 0.1
**Acceptance Criteria:**
- [x] requirements.txt populated
- [x] All packages installed without errors

**requirements.txt contents:**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
apscheduler==3.10.4
jinja2==3.1.3
```

**Command:**
```bash
pip install -r requirements.txt
```

---

### Task 0.4: Configuration Setup ✅ DONE
**Description:** Create configuration file for office Wi-Fi name
**Dependencies:** Task 0.2
**Acceptance Criteria:**
- [x] .env file created with OFFICE_WIFI_NAME
- [x] config.py loads settings correctly

> **Note:** Port changed from 8000 → **8787** to avoid conflict with dev work.

**.env contents:**
```
OFFICE_WIFI_NAME=YourOfficeWiFiName
SERVER_HOST=127.0.0.1
SERVER_PORT=8787
LOG_LEVEL=INFO
WORK_DURATION_HOURS=4
BUFFER_MINUTES=10
WIFI_CHECK_INTERVAL_SECONDS=30
TIMER_CHECK_INTERVAL_SECONDS=60
```

---

## 🔍 Phase 1: Wi-Fi Detection System

**Goal:** Detect when laptop connects/disconnects from office Wi-Fi  
**Estimated Time:** 2-3 hours

---

### Task 1.1: Implement SSID Detection for macOS ✅ DONE
**Description:** Create function to get current Wi-Fi SSID using macOS system command
**Dependencies:** Task 0.2, 0.3
**Acceptance Criteria:**
- [x] Function returns current SSID or None if disconnected
- [x] Works on macOS
- [x] Handles errors gracefully

**File:** `app/wifi_detector.py`

> **Implementation Note:** The `airport -I` command is deprecated on modern macOS and returned no data.
> Implemented a **two-method fallback approach:**
> 1. **Primary:** `networksetup -getairportnetwork en0` (fast, ~0.1s)
> 2. **Fallback:** `system_profiler SPAirPortDataType` (slower ~1-2s, more reliable)
>
> Tested successfully — detected SSID `iPhone` (hotspot) via the fallback method.

**Test Command:**
```python
from app.wifi_detector import get_current_ssid
print(get_current_ssid())  # Returned: 'iPhone'
```

---

### Task 1.2: Create Background Wi-Fi Polling Loop ✅ DONE
**Description:** Async loop that checks Wi-Fi every 30 seconds
**Dependencies:** Task 1.1
**Acceptance Criteria:**
- [x] Loop runs in background
- [x] Checks SSID every 30 seconds
- [x] Logs SSID changes to console
- [x] Doesn't block main thread

**File:** `app/wifi_detector.py`

> **Implementation Note:** Added `wifi_polling_loop(on_change)` using asyncio.
> Includes an `on_change` callback hook for session_manager integration (Phase 2).
> Tested: starts cleanly, polls correctly, cancels without errors.

---

### Task 1.3: Integrate with FastAPI Lifespan ✅ DONE
**Description:** Start Wi-Fi polling when server starts
**Dependencies:** Task 1.2, Task 0.2 (main.py)
**Acceptance Criteria:**
- [x] Polling starts automatically with server
- [x] Stops gracefully on shutdown
- [x] No zombie processes

**File:** `app/main.py`

> **Implementation Note:** Lifespan creates `wifi_polling_loop` as an asyncio task on startup.
> On shutdown, all background tasks are cancelled via `asyncio.gather(..., return_exceptions=True)`.
> Tested with live server — starts polling, serves /health, shuts down cleanly.
>
> **Tests added:** `tests/test_phase_1_1.py` (11 tests), `tests/test_phase_1_2.py` (5 tests),
> `tests/test_phase_1_3.py` (3 tests) — **all 19 tests passing**.

---

### Task 1.4: Add Logging Configuration ✅ DONE
**Description:** Set up proper logging for debugging
**Dependencies:** Task 0.3
**Acceptance Criteria:**
- [x] Logs show timestamps
- [x] Different log levels work
- [x] Logs go to console and optionally to file

**Files:** `app/main.py`, `app/config.py`, `.env`, `.env.example`

> **Implementation Note:** Created `setup_logging()` function with:
> - Console handler (always on) with timestamp format
> - Optional `RotatingFileHandler` (5MB rotation, 3 backups) enabled via `LOG_TO_FILE=true`
> - Duplicate-handler guard via `_logging_configured` flag
> - Added `LOG_TO_FILE` and `LOG_FILE_PATH` to config/env files
>
> **Tests:** `tests/test_phase_1_4.py` (10 tests) — all passing.

---

### ✅ Phase 1 Definition of Done

- [x] Can detect current SSID on macOS
- [x] Background loop checks every 30 seconds
- [x] SSID changes logged to console
- [x] No crashes or errors during Wi-Fi changes
- [x] Code is modular and documented

> **Phase 1 complete — 29 tests across 4 test files, all passing.**

---

## 💾 Phase 2: File-Based Session Storage

**Goal:** Store session data in local JSON Lines files without database  
**Estimated Time:** 3-4 hours

---

### Task 2.1: Design File Storage Module ✅ DONE
**Description:** Create file_store.py with core file operations
**Dependencies:** Phase 1 complete
**Acceptance Criteria:**
- [x] Can create daily log files with naming: `sessions_DD-MM-YYYY.log`
- [x] Can append JSON lines to files
- [x] Can read today's sessions
- [x] Thread-safe file operations

**File:** `app/file_store.py`

> **Implementation Note:** Three public functions:
> - `get_log_path(date=None)` → Returns path using DD-MM-YYYY format
> - `append_session(session_dict)` → Thread-safe append via `threading.Lock`
> - `read_sessions(date=None)` → Reads sessions, skips corrupted lines gracefully
>
> Date format changed from YYYY-MM-DD to **DD-MM-YYYY** (Indian standard).
>
> **Tests:** `tests/test_phase_2_1.py` (13 tests) — DD-MM-YYYY naming, append, read,
> unicode, missing/empty/corrupted files, concurrent writes — all passing.

---

### Task 2.2: Implement Session State Machine ✅ DONE
**Description:** Create session manager with IDLE/IN_OFFICE_SESSION/COMPLETED states  
**Dependencies:** Task 2.1  
**Acceptance Criteria:**
- [x] Tracks current session state
- [x] Stores active session in memory
- [x] Transitions between states correctly
- [x] Persists state to file on changes

**File:** `app/session_manager.py`

**Key Components:**
- `SessionState` Enum (IDLE, IN_OFFICE_SESSION, COMPLETED)
- `Session` dataclass with start_time, end_time, ssid, etc.
- `SessionManager` class with state machine logic

> **Implementation Note:** Implemented deterministic, thread-safe `SessionManager` with:
> - Explicit transitions: `IDLE -> IN_OFFICE_SESSION -> COMPLETED -> IDLE`
> - Guarded invalid transitions (double start, end/complete without active session)
> - File persistence through `file_store.append_session` on every state change
> - Injectable `now_provider` and `persist_func` for deterministic testing
>
> **Tests:** `tests/test_phase_2_2.py` (12 tests) — core transitions, persistence calls,
> COMPLETED→IDLE path, persistence failure behavior, and duration edge cases — all passing.

**State Transitions:**
```
IDLE + office_wifi_detected → IN_OFFICE_SESSION (save start)
IN_OFFICE_SESSION + wifi_disconnected → IDLE (save end)
IN_OFFICE_SESSION + 4h_complete → COMPLETED (update file)
```

---

### Task 2.3: Integrate Session Manager with Wi-Fi Detector ✅ DONE
**Description:** Connect Wi-Fi change events to session manager  
**Dependencies:** Task 2.2, Phase 1  
**Acceptance Criteria:**
- [x] Wi-Fi connect to office → starts session
- [x] Wi-Fi disconnect from office → ends session
- [x] Sessions written to daily log file
- [x] Works across multiple connect/disconnect cycles

**Files:** `app/wifi_detector.py`, `app/session_manager.py`

**Key Integration Points:**
- Pass SSID changes to session manager
- Check if SSID matches OFFICE_WIFI_NAME
- Call session_manager.start_session() or end_session()

> **Implementation Note:** Added SSID transition routing in `wifi_detector`:
> - `process_ssid_change(old_ssid, new_ssid)` handles office connect/disconnect transitions
> - `get_session_manager()` provides a shared lazy-initialized `SessionManager`
> - `wifi_polling_loop()` now invokes `process_ssid_change` on each SSID change before optional callback
>
> **Tests:** `tests/test_phase_2_3.py` (7 tests) — office connect/disconnect behavior,
> non-office no-op behavior, multi-cycle transitions, polling-loop integration hook, and
> end-to-end persistence to daily log files, plus exception-resilience handling — all passing.

**Test:** Connect/disconnect Wi-Fi and verify sessions appear in `data/sessions_2026-02-12.log`

---

### Task 2.4: Implement File Rotation Logic ✅ DONE
**Description:** Rotate files when they exceed 5MB  
**Dependencies:** Task 2.1  
**Acceptance Criteria:**
- [x] Checks file size before writing
- [x] Moves file to archive/ if > 5MB
- [x] Creates new part file (sessions_DD-MM-YYYY_part2.log)
- [x] Maintains data integrity

**File:** `app/file_store.py`

**Key Implementation Points:**
- Check file size: `os.path.getsize()`
- Move to archive: `shutil.move()`
- Update filename with part number
- Handle edge cases (archive folder doesn't exist, etc.)

> **Implementation Note:** Added rotation in `append_session()` with:
> - pre-write size check against 5MB threshold
> - archive move for oversized active log file
> - automatic next-part file naming (`_part2`, `_part3`, ...)
> - fallback-safe archive path handling and collision-safe archive filenames
> - read compatibility across base/part files in both `data/` and `archive/`
>
> **Tests:** `tests/test_phase_2_4.py` (8 tests) — rotation trigger, archive move,
> part-file creation, multi-rotation behavior, strict `>` threshold behavior,
> data integrity across rotated files, archive collision filename handling,
> and move/error failure handling — all passing.

---

### Task 2.5: Add Session Recovery on Restart ✅ DONE
**Description:** Restore active session if app restarts during office hours
**Dependencies:** Task 2.3
**Acceptance Criteria:**
- [x] On startup, checks if currently connected to office Wi-Fi
- [x] Reads today's log for incomplete session
- [x] Resumes session if still in office
- [x] Creates new session if previous was completed

**Files:** `app/session_manager.py`, `app/main.py`

**Key Implementation Points:**
- On startup: check current SSID
- Read today's log file
- Look for session without end_time
- If found and still connected: resume
- If found but disconnected: close previous session

> **Implementation Note:** Added `recover_session(current_ssid)` method to `SessionManager`:
> - Reads today's sessions via injectable `read_sessions_func` (testable)
> - Scans backwards for last entry without `end_time` (incomplete session)
> - If still connected to same office Wi-Fi → restores in-memory state (no extra persist)
> - If disconnected or different SSID → persists a close record and stays IDLE
> - Handles malformed entries and reader exceptions gracefully
> - Thread-safe via existing `_lock`
> - Integrated into `main.py` lifespan — runs before polling loop starts
> - Lifespan also starts a fresh session if already on office Wi-Fi but nothing to recover
>
> **Tests:** `tests/test_phase_2_5.py` (13 tests) — resume connected, close stale (different SSID),
> close stale (no Wi-Fi), no sessions, all completed, already active, multiple incompletes,
> malformed entry, read exception, persist failure warning, lifespan integration,
> new session on office Wi-Fi, no session when not on office Wi-Fi — all passing.

---

### Task 2.6: Add Data Validation ✅ DONE
**Description:** Validate session data before saving  
**Dependencies:** Task 2.1  
**Acceptance Criteria:**
- [x] Uses Pydantic models for validation
- [x] Rejects invalid data
- [x] Clear error messages

**File:** `app/session_manager.py`

**Pydantic Model:**
```python
class SessionLog(BaseModel):
    date: str
    ssid: str
    start_time: str
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    completed_4h: bool = False
```

> **Implementation Note:** Added `SessionLog` as a validated persistence model and
> enforced validation in `SessionManager._persist_state()` before every save.
> Added field validators for:
> - `date` format (`DD-MM-YYYY`)
> - `start_time` / `end_time` format (`HH:MM:SS`)
> - non-empty `ssid`
> - non-negative `duration_minutes`
>
> Invalid payloads are rejected before file writes, with concise field-level
> error messages logged via `Session validation failed: ...`.
>
> **Tests:** Added dedicated validation coverage in `tests/test_phase_2_6.py`
> (6 tests) for valid persistence, rejection of malformed date/time/SSID/duration,
> corrupted in-memory state handling, and malformed recovery-entry handling — all passing.

---

### ✅ Phase 2 Definition of Done

- [x] Sessions saved to daily log files in JSON Lines format
- [x] New file created each day automatically
- [x] Connect/disconnect cycles logged correctly
- [x] Files rotate when > 5MB
- [x] Session resumes after app restart
- [x] Can read today's sessions programmatically
- [x] No data loss during crashes

---

## ⏱️ Phase 3: Timer Engine & Notifications

**Goal:** Track 4-hour completion and send alerts  
**Estimated Time:** 2-3 hours

---

### Task 3.1: Implement Timer Calculation Logic ✅ DONE
**Description:** Calculate elapsed and remaining time for active session
**Dependencies:** Phase 2 complete
**Acceptance Criteria:**
- [x] Calculates elapsed time: now - start_time
- [x] Calculates remaining time: (4h + buffer) - elapsed
- [x] Includes configurable `BUFFER_MINUTES` (default 10) in target
- [x] Returns formatted strings (HH:MM:SS)
- [x] Handles timezone correctly
- [x] Elapsed time keeps increasing after target is reached (no cap)

**File:** `app/timer_engine.py`, `app/config.py`

**Key Functions:**
- `get_elapsed_time(start_time: datetime) → timedelta`
- `get_remaining_time(start_time: datetime, target_hours: int, buffer_minutes: int) → timedelta`
- `format_time_display(td: timedelta) → str`
- `is_completed(start_time: datetime, target_hours: int, buffer_minutes: int) → bool`

**Config Addition:**
```
BUFFER_MINUTES=10  # Added to .env / config.py
```

**Important:** `remaining` can go negative. Negative remaining means overtime — the timer keeps tracking total elapsed time even after completion for weekly reporting purposes.

> **Implementation Note:** Implemented deterministic timer utilities in `app/timer_engine.py`:
> - `get_elapsed_time(...)` with timezone-aware handling and future-time clamping
> - `get_remaining_time(...)` using target + buffer and allowing negative overtime values
> - `format_time_display(...)` for positive/negative HH:MM:SS formatting
> - `is_completed(...)` based on target + buffer completion
> - Safe handling for invalid states (invalid type inputs, timezone mismatch, negative config values)
>
> Added `buffer_minutes: int = 10` to `app/config.py` for configurable buffer support.
>
> **Tests:** `tests/test_phase_3_1.py` (14 tests) — elapsed/remaining calculations,
> timezone-aware behavior, overtime handling, formatting, invalid state handling,
> and completion boundary behavior — all passing.

---

### Task 3.2: Create Background Timer Loop ✅ DONE
**Description:** Check timer every 60 seconds
**Dependencies:** Task 3.1
**Acceptance Criteria:**
- [x] Runs every 60 seconds
- [x] Only checks when session is active
- [x] Logs remaining time (or overtime amount if past target)
- [x] Detects completion (4h + buffer reached)
- [x] Continues running after completion to track total office time

**File:** `app/timer_engine.py`

**Key Implementation Points:**
- Use asyncio for background task
- Get active session from session manager
- Calculate remaining time including buffer
- Log every minute for debugging
- Trigger notification when completed
- Keep loop alive after completion — elapsed time keeps growing for reporting

> **Implementation Note:** Added `timer_polling_loop()` to `app/timer_engine.py`:
> - Async background loop with configurable interval (`TIMER_CHECK_INTERVAL_SECONDS`)
> - Fetches shared `SessionManager` and skips checks when no active session exists
> - Computes elapsed/remaining with existing Task 3.1 helpers
> - Logs remaining time before completion and overtime after completion
> - Detects completion and triggers notification through `send_notification(...)`
> - Prevents repeat notifications within the same active session runtime
> - Continues checking/logging after completion until session ends or task is cancelled
>
> **Tests:** `tests/test_phase_3_2.py` (9 tests) — interval behavior, active-session gating,
> remaining/overtime logging, completion notification trigger, post-completion continuity,
> malformed session handling, exception resilience, and duplicate-notification prevention — all passing.

---

### Task 3.3: Implement Notification System ✅ DONE
**Description:** Send macOS notification when 4h + buffer completed
**Dependencies:** Task 3.2
**Acceptance Criteria:**
- [x] Sends notification when (4h + buffer) completes
- [x] Only sends once per session
- [x] Message includes buffer info: "4 hours + 10 min buffer completed. You may leave."
- [x] Doesn't crash if notification fails

**File:** `app/notifier.py`

**Implementation:** macOS osascript (Notification Center)

**macOS Command:**
```bash
osascript -e 'display notification "4 hours + 10 min buffer completed. You may leave the office." with title "Office Wi-Fi Tracker"'
```

**Key Functions:**
- `send_notification(title: str, message: str) → bool`
- `can_send_notifications() → bool`

> **Implementation Note:** Replaced skeleton `app/notifier.py` with production-ready macOS notification sender:
> - `send_notification(title, message)` executes `osascript -e 'display notification ...'` via `subprocess.run` with 10s timeout
> - `can_send_notifications()` returns `True` only on macOS (Darwin)
> - `_escape_osascript_string()` escapes backslashes and double quotes for safe AppleScript embedding
> - Graceful failure handling: `subprocess.TimeoutExpired`, `FileNotFoundError`, `OSError`, and non-zero exit codes all return `False` with logged warnings
> - Non-macOS platforms are gated at entry — subprocess is never called
> - "Once per session" logic is handled by `timer_polling_loop()` (Task 3.2) via `notified_session_key`
>
> **Tests:** `tests/test_phase_3_3.py` (27 tests) — platform gating, string escaping, happy path,
> all failure modes (timeout, missing binary, OS error, non-zero exit), subprocess kwargs,
> command format, logging, and integration message format — all passing.

---

### Task 3.4: Add Completion Flag to Session ✅ DONE
**Description:** Mark session as completed in file when 4 hours reached  
**Dependencies:** Task 3.3, Phase 2  
**Acceptance Criteria:**
- [x] Updates session log with completed_4h = true
- [x] Only updates once
- [x] Persists immediately to file

**Files:** `app/timer_engine.py`, `app/file_store.py`

**Key Implementation Points:**
- Add update_session() function to file_store
- Read file, find active session line, update it
- Use file locking if needed (probably not for MVP)
- Log the update

> **Implementation Note:** Added in-place completion persistence:
> - `app/file_store.py` now includes `update_session(...)` which:
>   - acquires the module write lock
>   - locates the latest matching active session (`end_time is None`)
>   - updates the JSON line in-place
>   - persists immediately to disk
>   - avoids duplicate writes when data is already up-to-date
> - `app/timer_engine.py` `timer_polling_loop()` now:
>   - persists `completed_4h=True` as soon as completion is detected
>   - updates in-memory `active_session.completed_4h` after successful persistence
>   - avoids repeat completion updates for already-completed sessions
>
> **Tests:** `tests/test_phase_3_4.py` (8 tests) — file update happy path,
> no-match/no-op behavior, corrupted-line handling, invalid date handling,
> immediate timer-loop persistence, no repeat writes, and retry behavior on
> transient persistence failures — all passing.

---

### Task 3.5: Integrate Timer with FastAPI ✅ DONE
**Description:** Start timer loop as background task  
**Dependencies:** Task 3.2, Phase 1 Task 1.4  
**Acceptance Criteria:**
- [x] Timer starts with server
- [x] Runs alongside Wi-Fi detector
- [x] Stops gracefully on shutdown

**File:** `app/main.py`

**Key Implementation Points:**
- Import `timer_polling_loop` from `app.timer_engine`
- Start it as a background task in FastAPI lifespan
- Add to `_background_tasks` list for graceful shutdown
- Runs concurrently with Wi-Fi polling loop

> **Implementation Note:** Timer integration with FastAPI lifespan:
> - `app/main.py` now imports `timer_polling_loop` from `app.timer_engine`
> - Timer task starts on server startup alongside Wi-Fi detector
> - Both tasks added to `_background_tasks` list
> - Shutdown sequence cancels both tasks gracefully with `asyncio.gather(..., return_exceptions=True)`
> - Exception in one task does not crash the other
>
> **Tests:** `tests/test_phase_3_5.py` (7 tests) — both tasks start, run concurrently,
> stop gracefully, survive individual task exceptions, endpoints work correctly — all passing.
>
> **QA Fix:** Corrected test patch targets from `app.wifi_detector.get_current_ssid` to
> `app.main.get_current_ssid` to ensure deterministic test isolation (since `app.main`
> imports the function directly). Updated `docs/dev-context.md` to reflect completed
> `notifier.py` implementation and added missing test file entries.

---

### Task 3.6: Add Testing Mode (Short Duration)
**Description:** Allow shorter duration for testing (e.g., 2 minutes)  
**Dependencies:** Task 3.1  
**Acceptance Criteria:**
- [ ] Config option for TEST_MODE
- [ ] When enabled, uses 2-minute duration
- [ ] Easy to toggle on/off

**Files:** `app/config.py`, `.env`

**.env addition:**
```
TEST_MODE=true
TEST_DURATION_MINUTES=2
```

---

### ✅ Phase 3 Definition of Done

- [x] Timer calculates remaining time correctly (including buffer)
- [x] Notification appears when (4 hours + buffer) completes
- [ ] Only one notification per session
- [x] Session marked as completed in log file
- [x] Elapsed time continues tracking after completion (for weekly reports)
- [ ] Test mode works with 2-minute duration
- [ ] Timer survives app restart (resumes correctly)

---

## 🖥️ Phase 4: Live Dashboard UI

**Goal:** Single-page dashboard with live timer, today's sessions, and connection status
**Estimated Time:** 4-5 hours
**Tech:** HTML + Vanilla JS + Jinja2 (no React, no build tools)

---

### Task 4.1: Create API Endpoints for Status & Today's Data
**Description:** Backend endpoints that power the dashboard
**Dependencies:** Phase 3 complete
**Acceptance Criteria:**
- [ ] `GET /api/status` returns current session state + timer info
- [ ] `GET /api/today` returns today's sessions + total time
- [ ] Both return proper JSON with correct types
- [ ] Handle edge cases (no session, no data)

**File:** `app/main.py`

**API Response Examples:**

`GET /api/status`:
```json
{
  "connected": true,
  "ssid": "OfficeWifi",
  "session_active": true,
  "start_time": "09:42:10",
  "elapsed_seconds": 8130,
  "elapsed_display": "02:15:30",
  "remaining_seconds": 6270,
  "remaining_display": "01:44:30",
  "completed_4h": false,
  "progress_percent": 56.4,
  "target_display": "4h 10m"
}
```

`GET /api/today`:
```json
{
  "date": "12-02-2026",
  "sessions": [
    {
      "start_time": "09:42:10",
      "end_time": "13:48:55",
      "duration_minutes": 246,
      "completed_4h": true
    }
  ],
  "total_minutes": 246,
  "total_display": "4h 06m"
}
```

---

### Task 4.2: Create HTML Dashboard Template
**Description:** Single-page Jinja2 template with live timer, status, and session table
**Dependencies:** Task 4.1
**Acceptance Criteria:**
- [ ] Shows connection status (green connected / red disconnected)
- [ ] Large countdown timer display (HH:MM:SS)
- [ ] Progress bar (0% → 100%)
- [ ] After completion: shows "Completed! Total: HH:MM:SS" in green
- [ ] Today's sessions table (Start | End | Duration | Status)
- [ ] Today's total office time summary
- [ ] Tab/section navigation placeholders for Weekly & Monthly views

**File:** `templates/index.html`

**Layout:**
```
┌─────────────────────────────────────┐
│ Office Wi-Fi Tracker           [tabs]│
├─────────────────────────────────────┤
│ ● Connected to OfficeWifi          │
│ Started at 09:42:10                 │
├─────────────────────────────────────┤
│         01:44:30                    │
│      ████████░░░░░ 56%              │
│   Remaining (target: 4h 10m)       │
├─────────────────────────────────────┤
│ Today's Sessions                    │
│ Start    | End      | Dur  | Status │
│ 09:42:10 | —        | 2h15 | Active │
│ Total: 2h 15m                       │
└─────────────────────────────────────┘
```

---

### Task 4.3: Add CSS Styling
**Description:** Clean, modern CSS for the dashboard
**Dependencies:** Task 4.2
**Acceptance Criteria:**
- [ ] Minimalist design with clear hierarchy
- [ ] Color coding: green (connected/completed), yellow (>75%), red (disconnected)
- [ ] Large, readable timer font
- [ ] Responsive layout (works on laptop screen)

**File:** `static/style.css`

---

### Task 4.4: Implement Live Timer JavaScript
**Description:** Client-side countdown + auto-refresh from backend
**Dependencies:** Task 4.2
**Acceptance Criteria:**
- [ ] Countdown updates every 1 second (client-side calculation from start_time)
- [ ] Syncs with backend every 30 seconds via `fetch('/api/status')`
- [ ] Updates progress bar smoothly
- [ ] Refreshes session table on sync
- [ ] After completion: switches display to total elapsed (keeps counting)
- [ ] Error handling for fetch failures (shows last-known state)

**File:** `static/app.js`

---

### Task 4.5: Add Browser Notification Support
**Description:** Browser notification when 4h + buffer completes
**Dependencies:** Task 4.4
**Acceptance Criteria:**
- [ ] Requests Notification API permission on page load
- [ ] Detects completion via `/api/status` polling
- [ ] Shows browser notification once when `completed_4h` flips to true
- [ ] Works even if tab not focused

**File:** `static/app.js`

---

### ✅ Phase 4 Definition of Done

- [ ] Dashboard accessible at http://localhost:8787/
- [ ] Live countdown timer updates every second
- [ ] Progress bar reflects current progress
- [ ] After 4h + buffer: shows total elapsed time (keeps counting)
- [ ] Today's sessions displayed in table with total
- [ ] Syncs with backend every 30 seconds
- [ ] Browser notification on completion
- [ ] Clean, usable UI with no console errors

---

## 📊 Phase 5: Analytics & Charts

**Goal:** Weekly and monthly analytics views with graphical charts
**Estimated Time:** 4-5 hours
**Tech:** Chart.js (CDN), additional API endpoints

---

### Task 5.1: Weekly Data Aggregation API
**Description:** Backend endpoint that aggregates daily data into weekly view
**Dependencies:** Phase 4 complete
**Acceptance Criteria:**
- [ ] `GET /api/weekly?week=2026-W07` returns day-by-day breakdown
- [ ] Defaults to current week if no query param
- [ ] Each day: total_minutes, session_count, target_met (bool)
- [ ] Includes week totals and averages

**File:** `app/main.py` (or new `app/analytics.py` if complex)

**Response Example:**
```json
{
  "week": "2026-W07",
  "days": [
    {"date": "09-02-2026", "day": "Mon", "total_minutes": 380, "sessions": 2, "target_met": true},
    {"date": "10-02-2026", "day": "Tue", "total_minutes": 250, "sessions": 1, "target_met": true},
    {"date": "11-02-2026", "day": "Wed", "total_minutes": 0, "sessions": 0, "target_met": false}
  ],
  "total_minutes": 630,
  "avg_minutes_per_day": 210,
  "days_target_met": 2
}
```

---

### Task 5.2: Monthly Data Aggregation API
**Description:** Backend endpoint that aggregates weekly data into monthly view
**Dependencies:** Task 5.1
**Acceptance Criteria:**
- [ ] `GET /api/monthly?month=2026-02` returns week-by-week breakdown
- [ ] Defaults to current month if no query param
- [ ] Each week: total_minutes, days_present, avg_daily_minutes
- [ ] Includes month totals

**File:** `app/main.py` (or `app/analytics.py`)

---

### Task 5.3: Weekly Analytics UI View
**Description:** Weekly tab/section with day-by-day table and bar chart
**Dependencies:** Task 5.1, Phase 4 UI
**Acceptance Criteria:**
- [ ] Tab navigation: "Today" | "Weekly" | "Monthly"
- [ ] Day-by-day table: Date | Day | Hours | Sessions | Target Met
- [ ] Bar chart (Chart.js): days on X-axis, hours on Y-axis
- [ ] 4h target line drawn as horizontal reference
- [ ] Green bars for days >= target, red for < target
- [ ] Week selector (prev/next arrows)

**Files:** `templates/index.html`, `static/app.js`

---

### Task 5.4: Monthly Analytics UI View
**Description:** Monthly tab/section with week-by-week table and chart
**Dependencies:** Task 5.2, Task 5.3
**Acceptance Criteria:**
- [ ] Week-by-week table: Week | Total Hours | Days Present | Avg Daily
- [ ] Bar/line chart showing weekly totals across the month
- [ ] Month selector (prev/next arrows)
- [ ] Monthly summary stats (total hours, days present, overall average)

**Files:** `templates/index.html`, `static/app.js`

---

### ✅ Phase 5 Definition of Done

- [ ] Weekly view shows day-by-day breakdown with bar chart
- [ ] Monthly view shows week-by-week breakdown with chart
- [ ] Charts render via Chart.js (no build tools)
- [ ] Navigation between Today / Weekly / Monthly works
- [ ] Week and month selectors allow browsing history
- [ ] All data comes from JSON Lines files (no database)

---

## 🚀 Phase 6: Auto-Start on Boot

**Goal:** App starts automatically when Mac boots up
**Estimated Time:** 1-2 hours

---

### Task 6.1: Create launchd Plist File
**Description:** macOS launchd configuration for auto-start
**Dependencies:** Phases 1-5 complete
**Acceptance Criteria:**
- [ ] Plist file created with correct syntax
- [ ] Points to Python script in venv
- [ ] Uses port 8787
- [ ] Runs on system boot
- [ ] Logs to file for debugging

**File:** `com.officetracker.plist`

**Template:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.officetracker</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/rahulmishra/Desktop/Personal/wifi-tracking/venv/bin/python</string>
        <string>-m</string>
        <string>uvicorn</string>
        <string>app.main:app</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>8787</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/rahulmishra/Desktop/Personal/wifi-tracking</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/rahulmishra/Desktop/Personal/wifi-tracking/logs/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/rahulmishra/Desktop/Personal/wifi-tracking/logs/stderr.log</string>
</dict>
</plist>
```

---

### Task 6.2: Install Launch Agent
**Description:** Copy plist to LaunchAgents and load it
**Dependencies:** Task 6.1
**Acceptance Criteria:**
- [ ] Plist copied to ~/Library/LaunchAgents/
- [ ] Launch agent loaded successfully
- [ ] App starts automatically

---

### Task 6.3: Add Graceful Shutdown Handler
**Description:** Handle system shutdown/restart cleanly
**Dependencies:** Phase 2
**Acceptance Criteria:**
- [ ] Saves active session on shutdown
- [ ] Closes files properly
- [ ] No data corruption

**File:** `app/main.py`

---

### Task 6.4: Test Boot Auto-Start
**Description:** Verify app starts on system boot
**Dependencies:** Task 6.2
**Acceptance Criteria:**
- [ ] App runs after restart
- [ ] Dashboard accessible at http://localhost:8787 without manual start
- [ ] Sessions resume correctly
- [ ] Logs show successful startup

---

### Task 6.5: Create Install/Uninstall Scripts + Documentation
**Description:** Easy install, uninstall, and README
**Dependencies:** All previous tasks
**Acceptance Criteria:**
- [ ] `scripts/install.sh` — copies plist, loads agent
- [ ] `scripts/uninstall.sh` — unloads agent, removes plist
- [ ] README.md with setup, config, troubleshooting, uninstall

---

### ✅ Phase 6 Definition of Done

- [ ] App starts automatically on Mac boot
- [ ] No manual intervention needed
- [ ] Dashboard accessible immediately after boot
- [ ] Installation documented in README
- [ ] Uninstall process works
- [ ] Tested with actual restart

---

## 🧪 Testing & Validation

### End-to-End Test Scenarios

#### Scenario 1: Normal 4-Hour Office Day
1. Connect to office Wi-Fi → Session starts
2. Wait 4 hours (or 2 min in test mode) → Notification appears
3. Disconnect Wi-Fi → Session ends
4. Check log file → Session recorded with completed_4h=true

#### Scenario 2: Multiple Disconnects
1. Connect to office Wi-Fi → Session 1 starts
2. Disconnect after 1 hour → Session 1 ends
3. Reconnect to office Wi-Fi → Session 2 starts
4. Stay 3 more hours → Notification appears
5. Check log → Two sessions, only session 2 marked completed

#### Scenario 3: App Restart During Session
1. Connect to office Wi-Fi → Session starts
2. Kill and restart app after 2 hours
3. App resumes session → Timer shows 2 hours remaining
4. Complete 4 hours → Notification appears

#### Scenario 4: Laptop Sleep/Wake
1. Connect to office Wi-Fi → Session starts
2. Close laptop (sleep) after 1 hour
3. Wake laptop after 30 minutes
4. Timer continues from 1 hour elapsed (not 1.5 hours)

#### Scenario 5: System Reboot
1. Connect to office Wi-Fi → Session starts
2. Reboot Mac after 2 hours
3. App auto-starts
4. Reconnects to office Wi-Fi → Session resumes

---

## Timeline & Milestones

### Day 1: Foundation (COMPLETED)
- Phase 0: Environment setup
- Phase 1: Wi-Fi detection system (29 tests)
- Phase 2: File-based session storage (53 tests)

**Milestone:** Wi-Fi detection + session logging + recovery working (82 tests)

---

### Day 2: Timer + Dashboard Core
- Phase 3: Timer engine + notifications (3.1-3.6)
- Phase 4: Live dashboard UI (4.1-4.5)

**Milestone:** Live timer dashboard at http://localhost:8787

---

### Day 3: Analytics + Auto-Start
- Phase 5: Weekly + monthly analytics with Chart.js (5.1-5.4)
- Phase 6: Auto-start on boot via launchd (6.1-6.5)

**Milestone:** Fully automatic MVP with analytics complete

---

## 🔧 Troubleshooting Guide

### Issue: Wi-Fi Detection Not Working

**Symptoms:** App doesn't detect SSID changes

**Solutions:**
1. Check macOS airport command works:
   ```bash
   /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I
   ```
2. Verify polling loop is running (check logs)
3. Ensure correct office Wi-Fi name in .env
4. Check for typos in SSID (case-sensitive)

---

### Issue: Session Not Persisting

**Symptoms:** Session lost after restart

**Solutions:**
1. Check data/ folder exists and is writable
2. Verify JSON Lines format is valid
3. Check file permissions
4. Look for errors in logs/stderr.log

---

### Issue: Timer Not Counting

**Symptoms:** Remaining time not decreasing

**Solutions:**
1. Verify timer loop is running (check logs)
2. Check system clock is correct
3. Ensure session is marked as active
4. Verify start_time is valid datetime

---

### Issue: Notification Not Appearing

**Symptoms:** No alert at 4 hours

**Solutions:**
1. Check macOS notification permissions
2. Test osascript command manually:
   ```bash
   osascript -e 'display notification "Test" with title "Test"'
   ```
3. Verify timer completion logic works
4. Check notification was sent (logs)

---

### Issue: Auto-Start Not Working

**Symptoms:** App doesn't start on boot

**Solutions:**
1. Check plist is loaded:
   ```bash
   launchctl list | grep officetracker
   ```
2. Verify plist syntax:
   ```bash
   plutil -lint ~/Library/LaunchAgents/com.officetracker.plist
   ```
3. Check logs/stderr.log for errors
4. Ensure full paths in plist (no relative paths)
5. Verify venv Python path is correct

---

### Issue: Dashboard Not Loading

**Symptoms:** http://localhost:8000 doesn't work

**Solutions:**
1. Check if server is running:
   ```bash
   lsof -i :8000
   ```
2. Restart FastAPI server
3. Check logs for port conflicts
4. Try different port in .env

---

## Quick Start Commands

```bash
# Setup
cd /Users/rahulmishra/Desktop/Personal/wifi-tracking
source venv/bin/activate

# Run development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8787 --reload

# Open dashboard
open http://localhost:8787

# Run all tests
pytest tests/ -v

# Run tests for a specific phase
pytest tests/test_phase_3_1.py -v
```

---

## Success Criteria Checklist

### Feature Completeness
- [x] Automatically detects office Wi-Fi connection
- [ ] Starts 4-hour timer automatically
- [ ] Shows live countdown in web UI
- [ ] After completion, shows total elapsed time (keeps counting)
- [ ] Sends notification at (4h + buffer) completion
- [x] Stores sessions in local files (no database)
- [x] Works offline
- [x] Survives restarts (session recovery)
- [ ] Weekly analytics with day-by-day chart
- [ ] Monthly analytics with week-by-week chart
- [ ] Auto-starts on boot

### Quality Gates
- [x] No data loss during crashes
- [x] Files rotate properly (>5MB)
- [ ] Memory usage < 50MB
- [ ] CPU usage < 5% (when idle)
- [x] All edge cases handled
- [ ] Code is documented
- [ ] README has complete instructions

### Operational Readiness
- [ ] Can install in < 10 minutes
- [ ] Can uninstall cleanly
- [ ] Logs are readable
- [ ] HR can access log files
- [x] Works without internet

---

## Notes & Considerations

### Edge Cases to Handle
1. **Wi-Fi drops briefly (< 5 min):** Don't end session
2. **Multiple office Wi-Fi networks:** Support list in config
3. **Clock changes (DST):** Use monotonic time for elapsed
4. **File corruption:** Validate before writing, backup on rotation
5. **Concurrent access:** Use file locking if multiple instances

### Future Enhancements (Post-MVP)
- HR report export (PDF)
- Mobile app (PWA)
- Geo-location fallback
- Cloud sync (optional)
- Team aggregate view

### Security Considerations
- No sensitive data in logs
- Local files only (no external calls)
- No authentication needed (localhost only)

---

## Delivery Checklist

Before considering MVP complete:

- [ ] All 6 phases completed
- [ ] All Definition of Done items checked
- [ ] End-to-end tests pass
- [ ] Documentation complete
- [ ] Tested on actual office Wi-Fi
- [ ] Auto-start verified after reboot
- [ ] Handed off to user with:
  - [ ] README with setup instructions
  - [ ] Sample .env file
  - [ ] Troubleshooting guide

---

**Current State:** Phase 3 Tasks 3.1-3.5 DONE (153 tests passing, 0 warnings). Next: Task 3.6.

**Remember:** Build incrementally, test each phase before moving forward, and keep it simple!
