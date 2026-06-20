"""WebSocket connection manager for pixel-agents clients."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket

from server.pixel_bridge import PixelBridge


class ConnectionManager:
    """Broadcast pixel-agents protocol messages to all connected clients."""

    def __init__(self) -> None:
        self.active: list[WebSocket] = []
        self.bridge = PixelBridge()
        self._meeting_lock = asyncio.Lock()
        self._meeting_running = False

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        payload = json.dumps(message, ensure_ascii=False)
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_initial_state(self, websocket: WebSocket) -> None:
        """Send pixel-agents bootstrap messages after webviewReady."""
        for msg in [
            self.bridge.provider_capabilities(),
            self.bridge.settings_loaded(),
            self.bridge.layout_loaded(),
            self.bridge.existing_agents(),
        ]:
            await websocket.send_text(json.dumps(msg, ensure_ascii=False))
            # Set all agents to waiting initially
        for cfg in self.bridge.existing_agents()["agents"]:
            status = {"type": "agentStatus", "id": cfg, "status": "waiting"}
            await websocket.send_text(json.dumps(status))

    @property
    def meeting_running(self) -> bool:
        return self._meeting_running

    async def run_meeting(self) -> dict[str, Any]:
        """Run a live meeting if none is in progress."""
        if self._meeting_running:
            return {"error": "Meeting already in progress"}

        async with self._meeting_lock:
            self._meeting_running = True
            try:
                from server.meeting_runner import LiveMeetingRunner

                runner = LiveMeetingRunner(on_event=self.broadcast, step_delay=0.5)
                result = await runner.run()
                return {
                    "ok": True,
                    "summary": result.decision.summary,
                    "json_log": result.json_log_path,
                    "md_log": result.md_log_path,
                    "duration_ms": result.duration_ms,
                }
            finally:
                self._meeting_running = False