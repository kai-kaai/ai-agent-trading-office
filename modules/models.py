"""Pipeline data models for the 5-module trading architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import Enum
from typing import Any


class SetupGrade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"


class VoteDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class CouncilMember(str, Enum):
    BEAR = "bear"
    BULL = "bull"
    RISK_CHAIR = "risk_chair"


class ShieldVerdict(str, Enum):
    GO = "go"
    PASS = "pass"
    DEFER = "defer"


class PipelineStage(str, Enum):
    BRAIN = "brain"
    SHIELD = "shield"
    CFO = "cfo"
    WATCHMAN = "watchman"
    AUDITOR = "auditor"
    COMPLETE = "complete"


class PositionState(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    TRAILING = "trailing"
    CLOSED = "closed"


class StrategyStage(str, Enum):
    CANDIDATE = "candidate"
    BACKTEST = "backtest"
    SANDBOX = "sandbox"
    LIVE = "live"
    REJECTED = "rejected"


@dataclass
class CouncilVote:
    member: CouncilMember
    decision: VoteDecision
    rationale: str
    veto: bool = False


@dataclass
class CouncilVerdict:
    votes: list[CouncilVote]
    approval_count: int
    passed: bool
    vetoed: bool
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "votes": [
                {
                    "member": vote.member.value,
                    "decision": vote.decision.value,
                    "rationale": vote.rationale,
                    "veto": vote.veto,
                }
                for vote in self.votes
            ],
            "approval_count": self.approval_count,
            "passed": self.passed,
            "vetoed": self.vetoed,
            "summary": self.summary,
        }


@dataclass
class TradeSetup:
    ticker: str
    action: str
    grade: SetupGrade
    score: float
    council: CouncilVerdict
    sector: str | None = None
    sector_strength: float | None = None
    structure_notes: list[str] = field(default_factory=list)
    news_sentiment: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "action": self.action,
            "grade": self.grade.value,
            "score": round(self.score, 2),
            "council": self.council.to_dict(),
            "sector": self.sector,
            "sector_strength": self.sector_strength,
            "structure_notes": self.structure_notes,
            "news_sentiment": self.news_sentiment,
            "metadata": self.metadata,
            "evaluated_at": self.evaluated_at.isoformat(),
        }


@dataclass
class ShieldDecision:
    verdict: ShieldVerdict
    risk_reward: float | None
    overlap_warnings: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "risk_reward": self.risk_reward,
            "overlap_warnings": self.overlap_warnings,
            "reasons": self.reasons,
        }


@dataclass
class SizedOrder:
    ticker: str
    action: str
    shares: float
    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None
    risk_pct: float
    max_loss_usd: float
    volatility_regime: str = "normal"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "action": self.action,
            "shares": round(self.shares, 4),
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_pct": round(self.risk_pct, 4),
            "max_loss_usd": round(self.max_loss_usd, 2),
            "volatility_regime": self.volatility_regime,
        }


@dataclass
class LivePosition:
    position_id: str
    ticker: str
    action: str
    shares: float
    entry_price: float
    stop_loss: float | None
    take_profit: float | None
    state: PositionState
    opened_at: datetime
    trailing_stop: float | None = None
    last_price: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "position_id": self.position_id,
            "ticker": self.ticker,
            "action": self.action,
            "shares": round(self.shares, 4),
            "entry_price": round(self.entry_price, 4),
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "state": self.state.value,
            "opened_at": self.opened_at.isoformat(),
            "trailing_stop": self.trailing_stop,
            "last_price": self.last_price,
        }

    def is_long(self) -> bool:
        return self.action.lower() != "sell"

    def unrealized_pnl_pct(self, price: float | None = None) -> float | None:
        p = price or self.last_price
        if p is None or self.entry_price == 0:
            return None
        if self.is_long():
            return (p - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - p) / self.entry_price


@dataclass
class TradeAutopsy:
    trade_id: str
    ticker: str
    outcome: str
    lessons: list[str]
    mistakes: list[str]
    strengths: list[str]
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    entry_price: float | None = None
    exit_price: float | None = None
    pnl_pct: float | None = None
    r_multiple: float | None = None
    metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "ticker": self.ticker,
            "outcome": self.outcome,
            "lessons": self.lessons,
            "mistakes": self.mistakes,
            "strengths": self.strengths,
            "reviewed_at": self.reviewed_at.isoformat(),
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "pnl_pct": self.pnl_pct,
            "r_multiple": self.r_multiple,
            "metrics": self.metrics,
        }


@dataclass
class StrategyCandidate:
    strategy_id: str
    name: str
    hypothesis: str
    stage: StrategyStage
    source_autopsy_id: str | None = None
    backtest_metrics: dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "hypothesis": self.hypothesis,
            "stage": self.stage.value,
            "source_autopsy_id": self.source_autopsy_id,
            "backtest_metrics": self.backtest_metrics,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class PipelineResult:
    stage_reached: PipelineStage
    halted: bool
    setup: TradeSetup | None = None
    shield: ShieldDecision | None = None
    sized_order: SizedOrder | None = None
    halt_reason: str | None = None
    events: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_reached": self.stage_reached.value,
            "halted": self.halted,
            "setup": self.setup.to_dict() if self.setup else None,
            "shield": self.shield.to_dict() if self.shield else None,
            "sized_order": self.sized_order.to_dict() if self.sized_order else None,
            "halt_reason": self.halt_reason,
            "events": self.events,
        }