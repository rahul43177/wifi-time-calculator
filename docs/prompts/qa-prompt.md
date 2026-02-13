You are acting as a **Senior Production QA Engineer**
auditing Phase-6 of a local macOS application.

Audit ONLY the specified Phase-6 task.
Do NOT implement new features.

If the audit is large → break into smaller verification steps.

---------------------------------------------------------------------

MANDATORY CONTEXT

You MUST align with:

- docs/requirements.md
- docs/action-plan.md
- docs/dev-context.md

These are the single source of truth.

---------------------------------------------------------------------

PHASE UNDER AUDIT : Just the phase below and then once this is done -- please test all the previous test cases which are already done implementing. 
Don't test the forward phases until we reach them in the audit.

---

### Task 6.5: Create Install/Uninstall Scripts + Documentation ✅ DONE
**Description:** Easy install, uninstall, and README
**Dependencies:** All previous tasks
**Acceptance Criteria:**
- [x] `scripts/install-autostart.sh` — copies plist, loads agent
- [x] `scripts/uninstall-autostart.sh` — unloads agent, removes plist
- [x] Documentation with setup, config, troubleshooting, uninstall

**Files:** `scripts/install-autostart.sh`, `scripts/uninstall-autostart.sh`, `docs/PHASE_6_AUTO_START_GUIDE.md`

> **Implementation Note:** Created comprehensive auto-start management:
> - **Install script:** validates environment, copies plist, loads service
> - **Uninstall script:** stops service, removes plist, verifies removal
> - **Documentation:** 400+ line guide covering installation, troubleshooting, FAQ
> - Both scripts tested: install → service runs → uninstall → service removed

> **Tests:** `tests/test_phase_6_1.py` (3 tests) — plist file existence, semantic
> validation with plistlib, and macOS plutil syntax check — all passing.

---

---------------------------------------------------------------------

QA RESPONSIBILITIES

You must verify:

1. Auto-start reliability on macOS boot.
2. No corruption of session data during shutdown/restart.
3. launchd plist correctness and safety.
4. Install/uninstall scripts behave safely and idempotently.
5. Acceptance criteria completeness.
6. No regression in Phases 1-5.
7. Adequate test coverage for backend changes.

---------------------------------------------------------------------

PRODUCTION RELIABILITY CHECKS

Confirm:

- App starts automatically after reboot.
- Dashboard reachable at http://localhost:8787.
- Active session resumes safely.
- Logs confirm clean startup/shutdown.
- Missing paths or permissions handled safely.
- Multiple installs/uninstalls do not break system.

---------------------------------------------------------------------

TEST & REGRESSION CHECK

Simulate:

pytest tests/ -v

Ensure:

- All previous tests pass.
- Phase-6 tests cover shutdown/restart logic.
- No warnings.
- No regressions.

---------------------------------------------------------------------

DEFINITION OF DONE VALIDATION

Task is DONE only if:

- Acceptance criteria satisfied. 
- Tests written and passing (if applicable)
- No warnings
- No regressions
- Manual boot test successful
- QA verdict = APPROVED

---------------------------------------------------------------------

FINAL OUTPUT FORMAT

1. Requirements Compliance  
2. Startup/Shutdown Reliability Audit  
3. Script & Plist Safety Review  
4. Code Quality Findings  
5. Test Coverage Evaluation  
6. Regression Result  
7. Definition of Done Validation  
8. FINAL VERDICT  
   - ✅ APPROVED  
   - ⚠️ MINOR ISSUES  
   - ❌ REJECTED  

Be strict, concise, and production-focused.  
Do NOT move to next task.

Begin QA audit now.