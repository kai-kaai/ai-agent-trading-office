"""Market Researcher agent – technical analysis and market timing."""

from __future__ import annotations

from core.base_agent import BaseAgent
from core.models import (
    AgentReport,
    MeetingContext,
    Recommendation,
    StockScore,
)


class MarketResearcher(BaseAgent):
    """Analyzes price action, trends, and market conditions.

    Responsibilities (per AGENTS.md):
    - Analyze price and technical indicators
    - Assess trend, sector rotation, and overall market condition
    - Evaluate entry/exit timing
    """

    INDICATORS = ("rsi", "macd", "sma_50", "sma_200", "volume_trend")

    def __init__(self) -> None:
        super().__init__(
            name="Market Researcher",
            role="market_researcher",
            description=(
                "Evaluates technical indicators, sector trends, and market "
                "conditions to assess optimal entry and exit timing."
            ),
        )

    def analyze(self, context: MeetingContext) -> AgentReport:
        """Assess technical setup for portfolio and watchlist tickers.

        Phase 1 uses placeholder indicators. Real price data will be wired in
        during the backtest integration step.
        """
        tickers = self._collect_tickers(context)
        stock_scores = [self._score_technicals(ticker, context) for ticker in tickers]

        bullish = [s for s in stock_scores if s.score >= 65]
        bearish = [s for s in stock_scores if s.score < 45]

        market_condition = context.extra.get("market_condition", "neutral")
        sector_rotation = context.extra.get("sector_rotation", "technology")

        key_points = [
            f"Technical review for {len(tickers)} tickers.",
            f"{len(bullish)} names with bullish setup, {len(bearish)} bearish.",
            f"Overall market condition: {market_condition}.",
            f"Sector rotation signal: {sector_rotation}.",
        ]

        warnings = []
        if bearish:
            warnings.append(
                "Bearish technicals: " + ", ".join(s.ticker for s in bearish[:5])
            )

        summary = (
            f"Market/technical review complete. "
            f"Average technical score: {self._average_score(stock_scores):.1f}/100."
        )

        return self._build_report(
            summary,
            stock_scores=stock_scores,
            key_points=key_points,
            warnings=warnings,
            metadata={
                "indicators_reviewed": list(self.INDICATORS),
                "market_condition": market_condition,
                "data_source": "placeholder",
            },
        )

    def _collect_tickers(self, context: MeetingContext) -> list[str]:
        """Merge portfolio tickers and watchlist, preserving order."""
        seen: set[str] = set()
        ordered: list[str] = []
        for ticker in [p.ticker for p in context.portfolio] + context.watchlist:
            upper = ticker.upper()
            if upper not in seen:
                seen.add(upper)
                ordered.append(upper)
        return ordered

    def _score_technicals(self, ticker: str, context: MeetingContext) -> StockScore:
        """Produce a placeholder technical score for one ticker."""
        in_portfolio = any(p.ticker.upper() == ticker for p in context.portfolio)
        base_score = 60.0 if in_portfolio else 54.0
        trend = "uptrend" if base_score >= 58 else "sideways"

        return StockScore(
            ticker=ticker,
            score=base_score,
            recommendation=self._technical_to_recommendation(base_score),
            rationale=(
                f"{ticker}: placeholder technical score, trend={trend}. "
                "Live price data pending integration."
            ),
            metrics={
                "trend": trend,
                "rsi": None,
                "macd": None,
                "data_source": "placeholder",
            },
        )

    @staticmethod
    def _technical_to_recommendation(score: float) -> Recommendation:
        if score >= 75:
            return Recommendation.STRONG_BUY
        if score >= 60:
            return Recommendation.BUY
        if score >= 45:
            return Recommendation.HOLD
        if score >= 30:
            return Recommendation.SELL
        return Recommendation.STRONG_SELL

    @staticmethod
    def _average_score(scores: list[StockScore]) -> float:
        if not scores:
            return 0.0
        return sum(s.score for s in scores) / len(scores)