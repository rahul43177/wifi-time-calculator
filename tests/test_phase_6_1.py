"""
Tests for Phase 6.1: launchd Plist File.

Verifies that the plist file exists, is valid, and contains correct production settings
for automatic startup on macOS login.

Coverage:
- Plist file existence and syntax validation
- Semantic correctness (RunAtLoad, KeepAlive, paths, arguments)
- Boot flow configuration validation
- Error handling for malformed configurations
"""

import os
import plistlib
from pathlib import Path


def test_plist_file_exists():
    """Verify that com.officetracker.plist exists in the root directory."""
    plist_path = Path("com.officetracker.plist")
    assert plist_path.exists(), "Plist file must exist in project root"
    assert plist_path.is_file(), "Plist path must be a file, not a directory"


def test_plist_syntax_via_plutil():
    """Verify that the plist passes macOS native syntax check."""
    exit_code = os.system("plutil -lint com.officetracker.plist > /dev/null 2>&1")
    assert exit_code == 0, "Plist must pass plutil -lint validation"


def test_plist_semantic_validation():
    """Use plistlib to verify the semantic structure and flags of the plist."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    # Basic structure
    assert isinstance(data, dict), "Plist root must be a dictionary"

    # Required keys exist
    assert "Label" in data, "Label key is required"
    assert "ProgramArguments" in data, "ProgramArguments key is required"
    assert "WorkingDirectory" in data, "WorkingDirectory key is required"
    assert "RunAtLoad" in data, "RunAtLoad key is required"
    assert "KeepAlive" in data, "KeepAlive key is required"
    assert "StandardOutPath" in data, "StandardOutPath key is required"
    assert "StandardErrorPath" in data, "StandardErrorPath key is required"


def test_plist_label_is_correct():
    """Verify Label follows reverse-DNS naming convention."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    label = data["Label"]
    assert label == "com.officetracker", f"Label must be 'com.officetracker', got '{label}'"
    assert isinstance(label, str), "Label must be a string"
    assert label.startswith("com."), "Label should follow reverse-DNS convention"


def test_plist_run_at_load_is_true():
    """Verify RunAtLoad is boolean true for automatic startup on login."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    run_at_load = data["RunAtLoad"]
    assert run_at_load is True, "RunAtLoad must be boolean True for auto-start"
    assert isinstance(run_at_load, bool), "RunAtLoad must be boolean, not string 'true'"


def test_plist_keep_alive_is_true():
    """Verify KeepAlive is boolean true for automatic restart on crash."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    keep_alive = data["KeepAlive"]
    assert keep_alive is True, "KeepAlive must be boolean True for crash recovery"
    assert isinstance(keep_alive, bool), "KeepAlive must be boolean, not string 'true'"


def test_plist_program_arguments_structure():
    """Verify ProgramArguments is a list with required elements."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    args = data["ProgramArguments"]
    assert isinstance(args, list), "ProgramArguments must be a list"
    assert len(args) > 0, "ProgramArguments cannot be empty"


def test_plist_program_arguments_contains_python():
    """Verify ProgramArguments includes Python executable from venv."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    args = data["ProgramArguments"]
    python_path = args[0]

    assert "venv/bin/python" in python_path, "First argument must be venv Python executable"
    assert python_path.endswith("/venv/bin/python"), "Python path must end with /venv/bin/python"


def test_plist_program_arguments_contains_uvicorn():
    """Verify ProgramArguments includes uvicorn module invocation."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    args = data["ProgramArguments"]

    # Should have: python -m uvicorn app.main:app
    assert "-m" in args, "ProgramArguments must include -m flag for module execution"
    assert "uvicorn" in args, "ProgramArguments must include uvicorn module"


def test_plist_program_arguments_contains_app_module():
    """Verify ProgramArguments includes app.main:app FastAPI application."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    args = data["ProgramArguments"]
    assert "app.main:app" in args, "ProgramArguments must include app.main:app"


def test_plist_program_arguments_contains_host():
    """Verify ProgramArguments includes host binding to localhost."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    args = data["ProgramArguments"]
    assert "--host" in args, "ProgramArguments must include --host flag"
    assert "127.0.0.1" in args, "ProgramArguments must bind to 127.0.0.1 (localhost)"


def test_plist_program_arguments_contains_port():
    """Verify ProgramArguments includes port 8787."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    args = data["ProgramArguments"]
    assert "--port" in args, "ProgramArguments must include --port flag"
    assert "8787" in args, "ProgramArguments must specify port 8787"


def test_plist_working_directory_is_project_root():
    """Verify WorkingDirectory points to project root."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    working_dir = data["WorkingDirectory"]
    assert isinstance(working_dir, str), "WorkingDirectory must be a string"
    assert "wifi-tracking" in working_dir, "WorkingDirectory must be the project directory"
    assert not working_dir.endswith("/"), "WorkingDirectory should not end with slash"


def test_plist_stdout_log_path_is_valid():
    """Verify StandardOutPath points to logs directory."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    stdout_path = data["StandardOutPath"]
    assert isinstance(stdout_path, str), "StandardOutPath must be a string"
    assert "logs/stdout.log" in stdout_path, "StandardOutPath must point to logs/stdout.log"
    assert stdout_path.endswith("/logs/stdout.log"), "StandardOutPath must end with /logs/stdout.log"


def test_plist_stderr_log_path_is_valid():
    """Verify StandardErrorPath points to logs directory."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    stderr_path = data["StandardErrorPath"]
    assert isinstance(stderr_path, str), "StandardErrorPath must be a string"
    assert "logs/stderr.log" in stderr_path, "StandardErrorPath must point to logs/stderr.log"
    assert stderr_path.endswith("/logs/stderr.log"), "StandardErrorPath must end with /logs/stderr.log"


def test_plist_log_directories_exist():
    """Verify log directories referenced in plist exist."""
    logs_dir = Path("logs")
    assert logs_dir.exists(), "logs/ directory must exist for StandardOutPath/StandardErrorPath"
    assert logs_dir.is_dir(), "logs/ must be a directory"


def test_plist_python_executable_path_exists():
    """Verify Python executable referenced in plist exists."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    args = data["ProgramArguments"]
    python_path = Path(args[0])

    assert python_path.exists(), f"Python executable must exist at {python_path}"
    assert python_path.is_file(), f"Python path must be a file at {python_path}"
    assert os.access(python_path, os.X_OK), f"Python executable must be executable at {python_path}"


def test_plist_working_directory_exists():
    """Verify WorkingDirectory referenced in plist exists."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    working_dir = Path(data["WorkingDirectory"])
    assert working_dir.exists(), f"WorkingDirectory must exist at {working_dir}"
    assert working_dir.is_dir(), f"WorkingDirectory must be a directory at {working_dir}"


def test_plist_has_no_extra_unexpected_keys():
    """Verify plist doesn't have unexpected/risky keys."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    # These keys should NOT be present (security/safety)
    unsafe_keys = ["UserName", "GroupName", "RootDirectory", "Umask", "SessionCreate"]
    for key in unsafe_keys:
        assert key not in data, f"Plist should not contain {key} (security risk)"


def test_plist_program_arguments_order_is_correct():
    """Verify ProgramArguments are in correct execution order."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    args = data["ProgramArguments"]

    # Expected order: python, -m, uvicorn, app.main:app, --host, 127.0.0.1, --port, 8787
    assert args[1] == "-m", "Second argument must be -m"
    assert args[2] == "uvicorn", "Third argument must be uvicorn"

    # Find --host and verify next element is IP
    host_idx = args.index("--host")
    assert args[host_idx + 1] == "127.0.0.1", "Host value must follow --host flag"

    # Find --port and verify next element is port number
    port_idx = args.index("--port")
    assert args[port_idx + 1] == "8787", "Port value must follow --port flag"


def test_plist_paths_are_absolute():
    """Verify all paths in plist are absolute, not relative."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    # Check all path fields are absolute
    python_path = data["ProgramArguments"][0]
    working_dir = data["WorkingDirectory"]
    stdout_path = data["StandardOutPath"]
    stderr_path = data["StandardErrorPath"]

    assert python_path.startswith("/"), "Python path must be absolute"
    assert working_dir.startswith("/"), "WorkingDirectory must be absolute"
    assert stdout_path.startswith("/"), "StandardOutPath must be absolute"
    assert stderr_path.startswith("/"), "StandardErrorPath must be absolute"


def test_plist_boot_flow_configuration():
    """Verify plist is configured for proper boot flow behavior."""
    with open("com.officetracker.plist", "rb") as f:
        data = plistlib.load(f)

    # Must have RunAtLoad for boot-time startup
    assert data["RunAtLoad"] is True, "RunAtLoad required for auto-start on login"

    # Must have KeepAlive for crash recovery
    assert data["KeepAlive"] is True, "KeepAlive required for automatic restart"

    # Must have proper logging for debugging boot issues
    assert "StandardOutPath" in data, "StandardOutPath required for boot diagnostics"
    assert "StandardErrorPath" in data, "StandardErrorPath required for boot error diagnosis"

    # Must NOT have StartInterval (would cause repeated restarts)
    assert "StartInterval" not in data, "StartInterval should not be present (causes restart loops)"


def test_plist_file_size_is_reasonable():
    """Verify plist file size is reasonable (not corrupted or malformed)."""
    plist_path = Path("com.officetracker.plist")
    file_size = plist_path.stat().st_size

    # Should be between 500 bytes and 10KB
    assert 500 < file_size < 10240, f"Plist file size {file_size} bytes seems unusual (expected 500-10KB)"
