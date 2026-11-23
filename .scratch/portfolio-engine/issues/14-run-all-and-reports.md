# 14: `stockengine run-all` and HTML report (`--report`)

**What to build:** The `run-all` subcommand that chains audit → optimise → forecast → backtest in sequence, feeding each stage's output to the next, giving the user the complete analysis in one command. Also ships the full `--report` HTML output with all Plotly charts, completing the output layer for every subcommand.

**Blocked by:** 06, 08, 11, 13

**Status:** ready-for-agent

- [ ] `stockengine run-all --portfolio <file>` executes `audit` → `optimise` → `forecast` → `backtest` in order using a single shared `Config` and a single shared `DataSource` instance (data fetched once, cached, reused across all stages)
- [ ] `run-all` prints all four `rich` table sets in sequence, clearly delimited by stage headers
- [ ] `run-all --report` generates four HTML report files (one per stage) in their respective `output/` subdirectories, plus a combined `output/report.html` that embeds all charts in a single scrollable page with section anchors
- [ ] `--with-forecasts` on `run-all` passes forecast-tilted Weights into both the optimise and backtest stages
- [ ] `--initial-weights actual` on `run-all` passes through to the backtest stage
- [ ] Any per-stage CLI override (e.g. `--max-weight 0.30`) applies to all stages that use that parameter
- [ ] **Audit HTML charts**: Plotly correlation heatmap (hierarchically clustered), DMA Regime timeline per Ticker (colour-coded Bullish/Transitional/Bearish strips over the price history)
- [ ] **Optimise HTML charts**: Plotly stacked-bar of current vs. proposed Weights per Ticker
- [ ] **Forecast HTML charts**: Plotly bar chart of `direction_prob` per Ticker, colour-coded by quartile rank
- [ ] **Backtest HTML charts**: cumulative return curves (strategy, Benchmark, equal-weight) with drawdown shading; underwater drawdown chart; stacked-area Weight allocation over rebalancing dates
- [ ] End-to-end test: `run-all` with `FixtureSource` completes without error; the backtest Sharpe in the `run-all` output matches the Sharpe produced by calling `stockengine backtest` independently on the same fixture
- [ ] No stage's computation is re-run if its output was already produced earlier in the `run-all` chain (audit's Log Returns are reused by optimise; walk-forward folds are reused by backtest)
