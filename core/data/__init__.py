"""Shared data services for agent analysis.

Keep the meeting-context builder lazy: it depends on the backtest package, while
the backtest strategy imports the fundamental scoring service from this package.
Importing both eagerly creates a circular import for ``python -m backtest``.
"""

from __future__ import annotations

from datetime import date

from core.data.fundamentals import FundamentalService, fundamental_score
from core.data.market_data import MarketDataService
from core.data.news import NewsSentimentService
from core.data.tickers import collect_tickers
from core.models import MeetingContext


def build_meeting_context(meeting_date: date | None = None) -> MeetingContext:
    """Build a meeting context without importing backtest code at package load."""
    from core.data.context_builder import build_meeting_context as _build

    return _build(meeting_date)

__all__ = [
    "FundamentalService",
    "MarketDataService",
    "NewsSentimentService",
    "build_meeting_context",
    "collect_tickers",
    "fundamental_score",
]
