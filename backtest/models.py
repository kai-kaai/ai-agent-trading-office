"""Data models for backtest results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class TradeRecord:
    """A single simulated trade."""

    date: date
    ticker: str
    action: str
    shares: float
    price: float
    value: float
    rationale: str = ""


@dataclass
class NavSnapshot:
    """Portfolio NAV at a point in time."""

    date: date
    nav: float
    cash: float
    holdings_count: int
    injected_capital: float


@dataclass
class BacktestResult:
    """Outcome of a portfolio simulation."""

    name: str
    start_date: date
    end_date: date
    total_injected: float
    final_nav: float
    total_return: float
    nav_history: list[NavSnapshot] = field(default_factory=list)
    trades: list[TradeRecord] = field(default_factory=list)
    final_holdings: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API responses."""
        return {
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_injected": round(self.total_injected, 2),
            "final_nav": round(self.final_nav, 2),
            "total_return": round(self.total_return, 6),
            "total_return_pct": round(self.total_return * 100, 2),
            "nav_history": [
                {
                    "date": snap.date.isoformat(),
                    "nav": round(snap.nav, 2),
                    "cash": round(snap.cash, 2),
                    "holdings_count": snap.holdings_count,
                    "injected_capital": round(snap.injected_capital, 2),
                }
                for snap in self.nav_history
            ],
            "trade_count": len(self.trades),
            "final_holdings": {
                ticker: round(shares, 4) for ticker, shares in self.final_holdings.items()
            },
        }


@dataclass
class BacktestComparison:
    """AI portfolio vs Tech Titans benchmark."""

    agent: BacktestResult
    benchmark: BacktestResult
    alpha: float
    months: int
    weekly_rebalances: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API responses."""
        return {
            "agent": self.agent.to_dict(),
            "benchmark": self.benchmark.to_dict(),
            "alpha": round(self.alpha, 6),
            "alpha_pct": round(self.alpha * 100, 2),
            "months": self.months,
            "weekly_rebalances": self.weekly_rebalances,
            "portfolio_return": self.agent.total_return,
            "benchmark_return": self.benchmark.total_return,
        }