"""Ticker collection helpers shared across agents."""

from __future__ import annotations

from core.models import MeetingContext


def collect_tickers(context: MeetingContext) -> list[str]:
    """Merge portfolio tickers and watchlist, preserving order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for ticker in [p.ticker for p in context.portfolio] + context.watchlist:
        upper = ticker.upper()
        if upper not in seen:
            seen.add(upper)
            ordered.append(upper)
    return ordered