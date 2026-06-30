"""Backtest engine for AI Agent Trading Office."""

from __future__ import annotations

from importlib import import_module
from typing import Any

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

_EXPORT_MODULES = {
    "BacktestComparison": "backtest.models",
    "BacktestEngine": "backtest.engine",
    "BacktestResult": "backtest.models",
    "DEFAULT_MONTHS": "backtest.engine",
    "build_context_extra": "backtest.context",
    "format_report": "backtest.report",
    "get_cached_comparison": "backtest.context",
    "run_and_cache": "backtest.context",
}


def __getattr__(name: str) -> Any:
    """Load public exports on demand to keep submodule imports cycle-free."""
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
