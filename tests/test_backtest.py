from __future__ import annotations

import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path

from backtest.data_loader import TechTitansData
from backtest.dates import iter_weekly_dates
from backtest.engine import BacktestEngine
from backtest.strategy import MONTHLY_INJECTION


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class BacktestImportTests(unittest.TestCase):
    def assert_clean_import(self, statement: str) -> None:
        """Run an import statement in isolation and report its stderr on failure."""
        result = subprocess.run(
            [sys.executable, "-c", statement],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_backtest_imports_first_in_clean_interpreter(self) -> None:
        """Catch import-order regressions such as the former circular import."""
        self.assert_clean_import(
            "from backtest.engine import BacktestEngine; "
            "from core.data import build_meeting_context"
        )

    def test_core_data_imports_first_in_clean_interpreter(self) -> None:
        self.assert_clean_import(
            "from core.data import build_meeting_context; "
            "from backtest.engine import BacktestEngine"
        )

    def test_backtest_public_api_remains_available(self) -> None:
        self.assert_clean_import(
            "from backtest import BacktestEngine, DEFAULT_MONTHS, format_report; "
            "assert DEFAULT_MONTHS == 6"
        )

    def test_cli_runs_and_prints_report(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "backtest", "--months", "2"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AI Agent Trading Office — Backtest Report", result.stdout)
        self.assertIn("(2 months)", result.stdout)
        self.assertIn("Alpha (AI − Benchmark)", result.stdout)


class BacktestEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = TechTitansData()

    def test_data_window_uses_requested_month_count(self) -> None:
        start, end = self.data.available_window(6)

        months = [month for month in self.data.months if start <= month <= end]
        self.assertEqual(len(months), 6)
        self.assertEqual(end, self.data.months[-1])

    def test_engine_preserves_backtest_accounting_invariants(self) -> None:
        comparison = BacktestEngine().run(months=2)

        self.assertEqual(comparison.months, 2)
        self.assertEqual(comparison.agent.total_injected, 2 * MONTHLY_INJECTION)
        self.assertEqual(comparison.benchmark.total_injected, 2 * MONTHLY_INJECTION)
        self.assertAlmostEqual(
            comparison.alpha,
            comparison.agent.total_return - comparison.benchmark.total_return,
        )
        self.assertAlmostEqual(
            comparison.agent.final_nav,
            comparison.agent.nav_history[-1].nav,
        )
        self.assertAlmostEqual(
            comparison.benchmark.final_nav,
            comparison.benchmark.nav_history[-1].nav,
        )
        self.assertEqual(
            len(comparison.benchmark.nav_history),
            len(comparison.agent.nav_history),
        )
        self.assertLessEqual(len(comparison.agent.final_holdings), 15)

    def test_weekly_dates_include_end_date(self) -> None:
        dates = iter_weekly_dates(date(2026, 1, 1), date(2026, 1, 10))

        self.assertEqual(dates, [date(2026, 1, 1), date(2026, 1, 8), date(2026, 1, 10)])


if __name__ == "__main__":
    unittest.main()
