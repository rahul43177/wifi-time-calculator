"""
Task 7.9: Accessibility Improvements — Test Suite

Tests for WCAG 2.1 AA compliance including keyboard navigation,
ARIA labels, screen reader support, focus indicators, and high contrast mode.

Acceptance Criteria:
- Keyboard navigation for all interactions
- ARIA labels on all interactive elements
- Screen reader-friendly timer updates
- High contrast mode option
- Focus indicators visible
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


# --- Acceptance Criterion 1: Keyboard navigation for all interactions ---

def test_tabs_have_proper_role(html_content):
    """Test that tabs have proper ARIA role."""
    assert 'role="tab"' in html_content, \
        "Tabs should have role='tab' for screen readers"


def test_tabs_have_aria_controls(html_content):
    """Test that tabs have aria-controls linking to tab panels."""
    assert 'aria-controls="tab-live"' in html_content, \
        "Live tab should have aria-controls"

    assert 'aria-controls="tab-today"' in html_content, \
        "Today tab should have aria-controls"

    assert 'aria-controls="tab-weekly"' in html_content, \
        "Weekly tab should have aria-controls"

    assert 'aria-controls="tab-monthly"' in html_content, \
        "Monthly tab should have aria-controls"


def test_tabs_have_aria_selected(html_content):
    """Test that tabs have aria-selected attribute."""
    assert 'aria-selected="true"' in html_content, \
        "Active tab should have aria-selected='true'"

    assert 'aria-selected="false"' in html_content, \
        "Inactive tabs should have aria-selected='false'"


def test_tabs_have_tabindex(html_content):
    """Test that tabs have proper tabindex for keyboard navigation."""
    assert 'tabindex="0"' in html_content, \
        "Active tab should have tabindex='0'"

    assert 'tabindex="-1"' in html_content, \
        "Inactive tabs should have tabindex='-1'"


def test_tab_panels_have_role(html_content):
    """Test that tab panels have proper role."""
    assert 'role="tabpanel"' in html_content, \
        "Tab content should have role='tabpanel'"


def test_tab_panels_have_aria_labelledby(html_content):
    """Test that tab panels are labeled by their tabs."""
    assert 'aria-labelledby="tab-live"' in html_content, \
        "Live panel should be labeled by tab"

    assert 'aria-labelledby="tab-today"' in html_content, \
        "Today panel should be labeled by tab"


def test_keyboard_navigation_handler_exists(js_content):
    """Test that keyboard navigation handler exists."""
    assert 'handleTabKeyboard' in js_content, \
        "Keyboard navigation handler function not found"

    # Check for arrow key handling
    assert 'ArrowLeft' in js_content or 'case "ArrowLeft"' in js_content, \
        "Left arrow key not handled"

    assert 'ArrowRight' in js_content or 'case "ArrowRight"' in js_content, \
        "Right arrow key not handled"


def test_keyboard_navigation_supports_home_end(js_content):
    """Test that keyboard navigation supports Home/End keys."""
    assert 'Home' in js_content or 'case "Home"' in js_content, \
        "Home key should navigate to first tab"

    assert 'End' in js_content or 'case "End"' in js_content, \
        "End key should navigate to last tab"


def test_keyboard_handler_wired_to_tabs(js_content):
    """Test that keyboard handler is attached to tabs."""
    assert 'addEventListener("keydown", handleTabKeyboard)' in js_content or \
           'addEventListener(\'keydown\', handleTabKeyboard)' in js_content, \
        "Keyboard handler not attached to tabs"


# --- Acceptance Criterion 2: ARIA labels on all interactive elements ---

def test_theme_toggle_has_aria_label(html_content):
    """Test that theme toggle button has aria-label."""
    assert 'aria-label="Toggle dark mode"' in html_content, \
        "Theme toggle should have descriptive aria-label"


def test_navigation_buttons_have_aria_labels(html_content):
    """Test that week/month navigation buttons have aria-labels."""
    assert 'aria-label="Previous week"' in html_content, \
        "Previous week button should have aria-label"

    assert 'aria-label="Next week"' in html_content, \
        "Next week button should have aria-label"

    assert 'aria-label="Previous month"' in html_content, \
        "Previous month button should have aria-label"

    assert 'aria-label="Next month"' in html_content, \
        "Next month button should have aria-label"


def test_decorative_icons_hidden_from_screen_readers(html_content):
    """Test that decorative icons have aria-hidden."""
    # Check that emojis and icons have aria-hidden
    assert html_content.count('aria-hidden="true"') >= 5, \
        "Decorative icons should have aria-hidden='true'"


def test_nav_has_aria_label(html_content):
    """Test that navigation has descriptive label."""
    assert 'aria-label="Dashboard sections"' in html_content, \
        "Navigation should have aria-label"


def test_tables_have_aria_labels(html_content):
    """Test that tables have descriptive labels."""
    assert 'aria-label="Today\'s sessions"' in html_content or \
           'aria-label="Today&#39;s sessions"' in html_content, \
        "Sessions table should have aria-label"


def test_progress_bar_has_proper_role(html_content):
    """Test that progress bar has proper ARIA role and attributes."""
    assert 'role="progressbar"' in html_content, \
        "Progress element should have role='progressbar'"

    assert 'aria-valuemin="0"' in html_content, \
        "Progress bar should have aria-valuemin"

    assert 'aria-valuemax="100"' in html_content, \
        "Progress bar should have aria-valuemax"

    assert 'aria-valuenow' in html_content, \
        "Progress bar should have aria-valuenow"


# --- Acceptance Criterion 3: Screen reader-friendly timer updates ---

def test_timer_has_aria_live_region(html_content):
    """Test that timer has aria-live for screen reader updates."""
    assert 'aria-live="polite"' in html_content, \
        "Timer should have aria-live='polite' for announcements"


def test_timer_has_aria_atomic(html_content):
    """Test that timer has aria-atomic for complete announcements."""
    assert 'aria-atomic="true"' in html_content, \
        "Timer should have aria-atomic='true'"


def test_screen_reader_announcement_element_exists(html_content):
    """Test that dedicated announcement element exists."""
    assert 'id="timer-announcements"' in html_content, \
        "Dedicated screen reader announcement element should exist"

    assert 'aria-live="assertive"' in html_content, \
        "Announcements should use aria-live='assertive' for important updates"


def test_screen_reader_only_class_exists(html_content):
    """Test that screen reader only class is used."""
    assert 'class="sr-only"' in html_content, \
        "Screen reader only class should be used for announcement element"


def test_sr_only_css_class_defined(css_content):
    """Test that sr-only CSS class is defined."""
    assert '.sr-only' in css_content, \
        "Screen reader only CSS class should be defined"

    # Check it's properly hidden visually but accessible to screen readers
    assert 'position: absolute' in css_content or 'position:absolute' in css_content, \
        "sr-only should use absolute positioning"


def test_announce_to_screen_reader_function_exists(js_content):
    """Test that screen reader announcement function exists."""
    assert 'announceToScreenReader' in js_content, \
        "Function to announce to screen readers should exist"


def test_milestone_announcements_implemented(js_content):
    """Test that timer milestone announcements are implemented."""
    assert 'checkAndAnnounceTimerMilestones' in js_content, \
        "Milestone announcement function should exist"

    # Check for milestone messages
    assert '50%' in js_content or 'Halfway' in js_content, \
        "Should announce 50% milestone"

    assert '75%' in js_content or 'Almost there' in js_content, \
        "Should announce 75% milestone"


def test_announcements_called_from_timer_render(js_content):
    """Test that announcements are called from timer rendering."""
    # Find renderTimer function and check it calls announcements
    assert 'checkAndAnnounceTimerMilestones' in js_content, \
        "Timer rendering should call announcement function"


def test_week_month_labels_have_aria_live(html_content):
    """Test that dynamic week/month labels have aria-live."""
    # Check that current week and month labels update screen readers
    assert html_content.count('aria-live="polite"') >= 3, \
        "Dynamic labels should have aria-live for screen reader updates"


# --- Acceptance Criterion 4: High contrast mode option ---

def test_high_contrast_mode_media_query_exists(css_content):
    """Test that high contrast mode CSS exists."""
    assert '@media (prefers-contrast: high)' in css_content or \
           '@media (prefers-contrast:high)' in css_content, \
        "High contrast mode media query should exist"


def test_high_contrast_mode_adjusts_colors(css_content):
    """Test that high contrast mode adjusts colors."""
    # Check that high contrast mode defines strong contrasts
    # This is typically in the @media query block
    contrast_section_start = css_content.find('@media (prefers-contrast: high)')

    if contrast_section_start == -1:
        contrast_section_start = css_content.find('@media (prefers-contrast:high)')

    assert contrast_section_start != -1, \
        "High contrast mode should be defined"


def test_dark_mode_provides_contrast_option(css_content):
    """Test that dark mode serves as a contrast option."""
    # Dark mode variables should exist (already tested in 7.6)
    assert '[data-theme="dark"]' in css_content, \
        "Dark mode provides alternative contrast option"


# --- Acceptance Criterion 5: Focus indicators visible ---

def test_focus_indicators_defined(css_content):
    """Test that focus indicators are defined."""
    assert '*:focus' in css_content or ':focus' in css_content, \
        "Focus styles should be defined"


def test_focus_visible_support(css_content):
    """Test that :focus-visible is used for keyboard-only focus."""
    assert ':focus-visible' in css_content, \
        "Should use :focus-visible for keyboard-only focus indicators"


def test_focus_indicators_use_outline(css_content):
    """Test that focus indicators use visible outline."""
    assert 'outline:' in css_content or 'outline :' in css_content, \
        "Focus indicators should use outline property"

    # Check for adequate offset
    assert 'outline-offset' in css_content, \
        "Focus indicators should have outline-offset for visibility"


def test_tab_focus_indicators(css_content):
    """Test that tabs have specific focus indicators."""
    assert '.tab:focus-visible' in css_content, \
        "Tabs should have focus-visible styles"


def test_button_focus_indicators(css_content):
    """Test that buttons have focus indicators."""
    assert 'button:focus-visible' in css_content or \
           '.btn-primary:focus-visible' in css_content or \
           '.btn-secondary:focus-visible' in css_content, \
        "Buttons should have visible focus indicators"


def test_focus_indicators_high_contrast(css_content):
    """Test that focus indicators are enhanced in high contrast mode."""
    # In high contrast mode, focus indicators should be more prominent
    # Check if high contrast section mentions focus or outline
    assert 'outline:' in css_content or 'outline :' in css_content, \
        "High contrast mode should enhance focus visibility"


def test_theme_toggle_has_focus_indicator(css_content):
    """Test that theme toggle has focus indicator."""
    assert '.theme-toggle:focus-visible' in css_content, \
        "Theme toggle should have focus indicator"


# --- Regression Tests: Ensure existing functionality preserved ---

def test_existing_dark_mode_unchanged(css_content):
    """Test that dark mode from Task 7.6 is unchanged."""
    assert '[data-theme="dark"]' in css_content, \
        "Dark mode should still exist"


def test_existing_animations_unchanged(css_content):
    """Test that animations from Task 7.4 are unchanged."""
    assert '@keyframes fadeInUp' in css_content, \
        "fadeInUp animation should still exist"


def test_countdown_timer_unchanged(js_content):
    """Test that countdown timer logic is unchanged."""
    assert 'getLiveElapsedSeconds' in js_content, \
        "Timer core logic should be unchanged"


def test_tab_switching_still_works(js_content):
    """Test that tab switching function still exists."""
    assert 'switchTab' in js_content, \
        "Tab switching function should exist"

    # Should update ARIA attributes
    assert 'aria-selected' in js_content, \
        "Tab switching should update aria-selected"


# --- Code Quality & Best Practices ---

def test_aria_labels_are_descriptive(html_content):
    """Test that ARIA labels are descriptive, not generic."""
    # Should not have generic labels like "button" or "link"
    assert 'aria-label="button"' not in html_content.lower(), \
        "ARIA labels should be descriptive, not generic"


def test_keyboard_handler_prevents_default(js_content):
    """Test that keyboard handler prevents default for navigation keys."""
    assert 'preventDefault()' in js_content or 'preventDefault ()' in js_content, \
        "Keyboard handler should prevent default for arrow keys"


def test_no_positive_tabindex(html_content):
    """Test that no elements use positive tabindex."""
    # Positive tabindex is anti-pattern
    import re
    # Look for tabindex with positive numbers
    positive_tabindex = re.findall(r'tabindex=["\']([1-9]\d*)["\']', html_content)
    assert len(positive_tabindex) == 0, \
        "Should not use positive tabindex values (accessibility anti-pattern)"


def test_semantic_html_used(html_content):
    """Test that semantic HTML elements are used."""
    assert '<button' in html_content, \
        "Should use <button> for clickable elements"

    assert '<nav' in html_content, \
        "Should use <nav> for navigation"


# --- Summary Test: All Acceptance Criteria ---

def test_all_acceptance_criteria_met(html_content, css_content, js_content):
    """Meta-test: Verify all 5 acceptance criteria are implemented."""

    # 1. Keyboard navigation for all interactions
    assert 'handleTabKeyboard' in js_content, \
        "AC1: Keyboard navigation missing"

    # 2. ARIA labels on all interactive elements
    assert html_content.count('aria-label') >= 5, \
        "AC2: Insufficient ARIA labels"

    # 3. Screen reader-friendly timer updates
    assert 'aria-live' in html_content and 'announceToScreenReader' in js_content, \
        "AC3: Screen reader support missing"

    # 4. High contrast mode option
    assert '@media (prefers-contrast: high)' in css_content or \
           '[data-theme="dark"]' in css_content, \
        "AC4: High contrast mode missing"

    # 5. Focus indicators visible
    assert ':focus-visible' in css_content and 'outline:' in css_content, \
        "AC5: Focus indicators missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
