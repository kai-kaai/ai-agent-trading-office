import { useCallback, useEffect, useRef, useState } from "react";
import type { AgentState, PendingMeeting, ProposedTrade, ServerMessage, TranscriptEntry } from "../types";

const PALETTES = [
  "#4ade80",
  "#60a5fa",
  "#f472b6",
  "#fbbf24",
  "#a78bfa",
  "#fb923c",
];

export function usePixelAgentsWs() {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [agentStates, setAgentStates] = useState<Record<number, AgentState>>({});
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [meetingSummary, setMeetingSummary] = useState<string | null>(null);
  const [meetingRunning, setMeetingRunning] = useState(false);
  const [pendingMeeting, setPendingMeeting] = useState<PendingMeeting | null>(null);
  const [llmEnabled, setLlmEnabled] = useState(false);
  const [llmProvider, setLlmProvider] = useState("none");
  const [llmModel, setLlmModel] = useState("");

  const loadPending = useCallback(async () => {
    try {
      const res = await fetch("/api/meetings/pending");
      if (!res.ok) return;
      const data = await res.json();
      if (data.pending) {
        setPendingMeeting({
          meetingId: data.meeting_id,
          summary: data.summary,
          trades: data.trades ?? [],
          tradeCount: data.trade_count ?? 0,
          decisionSource: data.decision_source ?? "unknown",
          approvalStatus: data.approved ? "approved" : "pending",
        });
      }
    } catch {
      /* ignore */
    }
  }, []);

  const handleMessage = useCallback((msg: ServerMessage) => {
    switch (msg.type) {
      case "agentStatus": {
        const id = msg.id as number;
        const status = msg.status as "active" | "waiting";
        setAgentStates((prev) => ({
          ...prev,
          [id]: { ...prev[id], id, status, toolStatus: status === "waiting" ? undefined : prev[id]?.toolStatus },
        }));
        break;
      }
      case "agentToolStart": {
        const id = msg.id as number;
        const status = msg.status as string;
        setAgentStates((prev) => ({
          ...prev,
          [id]: { id, status: "active", toolStatus: status },
        }));
        break;
      }
      case "agentToolDone":
      case "agentToolsClear": {
        const id = msg.id as number;
        setAgentStates((prev) => ({
          ...prev,
          [id]: { ...prev[id], id, toolStatus: undefined },
        }));
        break;
      }
      case "tradingMeetingEvent": {
        const event = msg.event as string;
        const payload = msg.payload as Record<string, unknown>;
        if (event === "meeting_started") {
          setMeetingRunning(true);
          setTranscript([]);
          setMeetingSummary(null);
          setPendingMeeting(null);
        } else if (event === "utterance") {
          setTranscript((prev) => [
            ...prev,
            {
              phase: payload.phase as string,
              agent: payload.agent as string,
              content: payload.content as string,
              summary: payload.summary as string | undefined,
              ts: Date.now(),
            },
          ]);
        } else if (event === "meeting_completed") {
          setMeetingRunning(false);
          setMeetingSummary(payload.summary as string);
          setPendingMeeting({
            meetingId: payload.meeting_id as string,
            summary: payload.summary as string,
            trades: (payload.trades as ProposedTrade[]) ?? [],
            tradeCount: (payload.trade_count as number) ?? 0,
            decisionSource: (payload.decision_source as string) ?? "unknown",
            approvalStatus: "pending",
          });
        } else if (event === "decision_approved") {
          const approved = payload.approved as boolean;
          setPendingMeeting((prev) =>
            prev
              ? {
                  ...prev,
                  approvalStatus: approved ? "approved" : "rejected",
                }
              : prev,
          );
        }
        break;
      }
      default:
        break;
    }
  }, []);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: "webviewReady" }));
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as ServerMessage;
        handleMessage(msg);
      } catch {
        /* ignore */
      }
    };

    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    return () => ws.close();
  }, [handleMessage]);

  useEffect(() => {
    fetch("/api/status")
      .then((r) => r.json())
      .then((data) => {
        setLlmEnabled(Boolean(data.llm_enabled ?? data.grok_enabled));
        setLlmProvider(String(data.llm_provider ?? "none"));
        setLlmModel(String(data.llm_model ?? data.grok_model ?? ""));
      })
      .catch(() => {
        setLlmEnabled(false);
        setLlmProvider("none");
        setLlmModel("");
      });
    void loadPending();
  }, [loadPending]);

  const runMeeting = useCallback(async () => {
    const res = await fetch("/api/meetings/run", { method: "POST" });
    return res.json();
  }, []);

  const submitApproval = useCallback(async (meetingId: string, approved: boolean) => {
    const res = await fetch(`/api/meetings/${meetingId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved }),
    });
    if (!res.ok) throw new Error(`Approval failed (${res.status})`);
    const data = await res.json();
    setPendingMeeting((prev) =>
      prev
        ? {
            ...prev,
            approvalStatus: data.approved ? "approved" : "rejected",
          }
        : prev,
    );
    return data;
  }, []);

  return {
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
    palettes: PALETTES,
  };
}