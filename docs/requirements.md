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
remaining_time = 4 hours − (now − start_time)
```

5. When remaining_time ≤ 0:

   * Trigger **notification**.
   * Mark session as **completed**.
6. Provide **simple local UI** showing:

   * Connected status
   * Start time
   * Elapsed time
   * Remaining time countdown
   * Today’s history

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

* Simple **HTML + Vanilla JS**
* No React required.

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
4 hours reached →
Send notification →
Mark completed →
Wait for disconnect
```

---

## 9. Timer Engine

Runs every **60 seconds**.

### Calculation

```
elapsed = now − start_time
remaining = 4h − elapsed
```

### Conditions

**If remaining ≤ 0 AND not notified:**

* Send alert
* Mark `completed_4h = true`

---

## 10. Local UI Requirements

### Route

```
http://localhost:8000/
```

### Show

* Current SSID
* Session start time
* Live countdown timer
* Progress bar (0 → 4 hours)
* Today’s completed duration
* Table of today’s sessions

UI must **auto-refresh every 30 seconds**.

---

## 11. Notification Behavior

### Minimum Requirement

Browser popup:

```
"4 hours completed. You may leave the office."
```

### Optional Enhancement

OS notification support later.

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
* 4-hour alert appears
* Session stored in **daily log file**
* UI shows **correct remaining time**
* Works after **restart without manual action**

---

## 16. Future Enhancements (Not MVP)

* Weekly HR report export (PDF)
* Mobile PWA version
* Multiple office Wi-Fi names
* Geo-location fallback
* Cloud backup (optional)

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
