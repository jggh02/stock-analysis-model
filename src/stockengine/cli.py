"""
stockengine CLI — entry point for all subcommands.

Subcommands:  audit | optimise | forecast | backtest | run-all

Each subcommand's core logic lives in its own module; the CLI is a thin
adapter that parses CLI flags, assembles a :class:`~stockengine.config.Config`,
and delegates to the relevant function.

This module also serves as the ``__main__`` entry point so the package can
be invoked as ``python -m stockengine``.
"""
from __future__ import annotations

from pathlib import Path

import click

from stockengine.config import Config


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="stockengine")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=False, path_type=Path),
    default="config.yaml",
    show_default=True,
    help="Path to the YAML config file.",
)
@click.option("--risk-free-rate", type=float, default=None, help="Override Risk-Free Rate.")
@click.option("--max-weight", type=float, default=None, help="Override max single-stock Weight.")
@click.option("--strategy", type=click.Choice(["hrp", "mvo"]), default=None, help="Override optimizer strategy.")
@click.option("--transaction-cost", type=float, default=None, help="Override Transaction Cost.")
@click.option("--benchmark-ticker", type=str, default=None, help="Override Benchmark Ticker.")
@click.option("--rebalancing-period", type=str, default=None, help="Override Rebalancing Period.")
@click.option("--embargo-days", type=int, default=None, help="Override Embargo Period in days.")
@click.option("--tilt-top", type=float, default=None, help="Override tilt top factor.")
@click.option("--tilt-bottom", type=float, default=None, help="Override tilt bottom factor.")
@click.option("--direction-threshold", type=float, default=None, help="Override directional probability threshold.")
@click.option("--trading-days-per-year", type=int, default=None, help="Override trading days per year.")
@click.option("--min-training-years", type=int, default=None, help="Override min training years.")
@click.option("--initial-weights", type=click.Choice(["equal", "actual"]), default=None, help="Override initial weights.")
@click.pass_context
def main(
    ctx: click.Context,
    config_path: Path,
    risk_free_rate: float | None,
    max_weight: float | None,
    strategy: str | None,
    transaction_cost: float | None,
    benchmark_ticker: str | None,
    rebalancing_period: str | None,
    embargo_days: int | None,
    tilt_top: float | None,
    tilt_bottom: float | None,
    direction_threshold: float | None,
    trading_days_per_year: int | None,
    min_training_years: int | None,
    initial_weights: str | None,
) -> None:
    """stockengine — Portfolio analysis engine for Indian NSE equities.

    Load config from CONFIG_PATH (defaults to config.yaml in the current
    directory) and optionally override individual values via flags.
    """
    ctx.ensure_object(dict)

    # Load config (falls back to defaults if file absent or key missing).
    if config_path.exists():
        cfg = Config.from_yaml(config_path)
    else:
        cfg = Config()

    # Apply CLI overrides.
    overrides = {
        "risk_free_rate": risk_free_rate,
        "max_weight": max_weight,
        "strategy": strategy,
        "transaction_cost": transaction_cost,
        "benchmark_ticker": benchmark_ticker,
        "rebalancing_period": rebalancing_period,
        "embargo_days": embargo_days,
        "tilt_top": tilt_top,
        "tilt_bottom": tilt_bottom,
        "direction_threshold": direction_threshold,
        "trading_days_per_year": trading_days_per_year,
        "min_training_years": min_training_years,
        "initial_weights": initial_weights,
    }
    for key, val in overrides.items():
        if val is not None:
            setattr(cfg, key, val)

    ctx.obj["config"] = cfg


# ---------------------------------------------------------------------------
# Subcommands (stubs — implemented in later issues)
# ---------------------------------------------------------------------------

@main.command()
@click.option("--portfolio", required=True, type=click.Path(exists=True, path_type=Path), help="Portfolio file path.")
@click.option("--report", is_flag=True, default=False, help="Generate HTML report.")
@click.pass_context
def audit(ctx: click.Context, portfolio: Path, report: bool) -> None:
    """Audit portfolio risk and trend regime."""
    click.echo("audit subcommand — not yet implemented (issue #04)")


@main.command()
@click.option("--portfolio", required=True, type=click.Path(exists=True, path_type=Path), help="Portfolio file path.")
@click.option("--report", is_flag=True, default=False, help="Generate HTML report.")
@click.pass_context
def optimise(ctx: click.Context, portfolio: Path, report: bool) -> None:
    """Optimise portfolio Weights using HRP or MVO."""
    click.echo("optimise subcommand — not yet implemented (issue #07)")


@main.command()
@click.option("--portfolio", required=True, type=click.Path(exists=True, path_type=Path), help="Portfolio file path.")
@click.option("--report", is_flag=True, default=False, help="Generate HTML report.")
@click.pass_context
def forecast(ctx: click.Context, portfolio: Path, report: bool) -> None:
    """Forecast return ranks and directional probabilities."""
    click.echo("forecast subcommand — not yet implemented (issue #11)")


@main.command()
@click.option("--portfolio", required=True, type=click.Path(exists=True, path_type=Path), help="Portfolio file path.")
@click.option("--report", is_flag=True, default=False, help="Generate HTML report.")
@click.option(
    "--initial-weights",
    type=click.Choice(["equal", "actual"]),
    default=None,
    help="Override initial Weights for backtesting.",
)
@click.pass_context
def backtest(ctx: click.Context, portfolio: Path, report: bool, initial_weights: str | None) -> None:
    """Backtest the full pipeline against Benchmark and equal-weight baseline."""
    click.echo("backtest subcommand — not yet implemented (issue #13)")


@main.command("run-all")
@click.option("--portfolio", required=True, type=click.Path(exists=True, path_type=Path), help="Portfolio file path.")
@click.option("--report", is_flag=True, default=False, help="Generate HTML report.")
@click.pass_context
def run_all(ctx: click.Context, portfolio: Path, report: bool) -> None:
    """Chain audit → optimise → forecast → backtest in one command."""
    click.echo("run-all subcommand — not yet implemented (issue #14)")
