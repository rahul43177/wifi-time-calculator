"""
Notification module.
Sends OS-level notifications when 4-hour work period is complete.

Uses macOS Notification Center via osascript. Falls back gracefully
on unsupported platforms or when the subprocess fails.
"""

import logging
import platform
import subprocess

logger = logging.getLogger(__name__)


def _escape_osascript_string(value: str) -> str:
    """
    Escape a string for safe embedding inside an osascript double-quoted literal.

    Backslashes and double quotes must be escaped so the AppleScript
    interpreter does not misparse or execute unintended code.

    Args:
        value: Raw string to escape.

    Returns:
        Escaped string safe for osascript double-quoted context.
    """
    return value.replace("\\", "\\\\").replace('"', '\\"')


def can_send_notifications() -> bool:
    """
    Check if the current platform supports OS-level notifications.

    Returns:
        True on macOS (Darwin), False otherwise.
    """
    return platform.system() == "Darwin"


def send_notification(title: str, message: str) -> bool:
    """
    Send an OS-level notification to the user.

    On macOS, uses ``osascript`` to display a Notification Center alert.
    On unsupported platforms the call is logged and returns False without
    raising an exception.

    Args:
        title: Notification title (e.g. "Office Wi-Fi Tracker").
        message: Notification body (e.g. "4 hours + 10 min buffer completed.").

    Returns:
        True if the notification was delivered successfully, False otherwise.
    """
    if not can_send_notifications():
        logger.warning(
            "Notifications not supported on %s; skipping", platform.system()
        )
        return False

    safe_title = _escape_osascript_string(title)
    safe_message = _escape_osascript_string(message)

    script = (
        f'display notification "{safe_message}" with title "{safe_title}"'
    )

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            logger.info("Notification sent: %s — %s", title, message)
            return True

        logger.warning(
            "osascript returned non-zero exit code %d: %s",
            result.returncode,
            result.stderr.strip(),
        )
        return False

    except subprocess.TimeoutExpired:
        logger.warning("Notification timed out after 10 seconds")
        return False
    except FileNotFoundError:
        logger.warning("osascript binary not found; notifications unavailable")
        return False
    except OSError as exc:
        logger.warning("OS error sending notification: %s", exc)
        return False
