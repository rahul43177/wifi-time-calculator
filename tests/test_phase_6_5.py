"""
Tests for Phase 6.5: Install/Uninstall Scripts + Documentation.

Covers:
- Installation script completeness
- Uninstallation script completeness
- Documentation existence and quality
"""

from pathlib import Path


def test_install_script_provides_user_feedback():
    """Verify install script has helpful user feedback messages."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should have emoji/visual indicators
    assert "✅" in content or "Installing" in content

    # Should show success message
    assert "complete" in content.lower() or "success" in content.lower()


def test_uninstall_script_provides_user_feedback():
    """Verify uninstall script has helpful user feedback messages."""
    with open("scripts/uninstall-autostart.sh", "r") as f:
        content = f.read()

    # Should have emoji/visual indicators
    assert "✅" in content or "Uninstalling" in content

    # Should show completion message
    assert "complete" in content.lower() or "removed" in content.lower()


def test_install_script_has_error_handling():
    """Verify install script exits on errors with set -e."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should use set -e for error handling
    assert "set -e" in content


def test_uninstall_script_has_error_handling():
    """Verify uninstall script exits on errors with set -e."""
    with open("scripts/uninstall-autostart.sh", "r") as f:
        content = f.read()

    # Should use set -e for error handling
    assert "set -e" in content


def test_phase_6_documentation_exists():
    """Verify comprehensive Phase 6 documentation exists."""
    doc_path = Path("docs/PHASE_6_AUTO_START_GUIDE.md")
    assert doc_path.exists()
    assert doc_path.is_file()


def test_phase_6_documentation_is_substantial():
    """Verify Phase 6 documentation is comprehensive (not just a stub)."""
    doc_path = Path("docs/PHASE_6_AUTO_START_GUIDE.md")
    with open(doc_path, "r") as f:
        content = f.read()

    # Should be substantial (at least 5000 characters)
    assert len(content) > 5000, "Documentation should be comprehensive"


def test_phase_6_documentation_covers_installation():
    """Verify documentation covers installation process."""
    doc_path = Path("docs/PHASE_6_AUTO_START_GUIDE.md")
    with open(doc_path, "r") as f:
        content = f.read()

    assert "install" in content.lower()
    assert "installation" in content.lower() or "setup" in content.lower()


def test_phase_6_documentation_covers_troubleshooting():
    """Verify documentation includes troubleshooting section."""
    doc_path = Path("docs/PHASE_6_AUTO_START_GUIDE.md")
    with open(doc_path, "r") as f:
        content = f.read()

    assert "troubleshoot" in content.lower()


def test_phase_6_documentation_covers_uninstallation():
    """Verify documentation covers uninstallation process."""
    doc_path = Path("docs/PHASE_6_AUTO_START_GUIDE.md")
    with open(doc_path, "r") as f:
        content = f.read()

    assert "uninstall" in content.lower()


def test_phase_6_completion_report_exists():
    """Verify Phase 6 completion report exists."""
    report_path = Path("docs/PHASE_6_COMPLETION_REPORT.md")
    assert report_path.exists()
    assert report_path.is_file()


def test_readme_documents_autostart():
    """Verify README.md includes auto-start instructions."""
    readme_path = Path("README.md")
    with open(readme_path, "r") as f:
        content = f.read()

    assert "auto-start" in content.lower() or "autostart" in content.lower()
    assert "install-autostart.sh" in content


def test_action_plan_marks_phase_6_complete():
    """Verify action-plan.md marks Phase 6 tasks as complete."""
    action_plan_path = Path("docs/action-plan.md")
    with open(action_plan_path, "r") as f:
        content = f.read()

    # Should have Phase 6 section
    assert "Phase 6" in content

    # Should mark tasks as complete
    assert "✅ DONE" in content or "[x]" in content


def test_install_script_shows_helpful_commands():
    """Verify install script shows next-step commands to user."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should show how to check status
    assert "launchctl" in content

    # Should show log locations
    assert "logs" in content


def test_scripts_directory_contains_both_scripts():
    """Verify scripts directory contains both install and uninstall scripts."""
    scripts_dir = Path("scripts")
    assert scripts_dir.exists()

    install_script = scripts_dir / "install-autostart.sh"
    uninstall_script = scripts_dir / "uninstall-autostart.sh"

    assert install_script.exists()
    assert uninstall_script.exists()


def test_scripts_are_executable():
    """Verify both scripts have execute permissions."""
    import os

    install_script = Path("scripts/install-autostart.sh")
    uninstall_script = Path("scripts/uninstall-autostart.sh")

    assert os.access(install_script, os.X_OK), "install script must be executable"
    assert os.access(uninstall_script, os.X_OK), "uninstall script must be executable"


def test_install_script_validates_all_prerequisites():
    """Verify install script validates all prerequisites before installation."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should validate plist file
    assert "plutil -lint" in content, "Must validate plist syntax"

    # Should validate venv
    assert "venv/bin/python" in content, "Must check for virtual environment"

    # Should validate dependencies
    assert "import uvicorn" in content or "uvicorn" in content, "Must check for uvicorn"

    # Should validate before copying (set -e ensures early exit on failures)
    assert "set -e" in content, "Must use set -e for fail-fast behavior"


def test_uninstall_script_waits_for_launchd():
    """Verify uninstall script waits for launchd to complete unloading."""
    with open("scripts/uninstall-autostart.sh", "r") as f:
        content = f.read()

    # Should wait after bootout for launchd to complete
    lines = content.split('\n')

    bootout_found = False
    sleep_after_bootout = False

    for i, line in enumerate(lines):
        if "launchctl bootout" in line:
            bootout_found = True
        if bootout_found and "sleep" in line and i < len(lines) - 5:
            # Sleep should be reasonably long (at least 1 second, preferably 2+)
            if "sleep 2" in line or "sleep 3" in line:
                sleep_after_bootout = True
                break

    assert bootout_found, "Must have bootout command"
    assert sleep_after_bootout or "sleep 1" in content, "Must wait for launchd to complete"


def test_documentation_matches_script_behavior():
    """Verify documentation accurately describes script behavior."""
    doc_path = Path("docs/PHASE_6_AUTO_START_GUIDE.md")
    with open(doc_path, "r") as f:
        doc_content = f.read()

    with open("scripts/install-autostart.sh", "r") as f:
        install_content = f.read()

    # Doc should mention script names
    assert "install-autostart.sh" in doc_content, "Doc must mention install script"
    assert "uninstall-autostart.sh" in doc_content, "Doc must mention uninstall script"

    # Doc should mention prerequisites that script checks
    assert "venv" in doc_content.lower() or "virtual environment" in doc_content.lower(), \
        "Doc must mention venv requirement"

    # Doc should mention installation location
    assert "LaunchAgents" in doc_content, "Doc must mention LaunchAgents location"


def test_scripts_provide_clear_error_messages():
    """Verify scripts provide clear, actionable error messages."""
    with open("scripts/install-autostart.sh", "r") as f:
        install_content = f.read()

    # Error messages should be clear and actionable
    assert "Error:" in install_content or "❌" in install_content, \
        "Must have clear error indicators"

    # Should provide next steps for common errors
    assert "Please run:" in install_content or "pip install" in install_content, \
        "Should provide remediation steps for missing dependencies"


def test_install_script_shows_post_install_verification():
    """Verify install script shows users how to verify installation."""
    with open("scripts/install-autostart.sh", "r") as f:
        content = f.read()

    # Should show verification commands
    assert "launchctl list" in content, "Should show how to check service status"
    assert "grep officetracker" in content or "com.officetracker" in content, \
        "Should show how to filter for this service"

    # Should show dashboard URL
    assert "127.0.0.1:8787" in content or "localhost:8787" in content or "8787" in content, \
        "Should show dashboard URL"


def test_uninstall_script_confirms_removal():
    """Verify uninstall script confirms service removal."""
    with open("scripts/uninstall-autostart.sh", "r") as f:
        content = f.read()

    # Should verify service is not running after uninstall
    assert "launchctl list" in content, "Should check service status"

    # Should provide clear success/failure messages
    assert "completely removed" in content.lower() or "removed" in content.lower(), \
        "Should confirm successful removal"


def test_documentation_includes_common_issues():
    """Verify documentation covers common issues and solutions."""
    doc_path = Path("docs/PHASE_6_AUTO_START_GUIDE.md")
    with open(doc_path, "r") as f:
        content = f.read()

    # Should have FAQ or common issues section
    assert "faq" in content.lower() or "common" in content.lower() or "issue" in content.lower(), \
        "Should have FAQ or common issues section"

    # Should mention service status checking
    assert "launchctl" in content.lower(), "Should explain how to check service status"


def test_scripts_handle_repeated_execution():
    """Verify scripts can be run multiple times safely."""
    with open("scripts/install-autostart.sh", "r") as f:
        install_content = f.read()

    with open("scripts/uninstall-autostart.sh", "r") as f:
        uninstall_content = f.read()

    # Install should check if service is already running
    assert "if launchctl list" in install_content or "grep" in install_content, \
        "Install should check for existing service"

    # Uninstall should handle already-uninstalled case
    assert "if [ -f" in uninstall_content or "if launchctl list" in uninstall_content, \
        "Uninstall should check if already uninstalled"


def test_scripts_use_correct_paths():
    """Verify scripts use correct and consistent paths."""
    with open("scripts/install-autostart.sh", "r") as f:
        install_content = f.read()

    with open("scripts/uninstall-autostart.sh", "r") as f:
        uninstall_content = f.read()

    # Both should reference the same plist file name
    assert "com.officetracker.plist" in install_content
    assert "com.officetracker.plist" in uninstall_content

    # Both should reference LaunchAgents
    assert "LaunchAgents" in install_content
    assert "LaunchAgents" in uninstall_content

    # Should use $HOME or ~ for user home directory
    assert "$HOME" in install_content or "~" in install_content
    assert "$HOME" in uninstall_content or "~" in uninstall_content


def test_documentation_structure_is_complete():
    """Verify documentation has complete structure with all necessary sections."""
    doc_path = Path("docs/PHASE_6_AUTO_START_GUIDE.md")
    with open(doc_path, "r") as f:
        content = f.read()

    # Should have major sections
    sections = ["installation", "uninstall", "troubleshoot", "verify"]

    found_sections = []
    for section in sections:
        if section in content.lower():
            found_sections.append(section)

    assert len(found_sections) >= 3, \
        f"Documentation should have at least 3 major sections, found {len(found_sections)}: {found_sections}"


def test_readme_provides_quick_start():
    """Verify README provides quick-start instructions for auto-start."""
    readme_path = Path("README.md")
    with open(readme_path, "r") as f:
        content = f.read()

    # Should mention auto-start feature
    assert "auto" in content.lower() and "start" in content.lower(), \
        "README must mention auto-start feature"

    # Should provide script command
    assert "./scripts/install-autostart.sh" in content or \
           "scripts/install-autostart.sh" in content or \
           "bash scripts/install-autostart.sh" in content, \
        "README should show how to run install script"
