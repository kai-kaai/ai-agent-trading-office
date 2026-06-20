"""Financial Analyst agent – fundamental analysis and stock scoring."""

from __future__ import annotations

from core.base_agent import BaseAgent
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

    DEFAULT_METRICS = ("eps", "revenue_growth", "debt_ratio", "profit_margin")

    def __init__(self) -> None:
        super().__init__(
            name="Financial Analyst",
            role="financial_analyst",
            description=(
                "Evaluates company fundamentals and assigns quality scores "
                "based on EPS, revenue growth, debt ratio, and profit margin."
            ),
        )

    def analyze(self, context: MeetingContext) -> AgentReport:
        """Score portfolio holdings and watchlist tickers.

        Phase 1 uses placeholder logic. Real financial data will be wired in
        during the backtest integration step.
        """
        tickers = self._collect_tickers(context)
        stock_scores = [self._score_ticker(ticker, context) for ticker in tickers]

        strong = [s for s in stock_scores if s.score >= 70]
        weak = [s for s in stock_scores if s.score < 50]

        key_points = [
            f"Reviewed {len(tickers)} tickers across portfolio and watchlist.",
            f"{len(strong)} names rated fundamentally strong (score ≥ 70).",
            f"{len(weak)} names flagged as weak (score < 50).",
        ]

        warnings = []
        if weak:
            warnings.append(
                "Weak fundamentals detected: "
                + ", ".join(s.ticker for s in weak[:5])
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
            metadata={"metrics_reviewed": list(self.DEFAULT_METRICS)},
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

    def _score_ticker(self, ticker: str, context: MeetingContext) -> StockScore:
        """Produce a placeholder fundamental score for one ticker.

        Replace with real data feeds (e.g. yfinance, SEC filings) in Phase 2.
        """
        in_portfolio = any(p.ticker.upper() == ticker for p in context.portfolio)
        base_score = 62.0 if in_portfolio else 55.0

        metrics = {
            "eps": None,
            "revenue_growth": None,
            "debt_ratio": None,
            "profit_margin": None,
            "data_source": "placeholder",
        }

        recommendation = self._score_to_recommendation(base_score)
        rationale = (
            f"{ticker}: placeholder fundamental score pending live data. "
            f"{'Currently held in portfolio.' if in_portfolio else 'On watchlist.'}"
        )

        return StockScore(
            ticker=ticker,
            score=base_score,
            recommendation=recommendation,
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