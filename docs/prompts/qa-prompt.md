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