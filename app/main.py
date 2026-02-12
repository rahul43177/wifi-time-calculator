"""
Main FastAPI application for Office Wi-Fi Tracker.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.config import settings
from app.wifi_detector import wifi_polling_loop

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

    # Start Wi-Fi polling background task
    wifi_task = asyncio.create_task(wifi_polling_loop())
    _background_tasks.append(wifi_task)
    logger.info("Wi-Fi monitoring started")

    # TODO: Start timer engine background task (Phase 3)

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
