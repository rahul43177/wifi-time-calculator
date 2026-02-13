"""
Tests for Phase 4.2: HTML dashboard template rendering.

Covers:
- Root route returns Jinja-rendered dashboard HTML
- Required dashboard placeholders/sections exist
- Context values are wired from backend settings
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_root_renders_dashboard_template() -> None:
    """Root endpoint should render the dashboard template HTML."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<title>Office Wi-Fi Tracker</title>" in response.text
    assert "Office Wi-Fi Tracker" in response.text


@pytest.mark.asyncio
async def test_root_includes_required_dashboard_sections() -> None:
    """Template includes timer, progress, status, sessions table, and total summary."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    body = response.text
    assert 'id="connection-status"' in body
    assert 'id="timer-display"' in body
    assert 'role="progressbar"' in body
    assert 'id="completion-banner"' in body
    assert 'id="today-sessions-table"' in body
    assert 'id="today-total-display"' in body


@pytest.mark.asyncio
async def test_root_hides_completion_banner_by_default() -> None:
    """Completion banner should be present but hidden initially."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    body = response.text
    assert 'id="completion-banner"' in body
    assert 'class="completion hidden"' in body


@pytest.mark.asyncio
async def test_root_includes_weekly_monthly_tab_placeholders() -> None:
    """Template includes navigation placeholders for Weekly and Monthly sections."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "Weekly" in response.text
    assert "Monthly" in response.text


@pytest.mark.asyncio
async def test_root_displays_office_wifi_name_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Template should render current configured office SSID."""
    monkeypatch.setattr(settings, "office_wifi_name", "OfficeWifi-QA")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "OfficeWifi-QA" in response.text


@pytest.mark.asyncio
async def test_root_target_display_uses_test_mode_target(monkeypatch: pytest.MonkeyPatch) -> None:
    """When test mode is enabled, template target display should use minute-only target."""
    monkeypatch.setattr(settings, "test_mode", True)
    monkeypatch.setattr(settings, "test_duration_minutes", 2)
    monkeypatch.setattr(settings, "work_duration_hours", 4)
    monkeypatch.setattr(settings, "buffer_minutes", 10)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert 'id="target-display">2m<' in response.text
