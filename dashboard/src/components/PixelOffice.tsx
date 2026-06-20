import type { CSSProperties } from "react";
import type { AgentDesk, AgentState } from "../types";

interface Props {
  agents: AgentDesk[];
  agentStates: Record<number, AgentState>;
  palettes: string[];
}

const SEAT_ORDER = [
  "desk-ceo",
  "desk-fa",
  "desk-nr",
  "desk-mr",
  "desk-rm",
  "desk-bt",
];

export function PixelOffice({ agents, agentStates, palettes }: Props) {
  const bySeat = Object.fromEntries(agents.map((a) => [a.seatId, a]));

  return (
    <div className="pixel-office">
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