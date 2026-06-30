"""Generic JSON completion across configured LLM providers."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from core.config import get_llm_api_key, get_llm_base_url, get_llm_model, get_llm_provider
from core.llm.client import get_llm_client
from core.llm.json_utils import parse_json_content


def complete_json(user_prompt: str, system_prompt: str) -> dict[str, Any] | None:
    """Return parsed JSON from an LLM call, or None when unavailable."""
    client = get_llm_client()
    if client is None or not client.available:
        return None

    provider = get_llm_provider() or client.provider
    if provider == "anthropic":
        return _anthropic_json(system_prompt, user_prompt)
    return _openai_compatible_json(provider, system_prompt, user_prompt)


def _openai_compatible_json(provider: str, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    api_key = get_llm_api_key(provider)
    model = get_llm_model(provider)
    base_url = get_llm_base_url(provider).rstrip("/")

    if provider != "ollama" and not api_key:
        return None

    payload: dict[str, Any] = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if provider != "ollama":
        payload["response_format"] = {"type": "json_object"}

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    return parse_json_content(content) if content else None


def _anthropic_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    api_key = get_llm_api_key("anthropic")
    if not api_key:
        return None

    payload = {
        "model": get_llm_model("anthropic"),
        "max_tokens": 2048,
        "temperature": 0.2,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    blocks = body.get("content", [])
    text = "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
    return parse_json_content(text) if text else None