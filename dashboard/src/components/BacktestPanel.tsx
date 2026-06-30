import { useCallback, useEffect, useState } from "react";
import type { BacktestResult, PortfolioSnapshot } from "../types";
import { PerformanceChart } from "./PerformanceChart";

export function BacktestPanel() {
  const [data, setData] = useState<BacktestResult | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [portfolioError, setPortfolioError] = useState<string | null>(null);

  const load = useCallback(async (run = false) => {
    setLoading(true);
    setError(null);
    setPortfolioError(null);
    try {
      const url = run ? "/api/backtest/run" : "/api/backtest/latest";
      const response = await fetch(run ? `${url}?months=6` : url, { method: run ? "POST" : "GET" });
      if (!response.ok) throw new Error(`Backtest HTTP ${response.status}`);
      const nextData = (await response.json()) as BacktestResult;
      setData(nextData);
      window.dispatchEvent(new CustomEvent("backtest-updated", { detail: nextData }));

      try {
        const portfolioResponse = await fetch("/api/portfolio/latest");
        if (!portfolioResponse.ok) throw new Error(`Portfolio HTTP ${portfolioResponse.status}`);
        setPortfolio((await portfolioResponse.json()) as PortfolioSnapshot);
      } catch (portfolioErr) {
        setPortfolio(null);
        setPortfolioError(
          portfolioErr instanceof Error ? portfolioErr.message : "Failed to load portfolio",
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load backtest");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(false);
  }, [load]);

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
      {portfolioError && !error && <p className="backtest-warning">{portfolioError}</p>}

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

          <PerformanceChart data={data} />
          <p className="chart-note">
            Capital injected: ${data.agent.total_injected.toLocaleString()} ({data.agent.start_date} → {data.agent.end_date}).
            Both series use weekly mark-to-market snapshots; Tech Titans rebalances monthly, AI Agent weekly.
          </p>

          {portfolio && (
            <section className="portfolio-card">
              <div className="portfolio-heading">
                <div>
                  <span className="eyebrow">SIMULATED PORTFOLIO</span>
                  <h3>Current holdings</h3>
                  <p>As of {portfolio.as_of} · priced from Tech Titans CSV proxy</p>
                </div>
                <div className="portfolio-total">
                  <span>Total NAV</span>
                  <strong>${portfolio.total_nav.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
                </div>
              </div>
              <div className="portfolio-summary">
                <div><span>Positions</span><strong>{portfolio.position_count}</strong></div>
                <div><span>Cash</span><strong>${portfolio.cash.toFixed(2)}</strong></div>
                <div><span>Cash weight</span><strong>{portfolio.cash_weight_pct.toFixed(1)}%</strong></div>
                <div><span>Return</span><strong className={portfolio.total_return_pct >= 0 ? "positive" : "negative"}>{portfolio.total_return_pct >= 0 ? "+" : ""}{portfolio.total_return_pct.toFixed(2)}%</strong></div>
              </div>
              <div className="holdings-table-wrap">
                <table className="holdings-table">
                  <thead><tr><th>Ticker</th><th>Shares</th><th>Proxy price</th><th>Market value</th><th>Weight</th></tr></thead>
                  <tbody>
                    {portfolio.positions.map((position) => (
                      <tr key={position.ticker}>
                        <td><strong>{position.ticker}</strong></td>
                        <td>{position.shares.toFixed(2)}</td>
                        <td>${position.price.toFixed(2)}</td>
                        <td>${position.market_value.toFixed(2)}</td>
                        <td>
                          <div className="weight-cell"><span>{position.weight_pct.toFixed(1)}%</span><i><b style={{ width: `${Math.min(position.weight_pct, 100)}%` }} /></i></div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

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
              <h3>Benchmark Holdings ({Object.keys(data.benchmark.final_holdings).length})</h3>
              <ul>
                {Object.entries(data.benchmark.final_holdings).map(([ticker, shares]) => (
                  <li key={ticker}>
                    <strong>{ticker}</strong> — {shares.toFixed(2)} shares
                  </li>
                ))}
              </ul>
              <p className="trade-count">{data.benchmark.trade_count} trades executed</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}