import logging
import sys
from typing import Any, Dict

from loguru import logger

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    # Remove default loguru handler
    logger.remove()
    # Add stdout with level and format
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
    )
    # Optionally add file handler
    # logger.add("logs/app.log", rotation="10 MB", retention="30 days", level="INFO")


class InterceptHandler(logging.Handler):
    """Intercept standard logging and forward to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_uvicorn_logging() -> Dict[str, Any]:
    # Configure uvicorn to use loguru
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {},
        "handlers": {
            "default": {
                "()": InterceptHandler,
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": settings.LOG_LEVEL, "propagate": False},
            "uvicorn.error": {"handlers": ["default"], "level": settings.LOG_LEVEL, "propagate": False},
            "uvicorn.access": {"handlers": ["default"], "level": settings.LOG_LEVEL, "propagate": False},
        },
    }
