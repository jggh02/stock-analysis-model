# Stock Analysis Engine

A Python engine for portfolio risk analysis, weight optimisation, return forecasting, and backtesting, targeting Indian NSE equities.

## Language

**Ticker**:
The NSE trading symbol for an equity (e.g., `RELIANCE`, `TCS`). The canonical identifier throughout the system; a `.NS` suffix is appended only at the data-source boundary for `yfinance` calls.
_Avoid_: scrip, stock code, BSE code (stored as optional secondary field, never used as the primary key)

**Holding**:
A single position in a portfolio: one ticker, a quantity of shares, a buy price, and a buy date.
_Avoid_: position (overloaded with trading jargon), lot

**Portfolio**:
An ordered collection of Holdings representing the user's current equity positions. The human-authored input is CSV; the canonical internal representation is JSON.
_Avoid_: watchlist (a watchlist has no quantities or buy prices)

**Trading Calendar**:
The set of market-open dates for NSE, in IST. Determines which dates have valid price bars and which are holidays/weekends.
_Avoid_: schedule, market hours

**Risk-Free Rate**:
A user-configurable annualised return used as the baseline for excess-return calculations (Sharpe, Sortino). Defaults to the 91-day Indian T-bill yield (~6.5%).
_Avoid_: benchmark rate, hurdle rate

**DataSource**:
A protocol (interface) that fetches historical OHLCV bars for a given ticker and date range. The default implementation wraps `yfinance`; others can be plugged in.
_Avoid_: provider, feed, API client

**Price Bar**:
One day's adjusted Open, High, Low, Close, and Volume for a single ticker. The atomic unit of market data in this system.
_Avoid_: candle (implies intraday charting), tick

**Log Return**:
The natural logarithm of `close(t) / close(t-1)`. The canonical daily return series used internally for all risk, correlation, and forecasting computations. Simple (arithmetic) returns are derived from log returns only for user-facing reports.
_Avoid_: simple return (as the internal representation), percentage change

**Weight**:
The fraction of total portfolio value allocated to a single Holding, expressed as a decimal (0.0–1.0). The optimizer outputs a Weight per ticker; a hard constraint caps any single Weight at a user-configurable maximum (default 0.25).
_Avoid_: allocation (vague), share (ambiguous with quantity)

**Rebalancing Period**:
The interval between successive optimizer runs. Defaults to monthly (first trading day of each calendar month). At each rebalancing date, the optimizer proposes new Weights; the backtester simulates executing the trades.
_Avoid_: rebalancing frequency (frequency is the inverse; the period is what the system schedules)

**Excess Return**:
A ticker's Log Return minus the annualised Risk-Free Rate scaled to the same period. The base quantity for Sharpe, Sortino, and the forecasting targets.
_Avoid_: alpha (alpha implies a model; excess return is a raw observation)

**Forward Excess Return Rank**:
The cross-sectional rank of each ticker's realised Excess Return over the next Rebalancing Period, among all tickers in the Portfolio. The primary prediction target for the forecasting model: "which stocks will outperform the others?"
_Avoid_: return prediction (we predict rank, not magnitude)

**Directional Probability**:
The model's estimated probability that a ticker's Excess Return over the next Rebalancing Period will be positive: P(excess return > 0). Used as a secondary exposure gate — if below a threshold, the optimizer reduces the ticker's Weight regardless of its predicted rank.
_Avoid_: signal, score (too vague)

**Walk-Forward Validation**:
The evaluation protocol for the forecasting model. An expanding window trains on all history up to date t (with a minimum of 2 years), predicts for the next Rebalancing Period, then advances t by one period and repeats. No future data ever enters the training set.
_Avoid_: cross-validation (which shuffles time), train-test split (implies a single cut)

**Embargo Period**:
A configurable gap (default: 5 trading days) between the end of a Walk-Forward Validation training window and the start of its test window. Prevents leakage from overlapping return windows or autocorrelated features at the fold boundary.
_Avoid_: buffer, gap (too vague)

**Feature Registry**:
A decorator-based catalogue of all feature functions, each annotated with its maximum lookback in trading days. The pipeline uses the registry to verify that no feature reaches beyond available history; if a feature's lookback exceeds the available window, its value is NaN-masked rather than forward-filled.
_Avoid_: feature store (implies a separate infrastructure service)

**Transaction Cost**:
A flat round-trip percentage deducted from each trade in the optimizer and backtester. User-configurable in `config.yaml`; defaults to 0.28% round-trip, reflecting Groww delivery brokerage (0.1% up to ₹20/order) plus Indian statutory charges (STT, exchange fees, stamp duty, GST).
_Avoid_: commission, slippage (slippage is a separate concept not modelled in v1)

**Groww Holdings Export**:
An XLSX (or manually-saved CSV) file downloaded from Groww's "Profile → Reports → Holdings → Stocks" page. Contains columns: `Stock name`, `Symbol`, `ISIN`, `Quantity`, `Buy value`, `Closing value`, `Unrealised P&L` (column names vary across app versions; `Average price`, `LTP`, `% return` may also appear). Does **not** include purchase dates. The portfolio loader normalises this into the canonical Portfolio JSON format, stripping the `-EQ` suffix Groww sometimes appends to symbols, and cleaning comma/₹ formatting from numeric fields.
_Avoid_: Groww CSV (the native format is XLSX, not CSV)

**Groww Tradebook Export**:
An XLSX file downloaded from Groww's "Profile → Reports → Order History / Tradebook". Contains: `Stock name`, `Symbol`, `ISIN`, `Type` (BUY/SELL), `Quantity`, `Value`, `Price`, `Exchange` (NSE/BSE), `Exchange Order Id`, `Executed date and time` (YYYY-MM-DD HH:MM:SS), `Order status`. Unlike the Holdings Export, this **does** include dates and exchange info. The loader can reconstruct per-Holding buy dates and prices from the tradebook when the holdings export lacks them.
_Avoid_: order history (ambiguous)

**Benchmark**:
The return series against which portfolio performance is measured in backtest reports. User-configurable; defaults to the Nifty 50 index (`^NSEI`). An equal-weighted buy-and-hold of the Portfolio's own tickers is always computed alongside as a secondary baseline.
_Avoid_: index (too generic), market (ambiguous)

**DMA Regime**:
A three-state classification of a ticker's trend posture, derived from the 50-day and 200-day simple moving averages (DMA50, DMA200). **Bullish**: Close > DMA50 > DMA200. **Bearish**: Close < DMA50 < DMA200. **Transitional**: everything else (crossover in progress, mixed signals). A **Golden Cross** (DMA50 crosses above DMA200) marks a shift toward Bullish; a **Death Cross** (DMA50 crosses below DMA200) marks a shift toward Bearish.
_Avoid_: trend (too vague), signal (overloaded)

**Forecast**:
The output of the forecasting model for a single ticker at a single Rebalancing date. Contains two fields: `predicted_rank` (float; lower = expected to outperform peers) and `direction_prob` (float, 0–1; estimated probability that the ticker's Excess Return over the next Rebalancing Period is positive). Consumed by the optimizer via gate-then-tilt integration.
_Avoid_: prediction (ambiguous — could mean the model itself or its output), signal

**Tilt Factor**:
A rank-derived multiplier applied to the optimizer's base Weight for each ticker. Top-quartile predicted ranks receive a multiplier > 1.0 (default 1.2×); bottom-quartile receive < 1.0 (default 0.8×). After tilting, Weights are re-normalised to sum to 1.0. User-configurable magnitudes in `config.yaml`.
_Avoid_: alpha weight, overlay

**Global Minimum Variance**:
The operating mode of Mean-Variance Optimisation in this system. All tickers are assigned equal expected returns, so the optimizer minimises portfolio variance without taking a view on which tickers will outperform. This makes MVO a pure risk-based allocator (like HRP), with return alpha entering only via the Tilt Factor from the forecaster.
_Avoid_: efficient frontier (implies varying expected returns), Markowitz (implies the full expected-return formulation)
