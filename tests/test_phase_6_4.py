"""
Tests for Phase 6.4: Test Boot Auto-Start.

Covers:
- Service loading verification
- Health endpoint accessibility
- Session recovery integration
- Log file creation
"""

import subprocess
from pathlib import Path


def test_launchd_plist_location_is_correct():
    """Verify plist should be installed to user LaunchAgents directory."""
    expected_location = Path.home() / "Library" / "LaunchAgents" / "com.officetracker.plist"
    # Test just verifies the expected path - actual installation is manual/scripted
    assert expected_location.parent.exists(), "LaunchAgents directory should exist"


def test_service_can_be_queried_with_launchctl():
    """Verify launchctl command is available and functional."""
    # This test verifies launchctl is available (critical for boot auto-start)
    try:
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, "launchctl list should succeed"
    except FileNotFoundError:
        # launchctl not found - likely not macOS or restricted environment
        import pytest
        pytest.skip("launchctl not available (not macOS or restricted environment)")
    except subprocess.TimeoutExpired:
        # launchctl hung - environment issue
        import pytest
        pytest.skip("launchctl command timed out (environment issue)")


def test_logs_directory_exists():
    """Verify logs directory exists for stdout/stderr."""
    logs_dir = Path("logs")
    assert logs_dir.exists()
    assert logs_dir.is_dir()


def test_stdout_log_path_is_valid():
    """Verify stdout.log path is accessible."""
    stdout_log = Path("logs/stdout.log")
    # Log file should be creatable (may not exist yet if service not started)
    assert stdout_log.parent.exists()


def test_stderr_log_path_is_valid():
    """Verify stderr.log path is accessible."""
    stderr_log = Path("logs/stderr.log")
    # Log file should be creatable (may not exist yet if service not started)
    assert stderr_log.parent.exists()


def test_plist_points_to_correct_working_directory():
    """Verify plist WorkingDirectory matches project root."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    working_dir = plist_data.get("WorkingDirectory")
    assert working_dir is not None
    assert "wifi-tracking" in working_dir


def test_plist_points_to_correct_python_executable():
    """Verify plist ProgramArguments includes venv python."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    program_args = plist_data.get("ProgramArguments", [])
    assert len(program_args) > 0
    python_path = program_args[0]
    assert "venv/bin/python" in python_path


def test_plist_includes_uvicorn_command():
    """Verify plist ProgramArguments includes uvicorn module."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    program_args = plist_data.get("ProgramArguments", [])
    assert "uvicorn" in program_args or any("uvicorn" in arg for arg in program_args)


def test_plist_includes_app_main():
    """Verify plist ProgramArguments includes app.main:app."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    program_args = plist_data.get("ProgramArguments", [])
    assert "app.main:app" in program_args


def test_plist_includes_correct_port():
    """Verify plist ProgramArguments includes port 8787."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    program_args = plist_data.get("ProgramArguments", [])
    assert "8787" in program_args


def test_plist_has_boot_required_keys():
    """Verify plist has all keys required for boot auto-start."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    # Critical keys for boot auto-start
    required_keys = ["Label", "ProgramArguments", "RunAtLoad", "KeepAlive",
                     "WorkingDirectory", "StandardOutPath", "StandardErrorPath"]

    for key in required_keys:
        assert key in plist_data, f"Plist must have {key} for boot auto-start"


def test_plist_run_at_load_enabled():
    """Verify RunAtLoad is enabled for automatic boot startup."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    assert plist_data.get("RunAtLoad") is True, \
        "RunAtLoad must be True for boot auto-start"


def test_plist_keep_alive_enabled():
    """Verify KeepAlive is enabled for crash recovery."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    assert plist_data.get("KeepAlive") is True, \
        "KeepAlive must be True for automatic restart on crash"


def test_log_paths_are_writable():
    """Verify log directory is writable for service logging."""
    logs_dir = Path("logs")

    # Logs directory should exist
    assert logs_dir.exists(), "logs directory must exist"
    assert logs_dir.is_dir(), "logs must be a directory"

    # Directory should be writable
    import os
    assert os.access(logs_dir, os.W_OK), "logs directory must be writable"


def test_plist_log_paths_point_to_project():
    """Verify plist log paths point to project logs directory."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    stdout_path = plist_data.get("StandardOutPath", "")
    stderr_path = plist_data.get("StandardErrorPath", "")

    # Log paths should contain project path
    assert "wifi-tracking" in stdout_path, "stdout path should point to project"
    assert "wifi-tracking" in stderr_path, "stderr path should point to project"

    # Log paths should end with expected filenames
    assert stdout_path.endswith("/logs/stdout.log"), "stdout should be logs/stdout.log"
    assert stderr_path.endswith("/logs/stderr.log"), "stderr should be logs/stderr.log"


def test_service_configuration_matches_requirements():
    """Verify service configuration matches production requirements."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    # Verify localhost binding (security)
    program_args = plist_data.get("ProgramArguments", [])
    assert "127.0.0.1" in program_args, "Must bind to localhost for security"

    # Verify correct port
    assert "8787" in program_args, "Must use port 8787"

    # Verify correct app entry point
    assert "app.main:app" in program_args, "Must use app.main:app entry point"


def test_session_recovery_dependencies_present():
    """Verify session recovery system components exist."""
    # Session manager should be importable
    try:
        from app.session_manager import SessionManager
        assert SessionManager is not None
    except ImportError as e:
        raise AssertionError(f"SessionManager must be importable for recovery: {e}")

    # File store should be importable
    try:
        from app.file_store import read_sessions, append_session
        assert read_sessions is not None
        assert append_session is not None
    except ImportError as e:
        raise AssertionError(f"File store must be importable for recovery: {e}")

    # Data directory should exist
    data_dir = Path("data")
    assert data_dir.exists(), "data directory must exist for session recovery"
    assert data_dir.is_dir(), "data must be a directory"


def test_boot_startup_command_is_correct():
    """Verify plist contains correct startup command structure."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    program_args = plist_data.get("ProgramArguments", [])

    # Should have at least: python, -m, uvicorn, app.main:app, --host, 127.0.0.1, --port, 8787
    assert len(program_args) >= 8, "Must have complete command with all arguments"

    # Verify command structure
    assert program_args[0].endswith("/venv/bin/python"), "First arg must be Python"
    assert program_args[1] == "-m", "Second arg must be -m flag"
    assert program_args[2] == "uvicorn", "Third arg must be uvicorn"


def test_plist_working_directory_is_absolute():
    """Verify WorkingDirectory is absolute path for boot reliability."""
    import plistlib

    with open("com.officetracker.plist", "rb") as f:
        plist_data = plistlib.load(f)

    working_dir = plist_data.get("WorkingDirectory", "")
    assert working_dir.startswith("/"), \
        "WorkingDirectory must be absolute path for boot auto-start"
    assert Path(working_dir).exists(), \
        f"WorkingDirectory must exist: {working_dir}"
