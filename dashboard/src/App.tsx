import { useCallback, useEffect, useState } from "react";
import { AgentRoster } from "./components/AgentRoster";
import { BacktestPanel } from "./components/BacktestPanel";
import { DecisionLogList } from "./components/DecisionLogList";
import { MeetingPanel } from "./components/MeetingPanel";
import { PixelOffice } from "./components/PixelOffice";
import { PipelinePanel } from "./components/PipelinePanel";
import { PaperPortfolioPanel } from "./components/PaperPortfolioPanel";
import { usePixelAgentsWs } from "./hooks/usePixelAgentsWs";
import type { AgentDesk } from "./types";
import "./App.css";



type Tab = "office" | "pipeline" | "portfolio" | "meetings" | "backtest" | "agents" | "logs";

export default function App() {
  const [tab, setTab] = useState<Tab>("office");
  const [agents, setAgents] = useState<AgentDesk[]>([]);
  const {
    connected,
    agentStates,
    transcript,
    meetingSummary,
    meetingRunning,
    pendingMeeting,
    llmEnabled,
    llmProvider,
    llmModel,
    runMeeting,
    submitApproval,
    palettes,
  } = usePixelAgentsWs();
  const [approvalBusy, setApprovalBusy] = useState(false);

  useEffect(() => {
    fetch("/api/agents")
      .then((r) => r.json())
      .then(setAgents)
      .catch(() => setAgents([]));
  }, []);

  const handleRunMeeting = useCallback(async () => {
    await runMeeting();
  }, [runMeeting]);

  const handleApprove = useCallback(
    async (meetingId: string) => {
      setApprovalBusy(true);
      try {
        await submitApproval(meetingId, true);
      } finally {
        setApprovalBusy(false);
      }
    },
    [submitApproval],
  );

  const handleReject = useCallback(
    async (meetingId: string) => {
      setApprovalBusy(true);
      try {
        await submitApproval(meetingId, false);
      } finally {
        setApprovalBusy(false);
      }
    },
    [submitApproval],
  );

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand-icon">◈</span>
          <div>
            <h1>AI Agent Trading Office</h1>
            <p>Multi-Agent Portfolio · Pixel Office Dashboard</p>
          </div>
        </div>
        <div className="header-status">
          <span className={`status-dot ${connected ? "online" : "offline"}`} />
          {connected ? "Pixel bridge connected" : "Connecting…"}
        </div>
      </header>

      <nav className="tab-nav">
        {(
          [
            ["office", "Pixel Office"],
            ["pipeline", "Trading Pipeline"],
            ["portfolio", "Paper Portfolio"],
            ["meetings", "Live Meeting"],
            ["backtest", "Backtest"],
            ["agents", "Agents"],
            ["logs", "Decision Log"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            className={tab === id ? "tab active" : "tab"}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {tab === "office" && (
          <div className="office-view">
            <PixelOffice
              agents={agents}
              agentStates={agentStates}
              palettes={palettes}
              connected={connected}
              meetingRunning={meetingRunning}
              pendingMeeting={pendingMeeting}
            />
            <MeetingPanel
              transcript={transcript.slice(-3)}
              meetingSummary={meetingSummary}
              meetingRunning={meetingRunning}
              onRunMeeting={handleRunMeeting}
              connected={connected}
              pendingMeeting={pendingMeeting}
              llmEnabled={llmEnabled}
              llmProvider={llmProvider}
              llmModel={llmModel}
              onApprove={handleApprove}
              onReject={handleReject}
              approvalBusy={approvalBusy}
            />
          </div>
        )}

        {tab === "meetings" && (
          <MeetingPanel
            transcript={transcript}
            meetingSummary={meetingSummary}
            meetingRunning={meetingRunning}
            onRunMeeting={handleRunMeeting}
            connected={connected}
            pendingMeeting={pendingMeeting}
            llmEnabled={llmEnabled}
            llmProvider={llmProvider}
            llmModel={llmModel}
            onApprove={handleApprove}
            onReject={handleReject}
            approvalBusy={approvalBusy}
          />
        )}

        {tab === "pipeline" && <PipelinePanel />}
        {tab === "portfolio" && <PaperPortfolioPanel />}

        {tab === "backtest" && <BacktestPanel />}
        {tab === "agents" && <AgentRoster agents={agents} />}
        {tab === "logs" && <DecisionLogList />}
      </main>

      <footer className="app-footer">
        Terminal mode · No VS Code required · Protocol compatible with{" "}
        <a href="https://github.com/pixel-agents-hq/pixel-agents" target="_blank" rel="noreferrer">
          pixel-agents
        </a>
      </footer>
    </div>
  );
}
