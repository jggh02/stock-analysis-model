# 04: Log Return computation and risk metrics (audit core)

**What to build:** The core mathematical layer that all four engine capabilities depend on. Given a DataFrame of daily Price Bars, compute Log Returns as the canonical internal series. From Log Returns, compute all six risk metrics (annualised volatility, Sharpe ratio, Sortino ratio, max drawdown, max drawdown duration, Calmar ratio) over both the full history and the trailing 1-year window, at both portfolio level and per-Ticker level. Includes the `to_simple_return()` utility for user-facing display.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `log_returns(price_bars) -> DataFrame` computes `ln(close_t / close_{t-1})` per Ticker; first row is NaN (no prior close)
- [ ] `to_simple_return(log_returns) -> DataFrame` converts to arithmetic simple returns for display
- [ ] `portfolio_log_returns(log_returns, weights) -> Series` computes the weighted portfolio return series
- [ ] Annualised volatility = standard deviation of daily Log Returns × √`trading_days_per_year`
- [ ] Sharpe ratio = (CAGR − `risk_free_rate`) / annualised volatility; annualisation uses `trading_days_per_year` from Config
- [ ] Sortino ratio = (CAGR − `risk_free_rate`) / downside deviation (std of negative Log Returns only × √`trading_days_per_year`)
- [ ] Max drawdown = largest peak-to-trough decline on the cumulative Log Return series
- [ ] Max drawdown duration = longest consecutive number of trading days the cumulative return remains below its previous peak
- [ ] Calmar ratio = CAGR / |max drawdown|
- [ ] All six metrics computed for both full-history and trailing 1Y windows (1Y = last `trading_days_per_year` bars)
- [ ] All six metrics computed both portfolio-level (using weighted Log Returns) and per-Ticker (using individual Log Returns)
- [ ] Tests assert computed values match hand-calculated expectations on a small deterministic fixture (e.g. a constant-return series where Sharpe is analytically known)
- [ ] Tests confirm trailing-1Y and full-history figures differ when the fixture's recent period has different characteristics than its full history
