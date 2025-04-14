"""Logging configuration for Speech to Console."""

import logging
import sys
from typing import Callable, List, Optional, TextIO

import structlog

from speech_to_console.config import Config


def setup_logging(
    config: Config, stream: Optional[TextIO] = None
) -> structlog.stdlib.BoundLogger:
    """Configure and set up structlog logging.

    Args:
        config: Application configuration
        stream: Optional stream to write logs to (defaults to sys.stdout)

    Returns:
        Configured structlog logger
    """
    # Map string log levels to logging module levels
    log_level = getattr(logging, config.log_level)

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        stream=stream or sys.stdout,
        force=True,  # Override existing configuration
    )

    # Configure structlog processors
    processors: List[Callable] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add console renderer for terminal output
    # In production, you might want to use a different renderer like JSONRenderer
    processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Reset previous configuration if any
    structlog.reset_defaults()

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Create and return a logger
    return structlog.get_logger("speech_to_console")
