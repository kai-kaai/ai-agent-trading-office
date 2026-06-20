"""Risk Manager agent – portfolio risk controls and position sizing."""

from __future__ import annotations

from collections import defaultdict

from core.base_agent import BaseAgent
from core.models import (
    AgentReport,
    MeetingContext,
    Recommendation,
    StockScore,
)

# Risk thresholds aligned with TRADING-RULES.md (tech-only, weekly rebalance).
MAX_SECTOR_CONCENTRATION = 0.40  # 40% max in one sub-sector bucket
MAX_SINGLE_POSITION = 0.15  # 15% max per ticker
MAX_DRAWDOWN_WARNING = 0.10  # warn when portfolio drawdown exceeds 10%
TARGET_CASH_BUFFER = 0.05  # keep ~5% cash for flexibility between monthly injections


class RiskManager(BaseAgent):
    """Monitors portfolio risk and recommends position sizing constraints.

    Responsibilities (per AGENTS.md):
    - Control overall portfolio risk
    - Recommend position sizing
    - Check sector concentration and drawdown limits
    """

    def __init__(self) -> None:
        super().__init__(
            name="Risk Manager",
            role="risk_manager",
            description=(
                "Enforces concentration limits, monitors drawdown, and "
                "recommends position sizes consistent with trading rules."
            ),
        )

    def analyze(self, context: MeetingContext) -> AgentReport:
        """Assess portfolio risk profile against defined guardrails."""
        total_value = context.total_portfolio_value
        warnings: list[str] = []
        key_points: list[str] = []
        stock_scores: list[StockScore] = []

        if total_value <= 0:
            return self._build_report(
                "Portfolio value is zero; risk assessment deferred.",
                warnings=["Cannot assess risk on an empty portfolio."],
            )

        # Position concentration
        for position in context.portfolio:
            weight = position.market_value / total_value
            risk_score = self._position_risk_score(weight)
            stock_scores.append(
                StockScore(
                    ticker=position.ticker,
                    score=risk_score,
                    recommendation=self._risk_to_recommendation(risk_score),
                    rationale=(
                        f"Position weight {weight:.1%} of portfolio "
                        f"(limit {MAX_SINGLE_POSITION:.0%})."
                    ),
                    metrics={"weight": round(weight, 4), "sector": position.sector},
                )
            )
            if weight > MAX_SINGLE_POSITION:
                warnings.append(
                    f"{position.ticker} exceeds single-position limit "
                    f"({weight:.1%} > {MAX_SINGLE_POSITION:.0%})."
                )

        # Sector concentration (grouped by sector field on positions)
        sector_weights = self._sector_weights(context, total_value)
        for sector, weight in sector_weights.items():
            key_points.append(f"Sector '{sector}': {weight:.1%} of portfolio.")
            if weight > MAX_SECTOR_CONCENTRATION:
                warnings.append(
                    f"Sector '{sector}' concentration {weight:.1%} exceeds "
                    f"{MAX_SECTOR_CONCENTRATION:.0%} limit."
                )

        # Cash buffer check (important between monthly 305 USD injections)
        cash_ratio = context.cash_balance / total_value
        key_points.append(f"Cash buffer: {cash_ratio:.1%} of portfolio.")
        if not context.is_first_trading_day_of_month and cash_ratio < TARGET_CASH_BUFFER:
            warnings.append(
                f"Low cash buffer ({cash_ratio:.1%}) mid-month. "
                "Rebalance should use only existing cash and sale proceeds."
            )

        drawdown = context.extra.get("current_drawdown", 0.0)
        if isinstance(drawdown, (int, float)) and drawdown > 0:
            key_points.append(f"Backtest drawdown from peak: {drawdown:.1%}.")
        if isinstance(drawdown, (int, float)) and drawdown > MAX_DRAWDOWN_WARNING:
            warnings.append(
                f"Portfolio drawdown {drawdown:.1%} exceeds "
                f"{MAX_DRAWDOWN_WARNING:.0%} warning threshold."
            )

        backtest_nav = context.extra.get("backtest_final_nav")
        if isinstance(backtest_nav, (int, float)):
            key_points.append(f"Backtest final NAV reference: {backtest_nav:,.2f} USD.")

        risk_level = "elevated" if warnings else "within limits"
        summary = (
            f"Risk review: portfolio at {total_value:,.2f} USD, "
            f"{len(context.portfolio)} positions, risk level {risk_level}."
        )

        data_source = "live_portfolio"
        if context.extra.get("backtest_holdings"):
            data_source = "backtest_engine"

        return self._build_report(
            summary,
            stock_scores=stock_scores,
            key_points=key_points,
            warnings=warnings,
            metadata={
                "cash_ratio": round(cash_ratio, 4),
                "sector_weights": {k: round(v, 4) for k, v in sector_weights.items()},
                "portfolio_weights": context.extra.get("portfolio_weights", {}),
                "current_drawdown": drawdown,
                "data_source": data_source,
                "limits": {
                    "max_single_position": MAX_SINGLE_POSITION,
                    "max_sector_concentration": MAX_SECTOR_CONCENTRATION,
                },
            },
        )

    @staticmethod
    def _sector_weights(
        context: MeetingContext, total_value: float
    ) -> dict[str, float]:
        """Compute weight per sector bucket."""
        sector_values: dict[str, float] = defaultdict(float)
        for position in context.portfolio:
            sector_values[position.sector] += position.market_value
        return {sector: value / total_value for sector, value in sector_values.items()}

    @staticmethod
    def _position_risk_score(weight: float) -> float:
        """Higher score = lower risk. Penalize overweight positions."""
        if weight <= MAX_SINGLE_POSITION * 0.5:
            return 90.0
        if weight <= MAX_SINGLE_POSITION:
            return 70.0
        if weight <= MAX_SINGLE_POSITION * 1.5:
            return 45.0
        return 20.0

    @staticmethod
    def _risk_to_recommendation(risk_score: float) -> Recommendation:
        """Translate risk score into a sizing recommendation."""
        if risk_score >= 80:
            return Recommendation.HOLD
        if risk_score >= 60:
            return Recommendation.HOLD
        if risk_score >= 40:
            return Recommendation.SELL
        return Recommendation.STRONG_SELL

    def suggest_position_size(
        self, ticker: str, context: MeetingContext, conviction: float = 1.0
    ) -> float:
        """Suggest maximum dollar allocation for a new or increased position.

        Args:
            ticker: Stock symbol.
            context: Current meeting context.
            conviction: Multiplier 0–1 reflecting analyst confidence.

        Returns:
            Suggested maximum allocation in USD.
        """
        total_value = context.total_portfolio_value
        base_allocation = total_value * MAX_SINGLE_POSITION
        available_cash = context.cash_balance

        if not context.is_first_trading_day_of_month:
            # Mid-month: only cash on hand (per TRADING-RULES.md)
            base_allocation = min(base_allocation, available_cash)

        return round(base_allocation * max(0.0, min(conviction, 1.0)), 2)