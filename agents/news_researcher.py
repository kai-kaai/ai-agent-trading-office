"""News Researcher agent – news sentiment and event monitoring."""

from __future__ import annotations

from core.base_agent import BaseAgent
from core.data.news import get_news_service
from core.data.tickers import collect_tickers
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
        self._news = get_news_service()

    def analyze(self, context: MeetingContext) -> AgentReport:
        """Assess news sentiment from yfinance headlines and momentum fallback."""
        tickers = collect_tickers(context)
        stock_scores = [
            self._score_sentiment(ticker, context) for ticker in tickers
        ]

        positive = [s for s in stock_scores if s.score >= 65]
        negative = [s for s in stock_scores if s.score < 45]
        all_events: list[dict[str, str]] = []
        for score in stock_scores:
            events = score.metrics.get("events", [])
            if isinstance(events, list):
                all_events.extend(events)

        key_points = [
            f"Scanned news sentiment for {len(tickers)} tickers.",
            f"{len(positive)} names with positive sentiment, "
            f"{len(negative)} with negative sentiment.",
        ]

        if all_events:
            key_points.append(f"{len(all_events)} headline(s) reviewed this week.")

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
            metadata={
                "data_source": "yfinance_news",
                "events_reviewed": len(all_events),
                "news_events": all_events[:10],
            },
        )

    def _score_sentiment(self, ticker: str, context: MeetingContext) -> StockScore:
        """Score one ticker from yfinance news or price-momentum fallback."""
        snap = self._news.analyze(ticker, context.meeting_date)

        headline = snap.top_headline or "No recent headlines"
        rationale = (
            f"{ticker}: {snap.sentiment} sentiment ({snap.headline_count} headlines). "
            f"Top: {headline[:80]}"
        )

        return StockScore(
            ticker=ticker,
            score=snap.score,
            recommendation=self._sentiment_to_recommendation(snap.score),
            rationale=rationale,
            metrics={
                "sentiment": snap.sentiment,
                "headline_count": snap.headline_count,
                "top_headline": snap.top_headline,
                "events": snap.events,
                "data_source": snap.data_source,
            },
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