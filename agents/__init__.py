"""AI Agent Trading Office – role implementations."""

from agents.backtester_evaluator import BacktesterEvaluator
from agents.financial_analyst import FinancialAnalyst
from agents.market_researcher import MarketResearcher
from agents.news_researcher import NewsResearcher
from agents.portfolio_manager import PortfolioManager
from agents.registry import (
    AGENT_REGISTRY,
    MEETING_TEAM_ROLES,
    get_agent,
    get_default_team,
    list_roles,
)
from agents.risk_manager import RiskManager

__all__ = [
    "AGENT_REGISTRY",
    "BacktesterEvaluator",
    "FinancialAnalyst",
    "MarketResearcher",
    "MEETING_TEAM_ROLES",
    "NewsResearcher",
    "PortfolioManager",
    "RiskManager",
    "get_agent",
    "get_default_team",
    "list_roles",
]