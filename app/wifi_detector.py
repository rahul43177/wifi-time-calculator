"""
Wi-Fi SSID detection module.
Detects current connected Wi-Fi network on macOS.
Provides background polling loop for SSID change detection.
"""

import asyncio
import logging
import subprocess
from typing import Callable, Optional

from app.config import settings
from app.session_manager import SessionManager

logger = logging.getLogger(__name__)

# Tracks the last known SSID across polling cycles
_previous_ssid: Optional[str] = None
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Return the shared SessionManager instance for Wi-Fi integration.

    Lazily initializes the manager to avoid import-time side effects and to
    support test-time dependency injection via mocking.
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def process_ssid_change(old_ssid: Optional[str], new_ssid: Optional[str]) -> None:
    """
    Route Wi-Fi SSID transitions to the session state machine.

    Transition rules:
    - Non-office -> office: start session
    - Office -> non-office: end session

    Args:
        old_ssid: Previous Wi-Fi SSID.
        new_ssid: Newly detected Wi-Fi SSID.
    """
    office_ssid = settings.office_wifi_name
    manager = get_session_manager()

    try:
        if new_ssid == office_ssid and old_ssid != office_ssid:
            manager.start_session(office_ssid)
        elif old_ssid == office_ssid and new_ssid != office_ssid:
            manager.end_session()
    except Exception:
        logger.exception("Failed to process session transition for SSID change")


def get_current_ssid() -> Optional[str]:
    """
    Get the currently connected Wi-Fi SSID on macOS.

    Uses `networksetup -getairportnetwork en0` as primary method,
    falls back to parsing `system_profiler SPAirPortDataType`.

    Returns:
        SSID string if connected, None otherwise.
    """
    ssid = _get_ssid_via_networksetup()
    if ssid is not None:
        return ssid

    return _get_ssid_via_system_profiler()


def _get_ssid_via_networksetup() -> Optional[str]:
    """Primary method: fast (~0.1s)."""
    try:
        result = subprocess.run(
            ["networksetup", "-getairportnetwork", "en0"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout.strip()
        # Output format: "Current Wi-Fi Network: <SSID>"
        if result.returncode == 0 and "Current Wi-Fi Network:" in output:
            ssid = output.split("Current Wi-Fi Network:", 1)[1].strip()
            if ssid:
                return ssid
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug("networksetup failed: %s", e)

    return None


def _get_ssid_via_system_profiler() -> Optional[str]:
    """Fallback method: slower (~1-2s) but more reliable."""
    try:
        result = subprocess.run(
            ["system_profiler", "SPAirPortDataType"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        # Parse output — SSID is the key name right after "Current Network Information:"
        lines = result.stdout.splitlines()
        for i, line in enumerate(lines):
            if "Current Network Information:" in line:
                # Next non-empty line has the SSID as "            <SSID>:"
                if i + 1 < len(lines):
                    ssid_line = lines[i + 1].strip()
                    if ssid_line.endswith(":"):
                        ssid = ssid_line[:-1].strip()
                        if ssid:
                            return ssid
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug("system_profiler failed: %s", e)

    return None


async def wifi_polling_loop(
    on_change: Optional[Callable[[Optional[str], Optional[str]], None]] = None,
) -> None:
    """
    Background loop that checks Wi-Fi SSID every N seconds.

    Detects changes and logs them. Optionally calls on_change(old_ssid, new_ssid)
    when the SSID changes — this hook will be used by session_manager in Phase 2.

    Runs forever until the task is cancelled.
    """
    global _previous_ssid
    interval = settings.wifi_check_interval_seconds

    # Capture initial state
    _previous_ssid = get_current_ssid()
    logger.info("Wi-Fi polling started — current SSID: %s, interval: %ds", _previous_ssid, interval)

    while True:
        await asyncio.sleep(interval)
        try:
            current_ssid = get_current_ssid()

            if current_ssid != _previous_ssid:
                logger.info("SSID changed: %s -> %s", _previous_ssid, current_ssid)
                process_ssid_change(_previous_ssid, current_ssid)
                if on_change is not None:
                    on_change(_previous_ssid, current_ssid)
                _previous_ssid = current_ssid
            else:
                logger.debug("SSID unchanged: %s", current_ssid)

        except Exception:
            logger.exception("Error during Wi-Fi poll")
