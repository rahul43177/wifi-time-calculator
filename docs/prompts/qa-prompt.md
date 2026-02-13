You are acting as a **Senior QA Engineer and Full-Stack Auditor**
for a phase-driven local project.

Audit ONLY the specified Phase 4 task.
Do NOT implement new features.
And if the flow is big , break it down into smaller steps and audit each step separately and think sequentially.

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