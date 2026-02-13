"""
Analytics module for aggregating session data.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.config import settings
from app.file_store import read_sessions
from app.timer_engine import _resolve_target_components

logger = logging.getLogger(__name__)


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


def get_weekly_aggregation(week_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Aggregate daily data for the specified week.
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
            
            # Use (start_time, ssid) as a simple key to avoid double-counting rotated log parts
            # although read_sessions already handles most of this.
            key = (s.get("start_time"), s.get("ssid"))
            if key in seen_sessions:
                continue
            seen_sessions.add(key)
            
            duration = s.get("duration_minutes")
            if duration is not None:
                day_minutes += max(0, int(duration))
            session_count += 1

        target_met = day_minutes >= target_total_minutes
        
        days_data.append({
            "date": current_day.strftime("%d-%m-%Y"),
            "day": current_day.strftime("%a"),
            "total_minutes": day_minutes,
            "session_count": session_count,
            "target_met": target_met
        })
        
        total_week_minutes += day_minutes
        if target_met:
            days_target_met += 1
            
        current_day += timedelta(days=1)

    avg_minutes = total_week_minutes / 7

    return {
        "week": effective_week_str,
        "days": days_data,
        "total_minutes": total_week_minutes,
        "avg_minutes_per_day": round(avg_minutes, 1),
        "days_target_met": days_target_met
    }
