import { useState, useEffect, useCallback } from "react";

interface PositionSnapshot {
  ticker: string;
  shares: number;
  price: number;
  market_value: number;
  weight_pct: number;
}

interface PortfolioView {
  total_nav: number;
  cash: number;
  cash_weight_pct: number;
  total_return_pct: number;
  positions: PositionSnapshot[];
}

interface Transaction {
  portfolio: string;
  timestamp: string;
  ticker: string;
  action: string;
  shares: number;
  price: number;
  value: number;
}

interface PaperData {
  tech_titans: PortfolioView;
  ai_agent: PortfolioView;
  transactions: Transaction[];
}

interface ProposedTrade {
  ticker: string;
  action: string;
  shares: number;
  rationale?: string;
}

interface PendingMeeting {
  pending: boolean;
  meeting_id?: string;
  summary?: string;
  trades?: ProposedTrade[];
  trade_count?: number;
}

export function PaperPortfolioPanel() {
  const [data, setData] = useState<PaperData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Meeting & Approval states
  const [meetingRunning, setMeetingRunning] = useState(false);
  const [meetingStatus, setMeetingStatus] = useState("");
  const [pendingMeeting, setPendingMeeting] = useState<PendingMeeting | null>(null);
  const [approvalBusy, setApprovalBusy] = useState(false);

  // Form states
  const [techTitansInput, setTechTitansInput] = useState("");
  const [aiAgentInput, setAiAgentInput] = useState("");
  const [rebalanceLoading, setRebalanceLoading] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/paper/portfolio");
      if (!response.ok) {
        throw new Error("Failed to load paper portfolios");
      }
      const resData = (await response.json()) as PaperData;
      setData(resData);

      // Pre-fill input boxes with current tickers if inputs are empty
      if (resData.tech_titans.positions.length > 0 && !techTitansInput) {
        setTechTitansInput(resData.tech_titans.positions.map((p) => p.ticker).join(", "));
      }
      if (resData.ai_agent.positions.length > 0 && !aiAgentInput) {
        setAiAgentInput(resData.ai_agent.positions.map((p) => p.ticker).join(", "));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error fetching portfolio data");
    } finally {
      setLoading(false);
    }
  }, [techTitansInput, aiAgentInput]);

  const checkPendingMeeting = useCallback(async () => {
    try {
      const response = await fetch("/api/meetings/pending");
      if (response.ok) {
        const pMeeting = (await response.json()) as PendingMeeting;
        setPendingMeeting(pMeeting.pending ? pMeeting : null);
      }
    } catch (err) {
      console.error("Error checking pending meeting:", err);
    }
  }, []);

  useEffect(() => {
    void loadData();
    void checkPendingMeeting();
  }, [loadData, checkPendingMeeting]);

  const handleRunMeeting = async () => {
    setMeetingRunning(true);
    setMeetingStatus("Initiating AI Agent Weekly Deliberation...");
    setError(null);
    try {
      // 1. Initiate meeting (blocks until completion)
      const response = await fetch("/api/meetings/run", { method: "POST" });
      if (!response.ok) {
        throw new Error("Meeting execution failed");
      }
      setMeetingStatus("Meeting completed! Awaiting your approval...");
      // 2. Fetch the newly created pending meeting
      await checkPendingMeeting();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error running weekly meeting");
    } finally {
      setMeetingRunning(false);
      setMeetingStatus("");
    }
  };

  const handleApproveMeeting = async (approved: boolean) => {
    if (!pendingMeeting || !pendingMeeting.meeting_id) return;
    setApprovalBusy(true);
    setError(null);
    try {
      const response = await fetch(`/api/meetings/${pendingMeeting.meeting_id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approved }),
      });

      if (!response.ok) {
        throw new Error("Failed to submit approval decision");
      }

      setPendingMeeting(null);
      // Reload holdings and transactions to show new balances!
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error approving meeting rebalance");
    } finally {
      setApprovalBusy(false);
    }
  };

  const handleRebalance = async (portfolio: "tech_titans" | "ai_agent", tickersString: string) => {
    setRebalanceLoading(portfolio);
    setError(null);
    try {
      const tickers = tickersString
        .split(",")
        .map((t) => t.trim().toUpperCase())
        .filter((t) => t.length > 0);

      const response = await fetch("/api/paper/rebalance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ portfolio, tickers }),
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail.detail || "Rebalance failed");
      }

      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error rebalancing portfolio");
    } finally {
      setRebalanceLoading(null);
    }
  };

  const handleInject = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/paper/inject", { method: "POST" });
      if (!response.ok) {
        throw new Error("Failed to inject capital");
      }
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error injecting capital");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm("Are you sure you want to reset both portfolios back to initial $10,000 cash?")) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/paper/reset", { method: "POST" });
      if (!response.ok) {
        throw new Error("Failed to reset portfolios");
      }
      setTechTitansInput("");
      setAiAgentInput("");
      setPendingMeeting(null);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error resetting portfolio");
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleString();
    } catch {
      return isoString;
    }
  };

  const alpha = data
    ? data.ai_agent.total_nav - data.tech_titans.total_nav
    : 0.0;
  const alphaPct = data
    ? data.ai_agent.total_return_pct - data.tech_titans.total_return_pct
    : 0.0;

  return (
    <div className="paper-portfolio-panel">
      {/* 1. Header */}
      <div className="portfolio-header">
        <div>
          <h2>Live Paper Portfolio Sandbox</h2>
          <p className="panel-sub">
            Track and compare weekly AI Agent rebalances against monthly Tech Titans selections (executed at Market Open price).
          </p>
        </div>
      </div>

      {error && <div className="portfolio-error">{error}</div>}

      {/* 2. Top Metric Cards */}
      {data && (
        <div className="portfolio-metrics-row">
          <div className="metric-card bg-glow-agent">
            <span className="metric-label">AI Agent Return</span>
            <span
              className={`metric-value ${
                data.ai_agent.total_return_pct >= 0 ? "positive" : "negative"
              }`}
            >
              {data.ai_agent.total_return_pct >= 0 ? "+" : ""}
              {data.ai_agent.total_return_pct.toFixed(2)}%
            </span>
            <span className="metric-sub">
              NAV: ${data.ai_agent.total_nav.toLocaleString(undefined, { minimumFractionDigits: 2 })} (Cash: ${data.ai_agent.cash.toLocaleString()})
            </span>
          </div>

          <div className="metric-card bg-glow-titans">
            <span className="metric-label">Tech Titans Return</span>
            <span
              className={`metric-value ${
                data.tech_titans.total_return_pct >= 0 ? "positive" : "negative"
              }`}
            >
              {data.tech_titans.total_return_pct >= 0 ? "+" : ""}
              {data.tech_titans.total_return_pct.toFixed(2)}%
            </span>
            <span className="metric-sub">
              NAV: ${data.tech_titans.total_nav.toLocaleString(undefined, { minimumFractionDigits: 2 })} (Cash: ${data.tech_titans.cash.toLocaleString()})
            </span>
          </div>

          <div className={`metric-card alpha-card ${alphaPct >= 0 ? "positive-glow" : "negative-glow"}`}>
            <span className="metric-label">Alpha (vs Benchmark)</span>
            <span className={`metric-value ${alphaPct >= 0 ? "positive" : "negative"}`}>
              {alphaPct >= 0 ? "+" : ""}
              {alphaPct.toFixed(2)}%
            </span>
            <span className="metric-sub">
              NAV diff: {alpha >= 0 ? "+" : ""}${alpha.toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      )}

      {/* 3. Control Panel Bar */}
      <div className="portfolio-actions-bar">
        <button className="btn-primary" onClick={handleInject} disabled={loading || meetingRunning}>
          Inject Monthly Capital ($305)
        </button>
        <button className="btn-ghost" onClick={handleReset} disabled={loading || meetingRunning}>
          Reset Sandbox Portfolios
        </button>
        <button className="btn-ghost" onClick={loadData} disabled={loading || meetingRunning}>
          Refresh Prices
        </button>
      </div>

      {/* 4. Active Pending Meeting Approval Box */}
      {pendingMeeting && pendingMeeting.trades && (
        <div className="approval-panel paper-meeting-approval">
          <div className="approval-header">
            <h3>🤝 AI Agent Weekly Meeting Summary — Awaiting Your Approval</h3>
            <span className="approval-source">Awaiting execution at Market Open</span>
          </div>
          <p className="approval-summary"><strong>Meeting conclusion:</strong> {pendingMeeting.summary}</p>
          <ul className="approval-trades">
            {pendingMeeting.trades.map((trade, i) => (
              <li key={i}>
                <strong className={trade.action}>{trade.action.toUpperCase()}</strong> {trade.ticker} · {trade.shares} shares
                {trade.rationale && <span className="trade-rationale"> — {trade.rationale}</span>}
              </li>
            ))}
            {pendingMeeting.trades.length === 0 && (
              <li className="muted">No trades proposed — HOLD current allocation.</li>
            )}
          </ul>
          <div className="approval-actions">
            <button
              className="btn-approve"
              onClick={() => handleApproveMeeting(true)}
              disabled={approvalBusy}
            >
              Approve & Execute Trades
            </button>
            <button
              className="btn-reject"
              onClick={() => handleApproveMeeting(false)}
              disabled={approvalBusy}
            >
              Reject & Dismiss
            </button>
          </div>
        </div>
      )}

      {/* 5. Interactive Rebalancing Inputs */}
      <div className="rebalance-forms-row">
        {/* Tech Titans input */}
        <div className="card rebalance-form-card">
          <h3>📅 Tech Titans Monthly Input</h3>
          <p className="card-sub">
            Input stocks selected by Tech Titans for this month. Portfolio will equal-weight the cash among them at market open price.
          </p>
          <div className="form-group">
            <label>Tech Titans Tickers (comma-separated)</label>
            <input
              type="text"
              value={techTitansInput}
              onChange={(e) => setTechTitansInput(e.target.value)}
              placeholder="AAPL, MSFT, NVDA, TSLA, AVGO"
            />
          </div>
          <button
            className="btn-primary btn-rebalance-submit"
            onClick={() => handleRebalance("tech_titans", techTitansInput)}
            disabled={rebalanceLoading !== null || meetingRunning}
          >
            {rebalanceLoading === "tech_titans" ? "Rebalancing at Open…" : "Execute Tech Titans Rebalance"}
          </button>
        </div>

        {/* AI Agent Automated Trigger */}
        <div className="card rebalance-form-card">
          <h3>⚡ AI Agent Rebalance Meeting</h3>
          <p className="card-sub">
            Initiate the AI Agent weekly rebalance. The 6 agents will perform their analysis, hold a deliberation meeting, and propose trades.
          </p>
          {meetingRunning ? (
            <div className="meeting-loader-container">
              <div className="spinner" />
              <div className="meeting-status-text">{meetingStatus}</div>
            </div>
          ) : (
            <div className="agent-trigger-box">
              <button
                className="btn-primary btn-rebalance-submit btn-initiate-agent"
                onClick={handleRunMeeting}
                disabled={loading || rebalanceLoading !== null}
              >
                Initiate AI Agent Rebalance Meeting
              </button>
              <div className="divider-or"><span>OR MANUALLY REBALANCE</span></div>
              <div className="form-group">
                <input
                  type="text"
                  value={aiAgentInput}
                  onChange={(e) => setAiAgentInput(e.target.value)}
                  placeholder="NFLX, AMZN, WDAY, GOOG"
                />
              </div>
              <button
                className="btn-ghost btn-rebalance-submit"
                onClick={() => handleRebalance("ai_agent", aiAgentInput)}
                disabled={rebalanceLoading !== null}
              >
                Execute Manual rebalance
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 6. Holdings Display Tables */}
      {data && (
        <div className="holdings-tables-row">
          {/* AI Agent Holdings */}
          <div className="card holdings-card">
            <div className="holdings-header">
              <h3>🤖 AI Agent Holdings ({data.ai_agent.positions.length})</h3>
              <strong>NAV: ${data.ai_agent.total_nav.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
            </div>
            <div className="holdings-table-wrap">
              <table className="holdings-table">
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Shares</th>
                    <th>Open Price</th>
                    <th>Market Value</th>
                    <th>Weight</th>
                  </tr>
                </thead>
                <tbody>
                  {data.ai_agent.positions.map((pos) => (
                    <tr key={pos.ticker}>
                      <td><strong>{pos.ticker}</strong></td>
                      <td>{pos.shares.toFixed(2)}</td>
                      <td>${pos.price.toFixed(2)}</td>
                      <td>${pos.market_value.toLocaleString()}</td>
                      <td>
                        <div className="weight-cell">
                          <span>{pos.weight_pct.toFixed(1)}%</span>
                          <i>
                            <b style={{ width: `${Math.min(pos.weight_pct, 100)}%` }} />
                          </i>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {data.ai_agent.positions.length === 0 && (
                    <tr>
                      <td colSpan={5} className="table-empty">No positions held (100% Cash)</td>
                    </tr>
                  )}
                  <tr className="table-cash-row">
                    <td><strong>CASH</strong></td>
                    <td>—</td>
                    <td>—</td>
                    <td>${data.ai_agent.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td>
                      <div className="weight-cell">
                        <span>{data.ai_agent.cash_weight_pct.toFixed(1)}%</span>
                        <i>
                          <b style={{ width: `${Math.min(data.ai_agent.cash_weight_pct, 100)}%`, backgroundColor: "var(--muted)" }} />
                        </i>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Tech Titans Holdings */}
          <div className="card holdings-card">
            <div className="holdings-header">
              <h3>📊 Tech Titans Holdings ({data.tech_titans.positions.length})</h3>
              <strong>NAV: ${data.tech_titans.total_nav.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
            </div>
            <div className="holdings-table-wrap">
              <table className="holdings-table">
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Shares</th>
                    <th>Open Price</th>
                    <th>Market Value</th>
                    <th>Weight</th>
                  </tr>
                </thead>
                <tbody>
                  {data.tech_titans.positions.map((pos) => (
                    <tr key={pos.ticker}>
                      <td><strong>{pos.ticker}</strong></td>
                      <td>{pos.shares.toFixed(2)}</td>
                      <td>${pos.price.toFixed(2)}</td>
                      <td>${pos.market_value.toLocaleString()}</td>
                      <td>
                        <div className="weight-cell">
                          <span>{pos.weight_pct.toFixed(1)}%</span>
                          <i>
                            <b style={{ width: `${Math.min(pos.weight_pct, 100)}%` }} />
                          </i>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {data.tech_titans.positions.length === 0 && (
                    <tr>
                      <td colSpan={5} className="table-empty">No positions held (100% Cash)</td>
                    </tr>
                  )}
                  <tr className="table-cash-row">
                    <td><strong>CASH</strong></td>
                    <td>—</td>
                    <td>—</td>
                    <td>${data.tech_titans.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td>
                      <div className="weight-cell">
                        <span>{data.tech_titans.cash_weight_pct.toFixed(1)}%</span>
                        <i>
                          <b style={{ width: `${Math.min(data.tech_titans.cash_weight_pct, 100)}%`, backgroundColor: "var(--muted)" }} />
                        </i>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 7. Transaction Log Console */}
      {data && data.transactions.length > 0 && (
        <div className="card transaction-console-card">
          <div className="console-header">Sandbox Transaction Ledger</div>
          <div className="console-body">
            {data.transactions
              .slice()
              .reverse()
              .map((tx, idx) => (
                <div key={idx} className={`console-line ${tx.action}`}>
                  <span className="console-time">[{formatTimestamp(tx.timestamp)}]</span>
                  <span className="console-portfolio">[{tx.portfolio.toUpperCase()}]</span>
                  <strong className="console-action">{tx.action.toUpperCase()}</strong>
                  <span className="console-details">
                    {tx.ticker} — {tx.shares.toFixed(2)} shares @ ${tx.price.toFixed(2)} (Value: ${tx.value.toLocaleString(undefined, { minimumFractionDigits: 2 })})
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
