"""
Tests for API Endpoints - Personal Leave Time and Completion Status.

Covers:
- /api/status endpoint includes completed_4h and personal_leave_time_ist
- /api/today endpoint includes personal_leave_time_ist
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_api_status_includes_completed_4h() -> None:
    """The /api/status endpoint must return the completed_4h boolean."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert "completed_4h" in data
    assert isinstance(data["completed_4h"], bool)


@pytest.mark.asyncio
async def test_api_status_includes_personal_leave_time_field() -> None:
    """/api/status should always include personal_leave_time_ist (nullable)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert "personal_leave_time_ist" in data
    assert data["personal_leave_time_ist"] is None or isinstance(
        data["personal_leave_time_ist"], str
    )


@pytest.mark.asyncio
async def test_api_today_includes_personal_leave_time_field() -> None:
    """/api/today should always include personal_leave_time_ist (nullable)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/today")

    assert response.status_code == 200
    data = response.json()
    assert "personal_leave_time_ist" in data
    assert data["personal_leave_time_ist"] is None or isinstance(
        data["personal_leave_time_ist"], str
    )
