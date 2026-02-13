"""
File-based session storage using JSON Lines (no database).

Each day gets its own log file: sessions_DD-MM-YYYY.log
Each session is appended as one JSON object per line.
All file writes use a threading lock to ensure safe concurrent access.
"""

import json
import logging
import os
import re
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from app.cache import cache_sessions, invalidate_cache
from app.config import settings

logger = logging.getLogger(__name__)

# Module-level lock for thread-safe file writes
_write_lock = threading.Lock()
MAX_LOG_FILE_SIZE_BYTES = 5 * 1024 * 1024


def _get_data_dir() -> Path:
    """Return the configured data directory path."""
    return Path(str(settings.data_dir))


def _get_archive_dir() -> Path:
    """Return the configured archive directory path with a safe fallback."""
    archive_value = getattr(settings, "archive_dir", None)
    if isinstance(archive_value, str) and archive_value:
        return Path(archive_value)
    return _get_data_dir() / "archive"


def get_log_path(date: datetime | None = None, part: int | None = None) -> Path:
    """
    Get the path to a session log file for a given date.

    Args:
        date: The date for the log file. Defaults to today.
        part: Optional part number. Base file when None or 1.

    Returns:
        Path like data/sessions_12-02-2026.log
    """
    if date is None:
        date = datetime.now()
    date_token = date.strftime("%d-%m-%Y")
    if part is None or part <= 1:
        filename = f"sessions_{date_token}.log"
    else:
        filename = f"sessions_{date_token}_part{part}.log"
    return _get_data_dir() / filename


def _extract_part_number(path: Path) -> int:
    """Extract log part number from filename (base file = part 1)."""
    match = re.search(r"_part(\d+)(?:_\d+)?$", path.stem)
    if match:
        return int(match.group(1))
    return 1


def _extract_collision_number(path: Path) -> int:
    """Extract optional collision suffix number from filename."""
    match = re.search(r"_(\d+)$", path.stem)
    if match:
        return int(match.group(1))
    return 0


def _log_sort_key(path: Path) -> tuple[int, int]:
    """Sort logs by part number first, then collision number."""
    return (_extract_part_number(path), _extract_collision_number(path))


def _is_log_for_date(filename: str, date_token: str) -> bool:
    """Return True if filename matches base/part log naming for a date."""
    pattern = rf"^sessions_{re.escape(date_token)}(?:_part\d+)?(?:_\d+)?\.log$"
    return re.match(pattern, filename) is not None


def _list_log_files_for_date(directory: Path, date: datetime) -> list[Path]:
    """List base+part log files for a date in a single directory."""
    if not directory.exists():
        return []

    date_token = date.strftime("%d-%m-%Y")
    paths = [
        path
        for path in directory.iterdir()
        if path.is_file() and _is_log_for_date(path.name, date_token)
    ]
    return sorted(paths, key=_log_sort_key)


def _get_active_log_path(date: datetime) -> Path:
    """Return the current writable log path for a given date."""
    part_logs = _list_log_files_for_date(_get_data_dir(), date)
    if part_logs:
        return max(part_logs, key=_log_sort_key)
    return get_log_path(date)


def _get_unique_archive_path(filename: str) -> Path:
    """Build a non-colliding archive destination path."""
    archive_dir = _get_archive_dir()
    candidate = archive_dir / filename
    if not candidate.exists():
        return candidate

    original = Path(filename)
    counter = 1
    while True:
        candidate = archive_dir / f"{original.stem}_{counter}{original.suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _rotate_log_file(log_path: Path, date: datetime) -> Path:
    """
    Move oversized log file to archive and return the next part file path.
    """
    archive_dir = _get_archive_dir()
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = _get_unique_archive_path(log_path.name)
    shutil.move(str(log_path), str(archive_path))
    logger.info("Rotated %s to archive: %s", log_path.name, archive_path.name)
    next_part = _extract_part_number(log_path) + 1
    return get_log_path(date, part=next_part)


def _get_read_paths(date: datetime) -> list[Path]:
    """Collect all readable log paths for a date across archive and data dirs."""
    path_by_name: dict[str, Path] = {}
    for directory in (_get_archive_dir(), _get_data_dir()):
        for path in _list_log_files_for_date(directory, date):
            path_by_name.setdefault(path.name, path)

    return sorted(path_by_name.values(), key=_log_sort_key)


def append_session(session_dict: dict[str, Any]) -> bool:
    """
    Append a session entry as a JSON line to today's log file.

    Thread-safe via module-level lock. Creates the data directory
    and file if they don't exist. Invalidates cache for today's date.

    Args:
        session_dict: Session data to write.

    Returns:
        True if write succeeded, False otherwise.
    """
    date = datetime.now()
    log_path = get_log_path(date)
    try:
        with _write_lock:
            log_path = _get_active_log_path(date)
            if log_path.exists():
                if os.path.getsize(log_path) > MAX_LOG_FILE_SIZE_BYTES:
                    log_path = _rotate_log_file(log_path, date)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(session_dict, ensure_ascii=False) + "\n")
        logger.info("Session appended to %s", log_path.name)
        # Invalidate cache for today's date
        invalidate_cache(date)
        return True
    except OSError as e:
        logger.error("Failed to append session to %s: %s", log_path, e)
        return False


@cache_sessions(ttl=30)  # Cache for 30 seconds
def read_sessions(date: datetime | None = None) -> list[dict[str, Any]]:
    """
    Read all sessions from a log file for a given date.

    Skips corrupted/malformed lines without crashing.
    Results are cached for 30 seconds to reduce file I/O.

    Args:
        date: The date to read sessions for. Defaults to today.

    Returns:
        List of session dictionaries. Empty list if file missing or empty.
    """
    if date is None:
        date = datetime.now()

    log_paths = _get_read_paths(date)
    if not log_paths:
        logger.debug("No log file found for date: %s", date.strftime("%d-%m-%Y"))
        return []

    sessions: list[dict[str, Any]] = []
    for log_path in log_paths:
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


def update_session(
    *,
    session_date: str,
    ssid: str,
    start_time: str,
    updates: dict[str, Any],
) -> bool:
    """
    Update the latest matching active session record in-place.

    Matching criteria:
    - same date, ssid, start_time
    - end_time is None (active/incomplete session snapshot)

    Args:
        session_date: Session date in DD-MM-YYYY format.
        ssid: Session SSID.
        start_time: Session start time in HH:MM:SS format.
        updates: Fields to update in the matched session entry.

    Returns:
        True when an entry is updated and persisted, False otherwise.
    """
    if not updates:
        logger.warning("update_session called with empty updates; skipping")
        return False

    try:
        date_obj = datetime.strptime(session_date, "%d-%m-%Y")
    except ValueError:
        logger.warning("update_session received invalid session_date: %s", session_date)
        return False

    try:
        with _write_lock:
            log_paths = _get_read_paths(date_obj)
            if not log_paths:
                logger.warning(
                    "No log files found for %s while updating session",
                    session_date,
                )
                return False

            # Walk newest-first to update the latest matching active snapshot.
            for log_path in reversed(log_paths):
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except OSError as e:
                    logger.error("Failed to read %s during update: %s", log_path, e)
                    continue

                for index in range(len(lines) - 1, -1, -1):
                    stripped = lines[index].strip()
                    if not stripped:
                        continue
                    try:
                        entry = json.loads(stripped)
                    except json.JSONDecodeError:
                        continue

                    if (
                        entry.get("date") == session_date
                        and entry.get("ssid") == ssid
                        and entry.get("start_time") == start_time
                        and entry.get("end_time") is None
                    ):
                        updated_entry = dict(entry)
                        updated_entry.update(updates)

                        if updated_entry == entry:
                            logger.info(
                                "Session already up-to-date in %s; no update required",
                                log_path.name,
                            )
                            return False

                        lines[index] = (
                            json.dumps(updated_entry, ensure_ascii=False) + "\n"
                        )
                        try:
                            with open(log_path, "w", encoding="utf-8") as f:
                                f.writelines(lines)
                        except OSError as e:
                            logger.error("Failed to persist update to %s: %s", log_path, e)
                            return False

                        logger.info("Session updated in %s", log_path.name)
                        # Invalidate cache for this date
                        invalidate_cache(date_obj)
                        return True

            logger.warning(
                "No matching active session found for update: %s %s %s",
                session_date,
                ssid,
                start_time,
            )
            return False
    except OSError as e:
        logger.error("update_session failed due to filesystem error: %s", e)
        return False
