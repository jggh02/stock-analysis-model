"""
Tests for issue #02 — Portfolio loader.

Pre-agreed seams under test:
1. load_portfolio(file_path) — format auto-detection & normalisation
2. load_portfolio(dir_path)  — Holdings + Tradebook merge
3. Portfolio.to_json() / from_json() — canonical JSON round-trip
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from stockengine.portfolio import Holding, Portfolio, load_portfolio


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "portfolios"


# ---------------------------------------------------------------------------
# Seam 3: Portfolio.to_json() / from_json() round-trip
# ---------------------------------------------------------------------------

class TestPortfolioJsonRoundTrip:
    """Portfolio.to_json() and from_json() must round-trip Holdings faithfully."""

    def test_round_trip_with_dates_and_none(self):
        portfolio = Portfolio(
            holdings=[
                Holding(ticker="RELIANCE", quantity=10.0, buy_price=2500.5, buy_date=date(2023, 1, 15)),
                Holding(ticker="TCS", quantity=5.0, buy_price=3400.0, buy_date=None),
            ]
        )
        raw = portfolio.to_json()
        restored = Portfolio.from_json(raw)
        assert restored == portfolio


# ---------------------------------------------------------------------------
# Seam 1: load_portfolio(file_path) — format auto-detection & normalisation
# ---------------------------------------------------------------------------

class TestLoadPortfolioFormats:
    """load_portfolio must auto-detect format by headers/content and normalise fields."""

    def test_load_plain_csv_with_dates(self):
        portfolio = load_portfolio(FIXTURES_DIR / "plain_portfolio.csv")
        assert portfolio.holdings == [
            Holding(ticker="RELIANCE", quantity=10.0, buy_price=2500.50, buy_date=date(2023, 1, 15)),
            Holding(ticker="TCS", quantity=5.0, buy_price=3400.00, buy_date=date(2023, 3, 10)),
            Holding(ticker="INFY", quantity=20.0, buy_price=1450.25, buy_date=None),
        ]

    def test_load_plain_csv_missing_buy_date_column(self):
        portfolio = load_portfolio(FIXTURES_DIR / "plain_no_date.csv")
        assert portfolio.holdings == [
            Holding(ticker="RELIANCE", quantity=10.0, buy_price=2500.50, buy_date=None),
            Holding(ticker="TCS", quantity=5.0, buy_price=3400.00, buy_date=None),
        ]

    def test_load_plain_json(self):
        portfolio = load_portfolio(FIXTURES_DIR / "plain_portfolio.json")
        assert portfolio.holdings == [
            Holding(ticker="RELIANCE", quantity=10.0, buy_price=2500.5, buy_date=date(2023, 1, 15)),
            Holding(ticker="TCS", quantity=5.0, buy_price=3400.0, buy_date=None),
        ]

    def test_detection_uses_headers_not_extension(self, tmp_path: Path):
        # Copy plain CSV and plain JSON to .txt / .dat extensions
        csv_copy = tmp_path / "holdings.txt"
        csv_copy.write_text((FIXTURES_DIR / "plain_no_date.csv").read_text(encoding="utf-8"), encoding="utf-8")
        json_copy = tmp_path / "holdings.dat"
        json_copy.write_text((FIXTURES_DIR / "plain_portfolio.json").read_text(encoding="utf-8"), encoding="utf-8")

        assert len(load_portfolio(csv_copy)) == 2
        assert len(load_portfolio(json_copy)) == 2

    @pytest.mark.parametrize("filename", ["groww_holdings.xlsx", "groww_holdings.csv"])
    def test_load_groww_holdings_normalises_ticker_and_numbers(self, filename: str):
        portfolio = load_portfolio(FIXTURES_DIR / filename)
        assert portfolio.holdings == [
            Holding(ticker="RELIANCE", quantity=25.0, buy_price=2600.0, buy_date=None),
            Holding(ticker="TCS", quantity=1000.0, buy_price=3400.0, buy_date=None),
        ]

    @pytest.mark.parametrize("filename", ["groww_tradebook.xlsx", "groww_tradebook.csv"])
    def test_load_groww_tradebook_uses_buy_only_weighted_avg_and_earliest_date(self, filename: str):
        portfolio = load_portfolio(FIXTURES_DIR / filename)
        # RELIANCE: BUY 10 @ 2400 (2023-01-15) + BUY 20 @ 2700 (2023-06-20); SELL ignored
        # Weighted avg buy_price = (24000 + 54000) / 30 = 2600.0; earliest date = 2023-01-15
        assert portfolio.holdings == [
            Holding(ticker="RELIANCE", quantity=30.0, buy_price=2600.0, buy_date=date(2023, 1, 15)),
            Holding(ticker="TCS", quantity=1000.0, buy_price=3500.0, buy_date=date(2022, 11, 5)),
        ]


# ---------------------------------------------------------------------------
# Seam 2: load_portfolio(dir_path) — Holdings + Tradebook merge
# ---------------------------------------------------------------------------

class TestMergeHoldingsAndTradebook:
    """When Holdings and Tradebook files are both present, Holdings are enriched by Tradebook."""

    def test_directory_merges_holdings_and_tradebook(self, tmp_path: Path):
        (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
        (tmp_path / "holdings.xlsx").write_bytes((FIXTURES_DIR / "groww_holdings.xlsx").read_bytes())
        (tmp_path / "tradebook.xlsx").write_bytes((FIXTURES_DIR / "groww_tradebook.xlsx").read_bytes())

        portfolio = load_portfolio(tmp_path)
        # Holdings supply current Holdings (25 RELIANCE, 1000 TCS);
        # Tradebook enriches buy_date and weighted-average buy_price from BUY rows.
        assert portfolio.holdings == [
            Holding(ticker="RELIANCE", quantity=25.0, buy_price=2600.0, buy_date=date(2023, 1, 15)),
            Holding(ticker="TCS", quantity=1000.0, buy_price=3500.0, buy_date=date(2022, 11, 5)),
        ]


