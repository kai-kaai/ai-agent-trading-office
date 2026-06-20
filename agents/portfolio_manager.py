"""Portfolio Manager agent – chairs meetings and makes final decisions."""

from __future__ import annotations

from core.base_agent import BaseAgent
from core.config import get_llm_model, get_llm_provider
from core.llm.client import get_llm_client
from core.models import (
    AgentReport,
    MeetingContext,
    PortfolioDecision,
    Recommendation,
    TradeAction,
)


class PortfolioManager(BaseAgent):
    """CEO of the trading office; synthesizes reports into portfolio actions.

    Responsibilities (per AGENTS.md):
    - Convene weekly agent meetings
    - Synthesize analyst and risk inputs
    - Issue final portfolio adjustment orders
    - Own the decision rationale recorded in the Decision Log
    """

    def __init__(self) -> None:
        super().__init__(
            name="Portfolio Manager",
            role="portfolio_manager",
            description=(
                "Leads weekly meetings, weighs all agent reports, and "
                "issues final buy/sell/hold instructions for the tech portfolio."
            ),
        )
        self._llm = get_llm_client()

    def analyze(self, context: MeetingContext) -> AgentReport:
        """Provide a high-level portfolio status report before deliberation."""
        total_value = context.total_portfolio_value
        position_count = len(context.portfolio)

        key_points = [
            f"Portfolio NAV: {total_value:,.2f} USD across {position_count} holdings.",
            f"Cash available: {context.cash_balance:,.2f} USD.",
        ]

        if context.is_first_trading_day_of_month:
            key_points.append(
                f"Monthly capital injection of {context.monthly_capital_injection:.0f} "
                "USD available today."
            )
        else:
            key_points.append(
                "Mid-month rebalance: limited to existing cash and sale proceeds."
            )

        if self._llm and self._llm.available:
            provider = get_llm_provider() or "llm"
            model = get_llm_model(provider)
            key_points.append(
                f"LLM connected ({provider}/{model}) — assisted deliberation enabled."
            )
        else:
            key_points.append(
                "No LLM configured — using rule-based fallback for decisions."
            )

        summary = (
            f"Portfolio overview as of {context.meeting_date.isoformat()}: "
            f"{position_count} tech positions, {total_value:,.2f} USD total."
        )

        return self._build_report(summary, key_points=key_points)

    def decide(
        self,
        context: MeetingContext,
        reports: list[AgentReport],
    ) -> PortfolioDecision:
        """Synthesize agent reports into a final portfolio decision.

        Uses configured LLM provider when available; falls back to rule-based logic.
        """
        llm_result = self._decide_with_llm(context, reports)
        if llm_result is not None:
            return llm_result

        trades = self._derive_trades(context, reports)
        reasoning = self._build_reasoning(reports, trades)
        summary = self._build_decision_summary(context, trades)
        deliberation = self._build_deliberation_fallback(reports)

        return PortfolioDecision(
            meeting_date=context.meeting_date,
            trades=trades,
            summary=summary,
            reasoning=reasoning,
            agent_reports=reports,
            deliberation=deliberation,
            decision_source="rule_based",
        )

    def _decide_with_llm(
        self,
        context: MeetingContext,
        reports: list[AgentReport],
    ) -> PortfolioDecision | None:
        """Ask the configured LLM to deliberate and return a structured decision."""
        if self._llm is None or not self._llm.available:
            return None

        prompt = self._build_llm_prompt(context, reports)
        llm_result = self._llm.deliberate(prompt)
        if llm_result is None or not llm_result.summary:
            return None

        trades = self._parse_llm_trades(llm_result.trades, context)
        reasoning = llm_result.reasoning or self._build_reasoning(reports, trades)
        deliberation = llm_result.deliberation or self._build_deliberation_fallback(
            reports
        )

        return PortfolioDecision(
            meeting_date=context.meeting_date,
            trades=trades,
            summary=llm_result.summary,
            reasoning=reasoning,
            agent_reports=reports,
            deliberation=deliberation,
            decision_source=f"{llm_result.provider}:{llm_result.model}",
        )

    def _build_llm_prompt(
        self,
        context: MeetingContext,
        reports: list[AgentReport],
    ) -> str:
        """Compact meeting context for the LLM prompt."""
        holdings = ", ".join(
            f"{p.ticker} ({p.shares:.2f} sh, ${p.market_value:,.0f})"
            for p in context.portfolio[:15]
        ) or "none"
        watchlist = ", ".join(context.watchlist[:10]) or "none"

        lines = [
            f"Meeting date: {context.meeting_date.isoformat()}",
            f"Portfolio NAV: ${context.total_portfolio_value:,.2f}",
            f"Cash: ${context.cash_balance:,.2f}",
            f"First trading day of month: {context.is_first_trading_day_of_month}",
            f"Holdings: {holdings}",
            f"Watchlist: {watchlist}",
            "",
            "Backtest context:",
            f"- Portfolio return: {context.extra.get('portfolio_return', 'n/a')}",
            f"- Benchmark return: {context.extra.get('benchmark_return', 'n/a')}",
            f"- Alpha: {context.extra.get('alpha', 'n/a')}",
            f"- Drawdown: {context.extra.get('current_drawdown', 'n/a')}",
            "",
            "Agent reports:",
        ]

        for report in reports:
            if report.agent_name == self.name:
                continue
            lines.append(f"## {report.agent_name} ({report.role})")
            lines.append(report.summary)
            for point in report.key_points[:4]:
                lines.append(f"- {point}")
            for warning in report.warnings[:3]:
                lines.append(f"- WARNING: {warning}")
            top_scores = sorted(report.stock_scores, key=lambda s: s.score, reverse=True)[:5]
            if top_scores:
                lines.append(
                    "Top scores: "
                    + ", ".join(f"{s.ticker} ({s.score:.0f})" for s in top_scores)
                )
            bottom_scores = sorted(report.stock_scores, key=lambda s: s.score)[:3]
            if bottom_scores:
                lines.append(
                    "Weak scores: "
                    + ", ".join(f"{s.ticker} ({s.score:.0f})" for s in bottom_scores)
                )
            lines.append("")

        lines.append(
            "Propose trades for human approval. Return JSON only."
        )
        return "\n".join(lines)

    def _parse_llm_trades(
        self,
        raw_trades: list[dict],
        context: MeetingContext,
    ) -> list[TradeAction]:
        """Convert LLM trade dicts into TradeAction objects."""
        held = {p.ticker.upper(): p for p in context.portfolio}
        trades: list[TradeAction] = []

        for item in raw_trades:
            if not isinstance(item, dict):
                continue
            ticker = str(item.get("ticker", "")).upper().strip()
            action = str(item.get("action", "")).lower().strip()
            if not ticker or action not in {"buy", "sell"}:
                continue

            shares = float(item.get("shares", 0) or 0)
            rationale = str(item.get("rationale", "LLM proposal")).strip()

            if action == "sell" and ticker in held and shares <= 0:
                shares = held[ticker].shares

            trades.append(
                TradeAction(
                    ticker=ticker,
                    action=action,
                    shares=shares,
                    rationale=rationale,
                )
            )

        return trades

    def _derive_trades(
        self,
        context: MeetingContext,
        reports: list[AgentReport],
    ) -> list[TradeAction]:
        """Convert aggregated agent scores into concrete trade proposals."""
        scores_by_ticker: dict[str, list[float]] = {}
        rationales_by_ticker: dict[str, list[str]] = {}

        for report in reports:
            for stock in report.stock_scores:
                scores_by_ticker.setdefault(stock.ticker, []).append(stock.score)
                rationales_by_ticker.setdefault(stock.ticker, []).append(
                    f"[{report.agent_name}] {stock.rationale}"
                )

        held_tickers = {p.ticker.upper() for p in context.portfolio}
        trades: list[TradeAction] = []

        for ticker, scores in scores_by_ticker.items():
            avg_score = sum(scores) / len(scores)
            combined_rationale = " | ".join(rationales_by_ticker[ticker][:2])

            if ticker in held_tickers and avg_score < 40:
                position = next(
                    p for p in context.portfolio if p.ticker.upper() == ticker
                )
                trades.append(
                    TradeAction(
                        ticker=ticker,
                        action="sell",
                        shares=position.shares,
                        rationale=(
                            f"Low composite score ({avg_score:.0f}). {combined_rationale}"
                        ),
                    )
                )
            elif ticker not in held_tickers and avg_score >= 75:
                trades.append(
                    TradeAction(
                        ticker=ticker,
                        action="buy",
                        shares=0.0,
                        rationale=(
                            f"High composite score ({avg_score:.0f}). {combined_rationale}"
                        ),
                    )
                )

        return trades

    def _build_reasoning(
        self,
        reports: list[AgentReport],
        trades: list[TradeAction],
    ) -> list[str]:
        """Compile human-readable reasoning from agent inputs."""
        reasoning: list[str] = []

        for report in reports:
            reasoning.append(f"{report.agent_name}: {report.summary}")
            for point in report.key_points[:2]:
                reasoning.append(f"  • {point}")
            for warning in report.warnings:
                reasoning.append(f"  ⚠ {warning}")

        if not trades:
            reasoning.append("No trades proposed; maintain current allocation.")
        else:
            reasoning.append(
                f"Proposed {len(trades)} trade(s): "
                + ", ".join(f"{t.action.upper()} {t.ticker}" for t in trades)
            )

        return reasoning

    @staticmethod
    def _build_deliberation_fallback(reports: list[AgentReport]) -> str:
        """Rule-based deliberation when no LLM is available."""
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

    @staticmethod
    def _build_decision_summary(
        context: MeetingContext,
        trades: list[TradeAction],
    ) -> str:
        """One-line summary of the final decision."""
        if not trades:
            return (
                f"Weekly meeting {context.meeting_date}: HOLD – no portfolio changes."
            )
        buy_count = sum(1 for t in trades if t.action == "buy")
        sell_count = sum(1 for t in trades if t.action == "sell")
        return (
            f"Weekly meeting {context.meeting_date}: "
            f"{buy_count} buy(s), {sell_count} sell(s) proposed."
        )

    @staticmethod
    def aggregate_recommendation(scores: list[float]) -> Recommendation:
        """Map averaged scores to a portfolio-level recommendation."""
        if not scores:
            return Recommendation.HOLD
        avg = sum(scores) / len(scores)
        if avg >= 75:
            return Recommendation.BUY
        if avg >= 55:
            return Recommendation.HOLD
        return Recommendation.SELL