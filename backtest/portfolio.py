"""Simulated portfolio with cash and share positions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from backtest.data_loader import TechTitansData
from backtest.models import TradeRecord


@dataclass
class Portfolio:
    """Mutable portfolio used by the backtest engine."""

    cash: float = 0.0
    shares: dict[str, float] = field(default_factory=dict)
    trades: list[TradeRecord] = field(default_factory=list)

    def nav(self, data: TechTitansData, on_date: date) -> float:
        """Net asset value using market-cap price proxies."""
        positions_value = sum(
            qty * data.price(ticker, on_date) for ticker, qty in self.shares.items()
        )
        return self.cash + positions_value

    def holdings_count(self) -> int:
        """Number of open positions with non-zero shares."""
        return sum(1 for qty in self.shares.values() if qty > 0)

    def sell_all(
        self,
        data: TechTitansData,
        on_date: date,
        rationale: str = "Liquidate position",
    ) -> float:
        """Sell every holding and return total sale proceeds."""
        proceeds = 0.0
        for ticker in list(self.shares.keys()):
            proceeds += self.sell(ticker, data, on_date, rationale=rationale)
        return proceeds

    def sell(
        self,
        ticker: str,
        data: TechTitansData,
        on_date: date,
        shares: float | None = None,
        rationale: str = "",
    ) -> float:
        """Sell shares and credit cash."""
        ticker = ticker.upper()
        held = self.shares.get(ticker, 0.0)
        if held <= 0:
            return 0.0

        qty = held if shares is None else min(shares, held)
        price = data.price(ticker, on_date)
        value = qty * price
        self.shares[ticker] = held - qty
        if self.shares[ticker] <= 1e-9:
            del self.shares[ticker]
        self.cash += value
        self.trades.append(
            TradeRecord(
                date=on_date,
                ticker=ticker,
                action="sell",
                shares=qty,
                price=price,
                value=value,
                rationale=rationale,
            )
        )
        return value

    def buy(
        self,
        ticker: str,
        data: TechTitansData,
        on_date: date,
        target_value: float,
        rationale: str = "",
    ) -> float:
        """Buy up to ``target_value`` worth of shares using available cash."""
        ticker = ticker.upper()
        if target_value <= 0 or self.cash <= 0:
            return 0.0

        spend = min(target_value, self.cash)
        price = data.price(ticker, on_date)
        qty = spend / price
        self.shares[ticker] = self.shares.get(ticker, 0.0) + qty
        self.cash -= spend
        self.trades.append(
            TradeRecord(
                date=on_date,
                ticker=ticker,
                action="buy",
                shares=qty,
                price=price,
                value=spend,
                rationale=rationale,
            )
        )
        return spend

    def rebalance_equal_weight(
        self,
        tickers: list[str],
        data: TechTitansData,
        on_date: date,
        rationale: str,
    ) -> None:
        """Liquidate and rebuild an equal-weight portfolio."""
        self.sell_all(data, on_date, rationale="Rebalance liquidation")
        if not tickers:
            return

        allocation = self.cash / len(tickers)
        for ticker in tickers:
            self.buy(
                ticker,
                data,
                on_date,
                allocation,
                rationale=rationale,
            )

    def copy_holdings(self) -> dict[str, float]:
        """Return a shallow copy of current share holdings."""
        return dict(self.shares)