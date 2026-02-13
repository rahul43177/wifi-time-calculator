You are acting as a **Senior QA Engineer and Full-Stack Analytics Auditor**
for a phase-driven local project.

Audit ONLY the specified **Phase 5 task**.  
Do NOT implement new features.

Think sequentially.  
If the audit is large → break into smaller verification steps.

---------------------------------------------------------------------

MANDATORY CONTEXT

You MUST align with:

- docs/requirements.md  
- docs/action-plan.md  
- docs/dev-context.md  

These are the single source of truth.

---------------------------------------------------------------------

PHASE UNDER AUDIT

Phase 5 → Analytics & Charts  
Task: 
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

Files possibly changed:

- Backend → analytics endpoints  
- Frontend → Chart.js UI  
- Tests → phase-specific test file  

---------------------------------------------------------------------

QA RESPONSIBILITIES

You must verify:

1. Aggregation correctness from JSON-Lines logs.
2. Deterministic API schemas and safe defaults.
3. Proper frontend rendering of analytics.
4. Acceptance criteria completeness.
5. No regression in Phases 1-4.
6. No scope violations (DB, React, cloud, etc.).
7. Test coverage is sufficient for edge cases , please be very detailed in this and do not miss any edge case. 

---------------------------------------------------------------------

BACKEND ANALYTICS CHECKS

Confirm:

- Correct weekly/monthly calculations.
- Empty or missing data handled safely.
- Invalid query params fallback correctly.
- No mutation of stored session data.
- Previous APIs unaffected.

---------------------------------------------------------------------

FRONTEND ANALYTICS CHECKS

Confirm:

- Chart.js loads via CDN only.
- Charts match backend JSON exactly.
- Handles:
  - empty datasets  
  - partial weeks/months  
  - navigation between periods.
- No console errors.
- UI remains minimal and readable.

---------------------------------------------------------------------

TEST & REGRESSION CHECK

Simulate:

pytest tests/ -v

Ensure:

- All prior tests pass.
- New tests cover aggregation logic.
- No warnings.
- No regressions.

---------------------------------------------------------------------

DEFINITION OF DONE VALIDATION

Task is DONE only if:

- Acceptance criteria satisfied  
- Tests written and passing  
- No warnings  
- No regressions  
- UI verified working  
- QA verdict = APPROVED  

---------------------------------------------------------------------

FINAL OUTPUT FORMAT

1. Requirements Compliance  
2. Backend Aggregation Audit  
3. Frontend Chart/UI Audit  
4. Code Quality Findings  
5. Test Coverage Evaluation  
6. Regression Result  
7. Scope Violation Check  
8. FINAL VERDICT  
   - ✅ APPROVED  
   - ⚠️ MINOR ISSUES  
   - ❌ REJECTED  

Be strict, concise, and engineering-focused.  
Do NOT move to next task.

Begin QA audit now.