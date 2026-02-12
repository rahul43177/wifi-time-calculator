"""
Tests for Phase 1.2: Background Wi-Fi Polling Loop.

Verifies that wifi_polling_loop detects changes, calls the callback,
and handles errors without crashing.
"""

import asyncio
from unittest.mock import patch, MagicMock

import pytest

from app.wifi_detector import wifi_polling_loop


@pytest.fixture(autouse=True)
def _fast_polling():
    """Override polling interval to 0.1s for fast tests."""
    with patch("app.wifi_detector.settings") as mock_settings:
        mock_settings.wifi_check_interval_seconds = 0.1
        yield


@pytest.mark.asyncio
async def test_polling_loop_detects_initial_ssid():
    """Loop starts and captures initial SSID."""
    with patch("app.wifi_detector.get_current_ssid", return_value="OfficeWifi"):
        task = asyncio.create_task(wifi_polling_loop())
        await asyncio.sleep(0.05)  # let it capture initial state
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_polling_loop_calls_on_change():
    """Calls on_change callback when SSID changes."""
    # First call is initial capture, second is the poll that sees a change
    ssid_sequence = iter(["OfficeWifi", "HomeWifi"])
    changes = []

    def on_change(old, new):
        changes.append((old, new))

    with patch("app.wifi_detector.get_current_ssid", side_effect=lambda: next(ssid_sequence, "HomeWifi")):
        task = asyncio.create_task(wifi_polling_loop(on_change=on_change))
        await asyncio.sleep(0.3)  # enough for initial + at least 1 poll
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert len(changes) == 1
    assert changes[0] == ("OfficeWifi", "HomeWifi")


@pytest.mark.asyncio
async def test_polling_loop_no_callback_when_unchanged():
    """Does not call on_change when SSID stays the same."""
    changes = []

    with patch("app.wifi_detector.get_current_ssid", return_value="OfficeWifi"):
        task = asyncio.create_task(wifi_polling_loop(on_change=lambda o, n: changes.append((o, n))))
        await asyncio.sleep(0.3)  # several polls
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert changes == []


@pytest.mark.asyncio
async def test_polling_loop_survives_exception():
    """Loop continues running even if get_current_ssid raises."""
    call_count = 0

    def flaky_ssid():
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("Simulated failure")
        return "OfficeWifi"

    with patch("app.wifi_detector.get_current_ssid", side_effect=flaky_ssid):
        task = asyncio.create_task(wifi_polling_loop())
        await asyncio.sleep(0.5)  # enough for several polls
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    # Should have been called more than 2 times (loop didn't die at call 2)
    assert call_count >= 3


@pytest.mark.asyncio
async def test_polling_loop_cancels_cleanly():
    """Task can be cancelled without errors."""
    with patch("app.wifi_detector.get_current_ssid", return_value="OfficeWifi"):
        task = asyncio.create_task(wifi_polling_loop())
        await asyncio.sleep(0.15)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    # If we get here, no unexpected exceptions were raised
