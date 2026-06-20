"""JSON parsing helpers for LLM responses."""

from __future__ import annotations

import json
import re
from typing import Any


def parse_json_content(content: str) -> dict[str, Any] | None:
    """Parse JSON from model output, tolerating fenced code blocks."""
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None