export interface AgentDesk {
  id: number;
  role: string;
  name: string;
  short: string;
  description: string;
  seatId: string;
  palette: number;
  folderName: string;
}

export interface AgentState {
  id: number;
  status: "active" | "waiting";
  toolStatus?: string;
}

export interface MeetingIndexEntry {
  meeting_id: string;
  json_file: string;
  md_file: string;
  meeting_date: string;
  summary: string;
  trade_count: number;
  approved: boolean;
  recorded_at: string;
}

export interface TranscriptEntry {
  phase: string;
  agent: string;
  content: string;
  summary?: string;
  ts: number;
}

export type ServerMessage = {
  type: string;
  [key: string]: unknown;
};