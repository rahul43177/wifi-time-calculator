"""
Tests for Phase 5.2: Monthly Data Aggregation API.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_monthly_api_schema_correctness():
    """GET /api/monthly should return correct schema and typed fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=2026-02")

    assert response.status_code == 200
    data = response.json()

    assert data["month"] == "2026-02"
    assert isinstance(data["weeks"], list)
    assert "total_minutes" in data
    assert "total_days_present" in data
    assert "avg_daily_minutes" in data
    assert len(data["weeks"]) == 4
    first_week = data["weeks"][0]
    assert "week" in first_week
    assert "start_date" in first_week
    assert "end_date" in first_week
    assert "total_minutes" in first_week
    assert "days_present" in first_week
    assert "avg_daily_minutes" in first_week


@pytest.mark.asyncio
@patch("app.analytics.datetime")
async def test_get_monthly_defaults_to_current_month(mock_datetime):
    """No month query should default to current month."""
    fixed_now = datetime(2026, 2, 13, 9, 0, 0)
    mock_datetime.now.return_value = fixed_now
    mock_datetime.strptime.side_effect = datetime.strptime

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly")

    assert response.status_code == 200
    assert response.json()["month"] == "2026-02"


@pytest.mark.asyncio
@patch("app.analytics.datetime")
async def test_get_monthly_invalid_month_falls_back_to_current(mock_datetime):
    """Invalid month query should fall back safely to current month."""
    fixed_now = datetime(2026, 3, 5, 10, 0, 0)
    mock_datetime.now.return_value = fixed_now
    mock_datetime.strptime.side_effect = datetime.strptime

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=invalid")

    assert response.status_code == 200
    assert response.json()["month"] == "2026-03"


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_monthly_aggregation_logic(mock_read_sessions):
    """Month aggregation should return week buckets and month totals."""

    def side_effect(date):
        token = date.strftime("%d-%m-%Y")
        if token == "01-02-2026":
            return [{"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 120}]
        if token == "02-02-2026":
            return [{"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 60}]
        if token == "08-02-2026":
            return [{"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 200}]
        if token == "09-02-2026":
            return [{"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 50}]
        return []

    mock_read_sessions.side_effect = side_effect

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=2026-02")

    assert response.status_code == 200
    data = response.json()
    assert data["month"] == "2026-02"
    assert data["total_minutes"] == 430
    assert data["total_days_present"] == 4
    assert data["avg_daily_minutes"] == 107.5

    week1 = data["weeks"][0]
    assert week1["week"] == "Week 1"
    assert week1["start_date"] == "01-02-2026"
    assert week1["end_date"] == "07-02-2026"
    assert week1["total_minutes"] == 180
    assert week1["days_present"] == 2
    assert week1["avg_daily_minutes"] == 90.0

    week2 = data["weeks"][1]
    assert week2["week"] == "Week 2"
    assert week2["total_minutes"] == 250
    assert week2["days_present"] == 2
    assert week2["avg_daily_minutes"] == 125.0


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_monthly_empty_data(mock_read_sessions):
    """Empty month should return zero totals and zero-present days."""
    mock_read_sessions.return_value = []

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=2026-02")

    assert response.status_code == 200
    data = response.json()
    assert data["total_minutes"] == 0
    assert data["total_days_present"] == 0
    assert data["avg_daily_minutes"] == 0.0
    assert len(data["weeks"]) == 4
    for week in data["weeks"]:
        assert week["total_minutes"] == 0
        assert week["days_present"] == 0
        assert week["avg_daily_minutes"] == 0.0


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_monthly_deduplicates_sessions_by_start_and_ssid(mock_read_sessions):
    """Duplicate rows should not be double-counted in daily totals."""
    mock_read_sessions.return_value = [
        {"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 100},
        {"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 100},
        {"start_time": "13:00:00", "ssid": "Office", "duration_minutes": 50},
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=2026-02")

    assert response.status_code == 200
    data = response.json()
    assert data["weeks"][0]["total_minutes"] == 1050
    assert data["weeks"][0]["days_present"] == 7
    assert data["weeks"][0]["avg_daily_minutes"] == 150.0


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_monthly_ignores_non_dict_and_none_duration_entries(mock_read_sessions):
    """Malformed rows should not break aggregation and None duration should be ignored."""
    mock_read_sessions.return_value = [
        "invalid-row",
        {"start_time": "09:00:00", "ssid": "Office", "duration_minutes": None},
        {"start_time": "10:00:00", "ssid": "Office", "duration_minutes": 100},
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=2026-02")

    assert response.status_code == 200
    data = response.json()
    assert data["weeks"][0]["total_minutes"] == 700
    assert data["weeks"][0]["days_present"] == 7
    assert data["weeks"][0]["avg_daily_minutes"] == 100.0


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_monthly_clamps_negative_and_invalid_duration_values(mock_read_sessions):
    """Negative or invalid duration values should be treated as zero."""
    mock_read_sessions.return_value = [
        {"start_time": "09:00:00", "ssid": "Office", "duration_minutes": -30},
        {"start_time": "10:00:00", "ssid": "Office", "duration_minutes": "oops"},
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=2026-02")

    assert response.status_code == 200
    data = response.json()
    assert data["total_minutes"] == 0
    assert data["total_days_present"] == 0
    assert data["avg_daily_minutes"] == 0.0


@pytest.mark.asyncio
async def test_get_monthly_31_day_month_has_five_week_buckets():
    """31-day month should be split into 5 week buckets with clipped final week."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=2026-01")

    assert response.status_code == 200
    data = response.json()
    assert data["month"] == "2026-01"
    assert len(data["weeks"]) == 5
    assert data["weeks"][0]["start_date"] == "01-01-2026"
    assert data["weeks"][-1]["end_date"] == "31-01-2026"


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_monthly_avg_daily_minutes_uses_days_present(mock_read_sessions):
    """Average daily minutes should divide by present days, not total calendar days."""

    def side_effect(date):
        token = date.strftime("%d-%m-%Y")
        if token in {"01-02-2026", "02-02-2026"}:
            return [{"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 120}]
        return []

    mock_read_sessions.side_effect = side_effect

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=2026-02")

    assert response.status_code == 200
    data = response.json()
    assert data["total_minutes"] == 240
    assert data["total_days_present"] == 2
    assert data["avg_daily_minutes"] == 120.0


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_monthly_handles_read_sessions_exception(mock_read_sessions):
    """Storage read errors should not crash monthly aggregation."""
    mock_read_sessions.side_effect = RuntimeError("read failed")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=2026-02")

    assert response.status_code == 200
    data = response.json()
    assert data["total_minutes"] == 0
    assert data["total_days_present"] == 0
    assert data["avg_daily_minutes"] == 0.0


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_monthly_handles_non_list_read_payload(mock_read_sessions):
    """Non-list payload from storage should degrade safely to zero data."""
    mock_read_sessions.return_value = {"unexpected": "shape"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/monthly?month=2026-02")

    assert response.status_code == 200
    data = response.json()
    assert data["total_minutes"] == 0
    assert data["total_days_present"] == 0
