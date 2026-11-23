# 08: `stockengine optimise` CLI subcommand (standalone, no tilt)

**What to build:** The optimise subcommand end-to-end, without forecast integration. A user runs `stockengine optimise --portfolio <file>` and receives a `rich` table of proposed Weights per Ticker using HRP (default) or Global Minimum Variance. Gate-then-tilt is not wired yet — that lands in Ticket 12.

**Blocked by:** 02, 07

**Status:** ready-for-agent

- [ ] `stockengine optimise --portfolio <file>` runs without error on the fixture portfolio file
- [ ] Output table shows: Ticker, proposed Weight (as a percentage), current Weight (derived from portfolio quantities × current prices), Weight change (proposed − current)
- [ ] `--strategy mvo` switches to Global Minimum Variance; `--strategy hrp` (or omitting the flag) uses HRP
- [ ] `--max-weight 0.30` overrides the Config constraint for this run
- [ ] All proposed Weights are ≥ 0, sum to 1.0, and no Ticker exceeds `max_weight`
- [ ] `--report` flag writes `output/optimise/optimise_report.html` containing a Plotly stacked-bar chart of current vs. proposed Weights
- [ ] End-to-end test: given `FixtureSource` and a fixture portfolio, the subcommand's output Weights match those produced by calling the Ticket 07 `optimise()` function directly on the same data
- [ ] No forecast or tilt logic is invoked or referenced in this ticket
