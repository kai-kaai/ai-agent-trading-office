"""Shared data models for the AI Agent Trading Office."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import Enum
from typing import Any


class Recommendation(str, Enum):
    """Suggested action for a single stock position."""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class MeetingPhase(str, Enum):
    """Stages of a weekly portfolio meeting."""

    OPENING = "opening"
    REPORT = "report"
    DELIBERATION = "deliberation"
    DECISION = "decision"


@dataclass
class StockScore:
    """Fundamental or qualitative score for one ticker."""

    ticker: str
    score: float  # 0.0 – 100.0
    recommendation: Recommendation
    rationale: str
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentReport:
    """Structured output produced by an agent during a weekly meeting."""

    agent_name: str
    role: str
    summary: str
    stock_scores: list[StockScore] = field(default_factory=list)
    key_points: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AgentUtterance:
    """A single spoken contribution during a meeting phase."""

    agent_name: str
    role: str
    phase: MeetingPhase
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class PortfolioPosition:
    """A single holding in the current portfolio."""

    ticker: str
    shares: float
    avg_cost: float
    sector: str = "technology"
    current_price: float | None = None

    @property
    def market_value(self) -> float:
        """Return current market value, falling back to cost basis."""
        price = self.current_price if self.current_price is not None else self.avg_cost
        return self.shares * price


@dataclass
class MeetingContext:
    """Shared state passed to every agent before a weekly meeting."""

    meeting_date: date
    portfolio: list[PortfolioPosition]
    cash_balance: float
    watchlist: list[str] = field(default_factory=list)
    monthly_capital_injection: float = 305.0
    is_first_trading_day_of_month: bool = False
    benchmark_holdings: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def total_portfolio_value(self) -> float:
        """Total portfolio value including cash."""
        positions_value = sum(p.market_value for p in self.portfolio)
        return positions_value + self.cash_balance


@dataclass
class TradeAction:
    """A concrete buy or sell instruction."""

    ticker: str
    action: str  # "buy" | "sell"
    shares: float
    rationale: str
    estimated_value: float | None = None


@dataclass
class PortfolioDecision:
    """Final portfolio adjustment decided by the Portfolio Manager."""

    meeting_date: date
    trades: list[TradeAction]
    summary: str
    reasoning: list[str]
    agent_reports: list[AgentReport]
    approved: bool = False
    deliberation: str | None = None
    decision_source: str = "rule_based"
    decided_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class MeetingRecord:
    """Complete record of a weekly meeting including transcript and decision."""

    meeting_id: str
    meeting_date: date
    participants: list[str]
    utterances: list[AgentUtterance]
    meeting_summary: str
    decision: PortfolioDecision
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
