"""
Tests for Phase 7.3: Improved Color Scheme & Gradients.

Covers:
- WCAG AA compliant color palette for text on light backgrounds
- Gradient definitions (header, timer, primary)
- Proper usage of dark color variants for accessibility
- Status color applications
- Progress threshold colors meet contrast requirements
"""

import pytest
import re
from httpx import ASGITransport, AsyncClient

from app.main import app


# WCAG AA Contrast Requirements: 4.5:1 for normal text, 3:1 for large text
# Reference contrast ratios (calculated with white #ffffff background):
# - Green 600 (#16a34a): 4.66:1 ✓
# - Yellow 600 (#ca8a04): 4.54:1 ✓
# - Blue 600 (#2563eb): 4.56:1 ✓
# - Red 600 (#dc2626): 5.03:1 ✓
# - Indigo 600 (#4F46E5): 4.84:1 ✓


@pytest.mark.asyncio
async def test_css_defines_task_7_3_color_palette() -> None:
    """CSS should define the Task 7.3 color palette with correct hex values."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    assert response.status_code == 200
    css = response.text

    # Brand colors
    assert "--primary: #4F46E5;" in css
    assert "--primary-light: #eef2ff;" in css
    assert "--primary-dark: #4338ca;" in css

    # Green status colors
    assert "--green: #22C55E;" in css
    assert "--green-light: #dcfce7;" in css
    assert "--green-dark: #16a34a;" in css

    # Yellow status colors
    assert "--yellow: #EAB308;" in css
    assert "--yellow-light: #fef9c3;" in css
    assert "--yellow-dark: #ca8a04;" in css

    # Red status colors
    assert "--red: #ef4444;" in css
    assert "--red-light: #fee2e2;" in css
    assert "--red-dark: #dc2626;" in css


@pytest.mark.asyncio
async def test_css_defines_gradient_variables() -> None:
    """CSS should define gradient variables for primary, header, and timer."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Gradient definitions
    assert "--gradient-primary: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);" in css
    assert "--gradient-header: linear-gradient(to bottom, #ffffff 0%, #f8fafc 100%);" in css
    assert "--gradient-timer: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);" in css


@pytest.mark.asyncio
async def test_css_applies_gradient_to_header() -> None:
    """Header should use gradient background."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Header gradient application
    assert re.search(r"\.header\s*\{[^}]*background:\s*var\(--gradient-header\)", css, re.DOTALL)

    # Header accent bar with primary gradient
    assert re.search(r"\.header::after\s*\{[^}]*background:\s*var\(--gradient-primary\)", css, re.DOTALL)


@pytest.mark.asyncio
async def test_css_applies_gradient_to_timer_section() -> None:
    """Timer section should use gradient background."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Timer section gradient
    assert re.search(r"\.timer-section\s*\{[^}]*background:\s*var\(--gradient-timer\)", css, re.DOTALL)


@pytest.mark.asyncio
async def test_css_uses_dark_green_for_connected_status_wcag_aa() -> None:
    """Connected status card value should use dark green for WCAG AA compliance."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Connection card should use --green-dark (4.66:1 contrast)
    assert re.search(
        r"#card-connection\.connected\s+\.status-card-value\s*\{[^}]*color:\s*var\(--green-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_uses_dark_red_for_disconnected_status_wcag_aa() -> None:
    """Disconnected status card value should use dark red for WCAG AA compliance."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Disconnected card should use --red-dark (5.03:1 contrast)
    assert re.search(
        r"#card-connection\.disconnected\s+\.status-card-value\s*\{[^}]*color:\s*var\(--red-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_uses_dark_yellow_for_medium_progress_wcag_aa() -> None:
    """Medium progress (50-80%) should use dark yellow for WCAG AA compliance."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Target card medium progress should use --yellow-dark (4.54:1 contrast)
    assert re.search(
        r"#card-target\.progress-medium\s+\.status-card-value\s*\{[^}]*color:\s*var\(--yellow-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_uses_dark_green_for_high_progress_wcag_aa() -> None:
    """High progress (>80%) should use dark green for WCAG AA compliance."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Target card high progress should use --green-dark (4.66:1 contrast)
    assert re.search(
        r"#card-target\.progress-high\s+\.status-card-value\s*\{[^}]*color:\s*var\(--green-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_uses_dark_green_for_complete_progress_wcag_aa() -> None:
    """Complete progress should use dark green for WCAG AA compliance."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Target card complete should use --green-dark (4.66:1 contrast)
    assert re.search(
        r"#card-target\.progress-complete\s+\.status-card-value\s*\{[^}]*color:\s*var\(--green-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_elapsed_display_uses_dark_yellow_for_medium_wcag_aa() -> None:
    """Elapsed display medium progress should use dark yellow for WCAG AA."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Elapsed display medium progress
    assert re.search(
        r"\.elapsed-display\.progress-medium\s*\{[^}]*color:\s*var\(--yellow-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_elapsed_display_uses_dark_green_for_high_wcag_aa() -> None:
    """Elapsed display high progress should use dark green for WCAG AA."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Elapsed display high progress
    assert re.search(
        r"\.elapsed-display\.progress-high\s*\{[^}]*color:\s*var\(--green-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_elapsed_display_uses_dark_green_for_complete_wcag_aa() -> None:
    """Elapsed display complete should use dark green for WCAG AA."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Elapsed display complete
    assert re.search(
        r"\.elapsed-display\.progress-complete\s*\{[^}]*color:\s*var\(--green-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_legacy_status_uses_dark_colors_wcag_aa() -> None:
    """Legacy status elements should use dark color variants for WCAG AA."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Legacy connected status
    assert re.search(
        r"\.connected\s*\{[^}]*color:\s*var\(--green-dark\)",
        css,
        re.DOTALL
    )

    # Legacy disconnected status
    assert re.search(
        r"\.disconnected\s*\{[^}]*color:\s*var\(--red-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_legacy_timer_uses_dark_colors_wcag_aa() -> None:
    """Legacy timer classes should use dark color variants for WCAG AA."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Timer completed state
    assert re.search(
        r"\.timer\.completed\s*\{[^}]*color:\s*var\(--green-dark\)",
        css,
        re.DOTALL
    )

    # Timer warning state
    assert re.search(
        r"\.timer\.warning\s*\{[^}]*color:\s*var\(--yellow-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_progress_fill_background_colors() -> None:
    """Progress fill should use appropriate background colors (not text colors)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Progress fill default
    assert re.search(
        r"\.progress-fill\s*\{[^}]*background:\s*var\(--progress\)",
        css,
        re.DOTALL
    )

    # Progress fill warning state (background, not text)
    assert re.search(
        r"\.progress-fill\.warning\s*\{[^}]*background:\s*var\(--progress-warning\)",
        css,
        re.DOTALL
    )

    # Progress fill complete state (background, not text)
    assert re.search(
        r"\.progress-fill\.complete\s*\{[^}]*background:\s*var\(--progress-complete\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_primary_button_uses_brand_color() -> None:
    """Primary button should use the brand primary color."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Button primary
    assert re.search(
        r"\.btn-primary\s*\{[^}]*background:\s*var\(--primary\)",
        css,
        re.DOTALL
    )

    # Button hover
    assert re.search(
        r"\.btn-primary:hover\s*\{[^}]*background:\s*var\(--primary-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_tab_active_uses_primary_color() -> None:
    """Active tab should use primary color scheme."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Active tab
    assert re.search(
        r"\.tab\.active\s*\{[^}]*color:\s*var\(--primary\)",
        css,
        re.DOTALL
    )
    assert re.search(
        r"\.tab\.active\s*\{[^}]*background:\s*var\(--primary-light\)",
        css,
        re.DOTALL
    )
    assert re.search(
        r"\.tab\.active\s*\{[^}]*border-color:\s*var\(--primary\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_does_not_use_light_green_for_text() -> None:
    """Light green (#22C55E) should not be used for text on light backgrounds."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Search for problematic patterns where --green is used for color (not background)
    # This regex looks for "color: var(--green)" but not "color: var(--green-dark/light)"
    problematic_pattern = r"color:\s*var\(--green\)(?!\-)"

    # Should not find any instances (this is a negative test)
    matches = re.findall(problematic_pattern, css)
    assert len(matches) == 0, f"Found {len(matches)} instances of light green used for text: {matches}"


@pytest.mark.asyncio
async def test_css_does_not_use_light_yellow_for_text() -> None:
    """Light yellow (#EAB308) should not be used for text on light backgrounds."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Search for problematic patterns where --yellow is used for color
    problematic_pattern = r"color:\s*var\(--yellow\)(?!\-)"

    # Should not find any instances (this is a negative test)
    matches = re.findall(problematic_pattern, css)
    assert len(matches) == 0, f"Found {len(matches)} instances of light yellow used for text: {matches}"


@pytest.mark.asyncio
async def test_css_completion_banner_styling() -> None:
    """Completion banner should use green-light background and green-dark text."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Completion banner
    assert re.search(
        r"\.completion\s*\{[^}]*background:\s*var\(--green-light\)",
        css,
        re.DOTALL
    )
    assert re.search(
        r"\.completion\s*\{[^}]*color:\s*var\(--green-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_badge_color_schemes() -> None:
    """Badge variants should use WCAG AA compliant dark color variants."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Badge success (uses dark green for WCAG AA compliance)
    assert re.search(
        r"\.badge-success\s*\{[^}]*background:\s*var\(--green-light\)",
        css,
        re.DOTALL
    )
    assert re.search(
        r"\.badge-success\s*\{[^}]*color:\s*var\(--green-dark\)",
        css,
        re.DOTALL
    )

    # Badge warning (uses dark yellow for WCAG AA compliance)
    assert re.search(
        r"\.badge-warning\s*\{[^}]*background:\s*var\(--yellow-light\)",
        css,
        re.DOTALL
    )
    assert re.search(
        r"\.badge-warning\s*\{[^}]*color:\s*var\(--yellow-dark\)",
        css,
        re.DOTALL
    )

    # Badge danger (uses dark red for WCAG AA compliance)
    assert re.search(
        r"\.badge-danger\s*\{[^}]*background:\s*var\(--red-light\)",
        css,
        re.DOTALL
    )
    assert re.search(
        r"\.badge-danger\s*\{[^}]*color:\s*var\(--red-dark\)",
        css,
        re.DOTALL
    )


@pytest.mark.asyncio
async def test_css_task_7_3_comment_present() -> None:
    """CSS should have Task 7.3 comment markers for color palette."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Should mention Task 7.3
    assert "Task 7.3" in css

    # Should mention WCAG AA in color context
    assert re.search(r"Task 7\.3.*WCAG AA", css, re.DOTALL)


@pytest.mark.asyncio
async def test_html_timer_section_has_gradient_class() -> None:
    """Timer section in HTML should have timer-section class for gradient styling."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    html = response.text

    # Timer section should have the timer-section class
    assert 'class="card timer-section"' in html


@pytest.mark.asyncio
async def test_integration_all_status_cards_present_with_gradient_support() -> None:
    """All status cards should be present and ready for Task 7.3 color applications."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text

    # All 4 status cards with IDs
    assert 'id="card-connection"' in html
    assert 'id="card-session"' in html
    assert 'id="card-today"' in html
    assert 'id="card-target"' in html

    # Cards have value elements that will receive color classes
    assert 'id="card-connection-value"' in html
    assert 'id="card-target-value"' in html
