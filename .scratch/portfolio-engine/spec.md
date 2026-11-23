Status: ready-for-agent

# Portfolio Engine — Spec

## Problem Statement

An Indian retail equity investor using Groww has no single tool that takes their current holdings, audits portfolio risk and trend regime, suggests optimal Weight reallocations backed by quantitative models (HRP / Global Minimum Variance), forecasts which Tickers are likely to outperform or underperform over the next Rebalancing Period, and backtests whether those signals would have added value historically — all while structurally preventing look-ahead bias. Existing options are either commercial black boxes, Jupyter notebook one-offs that break on reuse, or tools targeting US markets with the wrong calendar, currency, and brokerage cost assumptions.

## Solution

Build `stockengine`, a Python CLI with five subcommands (`audit`, `optimise`, `forecast`, `backtest`, `run-all`) that operates on a user-supplied Portfolio of Indian NSE equities. The engine fetches daily adjusted OHLCV Price Bars through a pluggable DataSource (default: `yfinance` with local Parquet caching), computes Log Returns as the canonical internal return series, and exposes four capabilities:

1. **Portfolio Risk & Trend Audit**: volatility, Sharpe, Sortino, max drawdown, correlation matrix (hierarchical-clustered), and three-state DMA Regime classification per Ticker.
2. **Portfolio Reallocation Optimizer**: HRP (default) or Global Minimum Variance behind a strategy enum, with a max single-stock Weight constraint and optional gate-then-tilt integration with the forecaster.
3. **Return & Movement Forecasting**: a pluggable Model (default: LightGBM) predicting Forward Excess Return Rank and Directional Probability via Walk-Forward Validation with structural look-ahead bias prevention.
4. **Backtesting Engine**: out-of-sample evaluation of reallocation and prediction signals with configurable Transaction Costs, comparing against a Benchmark (default: Nifty 50) and an equal-weight buy-and-hold baseline.

Output is CLI tables via `rich` by default, with an optional `--report` flag generating a static HTML report with Plotly charts.

## User Stories

1. As a Groww investor, I want to import my holdings by dropping a Groww Holdings Export (XLSX or CSV) into `data/portfolios/`, so that I don't have to manually re-type my portfolio.
2. As a Groww investor, I want to also drop my Groww Tradebook Export alongside the holdings file, so that each Holding is enriched with its actual buy date and buy price.
3. As a user, I want the portfolio loader to auto-detect whether a file is a Groww Holdings Export or a Groww Tradebook Export by inspecting column headers, so that I don't have to specify the file type.
4. As a user, I want the loader to strip the `-EQ` suffix from Groww symbols and clean comma/₹ formatting from numeric fields, so that Tickers normalise cleanly to NSE symbols.
5. As a user, I want to alternatively provide a simple CSV (`ticker, quantity, buy_price, buy_date`) or JSON file as my Portfolio input, so that I'm not locked into Groww's format.
6. As a user, I want `buy_date` to be optional in my portfolio input, so that I can run the engine even if I only have a holdings snapshot without purchase dates.
7. As a user, I want to run `stockengine audit --portfolio data/portfolios/my_holdings.xlsx` and see a risk summary table with annualised volatility, Sharpe ratio, Sortino ratio, max drawdown, max drawdown duration, and Calmar ratio for my portfolio, so that I understand my current risk exposure.
8. As a user, I want the audit to show both trailing 1-year and full-history risk metrics side-by-side, so that I can see whether recent performance diverges from the long-term picture.
9. As a user, I want the audit to show a per-Ticker detail table with individual max drawdowns, so that I can identify which Holdings are the biggest liability.
10. As a user, I want the audit to display a correlation matrix of my Holdings' Log Returns, rendered hierarchically clustered using the same dendrogram as HRP, so that I can see which Tickers move together.
11. As a user, I want the audit to classify each Ticker's DMA Regime as Bullish, Bearish, or Transitional (using the Close vs DMA50 vs DMA200 relationship), and flag recent Golden Cross or Death Cross events, so that I can see the trend posture of each Holding.
12. As a user, I want to run `stockengine optimise` and receive suggested Weights for each Ticker using HRP as the default allocation algorithm, so that I get a diversified, risk-parity-based rebalancing recommendation.
13. As a user, I want to switch the optimizer to Global Minimum Variance (MVO with equal expected returns) via `--strategy mvo` on the CLI or `strategy: mvo` in `config.yaml`, so that I can compare risk-minimisation approaches.
14. As a user, I want the optimizer to enforce a max single-stock Weight constraint (default 25%, configurable), so that no single Ticker dominates my portfolio.
15. As a user, I want the optimizer to integrate with the forecaster via gate-then-tilt when Forecasts are available: zeroing out Weights for Tickers whose Directional Probability is below the threshold (default 0.50), applying rank-based Tilt Factors (default 1.2× top quartile, 0.8× bottom quartile), and re-normalising to 1.0, so that the allocation tilts toward predicted outperformers.
16. As a user, I want the optimizer to work standalone without Forecasts (pure HRP/MVO Weights with no tilt), so that I can use risk-based allocation without running the forecasting pipeline.
17. As a user, I want to run `stockengine forecast` and see, for each Ticker, its predicted Forward Excess Return Rank and Directional Probability for the next Rebalancing Period, so that I know which Tickers the model expects to outperform.
18. As a user, I want the forecasting model to use Walk-Forward Validation with an expanding window and a minimum 2-year training period, so that every prediction is genuinely out-of-sample.
19. As a user, I want a configurable Embargo Period (default 5 trading days) between training and test windows, so that autocorrelated features don't leak across fold boundaries.
20. As a user, I want the default feature set to include 12 hand-engineered features across Momentum (1m/3m/6m/12m cumulative Log Returns), Trend (DMA50 ratio, DMA200 ratio, DMA50/DMA200 crossover flag), Volatility (20d/60d realised vol, vol ratio), and Volume (20d relative volume), so that the model captures the classic alpha factors without overfitting.
21. As a user, I want every feature function registered in the Feature Registry with its maximum lookback in trading days, so that the pipeline can verify no feature reaches beyond available history and NaN-masks any that do.
22. As a user, I want the prediction horizon to equal the Rebalancing Period, so that the model's target is perfectly aligned with the optimizer's decision boundary.
23. As a user, I want to swap in a different model by implementing the `Model` protocol, so that I'm not locked into LightGBM.
24. As a user, I want to run `stockengine backtest` and see a comparison table of 11 metrics (cumulative return, CAGR, annualised volatility, Sharpe, Sortino, max drawdown, max drawdown duration, Calmar, win rate, total Transaction Costs, turnover) for the strategy, the Benchmark, and the equal-weight buy-and-hold baseline, so that I can judge whether the engine adds value.
25. As a user, I want the backtest to use a configurable flat round-trip Transaction Cost (default 0.28%, reflecting Groww delivery charges), so that results account for real trading costs.
26. As a user, I want the Benchmark to be configurable (default Nifty 50 / `^NSEI`), and an equal-weight buy-and-hold of my own Tickers always computed alongside it, so that I have two baselines.
27. As a user, I want backtest initial Weights to default to equal-weight, with `--initial-weights actual` using my portfolio's current Weights, so that I can test both scenarios.
28. As a user, I want to run `stockengine run-all` to chain audit → optimise → forecast → backtest in sequence, feeding each stage's output to the next, so that I get the full analysis in one command.
29. As a user, I want all configurable parameters (Risk-Free Rate, max Weight, Rebalancing Period, Transaction Cost, Benchmark ticker, Embargo Period, Tilt Factors, trading days per year, Directional Probability threshold) to live in a `config.yaml` file, with CLI flags overriding individual values for one-off runs, so that I have one persistent config and ad-hoc flexibility.
30. As a user, I want the config loaded into a Python `@dataclass` with typed defaults, so that missing config values fall back to sensible defaults and type errors are caught early.
31. As a user, I want `--report` on any subcommand to generate a static HTML file with Plotly charts (cumulative return curves, drawdown chart, weight allocation over time, correlation heatmap, DMA regime timeline), so that I can share or archive visual results.
32. As a user, I want price data cached as Parquet files in `data/cache/` (one file per Ticker), so that repeated runs and backtests don't repeatedly hit Yahoo's servers.
33. As a user, I want `data/cache/` and `output/` to be gitignored (derived data), while `data/portfolios/` and `config.yaml` are committed (user input), so that the repo stays clean.
34. As a user, I want the Risk-Free Rate to default to 6.5% (approximate 91-day Indian T-bill yield) and to be overridable in `config.yaml`, so that Excess Return calculations use a sensible Indian baseline.
35. As a user, I want the trading-days-per-year annualisation factor to default to 252 and be overridable, so that Sharpe/Sortino/volatility annualisation is consistent and comparable to published research.

## Implementation Decisions

### Data Layer

- A `DataSource` protocol with a single `fetch_ohlcv(ticker: str, start: date, end: date) -> DataFrame` method. The default `YFinanceSource` appends `.NS` to the Ticker before calling `yfinance` and returns adjusted OHLCV. A `CachedSource` decorator wraps any `DataSource` and reads/writes Parquet files in `data/cache/`. (ADR-0002)
- Price data is NSE-only, INR-denominated, using the NSE Trading Calendar. (ADR-0001)
- Log Returns are the canonical internal return series, computed as `ln(close_t / close_{t-1})`. A `to_simple_return()` utility converts for user-facing display.

### Portfolio Loader

- A unified loader function accepts a file path and auto-detects the format by inspecting column headers: Groww Holdings Export, Groww Tradebook Export, plain CSV (`ticker, quantity, buy_price, buy_date`), or JSON.
- Groww normalisation: strip `-EQ` suffix from symbols, remove ₹ signs and comma thousands separators from numeric columns, parse XLSX via `openpyxl`, skip non-data header/footer rows.
- When both a Holdings file and a Tradebook file are present in `data/portfolios/`, the loader merges them: holdings for current positions, tradebook for `buy_date` and `buy_price` enrichment.
- `buy_date` is optional. When absent, the engine proceeds without holding-period-specific analysis.

### Configuration

- A `Config` dataclass with typed fields and defaults for every configurable parameter. Loaded from `config.yaml` at the repo root via a YAML parser. CLI arguments (via `click` or `argparse`) override individual fields.
- Parameters: `risk_free_rate` (0.065), `max_weight` (0.25), `rebalancing_period` ("monthly"), `transaction_cost` (0.0028), `benchmark_ticker` ("^NSEI"), `embargo_days` (5), `tilt_top` (1.2), `tilt_bottom` (0.8), `direction_threshold` (0.50), `trading_days_per_year` (252), `strategy` ("hrp"), `min_training_years` (2), `initial_weights` ("equal").

### Risk Audit Module

- Computes per-Ticker and portfolio-level: annualised volatility, Sharpe ratio, Sortino ratio, max drawdown (peak-to-trough on cumulative return), max drawdown duration (trading days below previous peak), Calmar ratio.
- All metrics computed over both trailing 1Y and full history, displayed side-by-side.
- Correlation matrix: Pearson correlation on daily Log Returns, full NxN. Report rendering reorders by HRP's hierarchical clustering dendrogram.
- DMA Regime: three-state classification per Ticker (Bullish / Bearish / Transitional) based on Close vs DMA50 vs DMA200 ordering. Golden Cross and Death Cross flags where DMA50 crosses DMA200.

### Optimizer Module

- Accepts the covariance matrix (from Log Returns) and the max-Weight constraint.
- HRP: hierarchical clustering on the correlation matrix, bisective allocation along the dendrogram, then cap enforcement.
- MVO (Global Minimum Variance): quadratic optimisation minimising portfolio variance with equal expected returns for all Tickers, subject to the max-Weight box constraint. (ADR-0006)
- When Forecasts are available, gate-then-tilt is applied after base Weight computation: (1) zero Weights where `direction_prob < threshold`, (2) multiply surviving Weights by rank-derived Tilt Factors (top quartile × `tilt_top`, bottom quartile × `tilt_bottom`), (3) re-normalise to sum to 1.0. (ADR-0005)
- When no Forecasts are available, the optimizer outputs pure risk-based Weights with no tilt.

### Forecasting Module

- `Model` protocol with `fit(X_train, y_train)` and `predict(X_test) -> Forecast[]` methods. Default implementation wraps LightGBM.
- Prediction targets: Forward Excess Return Rank (cross-sectional rank of realised Excess Returns over the next Rebalancing Period) and Directional Probability (P(excess return > 0)).
- Prediction horizon equals the Rebalancing Period.
- Feature Registry: a decorator `@register_feature(lookback_days=N)` that catalogues each feature function. The pipeline queries the registry to validate lookback availability and NaN-masks features that exceed the available window.
- Default feature set (12 features): Momentum (1m/3m/6m/12m cumulative Log Returns), Trend (close/DMA50 ratio, close/DMA200 ratio, DMA50/DMA200 crossover flag), Volatility (20d realised vol, 60d realised vol, 20d/60d vol ratio), Volume (20d relative volume).

### Walk-Forward Validation Engine

- Expanding window: trains on all data from the start up to date `t`, predicts for the Rebalancing Period starting at `t + embargo_days + 1`.
- Minimum training period: `min_training_years` × `trading_days_per_year` bars.
- Embargo Period: `embargo_days` trading days skipped between the training end and the test start. (ADR-0004)
- Advances `t` by one Rebalancing Period and repeats until the data is exhausted.

### Look-Ahead Bias Prevention (ADR-0004)

Seven structurally enforced rules — the pipeline code makes violations impossible:

1. **Temporal-only splits**: the Walk-Forward engine partitions by date; no random shuffle path exists.
2. **Point-in-time features**: the Feature Registry decorator enforces that each feature function receives only data up to date `t`; the pipeline slices the DataFrame before passing it.
3. **Label alignment**: labels are computed from returns over `[t+1, t+horizon]`; the label column is dropped from the feature DataFrame before model training.
4. **Embargo Period**: the Walk-Forward engine inserts a configurable gap between training end and test start.
5. **Adjusted prices only**: the DataSource returns split/bonus-adjusted OHLCV; no unadjusted price path exists.
6. **Benchmark alignment**: the Benchmark return series is computed over the same walk-forward date range, using the same look-forward logic.
7. **Feature Registry lookback validation**: features whose lookback exceeds available history are NaN-masked, never forward-filled.

### Backtesting Module

- Replays the walk-forward timeline: at each Rebalancing date, the optimizer proposes Weights (optionally tilted by Forecasts); the backtester simulates executing the trades with the configured Transaction Cost.
- Initial Weights: equal-weight (default) or actual portfolio Weights (`--initial-weights actual`).
- Computes 11 metrics for three portfolios (strategy, Benchmark, equal-weight buy-and-hold): cumulative return, CAGR, annualised volatility, Sharpe, Sortino, max drawdown, max drawdown duration, Calmar, win rate, total Transaction Costs, turnover.

### CLI

- Single entry point `stockengine` with subcommands: `audit`, `optimise`, `forecast`, `backtest`, `run-all`.
- `run-all` chains all four in sequence, feeding each stage's output to the next.
- `--portfolio` flag specifies the portfolio file path.
- `--report` flag on any subcommand generates a static HTML file with Plotly charts.
- Config values can be overridden as CLI flags (e.g., `--strategy mvo`, `--max-weight 0.30`).

### Output

- Default: `rich` tables printed to the terminal.
- `--report`: static HTML file written to `output/backtest/` (or `output/audit/`, etc.) with embedded Plotly charts — cumulative return curves, drawdown chart, weight allocation over time (stacked area), correlation heatmap, DMA regime timeline per Ticker.

## Testing Decisions

### What makes a good test

Tests exercise the external behaviour of the engine through its CLI subcommand entry points. They assert on the structured output (risk metrics, Weights, Forecasts, backtest metrics) rather than on the internal state of any module. If a refactoring doesn't change the output, no test should break.

### Primary seam: CLI subcommand functions

Each subcommand's core function is called with a `Config` object and a `DataSource` instance. Tests inject a **fixture DataSource** that returns deterministic, precomputed Price Bars (small synthetic datasets with known statistical properties), making tests fast, offline, and reproducible.

- **Audit tests**: given a fixture portfolio and known price series, assert that computed Sharpe, Sortino, max drawdown, and DMA Regime values match hand-calculated expectations.
- **Optimizer tests**: given known covariance structures, assert that HRP and MVO Weights satisfy the max-Weight constraint and sum to 1.0. With injected Forecasts, assert that gate-then-tilt correctly zeroes gated Tickers and applies Tilt Factors.
- **Forecast tests**: given a fixture dataset long enough for walk-forward training, assert that the model produces Forecasts with valid `predicted_rank` (sequential ranks) and `direction_prob` (between 0 and 1) for every Ticker.
- **Backtest tests**: given known Weights and price series, assert that cumulative return, Transaction Cost accrual, and turnover computations are correct to within floating-point tolerance.
- **Groww loader tests**: given sample Groww Holdings and Tradebook fixture files (XLSX/CSV), assert that Tickers are normalised (no `-EQ`), numeric fields are cleaned, and merging enriches Holdings with buy dates from the Tradebook.

### Secondary seam: DataSource protocol boundary

The fixture `DataSource` is the injection point that decouples all tests from network access. It implements the same `fetch_ohlcv` protocol as the real `YFinanceSource`.

### Look-ahead bias invariance test (ADR-0004)

A dedicated test that structurally verifies no future data leaks into present computations:

1. Run the full forecast pipeline on a fixture dataset, recording all computed features, walk-forward splits, and model predictions at every date `t`.
2. Modify the fixture dataset by altering all Price Bars from `t+1` onward (e.g., multiply all future closes by 2.0).
3. Re-run the pipeline on the modified dataset.
4. Assert that every feature value, every walk-forward train/test split boundary, and every model prediction at date `t` is **identical** between the two runs. Any difference proves a look-ahead violation.

This test should run for multiple values of `t` across the dataset and should cover all 12 default features, the Feature Registry's NaN-masking logic, and the Walk-Forward Validation engine's date fencing.

### What is NOT tested through a separate seam

- Individual feature functions are tested indirectly via forecast output.
- HRP/MVO internal clustering and matrix operations are tested indirectly via Weight output.
- Walk-Forward window logic is tested indirectly via backtest metrics with known data.
- The `CachedSource` Parquet read/write is tested indirectly via the DataSource protocol (fixture source makes caching unnecessary in tests).

## Out of Scope

- **Multi-market support**: only Indian NSE equities for v1 (ADR-0001). No US/global stocks, no currency conversion.
- **Intraday data**: daily adjusted OHLCV bars only. No 1m/5m/15m granularity.
- **Fundamental data**: no earnings, P/E, book value, or other fundamental features. No reliable free source for Indian equities.
- **Cross-sectional features**: no peer-relative features in the default feature set. Rank prediction already captures relative positioning implicitly.
- **Slippage modelling**: Transaction Cost is a flat percentage; no market-impact or slippage model.
- **Sector constraints**: no sector-concentration limits in the optimizer. Would require a Ticker-to-sector mapping data source.
- **Sliding window walk-forward**: only expanding window for v1. Sliding window is a future option flag.
- **Deep learning models**: no LSTM/Transformer models shipped. The pluggable `Model` protocol allows users to add them.
- **Live/paper trading**: no broker integration, no order execution. The engine is analytical only.
- **Jupyter dashboard**: output is CLI + optional HTML report. Jupyter is a consumption layer, not a deliverable.
- **Tiered Transaction Cost model**: no per-trade cap (₹20), no separate STT/stamp duty breakout. Flat percentage only.
- **Multi-currency portfolios**: INR only.
- **Tax-loss harvesting or tax-aware optimisation**.

## Further Notes

- The `DataSource` protocol should be designed so that adding a new adapter (e.g., Zerodha Kite, Upstox) requires implementing one class with one method — no changes to the rest of the pipeline.
- The `Model` protocol should similarly require only `fit` and `predict` — no changes to the Walk-Forward engine or the Feature Registry.
- The Feature Registry decorator pattern should make adding a new feature a one-function-one-decorator operation, with the pipeline automatically incorporating it.
- The gate-then-tilt integration should be a composable step that can be enabled or disabled without modifying the optimizer's core logic.
- All ADRs (0001–0006) represent decisions that are locked for v1. If a future version revisits them, the ADR should be superseded explicitly rather than silently overridden.
- Glossary terms defined in `GLOSSARY.md` are the canonical vocabulary for all code, tests, CLI help text, and report labels. Use the glossary term; avoid the _Avoid_ synonyms.
