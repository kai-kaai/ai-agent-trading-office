"""Load Tech Titans historical snapshots from CSV."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from backtest.parsers import parse_float, parse_multiple, parse_percent

DEFAULT_CSV = (
    Path(__file__).resolve().parent.parent / "data" / "tech_titans_history_template.csv"
)


@dataclass(frozen=True)
class StockSnapshot:
    """One ticker row for a given rebalance month."""

    snapshot_date: date
    ticker: str
    name: str
    stock_exchange: str
    sector: str
    market_cap_b: float
    revenue_b: float | None
    net_income_b: float | None
    operating_margin: float | None
    price_ltm_sales: float | None
    pe_ratio: float | None
    fcf_yield: float | None
    return_on_common: float | None
    cash_ratio: float | None
    price_52w_high_pct: float | None

    @property
    def price_proxy(self) -> float:
        """Use market cap as a relative price proxy (offline-friendly)."""
        return max(self.market_cap_b, 0.01)


class TechTitansData:
    """Indexed access to monthly Tech Titans benchmark snapshots."""

    def __init__(self, csv_path: Path | str = DEFAULT_CSV) -> None:
        self.csv_path = Path(csv_path)
        self._by_month: dict[date, dict[str, StockSnapshot]] = {}
        self._months: list[date] = []
        self._load()

    def _load(self) -> None:
        with self.csv_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                snapshot_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                ticker = row["ticker"].strip().upper()
                snapshot = StockSnapshot(
                    snapshot_date=snapshot_date,
                    ticker=ticker,
                    name=row["name"].strip(),
                    stock_exchange=row["stock_exchange"].strip(),
                    sector=row["sector"].strip(),
                    market_cap_b=parse_float(row["market_cap_b"]) or 0.01,
                    revenue_b=parse_float(row["revenue_b"]),
                    net_income_b=parse_float(row["net_income_b"]),
                    operating_margin=parse_percent(row["operating_margin"]),
                    price_ltm_sales=parse_multiple(row["price_ltm_sales"]),
                    pe_ratio=parse_multiple(row["pe_ratio"]),
                    fcf_yield=parse_percent(row["fcf_yield"]),
                    return_on_common=parse_percent(row["return_on_common"]),
                    cash_ratio=parse_percent(row["cash_ratio"]),
                    price_52w_high_pct=parse_percent(row["price_52w_high_pct"]),
                )
                month_bucket = self._by_month.setdefault(snapshot_date, {})
                month_bucket[ticker] = snapshot

        self._months = sorted(self._by_month.keys())

    @property
    def months(self) -> list[date]:
        """All snapshot months in ascending order."""
        return list(self._months)

    def month_for(self, on_date: date) -> date:
        """Return the latest snapshot month on or before ``on_date``."""
        eligible = [month for month in self._months if month <= on_date]
        if not eligible:
            raise ValueError(f"No Tech Titans data on or before {on_date}")
        return eligible[-1]

    def holdings(self, month_date: date) -> list[StockSnapshot]:
        """Benchmark holdings for a snapshot month."""
        return list(self._by_month[month_date].values())

    def tickers(self, month_date: date) -> list[str]:
        """Ticker symbols for a snapshot month."""
        return list(self._by_month[month_date].keys())

    def snapshot(self, ticker: str, month_date: date) -> StockSnapshot | None:
        """Lookup one ticker for a given month, if present."""
        return self._by_month.get(month_date, {}).get(ticker.upper())

    def price(self, ticker: str, on_date: date) -> float:
        """Price proxy for a ticker on a calendar date."""
        month_date = self.month_for(on_date)
        snap = self.snapshot(ticker, month_date)
        if snap is None:
            # Fall back to the most recent month where the ticker appears.
            for month in reversed(self._months):
                snap = self.snapshot(ticker, month)
                if snap is not None:
                    return snap.price_proxy
            return 0.01
        return snap.price_proxy

    def available_window(self, months: int) -> tuple[date, date]:
        """Return a default simulation window covering the last ``months`` months."""
        if months > len(self._months):
            raise ValueError(
                f"Requested {months} months but only {len(self._months)} available."
            )
        end_date = self._months[-1]
        start_date = self._months[-months]
        return start_date, end_date