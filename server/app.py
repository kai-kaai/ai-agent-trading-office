"""FastAPI server – REST API + Pixel Agents WebSocket for Trading Office."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Ensure project root is on sys.path when running as `python server/app.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.registry import AGENT_REGISTRY, list_roles  # noqa: E402
from core.decision_log import DecisionLog  # noqa: E402
from server.pixel_bridge import AGENT_DESK_CONFIG  # noqa: E402
from server.ws_manager import ConnectionManager  # noqa: E402

app = FastAPI(
    title="AI Agent Trading Office",
    description="REST API and Pixel Agents WebSocket bridge",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()
decision_log = DecisionLog()


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "trading-office"}


@app.get("/api/agents")
async def get_agents() -> list[dict]:
    """List all registered agents with desk assignments."""
    agents = []
    for cfg in AGENT_DESK_CONFIG:
        role = cfg["role"]
        cls = AGENT_REGISTRY[role]
        instance = cls()
        agents.append(
            {
                "id": cfg["id"],
                "role": role,
                "name": instance.name,
                "short": cfg["short"],
                "description": instance.description,
                "seatId": cfg["seatId"],
                "palette": cfg["palette"],
                "folderName": cfg["folderName"],
            }
        )
    return agents


@app.get("/api/meetings")
async def list_meetings() -> list[dict]:
    """Return meeting index (newest first)."""
    return decision_log.get_all()


@app.get("/api/meetings/file/{filename}")
async def get_meeting_file(filename: str) -> JSONResponse:
    data = decision_log.load_meeting(filename)
    return JSONResponse(data)


@app.post("/api/meetings/run")
async def run_meeting() -> dict:
    """Trigger a live weekly meeting with WebSocket broadcasts."""
    return await manager.run_meeting()


@app.get("/api/status")
async def office_status() -> dict:
    return {
        "connected_clients": len(manager.active),
        "meeting_running": manager.meeting_running,
        "agent_roles": list_roles(),
    }


# Serve built React dashboard in production
DASHBOARD_DIST = PROJECT_ROOT / "dashboard" / "dist"
if (DASHBOARD_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DASHBOARD_DIST / "assets"), name="assets")


@app.get("/", response_model=None)
async def serve_dashboard():
    index = DASHBOARD_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        {
            "message": "Dashboard not built. Run: cd dashboard && npm run build",
            "dev_hint": "Or run ./start.sh for dev mode (Vite on :5173)",
        }
    )


@app.websocket("/ws")
async def pixel_agents_ws(websocket: WebSocket) -> None:
    """Pixel Agents protocol WebSocket (compatible with pixel-agents SPA)."""
    await manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")
            if msg_type == "webviewReady":
                await manager.send_initial_state(websocket)
            elif msg_type == "launchAgent":
                # Map pixel-agents launchAgent → run trading meeting
                await manager.run_meeting()
            elif msg_type == "requestDiagnostics":
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "agentDiagnostics",
                            "agents": [
                                {
                                    "id": cfg["id"],
                                    "name": cfg["name"],
                                    "role": cfg["role"],
                                    "status": "connected",
                                    "provider": "trading-office",
                                }
                                for cfg in AGENT_DESK_CONFIG
                            ],
                        },
                        ensure_ascii=False,
                    )
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server.app:app",
        host="127.0.0.1",
        port=8080,
        reload=False,
    )