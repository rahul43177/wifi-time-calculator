"""
Tests for Phase 5.4: Monthly Analytics UI View.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_dashboard_includes_monthly_ui_elements() -> None:
    """Dashboard HTML should include Monthly tab and its required components."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    body = response.text
    
    # Navigation (Task 7.9: tabs are now buttons for accessibility)
    assert 'data-tab="monthly"' in body and 'Monthly</button>' in body
    
    # Section
    assert 'id="tab-monthly"' in body
    assert 'Monthly Analytics' in body
    
    # Selectors
    assert 'id="prev-month"' in body
    assert 'id="next-month"' in body
    assert 'id="current-month-label"' in body
    
    # Chart
    assert 'id="monthly-chart"' in body
    
    # Stats
    assert 'id="monthly-total-hours"' in body
    assert 'id="monthly-total-days"' in body
    assert 'id="monthly-avg-hours"' in body
    
    # Table
    assert 'id="monthly-table"' in body
    assert 'id="monthly-table-body"' in body


@pytest.mark.asyncio
async def test_js_contains_monthly_logic() -> None:
    """app.js should contain the logic for monthly analytics."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/static/app.js")

    assert response.status_code == 200
    body = response.text
    
    assert "function renderMonthlyTable()" in body
    assert "function renderMonthlyChart()" in body
    assert "function syncMonthly()" in body
    assert "function addMonths(" in body
    assert "dom.tabMonthly" in body
    assert "state.selectedMonth" in body
    assert "/api/monthly" in body
