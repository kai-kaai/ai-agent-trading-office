"""Financial Analyst agent – fundamental analysis and stock scoring."""

from __future__ import annotations

from core.base_agent import BaseAgent
from core.data.fundamentals import get_fundamental_service
from core.data.tickers import collect_tickers
from core.models import (
    AgentReport,
    MeetingContext,
    Recommendation,
    StockScore,
)


class FinancialAnalyst(BaseAgent):
    """Analyzes financial statements and assigns fundamental scores.

    Responsibilities (per AGENTS.md):
    - Review key metrics: EPS, revenue growth, debt ratio, profit margin
    - Score each stock on a 0–100 scale
    - Highlight fundamentally strong or weak names in the watchlist/portfolio
    """

    DEFAULT_METRICS = (
        "pe_ratio",
        "fcf_yield",
        "operating_margin",
        "return_on_common",
        "revenue_b",
        "market_cap_b",
    )

    def __init__(self) -> None:
        super().__init__(
            name="Financial Analyst",
            role="financial_analyst",
            description=(
                "Evaluates company fundamentals and assigns quality scores "
                "based on EPS, revenue growth, debt ratio, and profit margin."
            ),
        )
        self._fundamentals = get_fundamental_service()

    def analyze(self, context: MeetingContext) -> AgentReport:
        """Score portfolio holdings and watchlist tickers from CSV fundamentals."""
        tickers = collect_tickers(context)
        stock_scores = [
            self._score_ticker(ticker, context.meeting_date) for ticker in tickers
        ]

        strong = [s for s in stock_scores if s.score >= 70]
        weak = [s for s in stock_scores if s.score < 50]
        with_data = [s for s in stock_scores if s.metrics.get("data_source") == "tech_titans_csv"]

        key_points = [
            f"Reviewed {len(tickers)} tickers across portfolio and watchlist.",
            f"{len(with_data)} names scored from Tech Titans CSV fundamentals.",
            f"{len(strong)} names rated fundamentally strong (score ≥ 70).",
            f"{len(weak)} names flagged as weak (score < 50).",
        ]

        warnings = []
        if weak:
            warnings.append(
                "Weak fundamentals detected: "
                + ", ".join(s.ticker for s in weak[:5])
            )

        missing = [s.ticker for s in stock_scores if s.metrics.get("data_source") != "tech_titans_csv"]
        if missing:
            warnings.append(
                "No CSV fundamentals for: " + ", ".join(missing[:5])
            )

        summary = (
            f"Fundamental review complete for {len(tickers)} tech stocks. "
            f"Average score: {self._average_score(stock_scores):.1f}/100."
        )

        return self._build_report(
            summary,
            stock_scores=stock_scores,
            key_points=key_points,
            warnings=warnings,
            metadata={
                "metrics_reviewed": list(self.DEFAULT_METRICS),
                "data_source": "tech_titans_csv",
            },
        )

    def _score_ticker(self, ticker: str, on_date: object) -> StockScore:
        """Score one ticker using Tech Titans CSV metrics."""
        score, snap = self._fundamentals.score(ticker, on_date)  # type: ignore[arg-type]

        if snap is None:
            return StockScore(
                ticker=ticker,
                score=score,
                recommendation=self._score_to_recommendation(score),
                rationale=f"{ticker}: no Tech Titans CSV snapshot for this month.",
                metrics={"data_source": "missing"},
            )

        metrics = self._fundamentals.metrics_dict(snap)
        rationale = (
            f"{ticker}: PE {snap.pe_ratio or 'n/a'}x, "
            f"FCF yield {(snap.fcf_yield or 0) * 100:.1f}%, "
            f"margin {(snap.operating_margin or 0) * 100:.1f}% "
            f"→ score {score:.0f}/100."
        )

        return StockScore(
            ticker=ticker,
            score=score,
            recommendation=self._score_to_recommendation(score),
            rationale=rationale,
            metrics=metrics,
        )

    @staticmethod
    def _score_to_recommendation(score: float) -> Recommendation:
        """Map a numeric score to a discrete recommendation."""
        if score >= 80:
            return Recommendation.STRONG_BUY
        if score >= 65:
            return Recommendation.BUY
        if score >= 45:
            return Recommendation.HOLD
        if score >= 30:
            return Recommendation.SELL
        return Recommendation.STRONG_SELL

    @staticmethod
    def _average_score(scores: list[StockScore]) -> float:
        """Return mean score, or 0 when the list is empty."""
        if not scores:
            return 0.0
        return sum(s.score for s in scores) / len(scores)