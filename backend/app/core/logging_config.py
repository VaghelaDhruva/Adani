"""
PHASE 6 - CLEANUP & RELIABILITY: Enhanced Logging Configuration

This module provides comprehensive logging configuration for the Clinker Supply Chain
Optimization system with structured logging, file rotation, and production-ready
log management.
"""

import logging
import sys
import os
from typing import Any, Dict
from pathlib import Path

from loguru import logger

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """
    PHASE 6: Enhanced logging setup with file rotation and structured logging.
    
    Configures both console and file logging with appropriate levels,
    rotation policies, and structured formatting for production use.
    """
    # Remove default loguru handler
    logger.remove()
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Console handler with colored output for development
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        serialize=(settings.LOG_FORMAT == "json"),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # File handler for application logs with rotation
    logger.add(
        "logs/app.log",
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | "
            "{process.id}:{thread.id} | {message}"
        ),
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        serialize=(settings.LOG_FORMAT == "json"),
        backtrace=True,
        diagnose=True,
    )
    
    # Error-specific log file for critical issues
    logger.add(
        "logs/errors.log",
        level="ERROR",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | "
            "{process.id}:{thread.id} | {extra} | {message}"
        ),
        rotation="5 MB",
        retention="90 days",  # Keep errors longer
        compression="gz",
        serialize=(settings.LOG_FORMAT == "json"),
        backtrace=True,
        diagnose=True,
    )
    
    # Optimization-specific log file for performance monitoring
    logger.add(
        "logs/optimization.log",
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | "
            "OPTIMIZATION | {message}"
        ),
        filter=lambda record: "optimization" in record["name"].lower() or "solver" in record["name"].lower(),
        rotation="20 MB",
        retention="60 days",
        compression="gz",
    )
    
    # API access log for monitoring and debugging
    logger.add(
        "logs/api_access.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | API | {message}",
        filter=lambda record: "api" in record["name"].lower() or "routes" in record["name"].lower(),
        rotation="50 MB",
        retention="30 days",
        compression="gz",
    )
    
    # Performance metrics log
    logger.add(
        "logs/performance.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | PERF | {message}",
        filter=lambda record: "performance" in record.get("extra", {}).get("category", ""),
        rotation="10 MB",
        retention="14 days",
        compression="gz",
    )
    
    logger.info("PHASE 6: Enhanced logging configuration initialized")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Log format: {settings.LOG_FORMAT}")
    logger.info(f"Logs directory: {logs_dir.absolute()}")


class InterceptHandler(logging.Handler):
    """
    PHASE 6: Enhanced intercept handler for standard logging.
    
    Intercepts standard Python logging and forwards to loguru with
    proper context preservation and error handling.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Add extra context for better debugging
        extra = {
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "pathname": record.pathname,
        }

        logger.opt(depth=depth, exception=record.exc_info).bind(**extra).log(
            level, record.getMessage()
        )


def configure_uvicorn_logging() -> Dict[str, Any]:
    """
    PHASE 6: Enhanced uvicorn logging configuration.
    
    Configures uvicorn to use our enhanced logging system with
    proper access logging and error handling.
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(asctime)s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "()": InterceptHandler,
            },
            "access": {
                "()": InterceptHandler,
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"], 
                "level": settings.LOG_LEVEL, 
                "propagate": False
            },
            "uvicorn.error": {
                "handlers": ["default"], 
                "level": settings.LOG_LEVEL, 
                "propagate": False
            },
            "uvicorn.access": {
                "handlers": ["access"], 
                "level": "INFO", 
                "propagate": False
            },
            "sqlalchemy.engine": {
                "handlers": ["default"],
                "level": "WARNING",  # Reduce SQL query noise
                "propagate": False
            },
            "sqlalchemy.pool": {
                "handlers": ["default"],
                "level": "WARNING",
                "propagate": False
            },
        },
    }


def log_performance_metric(metric_name: str, value: float, unit: str = "", **kwargs):
    """
    PHASE 6: Log performance metrics for monitoring.
    
    Logs performance metrics in a structured format for monitoring
    and alerting systems.
    """
    extra = {
        "category": "performance",
        "metric": metric_name,
        "value": value,
        "unit": unit,
        **kwargs
    }
    logger.bind(**extra).info(f"METRIC: {metric_name}={value}{unit}")


def log_business_event(event_type: str, details: Dict[str, Any]):
    """
    PHASE 6: Log business events for audit and monitoring.
    
    Logs important business events like optimization runs,
    data uploads, and system state changes.
    """
    extra = {
        "category": "business_event",
        "event_type": event_type,
        **details
    }
    logger.bind(**extra).info(f"BUSINESS_EVENT: {event_type}", extra=extra)
