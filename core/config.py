"""Environment configuration for the trading office."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SUPPORTED_LLM_PROVIDERS = frozenset(
    {"grok", "openai", "deepseek", "anthropic", "ollama"}
)

PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "grok": {
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-4.3",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-6",
    },
    "ollama": {
        "base_url": "http://127.0.0.1:11434/v1",
        "default_model": "llama3.1",
    },
}

# Provider-specific env keys checked before generic LLM_API_KEY.
PROVIDER_API_KEY_ENV: dict[str, tuple[str, ...]] = {
    "grok": ("XAI_API_KEY", "GROK_API_KEY"),
    "openai": ("OPENAI_API_KEY",),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "ollama": (),
}

# Auto-detect provider when LLM_PROVIDER is not explicitly set.
AUTO_DETECT_ORDER: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("grok", ("XAI_API_KEY", "GROK_API_KEY")),
    ("openai", ("OPENAI_API_KEY",)),
    ("deepseek", ("DEEPSEEK_API_KEY",)),
    ("anthropic", ("ANTHROPIC_API_KEY",)),
)


def load_env_file() -> None:
    """Load key=value pairs from project ``.env`` if present."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def _env(name: str) -> str | None:
    load_env_file()
    value = os.environ.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


@lru_cache(maxsize=1)
def get_llm_provider() -> str | None:
    """Return the active LLM provider slug, or None when disabled."""
    explicit = (_env("LLM_PROVIDER") or "").lower()
    if explicit in {"", "none", "off", "disabled"}:
        if explicit in {"none", "off", "disabled"}:
            return None
        # Fall through to auto-detect when unset.
    elif explicit in SUPPORTED_LLM_PROVIDERS:
        return explicit

    for provider, keys in AUTO_DETECT_ORDER:
        if any(_env(key) for key in keys):
            return provider

    if _env("LLM_API_KEY") and explicit in SUPPORTED_LLM_PROVIDERS:
        return explicit

    return None


@lru_cache(maxsize=16)
def get_llm_api_key(provider: str | None = None) -> str | None:
    """Return API key for the given or active provider."""
    provider = provider or get_llm_provider()
    if not provider:
        return None

    for env_name in PROVIDER_API_KEY_ENV.get(provider, ()):
        value = _env(env_name)
        if value:
            return value

    return _env("LLM_API_KEY")


@lru_cache(maxsize=16)
def get_llm_model(provider: str | None = None) -> str:
    """Return model name for the given or active provider."""
    provider = provider or get_llm_provider() or "grok"
    override = _env("LLM_MODEL")
    if override:
        return override

    legacy_grok = _env("GROK_MODEL")
    if provider == "grok" and legacy_grok:
        return legacy_grok

    return PROVIDER_DEFAULTS.get(provider, {}).get("default_model", "grok-4.3")


@lru_cache(maxsize=16)
def get_llm_base_url(provider: str | None = None) -> str:
    """Return API base URL for the given or active provider."""
    provider = provider or get_llm_provider() or "grok"
    override = _env("LLM_BASE_URL")
    if override:
        return override.rstrip("/")
    return PROVIDER_DEFAULTS[provider]["base_url"].rstrip("/")


@lru_cache(maxsize=1)
def llm_enabled() -> bool:
    """Whether an LLM provider is configured for Portfolio Manager."""
    provider = get_llm_provider()
    if not provider:
        return False
    if provider == "ollama":
        return True
    return bool(get_llm_api_key(provider))


# Backward-compatible helpers from Phase 3.
@lru_cache(maxsize=1)
def get_xai_api_key() -> str | None:
    return get_llm_api_key("grok")


@lru_cache(maxsize=1)
def get_grok_model() -> str:
    return get_llm_model("grok")


@lru_cache(maxsize=1)
def grok_enabled() -> bool:
    return llm_enabled() and get_llm_provider() == "grok"