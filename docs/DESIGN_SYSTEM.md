# DailyFour Design System

## Purpose
This document defines the visual system for DailyFour so UI updates remain consistent, accessible, and professional across light/dark themes.

## Principles
- Clarity first: surface session progress and timing data with minimal visual noise.
- Semantic color meaning: success, warning, and error states must be obvious.
- Numeric readability: all timers and duration-heavy values use tabular mono digits.
- Accessibility baseline: WCAG AA contrast, keyboard-visible focus, and non-text icon parity.
- Emoji-free interface: user-facing UI uses text, badges, and vector/CSS icons only.

## Theme Tokens
Primary token source: `/Users/rahulmishra/Desktop/Personal/wifi-tracking/static/style.css`

### Core neutrals
- `--bg`, `--card-bg`
- `--text`, `--text-secondary`
- `--border`

### Brand + semantic
- `--primary`, `--primary-hover`, `--primary-light`
- `--success`, `--success-light`
- `--warning`, `--warning-light`
- `--error`, `--error-light`

### Compatibility aliases
Legacy aliases (`--green`, `--yellow`, `--red`, etc.) remain for compatibility and should map to semantic tokens.

## Typography
- Sans stack: `--font-sans`
- Mono stack: `--font-mono`
- Scale: `--text-xs` to `--text-2xl`
- Weights: `--font-normal`, `--font-medium`, `--font-semibold`, `--font-bold`
- Line-height: `--leading-tight`, `--leading-normal`, `--leading-relaxed`

### Required mono usage
- Live elapsed display
- Countdown timer
- Session durations and other dense numeric values

## Spacing System
Spacing uses the 4px grid token set:
- `--space-1` (4px) through `--space-16` (64px)
- Component spacing aliases:
  - `--gap-sm`, `--gap-md`, `--gap-lg`
  - `--padding-sm`, `--padding-md`, `--padding-lg`

Use tokens instead of one-off pixel literals for layout spacing whenever practical.

## Components
### Status cards
- Structure: label -> value -> detail
- Connection and target states are represented through class/state styling, not emoji.

### Timer section
- High emphasis on elapsed vs target.
- Countdown is secondary but always visible.
- Completion is indicated with text and color-state shifts, not decorative emoji.

### Tables
- Tokenized typography/spacing.
- Subtle hover and zebra striping.
- Clear state text (for example `Met` / `Not Met`) instead of emoji symbols.

### Charts
- Colors pulled from semantic tokens.
- Legend labels sanitize emoji characters.
- Tooltips use theme-aware tokenized colors and readable typography.

## Dark Mode Rules
- Theme toggles through `data-theme="light|dark"` on `<html>`.
- Theme icon uses CSS class-based moon/sun rendering (`theme-icon-moon`, `theme-icon-sun`), no emoji glyphs.
- Secondary controls (including weekly/monthly arrow buttons) must maintain AA contrast in dark mode.

## Accessibility Rules
- Keep visible focus styles (`:focus-visible`) on tabs, buttons, and toggles.
- Preserve `aria-label` and live-region behaviors.
- Decorative icons should be `aria-hidden="true"`.

## No-Emoji Policy
User-facing UI in:
- `/Users/rahulmishra/Desktop/Personal/wifi-tracking/templates/index.html`
- `/Users/rahulmishra/Desktop/Personal/wifi-tracking/static/app.js`

must avoid emoji glyphs. Use text labels, CSS/SVG icons, and semantic color states instead.

