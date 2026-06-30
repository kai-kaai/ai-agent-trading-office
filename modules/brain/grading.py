"""Setup grade helpers for The Brain."""

from __future__ import annotations

from modules.models import SetupGrade


def score_to_grade(score: float) -> SetupGrade:
    if score >= 85:
        return SetupGrade.A_PLUS
    if score >= 70:
        return SetupGrade.A
    if score >= 55:
        return SetupGrade.B
    return SetupGrade.C