"""Base agent class for the AI Agent Trading Office."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.models import (
    AgentReport,
    AgentUtterance,
    MeetingContext,
    MeetingPhase,
    StockScore,
)


class BaseAgent(ABC):
    """Abstract base class for all trading-office agents.

    Each agent receives a :class:`MeetingContext`, performs its specialty
    analysis, and returns an :class:`AgentReport` for the weekly meeting.
    """

    def __init__(self, name: str, role: str, description: str) -> None:
        self.name = name
        self.role = role
        self.description = description

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, role={self.role!r})"

    @abstractmethod
    def analyze(self, context: MeetingContext) -> AgentReport:
        """Analyze the current market/portfolio state and produce a report.

        Args:
            context: Shared meeting context with portfolio and market data.

        Returns:
            Structured report for discussion in the weekly meeting.
        """

    def speak(self, report: AgentReport, phase: MeetingPhase) -> AgentUtterance:
        """Convert a report into a human-readable meeting utterance.

        Args:
            report: The agent's structured report.
            phase: Which meeting phase this contribution belongs to.

        Returns:
            Transcript entry suitable for the Decision Log.
        """
        lines = [report.summary]

        for point in report.key_points:
            lines.append(f"• {point}")

        for warning in report.warnings:
            lines.append(f"⚠ {warning}")

        if report.stock_scores and phase == MeetingPhase.REPORT:
            top_scores = sorted(report.stock_scores, key=lambda s: s.score, reverse=True)[:3]
            score_line = ", ".join(f"{s.ticker} ({s.score:.0f})" for s in top_scores)
            lines.append(f"Top scores: {score_line}")

        return AgentUtterance(
            agent_name=self.name,
            role=self.role,
            phase=phase,
            content="\n".join(lines),
        )

    def _build_report(
        self,
        summary: str,
        *,
        stock_scores: list[StockScore] | None = None,
        key_points: list[str] | None = None,
        warnings: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentReport:
        """Helper to construct an :class:`AgentReport` with agent identity."""
        return AgentReport(
            agent_name=self.name,
            role=self.role,
            summary=summary,
            stock_scores=stock_scores or [],
            key_points=key_points or [],
            warnings=warnings or [],
            metadata=metadata or {},
        )