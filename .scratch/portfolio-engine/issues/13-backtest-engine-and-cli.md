# 13: Backtesting engine and `stockengine backtest` CLI

**What to build:** The backtesting engine that replays the walk-forward timeline, simulating rebalancing trades with Transaction Costs and computing 11 performance metrics for three portfolios: the strategy (HRP/MVO, optionally forecast-tilted), the Benchmark (Nifty 50), and the equal-weight buy-and-hold baseline.

**Blocked by:** 02, 07, 12

**Status:** ready-for-agent

- [ ] `backtest(price_bars, folds, weight_schedule, config) -> BacktestResult` replays the walk-forward timeline: at each Rebalancing date it applies the proposed Weights, deducts Transaction Costs for the traded fraction, and computes the daily portfolio return for the following period
- [ ] Transaction Cost is deducted as `config.transaction_cost × turnover` at each Rebalancing date, where turnover is the sum of absolute Weight changes
- [ ] Initial Weights default to equal-weight across all Tickers; `--initial-weights actual` uses the Holdings' current quantities × prices to derive starting Weights
- [ ] `BacktestResult` holds the daily portfolio return series plus all 11 metrics: cumulative return, CAGR, annualised volatility, Sharpe, Sortino, max drawdown, max drawdown duration, Calmar, win rate (% of Rebalancing Periods with positive Excess Return), total Transaction Costs paid, average turnover per rebalance
- [ ] The same 11 metrics are computed for the Benchmark (`config.benchmark_ticker`, fetched via DataSource) and for the equal-weight buy-and-hold portfolio (fixed equal Weights, no rebalancing, no Transaction Costs)
- [ ] `stockengine backtest --portfolio <file>` prints a `rich` comparison table: rows = the 11 metrics, columns = strategy / Benchmark / equal-weight
- [ ] `stockengine backtest --portfolio <file> --with-forecasts` additionally runs gate-then-tilt at each Rebalancing date, using the Forecast from the walk-forward fold for that date
- [ ] `stockengine backtest --portfolio <file> --initial-weights actual` starts the simulation from the Holdings' current Weight distribution
- [ ] `--report` flag writes `output/backtest/backtest_report.html` with Plotly charts: cumulative return curves (strategy, Benchmark, equal-weight), drawdown chart, Weight allocation over time (stacked area chart per rebalance)
- [ ] End-to-end test: given `FixtureSource` with a known constant-return series and a one-Ticker Portfolio, verify that cumulative return equals the analytic compound of daily returns minus the Transaction Costs at each rebalance, to within floating-point tolerance
- [ ] Test: turnover for a backtest where Weights never change is 0.0 (and Transaction Cost paid is 0.0 beyond the initial trade)
