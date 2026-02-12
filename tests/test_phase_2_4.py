"""
Tests for Phase 2.4: File Rotation Logic.

Covers:
- Pre-write size check and rotation trigger
- Archive move and part file creation
- Multiple rotation cycles
- Data integrity across rotated files
- Edge and failure handling
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.file_store import append_session, get_log_path, read_sessions


@pytest.fixture(autouse=True)
def _tmp_store_paths():
    """Use isolated temp data/archive directories for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = os.path.join(tmpdir, "data")
        archive_dir = os.path.join(tmpdir, "archive")
        with patch("app.file_store.settings") as mock_settings:
            mock_settings.data_dir = data_dir
            mock_settings.archive_dir = archive_dir
            yield Path(data_dir), Path(archive_dir)


def test_rotation_moves_base_file_and_writes_to_part2(_tmp_store_paths) -> None:
    """When base file exceeds threshold, it is archived and part2 receives new data."""
    data_dir, archive_dir = _tmp_store_paths
    base_path = get_log_path()
    base_path.parent.mkdir(parents=True, exist_ok=True)
    with open(base_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ssid": "Old"}) + "\n")

    with patch("app.file_store.MAX_LOG_FILE_SIZE_BYTES", 1):
        ok = append_session({"ssid": "New"})

    assert ok is True
    assert not base_path.exists()
    assert (archive_dir / base_path.name).exists()
    part2_path = get_log_path(part=2)
    assert part2_path.exists()
    with open(part2_path, "r", encoding="utf-8") as f:
        written = json.loads(f.readline())
    assert written["ssid"] == "New"


def test_rotation_supports_multiple_part_files(_tmp_store_paths) -> None:
    """Oversized part2 is rotated to archive and next write goes to part3."""
    _data_dir, archive_dir = _tmp_store_paths
    base_path = get_log_path()
    base_path.parent.mkdir(parents=True, exist_ok=True)
    with open(base_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ssid": "A"}) + "\n")

    with patch("app.file_store.MAX_LOG_FILE_SIZE_BYTES", 1):
        assert append_session({"ssid": "B"}) is True
        assert append_session({"ssid": "C"}) is True

    assert (archive_dir / base_path.name).exists()
    assert (archive_dir / get_log_path(part=2).name).exists()
    assert get_log_path(part=3).exists()

    sessions = read_sessions()
    assert [s["ssid"] for s in sessions] == ["A", "B", "C"]


def test_rotation_is_not_triggered_when_size_equals_threshold(_tmp_store_paths) -> None:
    """Rotation must trigger only for file size strictly greater than threshold."""
    _data_dir, archive_dir = _tmp_store_paths
    base_path = get_log_path()
    base_path.parent.mkdir(parents=True, exist_ok=True)
    with open(base_path, "w", encoding="utf-8") as f:
        f.write("12345")

    with patch("app.file_store.MAX_LOG_FILE_SIZE_BYTES", 5):
        ok = append_session({"ssid": "OfficeWifi"})

    assert ok is True
    assert base_path.exists()
    assert not (archive_dir / base_path.name).exists()
    assert not get_log_path(part=2).exists()


def test_read_sessions_preserves_data_across_archive_and_parts(
    _tmp_store_paths,
) -> None:
    """Read should include archived and active part files while skipping corrupted lines."""
    _data_dir, _archive_dir = _tmp_store_paths
    base_path = get_log_path()
    base_path.parent.mkdir(parents=True, exist_ok=True)
    with open(base_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ssid": "First"}) + "\n")
        f.write("CORRUPTED_LINE\n")

    with patch("app.file_store.MAX_LOG_FILE_SIZE_BYTES", 1):
        assert append_session({"ssid": "Second"}) is True

    sessions = read_sessions()
    assert len(sessions) == 2
    assert sessions[0]["ssid"] == "First"
    assert sessions[1]["ssid"] == "Second"


def test_rotation_creates_archive_directory_if_missing(_tmp_store_paths) -> None:
    """Archive directory is created automatically during rotation."""
    _data_dir, archive_dir = _tmp_store_paths
    base_path = get_log_path()
    base_path.parent.mkdir(parents=True, exist_ok=True)
    with open(base_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ssid": "Old"}) + "\n")

    assert not archive_dir.exists()
    with patch("app.file_store.MAX_LOG_FILE_SIZE_BYTES", 1):
        assert append_session({"ssid": "New"}) is True

    assert archive_dir.exists()


def test_append_returns_false_when_rotation_move_fails(_tmp_store_paths) -> None:
    """If archive move fails during rotation, append_session returns False safely."""
    _data_dir, _archive_dir = _tmp_store_paths
    base_path = get_log_path()
    base_path.parent.mkdir(parents=True, exist_ok=True)
    with open(base_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ssid": "Old"}) + "\n")

    with patch("app.file_store.MAX_LOG_FILE_SIZE_BYTES", 1):
        with patch("app.file_store.shutil.move", side_effect=OSError("move failed")):
            ok = append_session({"ssid": "New"})

    assert ok is False
    assert base_path.exists()
    assert not get_log_path(part=2).exists()


def test_read_sessions_includes_collision_named_archived_files(
    _tmp_store_paths,
) -> None:
    """Read should include archived files with collision suffix names."""
    _data_dir, archive_dir = _tmp_store_paths
    archive_dir.mkdir(parents=True, exist_ok=True)
    collision_base = archive_dir / f"{get_log_path().stem}_1.log"
    with open(collision_base, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ssid": "ArchivedBaseCollision"}) + "\n")

    active_path = get_log_path(part=2)
    active_path.parent.mkdir(parents=True, exist_ok=True)
    with open(active_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ssid": "ActivePart"}) + "\n")

    sessions = read_sessions()
    assert [s["ssid"] for s in sessions] == ["ArchivedBaseCollision", "ActivePart"]


def test_append_returns_false_when_active_path_resolution_fails(
    _tmp_store_paths,
) -> None:
    """Errors before active log path assignment should still fail gracefully."""
    _data_dir, _archive_dir = _tmp_store_paths
    with patch("app.file_store._get_active_log_path", side_effect=OSError("no access")):
        ok = append_session({"ssid": "OfficeWifi"})

    assert ok is False
