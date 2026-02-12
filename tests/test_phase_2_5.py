"""
Tests for Phase 2.5: Session Recovery on Restart.

Covers:
- Resume incomplete session when still connected to office Wi-Fi
- Close stale incomplete session when disconnected
- No recovery when no sessions exist for today
- No recovery when all sessions are already completed
- No recovery when session already active (not IDLE)
- Malformed session entries are skipped gracefully
- Multiple incomplete sessions — only the last one is considered
- Lifespan integration calls recover_session on startup
"""

import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.session_manager import SessionManager, SessionState


def _now_fixed(dt: datetime):
    """Return a deterministic now_provider that always returns dt."""
    return lambda: dt


# --- Happy path: resume session ---


def test_recover_resumes_incomplete_session_when_still_connected() -> None:
    """Incomplete session + same SSID connected → IN_OFFICE_SESSION."""
    log_data = [
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "09:00:00",
            "end_time": None,
            "duration_minutes": None,
            "completed_4h": False,
        }
    ]
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_fixed(datetime(2026, 2, 12, 11, 0, 0)),
        read_sessions_func=lambda: log_data,
    )

    result = manager.recover_session("OfficeWifi")

    assert result is True
    assert manager.state == SessionState.IN_OFFICE_SESSION
    assert manager.active_session is not None
    assert manager.active_session.ssid == "OfficeWifi"
    assert manager.active_session.start_time == "09:00:00"
    # Resume does NOT persist — it's restoring in-memory state
    persist.assert_not_called()


# --- Happy path: close stale session ---


def test_recover_closes_stale_session_when_disconnected() -> None:
    """Incomplete session + different SSID → close session and stay IDLE."""
    log_data = [
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "09:00:00",
            "end_time": None,
            "duration_minutes": None,
            "completed_4h": False,
        }
    ]
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_fixed(datetime(2026, 2, 12, 11, 30, 0)),
        read_sessions_func=lambda: log_data,
    )

    result = manager.recover_session("HomeWifi")

    assert result is False
    assert manager.state == SessionState.IDLE
    assert manager.active_session is None
    # Should have persisted a close record
    persist.assert_called_once()
    closed_payload = persist.call_args[0][0]
    assert closed_payload["end_time"] == "11:30:00"
    assert closed_payload["duration_minutes"] == 150  # 2.5 hours


def test_recover_closes_stale_session_when_wifi_disconnected() -> None:
    """Incomplete session + current_ssid is None → close session."""
    log_data = [
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "14:00:00",
            "end_time": None,
            "duration_minutes": None,
            "completed_4h": False,
        }
    ]
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_fixed(datetime(2026, 2, 12, 15, 0, 0)),
        read_sessions_func=lambda: log_data,
    )

    result = manager.recover_session(None)

    assert result is False
    assert manager.state == SessionState.IDLE
    persist.assert_called_once()
    closed_payload = persist.call_args[0][0]
    assert closed_payload["end_time"] == "15:00:00"
    assert closed_payload["duration_minutes"] == 60


# --- No recovery scenarios ---


def test_recover_returns_false_when_no_sessions_today() -> None:
    """Empty log → no recovery, stays IDLE."""
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        read_sessions_func=lambda: [],
    )

    result = manager.recover_session("OfficeWifi")

    assert result is False
    assert manager.state == SessionState.IDLE
    assert manager.active_session is None
    persist.assert_not_called()


def test_recover_returns_false_when_all_sessions_completed() -> None:
    """All sessions have end_time → nothing to recover."""
    log_data = [
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "09:00:00",
            "end_time": "13:00:00",
            "duration_minutes": 240,
            "completed_4h": True,
        },
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "09:00:00",
            "end_time": "13:00:00",
            "duration_minutes": 240,
            "completed_4h": True,
        },
    ]
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        read_sessions_func=lambda: log_data,
    )

    result = manager.recover_session("OfficeWifi")

    assert result is False
    assert manager.state == SessionState.IDLE
    persist.assert_not_called()


# --- Edge cases ---


def test_recover_skipped_when_session_already_active() -> None:
    """If a session is already active, recovery is skipped."""
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_fixed(datetime(2026, 2, 12, 9, 0, 0)),
        read_sessions_func=lambda: [
            {
                "date": "12-02-2026",
                "ssid": "OfficeWifi",
                "start_time": "08:00:00",
                "end_time": None,
            }
        ],
    )

    # Start a session first
    manager.start_session("OfficeWifi")
    persist.reset_mock()

    result = manager.recover_session("OfficeWifi")

    assert result is False
    assert manager.state == SessionState.IN_OFFICE_SESSION
    persist.assert_not_called()


def test_recover_uses_last_incomplete_session_when_multiple_exist() -> None:
    """When multiple incomplete sessions exist, the last one is recovered."""
    log_data = [
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "08:00:00",
            "end_time": None,
            "completed_4h": False,
        },
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "08:00:00",
            "end_time": "12:00:00",
            "duration_minutes": 240,
            "completed_4h": True,
        },
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "14:00:00",
            "end_time": None,
            "completed_4h": False,
        },
    ]
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        read_sessions_func=lambda: log_data,
    )

    result = manager.recover_session("OfficeWifi")

    assert result is True
    assert manager.active_session is not None
    assert manager.active_session.start_time == "14:00:00"


def test_recover_handles_malformed_session_entry() -> None:
    """Malformed session entries are skipped without crashing."""
    log_data = [
        {
            # Missing 'ssid' key — will fail Session() construction
            "date": "12-02-2026",
            "start_time": "09:00:00",
            "end_time": None,
        }
    ]
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        read_sessions_func=lambda: log_data,
    )

    result = manager.recover_session("OfficeWifi")

    assert result is False
    assert manager.state == SessionState.IDLE
    persist.assert_not_called()


def test_recover_handles_read_sessions_exception() -> None:
    """If read_sessions raises, recover_session catches it and returns False."""
    def exploding_reader():
        raise OSError("disk failure")

    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        read_sessions_func=exploding_reader,
    )

    result = manager.recover_session("OfficeWifi")

    assert result is False
    assert manager.state == SessionState.IDLE
    persist.assert_not_called()


# --- Lifespan integration ---


def test_recover_stale_close_persist_failure_logs_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When stale-close persist fails, a warning is logged."""
    log_data = [
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "09:00:00",
            "end_time": None,
            "completed_4h": False,
        }
    ]
    persist = Mock(return_value=False)  # persist fails
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_fixed(datetime(2026, 2, 12, 11, 0, 0)),
        read_sessions_func=lambda: log_data,
    )

    result = manager.recover_session("HomeWifi")

    assert result is False
    assert manager.state == SessionState.IDLE
    persist.assert_called_once()
    assert "failed to persist stale session close" in caplog.text


# --- Lifespan integration ---


@pytest.mark.asyncio
async def test_lifespan_calls_recover_session_on_startup() -> None:
    """Lifespan triggers session recovery before starting the polling loop."""
    from app.main import lifespan, app

    mock_manager = Mock()
    mock_manager.recover_session.return_value = False
    mock_manager.state = SessionState.IN_OFFICE_SESSION  # simulate already active

    with patch("app.main.get_current_ssid", return_value="OfficeWifi"):
        with patch("app.main.get_session_manager", return_value=mock_manager):
            with patch("app.main.settings") as mock_settings:
                mock_settings.office_wifi_name = "OfficeWifi"
                mock_settings.work_duration_hours = 4
                mock_settings.log_level = "INFO"
                mock_settings.log_to_file = False
                with patch("app.main.wifi_polling_loop") as mock_loop:
                    async def fake_loop(*args, **kwargs):
                        await asyncio.sleep(999)

                    mock_loop.side_effect = fake_loop

                    async with lifespan(app):
                        mock_manager.recover_session.assert_called_once_with("OfficeWifi")


@pytest.mark.asyncio
async def test_lifespan_starts_new_session_when_on_office_wifi_no_recovery() -> None:
    """If recovery returns False but we're on office Wi-Fi, a new session is started."""
    from app.main import lifespan, app

    mock_manager = Mock()
    mock_manager.recover_session.return_value = False
    mock_manager.state = SessionState.IDLE  # not recovered, still idle

    with patch("app.main.get_current_ssid", return_value="OfficeWifi"):
        with patch("app.main.get_session_manager", return_value=mock_manager):
            with patch("app.main.settings") as mock_settings:
                mock_settings.office_wifi_name = "OfficeWifi"
                mock_settings.work_duration_hours = 4
                mock_settings.log_level = "INFO"
                mock_settings.log_to_file = False
                with patch("app.main.wifi_polling_loop") as mock_loop:
                    async def fake_loop(*args, **kwargs):
                        await asyncio.sleep(999)

                    mock_loop.side_effect = fake_loop

                    async with lifespan(app):
                        mock_manager.start_session.assert_called_once_with("OfficeWifi")


@pytest.mark.asyncio
async def test_lifespan_no_new_session_when_not_on_office_wifi() -> None:
    """If not on office Wi-Fi and no recovery, no session is started."""
    from app.main import lifespan, app

    mock_manager = Mock()
    mock_manager.recover_session.return_value = False
    mock_manager.state = SessionState.IDLE

    with patch("app.main.get_current_ssid", return_value="HomeWifi"):
        with patch("app.main.get_session_manager", return_value=mock_manager):
            with patch("app.main.settings") as mock_settings:
                mock_settings.office_wifi_name = "OfficeWifi"
                mock_settings.work_duration_hours = 4
                mock_settings.log_level = "INFO"
                mock_settings.log_to_file = False
                with patch("app.main.wifi_polling_loop") as mock_loop:
                    async def fake_loop(*args, **kwargs):
                        await asyncio.sleep(999)

                    mock_loop.side_effect = fake_loop

                    async with lifespan(app):
                        mock_manager.start_session.assert_not_called()

