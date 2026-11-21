# Indian equities only (NSE) for v1

The engine targets Indian NSE-listed equities exclusively. Prices are denominated in INR, the trading calendar follows NSE holidays and IST market hours, and the canonical ticker format is the NSE symbol (e.g., `RELIANCE`). We considered multi-market support (US + India) but deferred it: adding a market-abstraction layer before a second market exists is premature, and constraining to one exchange simplifies the data pipeline, calendar handling, and ticker resolution. A future v2 can introduce an `Exchange` dimension if needed.
