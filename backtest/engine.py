"""Backtest engine – weekly AI agent vs monthly Tech Titans benchmark."""

from __future__ import annotations

from datetime import date

from backtest.benchmark import run_tech_titans_benchmark
from backtest.dates import iter_weekly_dates
from backtest.data_loader import DEFAULT_CSV, TechTitansData
from backtest.models import BacktestComparison, BacktestResult, NavSnapshot
from backtest.portfolio import Portfolio
from backtest.strategy import MONTHLY_INJECTION, apply_weekly_strategy

DEFAULT_MONTHS = 6


class BacktestEngine:
    """Run AI-agent and benchmark simulations over a historical window."""

    def __init__(self, csv_path: str | None = None) -> None:
        path = DEFAULT_CSV if csv_path is None else csv_path
        self.data = TechTitansData(path)

    def run(
        self,
        months: int = DEFAULT_MONTHS,
        start_month: date | None = None,
        end_month: date | None = None,
    ) -> BacktestComparison:
        """Execute both simulations and return a comparison report."""
        if start_month is None or end_month is None:
            start_month, end_month = self.data.available_window(months)

        benchmark = run_tech_titans_benchmark(self.data, start_month, end_month)
        agent = self._run_agent(start_month, end_month)
        alpha = agent.total_return - benchmark.total_return

        return BacktestComparison(
            agent=agent,
            benchmark=benchmark,
            alpha=alpha,
            months=len(
                [month for month in self.data.months if start_month <= month <= end_month]
            ),
            weekly_rebalances=len(agent.nav_history),
        )

    def _run_agent(self, start_month: date, end_month: date) -> BacktestResult:
        """Simulate the AI agent with weekly rebalances."""
        portfolio = Portfolio()
        nav_history: list[NavSnapshot] = []
        total_injected = 0.0
        injected_months: set[date] = set()

        for on_date in iter_weekly_dates(start_month, end_month):
            month_date = self.data.month_for(on_date)

            if month_date not in injected_months:
                portfolio.cash += MONTHLY_INJECTION
                total_injected += MONTHLY_INJECTION
                injected_months.add(month_date)

            apply_weekly_strategy(
                portfolio,
                self.data,
                on_date,
                month_date=month_date,
            )

            nav_history.append(
                NavSnapshot(
                    date=on_date,
                    nav=portfolio.nav(self.data, on_date),
                    cash=portfolio.cash,
                    holdings_count=portfolio.holdings_count(),
                    injected_capital=total_injected,
                )
            )

        final_nav = portfolio.nav(self.data, end_month)
        total_return = (final_nav / total_injected - 1.0) if total_injected else 0.0

        return BacktestResult(
            name="AI Agent Portfolio",
            start_date=start_month,
            end_date=end_month,
            total_injected=total_injected,
            final_nav=final_nav,
            total_return=total_return,
            nav_history=nav_history,
            trades=portfolio.trades,
            final_holdings=portfolio.copy_holdings(),
        )