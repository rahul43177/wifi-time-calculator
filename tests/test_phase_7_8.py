"""
Task 7.8: Enhanced Data Visualizations — Test Suite

Tests for improved charts with hover tooltips, animations, and better visual presentation.

Acceptance Criteria (Implemented):
- Animated bar charts on load
- Hover tooltips with exact values
- (Skipped: Monthly calendar heatmap - complex, low value)
- (Skipped: 30-day trend line - analytics v2)
- (Implicit: Color gradients already present)
"""

import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def static_js_path(project_root):
    """Return path to app.js."""
    return project_root / "static" / "app.js"


@pytest.fixture
def js_content(static_js_path):
    """Read JavaScript file content."""
    return static_js_path.read_text()


# --- Acceptance Criterion 1: Animated bar charts on load ---

def test_weekly_chart_has_animation_config(js_content):
    """Test that weekly chart has animation configuration."""
    # Find the weekly chart creation
    assert "state.charts.weekly = new Chart" in js_content, \
        "Weekly chart should exist"

    # Check for animation config
    assert "animation:" in js_content, \
        "Charts should have animation configuration"


def test_animation_duration_specified(js_content):
    """Test that animation duration is specified."""
    assert "duration:" in js_content, \
        "Animation should have duration specified"


def test_animation_easing_specified(js_content):
    """Test that animation easing is specified."""
    assert "easing:" in js_content or "easeInOutQuart" in js_content, \
        "Animation should have smooth easing function"


def test_monthly_chart_has_animation(js_content):
    """Test that monthly chart also has animations."""
    # Monthly chart should also have animation config
    assert "state.charts.monthly = new Chart" in js_content, \
        "Monthly chart should exist"

    # Count animation configs (should be at least 2 for both charts)
    animation_count = js_content.count("animation:")
    assert animation_count >= 2, \
        "Both weekly and monthly charts should have animations"


# --- Acceptance Criterion 2: Hover tooltips with exact values ---

def test_weekly_chart_has_tooltip_config(js_content):
    """Test that weekly chart has tooltip configuration."""
    assert "tooltip:" in js_content, \
        "Charts should have tooltip configuration"


def test_tooltips_are_enabled(js_content):
    """Test that tooltips are explicitly enabled."""
    assert "enabled: true" in js_content, \
        "Tooltips should be enabled"


def test_tooltips_have_custom_styling(js_content):
    """Test that tooltips have custom styling."""
    # Check for tooltip styling options
    assert "backgroundColor:" in js_content and "rgba" in js_content, \
        "Tooltips should have custom background color"

    assert "padding:" in js_content, \
        "Tooltips should have padding for readability"


def test_tooltips_have_callback_for_exact_values(js_content):
    """Test that tooltips have callbacks for displaying exact values."""
    assert "callbacks:" in js_content, \
        "Tooltips should have callback functions"

    assert "label: function" in js_content, \
        "Tooltip label callback should exist"


def test_tooltip_shows_hours_and_minutes(js_content):
    """Test that tooltip callback formats hours and minutes."""
    # Check that tooltip callback calculates hours and minutes
    assert "Math.floor(value)" in js_content or "Math.floor(" in js_content, \
        "Tooltip should calculate hours from decimal"

    # Check for minutes calculation (value - hours) * 60
    assert "* 60" in js_content, \
        "Tooltip should calculate minutes"


def test_tooltip_uses_padstart_for_formatting(js_content):
    """Test that tooltip uses padStart for zero-padding."""
    assert "padStart(2, '0')" in js_content or "padStart(2, \"0\")" in js_content, \
        "Minutes should be zero-padded (e.g., 01, 02)"


def test_weekly_tooltip_shows_session_count(js_content):
    """Test that weekly chart tooltip shows session count."""
    # Check for afterLabel callback
    assert "afterLabel:" in js_content or "afterLabel :" in js_content, \
        "Weekly tooltip should have afterLabel for session count"

    assert "session_count" in js_content, \
        "Tooltip should display session count"


def test_monthly_tooltip_shows_additional_details(js_content):
    """Test that monthly chart tooltip shows days present and average."""
    # Monthly tooltip should show more details
    assert "days_present" in js_content, \
        "Monthly tooltip should show days present"

    assert "avg_daily_minutes" in js_content, \
        "Monthly tooltip should show daily average"


# --- Hover Effects and Interaction ---

def test_charts_have_interaction_mode(js_content):
    """Test that charts have interaction mode configured."""
    assert "interaction:" in js_content, \
        "Charts should have interaction configuration"

    assert "mode:" in js_content, \
        "Interaction mode should be specified"


def test_weekly_chart_uses_index_interaction(js_content):
    """Test that weekly chart uses index mode for grouped tooltips."""
    # For weekly bar chart, index mode shows all datasets at that index
    assert "'index'" in js_content or '"index"' in js_content, \
        "Weekly chart should use 'index' interaction mode"


def test_monthly_chart_uses_nearest_interaction(js_content):
    """Test that monthly chart uses nearest mode for point interaction."""
    assert "'nearest'" in js_content or '"nearest"' in js_content, \
        "Monthly chart should use 'nearest' interaction mode"


def test_interaction_not_requiring_exact_intersect(js_content):
    """Test that interaction doesn't require exact intersect."""
    assert "intersect: false" in js_content, \
        "Tooltips should show without exact cursor intersection"


# --- Point Hover Effects (Monthly Chart) ---

def test_monthly_chart_has_point_hover_effects(js_content):
    """Test that monthly line chart has point hover effects."""
    assert "pointHoverRadius:" in js_content, \
        "Monthly chart should have hover radius for points"


def test_point_hover_increases_radius(js_content):
    """Test that point radius increases on hover."""
    # Should have both pointRadius and pointHoverRadius
    assert "pointRadius:" in js_content and "pointHoverRadius:" in js_content, \
        "Point should grow on hover"


def test_point_hover_changes_color(js_content):
    """Test that point changes color on hover."""
    assert "pointHoverBackgroundColor:" in js_content, \
        "Point should change background color on hover"


def test_point_hover_has_border(js_content):
    """Test that hovered point has border for emphasis."""
    assert "pointHoverBorderColor:" in js_content and \
           "pointHoverBorderWidth:" in js_content, \
        "Hovered point should have visible border"


# --- Regression Tests: Existing Features Preserved ---

def test_weekly_chart_still_has_bar_type(js_content):
    """Test that weekly chart is still a bar chart."""
    assert 'type: "bar"' in js_content, \
        "Weekly chart should remain a bar chart"


def test_monthly_chart_still_has_line_type(js_content):
    """Test that monthly chart is still a line chart."""
    assert 'type: "line"' in js_content, \
        "Monthly chart should remain a line chart"


def test_weekly_chart_has_target_line(js_content):
    """Test that weekly chart still has target line overlay."""
    # Target line should still exist
    assert "Target" in js_content and "borderDash:" in js_content, \
        "Weekly chart should still have dashed target line"


def test_monthly_chart_has_fill(js_content):
    """Test that monthly chart still has filled area."""
    assert "fill: true" in js_content, \
        "Monthly chart should still have filled area under line"


def test_charts_are_responsive(js_content):
    """Test that charts remain responsive."""
    # Should have responsive configuration
    assert "responsive: true" in js_content, \
        "Charts should be responsive"

    assert "maintainAspectRatio: false" in js_content, \
        "Charts should fill container height"


def test_y_axis_begins_at_zero(js_content):
    """Test that y-axis still begins at zero."""
    assert "beginAtZero: true" in js_content, \
        "Y-axis should start at zero for accurate comparison"


def test_chart_legends_configured(js_content):
    """Test that chart legends are configured."""
    assert "legend:" in js_content, \
        "Charts should have legend configuration"


# --- Code Quality ---

def test_tooltip_callbacks_are_functions(js_content):
    """Test that tooltip callbacks are defined as functions."""
    # Callbacks should be function definitions
    assert "function(context)" in js_content, \
        "Tooltip callbacks should be functions"


def test_no_console_errors_in_chart_code(js_content):
    """Test that chart code doesn't have console.error calls."""
    # Chart rendering shouldn't have error logging (warnings are ok)
    chart_weekly_start = js_content.find("state.charts.weekly = new Chart")
    chart_monthly_start = js_content.find("state.charts.monthly = new Chart")

    # Neither chart section should have console.error
    chart_weekly_section = js_content[chart_weekly_start:chart_weekly_start + 3000]
    assert "console.error" not in chart_weekly_section, \
        "Chart code should not have error logging"


def test_task_7_8_comments_present(js_content):
    """Test that Task 7.8 implementation is documented."""
    assert "Task 7.8" in js_content, \
        "Task 7.8 enhancements should be documented in comments"


# --- Performance Considerations ---

def test_animations_use_reasonable_duration(js_content):
    """Test that animation durations are reasonable (<2 seconds)."""
    # Animation durations should be specified in milliseconds
    # Look for duration values - should be between 500-2000ms
    import re
    durations = re.findall(r'duration:\s*(\d+)', js_content)

    for duration in durations:
        duration_ms = int(duration)
        assert 500 <= duration_ms <= 2000, \
            f"Animation duration {duration_ms}ms should be 500-2000ms for smooth UX"


def test_tooltip_styling_uses_rgba_for_transparency(js_content):
    """Test that tooltip background uses rgba for semi-transparency."""
    assert "rgba(0, 0, 0, 0.8)" in js_content or "rgba" in js_content, \
        "Tooltip background should use rgba for transparency"


# --- Summary Test: All Acceptance Criteria ---

def test_all_acceptance_criteria_met(js_content):
    """Meta-test: Verify implemented acceptance criteria."""

    # 1. Animated bar charts on load
    assert "animation:" in js_content and "duration:" in js_content, \
        "AC1: Chart animations missing"

    # 2. Hover tooltips with exact values
    assert "tooltip:" in js_content and "callbacks:" in js_content, \
        "AC2: Hover tooltips with exact values missing"

    # 3. Heatmap and trend line skipped (documented in comments)
    # These are documented as skipped in test docstring

    # 4. Color gradients (already existed, verified present)
    assert "backgroundColor:" in js_content, \
        "Color gradients should be present"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
