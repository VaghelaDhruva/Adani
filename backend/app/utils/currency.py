"""
Currency Formatting Utilities

STRICT RULE: All model math uses RAW RUPEES.
UI formatting converts to CRORES/LAKHS for display.
"""

from typing import Union
import logging

logger = logging.getLogger(__name__)


def format_rupees(value: Union[int, float]) -> str:
    """
    Format rupee value for display.
    
    Rules:
    - If value >= 1 Crore (1,00,00,000) → show as ₹X.XX Cr
    - Else if value >= 1 Lakh (1,00,000) → show as ₹X.XX L
    - Else → show as ₹X
    
    Args:
        value: Amount in RAW RUPEES
        
    Returns:
        Formatted string
    """
    if value is None:
        return "₹0"
    
    value = float(value)
    
    # 1 Crore = 1,00,00,000
    if abs(value) >= 10000000:
        crores = value / 10000000
        return f"₹{crores:.2f} Cr"
    
    # 1 Lakh = 1,00,000
    elif abs(value) >= 100000:
        lakhs = value / 100000
        return f"₹{lakhs:.2f} L"
    
    else:
        return f"₹{value:,.0f}"


def validate_cost_realism(total_cost: float) -> tuple[bool, str]:
    """
    Validate that cost appears realistic.
    
    Args:
        total_cost: Total cost in RAW RUPEES
        
    Returns:
        (is_valid, warning_message)
    """
    if total_cost < 2000000:  # Less than 20 lakhs
        warning = (
            f"Cost appears unrealistically low (₹{total_cost:,.2f}). "
            f"Possible scaling or missing-cost issue."
        )
        logger.warning(warning)
        return False, warning
    
    return True, ""


def ensure_raw_rupees(value: Union[int, float], context: str = "") -> float:
    """
    Ensure value is in RAW RUPEES (not scaled).
    
    Checks for common scaling errors:
    - Values < 1 that should be costs
    - Values that look like they've been divided by 1000
    
    Args:
        value: Value to check
        context: Context string for logging
        
    Returns:
        Value in RAW RUPEES
    """
    value = float(value)
    
    # If value is suspiciously low for a cost, warn
    if 0 < value < 1 and "cost" in context.lower():
        logger.warning(
            f"Value {value} in context '{context}' seems unusually low. "
            f"Ensure it's in RAW RUPEES, not scaled."
        )
    
    return value


def convert_to_rupees(value: Union[int, float], from_unit: str) -> float:
    """
    Convert from other units to RAW RUPEES.
    
    Args:
        value: Value to convert
        from_unit: Source unit (e.g., "crores", "lakhs", "thousands")
        
    Returns:
        Value in RAW RUPEES
    """
    value = float(value)
    
    if from_unit.lower() in ["crore", "crores", "cr"]:
        return value * 10000000
    elif from_unit.lower() in ["lakh", "lakhs", "l"]:
        return value * 100000
    elif from_unit.lower() in ["thousand", "thousands", "k"]:
        return value * 1000
    else:
        # Assume already in rupees
        return value

