from typing import Any, Dict, List

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from app.utils.exceptions import OptimizationError


class ScenarioType(str):
    BASE = "base"
    HIGH = "high"
    LOW = "low"
    STOCHASTIC = "stochastic"


class ScenarioConfig(BaseModel):
    """Configuration for a single scenario.

    Attributes
    ----------
    name:
        Scenario name (used in results).
    type:
        One of "base", "high", "low", "stochastic".
    scaling_factor:
        Optional deterministic scaling factor for "high" or "low" scenarios.
    dist_type:
        Distribution type for stochastic scenarios: "normal" or "triangular".
    std_dev:
        Standard deviation for normal distribution (as fraction of mean demand).
    tri_low, tri_mode, tri_high:
        Parameters for triangular distribution (multipliers around 1.0).
    random_seed:
        Seed for reproducible random demand draws.
    """

    name: str
    type: str = Field(default=ScenarioType.BASE)
    scaling_factor: float | None = None
    dist_type: str = "normal"  # for stochastic
    std_dev: float = 0.1
    tri_low: float = 0.8
    tri_mode: float = 1.0
    tri_high: float = 1.2
    random_seed: int | None = None

    class Config:
        from_attributes = True


def _scale_demand(df: pd.DataFrame, factor: float) -> pd.DataFrame:
    """Return a copy of df with demand columns scaled by factor."""
    scaled = df.copy()
    scaled["demand_tonnes"] = (scaled["demand_tonnes"] * factor).round(2)
    if "demand_low_tonnes" in scaled.columns:
        scaled["demand_low_tonnes"] = (scaled["demand_low_tonnes"] * factor).round(2)
    if "demand_high_tonnes" in scaled.columns:
        scaled["demand_high_tonnes"] = (scaled["demand_high_tonnes"] * factor).round(2)
    return scaled


def generate_demand_for_scenario(base_demand_df: pd.DataFrame, config: ScenarioConfig) -> pd.DataFrame:
    """Generate a demand DataFrame for a single scenario.

    This function does *not* change the input DataFrame; it returns a new one.
    """

    if config.type == ScenarioType.BASE:
        return base_demand_df.copy()

    if config.type in {ScenarioType.HIGH, ScenarioType.LOW}:
        factor = config.scaling_factor if config.scaling_factor is not None else (
            1.1 if config.type == ScenarioType.HIGH else 0.9
        )
        return _scale_demand(base_demand_df, factor)

    if config.type == ScenarioType.STOCHASTIC:
        if config.random_seed is not None:
            np.random.seed(config.random_seed)
        noisy = base_demand_df.copy()
        if config.dist_type == "normal":
            noise = np.random.normal(1.0, config.std_dev, size=len(noisy))
        elif config.dist_type == "triangular":
            noise = np.random.triangular(
                config.tri_low,
                config.tri_mode,
                config.tri_high,
                size=len(noisy),
            )
        else:
            raise OptimizationError(f"Unsupported distribution type: {config.dist_type}")
        noisy["demand_tonnes"] = (noisy["demand_tonnes"] * noise).round(2)
        return noisy

    raise OptimizationError(f"Unsupported scenario type: {config.type}")


def generate_demand_scenarios(base_demand: List[Dict[str, Any]], multipliers: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Generate demand scenarios by scaling base demand.
    multipliers: {"base": 1.0, "high": 1.2, "low": 0.8}
    Returns list of scenario dicts with name and scaled demand.
    """
    scenarios = []
    df = pd.DataFrame(base_demand)
    for name, mult in multipliers.items():
        scaled = df.copy()
        scaled["demand_tonnes"] = (scaled["demand_tonnes"] * mult).round(2)
        if "demand_low_tonnes" in scaled.columns:
            scaled["demand_low_tonnes"] = (scaled["demand_low_tonnes"] * mult).round(2)
        if "demand_high_tonnes" in scaled.columns:
            scaled["demand_high_tonnes"] = (scaled["demand_high_tonnes"] * mult).round(2)
        scenarios.append({"scenario_name": name, "demand": scaled.to_dict(orient="records")})
    return scenarios


def generate_stochastic_demand(base_demand: List[Dict[str, Any]], distribution: str = "normal", std_factor: float = 0.1) -> List[Dict[str, Any]]:
    """
    Generate stochastic demand draws for Monte Carlo.
    distribution: "normal" or "triangular"
    std_factor: relative std dev for normal
    Returns list of scenario dicts with random demand.
    """
    df = pd.DataFrame(base_demand)
    scenarios = []
    for i in range(10):  # generate 10 stochastic draws
        noisy = df.copy()
        if distribution == "normal":
            noise = np.random.normal(1.0, std_factor, size=len(df))
        elif distribution == "triangular":
            low, mode, high = 0.8, 1.0, 1.2
            noise = np.random.triangular(low, mode, high, size=len(df))
        else:
            raise OptimizationError(f"Unsupported distribution: {distribution}")
        noisy["demand_tonnes"] = (noisy["demand_tonnes"] * noise).round(2)
        scenarios.append({"scenario_name": f"stochastic_{i}", "demand": noisy.to_dict(orient="records")})
    return scenarios
