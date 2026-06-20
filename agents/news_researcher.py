"""News Researcher agent – news sentiment and event monitoring."""

from __future__ import annotations

from core.base_agent import BaseAgent
from core.models import (
    AgentReport,
    MeetingContext,
    Recommendation,
    StockScore,
)


class NewsResearcher(BaseAgent):
    """Monitors news flow and assesses sentiment impact on holdings.

    Responsibilities (per AGENTS.md):
    - Search for latest company news and developments
    - Analyze sentiment from news sources
    - Flag material events that may move prices
    """

    SENTIMENT_LABELS = ("positive", "neutral", "negative")

    def __init__(self) -> None:
        super().__init__(
            name="News Researcher",
            role="news_researcher",
            description=(
                "Tracks tech-sector news, scores sentiment per ticker, "
                "and highlights events that could affect portfolio positions."
            ),
        )

    def analyze(self, context: MeetingContext) -> AgentReport:
        """Assess news sentiment for portfolio and watchlist tickers.

        Phase 1 uses placeholder sentiment. Real news feeds will be wired in
        when the Grok API and data sources are integrated.
        """
        tickers = self._collect_tickers(context)
        stock_scores = [self._score_sentiment(ticker, context) for ticker in tickers]

        positive = [s for s in stock_scores if s.score >= 65]
        negative = [s for s in stock_scores if s.score < 45]
        events = context.extra.get("news_events", [])

        key_points = [
            f"Scanned news sentiment for {len(tickers)} tickers.",
            f"{len(positive)} names with positive sentiment, "
            f"{len(negative)} with negative sentiment.",
        ]

        if isinstance(events, list) and events:
            key_points.append(f"{len(events)} material event(s) flagged this week.")

        warnings = []
        if negative:
            warnings.append(
                "Negative news sentiment: "
                + ", ".join(s.ticker for s in negative[:5])
            )

        summary = (
            f"News review complete. Average sentiment score: "
            f"{self._average_score(stock_scores):.1f}/100."
        )

        return self._build_report(
            summary,
            stock_scores=stock_scores,
            key_points=key_points,
            warnings=warnings,
            metadata={"data_source": "placeholder", "events_reviewed": len(events)},
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

    def _score_sentiment(self, ticker: str, context: MeetingContext) -> StockScore:
        """Produce a placeholder news-sentiment score for one ticker."""
        in_portfolio = any(p.ticker.upper() == ticker for p in context.portfolio)
        base_score = 58.0 if in_portfolio else 52.0

        sentiment = "neutral"
        if base_score >= 60:
            sentiment = "positive"
        elif base_score < 50:
            sentiment = "negative"

        return StockScore(
            ticker=ticker,
            score=base_score,
            recommendation=self._sentiment_to_recommendation(base_score),
            rationale=(
                f"{ticker}: placeholder news sentiment ({sentiment}). "
                "Live news feed pending integration."
            ),
            metrics={"sentiment": sentiment, "data_source": "placeholder"},
        )

    @staticmethod
    def _sentiment_to_recommendation(score: float) -> Recommendation:
        if score >= 70:
            return Recommendation.BUY
        if score >= 50:
            return Recommendation.HOLD
        if score >= 35:
            return Recommendation.SELL
        return Recommendation.STRONG_SELL

    @staticmethod
    def _average_score(scores: list[StockScore]) -> float:
        if not scores:
            return 0.0
        return sum(s.score for s in scores) / len(scores)