"""
Main FastAPI application for Office Wi-Fi Tracker.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, tzinfo
from logging.handlers import RotatingFileHandler
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import settings
from app.file_store import read_sessions
from app.analytics import get_monthly_aggregation, get_weekly_aggregation
from app.gamification import gamification_service  # Task 7.7
from app.session_manager import SessionState
from app.timer_engine import (
    _resolve_target_components,
    format_time_display,
    get_elapsed_time,
    get_remaining_time,
    timer_polling_loop,
)
from app.wifi_detector import get_current_ssid, get_session_manager, wifi_polling_loop

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Office Wi-Fi Tracker starting up...")
    logger.info("Monitoring Wi-Fi: %s", settings.office_wifi_name)
    logger.info("Work duration: %d hours", settings.work_duration_hours)

    # Recover any incomplete session from today's log before polling starts
    current_ssid = get_current_ssid()
    manager = get_session_manager()
    recovered = manager.recover_session(current_ssid)
    if recovered:
        logger.info("Resumed incomplete session from today's log")
    elif current_ssid == settings.office_wifi_name and manager.state == SessionState.IDLE:
        # No session to recover but already on office Wi-Fi → start fresh
        manager.start_session(current_ssid)
        logger.info("Started new session — already connected to office Wi-Fi on startup")

    # Start Wi-Fi polling background task
    wifi_task = asyncio.create_task(wifi_polling_loop())
    _background_tasks.append(wifi_task)
    logger.info("Wi-Fi monitoring started")

    # Start timer polling background task
    timer_task = asyncio.create_task(timer_polling_loop())
    _background_tasks.append(timer_task)
    logger.info("Timer engine started")

    yield

    # Shutdown — cancel all background tasks
    logger.info("Office Wi-Fi Tracker shutting down...")
    for task in _background_tasks:
        task.cancel()
    await asyncio.gather(*_background_tasks, return_exceptions=True)
    _background_tasks.clear()
    # Note: Session state persists immediately on every change (no shutdown flush needed)
    logger.info("All background tasks stopped")


# Create FastAPI app
app = FastAPI(
    title="Office Wi-Fi 4-Hour Tracker",
    description="Local automation tool for tracking office presence",
    version="0.1.0",
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
    Return current connection and active-session timer status.
    """
    manager = get_session_manager()
    active_session = manager.active_session
    current_ssid = get_current_ssid()
    connected = current_ssid == settings.office_wifi_name

    target_hours, target_minutes = _resolve_target_components(
        test_mode=getattr(settings, "test_mode", False),
        test_duration_minutes=getattr(settings, "test_duration_minutes", 2),
        work_duration_hours=getattr(settings, "work_duration_hours", 4),
        buffer_minutes=getattr(settings, "buffer_minutes", 10),
    )
    target_duration = timedelta(hours=target_hours, minutes=target_minutes)
    target_seconds = int(target_duration.total_seconds())

    elapsed = timedelta(0)
    remaining = target_duration
    completed_4h = False
    start_time = None
    session_active = active_session is not None

    if active_session is not None:
        start_time_value = getattr(active_session, "start_time", None)
        if isinstance(start_time_value, str):
            start_time = start_time_value

        completed_4h = bool(getattr(active_session, "completed_4h", False))
        start_dt = _parse_session_datetime(
            getattr(active_session, "date", None),
            start_time_value,
        )
        if start_dt is None:
            logger.warning("Invalid active session timestamp in /api/status")
        else:
            now = _get_now(start_dt.tzinfo)
            elapsed = get_elapsed_time(start_dt, now=now)
            remaining = get_remaining_time(
                start_time=start_dt,
                target_hours=target_hours,
                buffer_minutes=target_minutes,
                now=now,
            )
            if remaining <= timedelta(0):
                completed_4h = True

    elapsed_seconds = int(elapsed.total_seconds())
    remaining_seconds = int(remaining.total_seconds())

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
    )


@app.get("/api/today", response_model=TodayResponse)
async def get_today_data() -> TodayResponse:
    """
    Return today's session history and total tracked minutes.
    """
    now = _get_now()
    today_token = now.strftime("%d-%m-%Y")
    manager = get_session_manager()
    active_session = manager.active_session

    raw_sessions = read_sessions(now)
    session_map: dict[tuple[str, str, str], TodaySessionResponse] = {}

    for entry in raw_sessions:
        if not isinstance(entry, dict):
            continue
        entry_date = entry.get("date")
        start_time = entry.get("start_time")
        if entry_date != today_token or not isinstance(start_time, str) or not start_time:
            continue

        session_key = (entry_date, start_time, str(entry.get("ssid", "")))
        session_map[session_key] = TodaySessionResponse(
            start_time=start_time,
            end_time=entry.get("end_time") if isinstance(entry.get("end_time"), str) else None,
            duration_minutes=_safe_duration_minutes(entry.get("duration_minutes")),
            completed_4h=bool(entry.get("completed_4h", False)),
        )

    if active_session is not None and getattr(active_session, "date", None) == today_token:
        active_start = getattr(active_session, "start_time", None)
        if isinstance(active_start, str) and active_start:
            active_duration = _safe_duration_minutes(getattr(active_session, "duration_minutes", None))
            active_start_dt = _parse_session_datetime(today_token, active_start)
            if active_start_dt is not None:
                active_now = _get_now(active_start_dt.tzinfo)
                active_duration = int(
                    get_elapsed_time(active_start_dt, now=active_now).total_seconds() // 60
                )

            active_key = (today_token, active_start, str(getattr(active_session, "ssid", "")))
            session_map[active_key] = TodaySessionResponse(
                start_time=active_start,
                end_time=None,
                duration_minutes=active_duration,
                completed_4h=bool(getattr(active_session, "completed_4h", False)),
            )

    sessions = sorted(session_map.values(), key=lambda session: session.start_time)
    total_minutes = sum(session.duration_minutes or 0 for session in sessions)

    return TodayResponse(
        date=today_token,
        sessions=sessions,
        total_minutes=total_minutes,
        total_display=_format_total_display(total_minutes),
    )


@app.get("/api/weekly", response_model=WeeklyResponse)
async def get_weekly_data(week: Optional[str] = None) -> WeeklyResponse:
    """
    Return weekly session aggregation.
    """
    return WeeklyResponse(**get_weekly_aggregation(week))


@app.get("/api/monthly", response_model=MonthlyResponse)
async def get_monthly_data(month: Optional[str] = None) -> MonthlyResponse:
    """
    Return monthly week-by-week session aggregation.
    """
    return MonthlyResponse(**get_monthly_aggregation(month))


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
