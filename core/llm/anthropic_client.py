"""Anthropic Claude messages API client."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from core.llm.json_utils import parse_json_content
from core.llm.models import LLMDecision
from core.llm.prompts import PORTFOLIO_MANAGER_SYSTEM_PROMPT


class AnthropicClient:
    """Call Anthropic ``/v1/messages`` for Portfolio Manager deliberation."""

    def __init__(self, api_key: str | None, model: str) -> None:
        self.provider = "anthropic"
        self.api_key = api_key
        self.model = model

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def deliberate(self, user_prompt: str) -> LLMDecision | None:
        """Request a portfolio deliberation/decision from Claude."""
        if not self.api_key:
            return None

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": 0.3,
            "system": PORTFOLIO_MANAGER_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return None

        content_blocks = body.get("content", [])
        content = ""
        for block in content_blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                content += block.get("text", "")

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