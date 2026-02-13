"""
Tests for Phase 5.1: Weekly Data Aggregation API.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_get_weekly_api_schema_correctness():
    """GET /api/weekly should return correct schema."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/weekly")
    assert response.status_code == 200
    data = response.json()
    assert "week" in data
    assert "days" in data
    assert len(data["days"]) == 7
    assert "total_minutes" in data
    assert "avg_minutes_per_day" in data
    assert "days_target_met" in data


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
@patch("app.analytics.datetime")
async def test_get_weekly_aggregation_logic(mock_datetime, mock_read_sessions):
    """Test weekly aggregation with mocked data."""
    # Mock current date to Wednesday, 2026-02-11
    fixed_now = datetime(2026, 2, 11)
    mock_datetime.now.return_value = fixed_now
    mock_datetime.strptime.side_effect = datetime.strptime
    
    # Week start (Monday) is 2026-02-09
    
    def side_effect(date):
        if date.strftime("%d-%m-%Y") == "09-02-2026":
            return [{"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 300, "completed_4h": True}]
        if date.strftime("%d-%m-%Y") == "10-02-2026":
            return [{"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 100, "completed_4h": False}]
        return []

    mock_read_sessions.side_effect = side_effect

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/weekly?week=2026-W07")
    assert response.status_code == 200
    data = response.json()
    
    assert data["week"] == "2026-W07"
    assert data["total_minutes"] == 400
    assert data["avg_minutes_per_day"] == round(400 / 7, 1)
    
    # Target is 4h 10m (250m) in normal mode
    assert data["days_target_met"] == 1
    
    day1 = next(d for d in data["days"] if d["date"] == "09-02-2026")
    assert day1["total_minutes"] == 300
    assert day1["target_met"] is True
    
    day2 = next(d for d in data["days"] if d["date"] == "10-02-2026")
    assert day2["total_minutes"] == 100
    assert day2["target_met"] is False


@pytest.mark.asyncio
async def test_get_weekly_invalid_params_fallback():
    """Invalid week parameter should fallback to current week."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/weekly?week=invalid")
    assert response.status_code == 200
    data = response.json()
    assert "W" in data["week"]


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_weekly_empty_data(mock_read_sessions):
    """Test aggregation with no sessions."""
    mock_read_sessions.return_value = []
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/weekly?week=2026-W01")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_minutes"] == 0
    assert data["days_target_met"] == 0
    for day in data["days"]:
        assert day["total_minutes"] == 0
        assert day["target_met"] is False


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_weekly_deduplication(mock_read_sessions):
    """Test that duplicate sessions (same start_time, ssid) are counted once."""
    mock_read_sessions.return_value = [
        {"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 100},
        {"start_time": "09:00:00", "ssid": "Office", "duration_minutes": 100}  # Duplicate
    ]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/weekly?week=2026-W07")
    
    data = response.json()
    # 7 days with same mock data = 700 minutes total
    assert data["total_minutes"] == 700
    assert data["days"][0]["total_minutes"] == 100
    assert data["days"][0]["session_count"] == 1


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_weekly_negative_duration_clamping(mock_read_sessions):
    """Test that negative durations are clamped to 0."""
    mock_read_sessions.return_value = [{"duration_minutes": -50, "start_time": "09:00:00", "ssid": "Office"}]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/weekly?week=2026-W07")
    
    data = response.json()
    assert data["total_minutes"] == 0


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_weekly_robustness_non_dict_entries(mock_read_sessions):
    """Test robustness against non-dict session entries."""
    mock_read_sessions.return_value = ["invalid", {"duration_minutes": 100, "start_time": "09:00:00", "ssid": "Office"}]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/weekly?week=2026-W07")
    
    data = response.json()
    assert data["days"][0]["total_minutes"] == 100
    assert data["days"][0]["session_count"] == 1


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_weekly_robustness_none_duration(mock_read_sessions):
    """Test robustness against None duration_minutes."""
    mock_read_sessions.return_value = [
        {"duration_minutes": 100, "start_time": "09:00:00", "ssid": "Office"},
        {"duration_minutes": None, "start_time": "13:00:00", "ssid": "Office"}
    ]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/weekly?week=2026-W07")
    
    data = response.json()
    assert data["days"][0]["total_minutes"] == 100
    assert data["days"][0]["session_count"] == 2


@pytest.mark.asyncio
async def test_get_weekly_year_boundary_2025_2026():
    """Test week calculation at year boundary."""
    # 2025-W52 ends Sunday 2025-12-28
    # 2026-W01 starts Monday 2025-12-29
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/weekly?week=2026-W01")
    
    assert response.status_code == 200
    data = response.json()
    assert data["week"] == "2026-W01"
    assert data["days"][0]["date"] == "29-12-2025" # Monday
    assert data["days"][6]["date"] == "04-01-2026" # Sunday


@pytest.mark.asyncio
@patch("app.analytics.read_sessions")
async def test_get_weekly_target_threshold_logic(mock_read_sessions):
    """Verify target met logic (target is 4h 10m = 250 minutes)."""
    
    def side_effect(date):
        if date.strftime("%d-%m-%Y") == "09-02-2026":
            return [{"duration_minutes": 249, "start_time": "09:00:00", "ssid": "Office"}] # Just under
        if date.strftime("%d-%m-%Y") == "10-02-2026":
            return [{"duration_minutes": 250, "start_time": "09:00:00", "ssid": "Office"}] # Exactly at
        return []

    mock_read_sessions.side_effect = side_effect
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/weekly?week=2026-W07")
    
    data = response.json()
    day1 = next(d for d in data["days"] if d["date"] == "09-02-2026")
    assert day1["target_met"] is False
    
    day2 = next(d for d in data["days"] if d["date"] == "10-02-2026")
    assert day2["target_met"] is True
