"""
Analytics module for aggregating session data with MongoDB support.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.config import settings
from app.file_store import read_sessions
from app.timer_engine import _resolve_target_components
from app.mongodb_store import MongoDBStore

logger = logging.getLogger(__name__)

# Global reference to MongoDB store (set by main.py)
_mongo_store: Optional[MongoDBStore] = None


def set_mongo_store(store: Optional[MongoDBStore]):
    """Set the global MongoDB store instance."""
    global _mongo_store
    _mongo_store = store


def get_mongo_store() -> Optional[MongoDBStore]:
    """Get the global MongoDB store instance."""
    return _mongo_store


def _is_mongo_store_ready(store: Optional[MongoDBStore]) -> bool:
    """Return True only when store exists and has an initialized db handle."""
    return bool(store and getattr(store, "db", None) is not None)


def get_week_range(week_str: Optional[str] = None) -> tuple[datetime, datetime, str]:
    """
    Get the start (Monday) and end (Sunday) of the week.
    Format of week_str: YYYY-Www (e.g., 2026-W07)
    """
    if week_str:
        try:
            # ISO week parsing
            start_date = datetime.strptime(week_str + "-1", "%G-W%V-%u")
            effective_week_str = week_str
        except ValueError:
            logger.warning("Invalid week format: %s. Defaulting to current week.", week_str)
            now = datetime.now()
            start_date = now - timedelta(days=now.weekday())
            effective_week_str = start_date.strftime("%G-W%V")
    else:
        now = datetime.now()
        start_date = now - timedelta(days=now.weekday())
        effective_week_str = start_date.strftime("%G-W%V")

    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=6)
    return start_date, end_date, effective_week_str


async def get_weekly_aggregation_async(week_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Aggregate daily data for the specified week using MongoDB.
    """
    start_date, end_date, effective_week_str = get_week_range(week_str)

    target_hours, target_minutes = _resolve_target_components(
        test_mode=getattr(settings, "test_mode", False),
        test_duration_minutes=getattr(settings, "test_duration_minutes", 2),
        work_duration_hours=getattr(settings, "work_duration_hours", 4),
        buffer_minutes=getattr(settings, "buffer_minutes", 10),
    )
    target_total_minutes = target_hours * 60 + target_minutes

    days_data = []
    total_week_minutes = 0
    days_target_met = 0

    # Use MongoDB if available, otherwise fallback to file-based
    store = get_mongo_store()
    if _is_mongo_store_ready(store):
        # MongoDB aggregation pipeline
        current_day = start_date
        while current_day <= end_date:
            date_str = current_day.strftime("%d-%m-%Y")
            doc = await store.get_daily_status(date_str)

            if doc:
                day_minutes = doc.get("total_minutes", 0)
                session_count = doc.get("sessions_count", 0)
            else:
                day_minutes = 0
                session_count = 0

            # Changed: Target is now "days in office" not "hours worked"
            # A day counts if you came to office (any time > 0)
            was_in_office = day_minutes > 0
            target_met = day_minutes >= target_total_minutes  # Keep for backward compatibility

            days_data.append({
                "date": date_str,
                "day": current_day.strftime("%a"),
                "total_minutes": day_minutes,
                "session_count": session_count,
                "target_met": target_met,
                "was_in_office": was_in_office  # New field
            })

            total_week_minutes += day_minutes
            if was_in_office:
                days_target_met += 1  # Now counts "days in office" not "days that met time target"

            current_day += timedelta(days=1)
    else:
        # Fallback to file-based (legacy)
        current_day = start_date
        while current_day <= end_date:
            sessions = read_sessions(current_day)

            day_minutes = 0
            session_count = 0

            # Deduplicate and aggregate
            seen_sessions = set()
            for s in sessions:
                if not isinstance(s, dict):
                    continue

                key = (s.get("start_time"), s.get("ssid"))
                if key in seen_sessions:
                    continue
                seen_sessions.add(key)

                duration = s.get("duration_minutes")
                if duration is not None:
                    day_minutes += max(0, int(duration))
                session_count += 1

            # Changed: Target is now "days in office" not "hours worked"
            was_in_office = day_minutes > 0
            target_met = day_minutes >= target_total_minutes  # Keep for backward compatibility

            days_data.append({
                "date": current_day.strftime("%d-%m-%Y"),
                "day": current_day.strftime("%a"),
                "total_minutes": day_minutes,
                "session_count": session_count,
                "target_met": target_met,
                "was_in_office": was_in_office  # New field
            })

            total_week_minutes += day_minutes
            if was_in_office:
                days_target_met += 1  # Now counts "days in office"

            current_day += timedelta(days=1)

    # Calculate average only for office days (days with time > 0)
    office_days_count = sum(1 for day in days_data if day["total_minutes"] > 0)
    avg_minutes = total_week_minutes / office_days_count if office_days_count > 0 else 0

    return {
        "week": effective_week_str,
        "days": days_data,
        "total_minutes": total_week_minutes,
        "avg_minutes_per_day": round(avg_minutes, 1),
        "days_target_met": days_target_met,  # Kept for backward compatibility
        "days_in_office": days_target_met,  # NEW: Number of days you came to office (target: 3/week)
        "office_days_count": office_days_count  # NEW: For debugging/display
    }


def get_weekly_aggregation(week_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for get_weekly_aggregation_async (for backward compatibility).
    """
    return asyncio.run(get_weekly_aggregation_async(week_str))


def get_month_range(month_str: Optional[str] = None) -> tuple[datetime, datetime, str]:
    """
    Get month start and end for YYYY-MM token.
    Falls back to current month on invalid input.
    """
    if month_str:
        try:
            month_start = datetime.strptime(month_str, "%Y-%m")
        except ValueError:
            logger.warning("Invalid month format: %s. Defaulting to current month.", month_str)
            month_start = datetime.now()
    else:
        month_start = datetime.now()

    month_start = month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1, day=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1, day=1)

    month_end = next_month_start - timedelta(days=1)
    effective_month_str = month_start.strftime("%Y-%m")
    return month_start, month_end, effective_month_str


def _safe_non_negative_minutes(value: Any) -> int:
    """Parse minutes and clamp invalid/negative values to zero."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def _aggregate_day_minutes(sessions: Any) -> int:
    """Aggregate total minutes for one day with duplicate protection."""
    if not isinstance(sessions, list):
        return 0

    day_minutes = 0
    seen_sessions = set()
    for session in sessions:
        if not isinstance(session, dict):
            continue

        key = (session.get("start_time"), session.get("ssid"))
        if key in seen_sessions:
            continue
        seen_sessions.add(key)

        day_minutes += _safe_non_negative_minutes(session.get("duration_minutes"))
    return day_minutes


async def get_monthly_aggregation_async(month_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Aggregate month data into week-sized buckets using MongoDB.
    """
    month_start, month_end, effective_month_str = get_month_range(month_str)

    weeks_data = []
    month_total_minutes = 0
    month_days_present = 0

    # Use MongoDB if available, otherwise fallback to file-based
    store = get_mongo_store()

    week_index = 1
    week_start = month_start
    while week_start <= month_end:
        week_end = min(week_start + timedelta(days=6), month_end)

        week_total_minutes = 0
        week_days_present = 0

        current_day = week_start
        while current_day <= week_end:
            if _is_mongo_store_ready(store):
                # MongoDB query
                date_str = current_day.strftime("%d-%m-%Y")
                try:
                    doc = await store.get_daily_status(date_str)
                    day_minutes = doc.get("total_minutes", 0) if doc else 0
                except Exception:
                    logger.warning("Failed to get MongoDB status for %s", date_str)
                    day_minutes = 0
            else:
                # Fallback to file-based (legacy)
                try:
                    sessions = read_sessions(current_day)
                except Exception:
                    logger.warning("Failed to read sessions for %s during monthly aggregation", current_day)
                    sessions = []
                day_minutes = _aggregate_day_minutes(sessions)

            week_total_minutes += day_minutes
            if day_minutes > 0:
                week_days_present += 1
            current_day += timedelta(days=1)

        week_avg_daily_minutes = (
            round(week_total_minutes / week_days_present, 1) if week_days_present > 0 else 0.0
        )

        weeks_data.append(
            {
                "week": f"Week {week_index}",
                "start_date": week_start.strftime("%d-%m-%Y"),
                "end_date": week_end.strftime("%d-%m-%Y"),
                "total_minutes": week_total_minutes,
                "days_present": week_days_present,
                "avg_daily_minutes": week_avg_daily_minutes,
            }
        )

        month_total_minutes += week_total_minutes
        month_days_present += week_days_present
        week_index += 1
        week_start = week_end + timedelta(days=1)

    month_avg_daily_minutes = (
        round(month_total_minutes / month_days_present, 1) if month_days_present > 0 else 0.0
    )

    return {
        "month": effective_month_str,
        "weeks": weeks_data,
        "total_minutes": month_total_minutes,
        "total_days_present": month_days_present,
        "avg_daily_minutes": month_avg_daily_minutes,
    }


def get_monthly_aggregation(month_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for get_monthly_aggregation_async (for backward compatibility).
    """
    return asyncio.run(get_monthly_aggregation_async(month_str))
