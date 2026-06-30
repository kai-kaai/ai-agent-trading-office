"""The Auditor — trade review and strategy promotion loop (Arch A5).

Performs post-trade autopsy, extracts lessons, proposes strategy candidates,
runs backtests for validation, and manages promotion: CANDIDATE → BACKTEST → SANDBOX → LIVE.
"""

from __future__ import annotations

from modules.models import StrategyCandidate, StrategyStage, TradeAutopsy

# Simple thresholds for auto-analysis
MIN_R_MULTIPLE_GOOD = 1.5
MAX_R_MULTIPLE_POOR = 0.5


class AuditorModule:
    """Auditor handles post-trade review and strategy evolution."""

    def autopsy_trade(
        self,
        trade_id: str,
        ticker: str,
        outcome: str,
        *,
        lessons: list[str] | None = None,
        mistakes: list[str] | None = None,
        strengths: list[str] | None = None,
        entry_price: float | None = None,
        exit_price: float | None = None,
        stop_price: float | None = None,  # for r-multiple calc
        metrics: dict[str, float] | None = None,
    ) -> TradeAutopsy:
        """Record a completed trade with optional price data for metrics."""
        autopsy = TradeAutopsy(
            trade_id=trade_id,
            ticker=ticker.upper(),
            outcome=outcome,
            lessons=lessons or [],
            mistakes=mistakes or [],
            strengths=strengths or [],
            entry_price=entry_price,
            exit_price=exit_price,
            metrics=metrics or {},
        )

        # Compute derived metrics if prices provided
        if entry_price and exit_price and entry_price > 0:
            pnl_pct = (exit_price - entry_price) / entry_price
            autopsy.pnl_pct = round(pnl_pct, 4)
            autopsy.metrics["pnl_pct"] = autopsy.pnl_pct

            if stop_price and stop_price != entry_price:
                risk = abs(entry_price - stop_price)
                if risk > 0:
                    r_multiple = (exit_price - entry_price) / risk if pnl_pct >= 0 else (exit_price - entry_price) / risk
                    autopsy.r_multiple = round(r_multiple, 2)
                    autopsy.metrics["r_multiple"] = autopsy.r_multiple

        # Auto-analyze if no explicit lessons provided
        if not (lessons or mistakes or strengths):
            auto = self._auto_analyze(autopsy)
            autopsy.lessons = auto["lessons"]
            autopsy.mistakes = auto["mistakes"]
            autopsy.strengths = auto["strengths"]

        return autopsy

    def _auto_analyze(self, autopsy: TradeAutopsy) -> dict[str, list[str]]:
        """Rule-based extraction of lessons from outcome and metrics."""
        lessons: list[str] = []
        mistakes: list[str] = []
        strengths: list[str] = []

        outcome = autopsy.outcome.lower()
        r = autopsy.r_multiple
        pnl = autopsy.pnl_pct

        if outcome in {"win", "profit", "tp", "take_profit"} or (pnl and pnl > 0):
            strengths.append("Captured positive outcome.")
            if r is not None and r >= MIN_R_MULTIPLE_GOOD:
                strengths.append(f"Good R-multiple ({r:.1f}) — solid risk-reward execution.")
            lessons.append("Repeat patterns that led to this win (check setup grade + structure).")
        elif outcome in {"loss", "stop", "sl", "stopped"} or (pnl and pnl < 0):
            mistakes.append("Trade resulted in loss.")
            if r is not None and r < MAX_R_MULTIPLE_POOR:
                mistakes.append(f"Poor R-multiple ({r:.1f}) — consider tighter entry or wider initial stop.")
            lessons.append("Review Brain scanners and Shield filters for this ticker.")
        else:
            lessons.append("Outcome unclear — record more price data next time.")

        if autopsy.metrics.get("hit_trailing"):
            strengths.append("Trailing stop protected gains.")

        return {"lessons": lessons, "mistakes": mistakes, "strengths": strengths}

    def propose_strategy(
        self, name: str, hypothesis: str, autopsy_id: str | None = None
    ) -> StrategyCandidate:
        """Create a new strategy candidate from autopsy insights."""
        return StrategyCandidate(
            strategy_id=f"strat-{name.lower().replace(' ', '-')}",
            name=name,
            hypothesis=hypothesis,
            stage=StrategyStage.CANDIDATE,
            source_autopsy_id=autopsy_id,
        )

    def promote(self, candidate: StrategyCandidate, new_stage: StrategyStage) -> StrategyCandidate:
        """Advance a candidate through the validation pipeline."""
        candidate.stage = new_stage
        return candidate

    def attach_backtest_results(
        self, candidate: StrategyCandidate, metrics: dict[str, float]
    ) -> StrategyCandidate:
        """Attach backtest performance (e.g. from BacktestEngine or custom sim)."""
        candidate.backtest_metrics.update({k: round(v, 4) for k, v in metrics.items()})
        if candidate.stage == StrategyStage.CANDIDATE:
            candidate.stage = StrategyStage.BACKTEST
        return candidate

    def review_and_promote(
        self,
        candidate: StrategyCandidate,
        backtest_metrics: dict[str, float] | None = None,
        sandbox_ok: bool = False,
        live_approved: bool = False,
    ) -> StrategyCandidate:
        """Convenience: progress candidate based on results."""
        if backtest_metrics:
            self.attach_backtest_results(candidate, backtest_metrics)

        if candidate.stage == StrategyStage.BACKTEST and backtest_metrics:
            # Simple rule: if positive alpha or good return, move to sandbox
            alpha = backtest_metrics.get("alpha", 0.0)
            if alpha > 0 or backtest_metrics.get("total_return", 0) > 0.05:
                candidate.stage = StrategyStage.SANDBOX

        if candidate.stage == StrategyStage.SANDBOX and sandbox_ok:
            candidate.stage = StrategyStage.LIVE

        if candidate.stage == StrategyStage.LIVE and not live_approved:
            # keep as candidate for semi-auto
            pass

        return candidate

    def autopsy_from_position(
        self,
        trade_id: str,
        position,  # LivePosition (closed)
        outcome: str,
        entry_setup: dict | None = None,
    ) -> TradeAutopsy:
        """Convenience helper: build autopsy from a closed LivePosition + optional setup data."""
        entry_p = getattr(position, "entry_price", None)
        exit_p = getattr(position, "last_price", None) or getattr(position, "exit_price", None)
        stop = getattr(position, "stop_loss", None) or getattr(position, "trailing_stop", None)

        metrics = {}
        if getattr(position, "state", None):
            metrics["final_state"] = getattr(position.state, "value", str(position.state))

        autopsy = self.autopsy_trade(
            trade_id=trade_id,
            ticker=position.ticker,
            outcome=outcome,
            entry_price=entry_p,
            exit_price=exit_p,
            stop_price=stop,
            metrics=metrics,
        )

        if entry_setup:
            # attach some brain info for context
            autopsy.metrics["setup_score"] = entry_setup.get("score")
            autopsy.metrics["setup_grade"] = entry_setup.get("grade")

        return autopsy