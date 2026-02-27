"""
Test that stale sessions from previous days are properly closed.

This tests the fix for the bug where sessions from previous days
continued running when the app never restarted.
"""

from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.session_manager import SessionManager


@pytest.mark.asyncio
async def test_start_session_closes_stale_session_from_previous_day():
    """
    When starting a session TODAY, if there's an active session from YESTERDAY
    in memory (_current_date), it should be force-closed first.
    """
    mock_store = AsyncMock()
    mock_network_checker = MagicMock()
    
    manager = SessionManager(mock_store, mock_network_checker)
    
    # Simulate having an active session from yesterday in memory
    manager._current_date = "26-02-2026"  # Yesterday
    manager._current_session_start = datetime(2026, 2, 26, 3, 0, 0, tzinfo=UTC)
    
    # Mock the old session data
    mock_store.get_daily_status.return_value = {
        "date": "26-02-2026",
        "total_minutes": 300,
        "is_active": True
    }
    
    mock_store.get_or_create_daily_session.return_value = {
        "date": "27-02-2026",
        "total_minutes": 0
    }
    
    mock_store.start_session.return_value = MagicMock(modified_count=1)
    mock_store.end_session.return_value = True
    mock_store.cancel_grace_period.return_value = True
    
    # Mock the current date to be TODAY (27-02-2026)
    with patch("app.session_manager.get_today_date_ist", return_value="27-02-2026"):
        with patch("app.session_manager.now_utc", return_value=datetime(2026, 2, 27, 3, 0, 0, tzinfo=UTC)):
            # Start session TODAY - should force-close yesterday's session first
            result = await manager.start_session("TestOfficeWiFi")
    
    # Verify the stale session was force-closed
    assert result is True
    mock_store.end_session.assert_called_once()
    
    # Verify the end_session was called with yesterday's date
    call_kwargs = mock_store.end_session.call_args.kwargs
    assert call_kwargs["date"] == "26-02-2026"
    assert call_kwargs["final_minutes"] == 300
    
    # Verify today's session was started
    mock_store.get_or_create_daily_session.assert_called_once_with(
        date="27-02-2026",
        ssid="TestOfficeWiFi",
        target_minutes=manager.target_minutes
    )
    
    mock_store.start_session.assert_called_once()
    
    # Verify state is updated to today
    assert manager._current_date == "27-02-2026"
    

@pytest.mark.asyncio
async def test_start_session_no_closure_for_same_day():
    """
    When starting a session and _current_date is already TODAY,
    should NOT try to close anything.
    """
    mock_store = AsyncMock()
    mock_network_checker = MagicMock()
    
    manager = SessionManager(mock_store, mock_network_checker)
    
    # Simulate having an active session from TODAY in memory
    manager._current_date = "27-02-2026"  # Today
    manager._current_session_start = datetime(2026, 2, 27, 3, 0, 0, tzinfo=UTC)
    
    mock_store.get_or_create_daily_session.return_value = {
        "date": "27-02-2026",
        "total_minutes": 100
    }
    
    mock_store.start_session.return_value = MagicMock(modified_count=1)
    mock_store.cancel_grace_period.return_value = True
    
    # Mock the current date to be TODAY (27-02-2026)
    with patch("app.session_manager.get_today_date_ist", return_value="27-02-2026"):
        with patch("app.session_manager.now_utc", return_value=datetime(2026, 2, 27, 3, 30, 0, tzinfo=UTC)):
            # Start/resume session TODAY - should NOT call end_session
            result = await manager.start_session("TestOfficeWiFi")
    
    # Verify NO stale session closure happened
    assert result is True
    mock_store.end_session.assert_not_called()
    mock_store.get_daily_status.assert_not_called()
    
    # Verify today's session was resumed
    mock_store.start_session.assert_called_once()


if __name__ == "__main__":
    import asyncio
    
    print("\n" + "="*60)
    print("TESTING STALE SESSION FIX")
    print("="*60 + "\n")
    
    print("Test 1: Force-close stale session from previous day")
    asyncio.run(test_start_session_closes_stale_session_from_previous_day())
    print("✓ Test passed\n")
    
    print("Test 2: No closure for same-day session")
    asyncio.run(test_start_session_no_closure_for_same_day())
    print("✓ Test passed\n")
    
    print("="*60)
    print("✅ ALL STALE SESSION TESTS PASSED!")
    print("="*60)
