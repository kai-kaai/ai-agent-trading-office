"""The Brain — AI Council vote logic and setup evaluation."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from core.config import get_llm_model, get_llm_provider
from core.llm.client import get_llm_client
from modules.brain.grading import score_to_grade
from modules.brain.llm_council import deliberate_with_llm
from modules.brain.scanners import ScannerReport, scan_ticker
from modules.models import (
    CouncilMember,
    CouncilVerdict,
    CouncilVote,
    SetupGrade,
    TradeSetup,
    VoteDecision,
)

COUNCIL_APPROVAL_THRESHOLD = 2


def evaluate_council(votes: list[CouncilVote]) -> CouncilVerdict:
    """Apply council rules: 2/3 approve AND no Risk Chair veto."""
    if len(votes) != 3:
        raise ValueError("Council requires exactly 3 votes.")

    members = {vote.member for vote in votes}
    if members != set(CouncilMember):
        raise ValueError("Council votes must include bear, bull, and risk_chair.")

    approval_count = sum(1 for vote in votes if vote.decision == VoteDecision.APPROVE)
    risk_vote = next(vote for vote in votes if vote.member == CouncilMember.RISK_CHAIR)
    vetoed = risk_vote.veto or risk_vote.decision == VoteDecision.REJECT
    passed = approval_count >= COUNCIL_APPROVAL_THRESHOLD and not vetoed

    if vetoed:
        summary = "Rejected — Risk Chair veto."
    elif passed:
        summary = f"Approved — {approval_count}/3 council votes."
    else:
        summary = f"Rejected — only {approval_count}/3 council votes."

    return CouncilVerdict(
        votes=votes,
        approval_count=approval_count,
        passed=passed,
        vetoed=vetoed,
        summary=summary,
    )


def rule_based_council_votes(report: ScannerReport) -> list[CouncilVote]:
    """Deterministic council when LLM is unavailable."""
    composite = report.composite_score
    grade = report.grade
    rsi_note = any("RSI" in note and "overbought" in note for note in report.structure_notes)

    bear_approve = composite >= 55 and not rsi_note
    bull_approve = composite >= 50 and report.trend in {"uptrend", "recovering", "sideways"}
    risk_approve = composite >= 62 and grade in {SetupGrade.A_PLUS, SetupGrade.A, SetupGrade.B}
    risk_veto = grade is SetupGrade.C or composite < 40

    return [
        CouncilVote(
            member=CouncilMember.BEAR,
            decision=VoteDecision.APPROVE if bear_approve else VoteDecision.REJECT,
            rationale=(
                f"Bear: composite {composite:.0f}, trend {report.trend}"
                + (" — overbought risk flagged." if rsi_note else ".")
            ),
        ),
        CouncilVote(
            member=CouncilMember.BULL,
            decision=VoteDecision.APPROVE if bull_approve else VoteDecision.REJECT,
            rationale=f"Bull: upside case from grade {grade.value} and sector strength {report.sector_strength:.0f}.",
        ),
        CouncilVote(
            member=CouncilMember.RISK_CHAIR,
            decision=VoteDecision.APPROVE if risk_approve and not risk_veto else VoteDecision.REJECT,
            rationale=f"Risk Chair: fundamental {report.fundamental_score:.0f}, structure {report.structure_score:.0f}.",
            veto=risk_veto,
        ),
    ]


class BrainModule:
    """Strategy Lab — scanners + AI Council."""

    def scan(self, ticker: str, action: str = "buy", on_date: date | None = None) -> ScannerReport:
        return scan_ticker(ticker, action=action, on_date=on_date)

    def evaluate(
        self,
        ticker: str,
        action: str = "buy",
        *,
        on_date: date | None = None,
        score_override: float | None = None,
    ) -> TradeSetup:
        """Scan ticker, run council (LLM or rule-based), return trade setup."""
        report = self.scan(ticker, action=action, on_date=on_date)

        if score_override is not None:
            report = replace(
                report,
                composite_score=score_override,
                grade=score_to_grade(score_override),
            )

        llm_votes = deliberate_with_llm(report)
        votes = llm_votes if llm_votes is not None else rule_based_council_votes(report)
        council = evaluate_council(votes)

        llm = get_llm_client()
        decision_source = "rule_based"
        if llm_votes is not None and llm is not None:
            provider = get_llm_provider() or llm.provider
            decision_source = f"council_llm:{provider}:{get_llm_model(provider)}"

        return TradeSetup(
            ticker=report.ticker,
            action=report.action,
            grade=report.grade,
            score=report.composite_score,
            council=council,
            sector=report.sector,
            sector_strength=report.sector_strength,
            structure_notes=report.structure_notes,
            news_sentiment=report.news_sentiment,
            metadata={
                "module": "brain",
                "phase": 1,
                "decision_source": decision_source,
                "scanner": report.to_dict(),
                "sector": report.sector,
                "trend": report.trend,
                "top_headline": report.top_headline,
            },
        )