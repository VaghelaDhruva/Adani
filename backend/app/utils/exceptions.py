
"""
PHASE 6 - CLEANUP & RELIABILITY: Centralized Exception Handling

This module provides a centralized exception hierarchy for the entire application.
All custom exceptions inherit from ClinkerOptException for consistent error handling.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class ClinkerOptException(Exception):
    """
    Base exception for the Clinker Supply Chain Optimization application.
    
    All custom exceptions should inherit from this class to ensure
    consistent error handling and logging throughout the application.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DataValidationError(ClinkerOptException):
    """
    Raised when data validation fails.
    
    This includes schema validation, business rule validation,
    referential integrity checks, and data quality issues.
    """
    pass


class OptimizationError(ClinkerOptException):
    """
    Raised when optimization execution fails.
    
    This includes solver failures, infeasible problems,
    and optimization model building errors.
    """
    pass


class SolverError(OptimizationError):
    """
    Raised when solver fails to find a solution.
    
    This is a specialized optimization error for solver-specific issues
    like timeout, infeasibility, or solver crashes.
    """
    pass


class ExternalAPIError(ClinkerOptException):
    """
    Raised when external API calls fail.
    
    This includes routing APIs (OSRM, ORS), data ingestion APIs,
    and any other external service integration failures.
    """
    pass


class ConfigurationError(ClinkerOptException):
    """
    Raised when configuration is invalid.
    
    This includes missing environment variables, invalid settings,
    and configuration file parsing errors.
    """
    pass


class IntegrationError(ClinkerOptException):
    """
    Raised when external integration fails.
    
    This includes database connection failures, file system errors,
    and other infrastructure-related issues.
    """
    pass


class AuthenticationError(ClinkerOptException):
    """
    Raised when authentication fails.
    
    This includes invalid credentials, expired tokens,
    and authorization failures.
    """
    pass


class BusinessRuleViolationError(DataValidationError):
    """
    Raised when business rules are violated.
    
    This is a specialized data validation error for domain-specific
    business logic violations (e.g., SBQ > capacity, negative demand).
    """
    pass


def raise_http_exception(detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
    """
    PHASE 6: Centralized HTTP exception raising with consistent error format.
    
    This function provides a standardized way to raise HTTP exceptions
    throughout the application with consistent error formatting.
    """
    raise HTTPException(status_code=status_code, detail=detail)

