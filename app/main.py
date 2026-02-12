"""
Main FastAPI application for Office Wi-Fi Tracker.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Office Wi-Fi Tracker starting up...")
    logger.info(f"📡 Monitoring Wi-Fi: {settings.office_wifi_name}")
    logger.info(f"⏱️  Work duration: {settings.work_duration_hours} hours")
    
    # TODO: Start Wi-Fi detector background task (Phase 1)
    # TODO: Start timer engine background task (Phase 3)
    
    yield
    
    # Shutdown
    logger.info("🛑 Office Wi-Fi Tracker shutting down...")
    # TODO: Save active session state
    # TODO: Cancel background tasks


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
