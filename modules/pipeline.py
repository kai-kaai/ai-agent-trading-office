"""Trading pipeline — every signal must pass The Brain before downstream modules."""

from __future__ import annotations

from dataclasses import dataclass, field

from modules.auditor import AuditorModule
from modules.brain import BrainModule
from modules.cfo import CFOModule
from modules.models import PipelineResult, PipelineStage, ShieldVerdict
from modules.shield import ShieldModule
from modules.watchman import WatchmanModule


@dataclass
class PipelineContext:
    """Inputs shared across pipeline stages."""

    nav_usd: float = 10_000.0
    volatility_regime: str = "normal"
    risk_reward: float = 2.0
    current_sectors: list[str] = field(default_factory=list)


class TradingPipeline:
    """Orchestrates Brain → Shield → CFO → Watchman.

    The Auditor runs post-trade and is not part of this forward path.
    Legacy weekly meetings (`core/orchestrator.py`) remain available.
    """

    STAGES = (
        PipelineStage.BRAIN,
        PipelineStage.SHIELD,
        PipelineStage.CFO,
        PipelineStage.WATCHMAN,
        PipelineStage.COMPLETE,
    )

    def __init__(
        self,
        brain: BrainModule | None = None,
        shield: ShieldModule | None = None,
        cfo: CFOModule | None = None,
        watchman: WatchmanModule | None = None,
        auditor: AuditorModule | None = None,
    ) -> None:
        self.brain = brain or BrainModule()
        self.shield = shield or ShieldModule()
        self.cfo = cfo or CFOModule()
        self.watchman = watchman or WatchmanModule()
        self.auditor = auditor or AuditorModule()
        self._last_setup: dict | None = None

    def run(
        self,
        ticker: str,
        action: str = "buy",
        *,
        score_override: float | None = None,
        context: PipelineContext | None = None,
    ) -> PipelineResult:
        ctx = context or PipelineContext()
        events: list[str] = []

        setup = self.brain.evaluate(ticker, action=action, score_override=score_override)
        self._last_setup = {"score": setup.score, "grade": setup.grade.value, "ticker": setup.ticker}
        events.append(f"brain: {setup.council.summary}")

        if not setup.council.passed:
            return PipelineResult(
                stage_reached=PipelineStage.BRAIN,
                halted=True,
                setup=setup,
                halt_reason=setup.council.summary,
                events=events,
            )

        shield = self.shield.evaluate(
            setup,
            risk_reward=ctx.risk_reward,
            current_sectors=ctx.current_sectors,
        )
        events.append(f"shield: {shield.verdict.value}")

        if shield.verdict is not ShieldVerdict.GO:
            return PipelineResult(
                stage_reached=PipelineStage.SHIELD,
                halted=True,
                setup=setup,
                shield=shield,
                halt_reason="; ".join(shield.reasons),
                events=events,
            )

        sized = self.cfo.size(
            setup,
            nav_usd=ctx.nav_usd,
            volatility_regime=ctx.volatility_regime,
            risk_reward=ctx.risk_reward,
        )
        events.append(f"cfo: sized {sized.shares:.2f} shares @ {sized.risk_pct * 100:.2f}% risk")

        position = self.watchman.plan_entry(sized)
        position = self.watchman.activate(position)  # A4: immediately ready (paper fill)
        events.append(f"watchman: {position.state.value} position {position.position_id}")

        # Record trailing info in event for observability
        trail_info = f"trail={position.trailing_stop}" if position.trailing_stop else ""
        events.append(f"watchman_position:{position.position_id} {trail_info}")

        return PipelineResult(
            stage_reached=PipelineStage.COMPLETE,
            halted=False,
            setup=setup,
            shield=shield,
            sized_order=sized,
            events=events,
        )

    def audit_closed_position(
        self,
        position,  # LivePosition after CLOSED
        outcome: str = "closed",
        *,
        trade_id: str | None = None,
        entry_setup: dict | None = None,
    ) -> "TradeAutopsy":
        """Post-trade hook (A5): run Auditor on a closed position from Watchman."""
        from modules.models import TradeAutopsy  # local to avoid circular

        if trade_id is None:
            trade_id = f"trade-{position.ticker}-{position.position_id[-6:]}"

        return self.auditor.autopsy_from_position(
            trade_id=trade_id,
            position=position,
            outcome=outcome,
            entry_setup=entry_setup or self._last_setup,
        )

    @staticmethod
    def describe() -> dict:
        return {
            "pipeline": "Brain → Shield → CFO → Watchman",
            "gate": "All signals must pass The Brain first; Risk Chair may veto.",
            "stages": [stage.value for stage in TradingPipeline.STAGES],
            "legacy": "Weekly meeting orchestrator remains at core/orchestrator.py",
            "brain": "Phase 1 — scanners + AI Council (LLM or rule-based)",
            "shield": "A2 — RRR >= 2.0, min grade B, sector overlap <= 4 per sector (for buys)",
            "cfo": "A3 — 1% NAV risk (scaled by vol regime + conviction), dynamic stop, RRR-aware TP",
            "watchman": "A4 — plan + activate + trailing stop management (paper first); states PENDING→OPEN→TRAILING→CLOSED",
            "auditor": "A5 — autopsy (metrics + auto lessons), propose/promote candidates, attach backtests. Promotion: CANDIDATE → BACKTEST → SANDBOX → LIVE (post-trade)",
        }