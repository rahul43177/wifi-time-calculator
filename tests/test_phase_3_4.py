"""
Tests for Phase 3.4: Completion Flag Persistence.

Covers:
- In-place completion flag update in session log
- Update idempotency and malformed-state handling
- Timer loop integration for immediate completion persistence
"""

import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from app.file_store import get_log_path, read_sessions, update_session
from app.session_manager import Session
from app.timer_engine import timer_polling_loop


def _write_log_lines(log_path, lines: list[dict | str]) -> None:
    """Write raw JSON-lines content to a log path for deterministic setup."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        for item in lines:
            if isinstance(item, str):
                f.write(item + "\n")
            else:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _active_session(
    *,
    date: str = "13-02-2026",
    ssid: str = "OfficeWifi",
    start_time: str = "09:00:00",
    completed_4h: bool = False,
) -> Session:
    """Create deterministic in-memory session object."""
    return Session(
        date=date,
        ssid=ssid,
        start_time=start_time,
        completed_4h=completed_4h,
    )


async def _run_loop_for(duration_seconds: float) -> None:
    """Run timer_polling_loop briefly and cancel cleanly."""
    task = asyncio.create_task(timer_polling_loop())
    await asyncio.sleep(duration_seconds)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def test_update_session_sets_completed_flag_for_latest_matching_entry() -> None:
    """Latest matching active snapshot is updated in-place."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.file_store.settings") as mock_settings:
            mock_settings.data_dir = tmpdir
            mock_settings.archive_dir = f"{tmpdir}/archive"
            day = datetime(2026, 2, 13)
            log_path = get_log_path(day)
            _write_log_lines(
                log_path,
                [
                    {
                        "date": "13-02-2026",
                        "ssid": "OfficeWifi",
                        "start_time": "09:00:00",
                        "end_time": None,
                        "completed_4h": False,
                    },
                    {
                        "date": "13-02-2026",
                        "ssid": "OfficeWifi",
                        "start_time": "09:00:00",
                        "end_time": None,
                        "completed_4h": False,
                    },
                ],
            )

            ok = update_session(
                session_date="13-02-2026",
                ssid="OfficeWifi",
                start_time="09:00:00",
                updates={"completed_4h": True},
            )

            assert ok is True
            sessions = read_sessions(day)
            assert sessions[0]["completed_4h"] is False
            assert sessions[1]["completed_4h"] is True


def test_update_session_returns_false_when_no_matching_active_entry() -> None:
    """No matching session should return False and keep file unchanged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.file_store.settings") as mock_settings:
            mock_settings.data_dir = tmpdir
            mock_settings.archive_dir = f"{tmpdir}/archive"
            day = datetime(2026, 2, 13)
            log_path = get_log_path(day)
            _write_log_lines(
                log_path,
                [
                    {
                        "date": "13-02-2026",
                        "ssid": "OtherWifi",
                        "start_time": "09:00:00",
                        "end_time": None,
                        "completed_4h": False,
                    }
                ],
            )

            ok = update_session(
                session_date="13-02-2026",
                ssid="OfficeWifi",
                start_time="09:00:00",
                updates={"completed_4h": True},
            )

            assert ok is False
            sessions = read_sessions(day)
            assert sessions[0]["completed_4h"] is False


def test_update_session_returns_false_when_already_up_to_date() -> None:
    """No-op updates are rejected so completion is persisted only once."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.file_store.settings") as mock_settings:
            mock_settings.data_dir = tmpdir
            mock_settings.archive_dir = f"{tmpdir}/archive"
            day = datetime(2026, 2, 13)
            log_path = get_log_path(day)
            _write_log_lines(
                log_path,
                [
                    {
                        "date": "13-02-2026",
                        "ssid": "OfficeWifi",
                        "start_time": "09:00:00",
                        "end_time": None,
                        "completed_4h": True,
                    }
                ],
            )

            ok = update_session(
                session_date="13-02-2026",
                ssid="OfficeWifi",
                start_time="09:00:00",
                updates={"completed_4h": True},
            )

            assert ok is False


def test_update_session_handles_corrupted_lines_and_updates_valid_entry() -> None:
    """Corrupted lines are skipped while valid target entry is still updated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.file_store.settings") as mock_settings:
            mock_settings.data_dir = tmpdir
            mock_settings.archive_dir = f"{tmpdir}/archive"
            day = datetime(2026, 2, 13)
            log_path = get_log_path(day)
            _write_log_lines(
                log_path,
                [
                    '{"date":"13-02-2026","ssid":"OfficeWifi","start_time":"08:00:00"',
                    {
                        "date": "13-02-2026",
                        "ssid": "OfficeWifi",
                        "start_time": "09:00:00",
                        "end_time": None,
                        "completed_4h": False,
                    },
                ],
            )

            ok = update_session(
                session_date="13-02-2026",
                ssid="OfficeWifi",
                start_time="09:00:00",
                updates={"completed_4h": True},
            )

            assert ok is True
            sessions = read_sessions(day)
            assert sessions[0]["completed_4h"] is True


def test_update_session_invalid_date_returns_false() -> None:
    """Invalid date format is rejected safely."""
    ok = update_session(
        session_date="2026-02-13",
        ssid="OfficeWifi",
        start_time="09:00:00",
        updates={"completed_4h": True},
    )
    assert ok is False


@pytest.mark.asyncio
async def test_timer_loop_persists_completion_immediately() -> None:
    """First completion tick should persist completed_4h and set in-memory flag."""
    manager = Mock()
    manager.active_session = _active_session(completed_4h=False)

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(hours=5)):
                with patch("app.timer_engine.get_remaining_time", return_value=timedelta(minutes=-5)):
                    with patch("app.timer_engine.is_completed", return_value=True):
                        with patch("app.timer_engine.update_session", return_value=True) as mock_update:
                            with patch("app.timer_engine.send_notification", return_value=True):
                                await _run_loop_for(0.06)

    mock_update.assert_called_once_with(
        session_date="13-02-2026",
        ssid="OfficeWifi",
        start_time="09:00:00",
        updates={"completed_4h": True},
    )
    assert manager.active_session.completed_4h is True


@pytest.mark.asyncio
async def test_timer_loop_does_not_repeat_persistence_for_completed_session() -> None:
    """Once marked completed, no additional update_session calls are made."""
    manager = Mock()
    manager.active_session = _active_session(completed_4h=True)

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(hours=5)):
                with patch("app.timer_engine.get_remaining_time", return_value=timedelta(minutes=-5)):
                    with patch("app.timer_engine.is_completed", return_value=True):
                        with patch("app.timer_engine.update_session") as mock_update:
                            with patch("app.timer_engine.send_notification", return_value=True):
                                await _run_loop_for(0.06)

    mock_update.assert_not_called()


@pytest.mark.asyncio
async def test_timer_loop_retries_completion_persist_when_update_fails() -> None:
    """Persistence failures are retried on subsequent ticks while session stays active."""
    manager = Mock()
    manager.active_session = _active_session(completed_4h=False)

    with patch("app.timer_engine.settings") as mock_settings:
        mock_settings.timer_check_interval_seconds = 0.02
        mock_settings.work_duration_hours = 4
        mock_settings.buffer_minutes = 10
        with patch("app.timer_engine.get_session_manager", return_value=manager):
            with patch("app.timer_engine.get_elapsed_time", return_value=timedelta(hours=5)):
                with patch("app.timer_engine.get_remaining_time", return_value=timedelta(minutes=-5)):
                    with patch("app.timer_engine.is_completed", return_value=True):
                        with patch("app.timer_engine.update_session", return_value=False) as mock_update:
                            with patch("app.timer_engine.send_notification", return_value=True):
                                await _run_loop_for(0.08)

    assert mock_update.call_count >= 2
