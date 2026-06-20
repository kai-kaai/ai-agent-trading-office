import type { PendingMeeting, TranscriptEntry } from "../types";

interface Props {
  transcript: TranscriptEntry[];
  meetingSummary: string | null;
  meetingRunning: boolean;
  onRunMeeting: () => void;
  connected: boolean;
  pendingMeeting?: PendingMeeting | null;
  llmEnabled?: boolean;
  llmProvider?: string;
  llmModel?: string;
  onApprove?: (meetingId: string) => void;
  onReject?: (meetingId: string) => void;
  approvalBusy?: boolean;
}

const PHASE_LABELS: Record<string, string> = {
  opening: "Opening",
  report: "Report",
  deliberation: "Deliberation",
  decision: "Decision",
};

export function MeetingPanel({
  transcript,
  meetingSummary,
  meetingRunning,
  onRunMeeting,
  connected,
  pendingMeeting,
  llmEnabled = false,
  llmProvider = "none",
  llmModel = "",
  onApprove,
  onReject,
  approvalBusy = false,
}: Props) {
  const showApproval =
    pendingMeeting &&
    pendingMeeting.approvalStatus === "pending" &&
    onApprove &&
    onReject;

  return (
    <section className="panel meeting-panel">
      <div className="panel-header">
        <h2>Live Meeting</h2>
        <div className="panel-header-actions">
          <span className={`llm-badge ${llmEnabled ? "on" : "off"}`} title={llmModel}>
            LLM {llmEnabled ? `${llmProvider}` : "OFF"}
          </span>
          <button
            className="btn-primary"
            onClick={onRunMeeting}
            disabled={!connected || meetingRunning}
          >
            {meetingRunning ? "Meeting in progress…" : "Run Weekly Meeting"}
          </button>
        </div>
      </div>

      {meetingSummary && (
        <div className="decision-banner">
          <strong>Decision:</strong> {meetingSummary}
        </div>
      )}

      {showApproval && (
        <div className="approval-panel">
          <div className="approval-header">
            <h3>Semi-Auto — Awaiting Your Approval</h3>
            <span className="approval-source">
              Source: {pendingMeeting.decisionSource}
            </span>
          </div>
          <p className="approval-summary">{pendingMeeting.summary}</p>

          {pendingMeeting.trades.length > 0 ? (
            <ul className="approval-trades">
              {pendingMeeting.trades.map((trade) => (
                <li key={`${trade.ticker}-${trade.action}`}>
                  <strong>{trade.action.toUpperCase()}</strong> {trade.ticker}
                  {trade.shares > 0 ? ` · ${trade.shares} shares` : ""}
                  {trade.rationale && (
                    <span className="trade-rationale"> — {trade.rationale}</span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No trades proposed — HOLD current allocation.</p>
          )}

          <div className="approval-actions">
            <button
              className="btn-approve"
              disabled={approvalBusy}
              onClick={() => onApprove(pendingMeeting.meetingId)}
            >
              Approve
            </button>
            <button
              className="btn-reject"
              disabled={approvalBusy}
              onClick={() => onReject(pendingMeeting.meetingId)}
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {pendingMeeting && pendingMeeting.approvalStatus !== "pending" && (
        <div
          className={`approval-result ${
            pendingMeeting.approvalStatus === "approved" ? "approved" : "rejected"
          }`}
        >
          Decision {pendingMeeting.approvalStatus === "approved" ? "approved" : "rejected"}.
          Logged to Decision Log.
        </div>
      )}

      <div className="transcript-feed">
        {transcript.length === 0 && !meetingRunning && (
          <p className="muted">Press "Run Weekly Meeting" to start a live session.</p>
        )}
        {transcript.map((entry, i) => (
          <article key={`${entry.ts}-${i}`} className={`transcript-item phase-${entry.phase}`}>
            <header>
              <span className="phase-tag">{PHASE_LABELS[entry.phase] ?? entry.phase}</span>
              <strong>{entry.agent}</strong>
            </header>
            <pre>{entry.content}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}