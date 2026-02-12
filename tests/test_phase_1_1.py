"""
Tests for Phase 1.1: SSID Detection for macOS.

Verifies that get_current_ssid() and its internal methods work correctly.
"""

from unittest.mock import patch, MagicMock
import subprocess

from app.wifi_detector import (
    get_current_ssid,
    _get_ssid_via_networksetup,
    _get_ssid_via_system_profiler,
)


# --- _get_ssid_via_networksetup tests ---


def test_networksetup_returns_ssid():
    """Parses SSID correctly from networksetup output."""
    mock_result = MagicMock(
        returncode=0,
        stdout="Current Wi-Fi Network: OfficeWifi\n",
    )
    with patch("app.wifi_detector.subprocess.run", return_value=mock_result):
        assert _get_ssid_via_networksetup() == "OfficeWifi"


def test_networksetup_not_associated():
    """Returns None when not connected."""
    mock_result = MagicMock(
        returncode=0,
        stdout="You are not associated with an AirPort network.\n",
    )
    with patch("app.wifi_detector.subprocess.run", return_value=mock_result):
        assert _get_ssid_via_networksetup() is None


def test_networksetup_timeout():
    """Returns None on timeout instead of crashing."""
    with patch(
        "app.wifi_detector.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="networksetup", timeout=5),
    ):
        assert _get_ssid_via_networksetup() is None


def test_networksetup_command_not_found():
    """Returns None if command doesn't exist."""
    with patch(
        "app.wifi_detector.subprocess.run",
        side_effect=FileNotFoundError(),
    ):
        assert _get_ssid_via_networksetup() is None


# --- _get_ssid_via_system_profiler tests ---


SYSTEM_PROFILER_OUTPUT = """\
Wi-Fi:

      Software Versions:
          CoreWLAN: 16.0 (1657)
      Interfaces:
        en0:
          Status: Connected
          Current Network Information:
            MyOfficeNetwork:
              PHY Mode: 802.11ax
              Channel: 149 (5GHz, 80MHz)
"""


def test_system_profiler_returns_ssid():
    """Parses SSID from system_profiler output."""
    mock_result = MagicMock(returncode=0, stdout=SYSTEM_PROFILER_OUTPUT)
    with patch("app.wifi_detector.subprocess.run", return_value=mock_result):
        assert _get_ssid_via_system_profiler() == "MyOfficeNetwork"


def test_system_profiler_no_network():
    """Returns None when no current network section exists."""
    mock_result = MagicMock(
        returncode=0,
        stdout="Wi-Fi:\n      Status: Disconnected\n",
    )
    with patch("app.wifi_detector.subprocess.run", return_value=mock_result):
        assert _get_ssid_via_system_profiler() is None


def test_system_profiler_command_failure():
    """Returns None when command returns non-zero exit code."""
    mock_result = MagicMock(returncode=1, stdout="")
    with patch("app.wifi_detector.subprocess.run", return_value=mock_result):
        assert _get_ssid_via_system_profiler() is None


def test_system_profiler_timeout():
    """Returns None on timeout."""
    with patch(
        "app.wifi_detector.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="system_profiler", timeout=10),
    ):
        assert _get_ssid_via_system_profiler() is None


# --- get_current_ssid (combined) tests ---


def test_get_current_ssid_uses_networksetup_first():
    """Uses networksetup when it succeeds."""
    with patch("app.wifi_detector._get_ssid_via_networksetup", return_value="FastWifi"):
        with patch("app.wifi_detector._get_ssid_via_system_profiler") as fallback:
            assert get_current_ssid() == "FastWifi"
            fallback.assert_not_called()


def test_get_current_ssid_falls_back_to_system_profiler():
    """Falls back to system_profiler when networksetup returns None."""
    with patch("app.wifi_detector._get_ssid_via_networksetup", return_value=None):
        with patch(
            "app.wifi_detector._get_ssid_via_system_profiler",
            return_value="SlowWifi",
        ):
            assert get_current_ssid() == "SlowWifi"


def test_get_current_ssid_returns_none_when_both_fail():
    """Returns None when both methods fail."""
    with patch("app.wifi_detector._get_ssid_via_networksetup", return_value=None):
        with patch("app.wifi_detector._get_ssid_via_system_profiler", return_value=None):
            assert get_current_ssid() is None
