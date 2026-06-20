"""Terminal and text reporting for backtest results."""

from __future__ import annotations

from backtest.models import BacktestComparison


def format_report(comparison: BacktestComparison) -> str:
    """Build a human-readable terminal report."""
    agent = comparison.agent
    benchmark = comparison.benchmark
    lines = [
        "=" * 60,
        "AI Agent Trading Office — Backtest Report",
        "=" * 60,
        f"Window: {agent.start_date.isoformat()} → {agent.end_date.isoformat()} "
        f"({comparison.months} months)",
        f"Weekly rebalances (AI): {comparison.weekly_rebalances}",
        "",
        "Capital injected (305 USD / month): "
        f"${agent.total_injected:,.2f}",
        "",
        "--- AI Agent Portfolio ---",
        f"Final NAV:     ${agent.final_nav:,.2f}",
        f"Total return:  {agent.total_return:+.2%}",
        f"Trades:        {len(agent.trades)}",
        f"Holdings:      {len(agent.final_holdings)}",
        "",
        "--- Tech Titans Benchmark ---",
        f"Final NAV:     ${benchmark.final_nav:,.2f}",
        f"Total return:  {benchmark.total_return:+.2%}",
        f"Trades:        {len(benchmark.trades)}",
        f"Holdings:      {len(benchmark.final_holdings)}",
        "",
        f"Alpha (AI − Benchmark): {comparison.alpha:+.2%}",
        "=" * 60,
    ]
    return "\n".join(lines)