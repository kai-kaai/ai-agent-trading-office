"""The Watchman — active position management (paper/live in Phase 4).

Responsibilities (A4):
- Plan entries from CFO sized orders
- Activate / fill positions (PENDING -> OPEN)
- Manage trailing stops for open positions (paper mode first)
- Detect exit conditions (stop / trail / take profit)
- Support state progression: PENDING -> OPEN -> TRAILING -> CLOSED
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from modules.models import LivePosition, PositionState, SizedOrder


class WatchmanModule:
    """The Watchman manages live/paper positions with trailing stop logic."""

    def __init__(self, paper_mode: bool = True) -> None:
        self.paper_mode = paper_mode
        self._positions: dict[str, LivePosition] = {}  # simple registry for demo

    def plan_entry(self, order: SizedOrder) -> LivePosition:
        """Create a planned position from a sized order (initially PENDING)."""
        entry_price = order.entry_price or 0.0
        initial_trail = order.stop_loss  # start trailing at the hard stop

        pos = LivePosition(
            position_id=f"pos-{uuid4().hex[:8]}",
            ticker=order.ticker,
            action=order.action,
            shares=order.shares,
            entry_price=entry_price,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            state=PositionState.PENDING,
            opened_at=datetime.now(UTC),
            trailing_stop=initial_trail,
        )
        self._positions[pos.position_id] = pos
        return pos

    def activate(self, position: LivePosition) -> LivePosition:
        """Simulate fill: move from PENDING to OPEN (ready for management)."""
        if position.state == PositionState.PENDING:
            position.state = PositionState.OPEN
        return position

    def update_price(
        self,
        position: LivePosition,
        current_price: float,
        *,
        trail_pct: float | None = None,
    ) -> tuple[LivePosition, list[str]]:
        """Update a position with latest price.

        - Checks hard stop_loss / take_profit
        - Applies trailing stop for longs (raise stop as price rises)
        - Promotes OPEN -> TRAILING once in profit
        - Returns (updated_position, list_of_events)
        """
        events: list[str] = []
        if position.state == PositionState.CLOSED:
            return position, events

        position.last_price = round(current_price, 4)

        action = position.action.lower()
        is_long = action != "sell"

        # Determine effective stop (trailing takes precedence once set)
        effective_stop = position.trailing_stop or position.stop_loss

        # Exit checks
        hit_stop = (is_long and current_price <= (effective_stop or 0)) or \
                   (not is_long and current_price >= (effective_stop or 0))
        hit_tp = (position.take_profit is not None) and (
            (is_long and current_price >= position.take_profit) or
            (not is_long and current_price <= position.take_profit)
        )

        if hit_stop:
            position.state = PositionState.CLOSED
            events.append(f"EXIT: {position.ticker} hit stop/trail @ {current_price}")
            return position, events

        if hit_tp:
            position.state = PositionState.CLOSED
            events.append(f"EXIT: {position.ticker} hit take_profit @ {current_price}")
            return position, events

        # Trailing logic (focus on longs for US tech long bias; shorts symmetric)
        if is_long and current_price > position.entry_price:
            # Promote to TRAILING state once we have some profit
            if position.state == PositionState.OPEN:
                position.state = PositionState.TRAILING
                events.append(f"TRAILING activated for {position.ticker}")

            # Compute trail distance
            # Prefer initial risk distance (entry - stop), fallback to trail_pct of price
            initial_risk = None
            if position.stop_loss and position.entry_price:
                initial_risk = position.entry_price - position.stop_loss

            if initial_risk and initial_risk > 0:
                trail_dist = initial_risk * 0.75  # trail a bit tighter than initial risk
            else:
                pct = trail_pct if trail_pct is not None else 0.03
                trail_dist = current_price * pct

            new_trail = current_price - trail_dist

            # Only raise the trailing stop (never lower for longs)
            if position.trailing_stop is None or new_trail > position.trailing_stop:
                old_trail = position.trailing_stop
                position.trailing_stop = round(new_trail, 4)
                events.append(
                    f"TRAIL updated {position.ticker}: "
                    f"{old_trail} -> {position.trailing_stop} (price={current_price})"
                )

        elif not is_long and current_price < position.entry_price:
            # Symmetric for shorts (lower the stop)
            if position.state == PositionState.OPEN:
                position.state = PositionState.TRAILING
                events.append(f"TRAILING activated for {position.ticker} (short)")

            initial_risk = None
            if position.stop_loss and position.entry_price:
                initial_risk = position.stop_loss - position.entry_price  # positive

            if initial_risk and initial_risk > 0:
                trail_dist = initial_risk * 0.75
            else:
                pct = trail_pct if trail_pct is not None else 0.03
                trail_dist = current_price * pct

            new_trail = current_price + trail_dist  # for shorts, trail stop moves down? wait for short: higher stop means worse? No:

            # For short: you want to lower the stop (tighten or trail down as price drops)
            # Actually for short sell: stop is above entry. As price falls, you can lower the stop to lock profit.
            if position.trailing_stop is None or new_trail < position.trailing_stop:
                old = position.trailing_stop
                position.trailing_stop = round(new_trail, 4)
                events.append(f"TRAIL updated {position.ticker} (short): {old} -> {position.trailing_stop}")

        return position, events

    def close(self, position: LivePosition, reason: str = "manual") -> LivePosition:
        """Force close a position."""
        position.state = PositionState.CLOSED
        return position

    def get_position(self, position_id: str) -> LivePosition | None:
        return self._positions.get(position_id)