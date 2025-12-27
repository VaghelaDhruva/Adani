from typing import Union


def tonnes_to_metric_tonnes(value: Union[float, int]) -> float:
    """Assume input is already in metric tonnes; placeholder for future conversions."""
    return float(value)


def normalize_currency(value: Union[float, int], from_currency: str, to_currency: str = "USD") -> float:
    """
    Placeholder for currency conversion.
    In production, integrate with a rates API or maintain a lookup table.
    """
    if from_currency == to_currency:
        return float(value)
    # TODO: implement real conversion
    return float(value)


def normalize_distance(value: Union[float, int], unit: str = "km") -> float:
    """Convert distance to kilometers if needed."""
    if unit == "km":
        return float(value)
    elif unit == "mi":
        return float(value) * 1.60934
    else:
        raise ValueError(f"Unsupported distance unit: {unit}")
