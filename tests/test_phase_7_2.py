"""
Tests for Phase 7.2: Status Cards with Icons.

Covers:
- HTML structure: 4 status cards with correct icons and IDs
- CSS grid layout: 2x2 on desktop, stacked on mobile
- JavaScript: DOM caching, rendering logic, and real-time updates
- Color coding: alignment with Task 7.1 thresholds
- Backward compatibility: legacy elements preserved
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


# =============================================================================
# HTML Structure Tests
# =============================================================================


@pytest.mark.asyncio
async def test_status_cards_grid_exists() -> None:
    """Dashboard should contain status-cards-grid container."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert '<div class="status-cards-grid">' in response.text


@pytest.mark.asyncio
async def test_connection_status_card_exists() -> None:
    """Card 1: Connection status should exist (Phase 8: emojis removed)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    assert 'id="card-connection"' in html
    assert 'id="card-connection-value"' in html
    assert 'id="card-connection-detail"' in html
    # Phase 8: Icons removed for professional appearance


@pytest.mark.asyncio
async def test_session_details_card_exists() -> None:
    """Card 2: Session details should exist (Phase 8: emojis removed)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    assert 'id="card-session"' in html
    assert 'id="card-session-value"' in html
    assert 'id="card-session-detail"' in html
    # Phase 8: Icons removed for professional appearance


@pytest.mark.asyncio
async def test_today_total_card_exists() -> None:
    """Card 3: Today's total should exist (Phase 8: emojis removed)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    assert 'id="card-today"' in html
    assert 'id="card-today-value"' in html
    assert 'id="card-today-detail"' in html
    # Phase 8: Icons removed for professional appearance


@pytest.mark.asyncio
async def test_target_progress_card_exists() -> None:
    """Card 4: Target progress should exist (Phase 8: emojis removed)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    assert 'id="card-target"' in html
    assert 'id="card-target-value"' in html
    assert 'id="card-target-detail"' in html
    # Phase 8: Icons removed for professional appearance


@pytest.mark.asyncio
async def test_all_four_cards_present() -> None:
    """All 4 status cards should be present in the grid."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    # Count status-card occurrences (excluding legacy status)
    card_count = html.count('class="status-card"')
    assert card_count == 4, f"Expected 4 status cards, found {card_count}"


@pytest.mark.asyncio
async def test_status_card_structure() -> None:
    """Each status card should have label, value, and detail (Phase 8: icons removed)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    # Phase 8: Icons removed, checking essential structure only
    assert 'class="status-card-content"' in html
    assert 'class="status-card-label"' in html
    assert 'class="status-card-value"' in html
    assert 'class="status-card-detail"' in html


# =============================================================================
# CSS Grid Layout Tests
# =============================================================================


@pytest.mark.asyncio
async def test_css_defines_status_cards_grid() -> None:
    """CSS should define status-cards-grid with 2-column layout."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert ".status-cards-grid {" in css
    assert "display: grid;" in css
    assert "grid-template-columns: repeat(2, 1fr);" in css


@pytest.mark.asyncio
async def test_css_defines_status_card_styling() -> None:
    """CSS should define status-card with flexbox layout."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert ".status-card {" in css
    # Phase 8: Removed flex properties (no icon to align with)


@pytest.mark.asyncio
async def test_css_defines_hover_effects() -> None:
    """Status cards should have hover effects for interactivity."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert ".status-card:hover {" in css
    assert "transform: translateY(-2px);" in css
    assert "box-shadow:" in css


@pytest.mark.asyncio
async def test_css_mobile_layout_stacks_cards() -> None:
    """Mobile layout should stack cards in single column."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert "@media (max-width: 600px)" in css
    # Within the mobile media query, status-cards-grid should be 1 column
    # We'll check that the mobile override exists
    mobile_section_start = css.find("@media (max-width: 600px)")
    mobile_section = css[mobile_section_start:mobile_section_start + 2000]
    assert ".status-cards-grid {" in mobile_section
    assert "grid-template-columns: 1fr;" in mobile_section


@pytest.mark.asyncio
async def test_css_defines_connection_color_states() -> None:
    """Connection card should have color states for connected/disconnected."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert "#card-connection.connected .status-card-value {" in css
    assert "#card-connection.disconnected .status-card-value {" in css


@pytest.mark.asyncio
async def test_css_defines_target_progress_color_states() -> None:
    """Target progress card should have color states aligned with Task 7.1."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert "#card-target.progress-low .status-card-value {" in css
    assert "#card-target.progress-medium .status-card-value {" in css
    assert "#card-target.progress-high .status-card-value {" in css
    assert "#card-target.progress-complete .status-card-value {" in css


# =============================================================================
# JavaScript Functionality Tests
# =============================================================================


@pytest.mark.asyncio
async def test_js_caches_status_card_dom_elements() -> None:
    """JavaScript should cache all status card DOM elements."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    assert 'cardConnection: null,' in js
    # Phase 8: cardConnectionIcon removed (no more emoji icons)
    assert 'cardConnectionValue: null,' in js
    assert 'cardConnectionDetail: null,' in js
    assert 'cardSessionValue: null,' in js
    assert 'cardSessionDetail: null,' in js
    assert 'cardTodayValue: null,' in js
    assert 'cardTodayDetail: null,' in js
    assert 'cardTarget: null,' in js
    assert 'cardTargetValue: null,' in js
    assert 'cardTargetDetail: null,' in js


@pytest.mark.asyncio
async def test_js_caches_status_card_elements_in_cache_function() -> None:
    """cacheElements() should query and cache all status card DOM nodes."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    assert 'dom.cardConnection = document.getElementById("card-connection");' in js
    # Phase 8: connection-icon removed (no more emoji icons)
    assert 'dom.cardConnectionValue = document.getElementById("card-connection-value");' in js
    assert 'dom.cardSessionValue = document.getElementById("card-session-value");' in js
    assert 'dom.cardTodayValue = document.getElementById("card-today-value");' in js
    assert 'dom.cardTargetValue = document.getElementById("card-target-value");' in js


@pytest.mark.asyncio
async def test_js_defines_render_status_cards_function() -> None:
    """JavaScript should define renderStatusCards() function."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    assert "function renderStatusCards() {" in js


@pytest.mark.asyncio
async def test_render_status_cards_updates_connection_card() -> None:
    """renderStatusCards() should update connection card with icon and status."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    # Check connection card update logic (Phase 8: icon logic removed)
    assert 'dom.cardConnectionValue.textContent = isConnected ? "Connected" : "Disconnected";' in js


@pytest.mark.asyncio
async def test_render_status_cards_updates_session_card() -> None:
    """renderStatusCards() should update session card with start time and elapsed."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    assert "dom.cardSessionValue.textContent = state.status.start_time" in js
    assert '`${formatSecondsToHM(elapsedSeconds)} elapsed`' in js


@pytest.mark.asyncio
async def test_render_status_cards_updates_today_card() -> None:
    """renderStatusCards() should update today's total card with time and session count."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    assert "dom.cardTodayValue.textContent = todayTotal;" in js
    assert 'sessionCount === 1 ? "1 session" : `${sessionCount} sessions`' in js


@pytest.mark.asyncio
async def test_render_status_cards_updates_target_card() -> None:
    """renderStatusCards() should update target progress card with percentage."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    assert "dom.cardTargetValue.textContent = formatPercent(progressValue);" in js


@pytest.mark.asyncio
async def test_render_status_cards_applies_color_classes() -> None:
    """renderStatusCards() should apply color classes based on Task 7.1 thresholds."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    # Check threshold logic
    assert 'dom.cardTarget.classList.remove("progress-low", "progress-medium", "progress-high", "progress-complete");' in js
    assert 'dom.cardTarget.classList.add("progress-complete");' in js
    assert 'dom.cardTarget.classList.add("progress-high");' in js
    assert 'dom.cardTarget.classList.add("progress-medium");' in js
    assert 'dom.cardTarget.classList.add("progress-low");' in js


@pytest.mark.asyncio
async def test_render_status_cards_called_from_render_all() -> None:
    """renderStatusCards() should be called from renderAll()."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    # Find renderAll function and verify it calls renderStatusCards
    render_all_start = js.find("function renderAll() {")
    render_all_end = js.find("}", render_all_start)
    render_all_body = js[render_all_start:render_all_end]
    assert "renderStatusCards();" in render_all_body


@pytest.mark.asyncio
async def test_render_status_cards_called_from_render_timer() -> None:
    """renderStatusCards() should be called from renderTimer() for real-time updates."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    # renderTimer should call renderStatusCards at the end
    render_timer_start = js.find("function renderTimer() {")
    # Find the closing brace of renderTimer (it's a large function)
    # We'll look for the renderStatusCards call within it
    # Task 7.4: Increased range to accommodate celebration animation logic
    render_timer_section = js[render_timer_start:render_timer_start + 3500]
    assert "renderStatusCards();" in render_timer_section


# =============================================================================
# Backward Compatibility Tests
# =============================================================================


@pytest.mark.asyncio
async def test_legacy_connection_status_elements_preserved() -> None:
    """Legacy connection-status, connection-label, and current-ssid should be preserved."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    assert 'id="connection-status"' in html
    assert 'id="connection-label"' in html
    assert 'id="current-ssid"' in html


@pytest.mark.asyncio
async def test_legacy_elements_are_hidden() -> None:
    """Legacy status elements should be hidden via CSS."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    # Legacy section should have "legacy-status hidden" classes
    assert 'class="card legacy-status hidden"' in html


@pytest.mark.asyncio
async def test_legacy_status_css_class_exists() -> None:
    """CSS should define .legacy-status as display: none."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text
    assert ".legacy-status {" in css
    assert "display: none !important;" in css


@pytest.mark.asyncio
async def test_render_connection_guards_legacy_elements() -> None:
    """renderConnection() should guard legacy element access with existence checks."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text
    # Check that renderConnection has guards
    assert "if (dom.connectionStatus) {" in js
    assert "if (dom.connectionLabel) {" in js
    assert "if (dom.currentSsid) {" in js


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_status_cards_render_with_timer_section() -> None:
    """Status cards and Task 7.1 timer section should coexist."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    # Both should be present
    assert 'class="status-cards-grid"' in html
    assert 'class="card timer-section"' in html
    assert 'id="elapsed-display"' in html  # Task 7.1 element


@pytest.mark.asyncio
async def test_no_duplicate_card_ids() -> None:
    """Each status card should have unique IDs."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    # Check that each card ID appears exactly once
    assert html.count('id="card-connection"') == 1
    assert html.count('id="card-session"') == 1
    assert html.count('id="card-today"') == 1
    assert html.count('id="card-target"') == 1


@pytest.mark.asyncio
async def test_timer_section_preserves_task_7_1_structure() -> None:
    """Timer section should still contain Task 7.1 elements."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    # Task 7.1 elements
    assert 'id="elapsed-time"' in html
    assert 'id="target-display"' in html
    assert 'id="elapsed-percent"' in html
    assert 'id="timer-display"' in html  # Countdown
    assert 'id="progress-fill"' in html


@pytest.mark.asyncio
async def test_status_cards_appear_before_timer_section() -> None:
    """Status cards should appear before the timer section in DOM order."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text
    cards_position = html.find('class="status-cards-grid"')
    timer_position = html.find('class="card timer-section"')
    assert cards_position < timer_position, "Status cards should appear before timer section"
