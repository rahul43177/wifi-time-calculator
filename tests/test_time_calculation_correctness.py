"""Focused tests for cumulative timing math in MongoDB mode."""

from datetime import datetime, timedelta, UTC
from unittest.mock import patch

import pytest

from app.session_manager import SessionManager
from app.timer_engine import _compute_running_total_minutes


def _utc_now() -> datetime:
    return datetime(2026, 2, 23, 12, 0, 0, tzinfo=UTC)


def test_running_total_uses_session_baseline_without_double_counting() -> None:
    now = _utc_now()
    doc = {
        "total_minutes": 123,
        "session_start_total_minutes": 120,
        "current_session_start": now - timedelta(minutes=20),
        "paused_duration_minutes": 0,
        "session_start_paused_minutes": 0,
        "has_network_access": True,
    }

    total = _compute_running_total_minutes(doc, now=now)
    assert total == 140


def test_running_total_falls_back_safely_when_baseline_missing() -> None:
    now = _utc_now()
    doc = {
        "total_minutes": 150,
        "current_session_start": now - timedelta(minutes=30),
        "paused_duration_minutes": 0,
        "has_network_access": True,
    }

    total = _compute_running_total_minutes(doc, now=now)
    assert total == 150


def test_running_total_subtracts_paused_time_since_session_start() -> None:
    now = _utc_now()
    doc = {
        "total_minutes": 140,
        "session_start_total_minutes": 100,
        "current_session_start": now - timedelta(minutes=60),
        "paused_duration_minutes": 15,
        "session_start_paused_minutes": 5,
        "has_network_access": True,
    }

    total = _compute_running_total_minutes(doc, now=now)
    assert total == 150


def test_running_total_excludes_current_ongoing_pause() -> None:
    now = _utc_now()
    doc = {
        "total_minutes": 55,
        "session_start_total_minutes": 0,
        "current_session_start": now - timedelta(minutes=60),
        "paused_duration_minutes": 0,
        "session_start_paused_minutes": 0,
        "has_network_access": False,
        "paused_at": now - timedelta(minutes=10),
    }

    total = _compute_running_total_minutes(doc, now=now)
    assert total == 50


@pytest.mark.asyncio
async def test_session_manager_final_total_uses_baseline_without_inflation() -> None:
    now = _utc_now()
    doc = {
        "total_minutes": 130,
        "session_start_total_minutes": 120,
        "current_session_start": now - timedelta(minutes=15),
        "paused_duration_minutes": 0,
        "session_start_paused_minutes": 0,
        "has_network_access": True,
    }

    class _Store:
        async def get_daily_status(self, _date: str):
            return doc

    manager = SessionManager(_Store())
    manager._current_date = "23-02-2026"
    manager._current_session_start = doc["current_session_start"]

    with patch("app.session_manager.now_utc", return_value=now):
        total = await manager._calculate_current_total()

    assert total == 135

