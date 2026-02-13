You are a senior full-stack engineer working inside an
already active, phase-driven local project.

You MUST strictly follow:

- docs/requirements.md
- docs/action-plan.md
- docs/dev-context.md

**See detailed proposal:** `docs/ui-enhancement-proposal.md`

These are the SINGLE SOURCE OF TRUTH.

---------------------------------------------------------------------

STRICT EXECUTION CONTRACT (MANDATORY)

You must:

1. Work ONLY on Phase -> Sub Phase mentioned 
2. Do NOT implement any other Phase 7 task.
3. Do NOT refactor unrelated UI, backend, or analytics logic.
4. Preserve full backward compatibility with Phases 1-6.
5. Keep implementation minimal, deterministic, and production-safe.
6. Write/update tests ONLY if backend logic is affected.
7. Ensure the full test suite would pass with:
   - 0 failures
   - 0 warnings
   - 0 regressions
8. Modify ONLY files required for Task 7.1.

If any rule is violated → implementation is INVALID.

---------------------------------------------------------------------

CURRENT PHASE CONTEXT

PHASE : 

---

### Task 7.6: Dark Mode Support
**Description:** Dark theme with system preference detection
**Dependencies:** Task 7.3
**Acceptance Criteria:**
- [ ] Auto-detects system dark mode preference
- [ ] Manual toggle available
- [ ] All colors optimized for dark background
- [ ] Smooth theme transition animation
- [ ] Preserves user preference in localStorage

**Files:** `static/style.css`, `static/app.js`

---
> Local-first • Offline-safe • Minimal • Deterministic • No new dependencies

---------------------------------------------------------------------


FRONTEND IMPLEMENTATION RULES

You must:

- Keep all timer calculations sourced from backend data already provided.
- Avoid duplicating business logic in JavaScript.
- Maintain responsive layout (mobile → desktop).
- Preserve accessibility and readability.
- Ensure graceful rendering when:
  - no active session
  - session just completed
  - backend temporarily unavailable.

Do NOT:

- Introduce frameworks or libraries.
- Modify analytics, charts, or gamification logic.
- Change existing countdown behavior.

---------------------------------------------------------------------

TESTING REQUIREMENTS

Since backend is unchanged:

- Do NOT create backend tests unless absolutely necessary.

Frontend validation must include:

- Manual browser verification.
- Responsive layout checks.
- Correct color transitions at:
  - <50%
  - 50-80%
  - >80%.
- If possible frontend unit tests for any new JavaScript logic (optional, not required).

---------------------------------------------------------------------

DEFINITION OF DONE

Task is complete ONLY if:

- Whatever is asked in the sub-phase description is done 
- Countdown timer unchanged and working.
- Correct color-coding applied.
- Layout responsive across screen sizes.
- No console errors.
- No regression in Phases 1-6.
- QA verdict would be APPROVED.

---------------------------------------------------------------------

OUTPUT FORMAT (STRICT)

Respond in this exact order:

1. Task 7.1 Understanding  
2. UI/UX Design Plan  
3. HTML Changes  
4. CSS Changes  
5. JavaScript Changes  
6. Manual Verification Steps  
7. Validation vs Acceptance Criteria  
8. Regression Safety Confirmation  

Do NOT proceed to Task , only focus on current task.
NOTE : The current implementation should not break the existing countdown timer or any other functionality.

Begin implementation now.