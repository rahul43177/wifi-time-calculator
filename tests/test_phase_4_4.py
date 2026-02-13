"""
Tests for Phase 4.4: Live timer JavaScript.

Covers:
- Static app.js serving and template script wiring
- Required sync/tick intervals and API polling endpoints
- Completion/overtime rendering hooks
- Session-table refresh hooks
- Fetch failure graceful-degradation message
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_static_js_is_served() -> None:
    """GET /static/app.js should return 200."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "javascript" in content_type or "text/plain" in content_type


@pytest.mark.asyncio
async def test_dashboard_links_live_timer_script() -> None:
    """Dashboard HTML should include app.js with defer."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert '<script src="/static/app.js" defer></script>' in response.text


@pytest.mark.asyncio
async def test_dashboard_has_sync_status_placeholder() -> None:
    """Template should include sync-status element used for fetch-failure messaging."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert 'id="sync-status"' in response.text
    assert 'aria-live="polite"' in response.text


@pytest.mark.asyncio
async def test_js_defines_tick_and_sync_intervals() -> None:
    """app.js should tick every 1s and sync every 30s."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    body = response.text
    assert "const TICK_INTERVAL_MS = 1000;" in body
    assert "const SYNC_INTERVAL_MS = 30000;" in body
    assert "setInterval(renderTimer, TICK_INTERVAL_MS);" in body
    assert "setInterval(() => {" in body
    assert "void syncFromBackend();" in body


@pytest.mark.asyncio
async def test_js_syncs_status_and_today_endpoints() -> None:
    """app.js should sync both /api/status and /api/today using Promise.all."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    body = response.text
    assert 'const STATUS_ENDPOINT = "/api/status";' in body
    assert 'const TODAY_ENDPOINT = "/api/today";' in body
    assert "Promise.all([" in body
    assert "fetchJson(STATUS_ENDPOINT)" in body
    assert "fetchJson(TODAY_ENDPOINT)" in body


@pytest.mark.asyncio
async def test_js_uses_start_time_for_client_side_elapsed_calculation() -> None:
    """Client-side elapsed time should be derived from parsed session start timestamp."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    body = response.text
    assert "function parseSessionStartMs(" in body
    assert "state.sessionStartMs = parseSessionStartMs" in body
    assert "Date.now() - state.sessionStartMs" in body


@pytest.mark.asyncio
async def test_js_handles_completion_and_overtime_view() -> None:
    """When complete, timer should switch to elapsed/total mode."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    body = response.text
    assert "const completed = Boolean(state.status.completed_4h) || remainingSeconds <= 0;" in body
    assert "dom.timerModeLabel.textContent = `Completed (target: ${targetDisplay})`;" in body
    assert "dom.completedTotal.textContent = formatHHMMSS(elapsedSeconds);" in body


@pytest.mark.asyncio
async def test_js_refreshes_today_sessions_table_on_sync() -> None:
    """app.js should rebuild today's table rows when synced."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    body = response.text
    assert "dom.todaySessionsBody.textContent = \"\";" in body
    assert "for (const session of state.today.sessions)" in body
    assert "dom.todayTotalDisplay.textContent = state.today.total_display || \"0h 00m\";" in body


@pytest.mark.asyncio
async def test_js_handles_fetch_failure_with_last_known_state_message() -> None:
    """Fetch failures should surface a non-crashing degraded-state message."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    body = response.text
    assert "console.warn(\"Dashboard sync failed:\", error);" in body
    assert "Live sync delayed. Showing last known data." in body
    assert "renderAll();" in body
