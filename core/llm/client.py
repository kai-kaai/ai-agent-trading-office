"""Multi-provider LLM client factory."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from core.config import (
    SUPPORTED_LLM_PROVIDERS,
    get_llm_api_key,
    get_llm_base_url,
    get_llm_model,
    get_llm_provider,
    llm_enabled,
)
from core.llm.anthropic_client import AnthropicClient
from core.llm.models import LLMDecision
from core.llm.openai_compatible import OpenAICompatibleClient


class LLMClient(Protocol):
    """Protocol implemented by all provider clients."""

    provider: str
    model: str

    @property
    def available(self) -> bool: ...

    def deliberate(self, user_prompt: str) -> LLMDecision | None: ...


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient | None:
    """Return the configured LLM client, or None when LLM is disabled."""
    provider = get_llm_provider()
    if not provider or not llm_enabled():
        return None

    model = get_llm_model(provider)
    api_key = get_llm_api_key(provider)

    if provider == "anthropic":
        return AnthropicClient(api_key=api_key, model=model)

    return OpenAICompatibleClient(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=get_llm_base_url(provider),
    )


def get_llm_status() -> dict[str, str | bool]:
    """Return LLM configuration summary for API/dashboard."""
    provider = get_llm_provider() or "none"
    enabled = llm_enabled()
    return {
        "llm_enabled": enabled,
        "llm_provider": provider,
        "llm_model": get_llm_model(provider) if provider in SUPPORTED_LLM_PROVIDERS else "",
        "llm_base_url": get_llm_base_url(provider) if provider in SUPPORTED_LLM_PROVIDERS else "",
        # Backward-compatible aliases from Phase 3
        "grok_enabled": enabled and provider == "grok",
        "grok_model": get_llm_model("grok") if provider == "grok" else "",
    }