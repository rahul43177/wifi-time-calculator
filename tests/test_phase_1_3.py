"""
Tests for Phase 1.3: FastAPI Lifespan Integration.

Verifies that the server starts the Wi-Fi polling task on startup,
serves endpoints correctly, and stops the task on shutdown.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app, _background_tasks, lifespan


@pytest.mark.asyncio
async def test_health_endpoint():
    """GET /health returns 200 with correct fields."""
    with patch("app.wifi_detector.get_current_ssid", return_value="TestWifi"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "office_wifi" in data
    assert "work_duration_hours" in data


@pytest.mark.asyncio
async def test_root_returns_html():
    """GET / returns HTML placeholder page."""
    with patch("app.wifi_detector.get_current_ssid", return_value="TestWifi"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/")

    assert resp.status_code == 200
    assert "DailyFour" in resp.text


@pytest.mark.asyncio
async def test_lifespan_starts_and_stops_polling():
    """Wi-Fi polling task is created on startup and cancelled on shutdown."""
    with patch("app.wifi_detector.get_current_ssid", return_value="TestWifi"):
        with patch("app.main.wifi_polling_loop") as mock_loop:
            with patch("app.main.MongoDBStore.connect", new_callable=AsyncMock):
                with patch("app.main.MongoDBStore.close_stale_sessions", new_callable=AsyncMock, return_value=0):
                    with patch("app.main.MongoDBStore.disconnect", new_callable=AsyncMock):
                        with patch("app.main.NetworkConnectivityChecker.initialize", new_callable=AsyncMock):
                            with patch("app.main.NetworkConnectivityChecker.cleanup", new_callable=AsyncMock):
                                with patch("app.session_manager.SessionManager.recover_session", new_callable=AsyncMock, return_value=False):
                                    async def fake_loop(*args, **kwargs):
                                        await asyncio.sleep(999)

                                    mock_loop.side_effect = fake_loop

                                    # Use lifespan directly instead of going through ASGITransport
                                    async with lifespan(app):
                                        mock_loop.assert_called_once()
                                        # Background task should be registered
                                        assert len(_background_tasks) >= 1

    # After exiting, tasks should have been cancelled and cleared
    assert len(_background_tasks) == 0
