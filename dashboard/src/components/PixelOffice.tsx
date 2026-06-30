import { useEffect, useState, type CSSProperties } from "react";
import type { AgentDesk, AgentState, BacktestResult, PendingMeeting } from "../types";

interface Props {
  agents: AgentDesk[];
  agentStates: Record<number, AgentState>;
  palettes: string[];
  connected: boolean;
  meetingRunning: boolean;
  pendingMeeting: PendingMeeting | null;
}

const SEAT_ORDER = [
  "desk-ceo",
  "desk-fa",
  "desk-nr",
  "desk-mr",
  "desk-rm",
  "desk-bt",
];

export function PixelOffice({ agents, agentStates, palettes, connected, meetingRunning, pendingMeeting }: Props) {
  const bySeat = Object.fromEntries(agents.map((a) => [a.seatId, a]));
  const [backtest, setBacktest] = useState<BacktestResult | null>(null);

  useEffect(() => {
    fetch("/api/backtest/latest")
      .then((response) => response.ok ? response.json() : null)
      .then((result) => result && setBacktest(result as BacktestResult))
      .catch(() => setBacktest(null));
    const update = (event: Event) => setBacktest((event as CustomEvent<BacktestResult>).detail);
    window.addEventListener("backtest-updated", update);
    return () => window.removeEventListener("backtest-updated", update);
  }, []);

  const mode = meetingRunning ? "LIVE MEETING" : pendingMeeting?.approvalStatus === "pending" ? "AWAITING APPROVAL" : "MONITORING";

  return (
    <div className="pixel-office">
      <div className="office-command-bar">
        <div className="office-mode"><span className={`status-dot ${connected ? "online" : "offline"}`} /><strong>{mode}</strong></div>
        <div className="office-stat"><span>Bridge</span><strong>{connected ? "ONLINE" : "OFFLINE"}</strong></div>
        <div className="office-stat"><span>Backtest</span><strong>{backtest ? `${backtest.months}M READY` : "LOADING"}</strong></div>
        <div className="office-stat"><span>Alpha</span><strong className={(backtest?.alpha_pct ?? 0) >= 0 ? "positive" : "negative"}>{backtest ? `${backtest.alpha_pct >= 0 ? "+" : ""}${backtest.alpha_pct.toFixed(2)}%` : "—"}</strong></div>
      </div>
      <div className="office-floor">
        {SEAT_ORDER.map((seatId) => {
          const agent = bySeat[seatId];
          if (!agent) return null;
          const state = agentStates[agent.id];
          const isActive = state?.status === "active";
          const color = palettes[agent.palette % palettes.length];

          return (
            <div key={seatId} className={`desk-cell ${isActive ? "desk-active" : ""}`}>
              <div className="desk-furniture">
                <div className="desk-surface" />
                <div className="desk-monitor" />
              </div>
              <div
                className={`pixel-agent ${isActive ? "pixel-agent-typing" : "pixel-agent-idle"}`}
                style={{ "--agent-color": color } as CSSProperties}
                title={agent.name}
              >
                <div className="pixel-head" />
                <div className="pixel-body" />
                <div className="pixel-legs" />
              </div>
              {state?.toolStatus && (
                <div className="speech-bubble">{state.toolStatus}</div>
              )}
              <div className="agent-label">
                <span className="agent-short">{agent.short}</span>
                <span className="agent-role">{agent.folderName}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
