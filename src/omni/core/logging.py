"""Structured logging setup for OMNI.

Configures JSON logging with component-based loggers and correlation IDs.
"""
import logging
import sys
from typing import Any, Dict

import structlog
from structlog.processors import JSONRenderer, TimeStamper
from structlog.stdlib import LoggerFactory, add_log_level, filter_by_level

from omni.core.config import get_settings


def configure_logging():
    """Configure structured logging for OMNI."""
    settings = get_settings()
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.logging.level.upper()),
    )
    
    # Configure structlog
    shared_processors: list = [
        # Add log level
        add_log_level,
        # Add timestamp
        TimeStamper(fmt="iso"),
        # Add logger name
        structlog.stdlib.ExtraAdder(),
    ]
    
    if settings.logging.format == "json":
        # JSON format
        processors = shared_processors + [
            # Render as JSON
            JSONRenderer(),
        ]
    else:
        # Console format
        processors = shared_processors + [
            # Format as console output
            structlog.dev.ConsoleRenderer(),
        ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str, **context) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with component context.
    
    Args:
        name: Logger name (typically __name__)
        **context: Additional context to bind to all log messages
        
    Returns:
        BoundLogger: Configured structured logger
    """
    logger = structlog.get_logger(name)
    
    if context:
        logger = logger.bind(**context)
    
    return logger


def bind_correlation_id(logger: structlog.stdlib.BoundLogger, correlation_id: str):
    """Bind a correlation ID to the logger.
    
    Args:
        logger: The logger instance
        correlation_id: Correlation ID for request tracing
        
    Returns:
        BoundLogger: Logger with correlation ID bound
    """
    return logger.bind(correlation_id=correlation_id)


# Pre-configured component loggers
def get_core_logger():
    """Get logger for core module."""
    return get_logger("omni.core")


def get_orchestrator_logger():
    """Get logger for orchestrator module."""
    return get_logger("omni.orchestrator")


def get_crew_logger():
    """Get logger for crews module."""
    return get_logger("omni.crews")


def get_validator_logger():
    """Get logger for validators module."""
    return get_logger("omni.validators")


def get_skill_logger():
    """Get logger for skills module."""
    return get_logger("omni.skills")


def get_db_logger():
    """Get logger for database module."""
    return get_logger("omni.db")


def get_api_logger():
    """Get logger for API module."""
    return get_logger("omni.api")


# Initialize logging on module import
configure_logging()
