"""
Comprehensive tests for MongoDB implementation.
This verifies the MongoDBStore and NetworkChecker are working correctly.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, UTC
from app.mongodb_store import MongoDBStore
from app.network_checker import NetworkConnectivityChecker
from app.config import settings


@pytest.mark.asyncio
async def test_mongodb_connection():
    """Test basic MongoDB connection"""
    store = MongoDBStore(settings.mongodb_uri, settings.mongodb_database)

    await store.connect()
    assert store.client is not None
    assert store.db is not None

    await store.disconnect()
    print("✅ MongoDB connection test passed")


@pytest.mark.asyncio
async def test_create_daily_session():
    """Test creating a new daily session"""
    store = MongoDBStore(settings.mongodb_uri, settings.mongodb_database)
    await store.connect()

    try:
        date = "15-02-2026-TEST"
        ssid = "TEST_WIFI"
        target_minutes = 250

        # Create session
        doc = await store.get_or_create_daily_session(date, ssid, target_minutes)

        assert doc is not None
        assert doc["date"] == date
        assert doc["ssid"] == ssid
        assert doc["total_minutes"] == 0
        assert doc["completed_4h"] is False
        assert doc["is_active"] is False

        # Clean up
        await store.db.daily_sessions.delete_one({"date": date})
        print("✅ Create daily session test passed")

    finally:
        await store.disconnect()


@pytest.mark.asyncio
async def test_start_and_end_session():
    """Test starting and ending a session"""
    store = MongoDBStore(settings.mongodb_uri, settings.mongodb_database)
    await store.connect()

    try:
        date = "15-02-2026-TEST2"
        ssid = "TEST_WIFI"

        # Create session
        await store.get_or_create_daily_session(date, ssid, 250)

        # Start session
        start_time = datetime.now(UTC)
        await store.start_session(date, ssid, start_time)

        doc = await store.get_daily_status(date)
        assert doc["is_active"] is True
        assert doc["current_session_start"] is not None
        assert doc["sessions_count"] == 1

        # Update elapsed time
        await asyncio.sleep(1)
        await store.update_elapsed_time(date, 5)

        doc = await store.get_daily_status(date)
        assert doc["total_minutes"] == 5

        # End session
        end_time = datetime.now(UTC)
        await store.end_session(date, end_time, 10)

        doc = await store.get_daily_status(date)
        assert doc["is_active"] is False
        assert doc["total_minutes"] == 10

        # Clean up
        await store.db.daily_sessions.delete_one({"date": date})
        print("✅ Start and end session test passed")

    finally:
        await store.disconnect()


@pytest.mark.asyncio
async def test_grace_period():
    """Test grace period functionality"""
    store = MongoDBStore(settings.mongodb_uri, settings.mongodb_database)
    await store.connect()

    try:
        date = "15-02-2026-TEST3"
        ssid = "TEST_WIFI"

        # Create and start session
        await store.get_or_create_daily_session(date, ssid, 250)
        await store.start_session(date, ssid, datetime.now(UTC))

        # Start grace period
        grace_start = datetime.now(UTC)
        await store.start_grace_period(date, grace_start)

        # Check status immediately
        status = await store.check_grace_period_status(date)
        assert status["active"] is True
        assert status["expired"] is False

        # Wait and check if expired
        await asyncio.sleep(1)
        status = await store.check_grace_period_status(date)
        assert status["elapsed_minutes"] > 0

        # Cancel grace period
        await store.cancel_grace_period(date)

        status = await store.check_grace_period_status(date)
        assert status["active"] is False

        # Clean up
        await store.db.daily_sessions.delete_one({"date": date})
        print("✅ Grace period test passed")

    finally:
        await store.disconnect()


@pytest.mark.asyncio
async def test_network_connectivity_pause_resume():
    """Test network connectivity pause/resume"""
    store = MongoDBStore(settings.mongodb_uri, settings.mongodb_database)
    await store.connect()

    try:
        date = "15-02-2026-TEST4"
        ssid = "TEST_WIFI"

        # Create and start session
        await store.get_or_create_daily_session(date, ssid, 250)
        await store.start_session(date, ssid, datetime.now(UTC))

        # Pause for re-auth
        pause_time = datetime.now(UTC)
        await store.pause_for_reauth(date, pause_time)

        doc = await store.get_daily_status(date)
        assert doc["has_network_access"] is False
        assert doc["paused_at"] is not None

        # Wait a bit
        await asyncio.sleep(2)

        # Resume after re-auth
        resume_time = datetime.now(UTC)
        result = await store.resume_after_reauth(date, resume_time)

        assert result is not None

        doc = await store.get_daily_status(date)
        assert doc["has_network_access"] is True
        assert doc["paused_at"] is None
        assert doc["paused_duration_minutes"] >= 0

        # Clean up
        await store.db.daily_sessions.delete_one({"date": date})
        print("✅ Network connectivity pause/resume test passed")

    finally:
        await store.disconnect()


@pytest.mark.asyncio
async def test_mark_completed():
    """Test marking 4-hour goal as completed"""
    store = MongoDBStore(settings.mongodb_uri, settings.mongodb_database)
    await store.connect()

    try:
        date = "15-02-2026-TEST5"
        ssid = "TEST_WIFI"

        # Create session
        await store.get_or_create_daily_session(date, ssid, 250)

        doc = await store.get_daily_status(date)
        assert doc["completed_4h"] is False

        # Mark completed
        await store.mark_completed(date)

        doc = await store.get_daily_status(date)
        assert doc["completed_4h"] is True

        # Clean up
        await store.db.daily_sessions.delete_one({"date": date})
        print("✅ Mark completed test passed")

    finally:
        await store.disconnect()


@pytest.mark.asyncio
async def test_network_checker_internet_access():
    """Test network connectivity checker"""
    checker = NetworkConnectivityChecker()
    await checker.initialize()

    try:
        # This should return True if internet is available
        has_access = await checker.has_internet_access()
        print(f"Internet access: {has_access}")

        # Should be bool
        assert isinstance(has_access, bool)
        print("✅ Network checker test passed")

    finally:
        await checker.cleanup()


@pytest.mark.asyncio
async def test_cumulative_tracking_scenario():
    """
    Test realistic scenario: Multiple sessions in one day should accumulate.
    This is the key requirement for the new system.
    """
    store = MongoDBStore(settings.mongodb_uri, settings.mongodb_database)
    await store.connect()

    try:
        date = "15-02-2026-TEST6"
        ssid = "OFFICE_WIFI"

        # Create daily session
        await store.get_or_create_daily_session(date, ssid, 250)

        # Session 1: Morning (2 hours = 120 minutes)
        await store.start_session(date, ssid, datetime.now(UTC))
        await store.update_elapsed_time(date, 120)
        await store.end_session(date, datetime.now(UTC), 120)

        doc = await store.get_daily_status(date)
        assert doc["total_minutes"] == 120
        assert doc["sessions_count"] == 1
        assert doc["is_active"] is False

        # Session 2: Afternoon (2 more hours = 120 minutes)
        # When we start again, it should be cumulative
        await store.start_session(date, ssid, datetime.now(UTC))

        # Simulate timer updating with cumulative total
        await store.update_elapsed_time(date, 240)  # 120 + 120

        doc = await store.get_daily_status(date)
        assert doc["total_minutes"] == 240
        assert doc["sessions_count"] == 2
        assert doc["is_active"] is True

        # Check if 4h completed (240 minutes)
        if doc["total_minutes"] >= 240:
            await store.mark_completed(date)

        doc = await store.get_daily_status(date)
        assert doc["completed_4h"] is True

        # Clean up
        await store.db.daily_sessions.delete_one({"date": date})
        print("✅ Cumulative tracking scenario test passed")

    finally:
        await store.disconnect()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING MONGODB IMPLEMENTATION")
    print("="*60 + "\n")

    # Run all tests
    asyncio.run(test_mongodb_connection())
    asyncio.run(test_create_daily_session())
    asyncio.run(test_start_and_end_session())
    asyncio.run(test_grace_period())
    asyncio.run(test_network_connectivity_pause_resume())
    asyncio.run(test_mark_completed())
    asyncio.run(test_network_checker_internet_access())
    asyncio.run(test_cumulative_tracking_scenario())

    print("\n" + "="*60)
    print("ALL TESTS PASSED ✅")
    print("="*60 + "\n")
