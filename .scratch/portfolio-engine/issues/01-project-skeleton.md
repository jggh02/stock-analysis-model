# 01: Project skeleton, Config dataclass, and fixture DataSource

**What to build:** Stand up the repo skeleton every later ticket builds on. By the end, `stockengine` can be installed locally, the `Config` dataclass loads from `config.yaml` with typed defaults and CLI overrides, the `DataSource` protocol is defined, a `FixtureSource` test double exists that returns deterministic Price Bars without hitting any network, and the `data/cache/` and `output/` directories are gitignored while `data/portfolios/` and `config.yaml` are committed.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] `pyproject.toml` (or equivalent) installs `stockengine` as a CLI entry point
- [x] `src/` layout follows the design in the spec (data, config, datasource, and test helper layers)
- [x] `Config` dataclass has typed fields and correct defaults for all 13 parameters: `risk_free_rate` (0.065), `max_weight` (0.25), `rebalancing_period` ("monthly"), `transaction_cost` (0.0028), `benchmark_ticker` ("^NSEI"), `embargo_days` (5), `tilt_top` (1.2), `tilt_bottom` (0.8), `direction_threshold` (0.50), `trading_days_per_year` (252), `strategy` ("hrp"), `min_training_years` (2), `initial_weights` ("equal")
- [x] `config.yaml` at the repo root is loaded into `Config`; missing keys fall back to dataclass defaults
- [x] CLI flags (e.g. `--max-weight`, `--strategy`) override individual `Config` fields for a single run
- [x] `DataSource` protocol is defined with a single `fetch_ohlcv(ticker, start, end) -> DataFrame` method
- [x] `FixtureSource` test double implements the same protocol and returns a small, fully deterministic Price Bar DataFrame (at least 600 rows, 5 Tickers, known statistical properties); no network access, no disk I/O
- [x] `.gitignore` covers `data/cache/`, `output/`, and standard Python artefacts (`__pycache__`, `.venv`, `*.pyc`)
- [x] `data/portfolios/` directory (committed) and `data/cache/`/`output/` directories (gitignored) exist
- [x] A smoke test confirms `Config` loads, `FixtureSource.fetch_ohlcv` returns a DataFrame of the correct shape, and the CLI entry point prints `--help` without error
