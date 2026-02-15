"""
Timezone utilities for India/Bangalore (IST = UTC+5:30).

All datetimes are stored in UTC in MongoDB, but displayed in IST for the user.
This ensures consistency across system restarts and handles edge cases correctly.
"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

# India Standard Time timezone
IST = ZoneInfo("Asia/Kolkata")  # UTC+5:30

# For systems without zoneinfo database, fallback to manual UTC offset
IST_OFFSET = timezone(timedelta(hours=5, minutes=30))


def now_ist() -> datetime:
    """
    Get current datetime in IST (India Standard Time).

    Returns:
        Timezone-aware datetime in IST
    """
    try:
        return datetime.now(IST)
    except Exception:
        # Fallback if zoneinfo is not available
        return datetime.now(IST_OFFSET)


def now_utc() -> datetime:
    """
    Get current datetime in UTC (for MongoDB storage).

    Returns:
        Timezone-aware datetime in UTC
    """
    return datetime.now(timezone.utc)


def utc_to_ist(dt: datetime) -> datetime:
    """
    Convert UTC datetime to IST.

    Args:
        dt: UTC datetime (timezone-aware or naive)

    Returns:
        Datetime in IST timezone
    """
    if dt is None:
        return None

    # If naive, assume it's UTC (from MongoDB)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    try:
        return dt.astimezone(IST)
    except Exception:
        # Fallback if zoneinfo is not available
        return dt.astimezone(IST_OFFSET)


def ist_to_utc(dt: datetime) -> datetime:
    """
    Convert IST datetime to UTC (for MongoDB storage).

    Args:
        dt: IST datetime

    Returns:
        Datetime in UTC timezone
    """
    if dt is None:
        return None

    # If naive, assume it's IST
    if dt.tzinfo is None:
        try:
            dt = dt.replace(tzinfo=IST)
        except Exception:
            dt = dt.replace(tzinfo=IST_OFFSET)

    return dt.astimezone(timezone.utc)


def get_today_date_ist() -> str:
    """
    Get today's date in IST as DD-MM-YYYY format.

    This is critical for session tracking - the "day" is based on
    Indian timezone, not UTC.

    Returns:
        Date string in DD-MM-YYYY format (IST)
    """
    return now_ist().strftime("%d-%m-%Y")


def format_time_ist(dt: datetime, time_format: str = "%H:%M:%S") -> str:
    """
    Format datetime in IST timezone.

    Args:
        dt: Datetime to format (UTC or IST)
        time_format: strftime format string

    Returns:
        Formatted time string in IST
    """
    if dt is None:
        return ""

    ist_dt = utc_to_ist(dt)
    return ist_dt.strftime(time_format)


def format_datetime_ist(dt: datetime, dt_format: str = "%d-%m-%Y %H:%M:%S") -> str:
    """
    Format datetime in IST timezone.

    Args:
        dt: Datetime to format (UTC or IST)
        dt_format: strftime format string

    Returns:
        Formatted datetime string in IST
    """
    if dt is None:
        return ""

    ist_dt = utc_to_ist(dt)
    return ist_dt.strftime(dt_format)


def get_ist_from_date_string(date_str: str) -> datetime:
    """
    Parse DD-MM-YYYY date string as IST midnight.

    Args:
        date_str: Date in DD-MM-YYYY format

    Returns:
        Datetime at midnight IST for that date
    """
    dt = datetime.strptime(date_str, "%d-%m-%Y")
    try:
        return dt.replace(tzinfo=IST)
    except Exception:
        return dt.replace(tzinfo=IST_OFFSET)


def is_same_day_ist(dt1: datetime, dt2: datetime) -> bool:
    """
    Check if two datetimes are on the same IST day.

    Important: A session at 23:00 IST and 01:00 IST next day
    are NOT the same day in India, even if only 2 hours apart.

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        True if same IST day, False otherwise
    """
    ist1 = utc_to_ist(dt1)
    ist2 = utc_to_ist(dt2)
    return ist1.date() == ist2.date()


def get_week_range_ist(date: datetime) -> tuple[datetime, datetime]:
    """
    Get the Monday-Sunday week range for a given date in IST.

    Args:
        date: Any datetime in the week

    Returns:
        Tuple of (monday_start, sunday_end) in IST
    """
    ist_date = utc_to_ist(date)

    # Find Monday of this week (weekday 0 = Monday)
    days_since_monday = ist_date.weekday()
    monday = ist_date - timedelta(days=days_since_monday)
    monday_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)

    # Find Sunday of this week
    sunday_end = monday_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    return (monday_start, sunday_end)


def get_month_range_ist(year: int, month: int) -> tuple[datetime, datetime]:
    """
    Get the first and last day of a month in IST.

    Args:
        year: Year (e.g., 2026)
        month: Month (1-12)

    Returns:
        Tuple of (first_day, last_day) in IST
    """
    try:
        first_day = datetime(year, month, 1, 0, 0, 0, tzinfo=IST)
    except Exception:
        first_day = datetime(year, month, 1, 0, 0, 0, tzinfo=IST_OFFSET)

    # Get last day of month
    if month == 12:
        try:
            next_month = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=IST)
        except Exception:
            next_month = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=IST_OFFSET)
    else:
        try:
            next_month = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=IST)
        except Exception:
            next_month = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=IST_OFFSET)

    last_day = next_month - timedelta(microseconds=1)

    return (first_day, last_day)


# Example usage and tests
if __name__ == "__main__":
    print("=" * 60)
    print("TIMEZONE UTILITIES TEST")
    print("=" * 60)

    print(f"\nCurrent time IST: {now_ist()}")
    print(f"Current time UTC: {now_utc()}")
    print(f"Today's date (IST): {get_today_date_ist()}")

    utc_time = now_utc()
    ist_time = utc_to_ist(utc_time)
    print(f"\nUTC: {utc_time}")
    print(f"IST: {ist_time}")
    print(f"Difference: {(ist_time.hour - utc_time.hour) % 24} hours {ist_time.minute - utc_time.minute} minutes")

    print(f"\nFormatted time (IST): {format_time_ist(utc_time)}")
    print(f"Formatted datetime (IST): {format_datetime_ist(utc_time)}")

    # Test date boundary crossing
    print("\n" + "=" * 60)
    print("MIDNIGHT BOUNDARY TEST")
    print("=" * 60)

    # Example: 23:00 IST = 17:30 UTC
    # Next hour: 00:00 IST = 18:30 UTC (same UTC day, different IST day)
    test_utc_1 = datetime(2026, 2, 15, 17, 30, 0, tzinfo=timezone.utc)  # 23:00 IST
    test_utc_2 = datetime(2026, 2, 15, 18, 30, 0, tzinfo=timezone.utc)  # 00:00 IST next day

    print(f"UTC 1: {test_utc_1} → IST: {utc_to_ist(test_utc_1)}")
    print(f"UTC 2: {test_utc_2} → IST: {utc_to_ist(test_utc_2)}")
    print(f"Same IST day? {is_same_day_ist(test_utc_1, test_utc_2)}")

    print("\n" + "=" * 60)
