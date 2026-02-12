"""
File-based session storage using JSON Lines (no database).

Each day gets its own log file: sessions_DD-MM-YYYY.log
Each session is appended as one JSON object per line.
All file writes use a threading lock to ensure safe concurrent access.
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level lock for thread-safe file writes
_write_lock = threading.Lock()


def get_log_path(date: datetime | None = None) -> Path:
    """
    Get the path to a session log file for a given date.

    Args:
        date: The date for the log file. Defaults to today.

    Returns:
        Path like data/sessions_12-02-2026.log
    """
    if date is None:
        date = datetime.now()
    filename = f"sessions_{date.strftime('%d-%m-%Y')}.log"
    return Path(settings.data_dir) / filename


def append_session(session_dict: dict[str, Any]) -> bool:
    """
    Append a session entry as a JSON line to today's log file.

    Thread-safe via module-level lock. Creates the data directory
    and file if they don't exist.

    Args:
        session_dict: Session data to write.

    Returns:
        True if write succeeded, False otherwise.
    """
    log_path = get_log_path()
    try:
        with _write_lock:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(session_dict, ensure_ascii=False) + "\n")
        logger.info("Session appended to %s", log_path.name)
        return True
    except OSError as e:
        logger.error("Failed to append session to %s: %s", log_path, e)
        return False


def read_sessions(date: datetime | None = None) -> list[dict[str, Any]]:
    """
    Read all sessions from a log file for a given date.

    Skips corrupted/malformed lines without crashing.

    Args:
        date: The date to read sessions for. Defaults to today.

    Returns:
        List of session dictionaries. Empty list if file missing or empty.
    """
    log_path = get_log_path(date)

    if not log_path.exists():
        logger.debug("No log file found: %s", log_path)
        return []

    sessions: list[dict[str, Any]] = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    sessions.append(json.loads(stripped))
                except json.JSONDecodeError:
                    logger.warning(
                        "Skipping corrupted line %d in %s", line_num, log_path.name
                    )
    except OSError as e:
        logger.error("Failed to read %s: %s", log_path, e)

    return sessions
