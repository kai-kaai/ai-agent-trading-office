"""Market Researcher agent – technical analysis and market timing."""

from __future__ import annotations

from core.base_agent import BaseAgent
from core.data.market_data import get_market_data_service
from core.data.tickers import collect_tickers
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

    INDICATORS = ("rsi_14", "sma_50", "sma_200", "return_1m", "pct_from_52w_high")

    def __init__(self) -> None:
        super().__init__(
            name="Market Researcher",
            role="market_researcher",
            description=(
                "Evaluates technical indicators, sector trends, and market "
                "conditions to assess optimal entry and exit timing."
            ),
        )
        self._market = get_market_data_service()

    def analyze(self, context: MeetingContext) -> AgentReport:
        """Assess technical setup using yfinance price history."""
        tickers = collect_tickers(context)
        stock_scores = [self._score_technicals(ticker) for ticker in tickers]

        bullish = [s for s in stock_scores if s.score >= 65]
        bearish = [s for s in stock_scores if s.score < 45]
        live = [s for s in stock_scores if s.metrics.get("data_source") == "yfinance"]

        market_condition = self._market.get_market_condition(tickers)
        sector_rotation = context.extra.get("sector_rotation", "technology")

        key_points = [
            f"Technical review for {len(tickers)} tickers ({len(live)} live via yfinance).",
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
                "data_source": "yfinance",
            },
        )

    def _score_technicals(self, ticker: str) -> StockScore:
        """Score one ticker from live technical indicators."""
        tech = self._market.get_technicals(ticker)

        rationale = (
            f"{ticker}: trend={tech.trend}, RSI {tech.rsi_14 or 'n/a'}, "
            f"1M return {(tech.return_1m or 0) * 100:+.1f}% "
            f"→ score {tech.score:.0f}/100."
        )

        return StockScore(
            ticker=ticker,
            score=tech.score,
            recommendation=self._technical_to_recommendation(tech.score),
            rationale=rationale,
            metrics={
                "trend": tech.trend,
                "rsi_14": tech.rsi_14,
                "sma_50": tech.sma_50,
                "sma_200": tech.sma_200,
                "return_1m": tech.return_1m,
                "return_3m": tech.return_3m,
                "pct_from_52w_high": tech.pct_from_52w_high,
                "price": tech.price,
                "data_source": tech.data_source,
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