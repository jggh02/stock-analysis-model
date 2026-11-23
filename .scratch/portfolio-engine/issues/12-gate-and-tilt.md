# 12: Gate-then-tilt integration and `stockengine optimise --with-forecasts`

**What to build:** The gate-then-tilt composable step (ADR-0005) that sits between the optimizer and the user, tilting base HRP/MVO Weights using Forecasts from the Model. Wire it into `stockengine optimise` via a `--with-forecasts` flag.

**Blocked by:** 08, 11

**Status:** ready-for-agent

- [ ] `gate_and_tilt(weights, forecasts, config) -> dict[str, float]` is a pure function: takes base Weights (from HRP or MVO) and a list of Forecasts, and returns tilted Weights
- [ ] Gate step: any Ticker whose `direction_prob < config.direction_threshold` has its Weight set to 0.0
- [ ] Tilt step: surviving Tickers in the top quartile by `predicted_rank` (lowest rank numbers = best) have their Weight multiplied by `config.tilt_top` (default 1.2); bottom-quartile Tickers multiplied by `config.tilt_bottom` (default 0.8); middle-quartile Tickers unchanged
- [ ] Quartile boundaries are computed across surviving (non-gated) Tickers only
- [ ] Re-normalise: after gating and tilting, Weights are divided by their sum so they total 1.0
- [ ] Max-Weight constraint is re-enforced after re-normalisation (clip + re-normalise again if any Weight exceeds `config.max_weight`)
- [ ] `gate_and_tilt` is a composable step — the optimizer in Ticket 07 is not modified; the function is called by the CLI layer after the optimizer returns base Weights
- [ ] `stockengine optimise --portfolio <file> --with-forecasts` runs the full forecast pipeline (Ticket 11) first, then applies `gate_and_tilt` to the base Weights before printing the output table
- [ ] Output table adds two columns vs. the standalone optimise output: `direction_prob` and `predicted_rank` per Ticker, with gated Tickers shown at Weight 0% and marked "GATED"
- [ ] Test: given 4 Tickers with equal base Weights (0.25 each), one Ticker with `direction_prob = 0.3` (below threshold 0.50) is gated to 0, top-quartile Ticker Weight increases, bottom-quartile decreases, sum remains 1.0
- [ ] Test: `gate_and_tilt` with no Forecasts supplied returns the base Weights unchanged (pure pass-through mode)
