"""
Tests for Phase 2.6: Data Validation.

Covers:
- Valid payload persistence through SessionLog validation
- Invalid date/time/duration rejection with clear messages
- Empty/whitespace SSID rejection
- Corrupted in-memory state handling during session end
- Malformed log entry rejection during recovery
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from app.session_manager import Session, SessionManager, SessionState


def _now_fixed(dt: datetime):
    """Return a deterministic now_provider that always returns dt."""
    return lambda: dt


def test_persist_state_valid_payload_is_saved() -> None:
    """Valid session data passes validation and is persisted."""
    persist = Mock(return_value=True)
    manager = SessionManager(persist_func=persist)
    session = Session(
        date="12-02-2026",
        ssid="OfficeWifi",
        start_time="09:00:00",
        end_time="10:00:00",
        duration_minutes=60,
        completed_4h=False,
    )

    ok = manager._persist_state(session)

    assert ok is True
    persist.assert_called_once()
    payload = persist.call_args[0][0]
    assert payload["date"] == "12-02-2026"
    assert payload["start_time"] == "09:00:00"
    assert payload["duration_minutes"] == 60


def test_persist_state_rejects_invalid_session_data_and_logs_clear_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Invalid date/time/duration is rejected before persistence."""
    persist = Mock(return_value=True)
    manager = SessionManager(persist_func=persist)
    invalid = Session.model_construct(  # bypass model validation intentionally
        date="2026-02-12",
        ssid="OfficeWifi",
        start_time="9:00",
        end_time=None,
        duration_minutes=-5,
        completed_4h=False,
    )

    ok = manager._persist_state(invalid)

    assert ok is False
    persist.assert_not_called()
    assert "Session validation failed" in caplog.text
    assert "date" in caplog.text
    assert "DD-MM-YYYY" in caplog.text
    assert "start_time" in caplog.text
    assert "HH:MM:SS" in caplog.text
    assert "duration_minutes" in caplog.text


def test_persist_state_rejects_empty_ssid_with_clear_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Whitespace SSID is rejected and reported clearly."""
    persist = Mock(return_value=True)
    manager = SessionManager(persist_func=persist)
    invalid = Session.model_construct(
        date="12-02-2026",
        ssid="   ",
        start_time="09:00:00",
        end_time=None,
        duration_minutes=5,
        completed_4h=False,
    )

    ok = manager._persist_state(invalid)

    assert ok is False
    persist.assert_not_called()
    assert "ssid" in caplog.text
    assert "must not be empty" in caplog.text


def test_persist_state_rejects_invalid_end_time_format(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Invalid end_time format is rejected before persistence."""
    persist = Mock(return_value=True)
    manager = SessionManager(persist_func=persist)
    invalid = Session.model_construct(
        date="12-02-2026",
        ssid="OfficeWifi",
        start_time="09:00:00",
        end_time="10:00",
        duration_minutes=60,
        completed_4h=False,
    )

    ok = manager._persist_state(invalid)

    assert ok is False
    persist.assert_not_called()
    assert "end_time" in caplog.text
    assert "HH:MM:SS" in caplog.text


def test_end_session_rejects_corrupted_active_session_data() -> None:
    """Corrupted in-memory data is rejected and state remains unchanged."""
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_fixed(datetime(2026, 2, 12, 10, 0, 0)),
    )

    assert manager.start_session("OfficeWifi") is True
    assert manager.active_session is not None
    manager.active_session = manager.active_session.model_copy(update={"start_time": "bad-time"})

    ok = manager.end_session()

    assert ok is False
    assert manager.state == SessionState.IN_OFFICE_SESSION
    assert manager.active_session is not None
    assert manager.active_session.end_time is None
    # Only start snapshot should have persisted; end snapshot rejected by validation.
    assert persist.call_count == 1


def test_recover_session_rejects_invalid_log_entry_with_clear_handling() -> None:
    """Recover ignores invalid data shape/format and stays in a safe IDLE state."""
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        read_sessions_func=lambda: [
            {
                "date": "2026-02-12",  # wrong format
                "ssid": "OfficeWifi",
                "start_time": "09:00:00",
                "end_time": None,
            }
        ],
    )

    recovered = manager.recover_session("OfficeWifi")

    assert recovered is False
    assert manager.state == SessionState.IDLE
    assert manager.active_session is None
    persist.assert_not_called()
