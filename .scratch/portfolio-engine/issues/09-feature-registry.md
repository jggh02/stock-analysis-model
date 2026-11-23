# 09: Feature Registry and 12 default features

**What to build:** The Feature Registry — a decorator-based catalogue of all feature functions, each annotated with its maximum lookback in trading days. The pipeline queries the registry to validate lookback availability and NaN-masks any feature whose lookback exceeds the available history. All 12 default features across the Momentum, Trend, Volatility, and Volume families ship here.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] `@register_feature(lookback_days=N)` decorator registers the function in a global Feature Registry with its name and maximum lookback
- [ ] `build_feature_matrix(price_bars, as_of_date, registry) -> DataFrame` applies all registered features to the price bars sliced up to `as_of_date`, NaN-masks each feature column where the available history is shorter than its registered `lookback_days`, and returns the result
- [ ] The pipeline never forward-fills NaN-masked feature values — NaN propagates to the model
- [ ] **Momentum features (4)**: 1-month (21-day), 3-month (63-day), 6-month (126-day), 12-month (252-day) cumulative Log Returns; lookback = window length respectively
- [ ] **Trend features (3)**: close/DMA50 ratio (lookback=50), close/DMA200 ratio (lookback=200), DMA50/DMA200 crossover flag — 1 if DMA50 > DMA200 else 0 (lookback=200)
- [ ] **Volatility features (3)**: 20-day realised volatility (std of Log Returns × √252, lookback=20), 60-day realised volatility (lookback=60), vol ratio = 20d vol / 60d vol (lookback=60)
- [ ] **Volume features (1)**: 20-day relative volume = today's volume / 20-day mean volume (lookback=20)
- [ ] Total registered features: 12 (4 + 3 + 3 + 1 + the crossover flag counts as one)
- [ ] Test: build feature matrix for a fixture with only 100 days of history; assert that all features with `lookback_days > 100` are entirely NaN, and features with `lookback_days ≤ 100` are non-NaN (where enough data exists)
- [ ] Test: adding a new feature via `@register_feature` causes it to appear in the matrix without any other code change
