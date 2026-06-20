"""CLI entry point: python3 -m backtest"""

from __future__ import annotations

import argparse

from backtest.engine import BacktestEngine, DEFAULT_MONTHS
from backtest.report import format_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI Agent vs Tech Titans backtest")
    parser.add_argument(
        "--months",
        type=int,
        default=DEFAULT_MONTHS,
        help=f"Number of months to simulate (default: {DEFAULT_MONTHS})",
    )
    args = parser.parse_args()

    comparison = BacktestEngine().run(months=args.months)
    print(format_report(comparison))


if __name__ == "__main__":
    main()