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
from html import escape
from typing import Any, Optional

from app.config import settings
from app.notifier import send_notification
from app.email_notifier import send_email_notification
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


def _compute_running_total_seconds(doc: dict, now: Optional[datetime] = None) -> int:
    """
    Compute cumulative daily total in seconds without double-counting the active session.

    Same logic as _compute_running_total_minutes but returns second-level precision
    instead of flooring to whole minutes. Used by the status API so the frontend
    timer does not jump on page refresh.

    total_seconds = session_start_total_minutes * 60 + effective_seconds_since_session_start
    """
    current_session_start = doc.get("current_session_start")
    if current_session_start is None:
        return _safe_int_minutes(doc.get("total_minutes", 0)) * 60

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

    effective_seconds = int(max(0.0, elapsed_seconds - paused_seconds))

    stored_total = _safe_int_minutes(doc.get("total_minutes", 0))
    effective_session_minutes = int(max(0.0, elapsed_seconds - paused_seconds) // 60)
    baseline_raw = doc.get("session_start_total_minutes")
    if baseline_raw is None:
        session_start_total_minutes = max(0, stored_total - effective_session_minutes)
    else:
        session_start_total_minutes = _safe_int_minutes(
            baseline_raw,
            default=max(0, stored_total - effective_session_minutes),
        )

    return (session_start_total_minutes * 60) + effective_seconds


def _normalize_utc_datetime(value: Any) -> Optional[datetime]:
    """Normalize MongoDB datetime values to timezone-aware UTC."""
    if not isinstance(value, datetime):
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _resolve_session_start_utc(doc: dict[str, Any]) -> Optional[datetime]:
    """Resolve the best available session start timestamp for messaging."""
    return _normalize_utc_datetime(
        doc.get("first_session_start_utc") or doc.get("current_session_start")
    )


def _format_ist_time(dt: Optional[datetime]) -> str:
    """Format datetime to user-facing IST time with timezone suffix."""
    if dt is None:
        return "N/A"
    return format_time_ist(dt, "%I:%M:%S %p IST")


def _build_pre_leave_email_message(
    doc: dict[str, Any],
    *,
    total_minutes: int,
    target_minutes: int,
) -> str:
    """Build the 10-minute pre-leave email body."""
    start_utc = _resolve_session_start_utc(doc)
    start_display = _format_ist_time(start_utc)
    duration_display = format_time_display(timedelta(minutes=max(0, total_minutes)))

    leave_time_utc = (
        start_utc + timedelta(minutes=target_minutes)
        if start_utc is not None
        else now_utc() + timedelta(minutes=max(0, target_minutes - total_minutes))
    )
    leave_time_display = _format_ist_time(leave_time_utc)

    return (
        f"Came office at / Start time: {start_display}\n"
        f"Duration complete: {duration_display}\n"
        f"You can leave in 10 mins with end time: {leave_time_display}"
    )


def _build_email_html(
    *,
    title: str,
    subtitle: str,
    badge_text: str,
    badge_bg: str,
    badge_fg: str,
    rows: list[tuple[str, str]],
    footer: str,
) -> str:
    """Build a minimal premium HTML email with inline styles for broad compatibility."""
    escaped_rows = [
        (escape(label), escape(value))
        for label, value in rows
    ]
    row_html = "".join(
        (
            "<tr>"
            f"<td style=\"padding:10px 0;color:#6b7280;font-size:13px;"
            "font-weight:500;border-bottom:1px solid #eef2f7;\">"
            f"{label}</td>"
            f"<td style=\"padding:10px 0;color:#111827;font-size:14px;text-align:right;"
            "font-weight:600;border-bottom:1px solid #eef2f7;\">"
            f"{value}</td>"
            "</tr>"
        )
        for label, value in escaped_rows
    )

    return f"""\
<!doctype html>
<html lang="en">
  <body style="margin:0;padding:0;background:#f5f7fb;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:620px;background:#ffffff;border:1px solid #e5e7eb;border-radius:16px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
            <tr>
              <td style="padding:24px 24px 14px;">
                <div style="color:#6b7280;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;font-weight:600;">Office Wi-Fi Tracker</div>
                <h1 style="margin:10px 0 8px;color:#111827;font-size:22px;line-height:1.3;">{escape(title)}</h1>
                <p style="margin:0 0 14px;color:#4b5563;font-size:14px;line-height:1.6;">{escape(subtitle)}</p>
                <span style="display:inline-block;padding:6px 12px;border-radius:999px;background:{badge_bg};color:{badge_fg};font-size:12px;font-weight:600;">{escape(badge_text)}</span>
              </td>
            </tr>
            <tr>
              <td style="padding:0 24px 8px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                  {row_html}
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:12px 24px 22px;color:#6b7280;font-size:12px;line-height:1.6;">
                {escape(footer)}
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def _build_pre_leave_email_html(
    doc: dict[str, Any],
    *,
    total_minutes: int,
    target_minutes: int,
) -> str:
    """Build styled HTML for pre-leave email."""
    start_utc = _resolve_session_start_utc(doc)
    start_display = _format_ist_time(start_utc)
    duration_display = format_time_display(timedelta(minutes=max(0, total_minutes)))
    leave_time_utc = (
        start_utc + timedelta(minutes=target_minutes)
        if start_utc is not None
        else now_utc() + timedelta(minutes=max(0, target_minutes - total_minutes))
    )
    leave_time_display = _format_ist_time(leave_time_utc)

    return _build_email_html(
        title="10 minutes to leave",
        subtitle="You are close to completing today’s tracked target.",
        badge_text="Pre-leave reminder",
        badge_bg="#fff7ed",
        badge_fg="#b45309",
        rows=[
            ("Came office at / Start time", start_display),
            ("Duration complete", duration_display),
            ("Leave in 10 mins (end time)", leave_time_display),
        ],
        footer="This is an automated reminder from your Office Wi-Fi Tracker.",
    )


def _build_completion_email_message(
    doc: dict[str, Any],
    *,
    total_minutes: int,
    completed_at_utc: datetime,
) -> str:
    """Build the completion email body."""
    start_utc = _resolve_session_start_utc(doc)
    start_display = _format_ist_time(start_utc)
    duration_display = format_time_display(timedelta(minutes=max(0, total_minutes)))
    completed_display = _format_ist_time(completed_at_utc)

    return (
        f"Came office at / Start time: {start_display}\n"
        f"Duration complete: {duration_display}\n"
        f"Target completed at: {completed_display}"
    )


def _build_completion_email_html(
    doc: dict[str, Any],
    *,
    total_minutes: int,
    completed_at_utc: datetime,
) -> str:
    """Build styled HTML for completion email."""
    start_utc = _resolve_session_start_utc(doc)
    start_display = _format_ist_time(start_utc)
    duration_display = format_time_display(timedelta(minutes=max(0, total_minutes)))
    completed_display = _format_ist_time(completed_at_utc)

    return _build_email_html(
        title="Target completed",
        subtitle="Your configured office session target has been completed.",
        badge_text="Completed",
        badge_bg="#ecfdf3",
        badge_fg="#166534",
        rows=[
            ("Came office at / Start time", start_display),
            ("Duration complete", duration_display),
            ("Target completed at", completed_display),
        ],
        footer="You can now wrap up and leave when ready.",
    )


async def timer_polling_loop() -> None:
    """
    Background loop that monitors cumulative daily timer progress.

    Behavior:
    - Monitors MongoDB for active session
    - Updates cumulative total_minutes periodically
    - Respects paused state (network connectivity)
    - Sends one pre-leave email in the last 10 minutes
    - Sends completion desktop + email alerts at target completion
    - Uses MongoDB sent flags to dedupe across restarts
    """
    interval = _normalize_interval_seconds(settings.timer_check_interval_seconds)
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
                continue

            date = doc.get("date")
            if not isinstance(date, str) or not date.strip():
                logger.warning("Timer check skipped: session document missing valid date")
                continue

            is_active = doc.get("is_active", False)
            has_network = doc.get("has_network_access", True)
            completed_4h = bool(doc.get("completed_4h", False))
            total_minutes = _safe_int_minutes(doc.get("total_minutes", 0))
            pre_leave_email_sent_at = doc.get("pre_leave_email_sent_at")
            completion_email_sent_at = doc.get("completion_email_sent_at")
            completion_desktop_sent_at = doc.get("completion_desktop_sent_at")

            # BUGFIX: Force-close stale sessions from previous days
            from app.timezone_utils import get_today_date_ist
            today_date = get_today_date_ist()
            if date and date != today_date:
                logger.warning(
                    f"Timer detected stale active session from {date} (today: {today_date}). "
                    "Force-closing..."
                )
                # Use last activity as logical end time for the stale session
                last_activity = doc.get("last_activity") or now_utc()
                await store.end_session(
                    date=date,
                    end_time=last_activity,
                    final_minutes=total_minutes
                )
                logger.info(f"Stale session from {date} force-closed by timer")
                continue

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
                # Use current_session_start and session_start_total_minutes as preconditions
                # to ensure we don't accidentally overwrite a manual edit from main.py
                updated = await store.update_elapsed_time(
                    date, 
                    computed_total_minutes,
                    expected_session_start=doc.get("current_session_start"),
                    expected_baseline_minutes=doc.get("session_start_total_minutes")
                )
                if updated:
                    total_minutes = computed_total_minutes
                else:
                    logger.debug("Timer update skipped: document changed between fetch and update (likely manual edit)")


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
                completed_4h = True

            # Send one pre-leave email once remaining time enters <= 10 minutes window.
            if (
                0 < remaining_minutes <= 10
                and pre_leave_email_sent_at is None
            ):
                pre_subject = "WiFi Tracker: 10 minutes to leave"
                pre_message = _build_pre_leave_email_message(
                    doc,
                    total_minutes=total_minutes,
                    target_minutes=target_minutes,
                )
                pre_html = _build_pre_leave_email_html(
                    doc,
                    total_minutes=total_minutes,
                    target_minutes=target_minutes,
                )
                pre_sent = await asyncio.to_thread(
                    send_email_notification,
                    pre_subject,
                    pre_message,
                    pre_html,
                )
                if pre_sent:
                    sent_at = now_utc()
                    await store.mark_pre_leave_email_sent(date, sent_at)
                    pre_leave_email_sent_at = sent_at
                    logger.info("Pre-leave email sent for %s", date)

            # Send completion notifications, deduped by persisted sent flags.
            if completed_4h:
                completed_at = now_utc()
                completion_subject = "WiFi Tracker: Target completed"
                completion_message = _build_completion_email_message(
                    doc,
                    total_minutes=total_minutes,
                    completed_at_utc=completed_at,
                )
                completion_html = _build_completion_email_html(
                    doc,
                    total_minutes=total_minutes,
                    completed_at_utc=completed_at,
                )

                if completion_desktop_sent_at is None:
                    desktop_sent = send_notification(
                        "Office Wi-Fi Tracker",
                        completion_message,
                    )
                    if desktop_sent:
                        await store.mark_completion_desktop_sent(date, completed_at)
                        completion_desktop_sent_at = completed_at
                        logger.info("Completion desktop notification sent for %s", date)

                if completion_email_sent_at is None:
                    completion_email_sent = await asyncio.to_thread(
                        send_email_notification,
                        completion_subject,
                        completion_message,
                        completion_html,
                    )
                    if completion_email_sent:
                        await store.mark_completion_email_sent(date, completed_at)
                        completion_email_sent_at = completed_at
                        logger.info("Completion email sent for %s", date)

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
