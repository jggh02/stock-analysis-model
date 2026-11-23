# 11: LightGBM Model implementation and `stockengine forecast` CLI

**What to build:** The `Model` protocol, the default LightGBM implementation, and the `stockengine forecast` subcommand end-to-end. A user runs `stockengine forecast --portfolio <file>` and sees, for each Ticker, the Forward Excess Return Rank and Directional Probability predicted for the next Rebalancing Period.

**Blocked by:** 02, 10

**Status:** ready-for-agent

- [ ] `Model` protocol defines `fit(X_train: DataFrame, y_train: DataFrame)` and `predict(X_test: DataFrame) -> list[Forecast]`
- [ ] `Forecast` dataclass has two fields: `ticker` (str), `predicted_rank` (float, lower = expected outperformer), `direction_prob` (float, 0.0–1.0)
- [ ] `LightGBMModel` implements `Model`; trains a LightGBM ranker for `predicted_rank` and a LightGBM classifier for `direction_prob`; both trained on the same feature matrix from the Feature Registry
- [ ] The Walk-Forward engine (Ticket 10) drives the training/prediction loop; `LightGBMModel.fit` is called once per fold on the training window, `predict` on the test window
- [ ] The final Forecast output for `stockengine forecast` is the prediction from the most recent completed fold — the model's current view of the next Rebalancing Period
- [ ] `predicted_rank` values across all Tickers are sequential integers (1 = best predicted, N = worst); no ties allowed in the output (break ties by `direction_prob` descending)
- [ ] `direction_prob` is in [0.0, 1.0] for every Ticker
- [ ] `stockengine forecast --portfolio <file>` prints a `rich` table: Ticker, predicted rank, direction probability, rank change vs. equal-weight neutral (all tickers at same rank)
- [ ] A custom `Model` can be injected by passing an instance to the forecast pipeline function (the LightGBM implementation is the default, not hardcoded)
- [ ] End-to-end test: given `FixtureSource` with enough history (≥ 2 years), the forecast subcommand produces one `Forecast` per Ticker with valid `predicted_rank` (1 to N, all distinct) and `direction_prob` in [0, 1]
- [ ] No test makes real model training calls that take > 5 seconds; use a small synthetic fixture with ≤ 10 Tickers and ≤ 600 rows
