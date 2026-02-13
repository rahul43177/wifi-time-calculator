# DailyFour - UI Refresh Action Plan

**Project:** Transform to professional, designer-quality interface
**Codename:** Project Polish
**Status:** Ready to start

---

## Overview

After 30 hours of development, DailyFour deserves a premium presentation. This plan removes emoji clutter, fixes dark mode issues, and implements a professional design system.

**Goals:**
1. Fix critical UX bugs (dark mode navigation)
2. Remove all emoji decorations
3. Rebrand to "DailyFour"
4. Implement professional typography & color system
5. Achieve Notion/Linear-level visual quality

---

## Phase 8: Critical Fixes & Rebranding

**Priority:** URGENT
**Estimated Time:** 1-2 hours
**Dependencies:** None

### Task 8.1: Fix Dark Mode Navigation Buttons ⚠️ CRITICAL

**Description:** Navigation arrows (`← →`) are invisible in dark mode, breaking UX

**Problem:**
```css
/* Current - broken */
.btn-secondary {
  color: var(--muted); /* Too low contrast in dark mode */
}
```

**Acceptance Criteria:**
- [ ] `← →` buttons clearly visible in dark mode
- [ ] Hover state shows clear feedback
- [ ] Maintains accessibility (WCAG AA)
- [ ] Works on both Weekly and Monthly tabs
- [ ] Focus indicators visible

**Implementation:**
```css
/* Fix approach */
.btn-secondary {
  background: var(--card-bg);
  color: var(--text);
  border: 1px solid var(--border);
  min-width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-secondary:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: var(--primary);
  color: var(--primary);
}

[data-theme="dark"] .btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: var(--text);
}

[data-theme="dark"] .btn-secondary:hover {
  background: rgba(99, 102, 241, 0.15);
  border-color: var(--primary);
}
```

**Files to modify:**
- `static/style.css` (lines ~820-850, button styles)

**Testing:**
- [ ] Toggle dark mode and verify arrows visible
- [ ] Test hover states in both modes
- [ ] Verify keyboard focus indicators
- [ ] Check on Weekly and Monthly tabs

---

### Task 8.2: Remove Emojis from Status Cards

**Description:** Replace emoji icons with professional indicators

**Current State:**
- 🌐 Connection
- ⏱️ Session
- 📊 Today's Total
- 🎯 Target Progress

**Acceptance Criteria:**
- [ ] All emoji icons removed from status cards
- [ ] Replaced with colored dot indicators or removed entirely
- [ ] Visual hierarchy maintained
- [ ] Cards still distinguishable

**Implementation:**

**Option A: Colored Indicators**
```html
<!-- BEFORE -->
<span aria-hidden="true">🌐</span>

<!-- AFTER -->
<span class="status-indicator status-connected"></span>
```

```css
.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}

.status-connected {
  background: var(--success);
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.15);
}

.status-disconnected {
  background: var(--text-secondary);
  opacity: 0.5;
}
```

**Option B: Remove Icons Entirely**
Just rely on card labels - modern apps often do this (Notion, Linear)

**Files to modify:**
- `templates/index.html` (lines ~44-89, status cards section)
- `static/style.css` (add status-indicator styles)

**Testing:**
- [ ] Visual check - cards still clear without emojis
- [ ] Color indicators work in both light/dark modes
- [ ] Accessibility preserved (indicators are decorative)

---

### Task 8.3: Remove Emojis from Gamification

**Description:** Professional badge system without emoji clutter

**Current State:**
- Streaks: 🔥 🏆 ⭐
- Achievements: 🌅 🏃 🔥 ⭐

**Acceptance Criteria:**
- [ ] All emojis removed from streak display
- [ ] All emojis removed from achievement badges
- [ ] Replaced with text badges or initials
- [ ] Earned vs locked state still clear

**Implementation:**

**Streak Display:**
```html
<!-- BEFORE -->
<span class="streak-icon" aria-hidden="true">🔥</span>

<!-- AFTER -->
<div class="streak-badge streak-badge-current">
  <span class="streak-value">5</span>
  <span class="streak-label">Current Streak</span>
</div>
```

**Achievement Badges:**
```html
<!-- BEFORE -->
<div class="achievement-icon locked" aria-hidden="true">🌅</div>

<!-- AFTER -->
<div class="achievement-badge" data-badge="EB">
  <span>EB</span>
</div>
```

```css
.achievement-badge {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  background: var(--card-bg);
  border: 2px solid var(--border);
  color: var(--text-secondary);
}

.achievement.earned .achievement-badge {
  background: var(--success);
  color: white;
  border-color: var(--success);
}
```

**Badge Codes:**
- Early Bird → "EB"
- Marathon Runner → "MR"
- Consistent → "CS"
- Dedicated → "DD"

**Files to modify:**
- `templates/index.html` (lines ~118-185, gamification section)
- `static/style.css` (lines ~927-1100, gamification styles)

**Testing:**
- [ ] Badges render correctly
- [ ] Earned state visually distinct from locked
- [ ] Works in both light/dark modes
- [ ] Initials are clear and readable

---

### Task 8.4: Remove Emojis from Contextual Messages

**Description:** Clean text-only status messages

**Current Examples:**
- "Target completed! 🎉 Great work today"
- "Three quarters done! 🚀 Almost there"
- "Halfway there! 🎯 You're doing great"
- "Good morning! 🌅 At this pace..."
- "Afternoon progress! Keep it up 💪"
- "Evening session! Stay focused 🌙"
- "Final stretch! 💯 Just a bit more"

**Acceptance Criteria:**
- [ ] All emojis removed from contextual messages
- [ ] Messages still encouraging and clear
- [ ] Punctuation and tone maintained
- [ ] No loss of meaning

**Implementation:**
```javascript
// BEFORE
message = "Target completed! 🎉 Great work today";

// AFTER
message = "Target completed! Great work today.";
```

**Cleaned Messages:**
- "Target completed! Great work today."
- "Three quarters done. Almost there."
- "Halfway there. You're doing great."
- "Good morning. At this pace, you'll reach your goal by 2:30 PM."
- "Afternoon progress. Keep it up."
- "Evening session. Stay focused."
- "Final stretch. Just a bit more."

**Files to modify:**
- `static/app.js` (lines ~1189-1225, renderContextualMessage function)

**Testing:**
- [ ] Messages display without emojis
- [ ] Tone still encouraging
- [ ] No strange punctuation/spacing
- [ ] Works across all progress states

---

### Task 8.5: Rebrand to "DailyFour"

**Description:** Update all branding from "Office Wi-Fi Tracker" to "DailyFour"

**Acceptance Criteria:**
- [ ] Page title changed
- [ ] Header/h1 changed
- [ ] Meta tags updated
- [ ] README updated
- [ ] No references to old name in user-facing text

**Files to modify:**
- `templates/index.html` (lines ~6, ~13, title and h1)
- `README.md` (all references)
- `app/main.py` (line ~277-279, FastAPI app metadata)

**Implementation:**
```html
<!-- BEFORE -->
<title>Office Wi-Fi Tracker</title>
<h1 class="title">Office Wi-Fi Tracker</h1>

<!-- AFTER -->
<title>DailyFour - Track Your 4 Hours</title>
<h1 class="title">DailyFour</h1>
```

```python
# BEFORE
app = FastAPI(
    title="Office Wi-Fi 4-Hour Tracker",
    description="Local automation tool for tracking office presence",
    version="0.1.0"
)

# AFTER
app = FastAPI(
    title="DailyFour",
    description="Simple time tracking for your daily 4-hour work goal",
    version="1.0.0"
)
```

**Testing:**
- [ ] Browser tab shows "DailyFour"
- [ ] Header shows new name
- [ ] OpenAPI docs show new branding
- [ ] README reflects new name

---

### ✅ Phase 8 Definition of Done

**Critical Fixes:**
- [x] Dark mode navigation buttons visible and functional
- [x] All emojis removed from status cards
- [x] All emojis removed from gamification
- [x] All emojis removed from messages
- [x] Rebranded to "DailyFour" throughout

**Quality Gates:**
- [ ] All 584 tests still passing
- [ ] Visual QA in both light and dark modes
- [ ] No regressions in existing functionality
- [ ] Professional appearance confirmed

---

## Phase 9: Design System Foundation

**Priority:** HIGH
**Estimated Time:** 2-3 hours
**Dependencies:** Phase 8 complete

### Task 9.1: Implement Typography System

**Description:** Professional font stack and type scale

**Acceptance Criteria:**
- [ ] System font stack implemented
- [ ] Type scale defined (xs, sm, base, lg, xl, 2xl)
- [ ] Font weights standardized (400, 500, 600, 700)
- [ ] All text elements use new system
- [ ] Monospace for data/times

**Implementation:**
```css
:root {
  /* Font families */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI",
               "Helvetica Neue", Arial, sans-serif;
  --font-mono: "SF Mono", "Monaco", "Consolas",
               "Liberation Mono", monospace;

  /* Type scale */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */

  /* Font weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  /* Line heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
}

h1, h2, h3 {
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
}

h1 { font-size: var(--text-2xl); }
h2 { font-size: var(--text-xl); }
h3 { font-size: var(--text-lg); }

.timer-countdown,
.elapsed-time,
.duration {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}
```

**Files to modify:**
- `static/style.css` (lines ~1-100, root variables and base styles)

**Testing:**
- [ ] Fonts render correctly across browsers
- [ ] Type scale is consistent
- [ ] Numbers/times use monospace
- [ ] Hierarchy is clear

---

### Task 9.2: Refine Color Palette

**Description:** Higher contrast, semantic colors

**Acceptance Criteria:**
- [ ] Light mode colors have high contrast (WCAG AAA where possible)
- [ ] Dark mode colors have high contrast
- [ ] Semantic colors (success, warning, error) clearly defined
- [ ] Primary accent color professional (indigo/blue)
- [ ] Smooth transitions between modes

**Implementation:**
```css
:root {
  /* Neutrals - Light Mode */
  --bg: #ffffff;
  --card-bg: #ffffff;
  --text: #0f172a;           /* Slate 900 - high contrast */
  --text-secondary: #475569; /* Slate 600 - readable */
  --border: #e2e8f0;         /* Slate 200 */

  /* Primary */
  --primary: #4f46e5;        /* Indigo 600 - professional */
  --primary-hover: #4338ca;  /* Indigo 700 */
  --primary-light: #eef2ff;  /* Indigo 50 */

  /* Semantic */
  --success: #059669;        /* Emerald 600 */
  --success-light: #d1fae5;  /* Emerald 100 */
  --warning: #d97706;        /* Amber 600 */
  --warning-light: #fef3c7;  /* Amber 100 */
  --error: #dc2626;          /* Red 600 */
  --error-light: #fee2e2;    /* Red 100 */

  /* Deprecated (remove old emoji colors) */
  --green: var(--success);
  --green-light: var(--success-light);
  --green-dark: #047857;     /* Keep for compatibility */
}

[data-theme="dark"] {
  /* Neutrals - Dark Mode */
  --bg: #0f172a;             /* Slate 900 */
  --card-bg: #1e293b;        /* Slate 800 */
  --text: #f1f5f9;           /* Slate 100 - high contrast */
  --text-secondary: #cbd5e1; /* Slate 300 - readable */
  --border: #334155;         /* Slate 700 */

  /* Primary - lighter in dark mode */
  --primary: #6366f1;        /* Indigo 500 */
  --primary-hover: #818cf8;  /* Indigo 400 */
  --primary-light: #1e1b4b;  /* Indigo 950 */

  /* Semantic - adjusted for dark */
  --success: #10b981;        /* Emerald 500 */
  --success-light: #064e3b;  /* Emerald 900 */
  --warning: #f59e0b;        /* Amber 500 */
  --warning-light: #78350f;  /* Amber 900 */
  --error: #ef4444;          /* Red 500 */
  --error-light: #7f1d1d;    /* Red 900 */
}
```

**Files to modify:**
- `static/style.css` (lines ~1-50, CSS custom properties)

**Testing:**
- [ ] Contrast ratios verified (use WebAIM contrast checker)
- [ ] Both modes look professional
- [ ] Colors have clear meaning (green=good, red=bad)
- [ ] Smooth toggle between light/dark

---

### Task 9.3: Spacing System

**Description:** Consistent spacing on 4px/8px grid

**Acceptance Criteria:**
- [ ] All spacing values use system
- [ ] Consistent padding/margins
- [ ] Clear visual rhythm
- [ ] Responsive spacing for mobile

**Implementation:**
```css
:root {
  /* Spacing scale (4px base) */
  --space-0: 0;
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-5: 1.25rem;  /* 20px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-10: 2.5rem;  /* 40px */
  --space-12: 3rem;    /* 48px */
  --space-16: 4rem;    /* 64px */

  /* Common patterns */
  --gap-sm: var(--space-2);
  --gap-md: var(--space-4);
  --gap-lg: var(--space-6);

  --padding-sm: var(--space-3);
  --padding-md: var(--space-4);
  --padding-lg: var(--space-6);
}

.card {
  padding: var(--padding-lg);
  margin-bottom: var(--space-6);
}

.status-cards-grid {
  gap: var(--gap-md);
}
```

**Files to modify:**
- `static/style.css` (spacing variables and component updates)

**Testing:**
- [ ] Visual consistency check
- [ ] Elements feel balanced
- [ ] Mobile spacing appropriate

---

### ✅ Phase 9 Definition of Done

**Design System:**
- [x] Typography system implemented and documented
- [x] Color palette refined with high contrast
- [x] Spacing system on 4px grid
- [x] All components use design tokens

**Quality Gates:**
- [ ] 584 tests passing
- [ ] Design system documented
- [ ] Both modes look professional
- [ ] Consistent spacing throughout

---

## Phase 10: Component Refinement

**Priority:** MEDIUM
**Estimated Time:** 2-3 hours
**Dependencies:** Phase 9 complete

### Task 10.1: Status Cards Visual Update

**Description:** Cleaner card design with better hierarchy

**Acceptance Criteria:**
- [ ] Cards use new typography system
- [ ] Clear visual hierarchy (label → value → detail)
- [ ] Subtle hover states
- [ ] Better spacing within cards

**Implementation:**
```css
.status-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: var(--padding-lg);
  transition: all 0.2s ease;
}

.status-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.status-card-label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.status-card-value {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  color: var(--text);
  line-height: var(--leading-tight);
  margin-bottom: var(--space-1);
}

.status-card-detail {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}
```

**Files to modify:**
- `static/style.css` (lines ~650-750, status card styles)

**Testing:**
- [ ] Cards render cleanly
- [ ] Hover states smooth
- [ ] Mobile responsive

---

### Task 10.2: Timer Section Refinement

**Description:** Better visual hierarchy for timer display

**Acceptance Criteria:**
- [ ] Elapsed/target display more prominent
- [ ] Countdown uses monospace font
- [ ] Progress bar has subtle animation
- [ ] Completion state celebrated (without emoji)

**Implementation:**
```css
.elapsed-display {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  color: var(--text);
  margin: var(--space-4) 0;
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}

.elapsed-time {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.timer-countdown {
  font-family: var(--font-mono);
  font-size: var(--text-xl);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.progress-fill {
  transition: width 0.3s ease, background-color 0.3s ease;
}
```

**Files to modify:**
- `static/style.css` (lines ~400-550, timer styles)

**Testing:**
- [ ] Timer displays clearly
- [ ] Progress bar animates smoothly
- [ ] Works in both modes

---

### Task 10.3: Table Styling

**Description:** Modern table design for session lists

**Acceptance Criteria:**
- [ ] Cleaner row styling
- [ ] Better hover states
- [ ] Zebra striping subtle
- [ ] Mobile responsive

**Implementation:**
```css
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

thead th {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-secondary);
  text-align: left;
  padding: var(--space-3) var(--space-4);
  border-bottom: 2px solid var(--border);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: rgba(99, 102, 241, 0.05);
}

tbody td {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
}
```

**Files to modify:**
- `static/style.css` (lines ~760-820, table styles)

**Testing:**
- [ ] Tables look modern
- [ ] Hover feedback clear
- [ ] Mobile scrolling works

---

### Task 10.4: Chart Polish

**Description:** Cleaner chart styling without emoji legends

**Acceptance Criteria:**
- [ ] Legend items use colored squares (no emoji)
- [ ] Tooltip styling matches design system
- [ ] Grid lines subtle
- [ ] Colors semantic (green=good, red=behind)

**Implementation:**
```javascript
// Chart.js options update
const chartOptions = {
  plugins: {
    legend: {
      labels: {
        usePointStyle: true,
        pointStyle: 'circle',
        font: {
          family: getComputedStyle(document.documentElement)
            .getPropertyValue('--font-sans').trim(),
          size: 14,
          weight: 500
        },
        color: getComputedStyle(document.documentElement)
          .getPropertyValue('--text').trim(),
        // Remove emoji from labels
        generateLabels: (chart) => {
          const labels = Chart.defaults.plugins.legend.labels.generateLabels(chart);
          // Clean up any emoji in label text
          labels.forEach(label => {
            label.text = label.text.replace(/[\u{1F300}-\u{1F9FF}]/gu, '').trim();
          });
          return labels;
        }
      }
    },
    tooltip: {
      backgroundColor: isDarkMode()
        ? 'rgba(30, 41, 59, 0.95)'  // --card-bg dark
        : 'rgba(255, 255, 255, 0.95)',
      titleColor: 'var(--text)',
      bodyColor: 'var(--text-secondary)',
      borderColor: 'var(--border)',
      borderWidth: 1,
      padding: 12,
      cornerRadius: 8,
      titleFont: {
        size: 14,
        weight: 600
      },
      bodyFont: {
        size: 13,
        weight: 400
      }
    }
  }
};
```

**Files to modify:**
- `static/app.js` (lines ~443-670, chart creation functions)

**Testing:**
- [ ] Charts render cleanly
- [ ] No emojis in legends
- [ ] Tooltips match design system
- [ ] Works in both modes

---

### ✅ Phase 10 Definition of Done

**Components:**
- [x] Status cards refined
- [x] Timer section polished
- [x] Tables modernized
- [x] Charts cleaned up

**Quality Gates:**
- [ ] 584 tests passing
- [ ] Visual consistency across components
- [ ] Professional appearance
- [ ] No emoji remnants

---

## Phase 11: Polish & Testing

**Priority:** MEDIUM
**Estimated Time:** 2 hours
**Dependencies:** Phase 10 complete

### Task 11.1: Button System Consistency

**Description:** Standardize all button styles

**Acceptance Criteria:**
- [ ] Primary, secondary, tertiary button styles defined
- [ ] Consistent hover/active/focus states
- [ ] Disabled states if needed
- [ ] Icon buttons (week/month navigation) consistent

**Files to modify:**
- `static/style.css` (button styles consolidation)

---

### Task 11.2: Animation Refinement

**Description:** Smooth, purposeful animations

**Acceptance Criteria:**
- [ ] Page transitions smooth
- [ ] Hover states have subtle motion
- [ ] Progress bar animation refined
- [ ] No janky animations

**Files to modify:**
- `static/style.css` (transition timings)
- `static/app.js` (animation settings)

---

### Task 11.3: Responsive Testing

**Description:** Verify mobile experience

**Acceptance Criteria:**
- [ ] Works on 320px width (iPhone SE)
- [ ] Tablets (768px) look good
- [ ] Desktop (1440px+) uses space well
- [ ] Touch targets adequate (44px min)

**Testing Checklist:**
- [ ] iPhone SE (320px)
- [ ] iPhone 12/13 (390px)
- [ ] iPad (768px)
- [ ] Desktop (1440px)

---

### Task 11.4: Cross-browser QA

**Description:** Test in major browsers

**Acceptance Criteria:**
- [ ] Chrome/Edge (Chromium)
- [ ] Safari (WebKit)
- [ ] Firefox (Gecko)
- [ ] Dark mode works in all
- [ ] No layout breaks

**Testing Checklist:**
- [ ] Chrome latest
- [ ] Safari latest
- [ ] Firefox latest
- [ ] Edge latest

---

### Task 11.5: Accessibility Re-audit

**Description:** Ensure changes maintain WCAG AA

**Acceptance Criteria:**
- [ ] All contrast ratios pass (4.5:1 minimum)
- [ ] Keyboard navigation still works
- [ ] Screen reader announcements unchanged
- [ ] Focus indicators visible
- [ ] No new ARIA violations

**Testing:**
- [ ] Run axe DevTools scan
- [ ] Manual keyboard navigation test
- [ ] VoiceOver/NVDA spot check
- [ ] Contrast checker on new colors

---

### Task 11.6: Performance Check

**Description:** Ensure UI changes don't impact performance

**Acceptance Criteria:**
- [ ] No layout thrashing
- [ ] Animations 60fps
- [ ] Paint/composite performance good
- [ ] Bundle size reasonable

**Testing:**
- [ ] Chrome DevTools Performance tab
- [ ] Lighthouse audit (performance score)
- [ ] Check for forced reflows

---

### ✅ Phase 11 Definition of Done

**Polish:**
- [x] All buttons consistent
- [x] Animations smooth
- [x] Responsive on all screen sizes
- [x] Cross-browser tested
- [x] Accessibility maintained
- [x] Performance verified

**Quality Gates:**
- [ ] 584 tests passing
- [ ] Lighthouse score >90
- [ ] No console errors
- [ ] Professional on all devices

---

## Phase 12: Documentation & Handoff

**Priority:** LOW
**Estimated Time:** 1 hour
**Dependencies:** Phase 11 complete

### Task 12.1: Design System Documentation

**Description:** Document the design system for future reference

**Deliverables:**
- [ ] Color palette reference
- [ ] Typography scale
- [ ] Spacing system
- [ ] Component library
- [ ] Usage guidelines

**File:** `docs/DESIGN_SYSTEM.md`

---

### Task 12.2: Update Screenshots

**Description:** Capture new professional UI

**Deliverables:**
- [ ] Hero screenshot (light mode)
- [ ] Hero screenshot (dark mode)
- [ ] Mobile screenshots
- [ ] Feature highlights

**Location:** `docs/screenshots/` or similar

---

### Task 12.3: Update README

**Description:** Reflect new branding and polish

**Acceptance Criteria:**
- [ ] "DailyFour" branding
- [ ] New screenshots
- [ ] Feature list updated
- [ ] Setup instructions verified

**Files to modify:**
- `README.md`

---

### ✅ Phase 12 Definition of Done

**Documentation:**
- [x] Design system documented
- [x] Screenshots updated
- [x] README reflects new UI
- [x] Handoff complete

---

## Summary & Roadmap

### Quick Start (Minimum Viable Polish)
1. **Phase 8** - Fix critical bugs, remove emojis (~1-2 hours)
2. **Phase 9** - Design system foundation (~2 hours)

**Result:** Professional appearance, no emoji clutter

### Full Implementation (Premium Polish)
3. **Phase 10** - Component refinement (~2-3 hours)
4. **Phase 11** - Polish & testing (~2 hours)
5. **Phase 12** - Documentation (~1 hour)

**Total Time:** ~8-10 hours for complete transformation

---

## Current Status

**Phase 8:** Not started
**Next Action:** Task 8.1 - Fix dark mode navigation buttons

---

## Testing Strategy

After each phase:
1. Run full test suite: `python -m pytest`
2. Visual QA in both light/dark modes
3. Check responsive behavior
4. Verify no regressions

After Phase 11:
1. Full cross-browser test
2. Accessibility audit
3. Performance check
4. User acceptance test

---

## Success Metrics

**Before (Current):**
- ❌ Dark mode navigation broken
- ❌ Emoji clutter throughout
- ❌ Generic "Office Wi-Fi Tracker" branding
- ⚠️ Variable text contrast

**After (Goal):**
- ✅ Fully functional dark mode
- ✅ Professional, emoji-free UI
- ✅ "DailyFour" brand identity
- ✅ High contrast throughout (WCAG AAA where possible)
- ✅ Notion/Linear-level visual quality

---

Ready to start Phase 8?
