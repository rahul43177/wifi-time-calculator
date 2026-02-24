"""
MongoDB Store - Persistent storage layer using MongoDB Atlas.

This module replaces the file-based storage system with MongoDB for:
- Atomic operations (no race conditions)
- Better durability and reliability
- Efficient aggregation queries
- Cumulative daily tracking
- Grace period management
- Network connectivity tracking
"""

import logging
from datetime import datetime, UTC
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
import certifi
from app.timezone_utils import now_utc

logger = logging.getLogger(__name__)


class MongoDBStore:
    """MongoDB storage layer for WiFi tracking sessions"""

    def __init__(self, uri: str, database: str):
        """
        Initialize MongoDB store.

        Args:
            uri: MongoDB Atlas connection string
            database: Database name
        """
        self.uri = uri
        self.database_name = database
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self):
        """
        Initialize async connection pool and ensure indexes.

        This should be called on application startup.
        """
        try:
            self.client = AsyncIOMotorClient(
                self.uri,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                retryWrites=True
            )
            self.db = self.client.get_database(self.database_name)

            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.database_name}")

            # Ensure indexes
            await self._ensure_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _ensure_indexes(self):
        """Create indexes on startup for performance"""
        try:
            # Daily sessions indexes
            await self.db.daily_sessions.create_index("date", unique=True)
            await self.db.daily_sessions.create_index("is_active")
            await self.db.daily_sessions.create_index([("date", 1), ("ssid", 1)])

            # Session events indexes (optional collection)
            await self.db.session_events.create_index([("date", 1), ("timestamp", 1)])
            await self.db.session_events.create_index("event_type")

            logger.info("MongoDB indexes ensured")

        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")

    # =========================================================================
    # Daily Session Operations
    # =========================================================================

    async def get_or_create_daily_session(
        self,
        date: str,
        ssid: str,
        target_minutes: int
    ) -> dict:
        """
        Get today's session or create new one (atomic operation).

        Args:
            date: DD-MM-YYYY format
            ssid: Office WiFi name
            target_minutes: 4h + buffer in minutes

        Returns:
            Daily session document
        """
        doc = await self.db.daily_sessions.find_one_and_update(
            {"date": date},
            {
                "$setOnInsert": {
                    "date": date,
                    "ssid": ssid,
                    "total_minutes": 0,
                    "completed_4h": False,
                    "target_minutes": target_minutes,
                    "is_active": False,
                    "sessions_count": 0,
                    "paused_duration_minutes": 0,
                    "session_start_total_minutes": 0,
                    "session_start_paused_minutes": 0,
                    "grace_period_minutes": 2,  # Default grace period
                    "grace_period_start": None,
                    "has_network_access": True,
                    "paused_at": None,
                    "created_at": now_utc()
                },
                "$set": {
                    "updated_at": now_utc()
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return doc

    async def start_session(
        self,
        date: str,
        ssid: str,
        start_time: datetime
    ):
        """
        Start or resume session for today (atomic operation).

        Args:
            date: DD-MM-YYYY format
            ssid: Office WiFi name
            start_time: UTC datetime when session started

        Returns:
            UpdateResult
        """
        first_session_start = start_time.strftime("%H:%M:%S")
        result = await self.db.daily_sessions.update_one(
            {"date": date},
            [
                {
                    "$set": {
                        "ssid": ssid,
                        "is_active": True,
                        "current_session_start": start_time,
                        "session_start_total_minutes": {"$ifNull": ["$total_minutes", 0]},
                        "session_start_paused_minutes": {"$ifNull": ["$paused_duration_minutes", 0]},
                        "first_session_start": {"$ifNull": ["$first_session_start", first_session_start]},
                        "last_activity": start_time,
                        "grace_period_start": None,  # Clear any grace period
                        "has_network_access": True,
                        "paused_at": None,
                        "updated_at": now_utc(),
                    }
                },
                {
                    "$set": {
                        "sessions_count": {"$add": [{"$ifNull": ["$sessions_count", 0]}, 1]}
                    }
                },
            ],
        )

        if result.modified_count > 0:
            logger.info(f"Session started/resumed for {date}")

        return result

    async def update_elapsed_time(
        self,
        date: str,
        current_total_minutes: int
    ) -> bool:
        """
        Update cumulative total minutes (called periodically by timer).

        Args:
            date: DD-MM-YYYY format
            current_total_minutes: Current cumulative total for today

        Returns:
            True if updated, False if no active session
        """
        result = await self.db.daily_sessions.update_one(
            {"date": date, "is_active": True},
            {
                "$set": {
                    "total_minutes": current_total_minutes,
                    "last_activity": now_utc(),
                    "updated_at": now_utc()
                }
            }
        )

        return result.modified_count > 0

    async def end_session(
        self,
        date: str,
        end_time: datetime,
        final_minutes: int
    ):
        """
        End current session (grace period expired or manual end).

        Args:
            date: DD-MM-YYYY format
            end_time: UTC datetime when session ended
            final_minutes: Final cumulative total for today

        Returns:
            UpdateResult
        """
        result = await self.db.daily_sessions.update_one(
            {"date": date, "is_active": True},
            {
                "$set": {
                    "is_active": False,
                    "total_minutes": final_minutes,
                    "last_session_end": end_time.strftime("%H:%M:%S"),
                    "current_session_start": None,
                    "session_start_total_minutes": None,
                    "session_start_paused_minutes": None,
                    "last_activity": end_time,
                    "grace_period_start": None,  # Clear grace period
                    "paused_at": None,
                    "has_network_access": True,
                    "updated_at": now_utc()
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"Session ended for {date} - Total: {final_minutes} min")

        return result

    # =========================================================================
    # Grace Period Operations
    # =========================================================================

    async def start_grace_period(
        self,
        date: str,
        grace_start: datetime
    ):
        """
        WiFi disconnected - start grace period for potential reconnection.

        Args:
            date: DD-MM-YYYY format
            grace_start: UTC datetime when WiFi disconnected

        Returns:
            UpdateResult
        """
        result = await self.db.daily_sessions.update_one(
            {"date": date, "is_active": True},
            {
                "$set": {
                    "grace_period_start": grace_start,
                    "updated_at": now_utc()
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"Grace period started for {date}")

        return result

    async def check_grace_period_status(self, date: str) -> dict:
        """
        Check if grace period is active and if it has expired.

        Args:
            date: DD-MM-YYYY format

        Returns:
            Dictionary with grace period status:
            - active: bool - Is grace period currently active?
            - expired: bool - Has grace period exceeded limit?
            - grace_start: datetime - When did grace period start?
            - elapsed_minutes: float - How long has it been?
        """
        doc = await self.db.daily_sessions.find_one(
            {
                "date": date,
                "is_active": True,
                "grace_period_start": {"$ne": None}
            }
        )

        if not doc:
            return {"active": False}

        # MongoDB returns offset-naive datetimes, so add UTC timezone
        grace_start = doc["grace_period_start"].replace(tzinfo=UTC)
        grace_minutes = doc.get("grace_period_minutes", 2)
        elapsed = (now_utc() - grace_start).total_seconds() / 60

        return {
            "active": True,
            "expired": elapsed > grace_minutes,
            "grace_start": grace_start,
            "elapsed_minutes": elapsed,
            "grace_limit_minutes": grace_minutes
        }

    async def cancel_grace_period(self, date: str):
        """
        WiFi reconnected - cancel grace period.

        Args:
            date: DD-MM-YYYY format

        Returns:
            UpdateResult
        """
        result = await self.db.daily_sessions.update_one(
            {"date": date},
            {
                "$set": {
                    "grace_period_start": None,
                    "updated_at": now_utc()
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"Grace period cancelled for {date}")

        return result

    # =========================================================================
    # Network Connectivity Operations
    # =========================================================================

    async def pause_for_reauth(
        self,
        date: str,
        pause_time: datetime
    ):
        """
        Network lost but WiFi connected - pause timer during re-authentication.

        Args:
            date: DD-MM-YYYY format
            pause_time: UTC datetime when network was lost

        Returns:
            UpdateResult
        """
        result = await self.db.daily_sessions.update_one(
            {"date": date, "is_active": True},
            {
                "$set": {
                    "has_network_access": False,
                    "paused_at": pause_time,
                    "last_connectivity_check": pause_time,
                    "updated_at": now_utc()
                }
            }
        )

        if result.modified_count > 0:
            logger.warning(f"Timer paused for re-auth on {date}")

        return result

    async def resume_after_reauth(
        self,
        date: str,
        resume_time: datetime
    ):
        """
        Network restored - resume timer and track pause duration.

        Args:
            date: DD-MM-YYYY format
            resume_time: UTC datetime when network was restored

        Returns:
            UpdateResult or None if no pause was active
        """
        # Get current document to calculate pause duration
        doc = await self.db.daily_sessions.find_one(
            {
                "date": date,
                "is_active": True,
                "paused_at": {"$ne": None}
            }
        )

        if not doc or not doc.get("paused_at"):
            return None

        # Calculate pause duration
        # MongoDB returns offset-naive datetimes, so add UTC timezone
        paused_at = doc["paused_at"].replace(tzinfo=UTC)
        pause_duration = (resume_time - paused_at).total_seconds() / 60

        result = await self.db.daily_sessions.update_one(
            {"date": date},
            {
                "$set": {
                    "has_network_access": True,
                    "paused_at": None,
                    "last_connectivity_check": resume_time,
                    "updated_at": now_utc()
                },
                "$inc": {
                    "paused_duration_minutes": round(pause_duration)
                }
            }
        )

        if result.modified_count > 0:
            logger.info(
                f"Timer resumed on {date} - Paused for {int(pause_duration)} min"
            )

        return result

    async def update_connectivity_check(
        self,
        date: str,
        has_access: bool
    ):
        """
        Update last connectivity check timestamp.

        Args:
            date: DD-MM-YYYY format
            has_access: Does device have internet access?

        Returns:
            UpdateResult
        """
        return await self.db.daily_sessions.update_one(
            {"date": date, "is_active": True},
            {
                "$set": {
                    "has_network_access": has_access,
                    "last_connectivity_check": now_utc(),
                    "updated_at": now_utc()
                }
            }
        )

    # =========================================================================
    # Completion Tracking
    # =========================================================================

    async def mark_completed(self, date: str):
        """
        Mark 4-hour goal as completed for today.

        Args:
            date: DD-MM-YYYY format

        Returns:
            UpdateResult
        """
        result = await self.db.daily_sessions.update_one(
            {"date": date, "completed_4h": False},
            {
                "$set": {
                    "completed_4h": True,
                    "updated_at": now_utc()
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"Daily goal completed for {date}")

        return result

    # =========================================================================
    # Query Operations
    # =========================================================================

    async def get_daily_status(self, date: str) -> Optional[dict]:
        """
        Get current status for a specific date.

        Args:
            date: DD-MM-YYYY format

        Returns:
            Daily session document or None if not found
        """
        return await self.db.daily_sessions.find_one({"date": date})

    async def get_active_session(self) -> Optional[dict]:
        """
        Get currently active session (if any).

        Returns:
            Active session document or None
        """
        return await self.db.daily_sessions.find_one({"is_active": True})

    async def close_stale_sessions(self, today_date: str) -> int:
        """
        Close any active sessions that are NOT from today.
        Called on startup to clean up sessions that were left open
        (e.g., app crashed or was killed without proper shutdown).

        Args:
            today_date: DD-MM-YYYY format for today

        Returns:
            Number of stale sessions closed
        """
        result = await self.db.daily_sessions.update_many(
            {"is_active": True, "date": {"$ne": today_date}},
            {
                "$set": {
                    "is_active": False,
                    "current_session_start": None,
                    "session_start_total_minutes": None,
                    "session_start_paused_minutes": None,
                    "paused_at": None,
                    "last_activity": now_utc(),
                    "updated_at": now_utc()
                }
            }
        )
        count = result.modified_count
        if count > 0:
            logger.info(f"Closed {count} stale session(s) from previous days")
        return count

    async def get_sessions_in_range(
        self,
        start_date: str,
        end_date: str
    ) -> list:
        """
        Get all sessions within a date range.

        Args:
            start_date: DD-MM-YYYY format
            end_date: DD-MM-YYYY format

        Returns:
            List of daily session documents
        """
        cursor = self.db.daily_sessions.find({
            "date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort("date", 1)

        return await cursor.to_list(length=None)

    # =========================================================================
    # Event Logging (Optional)
    # =========================================================================

    async def log_event(
        self,
        date: str,
        event_type: str,
        ssid: str,
        metadata: Optional[dict] = None
    ):
        """
        Log a session event for debugging and audit trail.

        Args:
            date: DD-MM-YYYY format
            event_type: "connect", "disconnect", "pause", "resume", "complete"
            ssid: Office WiFi name
            metadata: Additional event data

        Returns:
            InsertResult
        """
        event = {
            "date": date,
            "event_type": event_type,
            "timestamp": now_utc(),
            "ssid": ssid,
            "metadata": metadata or {}
        }

        return await self.db.session_events.insert_one(event)
