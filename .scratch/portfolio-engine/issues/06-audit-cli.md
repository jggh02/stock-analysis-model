# 06: `stockengine audit` CLI subcommand

**What to build:** The first user-facing subcommand, end-to-end: a user drops a portfolio file and runs `stockengine audit --portfolio <file>`; the engine loads the Portfolio, fetches Price Bars, computes all risk and trend metrics, and prints four `rich` tables to the terminal.

**Blocked by:** 02, 04, 05

**Status:** ready-for-agent

- [ ] `stockengine audit --portfolio <file>` runs without error on the fixture portfolio file
- [ ] Table 1 — Portfolio summary: annualised volatility, Sharpe, Sortino, max drawdown, max drawdown duration, Calmar; full-history and trailing-1Y columns side-by-side
- [ ] Table 2 — Per-Ticker risk detail: each Holding's max drawdown (full-history and trailing 1Y)
- [ ] Table 3 — Correlation matrix: raw NxN values displayed in Ticker pairs; row/column order follows `cluster_order` from Ticket 05 so the display is hierarchically grouped
- [ ] Table 4 — DMA Regime: per-Ticker current DMA Regime (Bullish / Bearish / Transitional), DMA50 value, DMA200 value, and a flag indicating whether a Golden Cross or Death Cross occurred within the last 20 trading days
- [ ] `--report` flag writes `output/audit/audit_report.html` containing a Plotly correlation heatmap (clustered) and a Plotly DMA regime timeline per Ticker; the CLI still prints the `rich` tables when `--report` is used
- [ ] Config overrides work: `stockengine audit --portfolio <file> --risk-free-rate 0.07` changes the Sharpe and Sortino figures accordingly
- [ ] End-to-end test: given the `FixtureSource` and a fixture portfolio, the subcommand function returns structured audit results whose portfolio-level Sharpe matches the value computed directly by the Ticket 04 functions on the same data
