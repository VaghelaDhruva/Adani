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
