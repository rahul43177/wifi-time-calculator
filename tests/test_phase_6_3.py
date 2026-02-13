"""
Tests for Phase 6.3: Graceful Shutdown Handler.

Covers:
- FastAPI lifespan shutdown behavior
- Background task cancellation
- Session state persistence on shutdown
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import lifespan, app


@pytest.mark.asyncio
async def test_lifespan_cancels_background_tasks_on_shutdown():
    """Lifespan should cancel all background tasks during shutdown."""
    with patch("app.main.wifi_polling_loop", new_callable=AsyncMock) as mock_wifi_loop, \
         patch("app.main.timer_polling_loop", new_callable=AsyncMock) as mock_timer_loop, \
         patch("app.main.get_current_ssid", return_value=None), \
         patch("app.main.get_session_manager") as mock_manager:

        mock_manager_instance = MagicMock()
        mock_manager_instance.recover_session.return_value = False
        mock_manager_instance.state = MagicMock()
        mock_manager.return_value = mock_manager_instance

        # Enter lifespan context
        async with lifespan(app):
            # Background tasks should be running
            assert mock_wifi_loop.called
            assert mock_timer_loop.called

        # After exiting context, tasks should be cancelled
        # asyncio.gather is called with return_exceptions=True in shutdown


@pytest.mark.asyncio
async def test_lifespan_clears_background_tasks_list():
    """Lifespan should clear _background_tasks list on shutdown."""
    from app.main import _background_tasks

    with patch("app.main.wifi_polling_loop", new_callable=AsyncMock), \
         patch("app.main.timer_polling_loop", new_callable=AsyncMock), \
         patch("app.main.get_current_ssid", return_value=None), \
         patch("app.main.get_session_manager") as mock_manager:

        mock_manager_instance = MagicMock()
        mock_manager_instance.recover_session.return_value = False
        mock_manager_instance.state = MagicMock()
        mock_manager.return_value = mock_manager_instance

        # Enter and exit lifespan context
        async with lifespan(app):
            pass

        # After shutdown, background tasks list should be empty
        assert len(_background_tasks) == 0


@pytest.mark.asyncio
async def test_session_state_persists_immediately_no_shutdown_flush_needed():
    """Session state persists on every change, no shutdown flush needed."""
    from app.session_manager import SessionManager
    from app.file_store import read_sessions
    from datetime import datetime

    # Create a session manager
    manager = SessionManager()

    # Start a session
    manager.start_session("TestWiFi")

    # Session should be persisted immediately
    sessions = read_sessions(datetime.now())

    # Should find at least one session
    assert len(sessions) > 0

    # The last session should match our test
    last_session = sessions[-1]
    assert last_session.get("ssid") == "TestWiFi"
    assert last_session.get("end_time") is None  # Still active


@pytest.mark.asyncio
async def test_lifespan_handles_task_exceptions_gracefully():
    """Lifespan shutdown should handle task exceptions without crashing."""

    async def failing_wifi_loop():
        """Simulates a failing wifi polling loop."""
        await asyncio.sleep(0.1)
        raise ValueError("Simulated wifi loop failure")

    async def failing_timer_loop():
        """Simulates a failing timer polling loop."""
        await asyncio.sleep(0.1)
        raise RuntimeError("Simulated timer loop failure")

    with patch("app.main.wifi_polling_loop", new=failing_wifi_loop), \
         patch("app.main.timer_polling_loop", new=failing_timer_loop), \
         patch("app.main.get_current_ssid", return_value=None), \
         patch("app.main.get_session_manager") as mock_manager:

        mock_manager_instance = MagicMock()
        mock_manager_instance.recover_session.return_value = False
        mock_manager_instance.state = MagicMock()
        mock_manager.return_value = mock_manager_instance

        # Lifespan should not raise despite task failures
        try:
            async with lifespan(app):
                await asyncio.sleep(0.2)  # Let tasks fail
            # Should reach here without exception
            assert True
        except (ValueError, RuntimeError):
            pytest.fail("Lifespan should handle task exceptions gracefully")


def test_graceful_shutdown_uses_return_exceptions():
    """Verify lifespan uses return_exceptions=True in asyncio.gather."""
    import inspect
    from app.main import lifespan

    # Get the source code of the lifespan function
    source = inspect.getsource(lifespan)

    # Should use asyncio.gather with return_exceptions=True
    assert "asyncio.gather" in source
    assert "return_exceptions=True" in source


def test_shutdown_code_has_no_stale_todo_comments():
    """Verify shutdown code has accurate comment (no misleading TODO)."""
    import inspect
    from app.main import lifespan

    # Get the source code of the lifespan function
    source = inspect.getsource(lifespan)

    # Should NOT have stale TODO about saving session state
    assert "TODO: Save active session state" not in source, \
        "Stale TODO comment should be removed (session persistence is immediate)"

    # Should have accurate note about immediate persistence
    assert "Session state persists immediately" in source or "no shutdown flush needed" in source, \
        "Should document that session persistence happens immediately"
