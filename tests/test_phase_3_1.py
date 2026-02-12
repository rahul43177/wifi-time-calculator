"""
Tests for Phase 3.1: Timer Calculation Logic.

Covers:
- Elapsed and remaining time calculations
- Buffer-aware target duration logic
- Negative remaining time (overtime) behavior
- Time display formatting
- Timezone-aware handling and invalid state safety
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.timer_engine import (
    format_time_display,
    get_elapsed_time,
    get_remaining_time,
    is_completed,
)


def test_get_elapsed_time_happy_path() -> None:
    """Elapsed time is now - start_time for naive datetimes."""
    start = datetime(2026, 2, 13, 9, 0, 0)
    now = datetime(2026, 2, 13, 10, 15, 30)

    elapsed = get_elapsed_time(start, now=now)

    assert elapsed == timedelta(hours=1, minutes=15, seconds=30)


def test_get_elapsed_time_uses_internal_time_provider_when_now_missing() -> None:
    """Elapsed calculation uses internal current-time provider when now not supplied."""
    start = datetime(2026, 2, 13, 9, 0, 0)
    fixed_now = datetime(2026, 2, 13, 9, 45, 0)

    with patch("app.timer_engine._get_current_time", return_value=fixed_now) as mocked_now:
        elapsed = get_elapsed_time(start)

    mocked_now.assert_called_once_with(start)
    assert elapsed == timedelta(minutes=45)


def test_get_elapsed_time_future_start_is_clamped_to_zero() -> None:
    """Future start times are clamped to zero elapsed."""
    start = datetime(2026, 2, 13, 12, 0, 0)
    now = datetime(2026, 2, 13, 11, 59, 59)

    elapsed = get_elapsed_time(start, now=now)

    assert elapsed == timedelta(0)


def test_get_elapsed_time_timezone_aware_values_are_supported() -> None:
    """Timezone-aware datetimes are calculated correctly."""
    ist = timezone(timedelta(hours=5, minutes=30))
    start = datetime(2026, 2, 13, 9, 0, 0, tzinfo=ist)
    now = datetime(2026, 2, 13, 10, 30, 0, tzinfo=ist)

    elapsed = get_elapsed_time(start, now=now)

    assert elapsed == timedelta(hours=1, minutes=30)


def test_get_elapsed_time_timezone_mismatch_returns_zero() -> None:
    """Mixed aware/naive datetime inputs return safe zero elapsed."""
    utc = timezone.utc
    start = datetime(2026, 2, 13, 9, 0, 0, tzinfo=utc)
    now = datetime(2026, 2, 13, 10, 0, 0)  # naive

    elapsed = get_elapsed_time(start, now=now)

    assert elapsed == timedelta(0)


def test_get_remaining_time_includes_buffer_minutes() -> None:
    """Remaining time uses target_hours + buffer_minutes."""
    start = datetime(2026, 2, 13, 9, 0, 0)
    now = datetime(2026, 2, 13, 11, 0, 0)  # elapsed 2h

    remaining = get_remaining_time(
        start_time=start,
        target_hours=4,
        buffer_minutes=10,
        now=now,
    )

    assert remaining == timedelta(hours=2, minutes=10)


def test_get_remaining_time_can_be_negative_after_target() -> None:
    """Remaining goes negative in overtime (no cap)."""
    start = datetime(2026, 2, 13, 9, 0, 0)
    now = datetime(2026, 2, 13, 13, 45, 0)  # elapsed 4h45m, target 4h10m

    remaining = get_remaining_time(
        start_time=start,
        target_hours=4,
        buffer_minutes=10,
        now=now,
    )

    assert remaining == timedelta(minutes=-35)


def test_get_remaining_time_negative_config_inputs_are_clamped() -> None:
    """Negative target inputs are clamped to zero for safe behavior."""
    start = datetime(2026, 2, 13, 9, 0, 0)
    now = datetime(2026, 2, 13, 9, 30, 0)

    remaining = get_remaining_time(
        start_time=start,
        target_hours=-4,
        buffer_minutes=-10,
        now=now,
    )

    assert remaining == timedelta(minutes=-30)


def test_format_time_display_positive_values() -> None:
    """Timedeltas are formatted as HH:MM:SS."""
    formatted = format_time_display(timedelta(hours=1, minutes=2, seconds=3))
    assert formatted == "01:02:03"


def test_format_time_display_negative_values() -> None:
    """Negative timedeltas include a '-' prefix."""
    formatted = format_time_display(timedelta(minutes=-20, seconds=-5))
    assert formatted == "-00:20:05"


def test_format_time_display_large_hour_values() -> None:
    """Formatting supports durations beyond 24 hours."""
    formatted = format_time_display(timedelta(hours=27, minutes=5, seconds=6))
    assert formatted == "27:05:06"


def test_format_time_display_invalid_input_returns_default() -> None:
    """Invalid values are handled gracefully with a safe default string."""
    formatted = format_time_display("not-a-timedelta")  # type: ignore[arg-type]
    assert formatted == "00:00:00"


def test_is_completed_false_before_target() -> None:
    """Completion is False before target + buffer is reached."""
    start = datetime(2026, 2, 13, 9, 0, 0)
    now = datetime(2026, 2, 13, 12, 0, 0)

    completed = is_completed(
        start_time=start,
        target_hours=4,
        buffer_minutes=10,
        now=now,
    )

    assert completed is False


def test_is_completed_true_at_or_after_target() -> None:
    """Completion is True at target boundary and in overtime."""
    start = datetime(2026, 2, 13, 9, 0, 0)
    at_target = datetime(2026, 2, 13, 13, 10, 0)
    after_target = datetime(2026, 2, 13, 13, 15, 0)

    assert is_completed(
        start_time=start,
        target_hours=4,
        buffer_minutes=10,
        now=at_target,
    ) is True
    assert is_completed(
        start_time=start,
        target_hours=4,
        buffer_minutes=10,
        now=after_target,
    ) is True
