<<<<<<< HEAD
from fastapi import HTTPException, status


class ClinkerOptException(Exception):
    """Base exception for the application."""


class DataValidationError(ClinkerOptException):
    """Raised when data validation fails."""


class OptimizationError(ClinkerOptException):
    """Raised when optimization fails."""


class ExternalAPIError(ClinkerOptException):
    """Raised when external API calls fail."""


def raise_http_exception(detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
    raise HTTPException(status_code=status_code, detail=detail)
=======
"""
Custom exceptions for the supply chain optimization system.
"""


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class OptimizationError(Exception):
    """Raised when optimization execution fails."""
    pass


class SolverError(Exception):
    """Raised when solver fails to find a solution."""
    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


class IntegrationError(Exception):
    """Raised when external integration fails."""
    pass
>>>>>>> d4196135 (Fixed Bug)
