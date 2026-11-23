# 07: HRP and Global Minimum Variance optimizer

**What to build:** The optimizer module implementing both allocation strategies behind a `strategy` enum. HRP uses hierarchical clustering on the correlation matrix for bisective risk-parity allocation. Global Minimum Variance (MVO with equal expected returns) minimises portfolio variance via quadratic optimisation. Both enforce the max single-stock Weight constraint. No gate-then-tilt yet — that lands in Ticket 12.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] `optimise(log_returns, strategy, config) -> dict[str, float]` returns a Weight per Ticker that sums to 1.0
- [ ] HRP path: compute correlation matrix → hierarchical clustering (Ward linkage or similar) → bisective allocation along the dendrogram → clip any Weight exceeding `config.max_weight` → re-normalise
- [ ] MVO path (Global Minimum Variance): minimise portfolio variance `w^T Σ w` subject to `sum(w) = 1`, `0 ≤ w_i ≤ max_weight`; equal expected returns for all Tickers (no return-view input) (ADR-0006)
- [ ] `strategy` enum has two values: `HRP` (default) and `MVO`
- [ ] Weights always sum to 1.0 (within floating-point tolerance) after the max-Weight cap and re-normalisation
- [ ] No single Ticker Weight exceeds `config.max_weight`
- [ ] All Weights are ≥ 0.0
- [ ] Tests assert both strategies on a known covariance structure (e.g. two perfectly correlated Tickers and one uncorrelated): HRP gives more weight to the uncorrelated Ticker; MVO minimises variance
- [ ] Tests assert that setting `max_weight = 0.25` with 3 Tickers produces no Weight above 0.25 even when the unconstrained optimal would exceed it
- [ ] Tests run without network access, using Log Returns derived from `FixtureSource`
