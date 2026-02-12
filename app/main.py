"""
Main FastAPI application for Office Wi-Fi Tracker.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.config import settings
from app.session_manager import SessionState
from app.timer_engine import timer_polling_loop
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
    # TODO: Save active session state (Phase 2)
    logger.info("All background tasks stopped")


# Create FastAPI app
app = FastAPI(
    title="Office Wi-Fi 4-Hour Tracker",
    description="Local automation tool for tracking office presence",
    version="0.1.0",
    lifespan=lifespan
)

# Mount static files (will be used in Phase 4)
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Dashboard homepage (placeholder for Phase 4).
    """
    return """
    <html>
        <head>
            <title>Office Wi-Fi Tracker</title>
        </head>
        <body>
            <h1>Office Wi-Fi 4-Hour Tracker</h1>
            <p>Dashboard coming in Phase 4...</p>
            <p>Server is running! ✅</p>
        </body>
    </html>
    """


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True
    )
