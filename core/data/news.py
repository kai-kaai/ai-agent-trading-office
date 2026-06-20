"""News sentiment from yfinance headlines and price momentum."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from core.data.fundamentals import get_fundamental_service
from core.data.market_data import get_market_data_service

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None  # type: ignore[assignment]

POSITIVE_WORDS = {
    "beat", "beats", "growth", "surge", "rally", "upgrade", "upgraded",
    "record", "strong", "profit", "profits", "gain", "gains", "boost",
    "outperform", "bullish", "partnership", "launch", "wins", "win",
}
NEGATIVE_WORDS = {
    "miss", "misses", "fall", "falls", "drop", "drops", "downgrade",
    "downgraded", "weak", "loss", "losses", "lawsuit", "cut", "cuts",
    "warning", "bearish", "decline", "declines", "layoff", "layoffs",
    "investigation", "recall",
}


@dataclass
class NewsSnapshot:
    """News sentiment summary for one ticker."""

    ticker: str
    score: float
    sentiment: str
    headline_count: int
    top_headline: str | None
    events: list[dict[str, str]]
    data_source: str


def _headline_sentiment(title: str) -> float:
    """Score a single headline from keyword hits (-1 to +1)."""
    words = {word.strip(".,!?\"'").lower() for word in title.split()}
    positive = len(words & POSITIVE_WORDS)
    negative = len(words & NEGATIVE_WORDS)
    if positive == negative == 0:
        return 0.0
    return (positive - negative) / max(positive + negative, 1)


class NewsSentimentService:
    """Score tickers using yfinance news with CSV/momentum fallback."""

    def analyze(self, ticker: str, on_date: Any = None) -> NewsSnapshot:
        """Return sentiment snapshot for a ticker."""
        events: list[dict[str, str]] = []
        headline_scores: list[float] = []
        top_headline: str | None = None
        data_source = "yfinance_news"

        if yf is not None:
            try:
                raw_news = yf.Ticker(ticker).news or []
            except Exception:
                raw_news = []

            for item in raw_news[:8]:
                title = (
                    item.get("title")
                    or item.get("content", {}).get("title")
                    or ""
                ).strip()
                if not title:
                    continue
                if top_headline is None:
                    top_headline = title
                headline_scores.append(_headline_sentiment(title))
                events.append(
                    {
                        "title": title,
                        "publisher": str(item.get("publisher", "unknown")),
                    }
                )

        score = 52.0
        if headline_scores:
            avg = sum(headline_scores) / len(headline_scores)
            score = 50.0 + avg * 35.0
        else:
            data_source = "momentum_fallback"
            fundamentals = get_fundamental_service()
            snap = fundamentals.snapshot(ticker, on_date) if on_date else None
            market = get_market_data_service().get_technicals(ticker)

            if market.return_1m is not None:
                if market.return_1m > 0.03:
                    score += 12
                elif market.return_1m > 0:
                    score += 5
                elif market.return_1m < -0.03:
                    score -= 12
                elif market.return_1m < 0:
                    score -= 5

            if snap and snap.price_52w_high_pct is not None:
                if snap.price_52w_high_pct > 0.90:
                    score += 4
                elif snap.price_52w_high_pct < 0.55:
                    score -= 4

            if top_headline is None and market.trend == "uptrend":
                top_headline = f"{ticker}: positive price momentum (no headlines fetched)"
            elif top_headline is None and market.trend == "downtrend":
                top_headline = f"{ticker}: negative price momentum (no headlines fetched)"

        score = max(0.0, min(100.0, score))
        sentiment = "neutral"
        if score >= 65:
            sentiment = "positive"
        elif score < 45:
            sentiment = "negative"

        return NewsSnapshot(
            ticker=ticker,
            score=score,
            sentiment=sentiment,
            headline_count=len(events),
            top_headline=top_headline,
            events=events,
            data_source=data_source,
        )


@lru_cache(maxsize=1)
def get_news_service() -> NewsSentimentService:
    """Return a shared news sentiment service."""
    return NewsSentimentService()