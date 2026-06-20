"""Run weekly meetings with live pixel-agents events."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any

from agents.registry import get_default_team
from agents.portfolio_manager import PortfolioManager
from core.decision_log import DecisionLog
from core.models import (
    AgentReport,
    AgentUtterance,
    MeetingContext,
    MeetingPhase,
    MeetingRecord,
)
from core.orchestrator import MeetingResult, TradingOfficeOrchestrator
from server.pixel_bridge import PixelBridge

EventCallback = Callable[[dict[str, Any]], Awaitable[None] | None]


class LiveMeetingRunner:
    """Execute a meeting step-by-step, broadcasting events to WebSocket clients."""

    def __init__(
        self,
        on_event: EventCallback | None = None,
        step_delay: float = 0.6,
    ) -> None:
        self.on_event = on_event
        self.step_delay = step_delay
        self.bridge = PixelBridge()
        self.orchestrator = TradingOfficeOrchestrator(auto_log=True)

    async def emit(self, message: dict[str, Any]) -> None:
        if self.on_event:
            result = self.on_event(message)
            if asyncio.iscoroutine(result):
                await result
        await asyncio.sleep(self.step_delay)

    async def run(
        self, context: MeetingContext | None = None
    ) -> MeetingResult:
        if context is None:
            try:
                from core.data.context_builder import build_meeting_context

                context = build_meeting_context()
            except Exception:
                from core.orchestrator import create_sample_context

                context = create_sample_context()

        start = time.perf_counter()
        pm = PortfolioManager()
        specialists = get_default_team()
        utterances: list[AgentUtterance] = []
        participants = [pm.name] + [a.name for a in specialists]

        await self.emit(
            self.bridge.trading_meeting_event(
                "meeting_started",
                {"date": context.meeting_date.isoformat(), "participants": participants},
            )
        )

        # OPENING
        agent_id = self.bridge.resolve_agent_id(name=pm.name)
        tool_id = f"opening-{uuid.uuid4().hex[:8]}"
        await self.emit(self.bridge.agent_status(agent_id, "active"))
        await self.emit(
            self.bridge.agent_tool_start(agent_id, tool_id, "Opening weekly meeting…")
        )
        pm_opening = pm.analyze(context)
        utterances.append(pm.speak(pm_opening, MeetingPhase.OPENING))
        await self.emit(self.bridge.agent_tool_done(agent_id, tool_id))
        await self.emit(self.bridge.agent_tools_clear(agent_id))
        await self.emit(
            self.bridge.trading_meeting_event(
                "utterance",
                {
                    "phase": MeetingPhase.OPENING.value,
                    "agent": pm.name,
                    "content": utterances[-1].content,
                },
            )
        )

        # REPORTS
        reports: list[AgentReport] = [pm_opening]
        for agent in specialists:
            agent_id = self.bridge.resolve_agent_id(name=agent.name, role=agent.role)
            tool_id = f"report-{uuid.uuid4().hex[:8]}"
            await self.emit(self.bridge.agent_status(agent_id, "active"))
            await self.emit(
                self.bridge.agent_tool_start(
                    agent_id, tool_id, f"{agent.name} preparing report…"
                )
            )
            report = agent.analyze(context)
            reports.append(report)
            utterances.append(agent.speak(report, MeetingPhase.REPORT))
            await self.emit(self.bridge.agent_tool_done(agent_id, tool_id))
            await self.emit(self.bridge.agent_tools_clear(agent_id))
            await self.emit(self.bridge.agent_status(agent_id, "waiting"))
            await self.emit(
                self.bridge.trading_meeting_event(
                    "utterance",
                    {
                        "phase": MeetingPhase.REPORT.value,
                        "agent": agent.name,
                        "content": utterances[-1].content,
                        "summary": report.summary,
                    },
                )
            )

        # DELIBERATION + DECISION (Grok-assisted when configured)
        agent_id = self.bridge.resolve_agent_id(name=pm.name)
        tool_label = (
            "LLM deliberating team reports…"
            if pm._llm and pm._llm.available  # noqa: SLF001
            else "Synthesizing team reports…"
        )
        tool_id = f"delib-{uuid.uuid4().hex[:8]}"
        await self.emit(self.bridge.agent_status(agent_id, "active"))
        await self.emit(self.bridge.agent_tool_start(agent_id, tool_id, tool_label))
        decision = pm.decide(context, reports)
        deliberation = (
            decision.deliberation
            or TradingOfficeOrchestrator._build_deliberation(reports)
        )
        utterances.append(
            AgentUtterance(
                agent_name=pm.name,
                role=pm.role,
                phase=MeetingPhase.DELIBERATION,
                content=deliberation,
            )
        )
        await self.emit(self.bridge.agent_tool_done(agent_id, tool_id))
        await self.emit(
            self.bridge.trading_meeting_event(
                "utterance",
                {
                    "phase": MeetingPhase.DELIBERATION.value,
                    "agent": pm.name,
                    "content": deliberation,
                },
            )
        )

        tool_id = f"decide-{uuid.uuid4().hex[:8]}"
        await self.emit(
            self.bridge.agent_tool_start(agent_id, tool_id, "Issuing portfolio decision…")
        )
        utterances.append(
            AgentUtterance(
                agent_name=pm.name,
                role=pm.role,
                phase=MeetingPhase.DECISION,
                content=decision.summary,
            )
        )
        await self.emit(self.bridge.agent_tool_done(agent_id, tool_id))
        await self.emit(self.bridge.agent_tools_clear(agent_id))
        await self.emit(self.bridge.agent_status(agent_id, "waiting"))

        meeting_id = str(uuid.uuid4())
        meeting_record = MeetingRecord(
            meeting_id=meeting_id,
            meeting_date=context.meeting_date,
            participants=participants,
            utterances=utterances,
            meeting_summary=decision.summary,
            decision=decision,
        )

        log = DecisionLog()
        json_path, md_path = log.record(meeting_record)
        elapsed_ms = (time.perf_counter() - start) * 1000

        result = MeetingResult(
            decision=decision,
            meeting_record=meeting_record,
            json_log_path=str(json_path),
            md_log_path=str(md_path),
            duration_ms=round(elapsed_ms, 2),
            participants=participants,
        )

        trade_payload = [
            {
                "ticker": t.ticker,
                "action": t.action,
                "shares": t.shares,
                "rationale": t.rationale,
            }
            for t in decision.trades
        ]

        from server.pending_meeting import PendingMeeting, set_pending

        set_pending(
            PendingMeeting(
                meeting_id=meeting_id,
                json_file=json_path.name,
                summary=decision.summary,
                trade_count=len(decision.trades),
                trades=trade_payload,
                decision_source=decision.decision_source,
                approved=False,
            )
        )

        await self.emit(
            self.bridge.trading_meeting_event(
                "meeting_completed",
                {
                    "meeting_id": meeting_id,
                    "summary": decision.summary,
                    "trades": trade_payload,
                    "trade_count": len(decision.trades),
                    "decision_source": decision.decision_source,
                    "approved": False,
                    "requires_approval": True,
                    "json_log": str(json_path),
                    "md_log": str(md_path),
                    "duration_ms": result.duration_ms,
                },
            )
        )

        return result