"""
Tests for Phase 6.2: Install Launch Agent.

Covers:
- Installation script validation
- Launch agent loading verification
- Service status checks
"""

import os
import subprocess
from pathlib import Path


def test_install_script_exists():
    """Verify install-autostart.sh exists and is executable."""
    script_path = Path("scripts/install-autostart.sh")
    assert script_path.exists()
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK), "Install script should be executable"


def test_uninstall_script_exists():
    """Verify uninstall-autostart.sh exists and is executable."""
    script_path = Path("scripts/uninstall-autostart.sh")
    assert script_path.exists()
    assert script_path.is_file()
    assert os.access(script_path, os.X_OK), "Uninstall script should be executable"


def test_install_script_has_shebang():
    """Verify install script has proper bash shebang."""
    with open("scripts/install-autostart.sh", "r") as f:
        first_line = f.readline().strip()
    assert first_line == "#!/bin/bash"


def test_uninstall_script_has_shebang():
    """Verify uninstall script has proper bash shebang."""
    with open("scripts/uninstall-autostart.sh", "r") as f:
        first_line = f.readline().strip()
    assert first_line == "#!/bin/bash"


def test_install_script_validates_plist():
    """Verify install script contains plist validation logic."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()
    assert "plutil -lint" in content
    assert "com.officetracker.plist" in content


def test_install_script_validates_venv():
    """Verify install script checks for virtual environment."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()
    assert "venv/bin/python" in content
    assert "virtual environment" in content.lower()


def test_install_script_validates_dependencies():
    """Verify install script checks for uvicorn dependency."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()
    assert "uvicorn" in content


def test_install_script_creates_launch_agents_dir():
    """Verify install script creates LaunchAgents directory if needed."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()
    assert "LaunchAgents" in content
    assert "mkdir" in content


def test_install_script_copies_plist():
    """Verify install script copies plist to LaunchAgents."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()
    assert "cp" in content
    assert "LaunchAgents" in content


def test_install_script_uses_modern_bootstrap():
    """Verify install script uses modern launchctl bootstrap (not legacy load)."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()
    assert "launchctl bootstrap" in content, "Should use modern 'bootstrap' command"
    assert "gui/$(id -u)" in content, "Should use gui domain with user ID"


def test_uninstall_script_uses_modern_bootout():
    """Verify uninstall script uses modern launchctl bootout (not legacy unload)."""
    with open("scripts/uninstall-autostart.sh", "r") as f:
        content = f.read()
    assert "launchctl bootout" in content, "Should use modern 'bootout' command"
    assert "gui/$(id -u)" in content, "Should use gui domain with user ID"


def test_uninstall_script_removes_plist():
    """Verify uninstall script removes plist file."""
    with open("scripts/uninstall-autostart.sh", "r") as f:
        content = f.read()
    assert "rm" in content
    assert "LaunchAgents" in content


def test_launch_agents_path_is_user_level():
    """Verify scripts use user-level LaunchAgents, not system-level LaunchDaemons."""
    with open("scripts/install-autostart.sh", "r") as f:
        install_content = f.read()

    # Should use ~/Library/LaunchAgents (user-level)
    assert "LaunchAgents" in install_content
    # Should NOT use /Library/LaunchDaemons (system-level, requires sudo)
    assert "/Library/LaunchDaemons" not in install_content


def test_install_script_handles_copy_failures():
    """Verify install script checks for copy operation failures."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should check if cp command succeeded
    assert "if ! cp" in content or "if cp" in content, "Should check cp command result"
    assert "permission denied" in content.lower() or "failed to copy" in content.lower(), \
        "Should provide helpful error message for copy failures"


def test_install_script_handles_bootstrap_failures():
    """Verify install script handles bootstrap command failures gracefully."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should check if bootstrap succeeded
    assert "if launchctl bootstrap" in content, "Should check bootstrap command result"
    # Should have error handling for bootstrap failure
    assert "Failed to load service" in content or "failed" in content.lower(), \
        "Should provide error message for bootstrap failures"


def test_install_script_provides_diagnostic_info_on_failure():
    """Verify install script provides diagnostic info when service fails to load."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should mention log files for troubleshooting
    assert "logs/stderr.log" in content or "tail -f" in content, \
        "Should direct users to log files for troubleshooting"


def test_uninstall_script_is_idempotent():
    """Verify uninstall script can be run multiple times safely."""
    with open("scripts/uninstall-autostart.sh", "r") as f:
        content = f.read()

    # Should check if service exists before unloading
    assert "if launchctl list | grep" in content, "Should check if service is running"
    # Should check if plist exists before removing
    assert "if [ -f" in content, "Should check if plist file exists"
    # Should have informational messages for already-removed state
    assert "already removed" in content.lower() or "not running" in content.lower(), \
        "Should handle already-uninstalled state gracefully"


def test_install_script_handles_already_loaded_service():
    """Verify install script handles service that's already loaded."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should check if service is already running
    assert "launchctl list | grep" in content, "Should check for existing service"
    # Should attempt to unload before installing
    assert "bootout" in content or "Unloading existing" in content, \
        "Should handle already-loaded service"


def test_scripts_use_absolute_paths():
    """Verify scripts resolve to absolute paths for reliability."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should compute PROJECT_DIR as absolute path
    assert "PROJECT_DIR=" in content, "Should define PROJECT_DIR variable"
    assert "$(cd" in content or "$(dirname" in content, \
        "Should compute absolute path for project directory"


def test_install_script_validates_before_install():
    """Verify install script validates all prerequisites before making changes."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Find line numbers for validation and installation steps
    lines = content.split('\n')

    validation_checks = []
    install_line = None

    for i, line in enumerate(lines):
        if "plutil -lint" in line:
            validation_checks.append(("plist", i))
        if "venv/bin/python" in line and "if [ ! -f" in line:
            validation_checks.append(("venv", i))
        if "import uvicorn" in line:
            validation_checks.append(("dependencies", i))
        if "cp" in line and "DEST_PLIST" in line and "echo" not in line:
            install_line = i

    # All validations should happen before installation
    if install_line:
        for check_name, check_line in validation_checks:
            assert check_line < install_line, \
                f"{check_name} validation (line {check_line}) should happen before install (line {install_line})"


def test_install_script_provides_post_install_instructions():
    """Verify install script provides helpful next-step commands."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should show how to check service status
    assert "launchctl list" in content, "Should show status check command"
    # Should show log locations
    assert "tail -f" in content, "Should show how to view logs"
    # Should mention dashboard URL
    assert "http://127.0.0.1:8787" in content or "8787" in content, \
        "Should mention dashboard URL"


def test_scripts_have_proper_error_exit_codes():
    """Verify scripts exit with non-zero codes on errors."""
    with open("scripts/install-autostart.sh", "r") as f:
        install_content = f.read()

    # Should have set -e for automatic error exits
    assert "set -e" in install_content, "Install script should use 'set -e'"

    # Should have explicit exit 1 for critical errors
    assert "exit 1" in install_content, "Install script should exit with code 1 on errors"

    with open("scripts/uninstall-autostart.sh", "r") as f:
        uninstall_content = f.read()

    assert "set -e" in uninstall_content, "Uninstall script should use 'set -e'"


def test_install_script_waits_for_service_startup():
    """Verify install script waits for service to start before declaring success."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should have sleep or wait after loading service
    assert "sleep" in content, "Should wait for service to start"
    # Should verify service is running after load
    lines = content.split('\n')

    bootstrap_line = None
    verify_line = None

    for i, line in enumerate(lines):
        if "launchctl bootstrap" in line:
            bootstrap_line = i
        if bootstrap_line and "launchctl list" in line and i > bootstrap_line:
            verify_line = i
            break

    assert verify_line is not None, "Should verify service status after bootstrap"
    assert verify_line > bootstrap_line, "Verification should happen after bootstrap"


def test_uninstall_script_waits_for_service_shutdown():
    """Verify uninstall script waits for service to stop before declaring success."""
    with open("scripts/uninstall-autostart.sh", "r") as f:
        content = f.read()

    # Should have sleep or wait after stopping service
    assert "sleep" in content, "Should wait for service to stop"
    # Should verify service is not running after bootout
    assert "launchctl list" in content, "Should verify service status"


def test_install_script_creates_directories_safely():
    """Verify install script creates directories with proper error handling."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should use mkdir -p for safe directory creation
    assert "mkdir -p" in content, "Should use 'mkdir -p' for safe directory creation"
    # Should create LaunchAgents directory
    assert "LaunchAgents" in content, "Should reference LaunchAgents directory"
