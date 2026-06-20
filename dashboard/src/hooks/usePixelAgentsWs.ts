import { useCallback, useEffect, useRef, useState } from "react";
import type { AgentState, ServerMessage, TranscriptEntry } from "../types";

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

  const runMeeting = useCallback(async () => {
    const res = await fetch("/api/meetings/run", { method: "POST" });
    return res.json();
  }, []);

  return {
    connected,
    agentStates,
    transcript,
    meetingSummary,
    meetingRunning,
    runMeeting,
    palettes: PALETTES,
  };
}