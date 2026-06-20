"""Portfolio Manager agent – chairs meetings and makes final decisions."""

from __future__ import annotations

from core.base_agent import BaseAgent
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

        Phase 1 uses rule-based synthesis. LLM-assisted deliberation will be
        added when the Grok API integration is wired up.

        Args:
            context: Current meeting context.
            reports: Reports collected from all participating agents.

        Returns:
            Final portfolio decision with proposed trades and reasoning.
        """
        trades = self._derive_trades(context, reports)
        reasoning = self._build_reasoning(reports, trades)

        summary = self._build_decision_summary(context, trades)

        return PortfolioDecision(
            meeting_date=context.meeting_date,
            trades=trades,
            summary=summary,
            reasoning=reasoning,
            agent_reports=reports,
        )

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
                        shares=0.0,  # sized by execution layer / risk manager
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