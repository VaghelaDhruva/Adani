"""
PHASE 6 - CLEANUP & RELIABILITY: Standardized Response Formatting

This module provides standardized response formatting utilities for consistent
API responses throughout the Clinker Supply Chain Optimization system.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from fastapi import status
from pydantic import BaseModel


class StandardResponse(BaseModel):
    """
    Standard API response format for consistent client integration.
    
    All API endpoints should use this format for consistent response structure
    and easier client-side handling.
    """
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str
    status_code: int


class PaginatedResponse(BaseModel):
    """
    Paginated response format for list endpoints.
    
    Provides consistent pagination metadata for all list endpoints
    with navigation and count information.
    """
    success: bool
    message: str
    data: List[Any]
    pagination: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str
    status_code: int


def create_success_response(
    data: Any = None,
    message: str = "Operation completed successfully",
    metadata: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK
) -> Dict[str, Any]:
    """
    PHASE 6: Create a standardized success response.
    
    Args:
        data: The response data
        message: Success message
        metadata: Additional metadata
        status_code: HTTP status code
        
    Returns:
        Standardized success response dictionary
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "errors": None,
        "metadata": metadata,
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": status_code
    }


def create_error_response(
    message: str = "An error occurred",
    errors: Optional[List[str]] = None,
    data: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> Dict[str, Any]:
    """
    PHASE 6: Create a standardized error response.
    
    Args:
        message: Error message
        errors: List of specific error details
        data: Any relevant data (usually None for errors)
        metadata: Additional metadata
        status_code: HTTP status code
        
    Returns:
        Standardized error response dictionary
    """
    return {
        "success": False,
        "message": message,
        "data": data,
        "errors": errors or [],
        "metadata": metadata,
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": status_code
    }


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 100,
    message: str = "Data retrieved successfully",
    metadata: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK
) -> Dict[str, Any]:
    """
    PHASE 6: Create a standardized paginated response.
    
    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number (1-based)
        page_size: Number of items per page
        message: Success message
        metadata: Additional metadata
        status_code: HTTP status code
        
    Returns:
        Standardized paginated response dictionary
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    
    pagination = {
        "current_page": page,
        "page_size": page_size,
        "total_items": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "next_page": page + 1 if page < total_pages else None,
        "previous_page": page - 1 if page > 1 else None
    }
    
    return {
        "success": True,
        "message": message,
        "data": items,
        "pagination": pagination,
        "errors": None,
        "metadata": metadata,
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": status_code
    }


def create_validation_error_response(
    validation_errors: Dict[str, List[str]],
    message: str = "Validation failed",
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
) -> Dict[str, Any]:
    """
    PHASE 6: Create a standardized validation error response.
    
    Args:
        validation_errors: Dictionary of field names to error lists
        message: Error message
        status_code: HTTP status code
        
    Returns:
        Standardized validation error response dictionary
    """
    # Flatten validation errors into a list
    error_list = []
    for field, field_errors in validation_errors.items():
        for error in field_errors:
            error_list.append(f"{field}: {error}")
    
    return create_error_response(
        message=message,
        errors=error_list,
        metadata={"validation_errors": validation_errors},
        status_code=status_code
    )


def create_optimization_response(
    run_id: str,
    scenario_name: str,
    status: str,
    objective_value: Optional[float] = None,
    solve_time: Optional[float] = None,
    solver_status: Optional[str] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    PHASE 6: Create a standardized optimization response.
    
    Args:
        run_id: Optimization run identifier
        scenario_name: Scenario name
        status: Optimization status (running, completed, failed)
        objective_value: Optimal objective value
        solve_time: Solver execution time in seconds
        solver_status: Solver-specific status
        message: Custom message
        
    Returns:
        Standardized optimization response dictionary
    """
    data = {
        "run_id": run_id,
        "scenario_name": scenario_name,
        "status": status,
        "objective_value": objective_value,
        "solve_time_seconds": solve_time,
        "solver_status": solver_status
    }
    
    if not message:
        if status == "completed":
            message = f"Optimization completed successfully for scenario '{scenario_name}'"
        elif status == "running":
            message = f"Optimization is running for scenario '{scenario_name}'"
        elif status == "failed":
            message = f"Optimization failed for scenario '{scenario_name}'"
        else:
            message = f"Optimization status: {status}"
    
    return create_success_response(
        data=data,
        message=message,
        metadata={
            "optimization_run": True,
            "scenario": scenario_name
        }
    )


def create_kpi_response(
    scenario_name: str,
    kpi_data: Dict[str, Any],
    run_id: Optional[str] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    PHASE 6: Create a standardized KPI response.
    
    Args:
        scenario_name: Scenario name
        kpi_data: KPI calculation results
        run_id: Associated optimization run ID
        message: Custom message
        
    Returns:
        Standardized KPI response dictionary
    """
    if not message:
        if run_id:
            message = f"KPIs calculated for scenario '{scenario_name}' (run: {run_id})"
        else:
            message = f"KPIs retrieved for scenario '{scenario_name}'"
    
    return create_success_response(
        data=kpi_data,
        message=message,
        metadata={
            "kpi_dashboard": True,
            "scenario": scenario_name,
            "run_id": run_id,
            "data_source": "real_optimization_results" if run_id else "cached_data"
        }
    )


def create_upload_response(
    filename: str,
    rows_processed: int,
    batch_id: Optional[str] = None,
    table_name: Optional[str] = None,
    validation_status: Optional[str] = None
) -> Dict[str, Any]:
    """
    PHASE 6: Create a standardized file upload response.
    
    Args:
        filename: Uploaded filename
        rows_processed: Number of rows processed
        batch_id: Batch identifier for staging
        table_name: Target table name
        validation_status: Validation status
        
    Returns:
        Standardized upload response dictionary
    """
    data = {
        "filename": filename,
        "rows_processed": rows_processed,
        "batch_id": batch_id,
        "table_name": table_name,
        "validation_status": validation_status
    }
    
    message = f"Successfully uploaded '{filename}' with {rows_processed} rows"
    if batch_id:
        message += f" (batch: {batch_id})"
    
    return create_success_response(
        data=data,
        message=message,
        metadata={
            "upload": True,
            "staging_pipeline": batch_id is not None
        },
        status_code=status.HTTP_201_CREATED
    )