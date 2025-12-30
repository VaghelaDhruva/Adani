"""
PHASE 6 - CLEANUP & RELIABILITY: Centralized Error Handling

This module provides comprehensive error handling utilities for consistent
error responses and logging throughout the application.
"""

import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
from loguru import logger

from app.utils.exceptions import (
    ClinkerOptException, DataValidationError, OptimizationError,
    SolverError, ExternalAPIError, ConfigurationError, IntegrationError,
    AuthenticationError, BusinessRuleViolationError
)
from app.utils.response_formatter import create_error_response


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    PHASE 6: Global exception handler for all unhandled exceptions.
    
    Provides consistent error responses and logging for all exceptions
    that are not explicitly handled by specific handlers.
    """
    
    # Log the exception with full traceback
    logger.error(
        f"Unhandled exception in {request.method} {request.url}: {exc}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )
    
    # Return generic error response
    response = create_error_response(
        message="An unexpected error occurred. Please try again later.",
        errors=[str(exc)],
        metadata={
            "exception_type": type(exc).__name__,
            "request_id": getattr(request.state, "request_id", None)
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response
    )


async def clinker_opt_exception_handler(request: Request, exc: ClinkerOptException) -> JSONResponse:
    """
    PHASE 6: Handler for custom application exceptions.
    
    Handles all custom exceptions that inherit from ClinkerOptException
    with appropriate logging and response formatting.
    """
    
    # Determine status code based on exception type
    if isinstance(exc, DataValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, BusinessRuleViolationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, AuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, OptimizationError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exc, ExternalAPIError):
        status_code = status.HTTP_502_BAD_GATEWAY
    elif isinstance(exc, ConfigurationError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Log with appropriate level
    if status_code >= 500:
        logger.error(
            f"Application error in {request.method} {request.url}: {exc}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "exception_type": type(exc).__name__,
                "details": getattr(exc, "details", {})
            }
        )
    else:
        logger.warning(
            f"Client error in {request.method} {request.url}: {exc}",
            extra={
                "method": request.method,
                "url": str(request.url),
                "exception_type": type(exc).__name__,
                "details": getattr(exc, "details", {})
            }
        )
    
    response = create_error_response(
        message=str(exc),
        errors=[str(exc)],
        metadata={
            "exception_type": type(exc).__name__,
            "details": getattr(exc, "details", {}),
            "request_id": getattr(request.state, "request_id", None)
        },
        status_code=status_code
    )
    
    return JSONResponse(status_code=status_code, content=response)


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    PHASE 6: Handler for Pydantic validation errors.
    
    Formats validation errors into a consistent response format
    with detailed field-level error information.
    """
    
    logger.warning(
        f"Validation error in {request.method} {request.url}: {exc}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "validation_errors": exc.errors()
        }
    )
    
    # Format validation errors
    formatted_errors = []
    validation_details = {}
    
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_type = error["type"]
        
        formatted_errors.append(f"{field}: {message}")
        
        if field not in validation_details:
            validation_details[field] = []
        validation_details[field].append({
            "message": message,
            "type": error_type,
            "input": error.get("input")
        })
    
    response = create_error_response(
        message="Validation failed",
        errors=formatted_errors,
        metadata={
            "validation_details": validation_details,
            "request_id": getattr(request.state, "request_id", None)
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    PHASE 6: Handler for SQLAlchemy database errors.
    
    Handles database-related errors with appropriate logging
    and user-friendly error messages.
    """
    
    logger.error(
        f"Database error in {request.method} {request.url}: {exc}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "exception_type": type(exc).__name__,
            "sql_error": str(exc)
        }
    )
    
    # Determine specific error type and message
    if isinstance(exc, IntegrityError):
        message = "Data integrity constraint violation"
        status_code = status.HTTP_409_CONFLICT
        
        # Check for specific constraint violations
        error_str = str(exc).lower()
        if "foreign key" in error_str:
            message = "Referenced record does not exist"
        elif "unique" in error_str:
            message = "Record with this value already exists"
        elif "not null" in error_str:
            message = "Required field cannot be empty"
            
    else:
        message = "Database operation failed"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    response = create_error_response(
        message=message,
        errors=[str(exc)],
        metadata={
            "exception_type": type(exc).__name__,
            "database_error": True,
            "request_id": getattr(request.state, "request_id", None)
        },
        status_code=status_code
    )
    
    return JSONResponse(status_code=status_code, content=response)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    PHASE 6: Handler for FastAPI HTTP exceptions.
    
    Formats HTTP exceptions into consistent response format
    while preserving the original status code and message.
    """
    
    logger.warning(
        f"HTTP exception in {request.method} {request.url}: {exc.status_code} - {exc.detail}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )
    
    response = create_error_response(
        message=exc.detail,
        errors=[exc.detail],
        metadata={
            "http_exception": True,
            "request_id": getattr(request.state, "request_id", None)
        },
        status_code=exc.status_code
    )
    
    return JSONResponse(status_code=exc.status_code, content=response)


def log_and_raise_error(
    error_type: type,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
):
    """
    PHASE 6: Utility function to log and raise errors consistently.
    
    Args:
        error_type: Exception class to raise
        message: Error message
        details: Additional error details
        context: Context information for logging
    """
    
    # Log the error with context
    log_context = {
        "error_type": error_type.__name__,
        "message": message,
        "details": details or {},
        **(context or {})
    }
    
    logger.error(f"Raising {error_type.__name__}: {message}", extra=log_context)
    
    # Raise the exception
    if issubclass(error_type, ClinkerOptException):
        raise error_type(message, details)
    else:
        raise error_type(message)


def handle_optimization_error(
    error: Exception,
    scenario_name: str,
    run_id: Optional[str] = None
) -> OptimizationError:
    """
    PHASE 6: Specialized handler for optimization errors.
    
    Converts various optimization-related errors into standardized
    OptimizationError with proper context and logging.
    """
    
    context = {
        "scenario_name": scenario_name,
        "run_id": run_id,
        "original_error": str(error),
        "original_error_type": type(error).__name__
    }
    
    if isinstance(error, SolverError):
        message = f"Solver failed for scenario '{scenario_name}': {error}"
    elif "infeasible" in str(error).lower():
        message = f"Optimization problem is infeasible for scenario '{scenario_name}'"
    elif "timeout" in str(error).lower():
        message = f"Optimization timed out for scenario '{scenario_name}'"
    else:
        message = f"Optimization failed for scenario '{scenario_name}': {error}"
    
    logger.error(f"Optimization error: {message}", extra=context)
    
    return OptimizationError(message, context)