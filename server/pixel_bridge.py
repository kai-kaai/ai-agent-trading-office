"""Pixel Agents protocol bridge for the Trading Office.

Emits WebSocket messages compatible with the Pixel Agents protocol
(https://github.com/pixel-agents-hq/pixel-agents) so the React dashboard
(or any pixel-agents SPA client) can render agent activity without VS Code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Trading-office agents mapped to pixel-agents IDs and desk seats.
AGENT_DESK_CONFIG: list[dict[str, Any]] = [
    {
        "id": 1,
        "role": "portfolio_manager",
        "name": "Portfolio Manager",
        "short": "PM",
        "seatId": "desk-ceo",
        "palette": 0,
        "hueShift": 0,
        "folderName": "CEO / Decision",
    },
    {
        "id": 2,
        "role": "financial_analyst",
        "name": "Financial Analyst",
        "short": "FA",
        "seatId": "desk-fa",
        "palette": 1,
        "hueShift": 0,
        "folderName": "Fundamentals",
    },
    {
        "id": 3,
        "role": "news_researcher",
        "name": "News Researcher",
        "short": "NR",
        "seatId": "desk-nr",
        "palette": 2,
        "hueShift": 0,
        "folderName": "News & Sentiment",
    },
    {
        "id": 4,
        "role": "market_researcher",
        "name": "Market Researcher",
        "short": "MR",
        "seatId": "desk-mr",
        "palette": 3,
        "hueShift": 0,
        "folderName": "Technical Analysis",
    },
    {
        "id": 5,
        "role": "risk_manager",
        "name": "Risk Manager",
        "short": "RM",
        "seatId": "desk-rm",
        "palette": 4,
        "hueShift": 0,
        "folderName": "Risk Control",
    },
    {
        "id": 6,
        "role": "backtester_evaluator",
        "name": "Backtester & Evaluator",
        "short": "BT",
        "seatId": "desk-bt",
        "palette": 5,
        "hueShift": 0,
        "folderName": "Backtest & Eval",
    },
]

AGENT_BY_ROLE: dict[str, dict[str, Any]] = {
    cfg["role"]: cfg for cfg in AGENT_DESK_CONFIG
}
AGENT_BY_NAME: dict[str, dict[str, Any]] = {
    cfg["name"]: cfg for cfg in AGENT_DESK_CONFIG
}


@dataclass
class OfficeLayout:
    """Minimal office layout for the pixel office renderer."""

    cols: int = 8
    rows: int = 5
    tileColors: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "cols": self.cols,
            "rows": self.rows,
            "tileColors": self.tileColors or {"floor": "#2d4a3e", "wall": "#1a2e26"},
            "furniture": [
                {"id": cfg["seatId"], "type": "desk", "agentRole": cfg["role"]}
                for cfg in AGENT_DESK_CONFIG
            ],
        }


class PixelBridge:
    """Builds pixel-agents-compatible WebSocket messages."""

    def provider_capabilities(self) -> dict[str, Any]:
        return {
            "type": "providerCapabilities",
            "readingTools": ["analyze", "research", "evaluate"],
            "subagentToolNames": [],
        }

    def settings_loaded(self) -> dict[str, Any]:
        return {
            "type": "settingsLoaded",
            "soundEnabled": False,
            "lastSeenVersion": "1.0.0",
            "extensionVersion": "trading-office-1.0.0",
            "watchAllSessions": True,
            "alwaysShowLabels": True,
            "hooksEnabled": False,
            "hooksInfoShown": True,
            "externalAssetDirectories": [],
        }

    def layout_loaded(self) -> dict[str, Any]:
        return {
            "type": "layoutLoaded",
            "layout": OfficeLayout().to_dict(),
            "wasReset": False,
        }

    def existing_agents(self) -> dict[str, Any]:
        agents = [cfg["id"] for cfg in AGENT_DESK_CONFIG]
        agent_meta = {
            str(cfg["id"]): {
                "palette": cfg["palette"],
                "hueShift": cfg["hueShift"],
                "seatId": cfg["seatId"],
            }
            for cfg in AGENT_DESK_CONFIG
        }
        folder_names = {
            str(cfg["id"]): cfg["folderName"] for cfg in AGENT_DESK_CONFIG
        }
        return {
            "type": "existingAgents",
            "agents": agents,
            "agentMeta": agent_meta,
            "folderNames": folder_names,
            "externalAgents": {str(cfg["id"]): False for cfg in AGENT_DESK_CONFIG},
        }

    def agent_status(self, agent_id: int, status: str = "active") -> dict[str, Any]:
        return {"type": "agentStatus", "id": agent_id, "status": status}

    def agent_tool_start(
        self, agent_id: int, tool_id: str, status: str, tool_name: str = "analyze"
    ) -> dict[str, Any]:
        return {
            "type": "agentToolStart",
            "id": agent_id,
            "toolId": tool_id,
            "status": status,
            "toolName": tool_name,
            "permissionActive": False,
            "runInBackground": False,
        }

    def agent_tool_done(self, agent_id: int, tool_id: str) -> dict[str, Any]:
        return {"type": "agentToolDone", "id": agent_id, "toolId": tool_id}

    def agent_tools_clear(self, agent_id: int) -> dict[str, Any]:
        return {"type": "agentToolsClear", "id": agent_id}

    def trading_meeting_event(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Extension message for the Trading Office dashboard (not in pixel-agents core)."""
        return {"type": "tradingMeetingEvent", "event": event, "payload": payload}

    @staticmethod
    def resolve_agent_id(name: str | None = None, role: str | None = None) -> int:
        if role and role in AGENT_BY_ROLE:
            return AGENT_BY_ROLE[role]["id"]
        if name and name in AGENT_BY_NAME:
            return AGENT_BY_NAME[name]["id"]
        return 1