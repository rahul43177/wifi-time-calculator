"""
Tests for SessionManager with MongoDB backend.

Tests cumulative daily tracking, grace period, network connectivity,
and session recovery functionality.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock

from app.session_manager import SessionManager, SessionState
from app.mongodb_store import MongoDBStore
from app.network_checker import NetworkConnectivityChecker
from app.config import settings


@pytest_asyncio.fixture
async def mongo_store():
    """Create MongoDB store for testing"""
    store = MongoDBStore(settings.mongodb_uri, settings.mongodb_database)
    await store.connect()
    yield store
    await store.disconnect()


@pytest_asyncio.fixture
async def network_checker():
    """Create network connectivity checker for testing"""
    checker = NetworkConnectivityChecker()
    await checker.initialize()
    yield checker
    await checker.cleanup()


@pytest_asyncio.fixture
async def session_manager(mongo_store, network_checker):
    """Create session manager with MongoDB backend"""
    return SessionManager(mongo_store, network_checker)


@pytest.fixture
def test_date():
    """Generate unique test date for each test"""
    import random
    return f"15-02-2026-TEST-{random.randint(10000, 99999)}"


@pytest.mark.asyncio
async def test_start_session(session_manager, mongo_store, test_date):
    """Test starting a new session"""
    ssid = "TEST_WIFI"

    # Mock get_today_date_ist to return our test date
    import app.session_manager as sm_module
    original_get_date = sm_module.get_today_date_ist
    sm_module.get_today_date_ist = lambda: test_date

    try:
        # Start session
        result = await session_manager.start_session(ssid)
        assert result is True

        # Verify state
        assert session_manager.state == SessionState.IN_OFFICE_SESSION
        assert session_manager._current_date == test_date

        # Verify MongoDB
        doc = await mongo_store.get_daily_status(test_date)
        assert doc is not None
        assert doc["ssid"] == ssid
        assert doc["is_active"] is True
        assert doc["sessions_count"] == 1

        # Clean up
        await mongo_store.db.daily_sessions.delete_one({"date": test_date})

    finally:
        sm_module.get_today_date_ist = original_get_date


@pytest.mark.asyncio
async def test_end_session(session_manager, mongo_store, test_date):
    """Test ending a session"""
    ssid = "TEST_WIFI"

    import app.session_manager as sm_module
    original_get_date = sm_module.get_today_date_ist
    sm_module.get_today_date_ist = lambda: test_date

    try:
        # Start and end session
        await session_manager.start_session(ssid)
        await asyncio.sleep(1)  # Ensure some time passes

        result = await session_manager.end_session()
        assert result is True

        # Verify state
        assert session_manager.state == SessionState.IDLE
        assert session_manager._current_date is None

        # Verify MongoDB
        doc = await mongo_store.get_daily_status(test_date)
        assert doc is not None
        assert doc["is_active"] is False
        assert doc["total_minutes"] >= 0

        # Clean up
        await mongo_store.db.daily_sessions.delete_one({"date": test_date})

    finally:
        sm_module.get_today_date_ist = original_get_date


@pytest.mark.asyncio
async def test_grace_period_start(session_manager, mongo_store, test_date):
    """Test starting grace period on WiFi disconnect"""
    ssid = "TEST_WIFI"

    import app.session_manager as sm_module
    original_get_date = sm_module.get_today_date_ist
    sm_module.get_today_date_ist = lambda: test_date

    try:
        # Start session
        await session_manager.start_session(ssid)

        # Simulate WiFi disconnect
        result = await session_manager.handle_disconnect()
        assert result is True

        # Verify state
        assert session_manager.state == SessionState.IN_GRACE_PERIOD

        # Verify MongoDB
        doc = await mongo_store.get_daily_status(test_date)
        assert doc is not None
        assert doc["grace_period_start"] is not None
        assert doc["is_active"] is True  # Still active during grace period

        # Clean up grace period task
        if session_manager._grace_period_task:
            session_manager._grace_period_task.cancel()
            try:
                await session_manager._grace_period_task
            except asyncio.CancelledError:
                pass

        # Clean up
        await mongo_store.db.daily_sessions.delete_one({"date": test_date})

    finally:
        sm_module.get_today_date_ist = original_get_date


@pytest.mark.asyncio
async def test_grace_period_reconnect(session_manager, mongo_store, test_date):
    """Test reconnecting during grace period cancels it"""
    ssid = "TEST_WIFI"

    import app.session_manager as sm_module
    original_get_date = sm_module.get_today_date_ist
    sm_module.get_today_date_ist = lambda: test_date

    try:
        # Start session
        await session_manager.start_session(ssid)

        # Disconnect
        await session_manager.handle_disconnect()
        assert session_manager.state == SessionState.IN_GRACE_PERIOD

        # Wait a bit
        await asyncio.sleep(0.5)

        # Reconnect (start session again)
        await session_manager.start_session(ssid)

        # Verify grace period is cancelled
        assert session_manager.state == SessionState.IN_OFFICE_SESSION

        # Verify MongoDB
        doc = await mongo_store.get_daily_status(test_date)
        assert doc is not None
        assert doc["grace_period_start"] is None
        assert doc["is_active"] is True

        # Clean up
        await mongo_store.db.daily_sessions.delete_one({"date": test_date})

    finally:
        sm_module.get_today_date_ist = original_get_date


@pytest.mark.asyncio
async def test_cumulative_tracking(session_manager, mongo_store, test_date):
    """Test cumulative daily tracking across multiple sessions"""
    ssid = "TEST_WIFI"

    import app.session_manager as sm_module
    original_get_date = sm_module.get_today_date_ist
    sm_module.get_today_date_ist = lambda: test_date

    try:
        # Session 1: Start and end
        await session_manager.start_session(ssid)
        await asyncio.sleep(1)
        await session_manager.end_session()

        # Check total after first session
        doc = await mongo_store.get_daily_status(test_date)
        first_total = doc["total_minutes"]
        assert first_total >= 0
        assert doc["sessions_count"] == 1

        # Session 2: Start again (should accumulate)
        await session_manager.start_session(ssid)
        await asyncio.sleep(1)
        await session_manager.end_session()

        # Check cumulative total
        doc = await mongo_store.get_daily_status(test_date)
        second_total = doc["total_minutes"]
        assert second_total >= first_total  # Should accumulate
        assert doc["sessions_count"] == 2

        # Clean up
        await mongo_store.db.daily_sessions.delete_one({"date": test_date})

    finally:
        sm_module.get_today_date_ist = original_get_date


@pytest.mark.asyncio
async def test_mark_session_completed(session_manager, mongo_store, test_date):
    """Test marking 4-hour goal as completed"""
    ssid = "TEST_WIFI"

    import app.session_manager as sm_module
    original_get_date = sm_module.get_today_date_ist
    sm_module.get_today_date_ist = lambda: test_date

    try:
        # Start session
        await session_manager.start_session(ssid)

        # Mark as completed
        result = await session_manager.mark_session_completed()
        assert result is True

        # Verify state
        assert session_manager.state == SessionState.COMPLETED

        # Verify MongoDB
        doc = await mongo_store.get_daily_status(test_date)
        assert doc is not None
        assert doc["completed_4h"] is True

        # Clean up
        await mongo_store.db.daily_sessions.delete_one({"date": test_date})

    finally:
        sm_module.get_today_date_ist = original_get_date


@pytest.mark.asyncio
async def test_recover_session_active(session_manager, mongo_store, test_date):
    """Test recovering an active session after restart"""
    ssid = "TEST_WIFI"

    import app.session_manager as sm_module
    original_get_date = sm_module.get_today_date_ist
    original_office_wifi_name = sm_module.settings.office_wifi_name
    sm_module.get_today_date_ist = lambda: test_date
    sm_module.settings.office_wifi_name = ssid

    try:
        # Create active session in MongoDB
        await mongo_store.get_or_create_daily_session(test_date, ssid, 250)
        await mongo_store.start_session(test_date, ssid, datetime.now(UTC))

        # Create new session manager (simulating restart)
        new_manager = SessionManager(mongo_store)

        # Try to recover
        result = await new_manager.recover_session(ssid)
        assert result is True

        # Verify state
        assert new_manager.state == SessionState.IN_OFFICE_SESSION
        assert new_manager._current_date == test_date

        # Clean up
        await mongo_store.db.daily_sessions.delete_one({"date": test_date})

    finally:
        sm_module.get_today_date_ist = original_get_date
        sm_module.settings.office_wifi_name = original_office_wifi_name


@pytest.mark.asyncio
async def test_recover_session_disconnected(session_manager, mongo_store, test_date):
    """Test recovering when disconnected from WiFi"""
    ssid = "TEST_WIFI"

    import app.session_manager as sm_module
    original_get_date = sm_module.get_today_date_ist
    sm_module.get_today_date_ist = lambda: test_date

    try:
        # Create active session in MongoDB
        await mongo_store.get_or_create_daily_session(test_date, ssid, 250)
        await mongo_store.start_session(test_date, ssid, datetime.now(UTC))

        # Create new session manager (simulating restart)
        new_manager = SessionManager(mongo_store)

        # Try to recover with different SSID (disconnected)
        result = await new_manager.recover_session("DIFFERENT_WIFI")
        assert result is False

        # Verify session was ended
        doc = await mongo_store.get_daily_status(test_date)
        assert doc is not None
        assert doc["is_active"] is False

        # Clean up
        await mongo_store.db.daily_sessions.delete_one({"date": test_date})

    finally:
        sm_module.get_today_date_ist = original_get_date


@pytest.mark.asyncio
async def test_get_current_status(session_manager, mongo_store, test_date):
    """Test getting current session status"""
    ssid = "TEST_WIFI"

    import app.session_manager as sm_module
    original_get_date = sm_module.get_today_date_ist
    sm_module.get_today_date_ist = lambda: test_date

    try:
        # Start session
        await session_manager.start_session(ssid)

        # Get status
        status = await session_manager.get_current_status()

        # Verify status
        assert status["connected"] is True
        assert status["session_active"] is True
        assert status["total_minutes"] >= 0
        assert status["completed_4h"] is False
        assert status["state"] == SessionState.IN_OFFICE_SESSION.value
        assert status["date"] == test_date

        # Clean up
        await mongo_store.db.daily_sessions.delete_one({"date": test_date})

    finally:
        sm_module.get_today_date_ist = original_get_date


@pytest.mark.asyncio
async def test_network_connectivity_pause_resume(session_manager, mongo_store, test_date):
    """Test network connectivity monitoring (pause/resume)"""
    ssid = "TEST_WIFI"

    import app.session_manager as sm_module
    original_get_date = sm_module.get_today_date_ist
    sm_module.get_today_date_ist = lambda: test_date

    # Mock network checker
    mock_checker = AsyncMock()
    session_manager.network_checker = mock_checker

    try:
        # Start session
        await session_manager.start_session(ssid)

        # Simulate network loss (WiFi connected but no internet)
        mock_checker.has_internet_access.return_value = False
        await session_manager.check_network_connectivity()

        # Verify paused
        assert session_manager.state == SessionState.PAUSED_FOR_REAUTH

        # Verify MongoDB
        doc = await mongo_store.get_daily_status(test_date)
        assert doc is not None
        assert doc["has_network_access"] is False

        # Simulate network restored
        mock_checker.has_internet_access.return_value = True
        await session_manager.check_network_connectivity()

        # Verify resumed
        assert session_manager.state == SessionState.IN_OFFICE_SESSION

        # Verify MongoDB
        doc = await mongo_store.get_daily_status(test_date)
        assert doc is not None
        assert doc["has_network_access"] is True

        # Clean up
        await mongo_store.db.daily_sessions.delete_one({"date": test_date})

    finally:
        sm_module.get_today_date_ist = original_get_date


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
