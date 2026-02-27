"""
Main FastAPI application for DailyFour.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone, tzinfo, UTC
from logging.handlers import RotatingFileHandler
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import settings
from app.file_store import read_sessions
from app.analytics import (
    get_monthly_aggregation,
    get_monthly_aggregation_async,
    get_weekly_aggregation,
    get_weekly_aggregation_async,
)
from app.gamification import gamification_service  # Task 7.7
from app.session_manager import SessionState
from app.timer_engine import (
    _resolve_target_components,
    format_time_display,
    get_elapsed_time,
    get_remaining_time,
    timer_polling_loop,
    set_mongo_store as set_timer_mongo_store,
)
from app.wifi_detector import (
    get_current_ssid,
    get_session_manager,
    is_office_ssid,
    set_session_manager,
    wifi_polling_loop,
)
from app.mongodb_store import MongoDBStore
from app.network_checker import NetworkConnectivityChecker
from app.timezone_utils import format_time_ist, get_today_date_ist, now_ist, utc_to_ist
from app import analytics

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_logging_configured = False


def setup_logging() -> None:
    """Configure root logger with console output and optional file output."""
    global _logging_configured
    if _logging_configured:
        return
    _logging_configured = True

    root_logger = logging.getLogger()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Console handler (always on)
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(console)

    # File handler (opt-in via LOG_TO_FILE=true)
    if settings.log_to_file:
        log_dir = os.path.dirname(settings.log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            settings.log_file_path,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(file_handler)


class StatusResponse(BaseModel):
    """Typed schema for dashboard status API."""

    connected: bool
    ssid: str | None
    session_active: bool
    start_time: str | None
    elapsed_seconds: int
    elapsed_display: str
    remaining_seconds: int
    remaining_display: str
    completed_4h: bool
    progress_percent: float
    target_display: str
    target_completion_time_ist: str | None
    personal_leave_time_ist: str | None


class TodaySessionResponse(BaseModel):
    """Typed schema for one session row in today's data API."""

    start_time: str
    end_time: str | None
    duration_minutes: int | None
    completed_4h: bool


class TodayResponse(BaseModel):
    """Typed schema for today's sessions API."""

    date: str
    sessions: list[TodaySessionResponse]
    total_minutes: int
    total_display: str
    personal_leave_time_ist: str | None


class WeeklyDayResponse(BaseModel):
    """Typed schema for one day in weekly aggregation."""

    date: str
    day: str
    total_minutes: int
    session_count: int
    target_met: bool


class WeeklyResponse(BaseModel):
    """Typed schema for weekly aggregation API."""

    week: str
    days: list[WeeklyDayResponse]
    total_minutes: int
    avg_minutes_per_day: float
    days_target_met: int


class MonthlyWeekResponse(BaseModel):
    """Typed schema for one week in monthly aggregation."""

    week: str
    start_date: str
    end_date: str
    total_minutes: int
    days_present: int
    avg_daily_minutes: float


class MonthlyResponse(BaseModel):
    """Typed schema for monthly aggregation API."""

    month: str
    weeks: list[MonthlyWeekResponse]
    total_minutes: int
    total_days_present: int
    avg_daily_minutes: float


# Task 7.7: Gamification response models
class AchievementResponse(BaseModel):
    """Achievement information."""

    id: str
    name: str
    description: str
    icon: str
    earned: bool


class GamificationResponse(BaseModel):
    """Gamification data including streaks and achievements."""

    current_streak: int
    longest_streak: int
    total_days_met_target: int
    achievements: list[AchievementResponse]


def _get_now(tz: Optional[tzinfo] = None) -> datetime:
    """Return current time, optionally timezone-aware."""
    if tz is None:
        return datetime.now()
    return datetime.now(tz=tz)


def _parse_session_datetime(session_date: Any, session_start_time: Any) -> Optional[datetime]:
    """Parse DD-MM-YYYY + HH:MM:SS into datetime."""
    if not isinstance(session_date, str) or not isinstance(session_start_time, str):
        return None
    try:
        return datetime.strptime(
            f"{session_date} {session_start_time}",
            "%d-%m-%Y %H:%M:%S",
        )
    except ValueError:
        return None


def _safe_duration_minutes(value: Any) -> int | None:
    """Normalize duration to a non-negative integer when possible."""
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def _format_target_display(target_hours: int, target_minutes: int) -> str:
    """Format timer target for API display."""
    if target_hours <= 0:
        return f"{target_minutes}m"
    return f"{target_hours}h {target_minutes:02d}m"


def _format_total_display(total_minutes: int) -> str:
    """Format total minutes as Hh MMm."""
    safe_total = max(0, total_minutes)
    hours, minutes = divmod(safe_total, 60)
    return f"{hours}h {minutes:02d}m"


def _format_ist_time_12h(dt: Optional[datetime]) -> Optional[str]:
    """
    Format datetime as 12-hour IST with seconds and AM/PM.

    Explicit formatting ensures consistent 12-hour display across all sessions.
    Example output: "05:44:48 PM IST" or "11:30:00 AM IST"
    """
    if dt is None:
        return None

    # Convert to IST first.
    # `utc_to_ist` also normalizes naive datetimes as UTC, which is important
    # because MongoDB drivers can return naive datetime objects.
    ist_dt = utc_to_ist(dt)

    # Explicit 12-hour formatting (more reliable than strftime %p across locales)
    hour_12 = ist_dt.hour % 12
    if hour_12 == 0:
        hour_12 = 12  # Midnight (0:00) = 12 AM, Noon (12:00) = 12 PM
    am_pm = "AM" if ist_dt.hour < 12 else "PM"

    return f"{hour_12:02d}:{ist_dt.minute:02d}:{ist_dt.second:02d} {am_pm} IST"


def _parse_legacy_utc_datetime(session_date: str, session_time: str) -> Optional[datetime]:
    """Parse legacy HH:MM:SS values that were stored as UTC clock time."""
    parsed = _parse_session_datetime(session_date, session_time)
    if parsed is None:
        return None
    return parsed.replace(tzinfo=timezone.utc)


def _resolve_start_time_ist(doc: dict[str, Any], session_date: str) -> Optional[str]:
    """Resolve session start display time in IST from MongoDB document."""
    first_start_utc = doc.get("first_session_start_utc")
    if isinstance(first_start_utc, datetime):
        return _format_ist_time_12h(first_start_utc)

    current_start_utc = doc.get("current_session_start")
    if isinstance(current_start_utc, datetime):
        return _format_ist_time_12h(current_start_utc)

    legacy_start = doc.get("first_session_start")
    if isinstance(legacy_start, str):
        legacy_utc = _parse_legacy_utc_datetime(session_date, legacy_start)
        return _format_ist_time_12h(legacy_utc)

    return None


def _resolve_end_time_ist(doc: dict[str, Any], session_date: str) -> Optional[str]:
    """Resolve session end display time in IST from MongoDB document."""
    last_end_utc = doc.get("last_session_end_utc")
    if isinstance(last_end_utc, datetime):
        return _format_ist_time_12h(last_end_utc)

    # For completed sessions, last_activity is the session end timestamp.
    if not bool(doc.get("is_active", False)):
        last_activity = doc.get("last_activity")
        if isinstance(last_activity, datetime):
            return _format_ist_time_12h(last_activity)

    legacy_end = doc.get("last_session_end")
    if isinstance(legacy_end, str):
        legacy_utc = _parse_legacy_utc_datetime(session_date, legacy_end)
        return _format_ist_time_12h(legacy_utc)

    return None


def _resolve_first_session_start_utc(
    doc: dict[str, Any],
    session_date: str,
) -> Optional[datetime]:
    """Resolve the day's first session start as UTC datetime."""
    first_start_utc = doc.get("first_session_start_utc")
    if isinstance(first_start_utc, datetime):
        return first_start_utc if first_start_utc.tzinfo else first_start_utc.replace(tzinfo=UTC)

    current_start_utc = doc.get("current_session_start")
    if isinstance(current_start_utc, datetime):
        return current_start_utc if current_start_utc.tzinfo else current_start_utc.replace(tzinfo=UTC)

    legacy_start = doc.get("first_session_start")
    if isinstance(legacy_start, str):
        return _parse_legacy_utc_datetime(session_date, legacy_start)

    return None


def _resolve_personal_leave_time_ist(
    doc: dict[str, Any],
    session_date: str,
    target_duration: timedelta,
) -> Optional[str]:
    """Compute fixed personal leave time as first-login + target duration."""
    first_start_utc = _resolve_first_session_start_utc(doc, session_date)
    if first_start_utc is None:
        return None
    return _format_ist_time_12h(first_start_utc + target_duration)


def _calculate_progress_percent(
    elapsed_seconds: int,
    target_seconds: int,
    completed: bool,
) -> float:
    """Compute clamped progress percentage for UI."""
    if target_seconds <= 0:
        return 100.0 if completed or elapsed_seconds > 0 else 0.0

    progress = (elapsed_seconds / target_seconds) * 100
    clamped = max(0.0, min(progress, 100.0))
    return round(clamped, 1)


setup_logging()
logger = logging.getLogger(__name__)

# Holds references to background tasks so they can be cancelled on shutdown
_background_tasks: list[asyncio.Task] = []

# Global references for MongoDB and network checking
_mongo_store: Optional[MongoDBStore] = None
_network_checker: Optional[NetworkConnectivityChecker] = None


async def connectivity_polling_loop():
    """Background loop to check network connectivity every 30 seconds."""
    interval = settings.connectivity_check_interval_seconds
    logger.info(f"Network connectivity monitoring started — interval: {interval}s")

    while True:
        await asyncio.sleep(interval)
        try:
            current_ssid = get_current_ssid(use_cache=True)
            if not is_office_ssid(current_ssid):
                continue
            manager = get_session_manager()
            if manager:
                await manager.check_network_connectivity()
        except Exception:
            logger.exception("Error during network connectivity check")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    global _mongo_store, _network_checker

    # Startup
    logger.info("DailyFour starting up...")
    logger.info("Monitoring Wi-Fi: %s", settings.office_wifi_name)
    logger.info("Work duration: %d hours", settings.work_duration_hours)

    # Initialize MongoDB connection
    _mongo_store = MongoDBStore(settings.mongodb_uri, settings.mongodb_database)
    await _mongo_store.connect()
    logger.info("Connected to MongoDB")

    # Initialize network connectivity checker
    _network_checker = NetworkConnectivityChecker()
    await _network_checker.initialize()
    logger.info("Network connectivity checker initialized")

    # Create SessionManager with MongoDB backend
    from app.session_manager import SessionManager
    manager = SessionManager(_mongo_store, _network_checker)
    set_session_manager(manager)
    logger.info("SessionManager initialized with MongoDB backend")

    # Set MongoDB store in timer engine and analytics
    set_timer_mongo_store(_mongo_store)
    analytics.set_mongo_store(_mongo_store)
    logger.info("MongoDB store configured for timer and analytics")

    # Clean up any stale sessions from previous days
    today = get_today_date_ist()
    stale_count = await _mongo_store.close_stale_sessions(today)
    if stale_count:
        logger.info(f"Closed {stale_count} stale session(s) from previous days on startup")

    # Recover any active session after app restart
    current_ssid = get_current_ssid()
    recovered = await manager.recover_session(current_ssid)
    if recovered:
        logger.info("Resumed active session from MongoDB")
    elif is_office_ssid(current_ssid):
        # No session to recover but already on office Wi-Fi → start fresh
        await manager.start_session(settings.office_wifi_name)
        logger.info("Started new session — already connected to office Wi-Fi on startup")

    # Start Wi-Fi polling background task
    wifi_task = asyncio.create_task(wifi_polling_loop())
    _background_tasks.append(wifi_task)
    logger.info("Wi-Fi monitoring started")

    # Start timer polling background task
    timer_task = asyncio.create_task(timer_polling_loop())
    _background_tasks.append(timer_task)
    logger.info("Timer engine started")

    # Start network connectivity monitoring background task
    connectivity_task = asyncio.create_task(connectivity_polling_loop())
    _background_tasks.append(connectivity_task)
    logger.info("Network connectivity monitoring started")

    yield

    # Shutdown — cancel all background tasks
    logger.info("DailyFour shutting down...")
    for task in _background_tasks:
        task.cancel()
    await asyncio.gather(*_background_tasks, return_exceptions=True)
    _background_tasks.clear()

    # Cleanup network checker
    if _network_checker:
        await _network_checker.cleanup()
        logger.info("Network connectivity checker cleaned up")

    # Disconnect from MongoDB
    if _mongo_store:
        await _mongo_store.disconnect()
        logger.info("Disconnected from MongoDB")

    logger.info("All background tasks stopped")


# Create FastAPI app
app = FastAPI(
    title="DailyFour",
    description="Simple time tracking for your daily 4-hour work goal",
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Dashboard homepage template.
    """
    target_hours, target_minutes = _resolve_target_components(
        test_mode=getattr(settings, "test_mode", False),
        test_duration_minutes=getattr(settings, "test_duration_minutes", 2),
        work_duration_hours=getattr(settings, "work_duration_hours", 4),
        buffer_minutes=getattr(settings, "buffer_minutes", 10),
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "office_wifi_name": settings.office_wifi_name,
            "target_display": _format_target_display(target_hours, target_minutes),
        },
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "office_wifi": settings.office_wifi_name,
        "work_duration_hours": settings.work_duration_hours
    }


@app.get("/api/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """
    Return current connection and active-session timer status from MongoDB.
    """
    manager = get_session_manager()
    current_ssid = get_current_ssid(use_cache=True)  # Use cached SSID for fast API response
    connected = is_office_ssid(current_ssid)

    target_hours, target_minutes = _resolve_target_components(
        test_mode=getattr(settings, "test_mode", False),
        test_duration_minutes=getattr(settings, "test_duration_minutes", 2),
        work_duration_hours=getattr(settings, "work_duration_hours", 4),
        buffer_minutes=getattr(settings, "buffer_minutes", 10),
    )
    target_duration = timedelta(hours=target_hours, minutes=target_minutes)
    target_seconds = int(target_duration.total_seconds())

    # Default: no active timer when not connected to configured office SSID.
    session_active = False
    elapsed = timedelta(0)
    remaining = target_duration
    completed_4h = False
    start_time = None
    target_completion_time_ist = None
    personal_leave_time_ist = None

    status: dict[str, Any] = {}

    # Only read live session state while connected to office Wi-Fi.
    if manager and connected:
        status = await manager.get_current_status()
        session_active = bool(status.get("session_active", False))
        total_minutes = status.get("total_minutes", 0)
        completed_4h = bool(status.get("completed_4h", False))

        # Calculate elapsed and remaining
        elapsed = timedelta(minutes=total_minutes)
        remaining = target_duration - elapsed

        # Get today's session start time for display
        if session_active and _mongo_store:
            doc = None
            status_date = status.get("date")
            if isinstance(status_date, str) and status_date.strip():
                doc = await _mongo_store.get_daily_status(status_date)
            if not doc:
                doc = await _mongo_store.get_active_session()
            if doc:
                doc_date_raw = doc.get("date")
                doc_date = doc_date_raw if isinstance(doc_date_raw, str) else get_today_date_ist()
                start_time = _resolve_start_time_ist(doc, doc_date)
                personal_leave_time_ist = _resolve_personal_leave_time_ist(
                    doc,
                    doc_date,
                    target_duration,
                )

    elapsed_seconds = int(elapsed.total_seconds())
    remaining_seconds = int(remaining.total_seconds())
    if session_active:
        target_completion_dt = now_ist() + timedelta(seconds=max(0, remaining_seconds))
        target_completion_time_ist = _format_ist_time_12h(target_completion_dt)

    return StatusResponse(
        connected=connected,
        ssid=current_ssid,
        session_active=session_active,
        start_time=start_time,
        elapsed_seconds=elapsed_seconds,
        elapsed_display=format_time_display(elapsed),
        remaining_seconds=remaining_seconds,
        remaining_display=format_time_display(remaining),
        completed_4h=completed_4h,
        progress_percent=_calculate_progress_percent(
            elapsed_seconds=elapsed_seconds,
            target_seconds=target_seconds,
            completed=completed_4h,
        ),
        target_display=_format_target_display(target_hours, target_minutes),
        target_completion_time_ist=target_completion_time_ist,
        personal_leave_time_ist=personal_leave_time_ist,
    )


@app.get("/api/today", response_model=TodayResponse)
async def get_today_data() -> TodayResponse:
    """
    Return today's session history and total tracked minutes from MongoDB.
    """
    date = get_today_date_ist()  # DD-MM-YYYY in IST
    target_hours, target_minutes = _resolve_target_components(
        test_mode=getattr(settings, "test_mode", False),
        test_duration_minutes=getattr(settings, "test_duration_minutes", 2),
        work_duration_hours=getattr(settings, "work_duration_hours", 4),
        buffer_minutes=getattr(settings, "buffer_minutes", 10),
    )
    target_duration = timedelta(hours=target_hours, minutes=target_minutes)

    # Get today's data from MongoDB
    if _mongo_store:
        doc = await _mongo_store.get_daily_status(date)

        if doc:
            # MongoDB stores cumulative daily tracking
            # Create a single session entry representing all office time today
            sessions = []
            session_start = _resolve_start_time_ist(doc, date)
            if session_start:
                sessions.append(TodaySessionResponse(
                    start_time=session_start,
                    end_time=_resolve_end_time_ist(doc, date),
                    duration_minutes=doc.get("total_minutes", 0),
                    completed_4h=doc.get("completed_4h", False),
                ))

            total_minutes = doc.get("total_minutes", 0)
            personal_leave_time_ist = _resolve_personal_leave_time_ist(
                doc,
                date,
                target_duration,
            )
        else:
            sessions = []
            total_minutes = 0
            personal_leave_time_ist = None
    else:
        # Fallback if MongoDB not initialized
        sessions = []
        total_minutes = 0
        personal_leave_time_ist = None

    return TodayResponse(
        date=date,
        sessions=sessions,
        total_minutes=total_minutes,
        total_display=_format_total_display(total_minutes),
        personal_leave_time_ist=personal_leave_time_ist,
    )


@app.get("/api/weekly", response_model=WeeklyResponse)
async def get_weekly_data(week: Optional[str] = None) -> WeeklyResponse:
    """
    Return weekly session aggregation from MongoDB.
    """
    data = await get_weekly_aggregation_async(week)
    return WeeklyResponse(**data)


@app.get("/api/monthly", response_model=MonthlyResponse)
async def get_monthly_data(month: Optional[str] = None) -> MonthlyResponse:
    """
    Return monthly week-by-week session aggregation from MongoDB.
    """
    data = await get_monthly_aggregation_async(month)
    return MonthlyResponse(**data)


# Task 7.7: Gamification endpoint
@app.get("/api/gamification", response_model=GamificationResponse)
async def get_gamification_data() -> GamificationResponse:
    """
    Return gamification data including streaks and achievements.
    """
    # Get streak info
    streak_info = gamification_service.get_streak_info()

    # Get today's sessions for achievement checking
    sessions = read_sessions()
    today_str = datetime.now().strftime("%d-%m-%Y")
    today_sessions = [s for s in sessions if s.get("date") == today_str]

    # Get achievements
    achievements = gamification_service.get_achievements(today_sessions)

    return GamificationResponse(
        current_streak=streak_info["current_streak"],
        longest_streak=streak_info["longest_streak"],
        total_days_met_target=streak_info["total_days_met_target"],
        achievements=[AchievementResponse(**a) for a in achievements]
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )
