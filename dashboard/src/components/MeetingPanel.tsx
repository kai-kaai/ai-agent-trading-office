import type { TranscriptEntry } from "../types";

interface Props {
  transcript: TranscriptEntry[];
  meetingSummary: string | null;
  meetingRunning: boolean;
  onRunMeeting: () => void;
  connected: boolean;
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
}: Props) {
  return (
    <section className="panel meeting-panel">
      <div className="panel-header">
        <h2>Live Meeting</h2>
        <button
          className="btn-primary"
          onClick={onRunMeeting}
          disabled={!connected || meetingRunning}
        >
          {meetingRunning ? "Meeting in progress…" : "Run Weekly Meeting"}
        </button>
      </div>

      {meetingSummary && (
        <div className="decision-banner">
          <strong>Decision:</strong> {meetingSummary}
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