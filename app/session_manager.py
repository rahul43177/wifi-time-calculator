"""
Session management module with MongoDB and cumulative daily tracking.

Key Changes from File-Based System:
- Uses MongoDB for atomic operations (no race conditions)
- Cumulative daily tracking (all sessions in one day = one total)
- Grace period support (2-minute reconnection window)
- Network connectivity tracking (pauses during re-auth)
- IST timezone support for Bangalore, India
"""

import asyncio
import logging
from datetime import datetime, UTC
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, field_validator

from app.mongodb_store import MongoDBStore
from app.network_checker import NetworkConnectivityChecker
from app.gamification import gamification_service
from app.config import settings
from app.timezone_utils import now_utc, get_today_date_ist, format_time_ist

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Session state enumeration."""
    IDLE = "idle"
    IN_OFFICE_SESSION = "in_office_session"
    IN_GRACE_PERIOD = "in_grace_period"
    PAUSED_FOR_REAUTH = "paused_for_reauth"
    COMPLETED = "completed"


# ==============================================================================
# Legacy Classes for Backward Compatibility
# These are kept for existing tests but not used in MongoDB implementation
# ==============================================================================

class SessionLog(BaseModel):
    """Validated payload model (legacy - for backward compatibility)."""

    date: str
    ssid: str
    start_time: str
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    completed_4h: bool = False

    @field_validator("date")
    @classmethod
    def _validate_date_format(cls, value: str) -> str:
        """Validate that date follows DD-MM-YYYY format."""
        try:
            datetime.strptime(value, "%d-%m-%Y")
        except ValueError as exc:
            raise ValueError("date must be in DD-MM-YYYY format") from exc
        return value

    @field_validator("start_time", "end_time")
    @classmethod
    def _validate_time_format(cls, value: Optional[str], info: Any) -> Optional[str]:
        """Validate that time fields use HH:MM:SS format."""
        if value is None:
            return value
        try:
            datetime.strptime(value, "%H:%M:%S")
        except ValueError as exc:
            raise ValueError(f"{info.field_name} must be in HH:MM:SS format") from exc
        return value

    @field_validator("ssid")
    @classmethod
    def _validate_ssid(cls, value: str) -> str:
        """Ensure SSID is non-empty after whitespace trimming."""
        if not value.strip():
            raise ValueError("ssid must not be empty")
        return value

    @field_validator("duration_minutes")
    @classmethod
    def _validate_duration(cls, value: Optional[int]) -> Optional[int]:
        """Ensure duration is non-negative when present."""
        if value is not None and value < 0:
            raise ValueError("duration_minutes must be greater than or equal to 0")
        return value


class Session(BaseModel):
    """Backward-compatible in-memory session model (legacy)."""

    date: str
    ssid: str
    start_time: str
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    completed_4h: bool = False


# ==============================================================================
# MongoDB-Based Session Manager
# ==============================================================================


class SessionManager:
    """
    Manages office session state with MongoDB backend.

    Features:
    - Cumulative daily tracking (multiple visits = one daily total)
    - Grace period for brief WiFi disconnects
    - Network connectivity monitoring
    - IST timezone support
    """

    def __init__(
        self,
        mongo_store: MongoDBStore,
        network_checker: Optional[NetworkConnectivityChecker] = None,
    ) -> None:
        """
        Initialize session manager with MongoDB backend.

        Args:
            mongo_store: MongoDB store instance
            network_checker: Network connectivity checker (optional)
        """
        self.store = mongo_store
        self.network_checker = network_checker
        self.state = SessionState.IDLE

        # Grace period tracking
        self.grace_period_minutes = settings.grace_period_minutes
        self._grace_period_task: Optional[asyncio.Task] = None

        # Session timing (in-memory for current session)
        self._current_session_start: Optional[datetime] = None
        self._current_date: Optional[str] = None

        # Target minutes (4 hours + buffer)
        self.target_minutes = (settings.work_duration_hours * 60) + settings.buffer_minutes

        logger.info("SessionManager initialized with MongoDB backend")

    async def start_session(self, ssid: str) -> bool:
        """
        Start or resume office session with cumulative daily tracking.

        This creates/updates today's MongoDB record and starts counting time.
        If multiple sessions happen in one day, they accumulate to one total.

        Args:
            ssid: Connected office Wi-Fi SSID

        Returns:
            True if session started successfully
        """
        try:
            date = get_today_date_ist()  # DD-MM-YYYY in IST
            start_time = now_utc()

            # BUGFIX: If we have an active session from a different day (app never restarted),
            # force-close it before starting today's session
            if self._current_date and self._current_date != date:
                logger.warning(
                    f"Detected stale session from {self._current_date} while starting session for {date}. "
                    "Force-closing old session..."
                )
                old_doc = await self.store.get_daily_status(self._current_date)
                if old_doc:
                    old_total = old_doc.get("total_minutes", 0)
                    await self.end_session(old_total)
                else:
                    # Clear stale in-memory state even if no doc found
                    self._current_date = None
                    self._current_session_start = None
                    self.state = SessionState.IDLE
                logger.info(f"Old session from {self._current_date} force-closed")

            # Get or create today's daily session record
            await self.store.get_or_create_daily_session(
                date=date,
                ssid=ssid,
                target_minutes=self.target_minutes
            )

            # Start/resume the session
            await self.store.start_session(date, ssid, start_time)

            # Cancel any active grace period
            if self._grace_period_task and not self._grace_period_task.done():
                self._grace_period_task.cancel()
                try:
                    await self._grace_period_task
                except asyncio.CancelledError:
                    pass

            await self.store.cancel_grace_period(date)

            # Update in-memory state
            self.state = SessionState.IN_OFFICE_SESSION
            self._current_session_start = start_time
            self._current_date = date

            logger.info(f"Session started/resumed for {date} at {format_time_ist(start_time)} IST")
            return True

        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return False

    async def end_session(self, final_minutes: Optional[int] = None) -> bool:
        """
        End current office session (grace period expired or manual end).

        Args:
            final_minutes: Optional final cumulative total. If None, calculated from current time.

        Returns:
            True if session ended successfully
        """
        try:
            if self._current_date is None:
                logger.warning("end_session ignored: no active session")
                return False

            end_time = now_utc()

            # Calculate final total if not provided
            if final_minutes is None:
                final_minutes = await self._calculate_current_total()

            # End the session in MongoDB
            await self.store.end_session(
                date=self._current_date,
                end_time=end_time,
                final_minutes=final_minutes
            )

            # Clear grace period if any
            if self._grace_period_task and not self._grace_period_task.done():
                self._grace_period_task.cancel()
                try:
                    await self._grace_period_task
                except asyncio.CancelledError:
                    pass

            # Update in-memory state
            self.state = SessionState.IDLE
            self._current_session_start = None
            self._current_date = None

            logger.info(f"Session ended - Total: {final_minutes} minutes")
            return True

        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return False

    async def handle_disconnect(self) -> bool:
        """
        WiFi disconnected - start grace period for potential reconnection.

        If user reconnects within grace period (default 2 minutes),
        session continues without interruption.

        Returns:
            True if grace period started successfully
        """
        try:
            if self._current_date is None:
                logger.debug("handle_disconnect ignored: no active session")
                return False

            grace_start = now_utc()

            # Start grace period in MongoDB
            await self.store.start_grace_period(self._current_date, grace_start)

            # Update in-memory state
            self.state = SessionState.IN_GRACE_PERIOD

            logger.info(f"WiFi disconnected - starting {self.grace_period_minutes}min grace period")

            # Schedule grace period expiry check
            self._grace_period_task = asyncio.create_task(
                self._monitor_grace_period()
            )

            return True

        except Exception as e:
            logger.error(f"Failed to handle disconnect: {e}")
            return False

    async def _monitor_grace_period(self):
        """
        Monitor grace period and end session if it expires.

        This background task waits for the grace period duration,
        then checks if WiFi reconnected. If not, it ends the session.
        """
        try:
            # Wait for grace period duration
            await asyncio.sleep(self.grace_period_minutes * 60)

            if self._current_date is None:
                return

            # Check if still in grace period
            status = await self.store.check_grace_period_status(self._current_date)

            if status.get("active") and status.get("expired"):
                # Grace period expired without reconnection - end session
                final_minutes = await self._calculate_current_total()
                await self.end_session(final_minutes)
                logger.info("Grace period expired - session ended")

        except asyncio.CancelledError:
            logger.debug("Grace period monitoring cancelled (reconnected)")
        except Exception as e:
            logger.error(f"Error monitoring grace period: {e}")

    async def mark_session_completed(self) -> bool:
        """
        Mark 4-hour daily goal as completed.

        Transition: IN_OFFICE_SESSION -> COMPLETED

        Returns:
            True if completion was persisted successfully
        """
        try:
            if self._current_date is None:
                logger.warning("mark_session_completed ignored: no active session")
                return False

            # Mark as completed in MongoDB
            await self.store.mark_completed(self._current_date)

            # Update in-memory state
            self.state = SessionState.COMPLETED

            logger.info(f"Daily goal completed for {self._current_date}")

            # Update gamification streak
            try:
                # Convert date from DD-MM-YYYY to YYYY-MM-DD
                date_parts = self._current_date.split("-")
                iso_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                gamification_service.update_streak(iso_date, target_met=True)
                logger.info(f"Gamification streak updated for {iso_date}")
            except Exception as e:
                logger.warning(f"Failed to update gamification streak: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to mark session completed: {e}")
            return False

    async def check_network_connectivity(self) -> bool:
        """
        Check internet connectivity and pause/resume timer accordingly.

        This detects re-authentication scenarios where WiFi is connected
        but internet access is lost (captive portal).

        Returns:
            True if connectivity check succeeded
        """
        try:
            if self._current_date is None or self.network_checker is None:
                return False

            # Check internet access
            has_internet = await self.network_checker.has_internet_access()

            # Get current MongoDB state
            doc = await self.store.get_daily_status(self._current_date)
            if not doc or not doc.get("is_active"):
                return False

            current_has_access = doc.get("has_network_access", True)

            # Transition: had access → lost access (re-auth needed)
            if current_has_access and not has_internet:
                await self.store.pause_for_reauth(self._current_date, now_utc())
                self.state = SessionState.PAUSED_FOR_REAUTH
                logger.warning("Network connectivity lost - timer paused (re-auth needed)")

            # Transition: lost access → regained access
            elif not current_has_access and has_internet:
                await self.store.resume_after_reauth(self._current_date, now_utc())
                self.state = SessionState.IN_OFFICE_SESSION
                logger.info("Network connectivity restored - timer resumed")

            return True

        except Exception as e:
            logger.error(f"Failed to check network connectivity: {e}")
            return False

    async def recover_session(self, current_ssid: Optional[str]) -> bool:
        """
        Recover active session after app restart.

        Checks MongoDB for today's active session. If found and still
        connected to office WiFi, resumes the session.

        Args:
            current_ssid: Currently connected WiFi SSID (or None)

        Returns:
            True if session was recovered
        """
        try:
            date = get_today_date_ist()

            # Check MongoDB for today's session
            doc = await self.store.get_daily_status(date)

            if not doc:
                logger.debug("recover_session: no session found for today")
                return False

            # Check if session is active
            if not doc.get("is_active"):
                logger.debug("recover_session: today's session is not active")
                return False

            # Check if still connected to the same WiFi and current configured office SSID.
            # This prevents stale sessions from being resumed after OFFICE_WIFI_NAME changes.
            def _normalize_ssid(value: Optional[str]) -> str:
                raw = (value or "").strip().casefold()
                return "".join(ch for ch in raw if ch.isalnum())

            normalized_current_ssid = _normalize_ssid(current_ssid)
            normalized_session_ssid = _normalize_ssid(doc.get("ssid"))
            normalized_configured_ssid = _normalize_ssid(settings.office_wifi_name)
            configured_ssid_is_placeholder = normalized_configured_ssid in {
                "",
                "yourofficewifiname",
            }

            same_session_ssid = normalized_current_ssid == normalized_session_ssid
            on_configured_office_ssid = normalized_current_ssid == normalized_configured_ssid

            if (
                not same_session_ssid
                or (not configured_ssid_is_placeholder and not on_configured_office_ssid)
            ):
                # Disconnected - end the stale session
                # Set current_date temporarily so end_session works
                self._current_date = date
                self._current_session_start = doc.get("current_session_start")

                final_minutes = doc.get("total_minutes", 0)
                await self.end_session(final_minutes)
                logger.info(
                    f"Session recovered: closed stale {doc.get('ssid')} session "
                    f"(current SSID: {current_ssid}, configured office SSID: {settings.office_wifi_name})"
                )
                return False

            # Still connected - resume session
            self._current_date = date
            self._current_session_start = doc.get("current_session_start")

            # Check if in grace period
            if doc.get("grace_period_start"):
                self.state = SessionState.IN_GRACE_PERIOD
                # Restart grace period monitoring
                self._grace_period_task = asyncio.create_task(
                    self._monitor_grace_period()
                )
            elif not doc.get("has_network_access", True):
                self.state = SessionState.PAUSED_FOR_REAUTH
            elif doc.get("completed_4h"):
                self.state = SessionState.COMPLETED
            else:
                self.state = SessionState.IN_OFFICE_SESSION

            logger.info(
                f"Session recovered: resumed {doc.get('ssid')} session "
                f"(total: {doc.get('total_minutes', 0)} minutes)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to recover session: {e}")
            return False

    async def get_current_status(self) -> dict:
        """
        Get current session status for API/dashboard.

        Returns:
            Dictionary with session status information
        """
        try:
            if self._current_date is None:
                return {
                    "connected": False,
                    "session_active": False,
                    "total_minutes": 0,
                    "target_minutes": self.target_minutes,
                    "completed_4h": False,
                    "state": self.state.value
                }

            doc = await self.store.get_daily_status(self._current_date)

            if not doc:
                return {
                    "connected": False,
                    "session_active": False,
                    "total_minutes": 0,
                    "target_minutes": self.target_minutes,
                    "completed_4h": False,
                    "state": self.state.value
                }

            return {
                "connected": doc.get("is_active", False),
                "session_active": doc.get("is_active", False),
                "total_minutes": doc.get("total_minutes", 0),
                "target_minutes": doc.get("target_minutes", self.target_minutes),
                "completed_4h": doc.get("completed_4h", False),
                "has_network_access": doc.get("has_network_access", True),
                "in_grace_period": doc.get("grace_period_start") is not None,
                "sessions_count": doc.get("sessions_count", 0),
                "paused_duration_minutes": doc.get("paused_duration_minutes", 0),
                "state": self.state.value,
                "date": self._current_date
            }

        except Exception as e:
            logger.error(f"Failed to get current status: {e}")
            return {
                "connected": False,
                "session_active": False,
                "total_minutes": 0,
                "target_minutes": self.target_minutes,
                "completed_4h": False,
                "state": "error"
            }

    async def _calculate_current_total(self) -> int:
        """
        Calculate current cumulative total for today.

        Returns:
            Total minutes accumulated today
        """
        try:
            if self._current_date is None:
                return 0

            # Get live status from MongoDB
            doc = await self.store.get_daily_status(self._current_date)
            if not doc:
                return 0

            start_raw = doc.get("current_session_start") or self._current_session_start
            if start_raw is None:
                try:
                    return max(0, int(doc.get("total_minutes", 0)))
                except (TypeError, ValueError):
                    return 0

            start = start_raw if start_raw.tzinfo else start_raw.replace(tzinfo=UTC)
            now = now_utc()
            elapsed_seconds = max(0.0, (now - start).total_seconds())

            try:
                paused_total_minutes = max(0, int(doc.get("paused_duration_minutes", 0)))
            except (TypeError, ValueError):
                paused_total_minutes = 0
            try:
                session_start_paused_minutes = int(
                    doc.get("session_start_paused_minutes", paused_total_minutes)
                )
            except (TypeError, ValueError):
                session_start_paused_minutes = paused_total_minutes
            paused_since_start_minutes = max(
                0,
                paused_total_minutes - session_start_paused_minutes,
            )
            paused_seconds = float(paused_since_start_minutes * 60)

            if not doc.get("has_network_access", True) and doc.get("paused_at"):
                paused_at_raw = doc["paused_at"]
                paused_at = paused_at_raw if paused_at_raw.tzinfo else paused_at_raw.replace(tzinfo=UTC)
                paused_seconds += max(0.0, (now - paused_at).total_seconds())

            effective_session_minutes = int(max(0.0, elapsed_seconds - paused_seconds) // 60)

            try:
                doc_total_minutes = max(0, int(doc.get("total_minutes", 0)))
            except (TypeError, ValueError):
                doc_total_minutes = 0

            baseline_raw = doc.get("session_start_total_minutes")
            if baseline_raw is None:
                session_start_total = max(0, doc_total_minutes - effective_session_minutes)
            else:
                try:
                    session_start_total = max(0, int(baseline_raw))
                except (TypeError, ValueError):
                    session_start_total = max(0, doc_total_minutes - effective_session_minutes)

            return session_start_total + effective_session_minutes

        except Exception as e:
            logger.error(f"Failed to calculate current total: {e}")
            return 0
