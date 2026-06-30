from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from core.data.market_data import TechnicalSnapshot
from modules.brain.council import BrainModule, evaluate_council, rule_based_council_votes
from modules.brain.grading import score_to_grade
from modules.brain.llm_council import parse_council_votes
from modules.brain.scanners import ScannerReport, scan_ticker
from modules.models import CouncilMember, CouncilVote, SetupGrade, VoteDecision


def _sample_report(composite: float = 75.0) -> ScannerReport:
    return ScannerReport(
        ticker="AAPL",
        action="buy",
        fundamental_score=70.0,
        sector_strength=68.0,
        structure_score=72.0,
        news_score=65.0,
        composite_score=composite,
        grade=score_to_grade(composite),
        sector="Technology",
        trend="uptrend",
        structure_notes=["Trend: uptrend"],
        news_sentiment=0.65,
        scanned_at=date(2026, 6, 25),
    )


class BrainScannerTests(unittest.TestCase):
    @patch("modules.brain.scanners.get_news_service")
    @patch("modules.brain.scanners.get_market_data_service")
    @patch("modules.brain.scanners.get_fundamental_service")
    def test_scan_ticker_composite_score(self, mock_fund, mock_market, mock_news) -> None:
        fund = mock_fund.return_value
        fund.score.return_value = (80.0, None)

        market = mock_market.return_value
        market.get_technicals.side_effect = lambda ticker: TechnicalSnapshot(
            ticker=ticker,
            price=100.0,
            sma_50=95.0,
            sma_200=90.0,
            rsi_14=55.0,
            return_1m=0.04,
            return_3m=0.10,
            pct_from_52w_high=0.92,
            trend="uptrend",
            score=75.0,
            data_source="test",
        )

        news = mock_news.return_value
        news.analyze.return_value.score = 60.0
        news.analyze.return_value.top_headline = "Test headline"
        news.analyze.return_value.data_source = "test"
        news.analyze.return_value.headline_count = 2

        report = scan_ticker("AAPL")
        self.assertEqual(report.ticker, "AAPL")
        self.assertGreater(report.composite_score, 0)
        self.assertIn(report.grade, {SetupGrade.A, SetupGrade.A_PLUS, SetupGrade.B})


class CouncilLogicTests(unittest.TestCase):
    def test_rule_based_council_approves_strong_setup(self) -> None:
        votes = rule_based_council_votes(_sample_report(82.0))
        verdict = evaluate_council(votes)
        self.assertTrue(verdict.passed)

    def test_rule_based_council_rejects_weak_setup(self) -> None:
        votes = rule_based_council_votes(_sample_report(30.0))
        verdict = evaluate_council(votes)
        self.assertFalse(verdict.passed)

    def test_parse_llm_council_votes(self) -> None:
        votes = parse_council_votes(
            {
                "votes": [
                    {"member": "bear", "decision": "approve", "rationale": "ok"},
                    {"member": "bull", "decision": "approve", "rationale": "ok"},
                    {"member": "risk_chair", "decision": "approve", "rationale": "ok", "veto": False},
                ]
            }
        )
        self.assertIsNotNone(votes)
        self.assertTrue(evaluate_council(votes).passed)


class BrainModuleTests(unittest.TestCase):
    @patch("modules.brain.council.deliberate_with_llm", return_value=None)
    @patch("modules.brain.council.scan_ticker")
    def test_evaluate_uses_scanner_report(self, mock_scan, _mock_llm) -> None:
        mock_scan.return_value = _sample_report(78.0)
        setup = BrainModule().evaluate("AAPL")
        self.assertEqual(setup.ticker, "AAPL")
        self.assertEqual(setup.score, 78.0)
        self.assertIn("scanner", setup.metadata)
        self.assertEqual(setup.metadata["decision_source"], "rule_based")


if __name__ == "__main__":
    unittest.main()