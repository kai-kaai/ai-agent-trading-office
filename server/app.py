"""FastAPI server – REST API + Pixel Agents WebSocket for Trading Office."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure project root is on sys.path when running as `python server/app.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.registry import AGENT_REGISTRY, list_roles  # noqa: E402
from backtest.context import get_cached_comparison, run_and_cache  # noqa: E402
from backtest.engine import DEFAULT_MONTHS  # noqa: E402
from core.llm.client import get_llm_status  # noqa: E402
from core.decision_log import DecisionLog  # noqa: E402
from server.pending_meeting import clear_pending, get_pending  # noqa: E402
from server.pixel_bridge import AGENT_DESK_CONFIG  # noqa: E402
from server.ws_manager import ConnectionManager  # noqa: E402


class ApprovalRequest(BaseModel):
    approved: bool

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


@app.get("/api/meetings/pending")
async def pending_meeting() -> dict:
    """Return the latest meeting awaiting human approval."""
    pending = get_pending()
    if pending is None:
        return {"pending": False}
    return {
        "pending": True,
        "meeting_id": pending.meeting_id,
        "json_file": pending.json_file,
        "summary": pending.summary,
        "trade_count": pending.trade_count,
        "trades": pending.trades,
        "decision_source": pending.decision_source,
        "approved": pending.approved,
    }


@app.post("/api/meetings/{meeting_id}/approve")
async def approve_meeting(meeting_id: str, body: ApprovalRequest) -> dict:
    """Approve or reject a proposed meeting decision (semi-auto mode)."""
    updated = decision_log.update_approval(meeting_id, approved=body.approved)
    if updated is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    pending = get_pending()
    if pending and pending.meeting_id == meeting_id:
        clear_pending()

    await manager.broadcast(
        {
            "type": "tradingMeetingEvent",
            "event": "decision_approved",
            "payload": {
                "meeting_id": meeting_id,
                "approved": body.approved,
                "status": "approved" if body.approved else "rejected",
            },
        }
    )

    return {
        "ok": True,
        "meeting_id": meeting_id,
        "approved": body.approved,
        "approval_status": "approved" if body.approved else "rejected",
    }


@app.get("/api/status")
async def office_status() -> dict:
    return {
        "connected_clients": len(manager.active),
        "meeting_running": manager.meeting_running,
        "agent_roles": list_roles(),
        "semi_auto": True,
        **get_llm_status(),
    }


@app.post("/api/backtest/run")
async def run_backtest(months: int = DEFAULT_MONTHS) -> dict:
    """Run AI Agent vs Tech Titans backtest and return comparison metrics."""
    comparison = run_and_cache(months=months)
    return comparison.to_dict()


@app.get("/api/backtest/latest")
async def latest_backtest() -> dict:
    """Return cached backtest results or run a default 6-month simulation."""
    comparison = get_cached_comparison()
    if comparison is None:
        comparison = run_and_cache(months=DEFAULT_MONTHS)
    return comparison.to_dict()


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