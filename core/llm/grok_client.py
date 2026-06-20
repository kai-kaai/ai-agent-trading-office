"""Backward-compatible Grok client wrapper.

New code should use :func:`core.llm.client.get_llm_client` instead.
"""

from __future__ import annotations

from functools import lru_cache

from core.llm.client import get_llm_client
from core.llm.models import GrokDecision, LLMDecision


class GrokClient:
    """Thin adapter around the multi-provider LLM client."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._client = get_llm_client()
        self.api_key = api_key
        self.model = model

    @property
    def available(self) -> bool:
        return self._client is not None and self._client.available

    def deliberate(self, user_prompt: str) -> GrokDecision | None:
        if self._client is None:
            return None
        result = self._client.deliberate(user_prompt)
        return result  # GrokDecision is an alias for LLMDecision


@lru_cache(maxsize=1)
def get_grok_client() -> GrokClient:
    """Shared client instance (backward compatible)."""
    return GrokClient()