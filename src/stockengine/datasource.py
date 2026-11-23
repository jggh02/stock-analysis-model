"""
DataSource protocol and FixtureSource test double.

The ``DataSource`` protocol is the primary seam between the data-fetch layer
and all analysis modules.  Any class that implements::

    fetch_ohlcv(ticker: str, start: date, end: date) -> DataFrame

satisfies the protocol and can be substituted in tests or production.

``FixtureSource`` is the canonical test double: it generates fully
deterministic Price Bars using a seeded random number generator.  It
requires no network access and no disk I/O.

Glossary alignment:
    DataSource  → DataSource protocol
    Price Bar   → one row: open, high, low, close, volume
    Ticker      → NSE trading symbol passed as-is (no .NS suffix)
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol, runtime_checkable

import numpy as np
import pandas as pd


@runtime_checkable
class DataSource(Protocol):
    """Protocol for any price-data adapter.

    Implementors must provide :meth:`fetch_ohlcv`; no other methods are
    required.  The design ensures that adding a new adapter (e.g. Zerodha
    Kite) requires implementing *only* this one method.
    """

    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        """Return daily adjusted Price Bars for *ticker* in [*start*, *end*].

        Parameters
        ----------
        ticker:
            NSE trading symbol (e.g. ``RELIANCE``).  The ``DataSource``
            implementation is responsible for appending ``.NS`` when calling
            external APIs; callers always use the bare NSE symbol.
        start:
            First date (inclusive) of the requested range.
        end:
            Last date (inclusive) of the requested range.

        Returns
        -------
        pd.DataFrame
            Index: ``pd.DatetimeIndex`` of trading days.
            Columns: ``open``, ``high``, ``low``, ``close``, ``volume``
            (all lowercase).  Prices are adjusted for splits and bonuses.
        """
        ...  # pragma: no cover


class FixtureSource:
    """Deterministic test double implementing :class:`DataSource`.

    Generates synthetic Price Bars using a seeded RNG so that every call
    with the same arguments returns identical data.  Covers 5 tickers with
    at least 600 trading-day rows each, satisfying the spec requirement.

    Statistical properties (known, independent of the implementation):
    - Log returns are approximately N(µ, σ²) with µ ≈ 0.0005, σ ≈ 0.015.
    - Each ticker gets a deterministic per-ticker seed so their return series
      are uncorrelated by construction.
    - Close prices start at a ticker-specific base and drift via GBM.

    Design note: ``FixtureSource`` never touches the network or the
    filesystem; it is safe to use in any sandboxed test environment.
    """

    # Canonical set of 5 NSE tickers the fixture covers.
    TICKERS: tuple[str, ...] = (
        "RELIANCE",
        "TCS",
        "INFY",
        "HDFCBANK",
        "ICICIBANK",
    )

    # Base prices and per-ticker seed offsets for reproducibility.
    _BASE_PRICES: dict[str, float] = {
        "RELIANCE": 2000.0,
        "TCS": 3200.0,
        "INFY": 1500.0,
        "HDFCBANK": 1600.0,
        "ICICIBANK": 800.0,
    }

    # Number of trading-day rows per ticker (well above the 600-row floor).
    _ROWS_PER_TICKER: int = 800

    # Fixed start date for the synthetic series (matches typical spec date range).
    _SERIES_START: date = date(2018, 1, 1)

    def _seed_for_ticker(self, ticker: str) -> int:
        """Derive a deterministic integer seed from the ticker string."""
        return sum(ord(c) * (i + 1) for i, c in enumerate(ticker)) % (2**31)

    def _generate_series(self, ticker: str) -> pd.DataFrame:
        """Build the full synthetic Price Bar DataFrame for *ticker*."""
        rng = np.random.default_rng(self._seed_for_ticker(ticker))

        n = self._ROWS_PER_TICKER
        base = self._BASE_PRICES.get(ticker, 1000.0)

        # Geometric Brownian Motion: S_{t+1} = S_t * exp(r_t)
        # r_t ~ N(0.0005, 0.015^2)  — daily drift, ~20% annualised volatility
        log_returns = rng.normal(loc=0.0005, scale=0.015, size=n)
        close = base * np.exp(np.cumsum(log_returns))

        # Synthetic OHLV derived from close so bars are internally consistent.
        daily_range = np.abs(rng.normal(loc=0.0, scale=0.008, size=n)) * close
        high = close + daily_range * 0.6
        low = close - daily_range * 0.4
        open_ = low + rng.uniform(0, 1, size=n) * (high - low)
        volume = rng.integers(100_000, 2_000_000, size=n).astype(float)

        # Build a trading-day DatetimeIndex starting from _SERIES_START.
        # We generate enough calendar days to get n trading days (Mon–Fri).
        calendar_start = pd.Timestamp(self._SERIES_START)
        trading_days = pd.bdate_range(start=calendar_start, periods=n)

        return pd.DataFrame(
            {
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            },
            index=trading_days,
        )

    def fetch_ohlcv(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        """Return deterministic Price Bars for *ticker* in [*start*, *end*].

        The underlying synthetic series always starts on :attr:`_SERIES_START`
        and spans :attr:`_ROWS_PER_TICKER` trading days.  The *start*/*end*
        window is applied by slicing the index — if the requested window
        exceeds the synthetic series, the full series is returned.

        Parameters
        ----------
        ticker:
            Any of the 5 canonical tickers; unknown tickers are accepted and
            use a generic seed so tests can call with arbitrary symbols.
        start:
            First date of the requested range (inclusive).
        end:
            Last date of the requested range (inclusive).

        Returns
        -------
        pd.DataFrame
            Columns: ``open``, ``high``, ``low``, ``close``, ``volume``.
            Index: ``pd.DatetimeIndex`` (business days, UTC-naive).
        """
        df = self._generate_series(ticker)
        # Slice to requested window.
        mask = (df.index.date >= start) & (df.index.date <= end)
        return df.loc[mask]
