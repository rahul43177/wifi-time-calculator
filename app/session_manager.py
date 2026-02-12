"""
Session management module.
Handles session state machine and session lifecycle.
"""

import logging
import threading
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ValidationError, field_validator

from app.file_store import append_session, read_sessions

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Session state enumeration."""
    IDLE = "idle"
    IN_OFFICE_SESSION = "in_office_session"
    COMPLETED = "completed"


class SessionLog(BaseModel):
    """Validated payload model used for persistence."""

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
    """Backward-compatible in-memory session model."""

    date: str
    ssid: str
    start_time: str
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    completed_4h: bool = False


class SessionManager:
    """
    Manages office session state and lifecycle.
    """

    def __init__(
        self,
        persist_func: Optional[Callable[[dict[str, Any]], bool]] = None,
        now_provider: Optional[Callable[[], datetime]] = None,
        read_sessions_func: Optional[Callable[[], list[dict[str, Any]]]] = None,
    ) -> None:
        """
        Initialize a new session manager.

        Args:
            persist_func: Optional persistence function. Defaults to file_store.append_session.
            now_provider: Optional current-time provider for deterministic testing.
            read_sessions_func: Optional function to read today's sessions. Defaults to file_store.read_sessions.
        """
        self.state = SessionState.IDLE
        self.active_session: Optional[Session] = None
        self._persist_func = persist_func or append_session
        self._now_provider = now_provider or datetime.now
        self._read_sessions_func = read_sessions_func or read_sessions
        self._lock = threading.Lock()
        logger.info("SessionManager initialized")

    def start_session(self, ssid: str) -> bool:
        """
        Start a new office session.

        Transition:
            IDLE -> IN_OFFICE_SESSION

        Args:
            ssid: Connected office Wi-Fi SSID.

        Returns:
            True if session started and persisted successfully, False otherwise.
        """
        with self._lock:
            if self.state != SessionState.IDLE or self.active_session is not None:
                logger.warning("start_session ignored: session already active")
                return False

            now = self._now_provider()
            session = Session(
                date=now.strftime("%d-%m-%Y"),
                ssid=ssid,
                start_time=now.strftime("%H:%M:%S"),
            )

            if not self._persist_state(session):
                logger.error("start_session failed: could not persist session start")
                return False

            self.active_session = session
            self.state = SessionState.IN_OFFICE_SESSION
            logger.info("Session started for SSID: %s", ssid)
            return True

    def end_session(self) -> bool:
        """
        End the current office session.

        Transition:
            IN_OFFICE_SESSION/COMPLETED -> IDLE

        Returns:
            True if session ended and persisted successfully, False otherwise.
        """
        with self._lock:
            if self.active_session is None:
                logger.warning("end_session ignored: no active session")
                return False

            now = self._now_provider()
            updated_session = self.active_session.model_copy(
                update={
                    "end_time": now.strftime("%H:%M:%S"),
                    "duration_minutes": self._calculate_duration_minutes(
                        self.active_session, now
                    ),
                }
            )

            if not self._persist_state(updated_session):
                logger.error("end_session failed: could not persist session end")
                return False

            self.active_session = None
            self.state = SessionState.IDLE
            logger.info("Session ended")
            return True

    def mark_session_completed(self) -> bool:
        """
        Mark the active session as 4-hour complete.

        Transition:
            IN_OFFICE_SESSION -> COMPLETED

        Returns:
            True if completion was persisted and state updated, False otherwise.
        """
        with self._lock:
            if self.state != SessionState.IN_OFFICE_SESSION or self.active_session is None:
                logger.warning("mark_session_completed ignored: no in-progress session")
                return False

            now = self._now_provider()
            updated_session = self.active_session.model_copy(
                update={
                    "completed_4h": True,
                    "duration_minutes": self._calculate_duration_minutes(
                        self.active_session, now
                    ),
                }
            )

            if not self._persist_state(updated_session):
                logger.error("mark_session_completed failed: could not persist completion")
                return False

            self.active_session = updated_session
            self.state = SessionState.COMPLETED
            logger.info("Session marked as completed")
            return True

    def recover_session(self, current_ssid: str | None) -> bool:
        """
        Recover an incomplete session from today's log after app restart.

        Reads today's log file, looks for the last session entry without an
        end_time (incomplete). If found and the laptop is still connected to
        the same office Wi-Fi, the session is resumed in-memory. If found but
        disconnected, the incomplete session is closed with an end record.

        Args:
            current_ssid: The Wi-Fi SSID currently connected, or None.

        Returns:
            True if a session was recovered (resumed), False otherwise.
        """
        with self._lock:
            if self.state != SessionState.IDLE or self.active_session is not None:
                logger.debug("recover_session skipped: session already active")
                return False

            try:
                sessions = self._read_sessions_func()
            except Exception:
                logger.exception("recover_session: failed to read today's sessions")
                return False

            if not sessions:
                logger.debug("recover_session: no sessions found for today")
                return False

            # Find the last incomplete session (no end_time)
            last_incomplete: dict[str, Any] | None = None
            for entry in reversed(sessions):
                if entry.get("end_time") is None:
                    last_incomplete = entry
                    break

            if last_incomplete is None:
                logger.debug("recover_session: no incomplete session found")
                return False

            # Try to reconstruct the Session object
            try:
                validated_entry = SessionLog.model_validate(
                    {
                        "date": last_incomplete["date"],
                        "ssid": last_incomplete["ssid"],
                        "start_time": last_incomplete["start_time"],
                        "end_time": last_incomplete.get("end_time"),
                        "duration_minutes": last_incomplete.get("duration_minutes"),
                        "completed_4h": last_incomplete.get("completed_4h", False),
                    }
                ).model_dump()
                incomplete_session = Session(
                    date=validated_entry["date"],
                    ssid=validated_entry["ssid"],
                    start_time=validated_entry["start_time"],
                    end_time=validated_entry.get("end_time"),
                    duration_minutes=validated_entry.get("duration_minutes"),
                    completed_4h=validated_entry.get("completed_4h", False),
                )
            except (KeyError, ValueError, ValidationError) as e:
                logger.warning("recover_session: malformed session entry, skipping: %s", e)
                return False

            # Decision: resume or close
            if current_ssid == incomplete_session.ssid:
                # Still connected to the same office Wi-Fi → resume
                self.active_session = incomplete_session
                self.state = SessionState.IN_OFFICE_SESSION
                logger.info(
                    "Session recovered: resumed %s session started at %s",
                    incomplete_session.ssid,
                    incomplete_session.start_time,
                )
                return True
            else:
                # Disconnected → close the stale session
                now = self._now_provider()
                closed_session = incomplete_session.model_copy(
                    update={
                        "end_time": now.strftime("%H:%M:%S"),
                        "duration_minutes": self._calculate_duration_minutes(
                            incomplete_session, now
                        ),
                    }
                )
                if not self._persist_state(closed_session):
                    logger.warning(
                        "recover_session: failed to persist stale session close"
                    )
                logger.info(
                    "Session recovered: closed stale %s session (started %s, "
                    "current SSID: %s)",
                    incomplete_session.ssid,
                    incomplete_session.start_time,
                    current_ssid,
                )
                return False

    def _persist_state(self, session: Session) -> bool:
        """
        Persist session state to file storage.

        Args:
            session: Session snapshot to persist.

        Returns:
            True when persistence succeeds, False otherwise.
        """
        try:
            validated_payload = SessionLog.model_validate(session.model_dump()).model_dump()
            return self._persist_func(validated_payload)
        except ValidationError as exc:
            logger.error("Session validation failed: %s", self._format_validation_error(exc))
            return False
        except Exception:
            logger.exception("Unexpected error while persisting session state")
            return False

    @staticmethod
    def _format_validation_error(error: ValidationError) -> str:
        """Build concise field-level validation errors for logging."""
        return "; ".join(
            f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}"
            for issue in error.errors()
        )

    @staticmethod
    def _calculate_duration_minutes(session: Session, now: datetime) -> Optional[int]:
        """
        Calculate elapsed minutes from session start to a given time.

        Args:
            session: Session containing date and start_time.
            now: Timestamp to calculate duration against.

        Returns:
            Rounded-down duration in minutes, or None if parsing fails.
        """
        try:
            start_dt = datetime.strptime(
                f"{session.date} {session.start_time}",
                "%d-%m-%Y %H:%M:%S",
            )
            elapsed_seconds = int((now - start_dt).total_seconds())
            if elapsed_seconds < 0:
                return 0
            return elapsed_seconds // 60
        except ValueError:
            logger.warning("Failed to parse session start datetime for duration calculation")
            return None
