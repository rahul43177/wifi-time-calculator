"""
Test that is_active is set to false immediately when grace period starts.

This is a critical reliability fix: if grace period monitoring fails,
the session should still be marked inactive.
"""

from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.mongodb_store import MongoDBStore


@pytest.mark.asyncio
async def test_start_grace_period_marks_session_inactive():
    """
    When grace period starts, is_active should be set to False immediately.
    This ensures the session is marked inactive even if grace period monitoring fails.
    """
    # Mock MongoDB
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.daily_sessions = mock_collection
    
    # Mock the update_one call
    mock_result = MagicMock()
    mock_result.modified_count = 1
    mock_collection.update_one = AsyncMock(return_value=mock_result)
    
    store = MongoDBStore("mongodb://test", "test_db")
    store.db = mock_db
    
    # Start grace period
    grace_start = datetime(2026, 2, 27, 10, 0, 0, tzinfo=UTC)
    await store.start_grace_period("27-02-2026", grace_start)
    
    # Verify is_active was set to False
    mock_collection.update_one.assert_called_once()
    call_args = mock_collection.update_one.call_args
    
    # Check the update query
    update_query = call_args[0][1]["$set"]
    assert update_query["is_active"] is False, "is_active should be set to False immediately"
    assert update_query["grace_period_start"] == grace_start
    print("✓ is_active set to False when grace period starts")


@pytest.mark.asyncio
async def test_start_session_reactivates_during_grace_period():
    """
    When reconnecting during grace period, is_active should be set back to True.
    """
    # Mock MongoDB
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.daily_sessions = mock_collection
    
    # Mock the update_one call
    mock_result = MagicMock()
    mock_result.modified_count = 1
    mock_collection.update_one = AsyncMock(return_value=mock_result)
    
    store = MongoDBStore("mongodb://test", "test_db")
    store.db = mock_db
    
    # Start session (reconnecting)
    reconnect_time = datetime(2026, 2, 27, 10, 1, 30, tzinfo=UTC)
    await store.start_session("27-02-2026", "TestWiFi", reconnect_time)
    
    # Verify is_active was set to True and grace_period cleared
    mock_collection.update_one.assert_called_once()
    call_args = mock_collection.update_one.call_args
    
    # Check the update pipeline (it's a list of update stages)
    update_pipeline = call_args[0][1]
    first_stage = update_pipeline[0]["$set"]
    
    assert first_stage["is_active"] is True, "is_active should be set to True when reconnecting"
    assert first_stage["grace_period_start"] is None, "grace_period_start should be cleared"
    print("✓ is_active set to True when reconnecting during grace period")


if __name__ == "__main__":
    import asyncio
    
    print("\n" + "="*60)
    print("TESTING GRACE PERIOD is_active FIX")
    print("="*60 + "\n")
    
    print("Test 1: is_active=false when grace period starts")
    asyncio.run(test_start_grace_period_marks_session_inactive())
    
    print("\nTest 2: is_active=true when reconnecting")
    asyncio.run(test_start_session_reactivates_during_grace_period())
    
    print("\n" + "="*60)
    print("✅ ALL GRACE PERIOD TESTS PASSED!")
    print("="*60)
    print("\nBehavior:")
    print("  Disconnect → is_active=false (IMMEDIATELY)")  
    print("  Reconnect  → is_active=true (grace period cleared)")
    print("\n✨ Session reliability guaranteed! ✨\n")
