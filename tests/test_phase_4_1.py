"""
Tests for Phase 4.1: Dashboard status/today API endpoints.

Covers:
- Normal API responses
- Empty states
- Edge cases and malformed state handling
- JSON schema/type correctness
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


@pytest.fixture(autouse=True)
def _set_office_wifi_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep office SSID deterministic across endpoint tests."""
    monkeypatch.setattr(settings, "office_wifi_name", "OfficeWifi")


def _session(
    *,
    date: str = "12-02-2026",
    ssid: str = "OfficeWifi",
    start_time: str = "09:00:00",
    end_time: str | None = None,
    duration_minutes: int | None = None,
    completed_4h: bool = False,
) -> SimpleNamespace:
    """Build a simple active-session stub object."""
    return SimpleNamespace(
        date=date,
        ssid=ssid,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration_minutes,
        completed_4h=completed_4h,
    )


@pytest.mark.asyncio
async def test_api_status_empty_state_returns_defaults() -> None:
    """No active session returns safe defaults with strict schema."""
    manager = SimpleNamespace(active_session=None)

    with patch("app.main.get_session_manager", return_value=manager):
        with patch("app.main.get_current_ssid", return_value=None):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/status")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "connected",
        "ssid",
        "session_active",
        "start_time",
        "elapsed_seconds",
        "elapsed_display",
        "remaining_seconds",
        "remaining_display",
        "completed_4h",
        "progress_percent",
        "target_display",
    }
    assert payload["connected"] is False
    assert payload["ssid"] is None
    assert payload["session_active"] is False
    assert payload["start_time"] is None
    assert payload["elapsed_seconds"] == 0
    assert payload["elapsed_display"] == "00:00:00"
    assert payload["remaining_seconds"] == (4 * 3600) + (10 * 60)
    assert payload["remaining_display"] == "04:10:00"
    assert payload["completed_4h"] is False
    assert payload["progress_percent"] == 0.0
    assert payload["target_display"] == "4h 10m"


@pytest.mark.asyncio
async def test_api_status_active_session_calculates_elapsed_remaining_and_progress() -> None:
    """Active session includes deterministic timer details."""
    active = _session()
    manager = SimpleNamespace(active_session=active)
    now = datetime(2026, 2, 12, 11, 0, 0)

    with patch("app.main.get_session_manager", return_value=manager):
        with patch("app.main.get_current_ssid", return_value="OfficeWifi"):
            with patch("app.main._get_now", return_value=now):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/api/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["connected"] is True
    assert payload["ssid"] == "OfficeWifi"
    assert payload["session_active"] is True
    assert payload["start_time"] == "09:00:00"
    assert payload["elapsed_seconds"] == 7200
    assert payload["elapsed_display"] == "02:00:00"
    assert payload["remaining_seconds"] == 7800
    assert payload["remaining_display"] == "02:10:00"
    assert payload["completed_4h"] is False
    assert payload["progress_percent"] == 48.0
    assert payload["target_display"] == "4h 10m"


@pytest.mark.asyncio
async def test_api_status_supports_overtime_without_capping_elapsed() -> None:
    """Remaining time can go negative while elapsed keeps increasing."""
    active = _session(start_time="09:00:00")
    manager = SimpleNamespace(active_session=active)
    now = datetime(2026, 2, 12, 14, 30, 0)

    with patch("app.main.get_session_manager", return_value=manager):
        with patch("app.main.get_current_ssid", return_value="OfficeWifi"):
            with patch("app.main._get_now", return_value=now):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/api/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["elapsed_seconds"] == (5 * 3600) + (30 * 60)
    assert payload["remaining_seconds"] == -4800
    assert payload["remaining_display"] == "-01:20:00"
    assert payload["completed_4h"] is True
    assert payload["progress_percent"] == 100.0


@pytest.mark.asyncio
async def test_api_status_uses_test_mode_target_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test mode changes target to short minute-based duration."""
    monkeypatch.setattr(settings, "test_mode", True)
    monkeypatch.setattr(settings, "test_duration_minutes", 2)
    active = _session(start_time="09:00:00")
    manager = SimpleNamespace(active_session=active)
    now = datetime(2026, 2, 12, 9, 1, 0)

    with patch("app.main.get_session_manager", return_value=manager):
        with patch("app.main.get_current_ssid", return_value="OfficeWifi"):
            with patch("app.main._get_now", return_value=now):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/api/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["remaining_seconds"] == 60
    assert payload["target_display"] == "2m"


@pytest.mark.asyncio
async def test_api_status_handles_invalid_active_session_timestamp_gracefully() -> None:
    """Malformed active session does not crash endpoint."""
    manager = SimpleNamespace(
        active_session=_session(date="bad-date", start_time="bad-time", completed_4h=True)
    )

    with patch("app.main.get_session_manager", return_value=manager):
        with patch("app.main.get_current_ssid", return_value="OfficeWifi"):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_active"] is True
    assert payload["start_time"] == "bad-time"
    assert payload["elapsed_seconds"] == 0
    assert payload["remaining_seconds"] == (4 * 3600) + (10 * 60)
    assert payload["completed_4h"] is True


@pytest.mark.asyncio
async def test_api_today_empty_state_returns_empty_sessions() -> None:
    """No file data and no active session returns empty response."""
    now = datetime(2026, 2, 12, 10, 0, 0)
    manager = SimpleNamespace(active_session=None)

    with patch("app.main.get_session_manager", return_value=manager):
        with patch("app.main.read_sessions", return_value=[]):
            with patch("app.main._get_now", return_value=now):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/api/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "date": "12-02-2026",
        "sessions": [],
        "total_minutes": 0,
        "total_display": "0h 00m",
    }


@pytest.mark.asyncio
async def test_api_today_merges_file_snapshots_and_active_session() -> None:
    """Latest file snapshot is used and active session stays live."""
    now = datetime(2026, 2, 12, 13, 15, 0)
    manager = SimpleNamespace(active_session=_session(start_time="12:00:00"))
    raw_sessions = [
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "09:00:00",
            "end_time": None,
            "duration_minutes": None,
            "completed_4h": False,
        },
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "duration_minutes": 120,
            "completed_4h": False,
        },
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "12:00:00",
            "end_time": None,
            "duration_minutes": None,
            "completed_4h": False,
        },
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": None,
            "end_time": None,
            "duration_minutes": 999,
            "completed_4h": False,
        },
    ]

    with patch("app.main.get_session_manager", return_value=manager):
        with patch("app.main.read_sessions", return_value=raw_sessions):
            with patch("app.main._get_now", return_value=now):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/api/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == "12-02-2026"
    assert payload["total_minutes"] == 195
    assert payload["total_display"] == "3h 15m"
    assert payload["sessions"] == [
        {
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "duration_minutes": 120,
            "completed_4h": False,
        },
        {
            "start_time": "12:00:00",
            "end_time": None,
            "duration_minutes": 75,
            "completed_4h": False,
        },
    ]


@pytest.mark.asyncio
async def test_api_today_ignores_non_today_entries() -> None:
    """Rows from other dates are filtered out safely."""
    now = datetime(2026, 2, 12, 10, 0, 0)
    manager = SimpleNamespace(active_session=None)
    raw_sessions = [
        {
            "date": "11-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "duration_minutes": 120,
            "completed_4h": False,
        }
    ]

    with patch("app.main.get_session_manager", return_value=manager):
        with patch("app.main.read_sessions", return_value=raw_sessions):
            with patch("app.main._get_now", return_value=now):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/api/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sessions"] == []
    assert payload["total_minutes"] == 0


@pytest.mark.asyncio
async def test_api_today_handles_invalid_active_session_timestamp_with_fallback_duration() -> None:
    """If active start time is malformed, endpoint falls back to stored duration."""
    now = datetime(2026, 2, 12, 16, 0, 0)
    manager = SimpleNamespace(
        active_session=_session(start_time="bad", duration_minutes=17, completed_4h=True)
    )

    with patch("app.main.get_session_manager", return_value=manager):
        with patch("app.main.read_sessions", return_value=[]):
            with patch("app.main._get_now", return_value=now):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/api/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sessions"] == [
        {
            "start_time": "bad",
            "end_time": None,
            "duration_minutes": 17,
            "completed_4h": True,
        }
    ]
    assert payload["total_minutes"] == 17
    assert payload["total_display"] == "0h 17m"


@pytest.mark.asyncio
async def test_api_today_response_schema_types_are_stable() -> None:
    """Schema fields preserve predictable JSON types for frontend consumption."""
    now = datetime(2026, 2, 12, 11, 0, 0)
    manager = SimpleNamespace(active_session=None)
    raw_sessions = [
        {
            "date": "12-02-2026",
            "ssid": "OfficeWifi",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "duration_minutes": 60,
            "completed_4h": False,
        }
    ]

    with patch("app.main.get_session_manager", return_value=manager):
        with patch("app.main.read_sessions", return_value=raw_sessions):
            with patch("app.main._get_now", return_value=now):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/api/today")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["date"], str)
    assert isinstance(payload["sessions"], list)
    assert isinstance(payload["total_minutes"], int)
    assert isinstance(payload["total_display"], str)
    assert len(payload["sessions"]) == 1
    row = payload["sessions"][0]
    assert isinstance(row["start_time"], str)
    assert isinstance(row["end_time"], str)
    assert isinstance(row["duration_minutes"], int)
    assert isinstance(row["completed_4h"], bool)
