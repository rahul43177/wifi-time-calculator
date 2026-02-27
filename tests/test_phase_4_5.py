"""
Tests for Phase 4.5: Browser Notification Support.

Covers:
- Presence of Notification API integration in app.js
- Permission request logic on startup
- Completion flip detection (lastCompleted4h state)
- Notification trigger on transition
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_js_contains_notification_logic() -> None:
    """app.js should contain Notification API calls and logic."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    body = response.text
    assert "function requestNotificationPermission()" in body
    assert "Notification.requestPermission()" in body
    assert "function notifyCompletion()" in body
    assert "new Notification(" in body


@pytest.mark.asyncio
async def test_js_tracks_completion_transition() -> None:
    """app.js should track lastCompleted4h to detect flip."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    body = response.text
    assert "lastCompleted4h: null" in body
    assert "state.lastCompleted4h === false && newCompleted4h === true" in body
    assert "notifyCompletion();" in body
    assert "state.lastCompleted4h = newCompleted4h;" in body


@pytest.mark.asyncio
async def test_js_calls_permission_request_on_start() -> None:
    """app.js should call requestNotificationPermission during start()."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    body = response.text
    # Ensure it's called inside the start function
    assert "function start() {" in body
    # Find start function and check if the call is present thereafter until the next major block or end of file
    start_pos = body.find("function start() {")
    end_pos = body.find("setInterval(() => {", start_pos)
    start_block = body[start_pos:end_pos]
    assert "requestNotificationPermission();" in start_block


@pytest.mark.asyncio
async def test_api_status_includes_completed_4h() -> None:
    """The /api/status endpoint must return the completed_4h boolean."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert "completed_4h" in data
    assert isinstance(data["completed_4h"], bool)


@pytest.mark.asyncio
async def test_api_status_includes_personal_leave_time_field() -> None:
    """/api/status should always include personal_leave_time_ist (nullable)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert "personal_leave_time_ist" in data
    assert data["personal_leave_time_ist"] is None or isinstance(
        data["personal_leave_time_ist"], str
    )


@pytest.mark.asyncio
async def test_api_today_includes_personal_leave_time_field() -> None:
    """/api/today should always include personal_leave_time_ist (nullable)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/today")

    assert response.status_code == 200
    data = response.json()
    assert "personal_leave_time_ist" in data
    assert data["personal_leave_time_ist"] is None or isinstance(
        data["personal_leave_time_ist"], str
    )
