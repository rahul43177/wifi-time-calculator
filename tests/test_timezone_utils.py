"""
Tests for timezone utilities (IST handling).
Ensures all datetime operations work correctly for India/Bangalore timezone.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.timezone_utils import (
    now_ist,
    now_utc,
    utc_to_ist,
    ist_to_utc,
    get_today_date_ist,
    format_time_ist,
    format_datetime_ist,
    is_same_day_ist,
    get_week_range_ist,
    get_month_range_ist
)


def test_now_functions():
    """Test that now_ist() and now_utc() return correct timezones"""
    utc_time = now_utc()
    ist_time = now_ist()

    # Both should be timezone-aware
    assert ist_time.tzinfo is not None
    assert utc_time.tzinfo is not None

    # Convert UTC to IST and compare hours/minutes (ignore seconds for timing differences)
    ist_from_utc = utc_to_ist(utc_time)

    # The hour and minute should match (allowing for potential minute boundary)
    hour_diff = abs(ist_time.hour - ist_from_utc.hour)
    minute_diff = abs(ist_time.minute - ist_from_utc.minute)

    # Should be within same minute or adjacent minute (for timing differences)
    assert hour_diff <= 1
    assert minute_diff <= 1


def test_utc_to_ist_conversion():
    """Test UTC to IST conversion"""
    # Create a UTC datetime
    utc_dt = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)  # 10:00 UTC

    # Convert to IST
    ist_dt = utc_to_ist(utc_dt)

    # Should be 15:30 IST (10:00 + 5:30)
    assert ist_dt.hour == 15
    assert ist_dt.minute == 30
    assert ist_dt.day == 15


def test_utc_to_ist_midnight_boundary():
    """Test UTC to IST conversion across midnight boundary"""
    # 20:00 UTC on Feb 15 = 01:30 IST on Feb 16
    utc_dt = datetime(2026, 2, 15, 20, 0, 0, tzinfo=timezone.utc)
    ist_dt = utc_to_ist(utc_dt)

    assert ist_dt.day == 16  # Next day in IST
    assert ist_dt.hour == 1
    assert ist_dt.minute == 30


def test_ist_to_utc_conversion():
    """Test IST to UTC conversion"""
    # Create an IST datetime (naive, will be treated as IST)
    ist_dt = datetime(2026, 2, 15, 15, 30, 0)  # 15:30 IST

    # Convert to UTC
    utc_dt = ist_to_utc(ist_dt)

    # Should be 10:00 UTC (15:30 - 5:30)
    assert utc_dt.hour == 10
    assert utc_dt.minute == 0
    assert utc_dt.day == 15


def test_get_today_date_ist():
    """Test that today's date is in DD-MM-YYYY format based on IST"""
    date_str = get_today_date_ist()

    # Should be in DD-MM-YYYY format
    assert len(date_str) == 10
    assert date_str[2] == '-'
    assert date_str[5] == '-'

    # Should parse correctly
    parsed = datetime.strptime(date_str, "%d-%m-%Y")
    assert parsed.year >= 2026


def test_format_time_ist():
    """Test time formatting in IST"""
    # UTC: 10:00:00
    utc_dt = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)

    # Format in IST (should be 15:30:00)
    time_str = format_time_ist(utc_dt)

    assert time_str == "15:30:00"


def test_format_datetime_ist():
    """Test datetime formatting in IST"""
    # UTC: Feb 15, 2026 10:00:00
    utc_dt = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)

    # Format in IST (should be Feb 15, 2026 15:30:00)
    dt_str = format_datetime_ist(utc_dt)

    assert dt_str == "15-02-2026 15:30:00"


def test_is_same_day_ist_true():
    """Test that datetimes on same IST day return True"""
    # Both on Feb 15 IST
    dt1 = datetime(2026, 2, 15, 5, 0, 0, tzinfo=timezone.utc)   # 10:30 IST
    dt2 = datetime(2026, 2, 15, 15, 0, 0, tzinfo=timezone.utc)  # 20:30 IST

    assert is_same_day_ist(dt1, dt2) is True


def test_is_same_day_ist_false():
    """Test that datetimes on different IST days return False"""
    # Feb 15 23:00 IST vs Feb 16 00:00 IST (same UTC day, different IST day)
    dt1 = datetime(2026, 2, 15, 17, 30, 0, tzinfo=timezone.utc)  # Feb 15 23:00 IST
    dt2 = datetime(2026, 2, 15, 18, 30, 0, tzinfo=timezone.utc)  # Feb 16 00:00 IST

    assert is_same_day_ist(dt1, dt2) is False


def test_get_week_range_ist():
    """Test getting week range in IST"""
    # Feb 15, 2026 is a Sunday
    test_date = datetime(2026, 2, 15, 12, 0, 0, tzinfo=timezone.utc)  # Some time on Feb 15

    monday_start, sunday_end = get_week_range_ist(test_date)

    # Week should be Feb 9 (Monday) to Feb 15 (Sunday)
    assert monday_start.day == 9
    assert sunday_end.day == 15
    assert monday_start.hour == 0
    assert monday_start.minute == 0


def test_get_month_range_ist():
    """Test getting month range in IST"""
    first_day, last_day = get_month_range_ist(2026, 2)

    # February 2026
    assert first_day.day == 1
    assert first_day.month == 2
    assert first_day.year == 2026

    # February has 28 days in 2026 (not a leap year)
    assert last_day.day == 28
    assert last_day.month == 2


def test_utc_to_ist_naive_datetime():
    """Test that naive datetimes are treated as UTC"""
    # Naive datetime (no timezone)
    naive_dt = datetime(2026, 2, 15, 10, 0, 0)

    # Should treat as UTC and convert to IST
    ist_dt = utc_to_ist(naive_dt)

    assert ist_dt.hour == 15
    assert ist_dt.minute == 30


def test_format_none_values():
    """Test that formatting None values returns empty string"""
    assert format_time_ist(None) == ""
    assert format_datetime_ist(None) == ""


def test_critical_midnight_boundary():
    """
    Critical test: Ensure session tracking works correctly across midnight IST.

    Scenario: User connects at 23:00 IST, app restarts at 00:30 IST.
    - Connection at 23:00 IST = Feb 15
    - Restart at 00:30 IST = Feb 16
    - These should be treated as DIFFERENT days
    """
    # 23:00 IST on Feb 15 (17:30 UTC)
    connect_time_utc = datetime(2026, 2, 15, 17, 30, 0, tzinfo=timezone.utc)

    # 00:30 IST on Feb 16 (19:00 UTC on Feb 15)
    restart_time_utc = datetime(2026, 2, 15, 19, 0, 0, tzinfo=timezone.utc)

    # Convert to IST
    connect_ist = utc_to_ist(connect_time_utc)
    restart_ist = utc_to_ist(restart_time_utc)

    # Verify IST dates
    assert connect_ist.day == 15
    assert connect_ist.hour == 23

    assert restart_ist.day == 16
    assert restart_ist.hour == 0
    assert restart_ist.minute == 30

    # Different IST days
    assert is_same_day_ist(connect_time_utc, restart_time_utc) is False

    # Date strings should be different
    connect_date = format_datetime_ist(connect_time_utc, "%d-%m-%Y")
    restart_date = format_datetime_ist(restart_time_utc, "%d-%m-%Y")

    assert connect_date == "15-02-2026"
    assert restart_date == "16-02-2026"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
