"""
Tests for Phase 3.5: Timer Integration with FastAPI Lifespan.

Verifies that the timer polling loop starts as a background task
alongside the Wi-Fi polling loop, and both stop gracefully on shutdown.
"""

import asyncio
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app, _background_tasks, lifespan


@pytest.mark.asyncio
async def test_lifespan_starts_both_wifi_and_timer_tasks():
    """Both Wi-Fi and timer polling tasks start on app startup."""
    with patch("app.main.get_current_ssid", return_value="TestWifi"):
        with patch("app.main.wifi_polling_loop") as mock_wifi_loop:
            with patch("app.main.timer_polling_loop") as mock_timer_loop:
                async def fake_loop(*args, **kwargs):
                    await asyncio.sleep(999)

                mock_wifi_loop.side_effect = fake_loop
                mock_timer_loop.side_effect = fake_loop

                async with lifespan(app):
                    mock_wifi_loop.assert_called_once()
                    mock_timer_loop.assert_called_once()
                    # Both tasks should be registered
                    assert len(_background_tasks) == 2

    # After exiting, tasks should be cancelled and cleared
    assert len(_background_tasks) == 0


@pytest.mark.asyncio
async def test_lifespan_stops_both_tasks_on_shutdown():
    """Both background tasks are cancelled cleanly on app shutdown."""
    with patch("app.main.get_current_ssid", return_value="TestWifi"):
        with patch("app.main.wifi_polling_loop") as mock_wifi_loop:
            with patch("app.main.timer_polling_loop") as mock_timer_loop:
                async def fake_loop(*args, **kwargs):
                    try:
                        await asyncio.sleep(999)
                    except asyncio.CancelledError:
                        raise

                mock_wifi_loop.side_effect = fake_loop
                mock_timer_loop.side_effect = fake_loop

                async with lifespan(app):
                    assert len(_background_tasks) == 2
                    for task in _background_tasks:
                        assert not task.done()

    # After context exit, both tasks should be cancelled
    assert len(_background_tasks) == 0


@pytest.mark.asyncio
async def test_timer_task_runs_alongside_wifi_task():
    """Timer and Wi-Fi tasks run concurrently without blocking each other."""
    wifi_called = False
    timer_called = False

    async def fake_wifi_loop(*args, **kwargs):
        nonlocal wifi_called
        wifi_called = True
        await asyncio.sleep(0.05)

    async def fake_timer_loop(*args, **kwargs):
        nonlocal timer_called
        timer_called = True
        await asyncio.sleep(0.05)

    with patch("app.main.get_current_ssid", return_value="TestWifi"):
        with patch("app.main.wifi_polling_loop", side_effect=fake_wifi_loop):
            with patch("app.main.timer_polling_loop", side_effect=fake_timer_loop):
                async with lifespan(app):
                    await asyncio.sleep(0.1)

    assert wifi_called, "Wi-Fi loop should have been called"
    assert timer_called, "Timer loop should have been called"


@pytest.mark.asyncio
async def test_health_endpoint_works_with_timer_integration():
    """Health check endpoint still works after timer integration."""
    with patch("app.main.get_current_ssid", return_value="TestWifi"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "work_duration_hours" in data


@pytest.mark.asyncio
async def test_lifespan_survives_timer_task_exception():
    """App continues running even if timer task encounters an exception."""
    with patch("app.main.get_current_ssid", return_value="TestWifi"):
        with patch("app.main.wifi_polling_loop") as mock_wifi_loop:
            with patch("app.main.timer_polling_loop") as mock_timer_loop:
                async def fake_wifi_loop(*args, **kwargs):
                    await asyncio.sleep(999)

                async def failing_timer_loop(*args, **kwargs):
                    raise RuntimeError("Timer task failure")

                mock_wifi_loop.side_effect = fake_wifi_loop
                mock_timer_loop.side_effect = failing_timer_loop

                # App should not crash; tasks are gathered with return_exceptions=True
                try:
                    async with lifespan(app):
                        await asyncio.sleep(0.05)
                        # Even if timer fails, Wi-Fi task should still exist
                        assert len(_background_tasks) == 2
                except RuntimeError:
                    pytest.fail("Lifespan should not propagate task exceptions")

    # Cleanup should still succeed
    assert len(_background_tasks) == 0


@pytest.mark.asyncio
async def test_lifespan_survives_wifi_task_exception():
    """App continues running even if Wi-Fi task encounters an exception."""
    with patch("app.main.get_current_ssid", return_value="TestWifi"):
        with patch("app.main.wifi_polling_loop") as mock_wifi_loop:
            with patch("app.main.timer_polling_loop") as mock_timer_loop:
                async def failing_wifi_loop(*args, **kwargs):
                    raise RuntimeError("Wi-Fi task failure")

                async def fake_timer_loop(*args, **kwargs):
                    await asyncio.sleep(999)

                mock_wifi_loop.side_effect = failing_wifi_loop
                mock_timer_loop.side_effect = fake_timer_loop

                # App should not crash
                try:
                    async with lifespan(app):
                        await asyncio.sleep(0.05)
                        # Even if Wi-Fi fails, timer task should still exist
                        assert len(_background_tasks) == 2
                except RuntimeError:
                    pytest.fail("Lifespan should not propagate task exceptions")

    # Cleanup should still succeed
    assert len(_background_tasks) == 0


@pytest.mark.asyncio
async def test_root_endpoint_works_with_timer_integration():
    """Root endpoint still returns HTML after timer integration."""
    with patch("app.main.get_current_ssid", return_value="TestWifi"):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/")

    assert resp.status_code == 200
    assert "Office Wi-Fi" in resp.text
