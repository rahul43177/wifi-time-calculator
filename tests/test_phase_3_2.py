"""
Tests for Phase 3.2: Background Timer Loop.

Covers:
- Loop interval behavior
- Active-session-only checks
- Remaining/overtime logging
- Completion detection and notification trigger
- Runtime continuation after completion
- Invalid state handling and exception resilience
"""

import asyncio
import logging
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest

from app.session_manager import Session
from app.timer_engine import timer_polling_loop


async def _run_loop_for(duration_seconds: float) -> None:
    """Run timer_polling_loop briefly, then cancel cleanly."""
    task = asyncio.create_task(timer_polling_loop())
    await asyncio.sleep(duration_seconds)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def _active_session(
    *,
    date: str = "13-02-2026",
    ssid: str = "OfficeWifi",
    start_time: str = "09:00:00",
    completed_4h: bool = False,
) -> Session:
    """Create a deterministic active session object for tests."""
    return Session(
        date=date,
        ssid=ssid,
        start_time=start_time,
        completed_4h=completed_4h,
    )


@pytest.mark.asyncio
async def test_timer_loop_runs_repeated_checks_at_interval() -> None:
    """Loop should evaluate timer repeatedly based on configured interval."""
    manager = Mock()
    manager.active_session = _active_session()

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(hours=1)) as mock_elapsed:
                with patch(
                        "app.timer_engine.get_remaining_time",
                        return_value=timedelta(minutes=5),
                ):
                    with patch("app.timer_engine.is_completed", return_value=False):
                        await _run_loop_for(0.15)

    assert mock_elapsed.call_count >= 2


@pytest.mark.asyncio
async def test_timer_loop_checks_only_when_session_is_active() -> None:
    """No timer math should run when there is no active session."""
    manager = Mock()
    manager.active_session = None

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_remaining_time") as mock_remaining:
                with patch("app.timer_engine.get_elapsed_time") as mock_elapsed:
                    await _run_loop_for(0.06)

    mock_remaining.assert_not_called()
    mock_elapsed.assert_not_called()


@pytest.mark.asyncio
async def test_timer_loop_logs_remaining_time_before_completion(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When not complete, loop logs remaining time."""
    caplog.set_level(logging.INFO, logger="app.timer_engine")
    manager = Mock()
    manager.active_session = _active_session()

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(hours=1)):
                with patch(
                    "app.timer_engine.get_remaining_time",
                    return_value=timedelta(minutes=30),
                ):
                    with patch("app.timer_engine.is_completed", return_value=False):
                        await _run_loop_for(0.05)

    assert "Timer remaining:" in caplog.text


@pytest.mark.asyncio
async def test_timer_loop_logs_overtime_when_target_passed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When complete and overtime, loop logs overtime amount."""
    caplog.set_level(logging.INFO, logger="app.timer_engine")
    manager = Mock()
    manager.active_session = _active_session()

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(hours=5)):
                with patch(
                    "app.timer_engine.get_remaining_time",
                    return_value=timedelta(minutes=-20),
                ):
                    with patch("app.timer_engine.is_completed", return_value=True):
                        with patch("app.timer_engine.send_notification", return_value=True):
                            await _run_loop_for(0.05)

    assert "Timer overtime:" in caplog.text


@pytest.mark.asyncio
async def test_timer_loop_detects_completion_and_triggers_notification_once() -> None:
    """Completion should trigger one notification per active session runtime."""
    manager = Mock()
    manager.active_session = _active_session()

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(hours=5)):
                with patch(
                    "app.timer_engine.get_remaining_time",
                    return_value=timedelta(minutes=-10),
                ):
                    with patch("app.timer_engine.is_completed", return_value=True):
                        with patch(
                            "app.timer_engine.send_notification",
                            return_value=True,
                        ) as mock_notify:
                            await _run_loop_for(0.1)

    mock_notify.assert_called_once()
    title, message = mock_notify.call_args[0]
    assert title == "Office Wi-Fi Tracker"
    assert "4 hours + 10 min buffer completed" in message


@pytest.mark.asyncio
async def test_timer_loop_continues_tracking_after_completion() -> None:
    """Loop keeps calculating after completion for overtime tracking."""
    manager = Mock()
    manager.active_session = _active_session()

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(hours=6)):
                with patch(
                    "app.timer_engine.get_remaining_time",
                    return_value=timedelta(hours=-1),
                ) as mock_remaining:
                    with patch("app.timer_engine.is_completed", return_value=True):
                        with patch("app.timer_engine.send_notification", return_value=True):
                            # Increased from 0.1s to 0.15s to reduce timing flakiness
                            await _run_loop_for(0.15)

    assert mock_remaining.call_count >= 2


@pytest.mark.asyncio
async def test_timer_loop_skips_invalid_active_session_state() -> None:
    """Malformed session timestamps should be skipped safely."""
    manager = Mock()
    manager.active_session = _active_session(start_time="bad-time")

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_remaining_time") as mock_remaining:
                with patch("app.timer_engine.get_elapsed_time") as mock_elapsed:
                    await _run_loop_for(0.05)

    mock_remaining.assert_not_called()
    mock_elapsed.assert_not_called()


@pytest.mark.asyncio
async def test_timer_loop_survives_runtime_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unexpected exceptions during a tick are logged and loop continues."""
    manager = Mock()
    manager.active_session = _active_session()
    calls = {"count": 0}

    def flaky_remaining(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("simulated timer failure")
        return timedelta(minutes=5)

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(hours=1)):
                with patch("app.timer_engine.get_remaining_time", side_effect=flaky_remaining):
                    with patch("app.timer_engine.is_completed", return_value=False):
                        await _run_loop_for(0.08)

    assert "Error during timer poll" in caplog.text
    assert calls["count"] >= 2


@pytest.mark.asyncio
async def test_timer_loop_does_not_notify_if_session_already_marked_completed() -> None:
    """If session is already marked completed, no notification is sent."""
    manager = Mock()
    manager.active_session = _active_session(completed_4h=True)

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(hours=5)):
                with patch(
                    "app.timer_engine.get_remaining_time",
                    return_value=timedelta(minutes=-5),
                ):
                    with patch("app.timer_engine.is_completed", return_value=True):
                        with patch(
                            "app.timer_engine.send_notification",
                            return_value=True,
                        ) as mock_notify:
                            await _run_loop_for(0.06)

    mock_notify.assert_not_called()
