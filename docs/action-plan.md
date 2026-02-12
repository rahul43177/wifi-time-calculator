# Office Wi-Fi 4-Hour Tracker — Action Plan

**Project Start Date:** February 12, 2026  
**Estimated MVP Completion:** 2-3 days of focused development  
**Target User:** Personal productivity + HR audit trail

---

## 📋 Table of Contents

1. [Pre-Development Setup](#pre-development-setup)
2. [Phase 1: Wi-Fi Detection System](#phase-1-wifi-detection-system)
3. [Phase 2: File-Based Session Storage](#phase-2-file-based-session-storage)
4. [Phase 3: Timer Engine & Notifications](#phase-3-timer-engine--notifications)
5. [Phase 4: Local Web UI Dashboard](#phase-4-local-web-ui-dashboard)
6. [Phase 5: Auto-Start on Boot](#phase-5-auto-start-on-boot)
7. [Testing & Validation](#testing--validation)
8. [Timeline & Milestones](#timeline--milestones)
9. [Troubleshooting Guide](#troubleshooting-guide)

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

### Task 1.4: Add Logging Configuration
**Description:** Set up proper logging for debugging
**Dependencies:** Task 0.3
**Acceptance Criteria:**
- [ ] Logs show timestamps
- [ ] Different log levels work
- [ ] Logs go to console and optionally to file

**File:** `app/main.py` and `app/config.py`

---

### ✅ Phase 1 Definition of Done

- [ ] Can detect current SSID on macOS
- [ ] Background loop checks every 30 seconds
- [ ] SSID changes logged to console
- [ ] No crashes or errors during Wi-Fi changes
- [ ] Code is modular and documented

---

## 💾 Phase 2: File-Based Session Storage

**Goal:** Store session data in local JSON Lines files without database  
**Estimated Time:** 3-4 hours

---

### Task 2.1: Design File Storage Module
**Description:** Create file_store.py with core file operations  
**Dependencies:** Phase 1 complete  
**Acceptance Criteria:**
- [ ] Can create daily log files with naming: `sessions_YYYY-MM-DD.log`
- [ ] Can append JSON lines to files
- [ ] Can read today's sessions
- [ ] Thread-safe file operations

**File:** `app/file_store.py`

**Key Functions:**
- `get_today_log_path()` → Returns path to today's file
- `append_session(session_dict)` → Appends JSON line
- `read_today_sessions()` → Returns list of session dicts
- `read_all_sessions(date)` → Read specific date

**JSON Line Format:**
```json
{"date": "2026-02-12", "ssid": "OfficeWifi", "start_time": "09:42:10", "end_time": "13:48:55", "duration_minutes": 246, "completed_4h": true}
```

---

### Task 2.2: Implement Session State Machine
**Description:** Create session manager with IDLE/IN_OFFICE_SESSION/COMPLETED states  
**Dependencies:** Task 2.1  
**Acceptance Criteria:**
- [ ] Tracks current session state
- [ ] Stores active session in memory
- [ ] Transitions between states correctly
- [ ] Persists state to file on changes

**File:** `app/session_manager.py`

**Key Components:**
- `SessionState` Enum (IDLE, IN_OFFICE_SESSION, COMPLETED)
- `Session` dataclass with start_time, end_time, ssid, etc.
- `SessionManager` class with state machine logic

**State Transitions:**
```
IDLE + office_wifi_detected → IN_OFFICE_SESSION (save start)
IN_OFFICE_SESSION + wifi_disconnected → IDLE (save end)
IN_OFFICE_SESSION + 4h_complete → COMPLETED (update file)
```

---

### Task 2.3: Integrate Session Manager with Wi-Fi Detector
**Description:** Connect Wi-Fi change events to session manager  
**Dependencies:** Task 2.2, Phase 1  
**Acceptance Criteria:**
- [ ] Wi-Fi connect to office → starts session
- [ ] Wi-Fi disconnect from office → ends session
- [ ] Sessions written to daily log file
- [ ] Works across multiple connect/disconnect cycles

**Files:** `app/wifi_detector.py`, `app/session_manager.py`

**Key Integration Points:**
- Pass SSID changes to session manager
- Check if SSID matches OFFICE_WIFI_NAME
- Call session_manager.start_session() or end_session()

**Test:** Connect/disconnect Wi-Fi and verify sessions appear in `data/sessions_2026-02-12.log`

---

### Task 2.4: Implement File Rotation Logic
**Description:** Rotate files when they exceed 5MB  
**Dependencies:** Task 2.1  
**Acceptance Criteria:**
- [ ] Checks file size before writing
- [ ] Moves file to archive/ if > 5MB
- [ ] Creates new part file (sessions_YYYY-MM-DD_part2.log)
- [ ] Maintains data integrity

**File:** `app/file_store.py`

**Key Implementation Points:**
- Check file size: `os.path.getsize()`
- Move to archive: `shutil.move()`
- Update filename with part number
- Handle edge cases (archive folder doesn't exist, etc.)

---

### Task 2.5: Add Session Recovery on Restart
**Description:** Restore active session if app restarts during office hours  
**Dependencies:** Task 2.3  
**Acceptance Criteria:**
- [ ] On startup, checks if currently connected to office Wi-Fi
- [ ] Reads today's log for incomplete session
- [ ] Resumes session if still in office
- [ ] Creates new session if previous was completed

**File:** `app/session_manager.py`

**Key Implementation Points:**
- On startup: check current SSID
- Read today's log file
- Look for session without end_time
- If found and still connected: resume
- If found but disconnected: close previous session

**Test:** Start session, restart app while connected, verify session continues

---

### Task 2.6: Add Data Validation
**Description:** Validate session data before saving  
**Dependencies:** Task 2.1  
**Acceptance Criteria:**
- [ ] Uses Pydantic models for validation
- [ ] Rejects invalid data
- [ ] Clear error messages

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

---

### ✅ Phase 2 Definition of Done

- [ ] Sessions saved to daily log files in JSON Lines format
- [ ] New file created each day automatically
- [ ] Connect/disconnect cycles logged correctly
- [ ] Files rotate when > 5MB
- [ ] Session resumes after app restart
- [ ] Can read today's sessions programmatically
- [ ] No data loss during crashes

---

## ⏱️ Phase 3: Timer Engine & Notifications

**Goal:** Track 4-hour completion and send alerts  
**Estimated Time:** 2-3 hours

---

### Task 3.1: Implement Timer Calculation Logic
**Description:** Calculate elapsed and remaining time for active session  
**Dependencies:** Phase 2 complete  
**Acceptance Criteria:**
- [ ] Calculates elapsed time: now - start_time
- [ ] Calculates remaining time: 4h - elapsed
- [ ] Returns formatted strings (HH:MM:SS)
- [ ] Handles timezone correctly

**File:** `app/timer_engine.py`

**Key Functions:**
- `get_elapsed_time(start_time: datetime) → timedelta`
- `get_remaining_time(start_time: datetime, target_hours: int) → timedelta`
- `format_time_display(td: timedelta) → str`
- `is_completed(start_time: datetime, target_hours: int) → bool`

---

### Task 3.2: Create Background Timer Loop
**Description:** Check timer every 60 seconds  
**Dependencies:** Task 3.1  
**Acceptance Criteria:**
- [ ] Runs every 60 seconds
- [ ] Only checks when session is active
- [ ] Logs remaining time
- [ ] Detects completion

**File:** `app/timer_engine.py`

**Key Implementation Points:**
- Use asyncio for background task
- Get active session from session manager
- Calculate remaining time
- Log every minute for debugging
- Trigger notification when completed

---

### Task 3.3: Implement Notification System
**Description:** Send browser/OS notification at 4-hour completion  
**Dependencies:** Task 3.2  
**Acceptance Criteria:**
- [ ] Sends notification when timer completes
- [ ] Only sends once per session
- [ ] Clear, actionable message
- [ ] Doesn't crash if notification fails

**File:** `app/notifier.py`

**Implementation Options:**
1. **Browser Notification API** (via WebSocket to UI)
2. **macOS Notification Center** (using osascript)
3. **Python plyer library** (cross-platform)

**Recommended for MVP:** macOS osascript

**macOS Command:**
```bash
osascript -e 'display notification "4 hours completed. You may leave the office." with title "Office Tracker"'
```

**Key Functions:**
- `send_notification(title: str, message: str) → bool`
- `can_send_notifications() → bool`

---

### Task 3.4: Add Completion Flag to Session
**Description:** Mark session as completed in file when 4 hours reached  
**Dependencies:** Task 3.3, Phase 2  
**Acceptance Criteria:**
- [ ] Updates session log with completed_4h = true
- [ ] Only updates once
- [ ] Persists immediately to file

**Files:** `app/timer_engine.py`, `app/file_store.py`

**Key Implementation Points:**
- Add update_session() function to file_store
- Read file, find active session line, update it
- Use file locking if needed (probably not for MVP)
- Log the update

---

### Task 3.5: Integrate Timer with FastAPI
**Description:** Start timer loop as background task  
**Dependencies:** Task 3.2, Phase 1 Task 1.4  
**Acceptance Criteria:**
- [ ] Timer starts with server
- [ ] Runs alongside Wi-Fi detector
- [ ] Stops gracefully on shutdown

**File:** `app/main.py`

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

- [ ] Timer calculates remaining time correctly
- [ ] Notification appears when 4 hours complete
- [ ] Only one notification per session
- [ ] Session marked as completed in log file
- [ ] Test mode works with 2-minute duration
- [ ] Timer survives app restart (resumes correctly)

---

## 🖥️ Phase 4: Local Web UI Dashboard

**Goal:** Simple web interface showing live status and today's history  
**Estimated Time:** 3-4 hours

---

### Task 4.1: Create FastAPI Routes
**Description:** Set up API endpoints for status and data  
**Dependencies:** Phase 3 complete  
**Acceptance Criteria:**
- [ ] GET / → HTML dashboard
- [ ] GET /api/status → Current session info
- [ ] GET /api/today → Today's completed sessions
- [ ] All endpoints return proper JSON/HTML

**File:** `app/main.py`

**API Response Examples:**

`GET /api/status`:
```json
{
  "connected": true,
  "ssid": "OfficeWifi",
  "session_active": true,
  "start_time": "2026-02-12T09:42:10",
  "elapsed": "02:15:30",
  "remaining": "01:44:30",
  "completed": false,
  "progress_percent": 56.4
}
```

`GET /api/today`:
```json
{
  "date": "2026-02-12",
  "sessions": [
    {
      "start_time": "09:42:10",
      "end_time": "13:48:55",
      "duration_minutes": 246,
      "completed_4h": true
    }
  ],
  "total_minutes": 246
}
```

---

### Task 4.2: Create HTML Dashboard Template
**Description:** Simple, clean HTML interface  
**Dependencies:** Task 4.1  
**Acceptance Criteria:**
- [ ] Shows current connection status
- [ ] Displays countdown timer
- [ ] Shows progress bar
- [ ] Lists today's sessions in table
- [ ] Responsive design (looks good on laptop)

**File:** `templates/index.html`

**UI Components:**
1. **Status Card:**
   - Connection status (✓ Connected / ✗ Disconnected)
   - Current SSID
   - Session start time

2. **Timer Card:**
   - Large countdown display (01:44:30 remaining)
   - Progress bar (0-100%)
   - Elapsed time

3. **Today's Sessions Table:**
   - Start time | End time | Duration | Status
   - Sortable columns

4. **Summary Stats:**
   - Total time today
   - Sessions completed
   - Next action (e.g., "Stay 1h 44m more")

---

### Task 4.3: Add CSS Styling
**Description:** Make UI visually appealing  
**Dependencies:** Task 4.2  
**Acceptance Criteria:**
- [ ] Clean, modern design
- [ ] Good color scheme (green for connected, red for disconnected)
- [ ] Readable fonts and spacing
- [ ] Mobile-friendly (bonus)

**File:** `static/style.css`

**Design Principles:**
- Minimalist design
- High contrast for readability
- Large, clear timer display
- Color coding: green (on track), yellow (almost done), red (disconnected)

---

### Task 4.4: Implement Auto-Refresh JavaScript
**Description:** Update UI every 30 seconds automatically  
**Dependencies:** Task 4.2  
**Acceptance Criteria:**
- [ ] Fetches /api/status every 30 seconds
- [ ] Updates countdown in real-time
- [ ] Updates progress bar
- [ ] Refreshes session table
- [ ] Shows loading indicators

**File:** `static/app.js`

**Key Features:**
- `setInterval()` for 30-second polling
- Fetch API for AJAX calls
- DOM manipulation to update values
- Error handling for network failures
- Visual feedback during updates

---

### Task 4.5: Add Browser Notification Support
**Description:** Request notification permission and show alerts  
**Dependencies:** Task 4.4  
**Acceptance Criteria:**
- [ ] Requests notification permission on page load
- [ ] Receives completion events from backend
- [ ] Shows browser notification
- [ ] Works even if tab not focused

**File:** `static/app.js`

**Implementation Options:**
1. **WebSocket** for real-time push
2. **Polling** /api/status for completion flag

**Recommended for MVP:** Polling approach (simpler)

---

### Task 4.6: Add Manual Controls (Optional)
**Description:** Buttons to manually start/stop sessions for testing  
**Dependencies:** Task 4.1  
**Acceptance Criteria:**
- [ ] "Start Session" button
- [ ] "End Session" button
- [ ] Only visible in TEST_MODE

**File:** `templates/index.html`, `app/main.py`

---

### ✅ Phase 4 Definition of Done

- [ ] Dashboard accessible at http://localhost:8000
- [ ] Shows real-time countdown
- [ ] Progress bar updates automatically
- [ ] Today's sessions displayed in table
- [ ] Auto-refreshes every 30 seconds
- [ ] Browser notification works
- [ ] UI is clean and usable
- [ ] No console errors

---

## 🚀 Phase 5: Auto-Start on Boot

**Goal:** App starts automatically when Mac boots up  
**Estimated Time:** 1-2 hours

---

### Task 5.1: Create launchd Plist File
**Description:** macOS launchd configuration for auto-start  
**Dependencies:** Phases 1-4 complete  
**Acceptance Criteria:**
- [ ] Plist file created with correct syntax
- [ ] Points to Python script in venv
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
        <string>8000</string>
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

### Task 5.2: Install Launch Agent
**Description:** Copy plist to LaunchAgents and load it  
**Dependencies:** Task 5.1  
**Acceptance Criteria:**
- [ ] Plist copied to ~/Library/LaunchAgents/
- [ ] Launch agent loaded successfully
- [ ] App starts automatically

**Commands:**
```bash
# Create logs directory
mkdir -p logs

# Copy plist file
cp com.officetracker.plist ~/Library/LaunchAgents/

# Load launch agent
launchctl load ~/Library/LaunchAgents/com.officetracker.plist

# Check status
launchctl list | grep officetracker
```

---

### Task 5.3: Add Graceful Shutdown Handler
**Description:** Handle system shutdown/restart cleanly  
**Dependencies:** Phase 2  
**Acceptance Criteria:**
- [ ] Saves active session on shutdown
- [ ] Closes files properly
- [ ] No data corruption

**File:** `app/main.py`

**Key Implementation Points:**
- Use FastAPI lifespan shutdown event
- Call session_manager.save_state()
- Close all file handles
- Log shutdown event

---

### Task 5.4: Test Boot Auto-Start
**Description:** Verify app starts on system boot  
**Dependencies:** Task 5.2  
**Acceptance Criteria:**
- [ ] App runs after restart
- [ ] Dashboard accessible without manual start
- [ ] Sessions resume correctly
- [ ] Logs show successful startup

**Test Steps:**
1. Load launch agent
2. Restart Mac
3. Wait 30 seconds
4. Open http://localhost:8000
5. Check logs in `logs/stdout.log`

---

### Task 5.5: Create Uninstall Script
**Description:** Easy way to remove auto-start  
**Dependencies:** Task 5.2  
**Acceptance Criteria:**
- [ ] Script unloads launch agent
- [ ] Removes plist file
- [ ] Stops running instance

**File:** `scripts/uninstall.sh`

```bash
#!/bin/bash
launchctl unload ~/Library/LaunchAgents/com.officetracker.plist
rm ~/Library/LaunchAgents/com.officetracker.plist
echo "Office tracker uninstalled"
```

---

### Task 5.6: Document Installation Steps
**Description:** Clear README with setup instructions  
**Dependencies:** All previous tasks  
**Acceptance Criteria:**
- [ ] Step-by-step installation guide
- [ ] Configuration instructions
- [ ] Troubleshooting section
- [ ] Uninstall instructions

**File:** `README.md`

---

### ✅ Phase 5 Definition of Done

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

## 📅 Timeline & Milestones

### Day 1: Foundation (6-7 hours)
- **Morning (3-4h):** Phase 0 + Phase 1
  - Setup environment
  - Implement Wi-Fi detection
  - Test SSID detection working
  
- **Afternoon (3h):** Phase 2 (partial)
  - File storage module
  - Session manager
  - Basic logging working

**Milestone:** Can detect Wi-Fi and log sessions to files

---

### Day 2: Core Logic (6-7 hours)
- **Morning (2-3h):** Phase 2 (complete)
  - File rotation
  - Session recovery
  - Testing
  
- **Afternoon (3-4h):** Phase 3
  - Timer engine
  - Notifications
  - 4-hour completion logic

**Milestone:** Timer works and notifications appear

---

### Day 3: UI & Polish (6-7 hours)
- **Morning (3-4h):** Phase 4
  - Dashboard UI
  - API endpoints
  - Auto-refresh
  
- **Afternoon (2-3h):** Phase 5
  - Auto-start setup
  - Testing
  - Documentation

**Milestone:** Fully automatic MVP complete ✅

---

### Total Estimated Time: 18-21 hours
**Recommendation:** Spread over 2-3 days with breaks

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

## 📦 Quick Start Commands

```bash
# Setup
git clone <repo>
cd wifi-tracking
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your office Wi-Fi name

# Run development server
uvicorn app.main:app --reload

# Open dashboard
open http://localhost:8000

# View logs
tail -f logs/stdout.log

# Test mode (2-minute duration)
# Set TEST_MODE=true in .env

# Install auto-start
cp com.officetracker.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.officetracker.plist

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.officetracker.plist
rm ~/Library/LaunchAgents/com.officetracker.plist
```

---

## 🎯 Success Criteria Checklist

### Feature Completeness
- [ ] Automatically detects office Wi-Fi connection
- [ ] Starts 4-hour timer automatically
- [ ] Shows live countdown in web UI
- [ ] Sends notification at completion
- [ ] Stores sessions in local files (no database)
- [ ] Works offline
- [ ] Survives restarts
- [ ] Auto-starts on boot

### Quality Gates
- [ ] No data loss during crashes
- [ ] Files rotate properly
- [ ] Memory usage < 50MB
- [ ] CPU usage < 5% (when idle)
- [ ] All edge cases handled
- [ ] Code is documented
- [ ] README has complete instructions

### Operational Readiness
- [ ] Can install in < 10 minutes
- [ ] Can uninstall cleanly
- [ ] Logs are readable
- [ ] HR can access log files
- [ ] Works without internet

---

## 📝 Notes & Considerations

### Edge Cases to Handle
1. **Wi-Fi drops briefly (< 5 min):** Don't end session
2. **Multiple office Wi-Fi networks:** Support list in config
3. **Clock changes (DST):** Use monotonic time for elapsed
4. **File corruption:** Validate before writing, backup on rotation
5. **Concurrent access:** Use file locking if multiple instances

### Future Enhancements (Post-MVP)
- Weekly summary email to HR
- Export to PDF
- Mobile app (PWA)
- Geo-location fallback
- Cloud sync (optional)
- Analytics dashboard
- Team aggregate view

### Security Considerations
- No sensitive data in logs
- Local files only (no external calls)
- No authentication needed (localhost only)
- Consider encryption for HR compliance

---

## 🚢 Delivery Checklist

Before considering MVP complete:

- [ ] All 5 phases completed
- [ ] All Definition of Done items checked
- [ ] End-to-end tests pass
- [ ] Documentation complete
- [ ] Tested on actual office Wi-Fi
- [ ] Auto-start verified after reboot
- [ ] Handed off to user with:
  - [ ] README with setup instructions
  - [ ] Sample .env file
  - [ ] Troubleshooting guide
  - [ ] Quick reference card

---

**Next Step:** Start with [Pre-Development Setup](#pre-development-setup) → Task 0.1

**Remember:** Build incrementally, test each phase before moving forward, and keep it simple!

