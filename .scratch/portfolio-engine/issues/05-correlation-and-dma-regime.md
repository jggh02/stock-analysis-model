# 05: Correlation matrix and DMA Regime classification

**What to build:** Two audit computations that sit alongside the risk metrics: a full NxN Pearson correlation matrix on daily Log Returns (with hierarchical clustering metadata for report rendering), and a three-state DMA Regime classification (Bullish / Bearish / Transitional) plus Golden/Death Cross flags per Ticker.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] `correlation_matrix(log_returns) -> DataFrame` computes the full NxN Pearson correlation matrix across all Tickers
- [ ] `cluster_order(correlation_matrix) -> list[str]` returns the Ticker ordering produced by HRP's hierarchical clustering dendrogram — used by the report to render the heatmap in clustered order (the HRP optimiser itself is not required here; a standalone `linkage` call on the correlation matrix suffices)
- [ ] `dma_regime(price_bars) -> DataFrame` computes per-Ticker DMA50 (50-day simple moving average) and DMA200 (200-day SMA) and classifies each date as Bullish (Close > DMA50 > DMA200), Bearish (Close < DMA50 < DMA200), or Transitional (all other cases)
- [ ] `golden_cross_dates(price_bars) -> dict[str, list[date]]` returns, per Ticker, the dates where DMA50 crossed above DMA200
- [ ] `death_cross_dates(price_bars) -> dict[str, list[date]]` returns, per Ticker, the dates where DMA50 crossed below DMA200
- [ ] DMA Regime for the most recent date is what the audit CLI displays per Ticker
- [ ] Tests verify regime classification on hand-constructed price sequences: a monotonically increasing price series with enough history to have DMA50 > DMA200 must classify as Bullish; a crossing sequence must produce exactly one Golden Cross event at the correct date
- [ ] Tests verify the correlation matrix is symmetric, has 1.0 on the diagonal, and lies in [−1, 1]
- [ ] Tests verify that `cluster_order` returns all Tickers exactly once
