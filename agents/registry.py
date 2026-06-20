"""Agent registry – central lookup for all trading-office roles."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.base_agent import BaseAgent

from agents.backtester_evaluator import BacktesterEvaluator
from agents.financial_analyst import FinancialAnalyst
from agents.market_researcher import MarketResearcher
from agents.news_researcher import NewsResearcher
from agents.portfolio_manager import PortfolioManager
from agents.risk_manager import RiskManager

AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "portfolio_manager": PortfolioManager,
    "financial_analyst": FinancialAnalyst,
    "news_researcher": NewsResearcher,
    "market_researcher": MarketResearcher,
    "risk_manager": RiskManager,
    "backtester_evaluator": BacktesterEvaluator,
}

# Specialist agents that attend weekly meetings (excludes Portfolio Manager).
MEETING_TEAM_ROLES: tuple[str, ...] = (
    "financial_analyst",
    "news_researcher",
    "market_researcher",
    "risk_manager",
    "backtester_evaluator",
)


def get_agent(role: str) -> BaseAgent:
    """Instantiate an agent by role name.

    Args:
        role: Registry key (e.g. ``"financial_analyst"``).

    Raises:
        KeyError: If the role is not registered.
    """
    if role not in AGENT_REGISTRY:
        available = ", ".join(sorted(AGENT_REGISTRY))
        raise KeyError(f"Unknown agent role '{role}'. Available: {available}")
    return AGENT_REGISTRY[role]()


def get_default_team() -> list[BaseAgent]:
    """Return the full specialist team for weekly meetings."""
    return [get_agent(role) for role in MEETING_TEAM_ROLES]


def list_roles() -> list[str]:
    """Return all registered agent role keys."""
    return sorted(AGENT_REGISTRY.keys())