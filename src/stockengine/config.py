"""
Config dataclass — all 13 configurable parameters with typed defaults.

Loaded from ``config.yaml`` via :meth:`Config.from_yaml`.  CLI flags override
individual fields by passing keyword arguments to the constructor or by
mutating a loaded instance.

Glossary alignment:
    Risk-Free Rate      → risk_free_rate
    Weight              → max_weight
    Rebalancing Period  → rebalancing_period
    Transaction Cost    → transaction_cost
    Benchmark           → benchmark_ticker
    Embargo Period      → embargo_days
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Union

import yaml


class Strategy(str, Enum):
    """Optimizer strategy options."""
    HRP = "hrp"
    MVO = "mvo"


class RebalancingPeriod(str, Enum):
    """Rebalancing period options."""
    MONTHLY = "monthly"
    WEEKLY = "weekly"


class InitialWeights(str, Enum):
    """Initial weights options for backtesting."""
    EQUAL = "equal"
    ACTUAL = "actual"


@dataclass
class Config:
    """Typed configuration for stockengine.

    All fields have sensible defaults so the dataclass can be constructed
    with zero arguments and used in tests without a YAML file.
    """

    # Risk calculations
    risk_free_rate: float = 0.065
    """Annualised Risk-Free Rate (91-day Indian T-bill yield)."""

    # Optimizer
    max_weight: float = 0.25
    """Maximum single-stock Weight cap (decimal, e.g. 0.25 = 25%)."""

    rebalancing_period: str = RebalancingPeriod.MONTHLY.value
    """Rebalancing Period: ``monthly`` or ``weekly``."""

    # Transaction simulation
    transaction_cost: float = 0.0028
    """Flat round-trip Transaction Cost as a decimal (0.28%)."""

    # Benchmark
    benchmark_ticker: str = "^NSEI"
    """Benchmark Ticker for performance comparison (default: Nifty 50)."""

    # Forecasting
    embargo_days: int = 5
    """Embargo Period in trading days between train and test windows."""

    tilt_top: float = 1.2
    """Tilt Factor applied to top-quartile Tickers in gate-then-tilt."""

    tilt_bottom: float = 0.8
    """Tilt Factor applied to bottom-quartile Tickers in gate-then-tilt."""

    direction_threshold: float = 0.50
    """Directional Probability gate threshold."""

    trading_days_per_year: int = 252
    """Annualisation factor (trading days per year for NSE)."""

    strategy: str = Strategy.HRP.value
    """Optimizer strategy: ``hrp`` (Hierarchical Risk Parity) or ``mvo``."""

    min_training_years: int = 2
    """Minimum Walk-Forward training window in years."""

    initial_weights: str = InitialWeights.EQUAL.value
    """Backtest initial Weights: ``equal`` or ``actual``."""

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "Config":
        """Load a ``Config`` from *path*, falling back to defaults for missing keys.

        Parameters
        ----------
        path:
            Path to a YAML file.  The file may be empty or contain only a
            subset of the recognised keys; all other keys fall back to their
            dataclass defaults.

        Returns
        -------
        Config
            A fully populated Config instance.
        """
        text = Path(path).read_text(encoding="utf-8")
        data: dict = yaml.safe_load(text) or {}
        # Only pass keys that are actual Config fields; ignore unknown keys.
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)
