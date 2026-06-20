"""Backtest engine for AI Agent Trading Office."""

from backtest.context import build_context_extra, get_cached_comparison, run_and_cache
from backtest.engine import BacktestEngine, DEFAULT_MONTHS
from backtest.models import BacktestComparison, BacktestResult
from backtest.report import format_report

__all__ = [
    "BacktestComparison",
    "BacktestEngine",
    "BacktestResult",
    "DEFAULT_MONTHS",
    "build_context_extra",
    "format_report",
    "get_cached_comparison",
    "run_and_cache",
]