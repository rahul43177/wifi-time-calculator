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
5. Write comprehensive tests for everything you implement and try to cover all the edge cases.
6. Mentally run the FULL test suite after changes.
7. Ensure:
   - 0 failing tests
   - 0 warnings
   - 0 regressions
8. Modify ONLY files relevant to this task.
9. Update the action plan and documentation for this phase.

If any rule is violated, the implementation is INVALID.

---------------------------------------------------------------------

CURRENT TASK

Phase: 

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

tests/test_phase_<test_phase_number>_<test_task_number>.py 
If you are confused in the naming convention , please refer to the test file naming in the previous phases. Write comprehensive tests covering: - Happy path behavior - Edge cases - Invalid state handling - Persistence or integration boundaries (mocked where needed) - Deterministic, isolated execution All tests must: - Use pytest - Avoid real external side effects - Pass individually AND in full suite


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
3. Validation Against Acceptance Criteria
4. Regression Safety Confirmation

Do NOT include unrelated explanations.
Do NOT proceed to next task.

Begin implementation now.