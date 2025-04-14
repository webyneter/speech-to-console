"""Tests for the logging module."""

import sys
from io import StringIO

from speech_to_console.config import Config
from speech_to_console.logging import setup_logging


def test_setup_logging():
    """Test that logging is correctly set up."""
    # Set up a test config
    config = Config(
        openai_api_key="fake_key",
        log_level="INFO",
    )

    # Redirect stdout to capture log output
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    try:
        # Set up logging with the StringIO as the output stream
        logger = setup_logging(config, mystdout)

        # Test log at INFO level (should appear)
        logger.info("Test INFO message")
        output = mystdout.getvalue()
        assert "Test INFO message" in output

        # Test log at DEBUG level (should not appear with INFO level)
        mystdout.truncate(0)
        mystdout.seek(0)
        logger.debug("Test DEBUG message")
        output = mystdout.getvalue()
        assert "Test DEBUG message" not in output

        # Change level to DEBUG
        config.log_level = "DEBUG"
        logger = setup_logging(config, mystdout)

        # Now debug messages should appear
        mystdout.truncate(0)
        mystdout.seek(0)
        logger.debug("Test DEBUG message")
        output = mystdout.getvalue()
        assert "Test DEBUG message" in output
    finally:
        # Restore stdout
        sys.stdout = old_stdout


def test_log_context():
    """Test that log context is correctly included."""
    # Set up a test config
    config = Config(
        openai_api_key="fake_key",
        log_level="DEBUG",
    )

    # Redirect stdout to capture log output
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    try:
        # Set up logging with the StringIO as the output stream
        logger = setup_logging(config, mystdout)

        # Test log with context
        logger.info("Test message with context", key1="value1", key2="value2")
        output = mystdout.getvalue()
        assert "Test message with context" in output
        assert "key1" in output
        assert "value1" in output
        assert "key2" in output
        assert "value2" in output
    finally:
        # Restore stdout
        sys.stdout = old_stdout
