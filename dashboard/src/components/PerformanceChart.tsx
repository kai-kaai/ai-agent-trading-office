import type { BacktestResult, NavPoint } from "../types";

interface Props {
  data: BacktestResult;
}

const WIDTH = 920;
const HEIGHT = 300;
const PAD = { top: 24, right: 28, bottom: 42, left: 58 };

function pointReturn(point: NavPoint) {
  return point.injected_capital > 0 ? (point.nav / point.injected_capital - 1) * 100 : 0;
}

export function PerformanceChart({ data }: Props) {
  const all = [...data.agent.nav_history, ...data.benchmark.nav_history];
  if (all.length < 2) return null;

  const times = all.map((point) => new Date(point.date).getTime());
  const returns = all.map(pointReturn);
  const minTime = Math.min(...times);
  const maxTime = Math.max(...times);
  const rawMin = Math.min(...returns, 0);
  const rawMax = Math.max(...returns, 0);
  const margin = Math.max((rawMax - rawMin) * 0.15, 0.5);
  const minReturn = rawMin - margin;
  const maxReturn = rawMax + margin;
  const innerWidth = WIDTH - PAD.left - PAD.right;
  const innerHeight = HEIGHT - PAD.top - PAD.bottom;

  const x = (point: NavPoint) =>
    PAD.left + ((new Date(point.date).getTime() - minTime) / Math.max(maxTime - minTime, 1)) * innerWidth;
  const y = (value: number) =>
    PAD.top + ((maxReturn - value) / Math.max(maxReturn - minReturn, 1)) * innerHeight;
  const path = (points: NavPoint[]) =>
    points.map((point, index) => `${index === 0 ? "M" : "L"} ${x(point).toFixed(1)} ${y(pointReturn(point)).toFixed(1)}`).join(" ");
  const grid = Array.from({ length: 5 }, (_, index) => {
    const value = maxReturn - ((maxReturn - minReturn) * index) / 4;
    return { value, y: y(value) };
  });

  return (
    <div className="performance-chart" aria-label="Portfolio return comparison chart">
      <div className="chart-title-row">
        <div>
          <h3>Performance over time</h3>
          <p>Weekly return on contributed capital (benchmark rebalances monthly)</p>
        </div>
        <div className="chart-legend">
          <span><i className="legend-line agent" />AI Agent</span>
          <span><i className="legend-line benchmark" />Tech Titans</span>
        </div>
      </div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img">
        {grid.map((line) => (
          <g key={line.value}>
            <line className="chart-grid" x1={PAD.left} x2={WIDTH - PAD.right} y1={line.y} y2={line.y} />
            <text className="chart-axis-label" x={PAD.left - 10} y={line.y + 4} textAnchor="end">
              {line.value.toFixed(1)}%
            </text>
          </g>
        ))}
        <line className="chart-zero" x1={PAD.left} x2={WIDTH - PAD.right} y1={y(0)} y2={y(0)} />
        <path className="chart-series benchmark" d={path(data.benchmark.nav_history)} />
        <path className="chart-series agent" d={path(data.agent.nav_history)} />
        <text className="chart-axis-label" x={PAD.left} y={HEIGHT - 12}>{data.agent.start_date}</text>
        <text className="chart-axis-label" x={WIDTH - PAD.right} y={HEIGHT - 12} textAnchor="end">{data.agent.end_date}</text>
      </svg>
    </div>
  );
}
