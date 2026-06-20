"""OpenAI-compatible chat completions client (Grok, OpenAI, DeepSeek, Ollama)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from core.llm.json_utils import parse_json_content
from core.llm.models import LLMDecision
from core.llm.prompts import PORTFOLIO_MANAGER_SYSTEM_PROMPT


class OpenAICompatibleClient:
    """Call any OpenAI-style ``/v1/chat/completions`` endpoint."""

    def __init__(
        self,
        provider: str,
        api_key: str | None,
        model: str,
        base_url: str,
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    @property
    def available(self) -> bool:
        if self.provider == "ollama":
            return True
        return bool(self.api_key)

    def deliberate(self, user_prompt: str) -> LLMDecision | None:
        """Request a portfolio deliberation/decision."""
        if not self.available:
            return None

        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": PORTFOLIO_MANAGER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }

        # Most providers accept json_object; Ollama may ignore it gracefully.
        if self.provider != "ollama":
            payload["response_format"] = {"type": "json_object"}

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None

        content = (
            body.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if not content:
            return None

        parsed = parse_json_content(content)
        if parsed is None:
            return None

        return LLMDecision(
            deliberation=str(parsed.get("deliberation", "")).strip(),
            summary=str(parsed.get("summary", "")).strip(),
            reasoning=[str(item) for item in parsed.get("reasoning", [])],
            trades=list(parsed.get("trades", [])),
            model=str(body.get("model", self.model)),
            provider=self.provider,
        )