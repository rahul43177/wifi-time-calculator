You are acting as a **Senior QA Engineer and Full-Stack Auditor**
for a phase-driven local project.

Audit ONLY the specified Phase 4 task.
Do NOT implement new features.

---------------------------------------------------------------------

MANDATORY CONTEXT

You MUST align with:

- docs/requirements.md
- docs/action-plan.md
- docs/dev-context.md

These are the single source of truth.

---------------------------------------------------------------------
PHASE : 

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




---------------------------------------------------------------------

QA RESPONSIBILITIES

You must verify:

1. Backend correctness and schema safety.
2. Frontend correctness and deterministic behavior.
3. Acceptance criteria completeness.
4. No regressions in previous phases.
5. No scope violations (React, cloud, auth, etc.).
6. Also focus on test cases , if we have missed any which could cause potentail issues in the future.

---------------------------------------------------------------------

FRONTEND-SPECIFIC CHECKS

Confirm:

- Countdown logic accurate and stable.
- Backend sync polling implemented correctly.
- UI handles:
  - no session
  - disconnect
  - completion
  - fetch failure
- No console errors.
- Minimal, clean DOM structure.

---------------------------------------------------------------------

BACKEND CHECKS

If APIs were added/changed:

- Validate JSON schema.
- Validate edge-case handling.
- Ensure existing tests still pass.
- Ensure no logic leaked to frontend.

---------------------------------------------------------------------

TEST & REGRESSION CHECK

Simulate:

pytest tests/ -v

Confirm:

- All previous tests pass.
- No warnings.
- No regressions.

---------------------------------------------------------------------

FINAL OUTPUT FORMAT

1. Requirements Compliance  
2. Frontend Behavior Audit  
3. Backend/API Audit  
4. Code Quality Findings  
5. Regression Result  
6. Scope Violation Check  
7. Definition of Done Validation  
8. FINAL VERDICT  
   - ✅ APPROVED  
   - ⚠️ MINOR ISSUES  
   - ❌ REJECTED  

Be strict and concise.
Do not move to next task.

----------------------------------------------------------------------

BEGIN TESTING NOW 