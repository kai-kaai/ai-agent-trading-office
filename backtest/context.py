"""Bridge backtest metrics into MeetingContext for agents."""

from __future__ import annotations

from datetime import date
from typing import Any

from backtest.engine import BacktestEngine, DEFAULT_MONTHS
from backtest.models import BacktestComparison

_cached_comparison: BacktestComparison | None = None


def run_and_cache(months: int = DEFAULT_MONTHS) -> BacktestComparison:
    """Run backtest once and cache the latest comparison."""
    global _cached_comparison
    _cached_comparison = BacktestEngine().run(months=months)
    return _cached_comparison


def get_cached_comparison() -> BacktestComparison | None:
    """Return the most recent cached comparison, if any."""
    return _cached_comparison


def build_context_extra(months: int = DEFAULT_MONTHS) -> dict[str, Any]:
    """Build ``context.extra`` fields for Backtester & Evaluator."""
    comparison = _cached_comparison or run_and_cache(months=months)
    return {
        "portfolio_return": comparison.agent.total_return,
        "benchmark_return": comparison.benchmark.total_return,
        "alpha": comparison.alpha,
        "decisions_evaluated": len(comparison.agent.trades),
        "decision_quality_score": min(
            100.0, max(0.0, 50.0 + comparison.alpha * 200)
        ),
        "backtest_start": comparison.agent.start_date.isoformat(),
        "backtest_end": comparison.agent.end_date.isoformat(),
        "final_nav": comparison.agent.final_nav,
        "benchmark_final_nav": comparison.benchmark.final_nav,
    }


def benchmark_holdings_for(meeting_date: date | None = None) -> list[str]:
    """Return Tech Titans tickers for the meeting month."""
    from backtest.data_loader import TechTitansData

    data = TechTitansData()
    on_date = meeting_date or date.today()
    month_date = data.month_for(on_date)
    return data.tickers(month_date)