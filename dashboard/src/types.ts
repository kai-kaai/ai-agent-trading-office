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

export interface NavPoint {
  date: string;
  nav: number;
  cash: number;
  holdings_count: number;
  injected_capital: number;
}

export interface BacktestSide {
  name: string;
  start_date: string;
  end_date: string;
  total_injected: number;
  final_nav: number;
  total_return_pct: number;
  trade_count: number;
  final_holdings: Record<string, number>;
  nav_history: NavPoint[];
}

export interface BacktestResult {
  agent: BacktestSide;
  benchmark: BacktestSide;
  alpha_pct: number;
  months: number;
  weekly_rebalances: number;
}

export interface PortfolioPositionSnapshot {
  ticker: string;
  shares: number;
  price: number;
  market_value: number;
  weight_pct: number;
}

export interface PortfolioSnapshot {
  as_of: string;
  source: "backtest";
  total_nav: number;
  cash: number;
  cash_weight_pct: number;
  total_return_pct: number;
  position_count: number;
  positions: PortfolioPositionSnapshot[];
}
