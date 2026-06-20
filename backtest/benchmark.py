"""Tech Titans monthly benchmark simulation."""

from __future__ import annotations

from datetime import date

from backtest.data_loader import TechTitansData
from backtest.models import BacktestResult, NavSnapshot
from backtest.portfolio import Portfolio
from backtest.strategy import MONTHLY_INJECTION


def run_tech_titans_benchmark(
    data: TechTitansData,
    start_month: date,
    end_month: date,
) -> BacktestResult:
    """Simulate Tech Titans: monthly rebalance + 305 USD injection on month start."""
    months = [month for month in data.months if start_month <= month <= end_month]
    if not months:
        raise ValueError("No benchmark months in the requested window.")

    portfolio = Portfolio()
    nav_history: list[NavSnapshot] = []
    total_injected = 0.0

    for month_date in months:
        portfolio.cash += MONTHLY_INJECTION
        total_injected += MONTHLY_INJECTION

        tickers = data.tickers(month_date)
        portfolio.rebalance_equal_weight(
            tickers,
            data,
            month_date,
            rationale=f"Tech Titans monthly rebalance ({month_date.isoformat()})",
        )

        nav_history.append(
            NavSnapshot(
                date=month_date,
                nav=portfolio.nav(data, month_date),
                cash=portfolio.cash,
                holdings_count=portfolio.holdings_count(),
                injected_capital=total_injected,
            )
        )

    final_nav = portfolio.nav(data, end_month)
    total_return = (final_nav / total_injected - 1.0) if total_injected else 0.0

    return BacktestResult(
        name="Tech Titans Benchmark",
        start_date=start_month,
        end_date=end_month,
        total_injected=total_injected,
        final_nav=final_nav,
        total_return=total_return,
        nav_history=nav_history,
        trades=portfolio.trades,
        final_holdings=portfolio.copy_holdings(),
    )