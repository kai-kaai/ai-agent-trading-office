"""Shared date helpers for backtest simulations."""

from __future__ import annotations

from datetime import date, timedelta


def iter_weekly_dates(start: date, end: date) -> list[date]:
    """Generate weekly rebalance dates from start through end."""
    cursor = start
    dates: list[date] = []
    while cursor <= end:
        dates.append(cursor)
        cursor += timedelta(days=7)
    if not dates or dates[-1] < end:
        dates.append(end)
    return dates