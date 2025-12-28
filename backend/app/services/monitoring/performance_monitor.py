"""
Performance monitoring and alerting for the optimization system.
Tracks solve times, solver performance, and system health.
"""

from typing import Dict, Any, List, Optional, Tuple
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Single performance metric measurement."""
    timestamp: datetime
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    alert_threshold: Optional[float] = None
