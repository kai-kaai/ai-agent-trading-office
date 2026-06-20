"""Live market prices and technical indicators via yfinance."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any

try:
    import yfinance as yf
except ImportError:  # pragma: no cover - optional dependency
    yf = None  # type: ignore[assignment]

CACHE_TTL_SECONDS = 3600


@dataclass
class TechnicalSnapshot:
    """Technical indicators for one ticker."""

    ticker: str
    price: float | None
    sma_50: float | None
    sma_200: float | None
    rsi_14: float | None
    return_1m: float | None
    return_3m: float | None
    pct_from_52w_high: float | None
    trend: str
    score: float
    data_source: str


def _compute_rsi(closes: list[float], period: int = 14) -> float | None:
    """Wilder RSI from a close-price series."""
    if len(closes) < period + 1:
        return None

    gains: list[float] = []
    losses: list[float] = []
    for idx in range(1, len(closes)):
        delta = closes[idx] - closes[idx - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for idx in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def technical_score(
    price: float | None,
    sma_50: float | None,
    sma_200: float | None,
    rsi_14: float | None,
    return_1m: float | None,
    pct_from_52w_high: float | None,
) -> tuple[float, str]:
    """Derive a 0–100 technical score and trend label."""
    score = 50.0
    trend = "sideways"

    if price and sma_50 and sma_200:
        if price > sma_50 > sma_200:
            score += 18
            trend = "uptrend"
        elif price < sma_50 < sma_200:
            score -= 18
            trend = "downtrend"
        elif price > sma_50:
            score += 8
            trend = "recovering"
        elif price < sma_50:
            score -= 8
            trend = "weakening"

    if rsi_14 is not None:
        if 45 <= rsi_14 <= 60:
            score += 5
        elif rsi_14 < 30:
            score += 8
        elif rsi_14 > 70:
            score -= 10

    if return_1m is not None:
        if return_1m > 0.05:
            score += 8
        elif return_1m > 0.01:
            score += 4
        elif return_1m < -0.05:
            score -= 10
        elif return_1m < -0.01:
            score -= 5

    if pct_from_52w_high is not None:
        if pct_from_52w_high > 0.95:
            score -= 5
        elif pct_from_52w_high < 0.70:
            score += 4

    return max(0.0, min(100.0, score)), trend


class MarketDataService:
    """Fetch and cache yfinance price history."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, TechnicalSnapshot]] = {}

    def get_technicals(self, ticker: str) -> TechnicalSnapshot:
        """Return technical indicators for a ticker."""
        key = ticker.upper()
        cached = self._cache.get(key)
        if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

        snapshot = self._fetch_technicals(key)
        self._cache[key] = (time.time(), snapshot)
        return snapshot

    def get_price(self, ticker: str) -> float | None:
        """Return the latest available close price."""
        return self.get_technicals(ticker).price

    def get_market_condition(self, tickers: list[str]) -> str:
        """Summarize overall market tone from a ticker basket."""
        if not tickers:
            return "neutral"

        scores: list[float] = []
        for ticker in tickers[:8]:
            tech = self.get_technicals(ticker)
            if tech.price is not None:
                scores.append(tech.score)

        if not scores:
            return "neutral"

        avg = sum(scores) / len(scores)
        if avg >= 62:
            return "bullish"
        if avg <= 42:
            return "bearish"
        return "neutral"

    def _fetch_technicals(self, ticker: str) -> TechnicalSnapshot:
        """Pull history from yfinance and compute indicators."""
        if yf is None:
            return TechnicalSnapshot(
                ticker=ticker,
                price=None,
                sma_50=None,
                sma_200=None,
                rsi_14=None,
                return_1m=None,
                return_3m=None,
                pct_from_52w_high=None,
                trend="unknown",
                score=50.0,
                data_source="unavailable",
            )

        try:
            history = yf.Ticker(ticker).history(period="1y", auto_adjust=True)
        except Exception:
            history = None

        if history is None or history.empty:
            return TechnicalSnapshot(
                ticker=ticker,
                price=None,
                sma_50=None,
                sma_200=None,
                rsi_14=None,
                return_1m=None,
                return_3m=None,
                pct_from_52w_high=None,
                trend="unknown",
                score=50.0,
                data_source="yfinance_empty",
            )

        closes = [float(value) for value in history["Close"].tolist()]
        price = closes[-1]
        sma_50 = sum(closes[-50:]) / min(50, len(closes)) if closes else None
        sma_200 = sum(closes[-200:]) / min(200, len(closes)) if closes else None
        rsi_14 = _compute_rsi(closes)

        return_1m = None
        return_3m = None
        if len(closes) > 22:
            return_1m = price / closes[-22] - 1.0
        if len(closes) > 66:
            return_3m = price / closes[-66] - 1.0

        high_52w = max(closes[-252:]) if len(closes) >= 252 else max(closes)
        pct_from_52w_high = price / high_52w if high_52w else None

        score, trend = technical_score(
            price, sma_50, sma_200, rsi_14, return_1m, pct_from_52w_high
        )

        return TechnicalSnapshot(
            ticker=ticker,
            price=price,
            sma_50=sma_50,
            sma_200=sma_200,
            rsi_14=rsi_14,
            return_1m=return_1m,
            return_3m=return_3m,
            pct_from_52w_high=pct_from_52w_high,
            trend=trend,
            score=score,
            data_source="yfinance",
        )


@lru_cache(maxsize=1)
def get_market_data_service() -> MarketDataService:
    """Return a shared market data service."""
    return MarketDataService()