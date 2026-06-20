"""Backtester & Evaluator agent – performance measurement vs Tech Titans."""

from __future__ import annotations

from core.base_agent import BaseAgent
from core.models import (
    AgentReport,
    MeetingContext,
    Recommendation,
    StockScore,
)


class BacktesterEvaluator(BaseAgent):
    """Evaluates portfolio performance against the Tech Titans benchmark.

    Responsibilities (per AGENTS.md):
    - Run and interpret backtests
    - Measure performance vs Tech Titans benchmark
    - Assess whether recent decisions improved outcomes
    """

    def __init__(self) -> None:
        super().__init__(
            name="Backtester & Evaluator",
            role="backtester_evaluator",
            description=(
                "Measures portfolio performance against Tech Titans, "
                "tracks decision quality, and reports backtest metrics."
            ),
        )

    def analyze(self, context: MeetingContext) -> AgentReport:
        """Report performance metrics and benchmark comparison.

        Reads optional backtest data from ``context.extra``:
        - ``portfolio_return``: cumulative return of AI portfolio
        - ``benchmark_return``: cumulative return of Tech Titans
        - ``decisions_evaluated``: number of past decisions reviewed
        - ``decision_quality_score``: 0–100 quality rating
        """
        extra = context.extra

        portfolio_return = extra.get("portfolio_return")
        benchmark_return = extra.get("benchmark_return")
        decisions_evaluated = extra.get("decisions_evaluated", 0)
        quality_score = extra.get("decision_quality_score")

        key_points: list[str] = []
        warnings: list[str] = []
        stock_scores: list[StockScore] = []

        if portfolio_return is not None and benchmark_return is not None:
            alpha = portfolio_return - benchmark_return
            key_points.append(
                f"Portfolio return: {portfolio_return:.1%} vs "
                f"Tech Titans: {benchmark_return:.1%} (alpha: {alpha:+.1%})."
            )
            if alpha < 0:
                warnings.append(
                    f"Underperforming Tech Titans by {abs(alpha):.1%}."
                )
        else:
            key_points.append(
                "Backtest data not yet available — awaiting historical run."
            )

        if decisions_evaluated:
            key_points.append(
                f"Evaluated {decisions_evaluated} past decision(s) from Decision Log."
            )

        # Score alignment with Tech Titans benchmark holdings
        if context.benchmark_holdings:
            stock_scores = self._score_benchmark_alignment(context)
            overlap = sum(
                1 for p in context.portfolio
                if p.ticker.upper() in {b.upper() for b in context.benchmark_holdings}
            )
            key_points.append(
                f"Benchmark overlap: {overlap}/{len(context.portfolio)} "
                f"positions match Tech Titans holdings."
            )

        overall_score = self._compute_overall_score(
            portfolio_return, benchmark_return, quality_score
        )

        if overall_score < 40:
            warnings.append("Overall backtest score below threshold (40).")

        summary = (
            f"Backtest evaluation: overall score {overall_score:.0f}/100. "
            + (
                "Benchmark comparison available."
                if portfolio_return is not None
                else "Placeholder — run backtest to populate metrics."
            )
        )

        return self._build_report(
            summary,
            stock_scores=stock_scores,
            key_points=key_points,
            warnings=warnings,
            metadata={
                "portfolio_return": portfolio_return,
                "benchmark_return": benchmark_return,
                "decisions_evaluated": decisions_evaluated,
                "overall_score": overall_score,
                "data_source": "placeholder" if portfolio_return is None else "backtest",
            },
        )

    def _score_benchmark_alignment(self, context: MeetingContext) -> list[StockScore]:
        """Score how well each holding aligns with Tech Titans benchmark."""
        benchmark_set = {b.upper() for b in context.benchmark_holdings}
        scores: list[StockScore] = []

        for position in context.portfolio:
            in_benchmark = position.ticker.upper() in benchmark_set
            score = 75.0 if in_benchmark else 40.0
            scores.append(
                StockScore(
                    ticker=position.ticker,
                    score=score,
                    recommendation=(
                        Recommendation.HOLD if in_benchmark else Recommendation.SELL
                    ),
                    rationale=(
                        f"{position.ticker}: "
                        + (
                            "held in Tech Titans benchmark."
                            if in_benchmark
                            else "not in current Tech Titans benchmark."
                        )
                    ),
                    metrics={"in_benchmark": in_benchmark},
                )
            )

        return scores

    @staticmethod
    def _compute_overall_score(
        portfolio_return: float | None,
        benchmark_return: float | None,
        quality_score: float | None,
    ) -> float:
        """Derive a composite evaluation score from available metrics."""
        if portfolio_return is None or benchmark_return is None:
            return quality_score if quality_score is not None else 50.0

        alpha = portfolio_return - benchmark_return
        alpha_component = min(100.0, max(0.0, 50.0 + alpha * 200))
        quality_component = quality_score if quality_score is not None else 50.0
        return (alpha_component + quality_component) / 2

    @staticmethod
    def _average_score(scores: list[StockScore]) -> float:
        if not scores:
            return 0.0
        return sum(s.score for s in scores) / len(scores)