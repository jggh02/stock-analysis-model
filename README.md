# Stock Analysis & Portfolio Optimization Engine (NSE India)

A quantitative Python engine for auditing portfolio risk, detecting market trend regimes, optimizing asset allocation, and forecasting forward excess returns for Indian equities (NSE).

Built with strict structural safeguards against look-ahead bias and realistic Indian retail delivery transaction costs.

---

## Core Capabilities

1. **Portfolio Risk & Trend Audit**
   - Computes annualized volatility, Sharpe & Sortino ratios (benchmarked against the 91-day Indian T-Bill yield), Maximum Drawdown, Beta vs. Nifty 50 (`^NSEI`), and pairwise asset correlation matrices.
   - Evaluates trend regimes using 50-day and 200-day moving averages (DMA).
2. **Portfolio Reallocation Optimizer**
   - Suggests optimal portfolio weights using **Hierarchical Risk Parity (HRP)** by default (with Mean-Variance Optimization available as an alternative).
   - Enforces configurable concentration caps (default: max 25% weight per single stock).
3. **Return & Movement Forecasting**
   - Uses **LightGBM** with expanding-window walk-forward validation to predict forward rebalancing-period excess return ranks (primary alpha signal) alongside directional probabilities (secondary exposure filter).
   - Engineered on stationary Momentum, Trend, Volatility, and Relative Volume features.
4. **Walk-Forward Backtesting Engine**
   - Simulates historical monthly rebalancing out-of-sample with a 5-day embargo period and a default **0.28% round-trip transaction cost** (calibrated for Groww equity delivery brokerage + STT + exchange fees + stamp duty + GST).
   - Compares strategy performance against both the **Nifty 50 (`^NSEI`)** and an equal-weighted buy-and-hold baseline.

---

## Project Structure

```text
stock-analysis-model/
├── config.yaml             # User-configurable parameters (risk-free rate, max weight, fees, etc.)
├── GLOSSARY.md             # Canonical domain definitions
├── AGENTS.md               # Agent workflow and repository rules
├── docs/
│   ├── adr/                # Architecture Decision Records
│   └── agents/             # Issue tracking, triage, and domain documentation rules
├── data/
│   ├── cache/              # Local Parquet cache of daily adjusted OHLCV bars (gitignored)
│   └── portfolios/         # Input portfolio CSVs/JSONs (e.g., Groww holdings exports)
├── output/
│   ├── backtest/           # Backtest metrics CSVs and interactive Plotly HTML reports (gitignored)
│   └── models/             # Serialized LightGBM model artifacts (gitignored)
└── src/                    # Core Python source modules
