"""Orchestrator – coordinates the weekly multi-agent meeting cycle."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Sequence

from core.base_agent import BaseAgent
from core.decision_log import DecisionLog
from core.models import (
    AgentReport,
    AgentUtterance,
    MeetingContext,
    MeetingPhase,
    MeetingRecord,
    PortfolioDecision,
    PortfolioPosition,
)


@dataclass
class MeetingResult:
    """Outcome of a full weekly meeting cycle."""

    decision: PortfolioDecision
    meeting_record: MeetingRecord
    json_log_path: str | None = None
    md_log_path: str | None = None
    duration_ms: float = 0.0
    participants: list[str] = field(default_factory=list)


class TradingOfficeOrchestrator:
    """Runs the weekly agent meeting and persists the outcome.

    Workflow (per AGENTS.md):
    1. Portfolio Manager convenes the meeting
    2. Each agent submits a report
    3. Agents deliberate (Phase 1: rule-based synthesis)
    4. Portfolio Manager decides
    5. Decision is recorded in the Decision Log

    Args:
        portfolio_manager: The PM agent that chairs meetings.
        agents: Specialist agents that submit reports.
        decision_log: Optional :class:`DecisionLog` instance.
        auto_log: When True, automatically write decisions to the log.
    """

    def __init__(
        self,
        portfolio_manager: BaseAgent | None = None,
        agents: Sequence[BaseAgent] | None = None,
        decision_log: DecisionLog | None = None,
        auto_log: bool = True,
    ) -> None:
        # Lazy import to avoid circular dependency at module load time.
        if portfolio_manager is None:
            from agents.portfolio_manager import PortfolioManager
            portfolio_manager = PortfolioManager()
        if agents is None:
            from agents.registry import get_default_team
            agents = get_default_team()

        self.portfolio_manager = portfolio_manager
        self.agents: list[BaseAgent] = list(agents)
        self.decision_log = decision_log or DecisionLog()
        self.auto_log = auto_log

    def run_weekly_meeting(self, context: MeetingContext) -> MeetingResult:
        """Execute the full weekly meeting cycle with transcript tracking.

        Args:
            context: Shared portfolio and market state for this meeting.

        Returns:
            :class:`MeetingResult` with decision, transcript, and log paths.
        """
        start = time.perf_counter()
        utterances: list[AgentUtterance] = []
        participants = [self.portfolio_manager.name] + [a.name for a in self.agents]

        # Phase 1 – OPENING: Portfolio Manager opens the meeting
        pm_opening = self.portfolio_manager.analyze(context)
        utterances.append(
            self.portfolio_manager.speak(pm_opening, MeetingPhase.OPENING)
        )

        # Phase 2 – REPORT: Each specialist agent submits a report
        reports: list[AgentReport] = [pm_opening]
        for agent in self.agents:
            report = agent.analyze(context)
            reports.append(report)
            utterances.append(agent.speak(report, MeetingPhase.REPORT))

        # Phase 3 – DELIBERATION: PM synthesizes key themes
        deliberation = self._build_deliberation(reports)
        utterances.append(
            AgentUtterance(
                agent_name=self.portfolio_manager.name,
                role=self.portfolio_manager.role,
                phase=MeetingPhase.DELIBERATION,
                content=deliberation,
            )
        )

        # Phase 4 – DECISION: PM issues final portfolio orders
        decision = self.portfolio_manager.decide(context, reports)  # type: ignore[attr-defined]
        utterances.append(
            AgentUtterance(
                agent_name=self.portfolio_manager.name,
                role=self.portfolio_manager.role,
                phase=MeetingPhase.DECISION,
                content=decision.summary,
            )
        )

        meeting_record = MeetingRecord(
            meeting_id=str(uuid.uuid4()),
            meeting_date=context.meeting_date,
            participants=participants,
            utterances=utterances,
            meeting_summary=decision.summary,
            decision=decision,
        )

        json_log_path: str | None = None
        md_log_path: str | None = None
        if self.auto_log:
            json_path, md_path = self.decision_log.record(meeting_record)
            json_log_path = str(json_path)
            md_log_path = str(md_path)

        elapsed_ms = (time.perf_counter() - start) * 1000

        return MeetingResult(
            decision=decision,
            meeting_record=meeting_record,
            json_log_path=json_log_path,
            md_log_path=md_log_path,
            duration_ms=round(elapsed_ms, 2),
            participants=participants,
        )

    def approve_decision(
        self, meeting_record: MeetingRecord, approved: bool = True
    ) -> MeetingRecord:
        """Mark a decision as human-approved (semi-auto mode).

        In semi-auto mode the human reviewer approves or rejects the
        proposed trades before execution.
        """
        meeting_record.decision.approved = approved
        if self.auto_log:
            self.decision_log.record(meeting_record)
        return meeting_record

    @staticmethod
    def _build_deliberation(reports: list[AgentReport]) -> str:
        """Synthesize specialist reports into a deliberation summary."""
        lines = ["Key themes from this week's reports:"]

        all_warnings: list[str] = []
        for report in reports:
            if report.agent_name == "Portfolio Manager":
                continue
            lines.append(f"• {report.agent_name}: {report.summary}")
            all_warnings.extend(report.warnings)

        if all_warnings:
            lines.append("")
            lines.append("Risk flags to consider:")
            for warning in all_warnings[:5]:
                lines.append(f"  ⚠ {warning}")
        else:
            lines.append("No major risk flags raised.")

        return "\n".join(lines)


def create_sample_context(meeting_date: date | None = None) -> MeetingContext:
    """Build a minimal demo context for smoke-testing the orchestrator."""
    meeting_date = meeting_date or date.today()
    return MeetingContext(
        meeting_date=meeting_date,
        portfolio=[
            PortfolioPosition("AAPL", shares=2.0, avg_cost=190.0, sector="technology"),
            PortfolioPosition("MSFT", shares=1.5, avg_cost=420.0, sector="technology"),
            PortfolioPosition("NVDA", shares=0.5, avg_cost=900.0, sector="semiconductor"),
        ],
        cash_balance=150.0,
        watchlist=["GOOGL", "META", "AMD"],
        is_first_trading_day_of_month=meeting_date.day <= 7,
    )