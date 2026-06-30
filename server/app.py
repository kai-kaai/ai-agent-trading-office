"""FastAPI server – REST API + Pixel Agents WebSocket for Trading Office."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
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
from backtest.data_loader import TechTitansData  # noqa: E402
from backtest.engine import DEFAULT_MONTHS  # noqa: E402
from core.llm.client import get_llm_status  # noqa: E402
from core.decision_log import DecisionLog  # noqa: E402
from server.pending_meeting import clear_pending, get_pending  # noqa: E402
from server.pixel_bridge import AGENT_DESK_CONFIG  # noqa: E402
from modules.brain import BrainModule  # noqa: E402
from modules.pipeline import PipelineContext, TradingPipeline  # noqa: E402
from server.ws_manager import ConnectionManager  # noqa: E402
from modules.paper_portfolio import PaperPortfolioManager  # noqa: E402


class ApprovalRequest(BaseModel):
    approved: bool


class PaperRebalanceRequest(BaseModel):
    portfolio: str
    tickers: list[str]



class CouncilEvaluateRequest(BaseModel):
    ticker: str
    action: str = "buy"


class PipelineRunRequest(BaseModel):
    ticker: str
    action: str = "buy"
    nav_usd: float = 10_000.0
    risk_reward: float = 2.0
    current_sectors: list[str] = []  # for A2 Shield sector overlap testing


class PipelineSimulateRequest(BaseModel):
    ticker: str
    action: str = "buy"
    nav_usd: float = 10_000.0
    risk_reward: float = 2.0
    current_sectors: list[str] = []
    volatility_regime: str = "normal"
    simulate_outcome: str = "win"  # "win", "loss", or "trailing_exit"
    score_override: float | None = None


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
        if body.approved and pending.trades:
            try:
                mgr = PaperPortfolioManager()
                mgr.execute_trades("ai_agent", pending.trades)
            except Exception as e:
                print(f"Error executing meeting trades on paper portfolio: {e}")
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
        "architecture": "five_module",
        **get_llm_status(),
    }


@app.get("/api/pipeline/info")
async def pipeline_info() -> dict:
    """Describe the Brain → Shield → CFO → Watchman pipeline."""
    return TradingPipeline.describe()


@app.post("/api/council/evaluate")
async def council_evaluate(body: CouncilEvaluateRequest) -> dict:
    """Run Brain scanners + AI Council for a ticker setup."""
    ticker = body.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker is required")
    action = body.action.lower().strip()
    if action not in {"buy", "sell"}:
        raise HTTPException(status_code=400, detail="action must be buy or sell")

    setup = BrainModule().evaluate(ticker, action=action)
    return setup.to_dict()


@app.post("/api/pipeline/run")
async def pipeline_run(body: PipelineRunRequest) -> dict:
    """Run the full Brain → Shield → CFO → Watchman pipeline."""
    ticker = body.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker is required")
    action = body.action.lower().strip()
    if action not in {"buy", "sell"}:
        raise HTTPException(status_code=400, detail="action must be buy or sell")

    result = TradingPipeline().run(
        ticker,
        action=action,
        context=PipelineContext(
            nav_usd=body.nav_usd,
            risk_reward=body.risk_reward,
            current_sectors=body.current_sectors,
        ),
    )
    return result.to_dict()


@app.post("/api/pipeline/simulate")
async def pipeline_simulate(body: PipelineSimulateRequest) -> dict:
    """Run the pipeline and simulate Watchman + Auditor lifecycle for A6 Dashboard."""
    ticker = body.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker is required")
    action = body.action.lower().strip()
    if action not in {"buy", "sell"}:
        raise HTTPException(status_code=400, detail="action must be buy or sell")

    # 1. Run Brain + Shield + CFO
    pipe = TradingPipeline()
    ctx = PipelineContext(
        nav_usd=body.nav_usd,
        risk_reward=body.risk_reward,
        current_sectors=body.current_sectors,
    )

    res = pipe.run(
        ticker,
        action=action,
        score_override=body.score_override,
        context=ctx,
    )

    if res.halted:
        return {
            "halted": True,
            "stage_reached": res.stage_reached.value,
            "halt_reason": res.halt_reason,
            "setup": res.setup.to_dict() if res.setup else None,
            "shield": res.shield.to_dict() if res.shield else None,
            "events": res.events,
            "simulation_steps": [],
            "autopsy": None,
            "strategy_candidate": None,
        }

    setup = res.setup
    shield = res.shield
    sized = res.sized_order

    # 2. Simulate Watchman lifecycle
    from modules.watchman.manager import WatchmanModule
    from modules.auditor.autopsy import AuditorModule
    from modules.models import PositionState, StrategyStage

    wm = WatchmanModule(paper_mode=True)
    auditor = AuditorModule()

    # Step 0: Plan Entry
    pos = wm.plan_entry(sized)
    steps = []

    def make_step_data(current_pos, price, evs, desc):
        pnl = current_pos.unrealized_pnl_pct(price)
        return {
            "description": desc,
            "price": round(price, 4),
            "state": current_pos.state.value,
            "trailing_stop": current_pos.trailing_stop,
            "take_profit": current_pos.take_profit,
            "stop_loss": current_pos.stop_loss,
            "events": evs,
            "unrealized_pnl_pct": round(pnl, 4) if pnl is not None else None,
        }

    steps.append(make_step_data(pos, sized.entry_price, ["Watchman planned entry (PENDING)"], "Planned position entry"))

    # Step 1: Activate
    pos = wm.activate(pos)
    steps.append(make_step_data(pos, sized.entry_price, ["Watchman simulated fill (OPEN)"], "Position filled / activated"))

    # Determine simulated price path
    entry = sized.entry_price
    stop = sized.stop_loss
    tp = sized.take_profit

    is_long = action != "sell"
    target_dist = abs(tp - entry) if tp else (entry * 0.1)
    stop_dist = abs(entry - stop) if stop else (entry * 0.05)

    price_path = []
    if body.simulate_outcome == "win":
        if is_long:
            price_path = [
                entry + target_dist * 0.25,
                entry + target_dist * 0.60,
                entry + target_dist * 0.85,
                tp + target_dist * 0.02,  # exceeds TP
            ]
        else:
            price_path = [
                entry - target_dist * 0.25,
                entry - target_dist * 0.60,
                entry - target_dist * 0.85,
                tp - target_dist * 0.02,
            ]
    elif body.simulate_outcome == "loss":
        if is_long:
            price_path = [
                entry - stop_dist * 0.40,
                stop - stop_dist * 0.02,  # hits stop
            ]
        else:
            price_path = [
                entry + stop_dist * 0.40,
                stop + stop_dist * 0.02,
            ]
    else:  # trailing_exit
        if is_long:
            price_path = [
                entry + target_dist * 0.30,  # rises, trail moves up
                entry + target_dist * 0.70,  # rises more, trail moves up
                entry + target_dist * 0.35,  # drops and hits trailing stop
            ]
        else:
            price_path = [
                entry - target_dist * 0.30,
                entry - target_dist * 0.70,
                entry - target_dist * 0.35,
            ]

    # Run price path through Watchman
    for p in price_path:
        pos, evs = wm.update_price(pos, p)
        desc = f"Price update: {p:.2f}"
        if pos.state == PositionState.CLOSED:
            desc = "Position exited (stop / take profit hit)"
        steps.append(make_step_data(pos, p, evs, desc))
        if pos.state == PositionState.CLOSED:
            break

    # 3. Auditor Autopsy (only if closed)
    autopsy_data = None
    strategy_candidate_data = None

    if pos.state == PositionState.CLOSED:
        outcome_label = "take_profit" if (is_long and pos.last_price >= tp) or (not is_long and pos.last_price <= tp) else "stop_loss"
        autopsy = auditor.autopsy_from_position(
            trade_id=f"sim-trade-{ticker}-{pos.position_id[-6:]}",
            position=pos,
            outcome=outcome_label,
            entry_setup={"score": setup.score, "grade": setup.grade.value, "ticker": setup.ticker}
        )
        autopsy_data = autopsy.to_dict()

        # Propose strategy candidate based on autopsy
        cand_name = f"{ticker} Trend Adaptive"
        cand = auditor.propose_strategy(cand_name, f"Simulated strategy candidate following autopsy of {ticker}.", autopsy.trade_id)

        # Simulate promotions
        promotions = []
        promotions.append(cand.to_dict())  # Stage: CANDIDATE

        cand = auditor.promote(cand, StrategyStage.BACKTEST)
        cand = auditor.attach_backtest_results(cand, {"alpha": 0.045, "total_return": 0.142})
        promotions.append(cand.to_dict())  # Stage: BACKTEST

        cand = auditor.review_and_promote(cand, sandbox_ok=True)
        promotions.append(cand.to_dict())  # Stage: SANDBOX / LIVE

        strategy_candidate_data = {
            "current": cand.to_dict(),
            "history": promotions
        }

    return {
        "halted": False,
        "stage_reached": "complete",
        "setup": setup.to_dict(),
        "shield": shield.to_dict(),
        "sized_order": sized.to_dict(),
        "events": res.events,
        "simulation_steps": steps,
        "autopsy": autopsy_data,
        "strategy_candidate": strategy_candidate_data,
    }


@app.get("/api/paper/portfolio")
async def get_paper_portfolios() -> dict:
    """Get live values and holdings for both paper portfolios."""
    mgr = PaperPortfolioManager()
    return {
        "tech_titans": mgr.get_portfolio_view("tech_titans"),
        "ai_agent": mgr.get_portfolio_view("ai_agent"),
        "transactions": mgr.data.get("transactions", [])
    }


@app.post("/api/paper/rebalance")
async def rebalance_paper_portfolio(body: PaperRebalanceRequest) -> dict:
    """Rebalance the specified paper portfolio to target equal-weight tickers."""
    mgr = PaperPortfolioManager()
    try:
        view = mgr.rebalance(body.portfolio, body.tickers)
        return {
            "status": "success",
            "portfolio": body.portfolio,
            "view": view,
            "transactions": mgr.data.get("transactions", [])
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/paper/inject")
async def inject_paper_capital() -> dict:
    """Inject $305 cash into both paper portfolios."""
    mgr = PaperPortfolioManager()
    mgr.inject_capital(305.0)
    return {
        "status": "success",
        "tech_titans": mgr.get_portfolio_view("tech_titans"),
        "ai_agent": mgr.get_portfolio_view("ai_agent"),
        "transactions": mgr.data.get("transactions", [])
    }


@app.post("/api/paper/reset")
async def reset_paper_portfolios() -> dict:
    """Reset both portfolios to $10,000 cash and empty holdings."""
    mgr = PaperPortfolioManager()
    mgr.reset()
    return {
        "status": "success",
        "tech_titans": mgr.get_portfolio_view("tech_titans"),
        "ai_agent": mgr.get_portfolio_view("ai_agent"),
        "transactions": []
    }




@app.post("/api/backtest/run")
async def run_backtest(months: int = Query(DEFAULT_MONTHS, ge=1)) -> dict:
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


@app.get("/api/portfolio/latest")
async def latest_portfolio() -> dict:
    """Return the current simulated portfolio with values and allocation weights."""
    comparison = get_cached_comparison()
    if comparison is None:
        comparison = run_and_cache(months=DEFAULT_MONTHS)

    agent = comparison.agent
    data = TechTitansData()
    cash = agent.nav_history[-1].cash if agent.nav_history else agent.final_nav
    positions = []
    for ticker, shares in agent.final_holdings.items():
        price = data.price(ticker, agent.end_date)
        market_value = shares * price
        positions.append(
            {
                "ticker": ticker,
                "shares": round(shares, 4),
                "price": round(price, 4),
                "market_value": round(market_value, 2),
                "weight_pct": round(
                    market_value / agent.final_nav * 100 if agent.final_nav else 0.0,
                    2,
                ),
            }
        )

    positions.sort(key=lambda item: item["market_value"], reverse=True)
    return {
        "as_of": agent.end_date.isoformat(),
        "source": "backtest",
        "total_nav": round(agent.final_nav, 2),
        "cash": round(cash, 2),
        "cash_weight_pct": round(cash / agent.final_nav * 100 if agent.final_nav else 0.0, 2),
        "total_return_pct": round(agent.total_return * 100, 2),
        "position_count": len(positions),
        "positions": positions,
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
