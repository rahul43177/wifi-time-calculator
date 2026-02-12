"""
Tests for Phase 2.2: Session State Machine.

Covers:
- Initial IDLE state
- Start/end/completion state transitions
- Persistence calls on each state change
- Edge cases for invalid transition attempts
"""

from datetime import datetime
from unittest.mock import Mock

from app.session_manager import Session, SessionManager, SessionState


def _now_sequence(values: list[datetime]):
    """Create a deterministic now_provider from a datetime sequence."""
    iterator = iter(values)
    return lambda: next(iterator)


def test_initial_state_is_idle() -> None:
    """SessionManager starts in IDLE with no active session."""
    manager = SessionManager(persist_func=Mock(return_value=True))

    assert manager.state == SessionState.IDLE
    assert manager.active_session is None


def test_start_session_transitions_to_in_office_and_persists() -> None:
    """IDLE + office Wi-Fi detected -> IN_OFFICE_SESSION and persisted."""
    persist = Mock(return_value=True)
    now = datetime(2026, 2, 12, 9, 30, 0)
    manager = SessionManager(persist_func=persist, now_provider=lambda: now)

    ok = manager.start_session("OfficeWifi")

    assert ok is True
    assert manager.state == SessionState.IN_OFFICE_SESSION
    assert manager.active_session is not None
    assert manager.active_session.ssid == "OfficeWifi"
    assert manager.active_session.date == "12-02-2026"
    assert manager.active_session.start_time == "09:30:00"
    assert manager.active_session.completed_4h is False
    persist.assert_called_once()
    persisted_payload = persist.call_args[0][0]
    assert persisted_payload["ssid"] == "OfficeWifi"
    assert persisted_payload["start_time"] == "09:30:00"
    assert persisted_payload["end_time"] is None


def test_end_session_transitions_to_idle_and_persists() -> None:
    """IN_OFFICE_SESSION + disconnect -> IDLE with end_time persisted."""
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_sequence(
            [
                datetime(2026, 2, 12, 9, 0, 0),   # start
                datetime(2026, 2, 12, 10, 30, 0),  # end
            ]
        ),
    )

    assert manager.start_session("OfficeWifi") is True
    ok = manager.end_session()

    assert ok is True
    assert manager.state == SessionState.IDLE
    assert manager.active_session is None
    assert persist.call_count == 2
    end_payload = persist.call_args_list[1][0][0]
    assert end_payload["end_time"] == "10:30:00"
    assert end_payload["duration_minutes"] == 90


def test_mark_completed_transitions_to_completed_and_persists() -> None:
    """IN_OFFICE_SESSION + 4h complete -> COMPLETED with completed_4h persisted."""
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_sequence(
            [
                datetime(2026, 2, 12, 9, 0, 0),   # start
                datetime(2026, 2, 12, 13, 1, 0),  # complete mark
            ]
        ),
    )

    assert manager.start_session("OfficeWifi") is True
    ok = manager.mark_session_completed()

    assert ok is True
    assert manager.state == SessionState.COMPLETED
    assert manager.active_session is not None
    assert manager.active_session.completed_4h is True
    assert persist.call_count == 2
    complete_payload = persist.call_args_list[1][0][0]
    assert complete_payload["completed_4h"] is True
    assert complete_payload["duration_minutes"] == 241


def test_double_start_is_prevented() -> None:
    """Second start request while active session exists is rejected."""
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_sequence(
            [
                datetime(2026, 2, 12, 9, 0, 0),
                datetime(2026, 2, 12, 9, 5, 0),
            ]
        ),
    )

    assert manager.start_session("OfficeWifi") is True
    second = manager.start_session("OfficeWifi")

    assert second is False
    assert manager.state == SessionState.IN_OFFICE_SESSION
    assert persist.call_count == 1


def test_end_without_active_session_returns_false() -> None:
    """Ending without active session does not persist and returns False."""
    persist = Mock(return_value=True)
    manager = SessionManager(persist_func=persist)

    ok = manager.end_session()

    assert ok is False
    assert manager.state == SessionState.IDLE
    persist.assert_not_called()


def test_completion_without_active_session_returns_false() -> None:
    """Completion without in-progress session does not persist and returns False."""
    persist = Mock(return_value=True)
    manager = SessionManager(persist_func=persist)

    ok = manager.mark_session_completed()

    assert ok is False
    assert manager.state == SessionState.IDLE
    persist.assert_not_called()


def test_end_session_from_completed_state_transitions_to_idle() -> None:
    """COMPLETED + end_session -> IDLE with final end snapshot persisted."""
    persist = Mock(return_value=True)
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_sequence(
            [
                datetime(2026, 2, 12, 9, 0, 0),   # start
                datetime(2026, 2, 12, 13, 0, 0),  # mark completed
                datetime(2026, 2, 12, 13, 10, 0),  # end
            ]
        ),
    )

    assert manager.start_session("OfficeWifi") is True
    assert manager.mark_session_completed() is True
    ok = manager.end_session()

    assert ok is True
    assert manager.state == SessionState.IDLE
    assert manager.active_session is None
    assert persist.call_count == 3
    end_payload = persist.call_args_list[2][0][0]
    assert end_payload["completed_4h"] is True
    assert end_payload["end_time"] == "13:10:00"
    assert end_payload["duration_minutes"] == 250


def test_end_session_persistence_failure_keeps_state_unchanged() -> None:
    """If end persistence fails, session remains active and state is unchanged."""
    persist = Mock(side_effect=[True, False])
    manager = SessionManager(
        persist_func=persist,
        now_provider=_now_sequence(
            [
                datetime(2026, 2, 12, 9, 0, 0),   # start
                datetime(2026, 2, 12, 10, 0, 0),  # failed end attempt
            ]
        ),
    )

    assert manager.start_session("OfficeWifi") is True
    ok = manager.end_session()

    assert ok is False
    assert manager.state == SessionState.IN_OFFICE_SESSION
    assert manager.active_session is not None
    assert manager.active_session.end_time is None
    assert persist.call_count == 2


def test_calculate_duration_minutes_handles_midnight_rollover() -> None:
    """Duration calculation works when session crosses midnight."""
    session = Session(
        date="12-02-2026",
        ssid="OfficeWifi",
        start_time="23:50:00",
    )
    now = datetime(2026, 2, 13, 0, 10, 0)

    duration = SessionManager._calculate_duration_minutes(session, now)

    assert duration == 20


def test_calculate_duration_minutes_handles_negative_elapsed() -> None:
    """Clock-skew negative elapsed values are clamped to zero."""
    session = Session(
        date="12-02-2026",
        ssid="OfficeWifi",
        start_time="09:00:00",
    )
    now = datetime(2026, 2, 12, 8, 59, 0)

    duration = SessionManager._calculate_duration_minutes(session, now)

    assert duration == 0


def test_calculate_duration_minutes_invalid_datetime_returns_none() -> None:
    """Malformed session datetime strings return None instead of raising."""
    session = Session(
        date="invalid-date",
        ssid="OfficeWifi",
        start_time="bad-time",
    )
    now = datetime(2026, 2, 12, 10, 0, 0)

    duration = SessionManager._calculate_duration_minutes(session, now)

    assert duration is None
