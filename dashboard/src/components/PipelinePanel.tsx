import { useState, useEffect, useCallback } from "react";

interface CouncilVote {
  member: string;
  decision: string;
  rationale: string;
  veto: boolean;
}

interface CouncilVerdict {
  votes: CouncilVote[];
  approval_count: number;
  passed: boolean;
  vetoed: boolean;
  summary: string;
}

interface TradeSetup {
  ticker: string;
  action: string;
  grade: string;
  score: number;
  council: CouncilVerdict;
  sector: string | null;
  sector_strength: number | null;
  structure_notes: string[];
  news_sentiment: number | null;
  metadata: {
    sector_label?: string;
    trend?: string;
    top_headline?: string;
  };
}

interface ShieldDecision {
  verdict: string;
  risk_reward: number | null;
  overlap_warnings: string[];
  reasons: string[];
}

interface SizedOrder {
  ticker: string;
  action: string;
  shares: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  risk_pct: number;
  max_loss_usd: number;
  volatility_regime: string;
}

interface SimulationStep {
  description: string;
  price: number;
  state: string;
  trailing_stop: number | null;
  take_profit: number | null;
  stop_loss: number | null;
  events: string[];
  unrealized_pnl_pct: number | null;
}

interface TradeAutopsy {
  trade_id: string;
  ticker: string;
  outcome: string;
  lessons: string[];
  mistakes: string[];
  strengths: string[];
  entry_price: number;
  exit_price: number;
  pnl_pct: number;
  r_multiple: number;
}

interface StrategyCandidate {
  strategy_id: string;
  name: string;
  hypothesis: string;
  stage: string;
  backtest_metrics: Record<string, number>;
}

interface SimulationResult {
  halted: boolean;
  stage_reached: string;
  halt_reason: string | null;
  setup: TradeSetup | null;
  shield: ShieldDecision | null;
  sized_order: SizedOrder | null;
  events: string[];
  simulation_steps: SimulationStep[];
  autopsy: TradeAutopsy | null;
  strategy_candidate: {
    current: StrategyCandidate;
    history: StrategyCandidate[];
  } | null;
}

export function PipelinePanel() {
  const [ticker, setTicker] = useState("WDAY");
  const [action, setAction] = useState<"buy" | "sell">("buy");
  const [navUsd, setNavUsd] = useState(10000);
  const [riskReward, setRiskReward] = useState(2.0);
  const [volatilityRegime, setVolatilityRegime] = useState("normal");
  const [simulateOutcome, setSimulateOutcome] = useState("win");
  const [scoreOverrideEnabled, setScoreOverrideEnabled] = useState(true);
  const [scoreOverrideVal, setScoreOverrideVal] = useState(85.0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);

  // Simulation controls
  const [stepIndex, setStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1200); // ms delay

  const runSimulation = useCallback(async () => {
    setLoading(true);
    setError(null);
    setIsPlaying(false);
    setStepIndex(0);
    try {
      const response = await fetch("/api/pipeline/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker,
          action,
          nav_usd: navUsd,
          risk_reward: riskReward,
          volatility_regime: volatilityRegime,
          simulate_outcome: simulateOutcome,
          score_override: scoreOverrideEnabled ? scoreOverrideVal : null,
        }),
      });

      if (!response.ok) {
        throw new Error(`Simulation failed: ${response.statusText}`);
      }

      const data = (await response.json()) as SimulationResult;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [ticker, action, navUsd, riskReward, volatilityRegime, simulateOutcome, scoreOverrideEnabled, scoreOverrideVal]);

  // Autoplay handler
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlaying && result && result.simulation_steps.length > 0) {
      timer = setTimeout(() => {
        setStepIndex((prev) => {
          if (prev >= result.simulation_steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, speed);
    }
    return () => clearTimeout(timer);
  }, [isPlaying, result, speed]);

  const currentStep = result?.simulation_steps[stepIndex] || null;

  return (
    <div className="pipeline-panel">
      {/* 1. Header & Controls Form */}
      <div className="pipeline-header">
        <div>
          <h2>5-Module Trading Pipeline</h2>
          <p className="panel-sub">
            AI Council Decisions ➔ Risk Filters ➔ Sizing ➔ Active Position Tracking ➔ Autopsy review
          </p>
        </div>
      </div>

      <div className="pipeline-config-grid">
        <div className="form-group">
          <label>Ticker Symbol</label>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="AAPL"
          />
        </div>

        <div className="form-group">
          <label>Action</label>
          <select value={action} onChange={(e) => setAction(e.target.value as "buy" | "sell")}>
            <option value="buy">BUY (Long)</option>
            <option value="sell">SELL (Short)</option>
          </select>
        </div>

        <div className="form-group">
          <label>Portfolio NAV (USD)</label>
          <input
            type="number"
            value={navUsd}
            onChange={(e) => setNavUsd(Number(e.target.value))}
            min="100"
          />
        </div>

        <div className="form-group">
          <label>Target RRR</label>
          <input
            type="number"
            value={riskReward}
            onChange={(e) => setRiskReward(Number(e.target.value))}
            step="0.1"
            min="0.5"
          />
        </div>

        <div className="form-group">
          <label>Volatility Regime</label>
          <select value={volatilityRegime} onChange={(e) => setVolatilityRegime(e.target.value)}>
            <option value="low">Low Volatility (1.0x size)</option>
            <option value="normal">Normal Volatility (1.0x size)</option>
            <option value="high">High Volatility (0.5x size)</option>
          </select>
        </div>

        <div className="form-group">
          <label>Simulate Exit</label>
          <select value={simulateOutcome} onChange={(e) => setSimulateOutcome(e.target.value)}>
            <option value="win">Win (Hits Take Profit)</option>
            <option value="loss">Loss (Hits Hard Stop)</option>
            <option value="trailing_exit">Trailing Stop Hit (Locked Profit)</option>
          </select>
        </div>

        <div className="form-group score-override-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={scoreOverrideEnabled}
              onChange={(e) => setScoreOverrideEnabled(e.target.checked)}
            />
            Composite Score Override
          </label>
          <input
            type="number"
            value={scoreOverrideVal}
            onChange={(e) => setScoreOverrideVal(Number(e.target.value))}
            disabled={!scoreOverrideEnabled}
            min="0"
            max="100"
          />
        </div>

        <div className="form-actions">
          <button className="btn-primary btn-run-pipe" onClick={runSimulation} disabled={loading}>
            {loading ? "Processing Pipeline…" : "Run Pipeline & Simulate"}
          </button>
        </div>
      </div>

      {error && <div className="pipeline-error">{error}</div>}

      {/* 2. Visual Pipeline Flow */}
      {result && (
        <div className="pipeline-workspace">
          {/* Stage Progress Indicator */}
          <div className="pipeline-progress-bar">
            {(["Brain", "Shield", "CFO", "Watchman", "Auditor"] as const).map((stage, idx) => {
              const stages = ["brain", "shield", "cfo", "watchman", "auditor"];
              const reachedIdx = stages.indexOf(result.stage_reached);
              const isHalted = result.halted;
              const isPast = idx < reachedIdx;
              const isCurrent = idx === reachedIdx;

              let statusClass = "upcoming";
              if (isPast) {
                statusClass = "completed";
              } else if (isCurrent) {
                statusClass = isHalted ? "halted" : "completed";
              }

              return (
                <div key={stage} className={`progress-step ${statusClass}`}>
                  <span className="step-num">{idx + 1}</span>
                  <span className="step-label">{stage}</span>
                </div>
              );
            })}
          </div>

          {result.halted && (
            <div className="pipeline-halt-banner">
              <strong>Pipeline Halted at {result.stage_reached.toUpperCase()}</strong>: {result.halt_reason}
            </div>
          )}

          {/* Module 1 & 2 layout: Setup and Risk Check */}
          <div className="modules-row">
            {/* The Brain Card */}
            {result.setup && (
              <div className="card brain-card">
                <div className="card-header">
                  <h3>🧠 Module 1: The Brain (AI Council)</h3>
                  <span className={`badge grade-${result.setup.grade.toLowerCase().replace("+", "-plus")}`}>
                    {result.setup.grade} (Score: {result.setup.score.toFixed(1)})
                  </span>
                </div>

                <div className="scanners-grid">
                  <div className="scan-item">
                    <span className="scan-label">Fundamental</span>
                    <strong className="scan-val">{result.setup.grade === "C" ? "Weak" : "Solid"}</strong>
                  </div>
                  <div className="scan-item">
                    <span className="scan-label">Sector vs QQQ</span>
                    <strong className="scan-val">{(result.setup.sector_strength || 50).toFixed(0)}%</strong>
                  </div>
                  <div className="scan-item">
                    <span className="scan-label">Structure</span>
                    <strong className="scan-val">{result.setup.metadata.trend || "Uptrend"}</strong>
                  </div>
                  <div className="scan-item">
                    <span className="scan-label">News Sentiment</span>
                    <strong className="scan-val">
                      {result.setup.news_sentiment ? `${(result.setup.news_sentiment * 100).toFixed(0)}%` : "Neutral"}
                    </strong>
                  </div>
                </div>

                <div className="council-votes">
                  <h4>AI Council Deliberation</h4>
                  <div className="votes-grid">
                    {result.setup.council.votes.map((vote) => (
                      <div
                        key={vote.member}
                        className={`vote-card ${vote.decision} ${vote.veto ? "vetoed" : ""}`}
                      >
                        <div className="vote-member-header">
                          <strong>{vote.member === "risk_chair" ? "Risk Chair ⚖️" : vote.member === "bull" ? "Bull 🐂" : "Bear 🐻"}</strong>
                          <span className={`vote-badge ${vote.decision}`}>
                            {vote.decision.toUpperCase()}
                          </span>
                        </div>
                        <p className="vote-rationale">"{vote.rationale}"</p>
                        {vote.veto && <span className="veto-tag">VETO TRIGGERED</span>}
                      </div>
                    ))}
                  </div>
                  <div className="council-summary">
                    <strong>Verdict:</strong> {result.setup.council.summary}
                  </div>
                </div>
              </div>
            )}

            {/* The Shield Card */}
            {result.shield && (
              <div className={`card shield-card ${result.shield.verdict}`}>
                <div className="card-header">
                  <h3>🛡️ Module 2: The Shield</h3>
                  <span className={`badge shield-${result.shield.verdict}`}>
                    {result.shield.verdict.toUpperCase()}
                  </span>
                </div>
                <div className="shield-metrics">
                  <div className="metric-row">
                    <span>Target Risk-Reward Ratio (RRR)</span>
                    <strong>{result.shield.risk_reward ? result.shield.risk_reward.toFixed(1) : "N/A"}</strong>
                  </div>
                  <div className="metric-row">
                    <span>Min RRR Gate</span>
                    <strong>&gt;= 2.0</strong>
                  </div>
                  <div className="metric-row">
                    <span>Sector Concentration</span>
                    <strong>Passed (&lt; 4 holdings)</strong>
                  </div>
                </div>

                <div className="shield-reasons">
                  <h4>Shield Evaluation Logs</h4>
                  <ul>
                    {result.shield.reasons.map((reason, i) => (
                      <li key={i}>{reason}</li>
                    ))}
                    {result.shield.overlap_warnings.map((warn, i) => (
                      <li key={i} className="warning-item">⚠️ {warn}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Module 3 & 4 Layout: Sizing and Active Tracking */}
          {!result.halted && result.sized_order && (
            <div className="modules-row">
              {/* The CFO Card */}
              <div className="card cfo-card">
                <div className="card-header">
                  <h3>💰 Module 3: The CFO</h3>
                  <span className="badge cfo-regime">{volatilityRegime.toUpperCase()} VOL</span>
                </div>
                <div className="cfo-sizing-details">
                  <div className="cfo-main-size">
                    <span>Simulated Size</span>
                    <strong>{result.sized_order.shares.toFixed(2)} Shares</strong>
                  </div>
                  <div className="sizing-table">
                    <div className="table-row">
                      <span>Total NAV</span>
                      <span>${navUsd.toLocaleString()}</span>
                    </div>
                    <div className="table-row">
                      <span>NAV Risk budget %</span>
                      <span>{(result.sized_order.risk_pct * 100).toFixed(3)}%</span>
                    </div>
                    <div className="table-row">
                      <span>Max Trade Loss</span>
                      <span>${result.sized_order.max_loss_usd.toFixed(2)}</span>
                    </div>
                    <div className="table-row">
                      <span>Volatility Regime</span>
                      <span>{result.sized_order.volatility_regime}</span>
                    </div>
                  </div>
                  <div className="levels-table">
                    <div className="level-col">
                      <span className="lbl stop">STOP LOSS</span>
                      <strong className="val">${result.sized_order.stop_loss.toFixed(2)}</strong>
                    </div>
                    <div className="level-col">
                      <span className="lbl entry">ENTRY PRICE</span>
                      <strong className="val">${result.sized_order.entry_price.toFixed(2)}</strong>
                    </div>
                    <div className="level-col">
                      <span className="lbl tp">TAKE PROFIT</span>
                      <strong className="val">${result.sized_order.take_profit.toFixed(2)}</strong>
                    </div>
                  </div>
                </div>
              </div>

              {/* The Watchman Card (Simulated interactive area) */}
              <div className="card watchman-card">
                <div className="card-header">
                  <h3>👀 Module 4: The Watchman</h3>
                  {currentStep && (
                    <span className={`badge state-${currentStep.state}`}>
                      {currentStep.state.toUpperCase()}
                    </span>
                  )}
                </div>

                {/* Simulation Controls */}
                <div className="sim-console-controls">
                  <button
                    className="btn-sim btn-prev"
                    onClick={() => setStepIndex((prev) => Math.max(0, prev - 1))}
                    disabled={stepIndex === 0}
                  >
                    ◀
                  </button>
                  <button
                    className={`btn-sim btn-play ${isPlaying ? "playing" : ""}`}
                    onClick={() => setIsPlaying(!isPlaying)}
                  >
                    {isPlaying ? "Pause" : "Play Price Path"}
                  </button>
                  <button
                    className="btn-sim btn-next"
                    onClick={() =>
                      setStepIndex((prev) =>
                        Math.min(result.simulation_steps.length - 1, prev + 1)
                      )
                    }
                    disabled={stepIndex === result.simulation_steps.length - 1}
                  >
                    ▶
                  </button>
                  <div className="speed-control">
                    <span>Speed</span>
                    <input
                      type="range"
                      min="500"
                      max="2000"
                      step="100"
                      value={speed}
                      onChange={(e) => setSpeed(Number(e.target.value))}
                    />
                  </div>
                </div>

                {/* Simulation Visualiser */}
                {currentStep && (
                  <div className="sim-viewer">
                    <div className="sim-timeline-slider">
                      <input
                        type="range"
                        min="0"
                        max={result.simulation_steps.length - 1}
                        value={stepIndex}
                        onChange={(e) => setStepIndex(Number(e.target.value))}
                      />
                      <span className="timeline-pos">
                        Step {stepIndex + 1} / {result.simulation_steps.length}
                      </span>
                    </div>

                    <div className="price-status-card">
                      <div className="status-metric">
                        <span className="lbl">Current Price</span>
                        <strong className="val">${currentStep.price.toFixed(2)}</strong>
                      </div>
                      <div className="status-metric">
                        <span className="lbl">Stop/Trailing level</span>
                        <strong className="val">
                          ${(currentStep.trailing_stop || currentStep.stop_loss || 0).toFixed(2)}
                        </strong>
                      </div>
                      <div className="status-metric">
                        <span className="lbl">Unrealized PnL</span>
                        <strong
                          className={`val ${
                            (currentStep.unrealized_pnl_pct || 0) >= 0 ? "positive" : "negative"
                          }`}
                        >
                          {currentStep.unrealized_pnl_pct !== null
                            ? `${currentStep.unrealized_pnl_pct >= 0 ? "+" : ""}${(
                                currentStep.unrealized_pnl_pct * 100
                              ).toFixed(2)}%`
                            : "0.00%"}
                        </strong>
                      </div>
                    </div>

                    {/* Progress Gauge */}
                    <div className="unrealized-bar-container">
                      <div className="bar-labels">
                        <span>Stop</span>
                        <span>Entry</span>
                        <span>Take Profit</span>
                      </div>
                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{
                            width: `${Math.max(
                              0,
                              Math.min(
                                100,
                                ((currentStep.price - (result.sized_order?.stop_loss || 0)) /
                                  ((result.sized_order?.take_profit || 1) -
                                    (result.sized_order?.stop_loss || 0))) *
                                  100
                              )
                            )}%`,
                          }}
                        />
                        <div
                          className="marker entry-marker"
                          style={{
                            left: `${
                              (((result.sized_order?.entry_price || 0) -
                                (result.sized_order?.stop_loss || 0)) /
                                ((result.sized_order?.take_profit || 1) -
                                  (result.sized_order?.stop_loss || 0))) *
                              100
                            }%`,
                          }}
                        />
                      </div>
                    </div>

                    {/* Watchman logs */}
                    <div className="watchman-terminal">
                      <div className="terminal-header">Watchman Events Log</div>
                      <div className="terminal-body">
                        {currentStep.events.map((ev, i) => (
                          <div key={i} className="terminal-line">
                            &gt; {ev}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Module 5: Auditor (Revealed when simulation is CLOSED) */}
          {!result.halted && result.autopsy && currentStep?.state === "closed" && (
            <div className="modules-row auditor-row">
              {/* Autopsy Card */}
              <div className="card autopsy-card">
                <div className="card-header">
                  <h3>⚖️ Module 5: The Auditor (Trade Autopsy)</h3>
                  <span className={`badge autopsy-${result.autopsy.outcome}`}>
                    {result.autopsy.outcome.toUpperCase()} ({(result.autopsy.pnl_pct * 100).toFixed(2)}%)
                  </span>
                </div>
                <div className="autopsy-summary-metrics">
                  <div className="metric">
                    <span>Entry Price</span>
                    <strong>${result.autopsy.entry_price.toFixed(2)}</strong>
                  </div>
                  <div className="metric">
                    <span>Exit Price</span>
                    <strong>${result.autopsy.exit_price.toFixed(2)}</strong>
                  </div>
                  <div className="metric">
                    <span>R Multiple</span>
                    <strong className={result.autopsy.r_multiple >= 0 ? "positive" : "negative"}>
                      {result.autopsy.r_multiple >= 0 ? "+" : ""}
                      {result.autopsy.r_multiple.toFixed(2)}R
                    </strong>
                  </div>
                </div>

                <div className="autopsy-lessons-grid">
                  <div className="lesson-col strengths">
                    <h4>Strengths</h4>
                    <ul>
                      {result.autopsy.strengths.map((str, i) => (
                        <li key={i}>✓ {str}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="lesson-col mistakes">
                    <h4>Mistakes</h4>
                    <ul>
                      {result.autopsy.mistakes.map((mis, i) => (
                        <li key={i}>✗ {mis}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="lesson-col lessons">
                    <h4>Lessons Learned</h4>
                    <ul>
                      {result.autopsy.lessons.map((les, i) => (
                        <li key={i}>➔ {les}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Strategy Candidate Card */}
              {result.strategy_candidate && (
                <div className="card strategy-card">
                  <div className="card-header">
                    <h3>💡 Strategy Promotion Loop</h3>
                    <span className="badge candidate-stage">
                      {result.strategy_candidate.current.stage.toUpperCase()}
                    </span>
                  </div>

                  <div className="strategy-hypothesis">
                    <strong>Hypothesis:</strong>
                    <p>"{result.strategy_candidate.current.hypothesis}"</p>
                  </div>

                  {/* Visual Promotion Line */}
                  <div className="promotion-tracker">
                    {(["candidate", "backtest", "sandbox", "live"] as const).map((stage, idx) => {
                      const stages = ["candidate", "backtest", "sandbox", "live"];
                      const currentIdx = stages.indexOf(result.strategy_candidate!.current.stage);
                      const activeClass = idx <= currentIdx ? "active" : "";

                      return (
                        <div key={stage} className={`promo-step ${activeClass}`}>
                          <span className="promo-label">{stage}</span>
                        </div>
                      );
                    })}
                  </div>

                  {result.strategy_candidate.current.backtest_metrics && (
                    <div className="candidate-metrics">
                      <h4>Backtest Verification Results</h4>
                      <div className="metrics-row">
                        <div className="m-item">
                          <span>Alpha</span>
                          <strong>
                            +{((result.strategy_candidate.current.backtest_metrics.alpha || 0) * 100).toFixed(1)}%
                          </strong>
                        </div>
                        <div className="m-item">
                          <span>Total Return</span>
                          <strong>
                            +{((result.strategy_candidate.current.backtest_metrics.total_return || 0) * 100).toFixed(1)}%
                          </strong>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
