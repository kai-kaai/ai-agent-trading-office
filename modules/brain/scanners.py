"""The Brain scanners — sector strength, structure, news, fundamentals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from core.data.fundamentals import get_fundamental_service
from core.data.market_data import TechnicalSnapshot, get_market_data_service
from core.data.news import get_news_service
from modules.brain.grading import score_to_grade
from modules.models import SetupGrade

TECH_SECTOR_PROXY = "QQQ"
SCAN_WEIGHTS = {
    "fundamental": 0.25,
    "sector": 0.20,
    "structure": 0.30,
    "news": 0.25,
}


@dataclass
class ScannerReport:
    ticker: str
    action: str
    fundamental_score: float
    sector_strength: float
    structure_score: float
    news_score: float
    composite_score: float
    grade: SetupGrade
    sector: str | None = None
    trend: str = "unknown"
    structure_notes: list[str] = field(default_factory=list)
    news_sentiment: float | None = None
    top_headline: str | None = None
    scanned_at: date | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "action": self.action,
            "fundamental_score": round(self.fundamental_score, 2),
            "sector_strength": round(self.sector_strength, 2),
            "structure_score": round(self.structure_score, 2),
            "news_score": round(self.news_score, 2),
            "composite_score": round(self.composite_score, 2),
            "grade": self.grade.value,
            "sector": self.sector,
            "trend": self.trend,
            "structure_notes": self.structure_notes,
            "news_sentiment": self.news_sentiment,
            "top_headline": self.top_headline,
            "scanned_at": self.scanned_at.isoformat() if self.scanned_at else None,
            "metadata": self.metadata,
        }


def _sector_strength_score(ticker: str, technical: TechnicalSnapshot, market: Any) -> tuple[float, str]:
    """Relative strength vs tech sector proxy (QQQ)."""
    proxy = market.get_technicals(TECH_SECTOR_PROXY)
    ticker_return = technical.return_1m
    proxy_return = proxy.return_1m

    if ticker_return is None or proxy_return is None:
        return 50.0, "insufficient_return_data"

    relative = ticker_return - proxy_return
    score = 50.0 + relative * 200.0
    if relative > 0.03:
        label = "outperforming_tech"
    elif relative < -0.03:
        label = "underperforming_tech"
    else:
        label = "inline_with_tech"
    return max(0.0, min(100.0, score)), label


def _structure_scan(technical: TechnicalSnapshot) -> tuple[float, list[str]]:
    """Price structure notes (US-stock interpretation of SMC-style context)."""
    notes: list[str] = []
    score = technical.score

    if technical.trend != "unknown":
        notes.append(f"Trend: {technical.trend}")

    if technical.price and technical.sma_50:
        relation = "above" if technical.price >= technical.sma_50 else "below"
        notes.append(f"Price {relation} SMA50")

    if technical.sma_50 and technical.sma_200:
        if technical.sma_50 > technical.sma_200:
            notes.append("SMA50 above SMA200 (bullish structure)")
        elif technical.sma_50 < technical.sma_200:
            notes.append("SMA50 below SMA200 (bearish structure)")

    if technical.rsi_14 is not None:
        if technical.rsi_14 > 70:
            notes.append(f"RSI {technical.rsi_14:.0f} — overbought zone")
            score -= 5
        elif technical.rsi_14 < 30:
            notes.append(f"RSI {technical.rsi_14:.0f} — oversold zone")
            score += 3

    if technical.pct_from_52w_high is not None:
        pct = technical.pct_from_52w_high * 100
        notes.append(f"{pct:.0f}% of 52-week high")
        if technical.pct_from_52w_high > 0.95:
            notes.append("Near 52w high — breakout or exhaustion risk")
        elif technical.pct_from_52w_high < 0.75:
            notes.append("Well below 52w high — potential value or weakness")

    if technical.return_1m is not None:
        notes.append(f"1-month return {technical.return_1m * 100:+.1f}%")

    return max(0.0, min(100.0, score)), notes


def scan_ticker(
    ticker: str,
    action: str = "buy",
    on_date: date | None = None,
) -> ScannerReport:
    """Run all Brain scanners and produce a composite A+ setup score."""
    ticker = ticker.upper()
    on_date = on_date or date.today()

    fundamentals = get_fundamental_service()
    market = get_market_data_service()
    news_svc = get_news_service()

    fund_score, snap = fundamentals.score(ticker, on_date)
    sector = snap.sector if snap else None
    technical = market.get_technicals(ticker)
    sector_score, sector_label = _sector_strength_score(ticker, technical, market)
    structure_score, structure_notes = _structure_scan(technical)
    news = news_svc.analyze(ticker, on_date)

    composite = (
        fund_score * SCAN_WEIGHTS["fundamental"]
        + sector_score * SCAN_WEIGHTS["sector"]
        + structure_score * SCAN_WEIGHTS["structure"]
        + news.score * SCAN_WEIGHTS["news"]
    )
    grade = score_to_grade(composite)

    return ScannerReport(
        ticker=ticker,
        action=action,
        fundamental_score=fund_score,
        sector_strength=sector_score,
        structure_score=structure_score,
        news_score=news.score,
        composite_score=composite,
        grade=grade,
        sector=sector,
        trend=technical.trend,
        structure_notes=structure_notes,
        news_sentiment=news.score / 100.0,
        top_headline=news.top_headline,
        scanned_at=on_date,
        metadata={
            "sector_label": sector_label,
            "technical_source": technical.data_source,
            "news_source": news.data_source,
            "news_headline_count": news.headline_count,
            "weights": SCAN_WEIGHTS,
        },
    )