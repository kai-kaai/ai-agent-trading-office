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
  approval_status?: "approved" | "rejected" | "pending";
  recorded_at: string;
}

export interface ProposedTrade {
  ticker: string;
  action: string;
  shares: number;
  rationale?: string;
}

export interface PendingMeeting {
  meetingId: string;
  summary: string;
  trades: ProposedTrade[];
  tradeCount: number;
  decisionSource: string;
  approvalStatus: "pending" | "approved" | "rejected";
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