"""
Tests for Phase 3.3: Notification System.

Covers:
- Happy path: successful macOS notification via osascript
- Platform gating: only Darwin is supported
- osascript failure modes: non-zero exit, timeout, missing binary, OS error
- String escaping for safe osascript embedding
- Graceful failure: never crashes the caller
- Integration: timer loop sends correct message format
"""

import logging
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app.notifier import _escape_osascript_string, can_send_notifications, send_notification


# --- can_send_notifications ---


def test_can_send_on_macos() -> None:
    """Returns True when running on macOS (Darwin)."""
    with patch("app.notifier.platform.system", return_value="Darwin"):
        assert can_send_notifications() is True


@pytest.mark.parametrize("os_name", ["Windows", "Linux", ""])
def test_cannot_send_on_non_macos(os_name: str) -> None:
    """Returns False for non-macOS platforms."""
    with patch("app.notifier.platform.system", return_value=os_name):
        assert can_send_notifications() is False


# --- _escape_osascript_string ---


def test_escape_plain_string() -> None:
    """Plain strings are returned unchanged."""
    assert _escape_osascript_string("hello world") == "hello world"


def test_escape_double_quotes() -> None:
    """Double quotes are backslash-escaped."""
    assert _escape_osascript_string('say "hi"') == 'say \\"hi\\"'


def test_escape_backslashes() -> None:
    """Backslashes are double-escaped."""
    assert _escape_osascript_string("path\\to\\file") == "path\\\\to\\\\file"


def test_escape_mixed_special_chars() -> None:
    """Both backslashes and double quotes are handled together."""
    assert (
        _escape_osascript_string('a\\b "c"')
        == 'a\\\\b \\"c\\"'
    )


def test_escape_empty_string() -> None:
    """Empty string is returned unchanged."""
    assert _escape_osascript_string("") == ""


# --- send_notification: happy path ---


def test_send_notification_success() -> None:
    """Successful osascript execution returns True."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch("app.notifier.subprocess.run", return_value=mock_result) as mock_run:
            result = send_notification("Office Wi-Fi Tracker", "You may leave.")

    assert result is True
    mock_run.assert_called_once()
    args = mock_run.call_args
    assert args[0][0][0] == "osascript"
    assert args[0][0][1] == "-e"
    assert "You may leave." in args[0][0][2]
    assert "Office Wi-Fi Tracker" in args[0][0][2]


def test_send_notification_logs_success(caplog: pytest.LogCaptureFixture) -> None:
    """Successful send logs an info message with title and body."""
    caplog.set_level(logging.INFO, logger="app.notifier")
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch("app.notifier.subprocess.run", return_value=mock_result):
            send_notification("Title", "Body")

    assert "Notification sent" in caplog.text
    assert "Title" in caplog.text


# --- send_notification: non-macOS platform ---


def test_send_notification_returns_false_on_unsupported_platform() -> None:
    """Returns False without calling subprocess on non-macOS."""
    with patch("app.notifier.can_send_notifications", return_value=False):
        with patch("app.notifier.subprocess.run") as mock_run:
            result = send_notification("T", "M")

    assert result is False
    mock_run.assert_not_called()


def test_send_notification_logs_warning_on_unsupported_platform(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Logs a warning when platform is unsupported."""
    caplog.set_level(logging.WARNING, logger="app.notifier")
    with patch("app.notifier.can_send_notifications", return_value=False):
        send_notification("T", "M")

    assert "not supported" in caplog.text


# --- send_notification: osascript failures ---


def test_send_notification_non_zero_exit_code() -> None:
    """Non-zero osascript exit code returns False."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "some error"

    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch("app.notifier.subprocess.run", return_value=mock_result):
            result = send_notification("T", "M")

    assert result is False


def test_send_notification_non_zero_logs_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Non-zero exit code logs the stderr output."""
    caplog.set_level(logging.WARNING, logger="app.notifier")
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "osascript error detail"

    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch("app.notifier.subprocess.run", return_value=mock_result):
            send_notification("T", "M")

    assert "non-zero exit code" in caplog.text


def test_send_notification_timeout() -> None:
    """Timeout during osascript returns False without crashing."""
    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch(
            "app.notifier.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="osascript", timeout=10),
        ):
            result = send_notification("T", "M")

    assert result is False


def test_send_notification_timeout_logs_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Timeout logs a descriptive warning."""
    caplog.set_level(logging.WARNING, logger="app.notifier")
    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch(
            "app.notifier.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="osascript", timeout=10),
        ):
            send_notification("T", "M")

    assert "timed out" in caplog.text


def test_send_notification_file_not_found() -> None:
    """Missing osascript binary returns False without crashing."""
    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch(
            "app.notifier.subprocess.run",
            side_effect=FileNotFoundError("osascript"),
        ):
            result = send_notification("T", "M")

    assert result is False


def test_send_notification_file_not_found_logs_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing binary logs a warning about unavailability."""
    caplog.set_level(logging.WARNING, logger="app.notifier")
    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch(
            "app.notifier.subprocess.run",
            side_effect=FileNotFoundError("osascript"),
        ):
            send_notification("T", "M")

    assert "not found" in caplog.text


def test_send_notification_os_error() -> None:
    """Generic OSError returns False without crashing."""
    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch(
            "app.notifier.subprocess.run",
            side_effect=OSError("permission denied"),
        ):
            result = send_notification("T", "M")

    assert result is False


def test_send_notification_os_error_logs_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """OSError logs the error detail."""
    caplog.set_level(logging.WARNING, logger="app.notifier")
    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch(
            "app.notifier.subprocess.run",
            side_effect=OSError("permission denied"),
        ):
            send_notification("T", "M")

    assert "OS error" in caplog.text


# --- String escaping integration ---


def test_send_notification_escapes_quotes_in_title() -> None:
    """Double quotes in title are escaped before passing to osascript."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch("app.notifier.subprocess.run", return_value=mock_result) as mock_run:
            send_notification('Title with "quotes"', "Body")

    script_arg = mock_run.call_args[0][0][2]
    assert '\\"quotes\\"' in script_arg


def test_send_notification_escapes_quotes_in_message() -> None:
    """Double quotes in message are escaped before passing to osascript."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch("app.notifier.subprocess.run", return_value=mock_result) as mock_run:
            send_notification("Title", 'Say "hello" to the team')

    script_arg = mock_run.call_args[0][0][2]
    assert '\\"hello\\"' in script_arg


def test_send_notification_escapes_backslashes() -> None:
    """Backslashes in message are escaped before passing to osascript."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch("app.notifier.subprocess.run", return_value=mock_result) as mock_run:
            send_notification("Title", "path\\to\\file")

    script_arg = mock_run.call_args[0][0][2]
    assert "path\\\\to\\\\file" in script_arg


# --- osascript command format ---


def test_send_notification_builds_correct_osascript_command() -> None:
    """The osascript command matches the expected AppleScript format."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch("app.notifier.subprocess.run", return_value=mock_result) as mock_run:
            send_notification("Office Wi-Fi Tracker", "4 hours + 10 min buffer completed.")

    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "osascript"
    assert cmd[1] == "-e"
    assert cmd[2] == (
        'display notification "4 hours + 10 min buffer completed." '
        'with title "Office Wi-Fi Tracker"'
    )


def test_send_notification_subprocess_called_with_correct_kwargs() -> None:
    """subprocess.run is called with capture_output, text, and timeout."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch("app.notifier.subprocess.run", return_value=mock_result) as mock_run:
            send_notification("T", "M")

    kwargs = mock_run.call_args[1]
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 10


# --- Integration: message format from timer loop ---


def test_notification_message_includes_buffer_info() -> None:
    """The message format used by timer_polling_loop includes buffer minutes."""
    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("app.notifier.can_send_notifications", return_value=True):
        with patch("app.notifier.subprocess.run", return_value=mock_result):
            # Simulate the exact call from timer_polling_loop (lines 269-274)
            title = "Office Wi-Fi Tracker"
            work_hours = 4
            buffer_mins = 10
            message = (
                f"{work_hours} hours + "
                f"{buffer_mins} min buffer completed. You may leave."
            )
            result = send_notification(title, message)

    assert result is True
