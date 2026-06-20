import { useEffect, useState } from "react";
import type { MeetingIndexEntry } from "../types";

export function DecisionLogList() {
  const [meetings, setMeetings] = useState<MeetingIndexEntry[]>([]);
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);

  const load = async () => {
    const res = await fetch("/api/meetings");
    if (res.ok) setMeetings(await res.json());
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  const openMeeting = async (filename: string) => {
    const res = await fetch(`/api/meetings/file/${filename}`);
    if (res.ok) setSelected(await res.json());
  };

  return (
    <section className="panel log-panel">
      <div className="panel-header">
        <h2>Decision Log</h2>
        <button className="btn-ghost" onClick={load}>
          Refresh
        </button>
      </div>

      <div className="log-layout">
        <ul className="meeting-list">
          {meetings.map((m) => (
            <li key={m.json_file}>
              <button
                className="meeting-item"
                onClick={() => openMeeting(m.json_file)}
              >
                <span className="meeting-date">{m.meeting_date}</span>
                <span className="meeting-summary">{m.summary}</span>
                <span className="meeting-meta">
                  {m.trade_count} trade(s) · {m.approved ? "approved" : "pending"}
                </span>
              </button>
            </li>
          ))}
          {meetings.length === 0 && <li className="muted">No meetings logged yet.</li>}
        </ul>

        {selected && (
          <div className="meeting-detail">
            <h3>{String(selected.meeting_summary ?? selected.meeting_date)}</h3>
            <pre>{JSON.stringify(selected, null, 2)}</pre>
          </div>
        )}
      </div>
    </section>
  );
}