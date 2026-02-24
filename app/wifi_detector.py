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

_AIRPORT_PATH = (
    "/System/Library/PrivateFrameworks/Apple80211.framework/"
    "Versions/Current/Resources/airport"
)


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


def _normalize_ssid(ssid: Optional[str]) -> str:
    """Normalize SSID for reliable comparisons."""
    raw = (ssid or "").strip().casefold()
    return "".join(ch for ch in raw if ch.isalnum())


def is_office_ssid(ssid: Optional[str]) -> bool:
    """Return True when SSID matches configured office SSID."""
    return _normalize_ssid(ssid) == _normalize_ssid(settings.office_wifi_name)


async def process_ssid_change(old_ssid: Optional[str], new_ssid: Optional[str]) -> None:
    """
    Route Wi-Fi SSID transitions to the session state machine (async).

    Transition rules:
    - Non-office -> office: start/resume session
    - Office -> non-office: end session immediately

    Args:
        old_ssid: Previous Wi-Fi SSID.
        new_ssid: Newly detected Wi-Fi SSID.
    """
    manager = get_session_manager()

    if manager is None:
        logger.warning("SessionManager not initialized, skipping SSID change processing")
        return

    try:
        # Office WiFi connected
        if is_office_ssid(new_ssid) and not is_office_ssid(old_ssid):
            await manager.start_session(settings.office_wifi_name)
            logger.info(f"Connected to office WiFi: {settings.office_wifi_name}")

        # Office WiFi disconnected - end session immediately
        elif is_office_ssid(old_ssid) and not is_office_ssid(new_ssid):
            await manager.end_session()
            logger.info("Disconnected from office WiFi - session ended")

    except Exception:
        logger.exception("Failed to process session transition for SSID change")


def get_current_ssid(use_cache: bool = False) -> Optional[str]:
    """
    Get the currently connected Wi-Fi SSID on macOS.

    Uses `airport -I` as primary method (more reliable for background agents),
    then `networksetup` fallback on likely interfaces, then `system_profiler`.

    Args:
        use_cache: If True, return cached SSID (fast, no subprocess). If False, query system (slow, accurate).

    Returns:
        SSID string if connected, None otherwise.
    """
    global _cached_ssid

    # Fast path: return cached SSID if available
    if use_cache and _cached_ssid is not None:
        return _cached_ssid

    ssid = _get_ssid_via_airport()
    if ssid is not None:
        _cached_ssid = ssid
        return ssid

    ssid = _get_ssid_via_networksetup()
    if ssid is not None:
        _cached_ssid = ssid
        return ssid

    ssid = _get_ssid_via_system_profiler()
    _cached_ssid = ssid
    return ssid


def _get_ssid_via_airport() -> Optional[str]:
    """Primary method for macOS background services."""
    try:
        result = subprocess.run(
            [_AIRPORT_PATH, "-I"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("SSID:"):
                ssid = stripped.split("SSID:", 1)[1].strip()
                if ssid:
                    return ssid
        return None
    except Exception:
        logger.debug("airport command failed or timed out")
        return None


def _get_ssid_via_networksetup() -> Optional[str]:
    """Fallback method: try common Wi-Fi interfaces."""
    for iface in ("en0", "en1"):
        try:
            result = subprocess.run(
                ["networksetup", "-getairportnetwork", iface],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = result.stdout.strip()
            # Output format: "Current Wi-Fi Network: <SSID>"
            if result.returncode == 0 and "Current Wi-Fi Network:" in output:
                ssid = output.split("Current Wi-Fi Network:")[1].strip()
                if ssid:
                    return ssid
        except Exception:
            logger.debug("networksetup command failed or timed out for %s", iface)
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
            manager = get_session_manager()

            # Self-heal: if already on office WiFi but session is not active, start it.
            if manager is not None and is_office_ssid(current_ssid):
                status = await manager.get_current_status()
                if not status.get("session_active", False):
                    started = await manager.start_session(settings.office_wifi_name)
                    if started:
                        logger.info(
                            "Auto-healed missing session while connected to office WiFi (%s)",
                            settings.office_wifi_name,
                        )

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
