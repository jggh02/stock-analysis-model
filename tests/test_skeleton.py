"""
Smoke tests for issue #01 — project skeleton.

Seams under test:
1. Config defaults         — 13 typed fields with correct default values
2. Config.from_yaml()      — YAML loading with override and fallback
3. FixtureSource protocol  — fetch_ohlcv returns correct shape/dtypes
4. CLI --help              — entry point prints help and exits 0
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from stockengine.config import Config
from stockengine.datasource import DataSource, FixtureSource


# ---------------------------------------------------------------------------
# Seam 1: Config defaults
# ---------------------------------------------------------------------------

class TestConfigDefaults:
    """Config() with no arguments must expose all 13 parameters at spec values."""

    def test_risk_free_rate_default(self):
        assert Config().risk_free_rate == 0.065

    def test_max_weight_default(self):
        assert Config().max_weight == 0.25

    def test_rebalancing_period_default(self):
        assert Config().rebalancing_period == "monthly"

    def test_transaction_cost_default(self):
        assert Config().transaction_cost == 0.0028

    def test_benchmark_ticker_default(self):
        assert Config().benchmark_ticker == "^NSEI"

    def test_embargo_days_default(self):
        assert Config().embargo_days == 5

    def test_tilt_top_default(self):
        assert Config().tilt_top == 1.2

    def test_tilt_bottom_default(self):
        assert Config().tilt_bottom == 0.8

    def test_direction_threshold_default(self):
        assert Config().direction_threshold == 0.50

    def test_trading_days_per_year_default(self):
        assert Config().trading_days_per_year == 252

    def test_strategy_default(self):
        assert Config().strategy == "hrp"

    def test_min_training_years_default(self):
        assert Config().min_training_years == 2

    def test_initial_weights_default(self):
        assert Config().initial_weights == "equal"


# ---------------------------------------------------------------------------
# Seam 2: Config.from_yaml()
# ---------------------------------------------------------------------------

class TestConfigFromYaml:
    """Config.from_yaml() must load overrides and fall back to defaults for missing keys."""

    def test_load_overrides_max_weight(self, tmp_path: Path):
        yaml_text = "max_weight: 0.10\n"
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml_text)
        cfg = Config.from_yaml(cfg_file)
        assert cfg.max_weight == 0.10

    def test_load_missing_key_falls_back_to_default(self, tmp_path: Path):
        # Only max_weight is set; all others should use their defaults.
        yaml_text = "max_weight: 0.10\n"
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml_text)
        cfg = Config.from_yaml(cfg_file)
        assert cfg.risk_free_rate == 0.065

    def test_load_strategy_override(self, tmp_path: Path):
        yaml_text = "strategy: mvo\n"
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml_text)
        cfg = Config.from_yaml(cfg_file)
        assert cfg.strategy == "mvo"

    def test_load_empty_yaml_gives_all_defaults(self, tmp_path: Path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("")
        cfg = Config.from_yaml(cfg_file)
        assert cfg == Config()


# ---------------------------------------------------------------------------
# Seam 3: DataSource protocol / FixtureSource
# ---------------------------------------------------------------------------

class TestFixtureSource:
    """FixtureSource must implement the DataSource protocol and return deterministic data."""

    TICKERS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

    @pytest.fixture
    def source(self) -> FixtureSource:
        return FixtureSource()

    def test_implements_datasource_protocol(self, source: FixtureSource):
        # Runtime check: DataSource is a Protocol; we verify via duck-typing.
        assert callable(getattr(source, "fetch_ohlcv", None))

    def test_fetch_returns_dataframe(self, source: FixtureSource):
        from datetime import date
        df = source.fetch_ohlcv("RELIANCE", date(2018, 1, 1), date(2020, 12, 31))
        assert isinstance(df, pd.DataFrame)

    def test_fetch_has_ohlcv_columns(self, source: FixtureSource):
        from datetime import date
        df = source.fetch_ohlcv("RELIANCE", date(2018, 1, 1), date(2020, 12, 31))
        assert set(["open", "high", "low", "close", "volume"]).issubset(
            {c.lower() for c in df.columns}
        )

    def test_fetch_at_least_600_rows_across_five_tickers(self, source: FixtureSource):
        """The spec requires ≥600 rows and 5 tickers in the fixture dataset."""
        from datetime import date
        total_rows = 0
        for ticker in self.TICKERS:
            df = source.fetch_ohlcv(ticker, date(2018, 1, 1), date(2020, 12, 31))
            total_rows += len(df)
        assert total_rows >= 600 * len(self.TICKERS)

    def test_fetch_is_deterministic(self, source: FixtureSource):
        """Calling fetch_ohlcv twice must return identical data."""
        from datetime import date
        df1 = source.fetch_ohlcv("TCS", date(2018, 1, 1), date(2020, 12, 31))
        df2 = source.fetch_ohlcv("TCS", date(2018, 1, 1), date(2020, 12, 31))
        pd.testing.assert_frame_equal(df1, df2)

    def test_fetch_no_network_access(self, source: FixtureSource):
        """FixtureSource must not raise on import even without network."""
        # Simply importing and calling the fixture is enough — if it depended
        # on network it would fail in the sandboxed test environment.
        from datetime import date
        df = source.fetch_ohlcv("INFY", date(2018, 1, 1), date(2020, 12, 31))
        assert len(df) > 0

    def test_close_prices_are_positive(self, source: FixtureSource):
        from datetime import date
        df = source.fetch_ohlcv("HDFCBANK", date(2018, 1, 1), date(2020, 12, 31))
        assert (df["close"] > 0).all()

    def test_fetch_date_filtering(self, source: FixtureSource):
        """fetch_ohlcv must filter strictly by the requested dates."""
        from datetime import date
        # Window of exactly 10 days
        df = source.fetch_ohlcv("RELIANCE", date(2019, 1, 1), date(2019, 1, 10))
        assert not df.empty
        assert (df.index.date >= date(2019, 1, 1)).all()
        assert (df.index.date <= date(2019, 1, 10)).all()

        # Date window before fixture data begins
        df_empty = source.fetch_ohlcv("RELIANCE", date(2010, 1, 1), date(2010, 1, 10))
        assert df_empty.empty
        assert set(["open", "high", "low", "close", "volume"]).issubset(
            {c.lower() for c in df_empty.columns}
        )


# ---------------------------------------------------------------------------
# Seam 4: CLI --help
# ---------------------------------------------------------------------------

class TestCLIEntryPoint:
    """stockengine --help and CLI flag overrides."""

    def test_help_exits_zero(self):
        result = subprocess.run(
            [sys.executable, "-m", "stockengine", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_help_mentions_stockengine(self):
        result = subprocess.run(
            [sys.executable, "-m", "stockengine", "--help"],
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        assert "stockengine" in output.lower()

    def test_cli_flags_override_config(self):
        """CLI flags should override individual Config fields."""
        from click.testing import CliRunner
        from stockengine.cli import main
        import click

        runner = CliRunner()

        @main.command("test-inspect-config")
        @click.pass_context
        def test_cmd(ctx):
            cfg = ctx.obj["config"]
            assert cfg.max_weight == 0.35
            assert cfg.strategy == "mvo"
            assert cfg.risk_free_rate == 0.07
            assert cfg.transaction_cost == 0.003
            assert cfg.benchmark_ticker == "^CRSLDX"
            assert cfg.rebalancing_period == "weekly"
            assert cfg.embargo_days == 10
            assert cfg.tilt_top == 1.5
            assert cfg.tilt_bottom == 0.5
            assert cfg.direction_threshold == 0.55
            assert cfg.trading_days_per_year == 250
            assert cfg.min_training_years == 3
            assert cfg.initial_weights == "actual"
            click.echo("CONFIG_OVERRIDE_VERIFIED")

        res = runner.invoke(
            main,
            [
                "--max-weight", "0.35",
                "--strategy", "mvo",
                "--risk-free-rate", "0.07",
                "--transaction-cost", "0.003",
                "--benchmark-ticker", "^CRSLDX",
                "--rebalancing-period", "weekly",
                "--embargo-days", "10",
                "--tilt-top", "1.5",
                "--tilt-bottom", "0.5",
                "--direction-threshold", "0.55",
                "--trading-days-per-year", "250",
                "--min-training-years", "3",
                "--initial-weights", "actual",
                "test-inspect-config",
            ],
            catch_exceptions=False,
        )
        assert res.exit_code == 0
        assert "CONFIG_OVERRIDE_VERIFIED" in res.output

