"""Fundamental metrics from Tech Titans CSV snapshots."""

from __future__ import annotations

from datetime import date
from functools import lru_cache

from backtest.data_loader import DEFAULT_CSV, StockSnapshot, TechTitansData


def fundamental_score(snapshot: StockSnapshot) -> float:
    """Score a stock using Tech Titans CSV fundamentals (0–100)."""
    score = 50.0

    pe = snapshot.pe_ratio
    if pe is not None:
        if pe > 0:
            if pe < 15:
                score += 15
            elif pe < 25:
                score += 10
            elif pe < 40:
                score += 5
            elif pe > 60:
                score -= 10
        else:
            score -= 15

    if snapshot.fcf_yield is not None:
        if snapshot.fcf_yield >= 0.10:
            score += 15
        elif snapshot.fcf_yield >= 0.05:
            score += 8
        elif snapshot.fcf_yield < 0:
            score -= 10

    if snapshot.operating_margin is not None:
        if snapshot.operating_margin >= 0.25:
            score += 10
        elif snapshot.operating_margin >= 0.15:
            score += 5
        elif snapshot.operating_margin < 0.05:
            score -= 8

    if snapshot.return_on_common is not None:
        if snapshot.return_on_common >= 0.20:
            score += 8
        elif snapshot.return_on_common < 0:
            score -= 5

    if snapshot.price_52w_high_pct is not None:
        if snapshot.price_52w_high_pct > 0.95:
            score -= 5
        elif snapshot.price_52w_high_pct < 0.50:
            score += 3

    return max(0.0, min(100.0, score))


class FundamentalService:
    """Lookup fundamental snapshots for agent scoring."""

    def __init__(self, csv_path: str | None = None) -> None:
        self._data = TechTitansData(csv_path or DEFAULT_CSV)

    def snapshot(self, ticker: str, on_date: date) -> StockSnapshot | None:
        """Return the CSV snapshot for a ticker on the nearest month."""
        month_date = self._data.month_for(on_date)
        snap = self._data.snapshot(ticker, month_date)
        if snap is not None:
            return snap

        for month in reversed(self._data.months):
            if month > month_date:
                continue
            snap = self._data.snapshot(ticker, month)
            if snap is not None:
                return snap
        return None

    def score(self, ticker: str, on_date: date) -> tuple[float, StockSnapshot | None]:
        """Return fundamental score and optional snapshot."""
        snap = self.snapshot(ticker, on_date)
        if snap is None:
            return 45.0, None
        return fundamental_score(snap), snap

    def metrics_dict(self, snap: StockSnapshot) -> dict[str, float | str | None]:
        """Flatten snapshot fields for agent report metrics."""
        return {
            "pe_ratio": snap.pe_ratio,
            "fcf_yield": snap.fcf_yield,
            "operating_margin": snap.operating_margin,
            "return_on_common": snap.return_on_common,
            "revenue_b": snap.revenue_b,
            "net_income_b": snap.net_income_b,
            "market_cap_b": snap.market_cap_b,
            "price_52w_high_pct": snap.price_52w_high_pct,
            "sector": snap.sector,
            "data_source": "tech_titans_csv",
        }


@lru_cache(maxsize=1)
def get_fundamental_service() -> FundamentalService:
    """Return a shared fundamental data service."""
    return FundamentalService()