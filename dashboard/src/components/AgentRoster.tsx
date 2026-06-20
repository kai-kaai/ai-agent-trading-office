import type { AgentDesk } from "../types";

interface Props {
  agents: AgentDesk[];
}

export function AgentRoster({ agents }: Props) {
  return (
    <section className="panel roster-panel">
      <h2>Agent Roster</h2>
      <div className="roster-grid">
        {agents.map((agent) => (
          <div key={agent.id} className="roster-card">
            <div className="roster-badge">{agent.short}</div>
            <h3>{agent.name}</h3>
            <p className="roster-role">{agent.role}</p>
            <p className="roster-desc">{agent.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}