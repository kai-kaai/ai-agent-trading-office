"""Build MeetingContext from backtest results and live data feeds."""

from __future__ import annotations

from datetime import date
from typing import Any

from backtest.context import benchmark_holdings_for, build_context_extra, get_cached_comparison, run_and_cache
from backtest.data_loader import TechTitansData
from core.data.fundamentals import get_fundamental_service
from core.data.market_data import get_market_data_service
from core.models import MeetingContext, PortfolioPosition


def _compute_drawdown(nav_history: list[Any]) -> float:
    """Peak-to-current drawdown from NAV snapshots."""
    if not nav_history:
        return 0.0
    navs = [snap.nav for snap in nav_history]
    peak = max(navs)
    current = navs[-1]
    if peak <= 0:
        return 0.0
    return max(0.0, (peak - current) / peak)


def _sector_label(raw_sector: str | None) -> str:
    if not raw_sector:
        return "technology"
    return raw_sector.replace("Information Technology", "technology").lower()


def build_meeting_context(meeting_date: date | None = None) -> MeetingContext:
    """Create a meeting context using backtest portfolio and live market data."""
    meeting_date = meeting_date or date.today()
    comparison = get_cached_comparison() or run_and_cache()
    data = TechTitansData()
    fundamentals = get_fundamental_service()
    market = get_market_data_service()
    month_date = data.month_for(meeting_date)
    benchmark_holdings = data.tickers(month_date)

    try:
        from modules.paper_portfolio import PaperPortfolioManager
        mgr = PaperPortfolioManager()
        portfolio_data = mgr.data["ai_agent"]
        holdings = portfolio_data.get("holdings", {})
        cash_balance = portfolio_data.get("cash", 10000.0)
    except Exception:
        holdings = comparison.agent.final_holdings
        latest_snap = comparison.agent.nav_history[-1] if comparison.agent.nav_history else None
        cash_balance = latest_snap.cash if latest_snap else 0.0

    portfolio: list[PortfolioPosition] = []
    live_prices: dict[str, float] = {}
    for ticker, shares in holdings.items():
        snap = fundamentals.snapshot(ticker, meeting_date)
        csv_price = data.price(ticker, meeting_date)
        live_price = market.get_price(ticker)
        if live_price is not None:
            live_prices[ticker] = live_price
            current_price = live_price
        else:
            current_price = csv_price
        avg_cost = current_price

        portfolio.append(
            PortfolioPosition(
                ticker=ticker,
                shares=shares,
                avg_cost=avg_cost,
                sector=_sector_label(snap.sector if snap else None),
                current_price=current_price,
            )
        )

    total_value = sum(position.market_value for position in portfolio) + cash_balance
    portfolio_weights = {
        position.ticker: (
            position.market_value / total_value if total_value > 0 else 0.0
        )
        for position in portfolio
    }

    held = set(holdings.keys())
    watchlist = [ticker for ticker in benchmark_holdings if ticker not in held][:8]

    extra = build_context_extra()
    extra.update(
        {
            "current_drawdown": _compute_drawdown(comparison.agent.nav_history),
            "portfolio_weights": {
                ticker: round(weight, 4) for ticker, weight in portfolio_weights.items()
            },
            "backtest_holdings": holdings,
            "backtest_final_nav": comparison.agent.final_nav,
            "market_condition": market.get_market_condition(
                list(holdings.keys()) or benchmark_holdings[:8]
            ),
            "sector_rotation": "technology",
            "live_prices": live_prices,
            "data_sources": {
                "fundamentals": "tech_titans_csv",
                "market": "yfinance",
                "news": "yfinance_news",
                "risk": "backtest_engine",
                "portfolio_pricing": "tech_titans_csv",
            },
        }
    )

    return MeetingContext(
        meeting_date=meeting_date,
        portfolio=portfolio,
        cash_balance=cash_balance,
        watchlist=watchlist,
        benchmark_holdings=benchmark_holdings,
        is_first_trading_day_of_month=meeting_date.day <= 7,
        extra=extra,
    )