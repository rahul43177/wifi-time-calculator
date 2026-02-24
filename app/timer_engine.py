"""
Timer engine module with MongoDB integration.

Key Changes:
- Works with cumulative daily tracking (not per-session)
- Respects paused state (network connectivity loss)
- Updates MongoDB periodically with current total
- Uses IST timezone utilities
"""

import asyncio
import logging
from datetime import datetime, timedelta, UTC
from typing import Any, Optional

from app.config import settings
from app.notifier import send_notification
from app.mongodb_store import MongoDBStore
from app.timezone_utils import now_utc, format_time_ist

logger = logging.getLogger(__name__)

# Global reference to MongoDB store (set by main.py)
_mongo_store: Optional[MongoDBStore] = None


def set_mongo_store(store: MongoDBStore):
    """Set the global MongoDB store instance."""
    global _mongo_store
    _mongo_store = store


def get_mongo_store() -> Optional[MongoDBStore]:
    """Get the global MongoDB store instance."""
    return _mongo_store


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
    Resolve effective timer target components (legacy function for analytics).

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


def _resolve_target_minutes() -> int:
    """
    Resolve effective timer target in minutes.

    In test mode: TEST_DURATION_MINUTES
    In normal mode: WORK_DURATION_HOURS * 60 + BUFFER_MINUTES

    Returns:
        Target minutes
    """
    if _is_enabled_test_mode(settings.test_mode):
        return _normalize_non_negative_int(
            settings.test_duration_minutes,
            "test_duration_minutes"
        )

    work_hours = _normalize_non_negative_int(settings.work_duration_hours, "work_duration_hours")
    buffer_mins = _normalize_non_negative_int(settings.buffer_minutes, "buffer_minutes")
    return (work_hours * 60) + buffer_mins


def _safe_int_minutes(value: Any, default: int = 0) -> int:
    """Parse integer minutes safely and clamp negatives to zero."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, parsed)


def _compute_running_total_minutes(doc: dict, now: Optional[datetime] = None) -> int:
    """
    Compute cumulative daily total without double-counting the active session.

    total = session_start_total_minutes + effective_minutes_since_current_session_start
    """
    current_session_start = doc.get("current_session_start")
    if current_session_start is None:
        return _safe_int_minutes(doc.get("total_minutes", 0))

    reference_now = now or now_utc()
    start = (
        current_session_start
        if current_session_start.tzinfo
        else current_session_start.replace(tzinfo=UTC)
    )
    elapsed_seconds = max(0.0, (reference_now - start).total_seconds())

    paused_total_minutes = _safe_int_minutes(doc.get("paused_duration_minutes", 0))
    session_start_paused_minutes = _safe_int_minutes(
        doc.get("session_start_paused_minutes", paused_total_minutes),
        default=paused_total_minutes,
    )
    paused_since_start_minutes = max(0, paused_total_minutes - session_start_paused_minutes)
    paused_seconds = float(paused_since_start_minutes * 60)

    # If currently paused, include ongoing pause so timer does not advance.
    if not doc.get("has_network_access", True) and doc.get("paused_at"):
        paused_at_raw = doc["paused_at"]
        paused_at = paused_at_raw if paused_at_raw.tzinfo else paused_at_raw.replace(tzinfo=UTC)
        paused_seconds += max(0.0, (reference_now - paused_at).total_seconds())

    effective_session_minutes = int(max(0.0, elapsed_seconds - paused_seconds) // 60)

    stored_total = _safe_int_minutes(doc.get("total_minutes", 0))
    baseline_raw = doc.get("session_start_total_minutes")
    if baseline_raw is None:
        session_start_total_minutes = max(0, stored_total - effective_session_minutes)
    else:
        session_start_total_minutes = _safe_int_minutes(
            baseline_raw,
            default=max(0, stored_total - effective_session_minutes),
        )

    return session_start_total_minutes + effective_session_minutes


async def timer_polling_loop() -> None:
    """
    Background loop that monitors cumulative daily timer progress.

    New Behavior:
    - Monitors MongoDB for active session
    - Updates cumulative total_minutes periodically
    - Respects paused state (network connectivity)
    - Detects 4-hour completion
    - Sends notification once per day when target reached
    """
    interval = _normalize_interval_seconds(settings.timer_check_interval_seconds)
    notified_date: Optional[str] = None
    target_minutes = _resolve_target_minutes()

    logger.info(f"Timer polling started — interval: {interval}s, target: {target_minutes} min")

    while True:
        await asyncio.sleep(interval)
        try:
            # Hard gate: never run timer math for non-office Wi-Fi.
            # This avoids unnecessary DB operations while away from office.
            from app.wifi_detector import get_current_ssid, is_office_ssid

            current_ssid = get_current_ssid(use_cache=True)
            if not is_office_ssid(current_ssid):
                notified_date = None
                logger.debug("Timer check skipped: not on configured office Wi-Fi")
                continue

            store = get_mongo_store()
            if store is None:
                logger.debug("Timer check skipped: MongoDB store not initialized")
                continue

            # Get active session from MongoDB
            doc = await store.get_active_session()

            if not doc:
                logger.debug("Timer check skipped: no active session")
                notified_date = None
                continue

            date = doc.get("date")
            is_active = doc.get("is_active", False)
            has_network = doc.get("has_network_access", True)
            completed_4h = doc.get("completed_4h", False)
            total_minutes = _safe_int_minutes(doc.get("total_minutes", 0))

            if not is_active:
                logger.debug("Timer check skipped: session not active")
                continue

            # Skip if paused for re-auth
            if not has_network:
                logger.debug("Timer paused: waiting for network connectivity")
                continue

            # Calculate and persist running cumulative total.
            computed_total_minutes = _compute_running_total_minutes(doc)
            if computed_total_minutes != total_minutes:
                updated = await store.update_elapsed_time(date, computed_total_minutes)
                if updated:
                    total_minutes = computed_total_minutes

            # Calculate remaining time
            remaining_minutes = target_minutes - total_minutes
            elapsed_display = format_time_display(timedelta(minutes=total_minutes))

            if remaining_minutes < 0:
                overtime_display = format_time_display(timedelta(minutes=abs(remaining_minutes)))
                logger.info(
                    f"Timer overtime: {overtime_display} (elapsed: {elapsed_display})"
                )
            else:
                remaining_display = format_time_display(timedelta(minutes=remaining_minutes))
                logger.info(
                    f"Timer remaining: {remaining_display} (elapsed: {elapsed_display})"
                )

            # Check if 4-hour goal completed
            if total_minutes >= target_minutes and not completed_4h:
                # Mark as completed in MongoDB
                await store.mark_completed(date)
                logger.info(f"Daily goal completed for {date} - Total: {total_minutes} min")

                # Update doc
                doc = await store.get_daily_status(date)
                completed_4h = True

            # Send notification once per day
            if completed_4h and date != notified_date:
                title = "Office Wi-Fi Tracker"
                if _is_enabled_test_mode(settings.test_mode):
                    message = f"Test mode: {target_minutes} min completed. You may leave."
                else:
                    hours = settings.work_duration_hours
                    buffer = settings.buffer_minutes
                    message = (
                        f"{hours} hours + {buffer} min buffer completed. "
                        f"You may leave."
                    )
                send_notification(title, message)
                notified_date = date
                logger.info(f"Completion notification sent for {date}")

        except Exception:
            logger.exception("Error during timer poll")


# ==============================================================================
# Legacy Functions for Backward Compatibility
# These are kept for existing tests but not used in MongoDB implementation
# ==============================================================================

def get_elapsed_time(start_time: datetime, now: Optional[datetime] = None) -> timedelta:
    """
    Calculate elapsed time since session start (legacy function).

    Args:
        start_time: Session start timestamp.
        now: Optional current timestamp for deterministic testing.

    Returns:
        Elapsed timedelta, clamped to zero for future start times or invalid states.
    """
    if not isinstance(start_time, datetime):
        logger.warning("Invalid start_time type %r; returning 0 elapsed", type(start_time))
        return timedelta(0)

    def _get_current_time(st: datetime) -> datetime:
        if st.tzinfo is not None and st.utcoffset() is not None:
            return datetime.now(tz=st.tzinfo)
        return datetime.now()

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
    Calculate remaining time until target hours completed (legacy function).

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


def is_completed(
    start_time: datetime,
    target_hours: int,
    buffer_minutes: int,
    now: Optional[datetime] = None,
) -> bool:
    """
    Check if target hours have been completed (legacy function).

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
