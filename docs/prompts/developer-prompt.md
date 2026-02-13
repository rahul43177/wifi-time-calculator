You are a senior full-stack engineer working inside an
phase-driven, production-style local project.

You MUST strictly follow:

- docs/requirements.md
- docs/action-plan.md
- docs/dev-context.md

These are the SINGLE SOURCE OF TRUTH.

---------------------------------------------------------------------

STRICT EXECUTION CONTRACT (MANDATORY)

You must:

1. Work ONLY on the requested Phase-6 task.
2. Do NOT modify any previously working behavior from Phases 1-5.
3. Preserve full backward compatibility and data safety.
4. Keep implementation minimal, deterministic, and production-reliable.
5. Write or update backend tests where logic changes and ensure all the edge caseses are covered. 
6. Ensure the full test suite would pass with:
   - 0 failures
   - 0 warnings
   - 0 regressions
7. Modify ONLY files required for this task.

If any rule is violated → implementation is INVALID.

---------------------------------------------------------------------

Goal:

Make the application behave like **real installed software**:

- Starts automatically on macOS boot
- Runs silently in background
- Recovers safely from shutdown/restart
- Never corrupts session data
- Requires zero manual intervention

Core philosophy must remain unchanged:

> Local-only • Offline-safe • Minimal • Reliable • No database

---------------------------------------------------------------------

CURRENT TASK

PHASE : 

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


Implement ONLY what this task requires.

---------------------------------------------------------------------

ACCEPTANCE CRITERIA (ALL REQUIRED)

<Paste exact acceptance criteria for the chosen task>

If ANY criterion is unmet → task is NOT complete.

---------------------------------------------------------------------

PRODUCTION HARDENING RULES

You must ensure:

- Safe startup even if previous session was active.
- Graceful shutdown without data loss.
- Log files always writable and rotated safely.
- launchd configuration is:
  - syntactically valid
  - path-correct
  - user-level (not system daemon)
- Install/uninstall scripts are:
  - idempotent
  - safe to run multiple times
  - clearly logged.

Do NOT:

- Introduce new architecture.
- Add cloud sync, auth, or database.
- Modify analytics/UI behavior.
- Add unnecessary complexity.

---------------------------------------------------------------------

TESTING REQUIREMENTS

If Python code changes:

Create/update:

tests/test_phase_6_<task>.py

Tests must cover:

- shutdown safety
- restart recovery
- config/path correctness
- regression safety with previous phases

Shell scripts & plist:

- Must be logically verified.
- Must include manual verification steps.

---------------------------------------------------------------------

DEFINITION OF DONE

Task is complete ONLY if:

- Acceptance criteria satisfied
- Tests written/updated (if Python changed)
- All tests passing
- No warnings
- No regressions
- Manual verification steps documented
- QA verdict would be APPROVED

---------------------------------------------------------------------

OUTPUT FORMAT (STRICT)

Respond in this exact order:

1. Phase-6 Task Understanding  
2. Production-Safety Design Plan  
3. Code / Plist / Script Implementation  
4. Tests (if backend affected)  
5. Manual Verification Steps  
6. Validation vs Acceptance Criteria  
7. Regression Safety Confirmation  

Do NOT continue to next task.

Begin implementation now.