# 10: Walk-Forward Validation engine and look-ahead bias invariance test

**What to build:** The Walk-Forward Validation engine that drives both the forecaster and the backtester. An expanding-window loop partitions the price history into training and test folds, enforcing the Embargo Period, minimum training period, and all seven look-ahead bias prevention rules structurally (ADR-0004). Ships with the dedicated invariance test that proves future Price Bars never influence computations at date t.

**Blocked by:** 09

**Status:** ready-for-agent

- [ ] `walk_forward_folds(price_bars, config) -> list[Fold]` returns an ordered list of `Fold` objects, each with `train_end_date`, `test_start_date`, `test_end_date`
- [ ] First fold's `train_end_date` is at least `min_training_years × trading_days_per_year` bars from the start of the price history
- [ ] Each fold's `test_start_date` = `train_end_date + embargo_days + 1 trading days`; the Embargo Period gap contains no data passed to the model
- [ ] Each fold advances by one Rebalancing Period; folds continue until `test_end_date` would exceed the last available Price Bar
- [ ] Rule 1 (temporal-only splits): no code path exists that randomly shuffles rows across the fold boundary
- [ ] Rule 2 (point-in-time features): `build_feature_matrix` is always called with `as_of_date = fold.train_end_date`; the DataFrame slice ends there
- [ ] Rule 3 (label alignment): labels for fold `f` use returns from `[test_start_date, test_end_date]`; the label column is not present in the feature DataFrame passed to `Model.fit`
- [ ] Rule 4 (embargo): `test_start_date > train_end_date + embargo_days` is a hard invariant checked at fold construction time
- [ ] Rule 5 (adjusted prices only): the Walk-Forward engine accepts data only from a `DataSource` that returns adjusted OHLCV; no unadjusted path
- [ ] Rule 6 (benchmark alignment): the Benchmark return series used for any walk-forward comparison is sliced to the same `[test_start_date, test_end_date]` window
- [ ] Rule 7 (lookback validation): delegated to the Feature Registry (Ticket 09); the Walk-Forward engine never forward-fills NaN features
- [ ] **Look-ahead bias invariance test**: (a) run the full feature computation pipeline on a fixture dataset, recording all feature values at every date `t`; (b) replace all Price Bars from `t+1` onward with altered values (e.g. multiply all future closes by 2.0); (c) re-run on the modified dataset; (d) assert every feature value at date `t` is bitwise-identical between the two runs. This assertion must hold for at least three distinct values of `t` spanning early, middle, and late in the fixture dataset, and must cover all 12 registered features and the Walk-Forward fold boundaries
