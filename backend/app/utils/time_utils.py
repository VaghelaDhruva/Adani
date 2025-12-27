from datetime import datetime, timedelta
from typing import List
import pandas as pd


def generate_periods(start: str, end: str, freq: str = "W") -> List[str]:
    """
    Generate a list of period strings between start and end.
    freq: pandas offset alias (D=daily, W=weekly, M=monthly)
    Returns strings like '2025-W01' for weekly or '2025-01' for monthly.
    """
    rng = pd.date_range(start=start, end=end, freq=freq)
    if freq.startswith("W"):
        return [f"{d.isocalendar().year}-W{d.isocalendar().week:02d}" for d in rng]
    elif freq.startswith("M"):
        return [f"{d.year}-{d.month:02d}" for d in rng]
    else:
        return [d.strftime("%Y-%m-%d") for d in rng]


def period_to_datetime(period: str, freq: str = "W") -> datetime:
    """Convert a period string back to a datetime (start of the period)."""
    if freq.startswith("W"):
        year, week = map(int, period.split("-W"))
        return datetime.strptime(f"{year} {week} 1", "%Y %W %w")
    elif freq.startswith("M"):
        year, month = map(int, period.split("-"))
        return datetime(year, month, 1)
    else:
        return datetime.strptime(period, "%Y-%m-%d")
