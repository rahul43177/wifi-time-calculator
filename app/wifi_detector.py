"""
Wi-Fi SSID detection module with MongoDB integration.

Key Changes:
- Async SessionManager integration
- Grace period support for brief disconnects
- MongoDB-backed session tracking
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
_cached_ssid: Optional[str] = None  # Cached SSID to avoid blocking subprocess calls


def set_session_manager(manager: SessionManager) -> None:
    """
    Set the shared SessionManager instance (called by main.py).

    Args:
        manager: Configured SessionManager with MongoDB store
    """
    global _session_manager
    _session_manager = manager


def get_session_manager() -> Optional[SessionManager]:
    """
    Return the shared SessionManager instance for Wi-Fi integration.

    Returns:
        SessionManager instance or None if not initialized
    """
    return _session_manager


async def process_ssid_change(old_ssid: Optional[str], new_ssid: Optional[str]) -> None:
    """
    Route Wi-Fi SSID transitions to the session state machine (async).

    Transition rules with grace period:
    - Non-office -> office: start/resume session (cancels grace period)
    - Office -> non-office: start grace period (session continues for 2 min)

    Args:
        old_ssid: Previous Wi-Fi SSID.
        new_ssid: Newly detected Wi-Fi SSID.
    """
    office_ssid = settings.office_wifi_name
    manager = get_session_manager()

    if manager is None:
        logger.warning("SessionManager not initialized, skipping SSID change processing")
        return

    try:
        # Office WiFi connected
        if new_ssid == office_ssid and old_ssid != office_ssid:
            await manager.start_session(office_ssid)
            logger.info(f"Connected to office WiFi: {office_ssid}")

        # Office WiFi disconnected - start grace period
        elif old_ssid == office_ssid and new_ssid != office_ssid:
            await manager.handle_disconnect()
            logger.info(f"Disconnected from office WiFi - grace period started")

    except Exception:
        logger.exception("Failed to process session transition for SSID change")


def get_current_ssid(use_cache: bool = False) -> Optional[str]:
    """
    Get the currently connected Wi-Fi SSID on macOS.

    Uses `networksetup -getairportnetwork en0` as primary method,
    falls back to parsing `system_profiler SPAirPortDataType`.

    Args:
        use_cache: If True, return cached SSID (fast, no subprocess). If False, query system (slow, accurate).

    Returns:
        SSID string if connected, None otherwise.
    """
    global _cached_ssid

    # Fast path: return cached SSID if available
    if use_cache and _cached_ssid is not None:
        return _cached_ssid

    ssid = _get_ssid_via_networksetup()
    if ssid is not None:
        _cached_ssid = ssid
        return ssid

    ssid = _get_ssid_via_system_profiler()
    _cached_ssid = ssid
    return ssid


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
            ssid = output.split("Current Wi-Fi Network:")[1].strip()
            return ssid
        return None
    except Exception:
        logger.debug("networksetup command failed or timed out")
        return None


def _get_ssid_via_system_profiler() -> Optional[str]:
    """Fallback method: slower (~2-3s) but more reliable."""
    try:
        result = subprocess.run(
            ["system_profiler", "SPAirPortDataType"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout
        lines = output.split("\n")

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Legacy format: "SSID: <name>"
            if stripped.startswith("SSID:"):
                ssid = stripped.split("SSID:", 1)[1].strip()
                if ssid:
                    return ssid

            # Modern macOS format: "Current Network Information:" then next line is "<SSID>:"
            if "Current Network Information:" in stripped and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # SSID appears as "<name>:" (ends with colon, no key:value pattern)
                if next_line.endswith(":") and ": " not in next_line:
                    ssid = next_line[:-1].strip()
                    if ssid:
                        return ssid

        return None
    except Exception:
        logger.debug("system_profiler command failed or timed out")
        return None


async def wifi_polling_loop(
    interval_seconds: Optional[float] = None,
    on_change: Optional[Callable[[Optional[str], Optional[str]], None]] = None,
) -> None:
    """
    Background loop that polls current Wi-Fi SSID at fixed intervals.

    When the SSID changes, triggers session state transitions via the
    SessionManager. Continues running until cancelled.

    Args:
        interval_seconds: Poll interval in seconds (default from settings).
        on_change: Optional callback for testing (receives old_ssid, new_ssid).
    """
    global _previous_ssid

    interval = interval_seconds or settings.wifi_check_interval_seconds
    if interval <= 0:
        logger.warning("Invalid Wi-Fi poll interval %s; using 30s", interval)
        interval = 30

    logger.info(f"Wi-Fi polling started — interval: {interval}s")

    # Initial SSID capture
    _previous_ssid = get_current_ssid()
    logger.debug(f"Initial SSID: {_previous_ssid or '(not connected)'}")

    while True:
        await asyncio.sleep(interval)
        try:
            current_ssid = get_current_ssid()

            if current_ssid != _previous_ssid:
                logger.info(
                    f"SSID changed: {_previous_ssid or '(none)'} -> {current_ssid or '(none)'}"
                )

                # Async session management
                await process_ssid_change(_previous_ssid, current_ssid)

                # Optional callback for testing (sync)
                if on_change is not None:
                    on_change(_previous_ssid, current_ssid)

                _previous_ssid = current_ssid

        except Exception:
            logger.exception("Error during Wi-Fi poll")
