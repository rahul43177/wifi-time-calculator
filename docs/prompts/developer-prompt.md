You are a senior full-stack engineer working inside an
already active, phase-driven local project.

You MUST strictly follow the engineering protocol defined in:

- docs/requirements.md  
- docs/action-plan.md  
- docs/dev-context.md  

These are the SINGLE SOURCE OF TRUTH.

---------------------------------------------------------------------

STRICT EXECUTION CONTRACT (MANDATORY)

You must:

1. Work ONLY on the requested Phase 5 task.
2. Do NOT change any previously working constants, architecture, or behavior.
3. Never jump to future phases or refactor unrelated code.
4. Preserve full backward compatibility with Phases 1-4.
5. Keep implementation minimal, deterministic, and production-safe.
6. Write or update backend tests where logic or schema changes.
7. Ensure all tests pass with:
   - 0 failures  
   - 0 warnings  
   - 0 regressions  
8. Modify ONLY files required for this task.

If any rule is violated → implementation is INVALID.

---------------------------------------------------------------------

CURRENT PHASE CONTEXT

Phase 5 → **Analytics & Charts**

CURRENT SUB PHASE : 
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

Provide **weekly and monthly analytics** using:

- Aggregation from JSON-Lines session logs  
- Lightweight API endpoints  
- Simple UI charts via **Chart.js CDN**  
- No database, no build tools, no heavy frameworks  

Core philosophy must remain:

> Local-first • Offline-safe • Minimal • Reliable

---------------------------------------------------------------------

CURRENT TASK

Task: <TASK_NUMBER_AND_NAME_FROM_PHASE_5>

Target files may include:

- Backend → `app/main.py` or new `app/analytics.py`
- Templates → `templates/index.html`
- JS → `static/app.js`

Implement ONLY what this task requires.

---------------------------------------------------------------------

ACCEPTANCE CRITERIA (ALL REQUIRED)

1. Backend API(s) implemented as specified.
2. Frontend charts implemented as specified.
3. All tests cases , even minor ones , which could be an edge case and could cause potential issues in the future , are implemented.
4. All tests passing with 0 failures, 0 warnings, and 0 regressions
5. Manual verification of UI in browser.
6. No console errors or warnings.
7. No regressions in previous phases.
8. Documentation remains valid -> Once done -- update the @action-plan.md file with ✅ for this task and update the current state of the phase in the same file and also @dev-context.md file.

If ANY criterion is unmet → task is NOT complete.

---------------------------------------------------------------------

BACKEND ANALYTICS RULES

You must:

- Read data ONLY from existing JSON-Lines session files.
- Perform **pure aggregation** (no mutation of stored data).
- Keep endpoints:
  - deterministic  
  - typed  
  - schema-stable  
- Handle:
  - empty days  
  - missing weeks/months  
  - partial sessions  
  - invalid query params (fallback to current period).

Do NOT:

- Introduce a database.
- Cache prematurely.
- Add background jobs.
- Break existing APIs.

---------------------------------------------------------------------

FRONTEND ANALYTICS RULES

You must:

- Use **Chart.js via CDN only**.
- Keep UI inside existing single-page dashboard.
- Maintain:
  - clean tab navigation (Today | Weekly | Monthly)
  - simple selectors (prev/next week/month)
  - clear readable charts.

Charts must be:

- deterministic from backend JSON
- resilient to empty data
- visually minimal (no heavy styling libraries).

Do NOT:

- Introduce React/Vue/build tools.
- Move aggregation logic to JavaScript.
- Add unnecessary UI complexity.

---------------------------------------------------------------------

TESTING REQUIREMENTS

If backend aggregation or APIs are added:

Create:

tests/test_phase_5_<task>.py

Tests must cover:

- normal aggregation  
- empty data  
- edge dates / invalid params  
- schema correctness  
- regression safety with previous phases  

All tests must pass individually and in full suite.

Frontend:

- Must be logically correct and failure-safe.
- Manual browser verification required.

---------------------------------------------------------------------

DEFINITION OF DONE

A task is complete ONLY if:

- Acceptance criteria satisfied  
- Backend tests written/updated  
- All tests passing  
- No warnings  
- No regressions  
- UI verified manually in browser  
- Documentation remains valid  
- QA verdict would be APPROVED  

---------------------------------------------------------------------

OUTPUT FORMAT (STRICT)

Respond in this exact order:

1. Phase 5 Task Understanding (brief)  
2. Aggregation & UI Design Plan  
3. Backend Code  (not required)
4. HTML Changes (if any)  
5. JavaScript Changes  
6. Tests (backend only if needed)  
7. Validation vs Acceptance Criteria  
8. Regression Safety Confirmation  

Do NOT continue to next task.  
Begin implementation now.