"""LLM decision models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMDecision:
    """Structured portfolio decision returned by any LLM provider."""

    deliberation: str
    summary: str
    reasoning: list[str] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    provider: str = ""


# Backward-compatible alias used during the Grok-only phase.
GrokDecision = LLMDecision