"""
Tests for Phase 1.4: Logging Configuration.

Verifies that setup_logging configures console and file handlers correctly,
respects log levels, and creates log directories as needed.
"""

import logging
import os
import tempfile
from unittest.mock import patch

import pytest

import app.main as main_module
from app.main import setup_logging, LOG_FORMAT


def _our_handlers(root: logging.Logger) -> list[logging.Handler]:
    """Return only handlers added by setup_logging (exclude pytest's LogCaptureHandler)."""
    return [h for h in root.handlers if type(h) in (
        logging.StreamHandler, logging.FileHandler,
        logging.handlers.RotatingFileHandler,
    )]


@pytest.fixture(autouse=True)
def _reset_logging():
    """Reset the _logging_configured flag and remove our handlers before each test."""
    main_module._logging_configured = False
    root = logging.getLogger()
    # Remove only our handlers, leave pytest's in place
    for h in list(root.handlers):
        if type(h) in (logging.StreamHandler, logging.FileHandler,
                        logging.handlers.RotatingFileHandler):
            root.removeHandler(h)
            h.close()
    yield
    # Cleanup after test
    main_module._logging_configured = False
    for h in list(root.handlers):
        if type(h) in (logging.StreamHandler, logging.FileHandler,
                        logging.handlers.RotatingFileHandler):
            root.removeHandler(h)
            h.close()


# --- Console handler tests ---


def test_console_handler_added():
    """setup_logging adds a StreamHandler to the root logger."""
    with patch("app.main.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.log_to_file = False
        setup_logging()

    root = logging.getLogger()
    stream_handlers = [h for h in _our_handlers(root)
                       if isinstance(h, logging.StreamHandler)
                       and not isinstance(h, logging.FileHandler)]
    assert len(stream_handlers) == 1


def test_console_handler_has_correct_format():
    """Console handler uses the expected log format."""
    with patch("app.main.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.log_to_file = False
        setup_logging()

    root = logging.getLogger()
    our = _our_handlers(root)
    assert len(our) >= 1
    assert our[0].formatter._fmt == LOG_FORMAT


def test_log_level_applied():
    """Root logger respects the configured log level."""
    with patch("app.main.settings") as mock_settings:
        mock_settings.log_level = "WARNING"
        mock_settings.log_to_file = False
        setup_logging()

    root = logging.getLogger()
    assert root.level == logging.WARNING


def test_log_level_debug():
    """DEBUG level is set correctly."""
    with patch("app.main.settings") as mock_settings:
        mock_settings.log_level = "DEBUG"
        mock_settings.log_to_file = False
        setup_logging()

    root = logging.getLogger()
    assert root.level == logging.DEBUG


def test_no_duplicate_handlers_on_reload():
    """Calling setup_logging twice doesn't add duplicate handlers."""
    with patch("app.main.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.log_to_file = False
        setup_logging()
        main_module._logging_configured = False  # simulate reload
        setup_logging()  # should be blocked by flag (reset above, but called once already)

    # First call sets flag, second call is a no-op because we didn't reset between
    # Let's test properly: call once, then call again without reset
    main_module._logging_configured = False
    root = logging.getLogger()
    for h in list(root.handlers):
        if type(h) in (logging.StreamHandler,):
            root.removeHandler(h)

    with patch("app.main.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.log_to_file = False
        setup_logging()
        # Second call should be blocked by the flag
        setup_logging()

    assert len(_our_handlers(root)) == 1


# --- File handler tests ---


def test_file_handler_added_when_enabled():
    """File handler is added when log_to_file is True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        with patch("app.main.settings") as mock_settings:
            mock_settings.log_level = "INFO"
            mock_settings.log_to_file = True
            mock_settings.log_file_path = log_path
            setup_logging()

        root = logging.getLogger()
        rotating_handlers = [h for h in root.handlers
                             if type(h) is logging.handlers.RotatingFileHandler]
        assert len(rotating_handlers) == 1


def test_file_handler_not_added_when_disabled():
    """No file handler when log_to_file is False."""
    with patch("app.main.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.log_to_file = False
        setup_logging()

    root = logging.getLogger()
    rotating_handlers = [h for h in root.handlers
                         if type(h) is logging.handlers.RotatingFileHandler]
    assert len(rotating_handlers) == 0


def test_file_handler_writes_logs():
    """Messages are actually written to the log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "test.log")
        with patch("app.main.settings") as mock_settings:
            mock_settings.log_level = "INFO"
            mock_settings.log_to_file = True
            mock_settings.log_file_path = log_path
            setup_logging()

        test_logger = logging.getLogger("test_file_write")
        test_logger.info("hello from test")

        for h in logging.getLogger().handlers:
            h.flush()

        with open(log_path) as f:
            content = f.read()
        assert "hello from test" in content


def test_file_handler_creates_directory():
    """Log directory is created automatically if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_path = os.path.join(tmpdir, "subdir", "deep", "test.log")
        with patch("app.main.settings") as mock_settings:
            mock_settings.log_level = "INFO"
            mock_settings.log_to_file = True
            mock_settings.log_file_path = nested_path
            setup_logging()

        assert os.path.exists(os.path.dirname(nested_path))


def test_invalid_log_level_defaults_to_info():
    """An unrecognized log level string defaults to INFO."""
    with patch("app.main.settings") as mock_settings:
        mock_settings.log_level = "NONEXISTENT"
        mock_settings.log_to_file = False
        setup_logging()

    root = logging.getLogger()
    assert root.level == logging.INFO
