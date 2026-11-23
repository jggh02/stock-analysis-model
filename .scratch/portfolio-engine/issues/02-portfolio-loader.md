# 02: Portfolio loader (plain CSV/JSON + Groww Holdings + Tradebook)

**What to build:** A unified loader that accepts any supported portfolio file and returns a canonical in-memory Portfolio (a list of Holdings). It auto-detects the format by inspecting column headers, normalises Tickers to NSE symbols, cleans numeric fields, makes `buy_date` optional, and merges a Tradebook Export into the Holdings when both files are present in `data/portfolios/`.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Loader accepts a file path and auto-detects one of four formats: plain CSV (`ticker, quantity, buy_price, buy_date`), plain JSON, Groww Holdings Export (XLSX or CSV), Groww Tradebook Export (XLSX or CSV)
- [ ] Detection is by column-header inspection, not by file extension alone
- [ ] Groww Holdings normalisation: strip `-EQ` suffix from symbols, remove ₹ signs and comma thousands-separators from numeric columns, skip non-data header/footer rows, parse XLSX via `openpyxl`
- [ ] Groww Tradebook normalisation: same numeric cleaning, plus parse `Executed date and time` (YYYY-MM-DD HH:MM:SS) into a `date` and derive per-Holding average buy price and earliest buy date from BUY transactions only
- [ ] When a Holdings file and a Tradebook file are both present in `data/portfolios/`, the loader merges them: Holdings supply current positions, Tradebook enriches each Holding with `buy_date` and `buy_price`
- [ ] `buy_date` is optional; when absent the Holding carries `buy_date=None` and the engine proceeds without holding-period-specific analysis
- [ ] Output is a list of Holding objects (Ticker, quantity, buy_price, buy_date) in the canonical internal representation; a `to_json()` / `from_json()` round-trip works
- [ ] Tests use fixture XLSX and CSV files (committed to the test fixtures directory); no Groww API calls
- [ ] Given a Groww Holdings fixture with `RELIANCE-EQ`, the loaded Ticker is `RELIANCE`
- [ ] Given a Holdings fixture (no dates) and a Tradebook fixture, the merged output carries the correct `buy_date` and weighted-average `buy_price` for each Holding
- [ ] Given a plain CSV with a missing `buy_date` column, the loader succeeds and all Holdings have `buy_date=None`
