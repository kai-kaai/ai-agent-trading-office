from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yfinance as yf
except ImportError:
    yf = None

import sys
import tempfile

if "unittest" in sys.modules or "pytest" in sys.modules:
    PORTFOLIO_FILE = Path(tempfile.gettempdir()) / "test_paper_portfolio.json"
else:
    PORTFOLIO_FILE = Path(__file__).parent.parent / "logs" / "paper_portfolio.json"

INITIAL_CASH = 10000.0


def get_open_price(ticker: str) -> float:
    """Fetch the latest available market open price for a ticker using yfinance.

    Falls back to the last close price if open is unavailable.
    """
    ticker = ticker.upper().strip()
    if not ticker:
        raise ValueError("Ticker cannot be empty")

    if yf is None:
        return 150.0  # mock fallback

    try:
        # Fetch last 5 days to ensure we get data even on weekends/holidays
        ticker_data = yf.Ticker(ticker)
        hist = ticker_data.history(period="5d")
        if hist.empty:
            raise ValueError(f"No price data found for ticker {ticker}")

        open_price = float(hist["Open"].iloc[-1])
        if open_price > 0:
            return open_price

        close_price = float(hist["Close"].iloc[-1])
        if close_price > 0:
            return close_price

        raise ValueError(f"Invalid price data for ticker {ticker}")
    except Exception as e:
        raise ValueError(f"Failed to fetch price for {ticker}: {str(e)}")


class PaperPortfolioManager:
    """Manages the persistent paper portfolios for AI Agent and Tech Titans."""

    def __init__(self, filepath: Path = PORTFOLIO_FILE) -> None:
        self.filepath = filepath
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.filepath.exists():
            return self._init_default()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self._init_default()

    def _init_default(self) -> dict[str, Any]:
        now_str = datetime.now(UTC).isoformat()
        default_data = {
            "tech_titans": {
                "cash": INITIAL_CASH,
                "holdings": {},  # ticker -> shares
                "history": [
                    {
                        "date": now_str,
                        "nav": INITIAL_CASH,
                        "cash": INITIAL_CASH,
                        "holdings": {},
                    }
                ],
            },
            "ai_agent": {
                "cash": INITIAL_CASH,
                "holdings": {},
                "history": [
                    {
                        "date": now_str,
                        "nav": INITIAL_CASH,
                        "cash": INITIAL_CASH,
                        "holdings": {},
                    }
                ],
            },
            "transactions": [],
        }
        self._save(default_data)
        return default_data

    def _save(self, data: dict[str, Any]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def reset(self) -> None:
        """Reset both portfolios to initial cash ($10,000) and no holdings."""
        self.data = self._init_default()

    def inject_capital(self, amount: float = 305.0) -> None:
        """Inject additional capital cash to both portfolios."""
        now_str = datetime.now(UTC).isoformat()

        for port_key in ["tech_titans", "ai_agent"]:
            portfolio = self.data[port_key]
            portfolio["cash"] += amount

            # Record transaction
            self.data["transactions"].append(
                {
                    "portfolio": port_key,
                    "timestamp": now_str,
                    "ticker": "CASH_INJECT",
                    "action": "inject",
                    "shares": 1.0,
                    "price": amount,
                    "value": amount,
                }
            )
            # Record current NAV in history
            self._update_history(port_key)

        self._save(self.data)

    def rebalance(self, portfolio_key: str, target_tickers: list[str]) -> dict[str, Any]:
        """Perform an equal-weight rebalancing on a portfolio at Market Open prices."""
        if portfolio_key not in ["tech_titans", "ai_agent"]:
            raise ValueError(f"Invalid portfolio: {portfolio_key}")

        target_tickers = [t.upper().strip() for t in target_tickers if t.strip()]
        if not target_tickers:
            # Rebalance to 100% cash
            return self._liquidate_all(portfolio_key)

        now_str = datetime.now(UTC).isoformat()
        portfolio = self.data[portfolio_key]
        current_holdings = portfolio["holdings"]
        current_cash = portfolio["cash"]

        # 1. Fetch market open prices for target tickers
        prices: dict[str, float] = {}
        for ticker in target_tickers:
            prices[ticker] = get_open_price(ticker)

        # 2. Sell held assets that are NOT in the target list
        for ticker, shares in list(current_holdings.items()):
            if ticker not in prices:
                open_price = get_open_price(ticker)
                sell_val = shares * open_price
                current_cash += sell_val

                # Record transaction
                self.data["transactions"].append(
                    {
                        "portfolio": portfolio_key,
                        "timestamp": now_str,
                        "ticker": ticker,
                        "action": "sell",
                        "shares": round(shares, 4),
                        "price": round(open_price, 4),
                        "value": round(sell_val, 2),
                    }
                )
                del current_holdings[ticker]

        # 3. Calculate target value allocation per ticker
        # Total NAV = Cash + market value of existing holdings that are in target
        existing_val = 0.0
        for ticker in target_tickers:
            if ticker in current_holdings:
                existing_val += current_holdings[ticker] * prices[ticker]

        total_nav = current_cash + existing_val
        target_val_per_ticker = total_nav / len(target_tickers)

        # 4. Adjust holdings to match target value allocation
        for ticker in target_tickers:
            open_price = prices[ticker]
            current_shares = current_holdings.get(ticker, 0.0)
            target_shares = target_val_per_ticker / open_price
            diff_shares = target_shares - current_shares

            if abs(diff_shares) < 0.0001:
                continue

            trade_value = diff_shares * open_price

            if diff_shares > 0:
                # Buy additional shares
                current_cash -= trade_value
                current_holdings[ticker] = current_shares + diff_shares
                self.data["transactions"].append(
                    {
                        "portfolio": portfolio_key,
                        "timestamp": now_str,
                        "ticker": ticker,
                        "action": "buy",
                        "shares": round(diff_shares, 4),
                        "price": round(open_price, 4),
                        "value": round(trade_value, 2),
                    }
                )
            elif diff_shares < 0:
                # Sell excess shares
                sell_shares = abs(diff_shares)
                sell_val = sell_shares * open_price
                current_cash += sell_val
                current_holdings[ticker] = current_shares - sell_shares
                if current_holdings[ticker] < 0.0001:
                    del current_holdings[ticker]

                self.data["transactions"].append(
                    {
                        "portfolio": portfolio_key,
                        "timestamp": now_str,
                        "ticker": ticker,
                        "action": "sell",
                        "shares": round(sell_shares, 4),
                        "price": round(open_price, 4),
                        "value": round(sell_val, 2),
                    }
                )

        # 5. Commit changes
        portfolio["cash"] = round(current_cash, 2)
        portfolio["holdings"] = {k: round(v, 4) for k, v in current_holdings.items()}

        self._update_history(portfolio_key)
        self._save(self.data)
        return self.get_portfolio_view(portfolio_key)

    def _liquidate_all(self, portfolio_key: str) -> dict[str, Any]:
        now_str = datetime.now(UTC).isoformat()
        portfolio = self.data[portfolio_key]
        current_holdings = portfolio["holdings"]
        current_cash = portfolio["cash"]

        for ticker, shares in list(current_holdings.items()):
            open_price = get_open_price(ticker)
            sell_val = shares * open_price
            current_cash += sell_val

            self.data["transactions"].append(
                {
                    "portfolio": portfolio_key,
                    "timestamp": now_str,
                    "ticker": ticker,
                    "action": "sell",
                    "shares": round(shares, 4),
                    "price": round(open_price, 4),
                    "value": round(sell_val, 2),
                }
            )

        portfolio["holdings"] = {}
        portfolio["cash"] = round(current_cash, 2)

        self._update_history(portfolio_key)
        self._save(self.data)
        return self.get_portfolio_view(portfolio_key)

    def _update_history(self, portfolio_key: str) -> None:
        portfolio = self.data[portfolio_key]
        now_str = datetime.now(UTC).isoformat()

        # Compute current market value
        market_val = 0.0
        for ticker, shares in portfolio["holdings"].items():
            try:
                open_price = get_open_price(ticker)
                market_val += shares * open_price
            except Exception:
                market_val += shares * 100.0  # fallback

        nav = portfolio["cash"] + market_val
        portfolio["history"].append(
            {
                "date": now_str,
                "nav": round(nav, 2),
                "cash": portfolio["cash"],
                "holdings": portfolio["holdings"].copy(),
            }
        )

    def get_portfolio_view(self, portfolio_key: str) -> dict[str, Any]:
        """Compute the fully-valued portfolio view (holdings, current price, values, weights)."""
        portfolio = self.data[portfolio_key]
        cash = portfolio["cash"]
        holdings = portfolio["holdings"]

        positions = []
        total_market_value = 0.0

        for ticker, shares in holdings.items():
            try:
                price = get_open_price(ticker)
            except Exception:
                price = 100.0

            mkt_val = shares * price
            total_market_value += mkt_val

        total_nav = cash + total_market_value

        for ticker, shares in holdings.items():
            try:
                price = get_open_price(ticker)
            except Exception:
                price = 100.0

            mkt_val = shares * price
            weight = mkt_val / total_nav if total_nav else 0.0

            positions.append(
                {
                    "ticker": ticker,
                    "shares": round(shares, 4),
                    "price": round(price, 4),
                    "market_value": round(mkt_val, 2),
                    "weight_pct": round(weight * 100, 2),
                }
            )

        positions.sort(key=lambda x: x["market_value"], reverse=True)

        # Calculate returns since inception
        start_nav = portfolio["history"][0]["nav"] if portfolio["history"] else INITIAL_CASH
        total_return_pct = (total_nav / start_nav - 1.0) * 100 if start_nav else 0.0

        return {
            "total_nav": round(total_nav, 2),
            "cash": round(cash, 2),
            "cash_weight_pct": round(cash / total_nav * 100, 2) if total_nav else 0.0,
            "total_return_pct": round(total_return_pct, 2),
            "positions": positions,
            "history": portfolio["history"],
        }

    def execute_trades(self, portfolio_key: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute a list of transaction orders (BUY/SELL) on a portfolio at Market Open prices."""
        if portfolio_key not in ["tech_titans", "ai_agent"]:
            raise ValueError(f"Invalid portfolio: {portfolio_key}")

        if not trades:
            return self.get_portfolio_view(portfolio_key)

        now_str = datetime.now(UTC).isoformat()
        portfolio = self.data[portfolio_key]
        current_holdings = portfolio["holdings"]
        current_cash = portfolio["cash"]

        # 1. Separate into sell, explicit buy, and empty buy trades
        sell_trades = []
        explicit_buys = []
        empty_buys = []

        for trade in trades:
            ticker = trade["ticker"].upper().strip()
            action = trade["action"].lower().strip()
            shares = float(trade.get("shares") or 0.0)

            if action == "sell":
                sell_trades.append((ticker, shares))
            elif action == "buy":
                if shares > 0.0:
                    explicit_buys.append((ticker, shares))
                else:
                    empty_buys.append(ticker)

        # 2. Execute all sell trades first to free up cash
        for ticker, shares in sell_trades:
            try:
                open_price = get_open_price(ticker)
            except Exception:
                open_price = 100.0  # fallback
            
            current_shares = current_holdings.get(ticker, 0.0)
            sell_shares = min(shares, current_shares)
            if sell_shares > 0.0001:
                sell_val = sell_shares * open_price
                current_cash += sell_val
                current_holdings[ticker] = current_shares - sell_shares
                if current_holdings[ticker] < 0.0001:
                    del current_holdings[ticker]

                self.data["transactions"].append(
                    {
                        "portfolio": portfolio_key,
                        "timestamp": now_str,
                        "ticker": ticker,
                        "action": "sell",
                        "shares": round(sell_shares, 4),
                        "price": round(open_price, 4),
                        "value": round(sell_val, 2),
                    }
                )

        # 3. Handle explicit buy trades
        buy_orders = []  # list of (ticker, shares, open_price)
        explicit_buy_cost = 0.0

        for ticker, shares in explicit_buys:
            try:
                open_price = get_open_price(ticker)
            except Exception:
                open_price = 100.0
            explicit_buy_cost += shares * open_price
            buy_orders.append((ticker, shares, open_price))

        # 4. Handle empty buy trades (allocate remaining cash equally)
        if empty_buys:
            remaining_cash = max(0.0, current_cash - explicit_buy_cost)
            allocation_per_buy = remaining_cash / len(empty_buys)
            for ticker in empty_buys:
                try:
                    open_price = get_open_price(ticker)
                except Exception:
                    open_price = 100.0
                shares = allocation_per_buy / open_price
                if shares > 0.0001:
                    buy_orders.append((ticker, shares, open_price))

        # 5. Execute all buy orders
        for ticker, shares, open_price in buy_orders:
            trade_value = shares * open_price
            if current_cash >= trade_value:
                current_cash -= trade_value
                current_holdings[ticker] = current_holdings.get(ticker, 0.0) + shares
                self.data["transactions"].append(
                    {
                        "portfolio": portfolio_key,
                        "timestamp": now_str,
                        "ticker": ticker,
                        "action": "buy",
                        "shares": round(shares, 4),
                        "price": round(open_price, 4),
                        "value": round(trade_value, 2),
                    }
                )
            else:
                # Buy as much as cash allows
                max_shares = current_cash / open_price
                if max_shares > 0.0001:
                    buy_val = max_shares * open_price
                    current_cash -= buy_val
                    current_holdings[ticker] = current_holdings.get(ticker, 0.0) + max_shares
                    self.data["transactions"].append(
                        {
                            "portfolio": portfolio_key,
                            "timestamp": now_str,
                            "ticker": ticker,
                            "action": "buy",
                            "shares": round(max_shares, 4),
                            "price": round(open_price, 4),
                            "value": round(buy_val, 2),
                        }
                    )

        portfolio["cash"] = round(current_cash, 2)
        portfolio["holdings"] = {k: round(v, 4) for k, v in current_holdings.items()}

        self._update_history(portfolio_key)
        self._save(self.data)
        return self.get_portfolio_view(portfolio_key)

