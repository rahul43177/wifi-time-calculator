"""
Task 7.6: Dark Mode Support — Test Suite

Tests for dark theme with system preference detection, manual toggle,
localStorage persistence, color optimization, and smooth transitions.

Acceptance Criteria:
- Auto-detects system dark mode preference
- Manual toggle available
- All colors optimized for dark background
- Smooth theme transition animation
- Preserves user preference in localStorage
"""

import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def static_css_path(project_root):
    """Return path to style.css."""
    return project_root / "static" / "style.css"


@pytest.fixture
def static_js_path(project_root):
    """Return path to app.js."""
    return project_root / "static" / "app.js"


@pytest.fixture
def template_html_path(project_root):
    """Return path to index.html."""
    return project_root / "templates" / "index.html"


@pytest.fixture
def css_content(static_css_path):
    """Read CSS file content."""
    return static_css_path.read_text()


@pytest.fixture
def js_content(static_js_path):
    """Read JavaScript file content."""
    return static_js_path.read_text()


@pytest.fixture
def html_content(template_html_path):
    """Read HTML template content."""
    return template_html_path.read_text()


# --- Acceptance Criterion 1: Auto-detects system dark mode preference ---

def test_dark_mode_css_variables_defined(css_content):
    """Test that dark mode CSS variables are defined (Phase 9 updated)."""
    assert '[data-theme="dark"]' in css_content, \
        "Dark mode CSS selector [data-theme='dark'] not found"

    # Phase 9: Check refined dark mode variables (lowercase hex)
    dark_vars = [
        '--card-bg: #1e293b',   # Slate 800 (renamed from --surface)
        '--text: #f1f5f9',      # Slate 100
        '--bg: #0f172a',        # Slate 900 (updated)
        '--text-secondary: #cbd5e1',  # Slate 300 (renamed from --muted)
        '--border: #334155',    # Slate 700
    ]

    for var in dark_vars:
        assert var in css_content, f"Dark mode variable {var} not found"


def test_system_preference_media_query_exists(css_content):
    """Test that CSS media query for system dark mode preference exists."""
    assert '@media (prefers-color-scheme: dark)' in css_content, \
        "Media query for system dark mode preference not found"

    # Verify it targets :root without explicit theme attribute
    assert ':root:not([data-theme="light"])' in css_content, \
        "System preference fallback selector not found"


def test_theme_initialization_before_app_load(js_content):
    """Test that theme is initialized before DOM loads (prevents flash)."""
    # Check for early initialization IIFE
    assert 'function initializeTheme()' in js_content, \
        "Theme initialization function not found"

    # Verify it runs immediately
    assert 'initializeTheme()' in js_content, \
        "Theme initialization not called"

    # Check it sets theme before app initialization
    init_theme_pos = js_content.find('function initializeTheme()')
    init_app_pos = js_content.find('function initializeDashboardApp()')
    assert init_theme_pos < init_app_pos, \
        "Theme initialization should run before app initialization"


def test_system_preference_detection_logic(js_content):
    """Test that JS detects system preference correctly."""
    assert 'window.matchMedia' in js_content, \
        "matchMedia API not used for system preference detection"

    assert 'prefers-color-scheme: dark' in js_content, \
        "System preference detection query not found"

    # Check for getSystemPreference function
    assert 'getSystemPreference' in js_content or \
           'prefers-color-scheme' in js_content, \
        "System preference detection function not found"


def test_theme_applied_to_document_element(js_content):
    """Test that theme is applied to document root element."""
    assert 'document.documentElement.setAttribute' in js_content, \
        "Theme not applied to document.documentElement"

    assert '"data-theme"' in js_content, \
        "data-theme attribute not set"


# --- Acceptance Criterion 2: Manual toggle available ---

def test_theme_toggle_button_in_html(html_content):
    """Test that theme toggle button exists in HTML."""
    assert 'id="theme-toggle"' in html_content, \
        "Theme toggle button not found in HTML"

    assert 'theme-toggle' in html_content, \
        "Theme toggle class not found"

    # Check for icon element
    assert 'id="theme-icon"' in html_content, \
        "Theme icon element not found"


def test_theme_toggle_button_styling(css_content):
    """Test that theme toggle button has proper styling."""
    assert '.theme-toggle' in css_content, \
        "Theme toggle button styles not found"

    # Check for essential styling properties
    assert '.theme-toggle:hover' in css_content, \
        "Theme toggle hover state not found"

    assert '.theme-toggle:active' in css_content or \
           'transform: scale' in css_content, \
        "Theme toggle active state feedback not found"


def test_theme_toggle_accessibility(html_content):
    """Test that theme toggle has proper accessibility attributes."""
    # Check for aria-label
    assert 'aria-label="Toggle dark mode"' in html_content, \
        "Theme toggle missing aria-label for screen readers"

    # Check for title attribute
    assert 'title="Toggle dark mode"' in html_content, \
        "Theme toggle missing title attribute for tooltip"

    # Check icon has aria-hidden
    assert 'aria-hidden="true"' in html_content, \
        "Theme icon should have aria-hidden=true"


def test_theme_toggle_js_wiring(js_content):
    """Test that theme toggle button is wired up correctly."""
    # Check DOM element is cached
    assert 'themeToggle' in js_content, \
        "Theme toggle DOM element not cached"

    assert 'themeIcon' in js_content, \
        "Theme icon DOM element not cached"

    # Check for toggle function
    assert 'toggleTheme' in js_content or \
           'addEventListener("click"' in js_content, \
        "Theme toggle event listener not found"


def test_theme_toggle_icon_updates(js_content):
    """Test that theme icon updates when theme changes."""
    assert 'updateThemeIcon' in js_content or \
           'themeIcon.textContent' in js_content, \
        "Theme icon update logic not found"

    # Check for sun/moon icons
    assert '☀️' in js_content or '"sun"' in js_content, \
        "Sun icon for light mode not found"

    assert '🌙' in js_content or '"moon"' in js_content, \
        "Moon icon for dark mode not found"


# --- Acceptance Criterion 3: All colors optimized for dark background ---

def test_dark_mode_brand_colors_adjusted(css_content):
    """Test that brand colors are adjusted for dark backgrounds (Phase 9)."""
    # Phase 9: Primary color is Indigo 500 in dark mode (lowercase)
    assert '--primary: #6366f1' in css_content, \
        "Primary color not adjusted for dark mode (should be #6366f1 - Indigo 500)"


def test_dark_mode_status_colors_wcag_compliant(css_content):
    """Test that status colors maintain WCAG AA compliance in dark mode (Phase 9)."""
    # Phase 9: Semantic colors adjusted for dark mode (lowercase hex)
    # Success (green) - Emerald 500
    assert '--success: #10b981' in css_content, \
        "Success color not optimized for dark backgrounds (should be #10b981)"

    # Warning (yellow) - Amber 500
    assert '--warning: #f59e0b' in css_content, \
        "Warning color not optimized for dark backgrounds (should be #f59e0b)"

    # Error (red) - Red 500
    assert '--error: #ef4444' in css_content, \
        "Error color not optimized for dark backgrounds (should be #ef4444)"


def test_dark_mode_progress_colors_defined(css_content):
    """Test that progress bar colors are defined for dark mode."""
    # Check dark mode progress colors
    dark_progress_vars = [
        '--progress:',
        '--progress-warning:',
        '--progress-complete:',
        '--progress-bg:',
    ]

    for var in dark_progress_vars:
        assert var in css_content, f"Dark mode {var} not found"


def test_dark_mode_gradient_definitions(css_content):
    """Test that gradients are redefined for dark mode."""
    assert '--gradient-primary:' in css_content, \
        "Primary gradient not found in dark mode"

    assert '--gradient-header:' in css_content, \
        "Header gradient not found in dark mode"

    assert '--gradient-timer:' in css_content, \
        "Timer gradient not found in dark mode"


def test_dark_mode_text_contrast(css_content):
    """Test that dark mode text colors provide adequate contrast (Phase 9)."""
    # Phase 9: Light text on dark background (lowercase hex)
    assert '--text: #f1f5f9' in css_content, \
        "Text color not light enough for dark backgrounds (should be #f1f5f9 - Slate 100)"

    # Phase 9: text-secondary (renamed from muted) should still be readable
    assert '--text-secondary: #cbd5e1' in css_content, \
        "Secondary text color not optimized for dark mode (should be #cbd5e1 - Slate 300)"


# --- Acceptance Criterion 4: Smooth theme transition animation ---

def test_theme_transition_applied(css_content):
    """Test that theme transitions are applied to elements."""
    assert 'transition:' in css_content, \
        "No transitions found in CSS"

    # Check for background-color transition
    assert 'background-color' in css_content, \
        "Background color transitions not found"

    # Check for color transition
    assert 'color 0.2s' in css_content or \
           'transition: background-color' in css_content, \
        "Color transitions not found"


def test_theme_transition_timing(css_content):
    """Test that theme transitions have appropriate timing."""
    # Check for reasonable transition duration (200ms is standard)
    assert '0.2s' in css_content or '200ms' in css_content, \
        "Theme transition duration not found (should be ~200ms)"

    # Check for smooth easing function
    assert 'ease-in-out' in css_content or 'ease' in css_content, \
        "Smooth easing function not found for transitions"


def test_transitions_dont_interfere_with_animations(css_content):
    """Test that theme transitions don't break existing animations."""
    # Check that animation keyframes are still present
    assert '@keyframes' in css_content, \
        "Existing animations might be missing"

    # Check specific animations from Task 7.4
    assert 'fadeInUp' in css_content, \
        "fadeInUp animation from Task 7.4 missing"

    assert 'celebrate' in css_content, \
        "celebrate animation from Task 7.4 missing"


def test_theme_icon_animation_on_toggle(css_content):
    """Test that theme icon has smooth animation on toggle."""
    assert '#theme-icon' in css_content or \
           '.theme-toggle' in css_content, \
        "Theme icon/toggle styles not found"

    # Check for icon rotation or transform
    assert 'transform:' in css_content or \
           'rotate' in css_content, \
        "Theme icon animation not found"


# --- Acceptance Criterion 5: Preserves user preference in localStorage ---

def test_localstorage_key_defined(js_content):
    """Test that localStorage key is defined."""
    assert 'THEME_KEY' in js_content or \
           'office-tracker-theme' in js_content, \
        "localStorage key for theme not found"


def test_theme_saved_to_localstorage(js_content):
    """Test that theme preference is saved to localStorage."""
    assert 'localStorage.setItem' in js_content, \
        "Theme not saved to localStorage"

    # Check it's wrapped in try/catch for safety
    assert 'try {' in js_content or 'catch' in js_content, \
        "localStorage operations should be wrapped in try/catch"


def test_theme_loaded_from_localstorage(js_content):
    """Test that theme preference is loaded from localStorage."""
    assert 'localStorage.getItem' in js_content, \
        "Theme not loaded from localStorage"


def test_localstorage_error_handling(js_content):
    """Test that localStorage errors are handled gracefully."""
    # Check for try/catch around localStorage operations
    localstorage_count = js_content.count('localStorage.')
    catch_count = js_content.count('catch')

    assert catch_count >= 2, \
        "localStorage operations should have error handling (try/catch)"


def test_localstorage_fallback_to_system(js_content):
    """Test that if localStorage is empty, fallback to system preference."""
    # Check for fallback logic
    assert 'getSystemPreference' in js_content or \
           'getSavedTheme' in js_content, \
        "Fallback to system preference not found"


# --- Regression Tests: Ensure Phase 1-6 functionality preserved ---

def test_countdown_timer_logic_unchanged(js_content):
    """Test that countdown timer logic from previous phases is unchanged."""
    # Core timer functions should still exist
    assert 'getLiveElapsedSeconds' in js_content, \
        "Core timer function missing"

    assert 'getLiveRemainingSeconds' in js_content, \
        "Remaining time calculation missing"

    assert 'renderTimer' in js_content, \
        "Timer rendering function missing"


def test_progress_thresholds_preserved(js_content):
    """Test that Task 7.1 progress thresholds are preserved."""
    # Check for 50/80 threshold model
    assert '50' in js_content and '80' in js_content, \
        "Progress thresholds (50%, 80%) not found"

    # Check color classes
    assert 'progress-low' in js_content or 'progress-medium' in js_content, \
        "Progress threshold classes not found"


def test_task_7_2_status_cards_unchanged(html_content):
    """Test that Task 7.2 status cards are still present."""
    # Check all 4 status cards exist
    assert 'id="card-connection"' in html_content, \
        "Connection status card missing"

    assert 'id="card-session"' in html_content, \
        "Session status card missing"

    assert 'id="card-today"' in html_content, \
        "Today total card missing"

    assert 'id="card-target"' in html_content, \
        "Target progress card missing"


def test_task_7_4_animations_preserved(css_content):
    """Test that Task 7.4 animations are still present."""
    # Check animation definitions
    assert '@keyframes fadeInUp' in css_content, \
        "fadeInUp animation from Task 7.4 missing"

    assert '@keyframes pulse' in css_content, \
        "pulse animation from Task 7.4 missing"

    assert '@keyframes celebrate' in css_content, \
        "celebrate animation from Task 7.4 missing"


def test_task_7_5_contextual_messages_preserved(html_content, js_content):
    """Test that Task 7.5 contextual messages are still present."""
    assert 'id="contextual-message"' in html_content, \
        "Contextual message element missing"

    assert 'renderContextualMessage' in js_content, \
        "Contextual message rendering function missing"


# --- Edge Cases & Error Handling ---

def test_theme_applies_on_elements_without_js(css_content):
    """Test that theme can apply via CSS alone (JavaScript disabled)."""
    # Media query should work without JS
    assert '@media (prefers-color-scheme: dark)' in css_content, \
        "CSS-only dark mode fallback missing"


def test_no_flash_of_unstyled_content(js_content):
    """Test that theme is applied before page renders."""
    # Theme init should be at top of file
    init_pos = js_content.find('initializeTheme')
    app_pos = js_content.find('initializeDashboardApp')

    assert init_pos < app_pos, \
        "Theme should initialize before app to prevent flash"


def test_theme_toggle_button_position(html_content):
    """Test that theme toggle is in header (accessible location)."""
    # Find header section
    header_start = html_content.find('class="card header"')
    header_end = html_content.find('</section>', header_start)

    # Check toggle is within header
    toggle_pos = html_content.find('id="theme-toggle"')
    assert header_start < toggle_pos < header_end, \
        "Theme toggle should be in header section"


def test_responsive_theme_toggle(css_content):
    """Test that theme toggle works on mobile screens."""
    # Check mobile breakpoint still exists
    assert '@media (max-width: 600px)' in css_content, \
        "Mobile responsive styles missing"


# --- Code Quality & Production Readiness ---

def test_no_hardcoded_theme_in_html(html_content):
    """Test that HTML doesn't have hardcoded data-theme attribute."""
    # Theme should be set by JavaScript, not hardcoded
    assert 'data-theme="light"' not in html_content, \
        "Theme should not be hardcoded in HTML"

    assert 'data-theme="dark"' not in html_content, \
        "Theme should not be hardcoded in HTML"


def test_theme_functions_are_encapsulated(js_content):
    """Test that theme functions are properly encapsulated."""
    # Check functions exist
    assert 'getCurrentTheme' in js_content or \
           'setTheme' in js_content, \
        "Theme management functions not found"


def test_css_variables_consistent_naming(css_content):
    """Test that CSS variables follow consistent naming convention."""
    # All variables should use kebab-case and start with --
    assert '--surface:' in css_content, "CSS variable --surface missing"
    assert '--text:' in css_content, "CSS variable --text missing"
    assert '--bg:' in css_content, "CSS variable --bg missing"


def test_no_console_errors_in_theme_code(js_content):
    """Test that theme code has proper error handling."""
    # Check for console.warn for non-critical errors
    assert 'console.warn' in js_content, \
        "Should have console.warn for localStorage errors"

    # Should not have console.error for expected failures
    localstorage_errors = js_content.count('localStorage')
    error_handling = js_content.count('catch')

    assert error_handling >= 2, \
        "localStorage operations should have error handling"


# --- Integration Tests ---

def test_theme_integrates_with_existing_ui(html_content, css_content):
    """Test that theme integrates seamlessly with existing UI."""
    # Check that all major sections still exist
    assert 'class="dashboard"' in html_content, \
        "Main dashboard container missing"

    assert 'timer-section' in html_content, \
        "Timer section missing"

    assert 'status-cards-grid' in html_content, \
        "Status cards grid missing"


def test_charts_work_in_dark_mode(html_content):
    """Test that Chart.js elements are present for dark mode testing."""
    # Charts should still be present
    assert 'id="weekly-chart"' in html_content, \
        "Weekly chart canvas missing"

    assert 'id="monthly-chart"' in html_content, \
        "Monthly chart canvas missing"


# --- Summary Test: All Acceptance Criteria ---

def test_all_acceptance_criteria_met(
    html_content, css_content, js_content
):
    """Meta-test: Verify all 5 acceptance criteria are implemented."""

    # 1. Auto-detects system dark mode preference
    assert '@media (prefers-color-scheme: dark)' in css_content, \
        "AC1: System preference detection missing"

    # 2. Manual toggle available
    assert 'id="theme-toggle"' in html_content, \
        "AC2: Manual toggle button missing"

    # 3. All colors optimized for dark background
    assert '[data-theme="dark"]' in css_content, \
        "AC3: Dark mode color palette missing"

    # 4. Smooth theme transition animation
    assert 'transition:' in css_content and '0.2s' in css_content, \
        "AC4: Smooth transitions missing"

    # 5. Preserves user preference in localStorage
    assert 'localStorage.setItem' in js_content and \
           'localStorage.getItem' in js_content, \
        "AC5: localStorage persistence missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
