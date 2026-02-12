"""
Tests for Phase 2.1: File Storage Module.

Covers:
- File creation with DD-MM-YYYY naming
- JSON line append correctness
- Reading today's sessions
- Thread-safety (simulated concurrent writes)
- Missing file, empty file, corrupted line handling
"""

import json
import os
import tempfile
import threading
from datetime import datetime
from unittest.mock import patch

import pytest

from app.file_store import get_log_path, append_session, read_sessions


@pytest.fixture(autouse=True)
def _tmp_data_dir():
    """Redirect all file_store operations to a temp directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.file_store.settings") as mock_settings:
            mock_settings.data_dir = tmpdir
            yield tmpdir


# --- get_log_path tests ---


def test_log_path_uses_dd_mm_yyyy_format():
    """Filename uses DD-MM-YYYY date format."""
    path = get_log_path(datetime(2026, 2, 5))
    assert path.name == "sessions_05-02-2026.log"


def test_log_path_defaults_to_today():
    """Defaults to today's date when no argument given."""
    path = get_log_path()
    today = datetime.now().strftime("%d-%m-%Y")
    assert path.name == f"sessions_{today}.log"


def test_log_path_inside_data_dir(_tmp_data_dir):
    """Path is inside the configured data directory."""
    path = get_log_path()
    assert str(path).startswith(_tmp_data_dir)


# --- append_session tests ---


def test_append_creates_file_and_writes_json(_tmp_data_dir):
    """First append creates the file with valid JSON line."""
    session = {"ssid": "OfficeWifi", "start_time": "09:30:00"}
    result = append_session(session)

    assert result is True

    log_path = get_log_path()
    assert log_path.exists()

    with open(log_path) as f:
        line = f.readline()
    assert json.loads(line) == session


def test_append_multiple_sessions(_tmp_data_dir):
    """Multiple appends produce multiple JSON lines."""
    s1 = {"ssid": "OfficeWifi", "start_time": "09:00:00"}
    s2 = {"ssid": "OfficeWifi", "start_time": "14:00:00"}

    append_session(s1)
    append_session(s2)

    with open(get_log_path()) as f:
        lines = f.readlines()

    assert len(lines) == 2
    assert json.loads(lines[0]) == s1
    assert json.loads(lines[1]) == s2


def test_append_returns_false_on_write_error():
    """Returns False when the directory is not writable."""
    with patch("app.file_store.settings") as mock_settings:
        mock_settings.data_dir = "/nonexistent/readonly/path"
        result = append_session({"ssid": "test"})
    assert result is False


def test_append_handles_unicode(_tmp_data_dir):
    """Unicode characters in session data are preserved."""
    session = {"ssid": "Büro-WiFi", "note": "Ñoño"}
    append_session(session)

    sessions = read_sessions()
    assert sessions[0]["ssid"] == "Büro-WiFi"
    assert sessions[0]["note"] == "Ñoño"


# --- read_sessions tests ---


def test_read_returns_empty_for_missing_file():
    """Returns empty list when no log file exists for the date."""
    sessions = read_sessions(datetime(2000, 1, 1))
    assert sessions == []


def test_read_returns_empty_for_empty_file(_tmp_data_dir):
    """Returns empty list when the log file exists but is empty."""
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.touch()

    assert read_sessions() == []


def test_read_skips_corrupted_lines(_tmp_data_dir):
    """Corrupted lines are skipped; valid lines still returned."""
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write('{"ssid": "Good"}\n')
        f.write("THIS IS NOT JSON\n")
        f.write('{"ssid": "AlsoGood"}\n')

    sessions = read_sessions()
    assert len(sessions) == 2
    assert sessions[0]["ssid"] == "Good"
    assert sessions[1]["ssid"] == "AlsoGood"


def test_read_skips_blank_lines(_tmp_data_dir):
    """Blank lines are silently skipped."""
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write('{"ssid": "A"}\n')
        f.write("\n")
        f.write("   \n")
        f.write('{"ssid": "B"}\n')

    sessions = read_sessions()
    assert len(sessions) == 2


def test_read_for_specific_date(_tmp_data_dir):
    """Can read sessions for a specific past date."""
    target = datetime(2026, 1, 15)
    log_path = get_log_path(target)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write('{"ssid": "OldSession"}\n')

    sessions = read_sessions(target)
    assert len(sessions) == 1
    assert sessions[0]["ssid"] == "OldSession"


# --- Thread-safety test ---


def test_concurrent_writes_no_data_loss(_tmp_data_dir):
    """Multiple threads writing simultaneously don't lose data."""
    num_threads = 10
    writes_per_thread = 20
    errors: list[str] = []

    def writer(thread_id: int) -> None:
        for i in range(writes_per_thread):
            ok = append_session({"thread": thread_id, "index": i})
            if not ok:
                errors.append(f"thread {thread_id} write {i} failed")

    threads = [threading.Thread(target=writer, args=(t,)) for t in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Write errors: {errors}"

    sessions = read_sessions()
    assert len(sessions) == num_threads * writes_per_thread
