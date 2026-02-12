# Office Wi-Fi 4-Hour Tracker — Local Automation Spec

## 1. Purpose

Build a **fully automatic local application** that:

* Detects when laptop connects to **office Wi-Fi**
* Starts a **4-hour work timer**
* Shows **live remaining time**
* Sends **alert when 4 hours complete**
* Stores **daily proof logs** locally for HR reference
* Uses **NO real database** (only local files)
* Runs **automatically in background**

This is a **personal productivity + audit trail tool**.

---

## 2. Core Requirements

### Functional

1. Detect current **connected Wi-Fi SSID** automatically.
2. When SSID == `OFFICE_WIFI_NAME`:

   * Start session timer.
   * Record **start timestamp**.
3. When Wi-Fi disconnects or changes:

   * Record **end timestamp**.
4. Continuously compute:

```
remaining_time = (4 hours + buffer) − (now − start_time)
```

5. When remaining_time ≤ 0:

   * Trigger **notification**.
   * Mark session as **completed**.
6. **Continue tracking elapsed time** after 4-hour completion:
   * Session remains active until Wi-Fi disconnect.
   * `duration_minutes` keeps increasing beyond 4 hours.
   * This enables **weekly reporting** (e.g., "Monday: 6h 20m, Tuesday: 4h 10m").
   * The session log stores the **actual total office time**, not just the 4-hour target.
7. Provide **simple local UI** showing:

   * Connected status
   * Start time
   * Elapsed time
   * Remaining time countdown
   * Today's total time (keeps going after 4h)
   * Today's history

---

### Buffer Time

A configurable **buffer period** (default: **10 minutes**) is added to the 4-hour target.

* Actual target = `WORK_DURATION_HOURS` + `BUFFER_MINUTES`
* Example: 4h + 10min = **4 hours 10 minutes** before "you may leave" notification
* Reason: accounts for breaks, movement between meetings, transition time
* The notification message says: "4 hours + 10 min buffer completed. You may leave."
* Configurable via `.env`: `BUFFER_MINUTES=10`

---

## 3. Non-Functional Requirements

* **No database** (Postgres, SQLite, etc. NOT allowed).
* Must use **plain local files**.
* Must survive:

  * Laptop restart
  * Server restart
  * Browser close
* Must run **fully automatic** after setup.
* Must be **lightweight (<50MB RAM)**.
* Must work **offline**.

---

## 4. Technology Stack

### Backend

* Python 3.11+
* FastAPI (local web server)
* Background scheduler (async loop or APScheduler)

### Storage

* **JSON Lines or TXT logs**
* Automatic **file rotation**

### Frontend

* **HTML + Vanilla JS** (Jinja2 templates, no React, no build tools)
* **Chart.js** (CDN) for weekly/monthly bar charts
* Single-page layout with tabbed sections

### Notifications

* Browser Notification API
  **OR**
* OS notification (Mac/Windows optional).

---

## 5. File-Based Storage Design (NO DB)

### Folder Structure

```
data/
 ├── sessions_2026-02-12.log
 ├── sessions_2026-02-13.log
 └── archive/
```

### Storage Strategy

Each day → **new log file**.

Each session → **append one JSON line**:

```json
{
  "date": "2026-02-12",
  "ssid": "OfficeWifi",
  "start_time": "09:42:10",
  "end_time": "13:48:55",
  "duration_minutes": 246,
  "completed_4h": true
}
```

### Why JSON Lines?

* Easy append
* Easy parse
* Human readable
* HR proof ready

---

## 6. File Rotation Rules

1. **New file every day**:

   ```
   sessions_YYYY-MM-DD.log
   ```

2. If file size > **5 MB**:

   * Move to:

     ```
     data/archive/
     ```
   * Create:

     ```
     sessions_YYYY-MM-DD_part2.log
     ```

3. Keep **unlimited history** (proof for HR).

---

## 7. Wi-Fi Detection Logic

### Check Interval

Every **30 seconds**.

### OS Commands

**Mac**

```
/System/Library/PrivateFrameworks/Apple80211.framework/.../airport -I
```

**Windows**

```
netsh wlan show interfaces
```

### Detection Rule

```
IF current_ssid == OFFICE_WIFI_NAME
AND previous_ssid != OFFICE_WIFI_NAME
→ START session
```

```
IF previous_ssid == OFFICE_WIFI_NAME
AND current_ssid != OFFICE_WIFI_NAME
→ END session
```

---

## 8. Session State Machine

### States

* `IDLE`
* `IN_OFFICE_SESSION`
* `COMPLETED`

### Flow

```
Connect Wi-Fi →
Create active session →
Run timer →
(4 hours + buffer) reached →
Send notification →
Mark completed →
Continue tracking elapsed time →
Wait for disconnect →
Record total duration
```

---

## 9. Timer Engine

Runs every **60 seconds**.

### Calculation

```
elapsed = now − start_time
target = WORK_DURATION_HOURS + BUFFER_MINUTES
remaining = target − elapsed
```

### Conditions

**If remaining ≤ 0 AND not notified:**

* Send alert
* Mark `completed_4h = true`

---

## 10. Local UI Requirements

### Route

```
http://localhost:8787/
```

### Technology

* **HTML + Vanilla JS + Chart.js** (no React, no build tools)
* Jinja2 server-side templates
* Chart.js via CDN `<script>` tag for graphical charts
* Single-page layout with tab/section navigation

### 10.1 Live Timer View (Default)

The primary view when the page loads:

* **Connection status** — green "Connected to OfficeWifi" or red "Disconnected"
* **Session start time** — e.g., "Started at 09:42:10"
* **Live countdown timer** — large display showing `HH:MM:SS` remaining until (4h + buffer)
  * Updates every second via JavaScript `setInterval()`
  * When target reached: switches to showing **total elapsed time** in green
  * Format after completion: "Completed! Total: 05:23:10"
* **Progress bar** — 0% → 100% (100% = 4h + buffer reached)
* **Today's total office time** — sum of all sessions today, keeps growing
* **Today's sessions table** — Start | End | Duration | Status (Active/Completed/Ended)

Auto-refresh from backend: every **30 seconds** via `fetch('/api/status')`.
Client-side countdown: every **1 second** (derived from last-known start_time).

### 10.2 Weekly Analytics View

Accessible via tab/link on the dashboard:

* **Day-by-day breakdown** for the current week (Mon–Sun):
  * Each day shows: total office time, number of sessions, whether 4h target met
  * Example: "Monday: 6h 20m (2 sessions) ✓" / "Tuesday: 3h 45m (1 session) ✗"
* **Bar chart** (Chart.js) — X-axis: days, Y-axis: hours
  * 4h target line drawn as horizontal reference
  * Green bars for days >= 4h, red bars for days < 4h
* **Week selector** — navigate to previous weeks
* **Weekly summary** — total hours, average per day, days with 4h+ completed

### 10.3 Monthly Analytics View

Accessible via tab/link on the dashboard:

* **Week-by-week breakdown** for the current month:
  * Each week shows: total hours, days present, average daily hours
  * Example: "Week 1 (Feb 1-7): 22h 15m, 5 days, avg 4h 27m"
* **Bar/line chart** (Chart.js) — X-axis: weeks, Y-axis: total hours
* **Month selector** — navigate to previous months
* **Monthly summary** — total hours, total days present, overall average

### 10.4 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | HTML dashboard (Jinja2 template) |
| `/api/status` | GET | Current session status + timer info |
| `/api/today` | GET | Today's sessions + total time |
| `/api/weekly` | GET | Weekly day-by-day data (query: `?week=2026-W07`) |
| `/api/monthly` | GET | Monthly week-by-week data (query: `?month=2026-02`) |
| `/health` | GET | Health check |

### 10.5 Backend Independence

* The backend **continues tracking** regardless of whether the browser is open
* The UI is a **read-only view** into the backend state
* Closing the browser tab does NOT stop tracking
* All timer logic runs server-side; the JS countdown is purely cosmetic (syncs every 30s)

---

## 11. Notification Behavior

### Minimum Requirement

OS notification (macOS):

```
"4 hours + 10 min buffer completed. You may leave the office."
```

The notification fires **once** when `elapsed >= (4h + buffer)`.
After notification, the timer **keeps running** to log total office time.

### Optional Enhancement

Browser notification support later.

---

## 12. Background Auto-Start

### Mac

Use **launchd**.

### Windows

Use **Startup Task Scheduler**.

Goal:
**User never manually starts app.**

---

## 13. Project Folder Structure

```
office-wifi-tracker/
 ├── app/
 │   ├── main.py
 │   ├── wifi_detector.py
 │   ├── session_manager.py
 │   ├── timer_engine.py
 │   ├── notifier.py
 │   └── file_store.py
 ├── data/
 ├── templates/
 ├── static/
 ├── requirements.txt
 └── README.md
```

---

## 14. MVP Development Phases

### Phase 1 — Wi-Fi detection

Log SSID changes in terminal.

### Phase 2 — File session logging

Write start/end sessions to **daily log file**.

### Phase 3 — 4-hour timer + notification

Trigger alert when time completes.

### Phase 4 — Local UI dashboard

Show timer + today history.

### Phase 5 — Auto-start on boot

Fully zero-manual system.

---

## 15. Definition of Done (MVP)

Project is complete when:

* Laptop connects to office Wi-Fi
* Timer starts **automatically**
* 4-hour + buffer alert appears
* Session stored in **daily log file**
* UI shows **live countdown timer** with remaining time
* After completion, UI shows **total elapsed time** (keeps counting)
* **Weekly analytics** show day-by-day breakdown with bar chart
* **Monthly analytics** show week-by-week breakdown with chart
* Works after **restart without manual action**
* Auto-starts on macOS boot via launchd

---

## 16. Future Enhancements (Not MVP)

* HR report export (PDF)
* Mobile PWA version
* Multiple office Wi-Fi names
* Geo-location fallback
* Cloud backup (optional)
* Team aggregate view

---

## 17. Build Instruction for Claude

Claude must:

* Follow **phase-wise implementation**
* Keep code **modular**
* Avoid **database usage**
* Use **pure file logging**
* Ensure **restart safety**
* Provide **clear setup steps**

End goal:

> A silent background tool that proves office presence and removes mental load of tracking 4 hours.

---
