"""
Tests for Phase 2.3: Session Manager + Wi-Fi Detector integration.

Covers:
- Office connect triggers session start
- Office disconnect triggers session end
- Non-office changes do not affect sessions
- Multiple connect/disconnect cycles
- Persistence to daily log file via integrated flow
"""

import asyncio
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.file_store import append_session, read_sessions
from app.session_manager import SessionManager
from app.wifi_detector import process_ssid_change, wifi_polling_loop


def _now_sequence(values: list[datetime]):
    """Create a deterministic now_provider from a datetime sequence."""
    iterator = iter(values)
    return lambda: next(iterator)


def test_process_ssid_change_starts_session_on_office_connect() -> None:
    """Non-office -> office triggers start_session once."""
    manager = Mock()
    with patch("app.wifi_detector.settings") as mock_settings:
        mock_settings.office_wifi_name = "OfficeWifi"
        with patch("app.wifi_detector.get_session_manager", return_value=manager):
            process_ssid_change("HomeWifi", "OfficeWifi")

    manager.start_session.assert_called_once_with("OfficeWifi")
    manager.end_session.assert_not_called()


def test_process_ssid_change_ends_session_on_office_disconnect() -> None:
    """Office -> non-office triggers end_session once."""
    manager = Mock()
    with patch("app.wifi_detector.settings") as mock_settings:
        mock_settings.office_wifi_name = "OfficeWifi"
        with patch("app.wifi_detector.get_session_manager", return_value=manager):
            process_ssid_change("OfficeWifi", "GuestWifi")

    manager.end_session.assert_called_once_with()
    manager.start_session.assert_not_called()


def test_process_ssid_change_ignores_non_office_transition() -> None:
    """Non-office -> non-office should not start or end sessions."""
    manager = Mock()
    with patch("app.wifi_detector.settings") as mock_settings:
        mock_settings.office_wifi_name = "OfficeWifi"
        with patch("app.wifi_detector.get_session_manager", return_value=manager):
            process_ssid_change("HomeWifi", "GuestWifi")

    manager.start_session.assert_not_called()
    manager.end_session.assert_not_called()


def test_process_ssid_change_supports_multiple_cycles() -> None:
    """Multiple connect/disconnect cycles call start/end repeatedly."""
    manager = Mock()
    with patch("app.wifi_detector.settings") as mock_settings:
        mock_settings.office_wifi_name = "OfficeWifi"
        with patch("app.wifi_detector.get_session_manager", return_value=manager):
            process_ssid_change(None, "OfficeWifi")
            process_ssid_change("OfficeWifi", None)
            process_ssid_change(None, "OfficeWifi")
            process_ssid_change("OfficeWifi", "HomeWifi")

    assert manager.start_session.call_count == 2
    assert manager.end_session.call_count == 2


def test_process_ssid_change_survives_session_manager_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Session manager exceptions are logged and do not escape."""
    manager = Mock()
    manager.start_session.side_effect = RuntimeError("simulated failure")

    with patch("app.wifi_detector.settings") as mock_settings:
        mock_settings.office_wifi_name = "OfficeWifi"
        with patch("app.wifi_detector.get_session_manager", return_value=manager):
            process_ssid_change("HomeWifi", "OfficeWifi")

    assert "Failed to process session transition for SSID change" in caplog.text


@pytest.mark.asyncio
async def test_wifi_polling_loop_routes_changes_to_process_ssid_change() -> None:
    """Polling loop should call process_ssid_change when SSID changes."""
    with patch("app.wifi_detector.settings") as mock_settings:
        mock_settings.wifi_check_interval_seconds = 0.1
        mock_settings.office_wifi_name = "OfficeWifi"
        with patch(
            "app.wifi_detector.get_current_ssid",
            side_effect=["HomeWifi", "OfficeWifi", "OfficeWifi"],
        ):
            with patch("app.wifi_detector.process_ssid_change") as mock_process:
                task = asyncio.create_task(wifi_polling_loop())
                await asyncio.sleep(0.3)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task

    mock_process.assert_called_once_with("HomeWifi", "OfficeWifi")


def test_integration_persists_sessions_to_daily_log_file() -> None:
    """Office connect/disconnect writes session snapshots to daily log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.file_store.settings") as mock_file_settings:
            mock_file_settings.data_dir = tmpdir
            manager = SessionManager(
                persist_func=append_session,
                now_provider=_now_sequence(
                    [
                        datetime(2026, 2, 12, 9, 0, 0),
                        datetime(2026, 2, 12, 13, 5, 0),
                    ]
                ),
            )
            with patch("app.wifi_detector.settings") as mock_wifi_settings:
                mock_wifi_settings.office_wifi_name = "OfficeWifi"
                with patch("app.wifi_detector.get_session_manager", return_value=manager):
                    process_ssid_change("HomeWifi", "OfficeWifi")
                    process_ssid_change("OfficeWifi", "HomeWifi")

            sessions = read_sessions()

    assert len(sessions) == 2
    assert sessions[0]["ssid"] == "OfficeWifi"
    assert sessions[0]["start_time"] == "09:00:00"
    assert sessions[1]["end_time"] == "13:05:00"
    assert sessions[1]["duration_minutes"] == 245
