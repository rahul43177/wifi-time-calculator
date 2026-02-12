"""
Timer engine module.
Calculates elapsed and remaining time for active sessions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from app.config import settings
from app.file_store import update_session
from app.notifier import send_notification
from app.wifi_detector import get_session_manager

logger = logging.getLogger(__name__)


def _normalize_non_negative_int(value: int, field_name: str) -> int:
    """
    Normalize numeric config inputs to non-negative integers.

    Args:
        value: Input integer-like value.
        field_name: Field name for logging context.

    Returns:
        Non-negative integer.
    """
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        logger.warning("Invalid %s value %r; defaulting to 0", field_name, value)
        return 0

    if normalized < 0:
        logger.warning("Negative %s value %d; clamping to 0", field_name, normalized)
        return 0
    return normalized


def _get_current_time(start_time: datetime) -> datetime:
    """
    Return current time aligned with start_time timezone awareness.
    """
    if start_time.tzinfo is not None and start_time.utcoffset() is not None:
        return datetime.now(tz=start_time.tzinfo)
    return datetime.now()


def get_elapsed_time(start_time: datetime, now: Optional[datetime] = None) -> timedelta:
    """
    Calculate elapsed time since session start.

    Args:
        start_time: Session start timestamp.
        now: Optional current timestamp for deterministic testing.

    Returns:
        Elapsed timedelta, clamped to zero for future start times or invalid states.
    """
    if not isinstance(start_time, datetime):
        logger.warning("Invalid start_time type %r; returning 0 elapsed", type(start_time))
        return timedelta(0)

    current_time = now or _get_current_time(start_time)
    start_is_aware = (
        start_time.tzinfo is not None and start_time.utcoffset() is not None
    )
    now_is_aware = (
        current_time.tzinfo is not None and current_time.utcoffset() is not None
    )
    if start_is_aware != now_is_aware:
        logger.warning(
            "Timezone mismatch between start_time and now; returning 0 elapsed"
        )
        return timedelta(0)

    elapsed = current_time - start_time
    if elapsed.total_seconds() < 0:
        logger.warning("start_time is in the future; returning 0 elapsed")
        return timedelta(0)
    return elapsed


def get_remaining_time(
    start_time: datetime,
    target_hours: int,
    buffer_minutes: int,
    now: Optional[datetime] = None,
) -> timedelta:
    """
    Calculate remaining time until target hours completed.

    Args:
        start_time: Session start timestamp.
        target_hours: Required work hours.
        buffer_minutes: Buffer minutes added to required work hours.
        now: Optional current timestamp for deterministic testing.

    Returns:
        Remaining timedelta. May be negative when target is exceeded.
    """
    safe_target_hours = _normalize_non_negative_int(target_hours, "target_hours")
    safe_buffer_minutes = _normalize_non_negative_int(buffer_minutes, "buffer_minutes")
    target_duration = timedelta(hours=safe_target_hours, minutes=safe_buffer_minutes)
    elapsed = get_elapsed_time(start_time, now=now)
    return target_duration - elapsed


def format_time_display(td: timedelta) -> str:
    """
    Format timedelta as HH:MM:SS string.

    Args:
        td: Time delta value.

    Returns:
        Formatted time string. Negative values are prefixed with '-'.
    """
    if not isinstance(td, timedelta):
        logger.warning("Invalid timedelta value %r; returning default display", td)
        return "00:00:00"

    total_seconds = int(td.total_seconds())
    sign = "-" if total_seconds < 0 else ""
    absolute_seconds = abs(total_seconds)

    hours, remainder = divmod(absolute_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"


def is_completed(
    start_time: datetime,
    target_hours: int,
    buffer_minutes: int,
    now: Optional[datetime] = None,
) -> bool:
    """
    Check if target hours have been completed.

    Args:
        start_time: Session start timestamp.
        target_hours: Required work hours.
        buffer_minutes: Buffer minutes added to required work hours.
        now: Optional current timestamp for deterministic testing.

    Returns:
        True when elapsed time meets or exceeds target duration.
    """
    remaining = get_remaining_time(
        start_time=start_time,
        target_hours=target_hours,
        buffer_minutes=buffer_minutes,
        now=now,
    )
    return remaining <= timedelta(0)


def _parse_session_start_datetime(active_session: Any) -> Optional[datetime]:
    """
    Parse session date/start_time into a datetime instance.

    Args:
        active_session: Session-like object with date and start_time fields.

    Returns:
        Parsed datetime, or None if parsing fails.
    """
    try:
        return datetime.strptime(
            f"{active_session.date} {active_session.start_time}",
            "%d-%m-%Y %H:%M:%S",
        )
    except (AttributeError, TypeError, ValueError):
        logger.warning("Invalid active session timestamp; skipping timer tick")
        return None


def _normalize_interval_seconds(value: Any) -> float:
    """
    Normalize loop interval to a positive float.

    Args:
        value: Interval value from settings.

    Returns:
        Positive interval in seconds, falling back to 60.0 if invalid.
    """
    try:
        interval = float(value)
        if interval > 0:
            return interval
    except (TypeError, ValueError):
        pass
    logger.warning("Invalid timer interval %r; defaulting to 60 seconds", value)
    return 60.0


def _is_enabled_test_mode(value: Any) -> bool:
    """
    Return True only for an explicit boolean True value.

    Args:
        value: Candidate test-mode value from settings.

    Returns:
        True only when value is exactly True.
    """
    return isinstance(value, bool) and value


def _resolve_target_components(
    *,
    test_mode: Any,
    test_duration_minutes: Any,
    work_duration_hours: Any,
    buffer_minutes: Any,
) -> tuple[int, int]:
    """
    Resolve effective timer target components.

    In test mode, target is expressed as minutes only:
        target_hours = 0, buffer_minutes = TEST_DURATION_MINUTES

    In normal mode, target uses:
        WORK_DURATION_HOURS + BUFFER_MINUTES

    Args:
        test_mode: Test mode flag.
        test_duration_minutes: Test duration in minutes.
        work_duration_hours: Normal work target in hours.
        buffer_minutes: Normal buffer in minutes.

    Returns:
        Tuple of (target_hours, buffer_minutes).
    """
    if _is_enabled_test_mode(test_mode):
        safe_test_minutes = _normalize_non_negative_int(
            test_duration_minutes,
            "test_duration_minutes",
        )
        return 0, safe_test_minutes

    safe_work_hours = _normalize_non_negative_int(work_duration_hours, "work_duration_hours")
    safe_buffer_minutes = _normalize_non_negative_int(buffer_minutes, "buffer_minutes")
    return safe_work_hours, safe_buffer_minutes


async def timer_polling_loop() -> None:
    """
    Background loop that checks timer progress at a fixed interval.

    Behavior:
    - Runs every configured timer interval.
    - Only performs calculations when a session is active.
    - Logs remaining time before completion and overtime after completion.
    - Detects completion and triggers a notification once per active session runtime.
    - Keeps running after completion until cancelled.
    """
    interval = _normalize_interval_seconds(settings.timer_check_interval_seconds)
    notified_session_key: Optional[tuple[str, str, str]] = None

    logger.info("Timer polling started — interval: %ss", interval)

    while True:
        await asyncio.sleep(interval)
        try:
            manager = get_session_manager()
            active_session = manager.active_session

            if active_session is None:
                logger.debug("Timer check skipped: no active session")
                notified_session_key = None
                continue

            session_key = (
                active_session.date,
                active_session.start_time,
                active_session.ssid,
            )

            start_dt = _parse_session_start_datetime(active_session)
            if start_dt is None:
                continue

            target_hours, target_buffer_minutes = _resolve_target_components(
                test_mode=getattr(settings, "test_mode", False),
                test_duration_minutes=getattr(settings, "test_duration_minutes", 2),
                work_duration_hours=getattr(settings, "work_duration_hours", 4),
                buffer_minutes=getattr(settings, "buffer_minutes", 10),
            )

            elapsed = get_elapsed_time(start_dt)
            remaining = get_remaining_time(
                start_time=start_dt,
                target_hours=target_hours,
                buffer_minutes=target_buffer_minutes,
            )

            elapsed_display = format_time_display(elapsed)
            if remaining.total_seconds() < 0:
                overtime_display = format_time_display(abs(remaining))
                logger.info(
                    "Timer overtime: %s (elapsed: %s)",
                    overtime_display,
                    elapsed_display,
                )
            else:
                remaining_display = format_time_display(remaining)
                logger.info(
                    "Timer remaining: %s (elapsed: %s)",
                    remaining_display,
                    elapsed_display,
                )

            completed = is_completed(
                start_time=start_dt,
                target_hours=target_hours,
                buffer_minutes=target_buffer_minutes,
            )
            was_marked_completed = bool(getattr(active_session, "completed_4h", False))

            if completed and not was_marked_completed:
                persisted = update_session(
                    session_date=active_session.date,
                    ssid=active_session.ssid,
                    start_time=active_session.start_time,
                    updates={"completed_4h": True},
                )
                if persisted:
                    active_session.completed_4h = True
                    logger.info(
                        "Session completion persisted: %s %s",
                        active_session.date,
                        active_session.start_time,
                    )
                else:
                    logger.warning(
                        "Failed to persist session completion: %s %s",
                        active_session.date,
                        active_session.start_time,
                    )

            if was_marked_completed:
                notified_session_key = session_key

            if completed and session_key != notified_session_key:
                title = "Office Wi-Fi Tracker"
                if _is_enabled_test_mode(getattr(settings, "test_mode", False)):
                    message = (
                        f"Test mode: {target_buffer_minutes} min completed. You may leave."
                    )
                else:
                    message = (
                        f"{target_hours} hours + "
                        f"{target_buffer_minutes} min buffer completed. You may leave."
                    )
                send_notification(title, message)
                notified_session_key = session_key

        except Exception:
            logger.exception("Error during timer poll")
