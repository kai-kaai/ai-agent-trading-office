import { useCallback, useEffect, useState } from "react";

type NavPoint = {
  date: string;
  nav: number;
  cash: number;
  holdings_count: number;
  injected_capital: number;
};

type BacktestSide = {
  name: string;
  start_date: string;
  end_date: string;
  total_injected: number;
  final_nav: number;
  total_return_pct: number;
  trade_count: number;
  final_holdings: Record<string, number>;
  nav_history: NavPoint[];
};

type BacktestResult = {
  agent: BacktestSide;
  benchmark: BacktestSide;
  alpha_pct: number;
  months: number;
  weekly_rebalances: number;
};

export function BacktestPanel() {
  const [data, setData] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (run = false) => {
    setLoading(true);
    setError(null);
    try {
      const url = run ? "/api/backtest/run" : "/api/backtest/latest";
      const response = await fetch(run ? `${url}?months=6` : url, {
        method: run ? "POST" : "GET",
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setData(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load backtest");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(false);
  }, [load]);

  const maxNav = Math.max(
    data?.agent.final_nav ?? 0,
    data?.benchmark.final_nav ?? 0,
    1,
  );

  return (
    <div className="backtest-panel">
      <div className="backtest-header">
        <div>
          <h2>Backtest — AI Agent vs Tech Titans</h2>
          <p className="backtest-sub">
            Phase 1 engine · 305 USD/month · 6-month window
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => void load(true)}
          disabled={loading}
        >
          {loading ? "Running…" : "Run Backtest"}
        </button>
      </div>

      {error && <p className="backtest-error">{error}</p>}

      {data && (
        <>
          <div className="backtest-metrics">
            <div className="metric-card">
              <span className="metric-label">AI Agent Return</span>
              <span
                className={`metric-value ${
                  data.agent.total_return_pct >= 0 ? "positive" : "negative"
                }`}
              >
                {data.agent.total_return_pct >= 0 ? "+" : ""}
                {data.agent.total_return_pct.toFixed(2)}%
              </span>
              <span className="metric-sub">
                NAV ${data.agent.final_nav.toLocaleString()}
              </span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Tech Titans Return</span>
              <span
                className={`metric-value ${
                  data.benchmark.total_return_pct >= 0 ? "positive" : "negative"
                }`}
              >
                {data.benchmark.total_return_pct >= 0 ? "+" : ""}
                {data.benchmark.total_return_pct.toFixed(2)}%
              </span>
              <span className="metric-sub">
                NAV ${data.benchmark.final_nav.toLocaleString()}
              </span>
            </div>
            <div className="metric-card accent">
              <span className="metric-label">Alpha</span>
              <span
                className={`metric-value ${
                  data.alpha_pct >= 0 ? "positive" : "negative"
                }`}
              >
                {data.alpha_pct >= 0 ? "+" : ""}
                {data.alpha_pct.toFixed(2)}%
              </span>
              <span className="metric-sub">
                {data.months} months · {data.weekly_rebalances} weekly rebalances
              </span>
            </div>
          </div>

          <div className="backtest-chart">
            <h3>NAV Comparison</h3>
            <div className="bar-chart">
              <div className="bar-row">
                <span className="bar-label">AI Agent</span>
                <div className="bar-track">
                  <div
                    className="bar-fill agent"
                    style={{ width: `${(data.agent.final_nav / maxNav) * 100}%` }}
                  />
                </div>
                <span className="bar-value">${data.agent.final_nav.toFixed(0)}</span>
              </div>
              <div className="bar-row">
                <span className="bar-label">Tech Titans</span>
                <div className="bar-track">
                  <div
                    className="bar-fill benchmark"
                    style={{
                      width: `${(data.benchmark.final_nav / maxNav) * 100}%`,
                    }}
                  />
                </div>
                <span className="bar-value">
                  ${data.benchmark.final_nav.toFixed(0)}
                </span>
              </div>
            </div>
            <p className="chart-note">
              Capital injected: ${data.agent.total_injected.toLocaleString()} (
              {data.agent.start_date} → {data.agent.end_date})
            </p>
          </div>

          <div className="backtest-details">
            <div className="detail-col">
              <h3>AI Holdings ({Object.keys(data.agent.final_holdings).length})</h3>
              <ul>
                {Object.entries(data.agent.final_holdings).map(([ticker, shares]) => (
                  <li key={ticker}>
                    <strong>{ticker}</strong> — {shares.toFixed(2)} shares
                  </li>
                ))}
              </ul>
              <p className="trade-count">{data.agent.trade_count} trades executed</p>
            </div>
            <div className="detail-col">
              <h3>
                Benchmark Holdings ({Object.keys(data.benchmark.final_holdings).length})
              </h3>
              <ul>
                {Object.entries(data.benchmark.final_holdings).map(
                  ([ticker, shares]) => (
                    <li key={ticker}>
                      <strong>{ticker}</strong> — {shares.toFixed(2)} shares
                    </li>
                  ),
                )}
              </ul>
              <p className="trade-count">
                {data.benchmark.trade_count} trades executed
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}