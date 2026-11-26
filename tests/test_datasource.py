"""
Tests for issue #03 — DataSource implementations (YFinanceSource, CachedSource).

Pre-agreed seams under test:
1. YFinanceSource.fetch_ohlcv(ticker, start, end) — with yfinance.download mocked
2. CachedSource.fetch_ohlcv(ticker, start, end)   — wrapping FixtureSource
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from stockengine.datasource import CachedSource, DataSource, FixtureSource, YFinanceSource


def _make_raw_ohlcv(dates: list[str]) -> pd.DataFrame:
    """Build a synthetic yfinance-shaped OHLCV DataFrame for *dates*."""
    n = len(dates)
    return pd.DataFrame(
        {
            "Open": [100.0 + i for i in range(n)],
            "High": [101.0 + i for i in range(n)],
            "Low": [99.0 + i for i in range(n)],
            "Close": [100.5 + i for i in range(n)],
            "Volume": [1000.0 + i * 100 for i in range(n)],
        },
        index=pd.DatetimeIndex(dates),
    )


# ---------------------------------------------------------------------------
# Seam 1: YFinanceSource.fetch_ohlcv(ticker, start, end)
# ---------------------------------------------------------------------------

class TestYFinanceSource:
    """YFinanceSource must adapt NSE Tickers to yfinance and normalise Price Bars."""

    def test_appends_ns_and_returns_adjusted_ohlcv(self):
        raw = _make_raw_ohlcv(["2024-01-02", "2024-01-03"])

        with patch("stockengine.datasource.yf.download", return_value=raw) as mock_dl:
            source = YFinanceSource()
            assert isinstance(source, DataSource)
            df = source.fetch_ohlcv("RELIANCE", date(2024, 1, 2), date(2024, 1, 3))

        mock_dl.assert_called_once()
        args, kwargs = mock_dl.call_args
        assert args[0] == "RELIANCE.NS"
        assert kwargs.get("auto_adjust") is True
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert isinstance(df.index, pd.DatetimeIndex)
        assert len(df) == 2

    def test_index_ticker_passes_through_without_ns(self):
        raw = _make_raw_ohlcv(["2024-01-02"])

        with patch("stockengine.datasource.yf.download", return_value=raw) as mock_dl:
            df = YFinanceSource().fetch_ohlcv("^NSEI", date(2024, 1, 2), date(2024, 1, 2))

        mock_dl.assert_called_once()
        assert mock_dl.call_args[0][0] == "^NSEI"
        assert len(df) == 1

    def test_filters_out_weekends_and_nse_holidays(self):
        # 2024-01-25 (Thu, open), 2024-01-26 (Fri, Republic Day - NSE holiday),
        # 2024-01-27 (Sat, weekend), 2024-01-28 (Sun, weekend), 2024-01-29 (Mon, open)
        raw = _make_raw_ohlcv(
            ["2024-01-25", "2024-01-26", "2024-01-27", "2024-01-28", "2024-01-29"]
        )

        with patch("stockengine.datasource.yf.download", return_value=raw):
            df = YFinanceSource().fetch_ohlcv("TCS", date(2024, 1, 25), date(2024, 1, 29))

        expected_dates = [date(2024, 1, 25), date(2024, 1, 29)]
        assert list(df.index.date) == expected_dates


# ---------------------------------------------------------------------------
# Seam 2: CachedSource.fetch_ohlcv(ticker, start, end)
# ---------------------------------------------------------------------------

class TestCachedSource:
    """CachedSource must cache DataSource results as <TICKER>.parquet."""

    def test_cache_miss_writes_parquet_without_ns_and_returns_data(self, tmp_path: Path):
        fixture = FixtureSource()
        cached = CachedSource(fixture, cache_dir=tmp_path)
        assert isinstance(cached, DataSource)

        start, end = date(2019, 1, 1), date(2019, 1, 31)
        df = cached.fetch_ohlcv("RELIANCE", start, end)

        assert (tmp_path / "RELIANCE.parquet").exists()
        assert not (tmp_path / "RELIANCE.NS.parquet").exists()
        expected = fixture.fetch_ohlcv("RELIANCE", start, end)
        pd.testing.assert_frame_equal(df, expected)

    def test_cache_hit_returns_identical_data_without_calling_wrapped_source(self, tmp_path: Path):
        fixture = FixtureSource()
        spy = MagicMock(wraps=fixture)
        cached = CachedSource(spy, cache_dir=tmp_path)

        start, end = date(2019, 1, 1), date(2019, 1, 31)
        first = cached.fetch_ohlcv("TCS", start, end)
        assert spy.fetch_ohlcv.call_count == 1
        assert (tmp_path / "TCS.parquet").exists()

        second = cached.fetch_ohlcv("TCS", start, end)
        assert spy.fetch_ohlcv.call_count == 1
        pd.testing.assert_frame_equal(second, first, check_freq=False)

        narrow = cached.fetch_ohlcv("TCS", date(2019, 1, 10), date(2019, 1, 20))
        assert spy.fetch_ohlcv.call_count == 1
        assert (narrow.index.date >= date(2019, 1, 10)).all()
        assert (narrow.index.date <= date(2019, 1, 20)).all()
