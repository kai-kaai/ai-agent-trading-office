"""LLM-powered AI Council deliberation."""

from __future__ import annotations

from core.llm.complete import complete_json
from core.llm.prompts import COUNCIL_SYSTEM_PROMPT
from modules.brain.scanners import ScannerReport
from modules.models import CouncilMember, CouncilVote, VoteDecision


_MEMBER_MAP = {
    "bear": CouncilMember.BEAR,
    "bull": CouncilMember.BULL,
    "risk_chair": CouncilMember.RISK_CHAIR,
}


def build_council_prompt(report: ScannerReport) -> str:
    lines = [
        f"Evaluate this {report.action.upper()} setup for {report.ticker}.",
        f"Composite score: {report.composite_score:.1f} ({report.grade.value})",
        f"Fundamental: {report.fundamental_score:.1f}",
        f"Sector strength: {report.sector_strength:.1f}",
        f"Structure: {report.structure_score:.1f}",
        f"News: {report.news_score:.1f}",
        f"Trend: {report.trend}",
    ]
    if report.sector:
        lines.append(f"Sector: {report.sector}")
    if report.top_headline:
        lines.append(f"Top headline: {report.top_headline}")
    for note in report.structure_notes[:6]:
        lines.append(f"- {note}")
    lines.append("Each council member must vote approve or reject with rationale.")
    return "\n".join(lines)


def parse_council_votes(payload: dict) -> list[CouncilVote] | None:
    raw_votes = payload.get("votes")
    if not isinstance(raw_votes, list) or len(raw_votes) != 3:
        return None

    votes: list[CouncilVote] = []
    for item in raw_votes:
        if not isinstance(item, dict):
            return None
        member_key = str(item.get("member", "")).lower().strip()
        member = _MEMBER_MAP.get(member_key)
        if member is None:
            return None
        decision_raw = str(item.get("decision", "")).lower().strip()
        decision = VoteDecision.APPROVE if decision_raw == "approve" else VoteDecision.REJECT
        votes.append(
            CouncilVote(
                member=member,
                decision=decision,
                rationale=str(item.get("rationale", "")).strip() or "No rationale provided.",
                veto=bool(item.get("veto", False)),
            )
        )

    if {vote.member for vote in votes} != set(CouncilMember):
        return None
    return votes


def deliberate_with_llm(report: ScannerReport) -> list[CouncilVote] | None:
    """Ask the configured LLM to produce three council votes."""
    payload = complete_json(build_council_prompt(report), COUNCIL_SYSTEM_PROMPT)
    if payload is None:
        return None
    return parse_council_votes(payload)