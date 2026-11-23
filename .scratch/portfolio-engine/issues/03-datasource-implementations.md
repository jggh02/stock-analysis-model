# 03: DataSource implementations — YFinanceSource and CachedSource

**What to build:** Two concrete implementations of the `DataSource` protocol. `YFinanceSource` wraps `yfinance`, appending `.NS` to Tickers and returning split/bonus-adjusted OHLCV. `CachedSource` is a decorator that wraps any `DataSource` and reads/writes Parquet files in `data/cache/` so repeated fetches skip the network. Both are tested against `FixtureSource` — no real network calls in tests.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `YFinanceSource.fetch_ohlcv(ticker, start, end)` appends `.NS` to the Ticker before calling `yfinance.download`, returns a DataFrame with columns Open, High, Low, Close, Volume using adjusted closing prices
- [ ] `YFinanceSource` returns a DataFrame indexed by date, restricted to NSE Trading Calendar dates (no weekend or holiday rows)
- [ ] `CachedSource` wraps any `DataSource`; on a cache hit it reads the matching Parquet file from `data/cache/` and returns it without calling the wrapped source; on a miss it calls the wrapped source, writes the result to `data/cache/<TICKER>.parquet`, then returns it
- [ ] Cache filenames are derived from the Ticker (e.g. `RELIANCE.parquet`); no `.NS` suffix in the filename
- [ ] `CachedSource` test wraps `FixtureSource`; asserts that after the first call the Parquet file exists and the second call returns identical data without invoking the wrapped source
- [ ] Both implementations satisfy the `DataSource` protocol (a type checker or `isinstance` check against the protocol passes)
- [ ] No test makes a real network request to Yahoo Finance or any other external service
