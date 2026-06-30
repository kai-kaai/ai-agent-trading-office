from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

from httpx import ASGITransport, AsyncClient

import server.app as server_app
from backtest.engine import BacktestEngine
from core.decision_log import DecisionLog
from core.models import MeetingRecord, PortfolioDecision, TradeAction
from server.pending_meeting import PendingMeeting, clear_pending, set_pending


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def request(self, method: str, path: str, **kwargs):
        transport = ASGITransport(app=server_app.app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, path, **kwargs)

    def tearDown(self) -> None:
        clear_pending()

    async def test_council_evaluate(self) -> None:
        sample = {
            "ticker": "AAPL",
            "action": "buy",
            "grade": "A",
            "score": 72.0,
            "council": {"passed": True, "approval_count": 3, "vetoed": False, "summary": "ok", "votes": []},
        }

        with patch.object(server_app, "BrainModule") as brain_cls:
            brain_cls.return_value.evaluate.return_value.to_dict.return_value = sample
            response = await self.request(
                "POST",
                "/api/council/evaluate",
                json={"ticker": "AAPL", "action": "buy"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ticker"], "AAPL")
        brain_cls.return_value.evaluate.assert_called_once_with("AAPL", action="buy")

    async def test_pipeline_info(self) -> None:
        response = await self.request("GET", "/api/pipeline/info")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("brain", payload["stages"])
        self.assertIn("Risk Chair", payload["gate"])
        self.assertIn("shield", payload)
        self.assertIn("watchman", payload)
        self.assertIn("auditor", payload)

    async def test_health(self) -> None:
        response = await self.request("GET", "/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "trading-office"},
        )

    async def test_run_backtest_returns_comparison(self) -> None:
        payload = {
            "agent": {"total_return_pct": -3.79},
            "benchmark": {"total_return_pct": -1.36},
            "alpha_pct": -2.42,
            "months": 3,
        }
        comparison = Mock()
        comparison.to_dict.return_value = payload

        with patch.object(server_app, "run_and_cache", return_value=comparison) as run:
            response = await self.request("POST", "/api/backtest/run?months=3")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), payload)
        run.assert_called_once_with(months=3)

    async def test_run_backtest_rejects_non_positive_months(self) -> None:
        response = await self.request("POST", "/api/backtest/run?months=0")

        self.assertEqual(response.status_code, 422)

    async def test_latest_portfolio_returns_valued_holdings(self) -> None:
        comparison = BacktestEngine().run(months=2)

        with patch.object(server_app, "get_cached_comparison", return_value=comparison):
            response = await self.request("GET", "/api/portfolio/latest")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source"], "backtest")
        self.assertEqual(payload["position_count"], len(payload["positions"]))
        self.assertAlmostEqual(payload["total_nav"], comparison.agent.final_nav, places=2)
        self.assertAlmostEqual(
            payload["cash"] + sum(item["market_value"] for item in payload["positions"]),
            payload["total_nav"],
            delta=0.1,
        )
        self.assertTrue(all(item["weight_pct"] >= 0 for item in payload["positions"]))

    async def test_meeting_run_pending_and_approval_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_log = DecisionLog(Path(temp_dir))
            meeting_id = "meeting-api-test"
            decision = PortfolioDecision(
                meeting_date=date(2026, 6, 21),
                trades=[
                    TradeAction(
                        ticker="AAPL",
                        action="buy",
                        shares=1.0,
                        rationale="API test trade",
                    )
                ],
                summary="Test meeting decision",
                reasoning=["Exercise API approval flow"],
                agent_reports=[],
                decision_source="rule_based",
            )
            record = MeetingRecord(
                meeting_id=meeting_id,
                meeting_date=decision.meeting_date,
                participants=["Portfolio Manager"],
                utterances=[],
                meeting_summary=decision.summary,
                decision=decision,
            )
            json_path, _ = test_log.record(record)

            async def fake_run_meeting() -> dict:
                set_pending(
                    PendingMeeting(
                        meeting_id=meeting_id,
                        json_file=json_path.name,
                        summary=decision.summary,
                        trade_count=1,
                        trades=[
                            {
                                "ticker": "AAPL",
                                "action": "buy",
                                "shares": 1.0,
                                "rationale": "API test trade",
                            }
                        ],
                        decision_source="rule_based",
                    )
                )
                return {
                    "ok": True,
                    "meeting_id": meeting_id,
                    "summary": decision.summary,
                    "trade_count": 1,
                    "requires_approval": True,
                }

            with (
                patch.object(server_app, "decision_log", test_log),
                patch.object(server_app.manager, "run_meeting", new=fake_run_meeting),
            ):
                run_response = await self.request("POST", "/api/meetings/run")
                pending_response = await self.request("GET", "/api/meetings/pending")
                approval_response = await self.request(
                    "POST",
                    f"/api/meetings/{meeting_id}/approve",
                    json={"approved": True},
                )
                cleared_response = await self.request("GET", "/api/meetings/pending")

            self.assertEqual(run_response.status_code, 200)
            self.assertEqual(run_response.json()["meeting_id"], meeting_id)
            self.assertTrue(run_response.json()["requires_approval"])

            self.assertEqual(pending_response.status_code, 200)
            self.assertTrue(pending_response.json()["pending"])
            self.assertEqual(pending_response.json()["trade_count"], 1)

            self.assertEqual(approval_response.status_code, 200)
            self.assertEqual(approval_response.json()["approval_status"], "approved")
            self.assertEqual(cleared_response.json(), {"pending": False})

            saved = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertTrue(saved["decision"]["approved"])
            self.assertEqual(saved["approval_status"], "approved")


if __name__ == "__main__":
    unittest.main()
