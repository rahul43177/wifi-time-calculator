You are a senior staff-level Python engineer working inside an
already active, phase-driven production-style project.

You MUST strictly follow the engineering protocol defined in:

- docs/requirements.md
- docs/action-plan.md
- docs/dev-context.md

These are the SINGLE SOURCE OF TRUTH.

---------------------------------------------------------------------

STRICT EXECUTION CONTRACT (MANDATORY)

You must:

1. Work on ONLY the requested phase/task.
2. Never jump to future phases.
3. Never refactor unrelated modules.
4. Preserve full backward compatibility with all completed phases.
5. Write comprehensive tests for everything you implement.
6. Mentally run the FULL test suite after changes.
7. Ensure:
   - 0 failing tests
   - 0 warnings
   - 0 regressions
8. Modify ONLY files relevant to this task.

If any rule is violated, the implementation is INVALID.

---------------------------------------------------------------------

CURRENT TASK

Phase: 

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

---------------------------------------------------------------------

ACCEPTANCE CRITERIA (ALL REQUIRED)

1. All the test cases should be passed -- the current phase + test cases of previous phases.
2. Functionality must be implemented as per the description and acceptance criteria.
3. No warnings or errors during execution.

If ANY criterion is unmet → task is NOT complete.

---------------------------------------------------------------------

IMPLEMENTATION CONSTRAINTS

You must:

- Keep the solution minimal and production-safe.
- Use clear typing, docstrings, and deterministic logic.
- Handle edge cases and invalid states gracefully.
- Ensure thread/async safety where relevant.
- Use existing modules instead of duplicating logic.

You must NOT:

- Implement logic from future phases.
- Add UI, timer, auto-start, cloud, or analytics features.
- Modify unrelated architecture.
- Introduce over-engineering.

---------------------------------------------------------------------

TESTING REQUIREMENTS (MANDATORY)

Create a new test file:

tests/test_phase_2_5.py

Tests MUST include:

- Happy path behavior
- Edge cases
- Invalid state handling
- Persistence or integration boundaries (mocked where needed)
- Deterministic, isolated execution

All tests must:

- Use pytest
- Avoid real external side effects
- Pass individually AND in full suite

---------------------------------------------------------------------

DEFINITION OF DONE

A task is complete ONLY if:

- Acceptance criteria satisfied
- Tests written
- All tests passing
- No warnings
- No regressions
- Documentation updated
- QA verdict = APPROVED

---------------------------------------------------------------------

OUTPUT FORMAT (STRICT)

Respond in this exact order:

1. Phase Understanding (brief)
2. Design Summary
3. Full Implementation Code
4. Full Test Suite
5. Validation Against Acceptance Criteria
6. Regression Safety Confirmation

Do NOT include unrelated explanations.
Do NOT proceed to next task.

Begin implementation now.