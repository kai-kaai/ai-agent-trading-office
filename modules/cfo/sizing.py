"""The CFO — position sizing and risk budgeting (Arch A3).

Core rule: risk a small % of NAV on each trade, sized to the distance to stop.
Volatility-aware: shrink risk budget in high-vol regimes.
Uses live price + simple volatility proxy from technicals when no overrides provided.
"""

from __future__ import annotations

from modules.models import SizedOrder, TradeSetup

from core.data.market_data import get_market_data_service

DEFAULT_RISK_PCT = 0.01  # 1% of NAV at risk per trade (base)
VOLATILITY_RISK_SCALE = {"low": 1.0, "normal": 1.0, "high": 0.5}
CONVICTION_RISK_CAP = 0.015  # never risk more than 1.5% even on A+ high conviction

# Base stop distances by regime (wider stops in high vol to avoid noise whipsaws)
BASE_STOP_PCT = {"low": 0.035, "normal": 0.05, "high": 0.07}


def _estimate_stop_distance(technical, regime: str, override: float | None) -> float:
    """Pick a reasonable stop distance using regime and a crude vol proxy."""
    if override is not None and override > 0:
        return max(0.005, min(override, 0.20))

    regime = (regime or "normal").lower()
    base = BASE_STOP_PCT.get(regime, 0.05)

    # Crude volatility adjustment from available snapshot fields
    vol_mult = 1.0
    if technical and technical.return_1m is not None:
        # Larger recent move => treat as higher vol environment
        abs_move = abs(technical.return_1m)
        if abs_move > 0.08:
            vol_mult = 1.35
        elif abs_move > 0.04:
            vol_mult = 1.15
        elif abs_move < 0.01:
            vol_mult = 0.85

    if technical and technical.pct_from_52w_high is not None:
        # Near 52w high with weak momentum can justify tighter stops
        if technical.pct_from_52w_high > 0.90 and (technical.return_1m or 0) < 0:
            vol_mult = min(vol_mult, 0.9)

    stop = base * vol_mult
    return max(0.02, min(stop, 0.12))  # clamp to sane range


class CFOModule:
    """CFO handles position sizing with risk-first, volatility-adjusted logic."""

    def size(
        self,
        setup: TradeSetup,
        nav_usd: float,
        entry_price: float | None = None,
        stop_distance_pct: float | None = None,
        volatility_regime: str = "normal",
        risk_reward: float = 2.0,
    ) -> SizedOrder:
        """Compute share quantity so that the max loss on the trade equals risk_pct * nav.

        - Fetches real price via market data when entry_price not supplied.
        - Dynamically sets stop distance using regime + recent price action.
        - Scales risk % by volatility regime.
        - Uses setup.score for mild conviction adjustment (higher score = modestly larger size).
        - Respects risk_reward for take-profit placement.
        """
        if nav_usd <= 0:
            nav_usd = 10_000.0

        # 1. Resolve entry price (real data preferred)
        price = entry_price
        technical = None
        if price is None or price <= 0:
            try:
                market = get_market_data_service()
                technical = market.get_technicals(setup.ticker)
                price = technical.price
            except Exception:
                technical = None
                price = None
        if price is None or price <= 0:
            price = 100.0  # last resort fallback

        # 2. Determine risk % (vol scaled + conviction)
        scale = VOLATILITY_RISK_SCALE.get(volatility_regime.lower(), 1.0)
        risk_pct = DEFAULT_RISK_PCT * scale

        # Light conviction boost: A+ setups can use a bit more risk, but capped
        conviction = max(0.6, min(1.3, setup.score / 70.0))
        risk_pct = min(CONVICTION_RISK_CAP, risk_pct * conviction)

        max_loss_usd = nav_usd * risk_pct

        # 3. Compute stop distance and levels
        stop_dist = _estimate_stop_distance(technical, volatility_regime, stop_distance_pct)
        stop_loss = round(price * (1.0 - stop_dist), 4)
        risk_per_share = max(price - stop_loss, 0.01)

        shares = max_loss_usd / risk_per_share

        # 4. Take profit using desired RRR (from Shield / context)
        reward_multiple = risk_reward if risk_reward and risk_reward > 0 else 2.0
        take_profit = round(price + (risk_per_share * reward_multiple), 4)

        return SizedOrder(
            ticker=setup.ticker,
            action=setup.action,
            shares=round(shares, 4),
            entry_price=round(price, 4),
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_pct=round(risk_pct, 5),
            max_loss_usd=round(max_loss_usd, 2),
            volatility_regime=volatility_regime,
        )