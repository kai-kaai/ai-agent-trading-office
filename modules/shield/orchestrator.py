"""The Shield — signal filtering after council approval.

A2 responsibilities:
- Enforce minimum Risk-Reward Ratio (RRR)
- Enforce minimum setup grade
- Detect excessive sector overlap / concentration
- Return GO / PASS (DEFER reserved for future)
"""

from __future__ import annotations

from modules.models import SetupGrade, ShieldDecision, ShieldVerdict, TradeSetup

MIN_RISK_REWARD = 2.0
MIN_GRADE_FOR_GO = SetupGrade.B
MAX_SECTOR_POSITIONS = 4  # max number of positions allowed in the same sector for buys


def _normalize_sector(sector: str | None) -> str | None:
    if not sector:
        return None
    s = sector.strip().lower()
    # Common normalizations
    if "information technology" in s or s == "tech":
        return "technology"
    if "semiconductor" in s:
        return "semiconductor"
    return s


class ShieldModule:
    """Shield enforces portfolio construction rules after The Brain approves."""

    def evaluate(
        self,
        setup: TradeSetup,
        risk_reward: float = 2.0,
        current_sectors: list[str] | None = None,
    ) -> ShieldDecision:
        reasons: list[str] = []
        overlap_warnings: list[str] = []
        current_sectors = current_sectors or []

        # 1. Grade gate
        if setup.grade.value == "C":
            reasons.append("Setup grade too low (C). Minimum B required.")
        elif setup.grade not in (SetupGrade.A_PLUS, SetupGrade.A, SetupGrade.B):
            reasons.append(f"Setup grade {setup.grade.value} not eligible.")

        # 2. RRR gate
        if risk_reward < MIN_RISK_REWARD:
            reasons.append(f"RRR {risk_reward:.1f} below minimum {MIN_RISK_REWARD:.1f}.")

        # 3. Sector overlap (primarily for buys)
        norm_sector = _normalize_sector(setup.sector)
        if setup.action.lower() == "buy" and norm_sector:
            # Count existing holdings in same normalized sector
            matching = sum(
                1 for s in current_sectors if _normalize_sector(s) == norm_sector
            )
            if matching >= MAX_SECTOR_POSITIONS:
                overlap_msg = (
                    f"Sector concentration: {matching} existing {norm_sector} positions "
                    f"(limit {MAX_SECTOR_POSITIONS})."
                )
                overlap_warnings.append(overlap_msg)
                reasons.append(overlap_msg)

        if reasons:
            return ShieldDecision(
                verdict=ShieldVerdict.PASS,
                risk_reward=risk_reward,
                overlap_warnings=overlap_warnings,
                reasons=reasons,
            )

        return ShieldDecision(
            verdict=ShieldVerdict.GO,
            risk_reward=risk_reward,
            overlap_warnings=overlap_warnings,
            reasons=[f"Shield passed: RRR={risk_reward:.1f}, grade={setup.grade.value}, sector OK."],
        )