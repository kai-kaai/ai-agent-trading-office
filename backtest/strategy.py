"""Fundamental scoring and weekly AI-agent rebalance rules."""

from __future__ import annotations

from datetime import date

from backtest.data_loader import StockSnapshot, TechTitansData
from backtest.portfolio import Portfolio
from core.data.fundamentals import fundamental_score

MAX_POSITIONS = 15
MONTHLY_INJECTION = 305.0
SELL_SCORE_THRESHOLD = 40.0
BUY_SCORE_THRESHOLD = 65.0


def score_universe(
    data: TechTitansData,
    month_date: date,
    extra_tickers: list[str] | None = None,
) -> list[tuple[str, float, StockSnapshot | None]]:
    """Score tickers from the benchmark month plus any held names."""
    tickers: list[str] = list(data.tickers(month_date))
    seen = set(tickers)
    for ticker in extra_tickers or []:
        upper = ticker.upper()
        if upper not in seen:
            seen.add(upper)
            tickers.append(upper)

    scored: list[tuple[str, float, StockSnapshot | None]] = []
    for ticker in tickers:
        snap = data.snapshot(ticker, month_date)
        if snap is None:
            scored.append((ticker, 45.0, None))
        else:
            scored.append((ticker, fundamental_score(snap), snap))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


def apply_weekly_strategy(
    portfolio: Portfolio,
    data: TechTitansData,
    on_date: date,
    month_date: date,
) -> None:
    """Apply weekly AI-agent trading rules from TRADING-RULES.md."""
    held_tickers = list(portfolio.shares.keys())
    scored = score_universe(data, month_date, extra_tickers=held_tickers)
    score_by_ticker = {ticker: score for ticker, score, _ in scored}

    for ticker in held_tickers:
        if score_by_ticker.get(ticker, 0.0) < SELL_SCORE_THRESHOLD:
            portfolio.sell(
                ticker,
                data,
                on_date,
                rationale=(
                    f"Weekly rebalance: score {score_by_ticker.get(ticker, 0):.0f} "
                    f"< {SELL_SCORE_THRESHOLD:.0f}"
                ),
            )

    candidates = [
        ticker
        for ticker, score, _ in scored
        if score >= BUY_SCORE_THRESHOLD and ticker not in portfolio.shares
    ]

    slots = max(0, MAX_POSITIONS - portfolio.holdings_count())
    if slots <= 0 or not candidates or portfolio.cash <= 0:
        return

    picks = candidates[:slots]
    allocation = portfolio.cash / len(picks)
    for ticker in picks:
        portfolio.buy(
            ticker,
            data,
            on_date,
            allocation,
            rationale=(
                f"Weekly rebalance: score {score_by_ticker[ticker]:.0f} "
                f">= {BUY_SCORE_THRESHOLD:.0f}"
            ),
        )