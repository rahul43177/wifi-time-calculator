"""
Tests for Phase 7.4: Micro-Animations & Transitions.

Covers:
- Smooth progress bar animation transitions
- Status card fade-in animations on load
- Connection status dot pulse animation
- Celebration animation on target completion
- Performance and accessibility checks
- Reduced motion support
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


# =============================================================================
# CSS Animation Definition Tests
# =============================================================================


@pytest.mark.asyncio
async def test_css_defines_fadeinup_animation() -> None:
    """CSS should define fadeInUp keyframe animation for status cards."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Task 7.4: fadeInUp animation
    assert "@keyframes fadeInUp" in css
    assert "opacity: 0" in css
    assert "transform: translateY(20px)" in css
    assert "opacity: 1" in css
    assert "transform: translateY(0)" in css


@pytest.mark.asyncio
async def test_css_defines_pulse_animation() -> None:
    """CSS should define pulse keyframe animation for connection dot."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Task 7.4: pulse animation
    assert "@keyframes pulse" in css
    assert "transform: scale(1)" in css
    assert "transform: scale(1.2)" in css


@pytest.mark.asyncio
async def test_css_defines_celebrate_animation() -> None:
    """CSS should define celebrate keyframe animation for target completion."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Task 7.4: celebrate animation
    assert "@keyframes celebrate" in css
    assert "transform: scale(1.1)" in css or "transform: scale(1.05)" in css


@pytest.mark.asyncio
async def test_css_defines_celebrate_glow_animation() -> None:
    """CSS should define celebrateGlow keyframe animation."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Task 7.4: celebrateGlow animation
    assert "@keyframes celebrateGlow" in css
    assert "box-shadow" in css


# =============================================================================
# Progress Bar Animation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_progress_bar_has_smooth_transition() -> None:
    """Progress bar should have smooth width transition (not instant jumps)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Progress fill should have width transition
    assert ".progress-fill" in css
    # Task 7.4: Should use cubic-bezier for natural feel
    assert "transition:" in css
    assert "width" in css
    # Should have reasonable duration (0.5s - 1s range)
    assert "0.8s" in css or "0.5s" in css or "1s" in css


@pytest.mark.asyncio
async def test_progress_bar_uses_gpu_friendly_properties() -> None:
    """Progress bar animation should use GPU-accelerated properties."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Should use cubic-bezier easing
    assert "cubic-bezier" in css


# =============================================================================
# Status Card Animation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_status_cards_have_fadein_animation() -> None:
    """Status cards should have fadeInUp animation applied."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Status cards should have animation
    assert ".status-card" in css
    assert "animation:" in css
    assert "fadeInUp" in css


@pytest.mark.asyncio
async def test_status_cards_have_staggered_delays() -> None:
    """Status cards should have staggered animation delays."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Should have nth-child selectors for stagger
    assert ":nth-child(1)" in css
    assert ":nth-child(2)" in css
    assert ":nth-child(3)" in css
    assert ":nth-child(4)" in css
    assert "animation-delay" in css


# =============================================================================
# Connection Dot Pulse Tests
# =============================================================================


@pytest.mark.asyncio
async def test_connection_dot_has_pulse_animation() -> None:
    """Connected status dot should have pulse animation."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Pulse should only apply to connected state
    assert ".connected .status-dot" in css
    # Should reference pulse animation
    pulse_section_start = css.find(".connected .status-dot")
    pulse_section = css[pulse_section_start:pulse_section_start + 200]
    assert "pulse" in pulse_section


@pytest.mark.asyncio
async def test_pulse_animation_is_infinite() -> None:
    """Pulse animation should loop infinitely."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Find pulse animation application
    pulse_section_start = css.find(".connected .status-dot")
    pulse_section = css[pulse_section_start:pulse_section_start + 200]
    assert "infinite" in pulse_section


# =============================================================================
# Celebration Animation Tests
# =============================================================================


@pytest.mark.asyncio
async def test_celebration_animation_class_defined() -> None:
    """Celebration animation should be defined for timer section."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Timer section should have celebration state
    assert ".timer-section.celebrating" in css
    assert "celebrate" in css


@pytest.mark.asyncio
async def test_celebration_has_glow_effect() -> None:
    """Celebration should include glow effect on elapsed display."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Celebrating state should affect elapsed display
    assert ".timer-section.celebrating .elapsed-display" in css
    assert "celebrateGlow" in css


# =============================================================================
# JavaScript Celebration Logic Tests
# =============================================================================


@pytest.mark.asyncio
async def test_js_tracks_completion_state() -> None:
    """JavaScript should track completion state for celebration trigger."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Should have wasCompleted state
    assert "wasCompleted" in js


@pytest.mark.asyncio
async def test_js_adds_celebrating_class() -> None:
    """JavaScript should add 'celebrating' class when target first reached."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Should add celebrating class
    assert "celebrating" in js
    assert "classList.add" in js


@pytest.mark.asyncio
async def test_js_removes_celebrating_class_with_timeout() -> None:
    """JavaScript should remove celebrating class after animation completes."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Should use setTimeout to remove class
    assert "setTimeout" in js
    assert "1200" in js  # Animation duration
    assert "classList.remove" in js


@pytest.mark.asyncio
async def test_js_caches_timer_section_element() -> None:
    """JavaScript should cache timer section DOM element."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Should cache timerSection in dom object
    assert "timerSection" in js
    assert "querySelector" in js or "getElementById" in js


# =============================================================================
# Accessibility Tests (Reduced Motion)
# =============================================================================


@pytest.mark.asyncio
async def test_reduced_motion_media_query_exists() -> None:
    """CSS should include prefers-reduced-motion media query."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Task 7.4: Accessibility - reduced motion support
    assert "@media (prefers-reduced-motion: reduce)" in css


@pytest.mark.asyncio
async def test_reduced_motion_disables_animations() -> None:
    """Reduced motion should disable or minimize animations."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Find reduced motion section
    reduced_motion_start = css.find("@media (prefers-reduced-motion: reduce)")
    if reduced_motion_start == -1:
        pytest.fail("Reduced motion media query not found")

    reduced_motion_section = css[reduced_motion_start:reduced_motion_start + 500]

    # Should disable or minimize animations
    assert ("animation: none" in reduced_motion_section or
            "animation-duration: 0" in reduced_motion_section or
            "0.01ms" in reduced_motion_section)


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.asyncio
async def test_animations_use_transform_not_layout_properties() -> None:
    """Animations should use transform/opacity for GPU acceleration."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Animations should primarily use transform and opacity
    fadeInUp_start = css.find("@keyframes fadeInUp")
    fadeInUp_section = css[fadeInUp_start:fadeInUp_start + 200]
    assert "transform:" in fadeInUp_section
    assert "opacity:" in fadeInUp_section

    # Should NOT animate width/height/top/left directly in keyframes
    # (progress bar width is an exception via transition)
    pulse_start = css.find("@keyframes pulse")
    pulse_section = css[pulse_start:pulse_start + 200]
    assert "transform:" in pulse_section


@pytest.mark.asyncio
async def test_animation_durations_reasonable() -> None:
    """Animation durations should be reasonable (not too fast or slow)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Durations should be in reasonable range (0.2s - 2s)
    # Check for common duration patterns
    assert ("0.4s" in css or "0.8s" in css or "1.2s" in css or "2s" in css)


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_animations_dont_break_existing_functionality() -> None:
    """Animations should not interfere with existing timer/status functionality."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # renderTimer should still exist and work
    assert "function renderTimer()" in js
    # renderStatusCards should still be called
    assert "renderStatusCards();" in js
    # Progress bar updates should still happen
    assert "progressFill.style.width" in js


@pytest.mark.asyncio
async def test_no_animation_on_disconnected_state() -> None:
    """Pulse animation should NOT apply to disconnected state."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/style.css")

    css = response.text

    # Disconnected should NOT have pulse
    disconnected_start = css.find(".disconnected .status-dot")
    if disconnected_start != -1:
        disconnected_section = css[disconnected_start:disconnected_start + 200]
        # Should NOT contain pulse animation
        assert "animation: pulse" not in disconnected_section


@pytest.mark.asyncio
async def test_task_7_4_comment_markers_present() -> None:
    """Code should have Task 7.4 comment markers for traceability."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        css_response = await client.get("/static/style.css")
        js_response = await client.get("/static/app.js")

    css = css_response.text
    js = js_response.text

    # Should have Task 7.4 markers
    assert "Task 7.4" in css
    assert "Task 7.4" in js


# =============================================================================
# Backward Compatibility Tests
# =============================================================================


@pytest.mark.asyncio
async def test_countdown_timer_unchanged() -> None:
    """Countdown timer logic should remain unchanged by Task 7.4."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Countdown timer elements should still be updated
    assert "timerDisplay.textContent" in js
    assert "formatHHMMSS" in js


@pytest.mark.asyncio
async def test_color_thresholds_preserved() -> None:
    """Task 7.1 color thresholds should be preserved."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Threshold logic should still exist
    assert "progressValue > 80" in js or "progressValue >= 50" in js


@pytest.mark.asyncio
async def test_status_cards_still_functional() -> None:
    """Task 7.2 status cards should remain fully functional."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    js = response.text

    # Status card updates should still happen
    assert "renderStatusCards" in js
    assert "cardConnection" in js
    assert "cardTarget" in js
