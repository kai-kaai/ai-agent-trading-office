"""Track the latest meeting awaiting human approval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PendingMeeting:
    """Meeting snapshot exposed to the dashboard for semi-auto approval."""

    meeting_id: str
    json_file: str
    summary: str
    trade_count: int
    trades: list[dict[str, Any]]
    decision_source: str
    approved: bool = False


_pending: PendingMeeting | None = None


def set_pending(meeting: PendingMeeting) -> None:
    """Store the latest meeting awaiting approval."""
    global _pending
    _pending = meeting


def get_pending() -> PendingMeeting | None:
    """Return the current pending meeting, if any."""
    return _pending


def clear_pending() -> None:
    """Clear pending meeting state after approval."""
    global _pending
    _pending = None