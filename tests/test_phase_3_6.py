"""
Tests for Phase 3.6: Testing Mode (Short Duration).

Covers:
- Test-mode target resolution (2-minute duration path)
- Easy toggle between test mode and normal mode
- Invalid-state handling for malformed test-mode inputs
- Timer-loop integration boundaries using mocked dependencies
"""

import asyncio
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest

from app.session_manager import Session
from app.timer_engine import _resolve_target_components, timer_polling_loop


def _active_session(
    *,
    date: str = "13-02-2026",
    ssid: str = "OfficeWifi",
    start_time: str = "09:00:00",
    completed_4h: bool = False,
) -> Session:
    """Create deterministic active session for timer-loop tests."""
    return Session(
        date=date,
        ssid=ssid,
        start_time=start_time,
        completed_4h=completed_4h,
    )


async def _run_loop_for(duration_seconds: float) -> None:
    """Run timer_polling_loop briefly, then cancel cleanly."""
    task = asyncio.create_task(timer_polling_loop())
    await asyncio.sleep(duration_seconds)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def test_resolve_target_components_normal_mode_uses_work_plus_buffer() -> None:
    """When test mode is OFF, normal target values are used."""
    hours, minutes = _resolve_target_components(
        test_mode=False,
        test_duration_minutes=2,
        work_duration_hours=4,
        buffer_minutes=10,
    )
    assert hours == 4
    assert minutes == 10


def test_resolve_target_components_test_mode_uses_short_minutes() -> None:
    """When test mode is ON, target becomes 0h + test_duration_minutes."""
    hours, minutes = _resolve_target_components(
        test_mode=True,
        test_duration_minutes=2,
        work_duration_hours=4,
        buffer_minutes=10,
    )
    assert hours == 0
    assert minutes == 2


def test_resolve_target_components_non_bool_test_mode_is_ignored() -> None:
    """Non-boolean test_mode values should not accidentally enable test mode."""
    hours, minutes = _resolve_target_components(
        test_mode="true",
        test_duration_minutes=2,
        work_duration_hours=4,
        buffer_minutes=10,
    )
    assert hours == 4
    assert minutes == 10


def test_resolve_target_components_invalid_test_duration_clamped_to_zero() -> None:
    """Invalid/negative test duration is clamped safely."""
    hours, minutes = _resolve_target_components(
        test_mode=True,
        test_duration_minutes=-5,
        work_duration_hours=4,
        buffer_minutes=10,
    )
    assert hours == 0
    assert minutes == 0


@pytest.mark.asyncio
async def test_timer_loop_uses_test_mode_duration_when_enabled() -> None:
    """Loop passes 0h + test_duration_minutes to timer math when test mode is ON."""
    manager = Mock()
    manager.active_session = _active_session()

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.test_mode = True
        mock_settings.test_duration_minutes = 2
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(minutes=1)):
                with patch(
                    "app.timer_engine.get_remaining_time",
                    return_value=timedelta(minutes=1),
                ) as mock_remaining:
                    with patch("app.timer_engine.is_completed", return_value=False):
                        await _run_loop_for(0.05)

    assert mock_remaining.call_count >= 1
    _, kwargs = mock_remaining.call_args
    assert kwargs["target_hours"] == 0
    assert kwargs["buffer_minutes"] == 2


@pytest.mark.asyncio
async def test_timer_loop_uses_normal_duration_when_test_mode_disabled() -> None:
    """Loop keeps normal 4h + buffer values when test mode is OFF."""
    manager = Mock()
    manager.active_session = _active_session()

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.test_mode = False
        mock_settings.test_duration_minutes = 2
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(minutes=1)):
                with patch(
                    "app.timer_engine.get_remaining_time",
                    return_value=timedelta(hours=4, minutes=9),
                ) as mock_remaining:
                    with patch("app.timer_engine.is_completed", return_value=False):
                        await _run_loop_for(0.05)

    assert mock_remaining.call_count >= 1
    _, kwargs = mock_remaining.call_args
    assert kwargs["target_hours"] == 4
    assert kwargs["buffer_minutes"] == 10


@pytest.mark.asyncio
async def test_timer_loop_uses_test_mode_message_on_completion() -> None:
    """Completion notification text reflects short test-mode duration."""
    manager = Mock()
    manager.active_session = _active_session(completed_4h=False)

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.test_mode = True
        mock_settings.test_duration_minutes = 2
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(minutes=3)):
                with patch(
                    "app.timer_engine.get_remaining_time",
                    return_value=timedelta(minutes=-1),
                ):
                    with patch("app.timer_engine.is_completed", return_value=True):
                        with patch("app.timer_engine.update_session", return_value=True):
                            with patch("app.timer_engine.send_notification", return_value=True) as mock_notify:
                                await _run_loop_for(0.06)

    mock_notify.assert_called_once()
    title, message = mock_notify.call_args[0]
    assert title == "Office Wi-Fi Tracker"
    assert message == "Test mode: 2 min completed. You may leave."
