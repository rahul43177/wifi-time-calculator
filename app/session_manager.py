"""
Session management module.
Handles session state machine and session lifecycle.
"""

import logging
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Session state enumeration."""
    IDLE = "idle"
    IN_OFFICE_SESSION = "in_office_session"
    COMPLETED = "completed"


class Session(BaseModel):
    """Session data model."""
    date: str
    ssid: str
    start_time: str
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    completed_4h: bool = False


class SessionManager:
    """
    Manages office session state and lifecycle.
    
    TODO: Implement in Phase 2, Task 2.2
    """
    
    def __init__(self):
        self.state = SessionState.IDLE
        self.active_session: Optional[Session] = None
        logger.info("SessionManager initialized")
    
    def start_session(self, ssid: str):
        """Start a new office session."""
        logger.info(f"Session start requested for SSID: {ssid} (not yet implemented)")
    
    def end_session(self):
        """End the current office session."""
        logger.info("Session end requested (not yet implemented)")
