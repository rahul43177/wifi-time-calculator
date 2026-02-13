"""
Tests for Phase 7.5: Contextual Insights & Messaging.

Covers:
- Morning greeting with estimated completion time
- Progress-based encouragement (50%, 75%, 90%)
- Completion celebration message
- Disconnection status with last session info
- Messages update dynamically based on state
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


# =============================================================================
# HTML Structure Tests
# =============================================================================


@pytest.mark.asyncio
async def test_html_has_contextual_message_element() -> None:
    """HTML should have contextual message container."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text

    # Task 7.5: Contextual message element
    assert 'id="contextual-message"' in html
    assert 'class="contextual-message"' in html


@pytest.mark.asyncio
async def test_contextual_message_placed_in_timer_section() -> None:
    """Contextual message should be in timer section between countdown and completion."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text

    # Find positions
    countdown_pos = html.find('class="countdown-section"')
    contextual_pos = html.find('id="contextual-message"')
    completion_pos = html.find('id="completion-banner"')

    # Verify order: countdown < contextual < completion
    assert countdown_pos < contextual_pos < completion_pos


# =============================================================================
# CSS Styling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_css_defines_contextual_message_base_style() -> None:
    """CSS should define base contextual message styling."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Task 7.5: Base contextual message styling
    assert ".contextual-message" in css
    assert "margin-top:" in css
    assert "padding:" in css
    assert "border-radius:" in css
    assert "text-align: center" in css


@pytest.mark.asyncio
async def test_css_defines_milestone_variant() -> None:
    """CSS should define milestone variant with primary color."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Task 7.5: Milestone variant
    assert ".contextual-message.milestone" in css
    # Should use primary color theme
    milestone_section = css[css.find(".contextual-message.milestone"):css.find(".contextual-message.milestone") + 200]
    assert "var(--primary" in milestone_section


@pytest.mark.asyncio
async def test_css_defines_celebration_variant() -> None:
    """CSS should define celebration variant with green color."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Task 7.5: Celebration variant
    assert ".contextual-message.celebration" in css
    celebration_section = css[css.find(".contextual-message.celebration"):css.find(".contextual-message.celebration") + 200]
    assert "var(--green" in celebration_section


@pytest.mark.asyncio
async def test_css_defines_disconnected_variant() -> None:
    """CSS should define disconnected variant with red color."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Task 7.5: Disconnected variant
    assert ".contextual-message.disconnected" in css
    disconnected_section = css[css.find(".contextual-message.disconnected"):css.find(".contextual-message.disconnected") + 200]
    assert "var(--red" in disconnected_section


@pytest.mark.asyncio
async def test_css_hides_empty_contextual_message() -> None:
    """CSS should hide contextual message when empty."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Task 7.5: Hide when empty
    assert ".contextual-message:empty" in css
    empty_section = css[css.find(".contextual-message:empty"):css.find(".contextual-message:empty") + 100]
    assert "display: none" in empty_section


# =============================================================================
# JavaScript Functionality Tests
# =============================================================================


@pytest.mark.asyncio
async def test_js_caches_contextual_message_element() -> None:
    """JavaScript should cache contextual message DOM element."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Task 7.5: DOM caching
    assert "contextualMessage" in js
    assert 'getElementById("contextual-message")' in js


@pytest.mark.asyncio
async def test_js_tracks_last_milestone_shown() -> None:
    """JavaScript should track last milestone shown to prevent flicker."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Task 7.5: Milestone tracking state
    assert "lastMilestoneShown" in js


@pytest.mark.asyncio
async def test_js_defines_render_contextual_message_function() -> None:
    """JavaScript should define renderContextualMessage function."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Task 7.5: Function definition
    assert "function renderContextualMessage()" in js


@pytest.mark.asyncio
async def test_render_contextual_message_called_from_render_timer() -> None:
    """renderContextualMessage should be called from renderTimer for dynamic updates."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Find renderTimer function
    render_timer_start = js.find("function renderTimer()")
    render_timer_section = js[render_timer_start:render_timer_start + 4000]

    # Task 7.5: Should call renderContextualMessage
    assert "renderContextualMessage()" in render_timer_section


@pytest.mark.asyncio
async def test_render_contextual_message_called_from_render_all() -> None:
    """renderContextualMessage should be called from renderAll for initial load."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Find renderAll function
    render_all_start = js.find("function renderAll()")
    render_all_section = js[render_all_start:render_all_start + 500]

    # Task 7.5: Should call renderContextualMessage
    assert "renderContextualMessage()" in render_all_section


@pytest.mark.asyncio
async def test_contextual_message_handles_disconnected_state() -> None:
    """Contextual message logic should handle disconnected state."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Find renderContextualMessage function
    func_start = js.find("function renderContextualMessage()")
    func_section = js[func_start:func_start + 3000]

    # Task 7.5: Disconnected state handling
    assert "isConnected" in func_section
    assert "sessionActive" in func_section
    assert "Last session ended" in func_section or "last session" in func_section.lower()


@pytest.mark.asyncio
async def test_contextual_message_handles_milestone_progression() -> None:
    """Contextual message should show milestone messages at 50%, 75%, 90%."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Find renderContextualMessage function
    func_start = js.find("function renderContextualMessage()")
    func_section = js[func_start:func_start + 3000]

    # Task 7.5: Milestone checks
    assert "progressValue >= 90" in func_section
    assert "progressValue >= 75" in func_section
    assert "progressValue >= 50" in func_section


@pytest.mark.asyncio
async def test_contextual_message_shows_completion_celebration() -> None:
    """Contextual message should show celebration when target completed."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Find renderContextualMessage function
    func_start = js.find("function renderContextualMessage()")
    func_section = js[func_start:func_start + 3000]

    # Task 7.5: Completion celebration
    assert "Target completed" in func_section or "completed" in func_section
    assert "celebration" in func_section


@pytest.mark.asyncio
async def test_contextual_message_shows_morning_greeting_with_eta() -> None:
    """Contextual message should show morning greeting with ETA."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Find renderContextualMessage function
    func_start = js.find("function renderContextualMessage()")
    func_section = js[func_start:func_start + 3000]

    # Task 7.5: Morning greeting with ETA calculation
    assert "hour < 12" in func_section or "morning" in func_section.lower()
    assert "Good morning" in func_section or "morning" in func_section
    assert "etaTime" in func_section or "ETA" in func_section or "goal by" in func_section


@pytest.mark.asyncio
async def test_contextual_message_uses_time_of_day_context() -> None:
    """Contextual message should use time-of-day context (morning/afternoon/evening)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Find renderContextualMessage function
    func_start = js.find("function renderContextualMessage()")
    func_section = js[func_start:func_start + 3000]

    # Task 7.5: Time-of-day checks
    assert "hour" in func_section.lower()
    # Should have different messages for different times
    assert ("morning" in func_section.lower() or "afternoon" in func_section.lower() or "evening" in func_section.lower())


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_contextual_message_does_not_break_timer_logic() -> None:
    """Task 7.5 should not interfere with existing timer rendering."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Verify core timer functions still exist
    assert "function renderTimer()" in js
    assert "getLiveElapsedSeconds()" in js
    assert "getLiveRemainingSeconds(" in js
    assert "formatHHMMSS(" in js


@pytest.mark.asyncio
async def test_task_7_5_comment_markers_present() -> None:
    """Code should have Task 7.5 comment markers for traceability."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        html_response = await client.get("/")
        css_response = await client.get("/static/style.css")
        js_response = await client.get("/static/app.js")

    html = html_response.text
    css = css_response.text
    js = js_response.text

    # Should have Task 7.5 markers
    assert "Task 7.5" in html
    assert "Task 7.5" in css
    assert "Task 7.5" in js


# =============================================================================
# Backward Compatibility Tests
# =============================================================================


@pytest.mark.asyncio
async def test_task_7_1_elapsed_display_unchanged() -> None:
    """Task 7.1 elapsed display should remain unchanged."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text

    # Task 7.1 elements should still exist
    assert 'id="elapsed-time"' in html
    assert 'id="target-display"' in html
    assert 'id="elapsed-percent"' in html


@pytest.mark.asyncio
async def test_task_7_2_status_cards_unchanged() -> None:
    """Task 7.2 status cards should remain unchanged."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    html = response.text

    # Task 7.2 cards should still exist
    assert 'id="card-connection"' in html
    assert 'id="card-session"' in html
    assert 'id="card-today"' in html
    assert 'id="card-target"' in html


@pytest.mark.asyncio
async def test_task_7_4_animations_unchanged() -> None:
    """Task 7.4 animations should remain unchanged."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        css_response = await client.get("/static/style.css")
        js_response = await client.get("/static/app.js")

    css = css_response.text
    js = js_response.text

    # Task 7.4 animations should still exist
    assert "@keyframes fadeInUp" in css
    assert "@keyframes pulse" in css
    assert "@keyframes celebrate" in css
    assert "wasCompleted" in js


@pytest.mark.asyncio
async def test_countdown_timer_logic_preserved() -> None:
    """Countdown timer logic should be completely preserved."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Countdown timer elements
    assert "timerDisplay" in js
    assert "formatHHMMSS" in js
    assert "remainingSeconds" in js
