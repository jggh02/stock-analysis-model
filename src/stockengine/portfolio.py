"""
Portfolio data structures and unified loader.

Supports plain CSV, plain JSON, Groww Holdings Export (XLSX/CSV), and
Groww Tradebook Export (XLSX/CSV), with automatic format detection by
column-header inspection and Holdings+Tradebook merging.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterator, Union

import openpyxl


@dataclass
class Holding:
    """A single equity Holding in a Portfolio."""

    ticker: str
    quantity: float
    buy_price: float
    buy_date: date | None = None


@dataclass
class Portfolio:
    """An ordered collection of Holdings in canonical internal representation."""

    holdings: list[Holding]

    def __len__(self) -> int:
        return len(self.holdings)

    def __iter__(self) -> Iterator[Holding]:
        return iter(self.holdings)

    def to_json(self) -> str:
        """Serialise the Portfolio to canonical JSON."""
        payload = {
            "holdings": [
                {
                    "ticker": h.ticker,
                    "quantity": h.quantity,
                    "buy_price": h.buy_price,
                    "buy_date": h.buy_date.isoformat() if h.buy_date is not None else None,
                }
                for h in self.holdings
            ]
        }
        return json.dumps(payload, indent=2)

    @classmethod
    def from_json(cls, raw: str) -> "Portfolio":
        """Deserialise a Portfolio from canonical JSON."""
        data = json.loads(raw)
        items = data["holdings"] if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise ValueError("Invalid portfolio JSON: expected a list of holdings")
        holdings = [
            Holding(
                ticker=str(item["ticker"]),
                quantity=float(item["quantity"]),
                buy_price=float(item["buy_price"]),
                buy_date=(
                    date.fromisoformat(item["buy_date"])
                    if item.get("buy_date") is not None
                    else None
                ),
            )
            for item in items
        ]
        return cls(holdings=holdings)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

@dataclass
class _TableHeader:
    fmt: str
    header_idx: int
    col_map: dict[str, int]


@dataclass
class _TradeAccum:
    quantity: float = 0.0
    cost: float = 0.0
    earliest_date: date | None = None


def _clean_ticker(raw: Any) -> str:
    symbol = str(raw).strip().upper()
    if symbol.endswith("-EQ"):
        symbol = symbol[:-3]
    return symbol


def _clean_number(raw: Any) -> float:
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = str(raw).replace("₹", "").replace(",", "").strip()
    return float(cleaned)


def _parse_date(raw: Any) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").date()


def _is_xlsx_bytes(data: bytes) -> bool:
    return data[:4] == b"PK\x03\x04"


def _read_xlsx_rows(path: Path) -> list[list[Any]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active
        return [list(row) for row in ws.iter_rows(values_only=True)]
    finally:
        wb.close()


def _detect_table_format(rows: list[list[Any]]) -> _TableHeader:
    """Scan rows to find the header row and classify the tabular format."""
    for idx, row in enumerate(rows):
        col_map: dict[str, int] = {}
        for col_idx, cell in enumerate(row):
            if cell is None:
                continue
            key = str(cell).strip().lower()
            if key:
                col_map[key] = col_idx

        keys = set(col_map)
        if {"symbol", "type", "quantity", "executed date and time"}.issubset(keys):
            return _TableHeader("groww_tradebook", idx, col_map)
        if {"symbol", "quantity"}.issubset(keys) and (
            "buy value" in keys or "average price" in keys or "closing value" in keys
        ):
            return _TableHeader("groww_holdings", idx, col_map)
        if {"ticker", "quantity", "buy_price"}.issubset(keys):
            return _TableHeader("plain_csv", idx, col_map)

    raise ValueError("Unable to detect portfolio format from column headers")


def _cell(row: list[Any], col_map: dict[str, int], name: str) -> Any:
    idx = col_map.get(name)
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def _parse_plain_csv(rows: list[list[Any]], header: _TableHeader) -> Portfolio:
    holdings: list[Holding] = []
    for row in rows[header.header_idx + 1 :]:
        raw_ticker = _cell(row, header.col_map, "ticker")
        if raw_ticker is None or not str(raw_ticker).strip():
            continue
        holdings.append(
            Holding(
                ticker=_clean_ticker(raw_ticker),
                quantity=_clean_number(_cell(row, header.col_map, "quantity")),
                buy_price=_clean_number(_cell(row, header.col_map, "buy_price")),
                buy_date=_parse_date(_cell(row, header.col_map, "buy_date")),
            )
        )
    return Portfolio(holdings=holdings)


def _parse_groww_holdings(rows: list[list[Any]], header: _TableHeader) -> Portfolio:
    holdings: list[Holding] = []
    for row in rows[header.header_idx + 1 :]:
        raw_symbol = _cell(row, header.col_map, "symbol")
        if raw_symbol is None or not str(raw_symbol).strip():
            continue
        try:
            quantity = _clean_number(_cell(row, header.col_map, "quantity"))
            avg_price_raw = _cell(row, header.col_map, "average price")
            if avg_price_raw is not None and str(avg_price_raw).strip():
                buy_price = _clean_number(avg_price_raw)
            else:
                buy_value = _clean_number(_cell(row, header.col_map, "buy value"))
                buy_price = buy_value / quantity if quantity else 0.0
        except (ValueError, TypeError):
            # Skip non-data footer or summary rows
            continue
        holdings.append(
            Holding(
                ticker=_clean_ticker(raw_symbol),
                quantity=quantity,
                buy_price=buy_price,
                buy_date=None,
            )
        )
    return Portfolio(holdings=holdings)


def _parse_groww_tradebook(rows: list[list[Any]], header: _TableHeader) -> Portfolio:
    agg: dict[str, _TradeAccum] = {}
    for row in rows[header.header_idx + 1 :]:
        raw_symbol = _cell(row, header.col_map, "symbol")
        raw_type = _cell(row, header.col_map, "type")
        if raw_symbol is None or not str(raw_symbol).strip() or raw_type is None:
            continue
        if str(raw_type).strip().upper() != "BUY":
            continue

        ticker = _clean_ticker(raw_symbol)
        qty = _clean_number(_cell(row, header.col_map, "quantity"))
        price_raw = _cell(row, header.col_map, "price")
        if price_raw is not None and str(price_raw).strip():
            cost = qty * _clean_number(price_raw)
        else:
            cost = _clean_number(_cell(row, header.col_map, "value"))
        exec_date = _parse_date(_cell(row, header.col_map, "executed date and time"))

        entry = agg.setdefault(ticker, _TradeAccum())
        entry.quantity += qty
        entry.cost += cost
        if exec_date is not None and (
            entry.earliest_date is None or exec_date < entry.earliest_date
        ):
            entry.earliest_date = exec_date

    holdings = [
        Holding(
            ticker=ticker,
            quantity=entry.quantity,
            buy_price=entry.cost / entry.quantity if entry.quantity else 0.0,
            buy_date=entry.earliest_date,
        )
        for ticker, entry in agg.items()
    ]
    return Portfolio(holdings=holdings)


_PARSERS: dict[str, Callable[[list[list[Any]], _TableHeader], Portfolio]] = {
    "plain_csv": _parse_plain_csv,
    "groww_holdings": _parse_groww_holdings,
    "groww_tradebook": _parse_groww_tradebook,
}


def _load_single_file(path: Path) -> tuple[str, Portfolio]:
    raw_bytes = path.read_bytes()
    if _is_xlsx_bytes(raw_bytes):
        rows = _read_xlsx_rows(path)
    else:
        text = raw_bytes.decode("utf-8-sig")
        stripped = text.strip()
        if stripped.startswith(("{", "[")):
            return "plain_json", Portfolio.from_json(stripped)
        rows = list(csv.reader(text.splitlines()))

    header = _detect_table_format(rows)
    return header.fmt, _PARSERS[header.fmt](rows, header)


def _merge_holdings_and_tradebook(
    holdings_portfolio: Portfolio,
    tradebook_portfolio: Portfolio,
) -> Portfolio:
    """Enrich Holdings with buy_date and weighted-average buy_price from Tradebook."""
    tb_by_ticker = {h.ticker: h for h in tradebook_portfolio.holdings}
    merged: list[Holding] = []
    for h in holdings_portfolio.holdings:
        tb = tb_by_ticker.get(h.ticker)
        if tb is not None:
            merged.append(
                Holding(
                    ticker=h.ticker,
                    quantity=h.quantity,
                    buy_price=tb.buy_price,
                    buy_date=tb.buy_date,
                )
            )
        else:
            merged.append(h)
    return Portfolio(holdings=merged)


def _load_directory(directory: Path) -> Portfolio:
    holdings_portfolio: Portfolio | None = None
    tradebook_portfolio: Portfolio | None = None

    for entry in sorted(directory.iterdir()):
        if not entry.is_file() or entry.name.startswith("."):
            continue
        try:
            fmt, loaded = _load_single_file(entry)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if fmt == "groww_tradebook" and tradebook_portfolio is None:
            tradebook_portfolio = loaded
        elif fmt != "groww_tradebook" and holdings_portfolio is None:
            holdings_portfolio = loaded

    if holdings_portfolio is not None and tradebook_portfolio is not None:
        return _merge_holdings_and_tradebook(holdings_portfolio, tradebook_portfolio)
    if holdings_portfolio is not None:
        return holdings_portfolio
    if tradebook_portfolio is not None:
        return tradebook_portfolio
    raise FileNotFoundError(f"No portfolio files found in {directory}")


def load_portfolio(
    path: Union[str, Path],
    tradebook_path: Union[str, Path, None] = None,
) -> Portfolio:
    """Load a Portfolio from a file or directory.

    When *path* is a directory containing both a Holdings file and a Tradebook
    file (or when *tradebook_path* is explicitly supplied), Holdings provide the
    current Holdings list and the Tradebook enriches each Holding with
    ``buy_date`` and weighted-average ``buy_price`` from BUY transactions.
    """
    target = Path(path)
    if target.is_dir():
        return _load_directory(target)

    _, portfolio = _load_single_file(target)
    if tradebook_path is not None:
        _, tb_portfolio = _load_single_file(Path(tradebook_path))
        return _merge_holdings_and_tradebook(portfolio, tb_portfolio)
    return portfolio
