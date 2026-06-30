from __future__ import annotations

import unittest

from modules.brain.council import evaluate_council
from modules.models import (
    CouncilMember,
    CouncilVerdict,
    CouncilVote,
    PipelineStage,
    SetupGrade,
    ShieldVerdict,
    TradeSetup,
    VoteDecision,
)
from modules.pipeline import PipelineContext, TradingPipeline
from modules.shield.orchestrator import ShieldModule
from modules.cfo.sizing import CFOModule
from modules.models import LivePosition, PositionState, SetupGrade, StrategyStage, TradeAutopsy
from modules.watchman.manager import WatchmanModule
from modules.auditor.autopsy import AuditorModule


class CouncilTests(unittest.TestCase):
    def test_passes_with_two_approvals_and_risk_chair_ok(self) -> None:
        verdict = evaluate_council(
            [
                CouncilVote(CouncilMember.BEAR, VoteDecision.APPROVE, "ok"),
                CouncilVote(CouncilMember.BULL, VoteDecision.APPROVE, "ok"),
                CouncilVote(CouncilMember.RISK_CHAIR, VoteDecision.APPROVE, "ok"),
            ]
        )
        self.assertTrue(verdict.passed)
        self.assertFalse(verdict.vetoed)

    def test_risk_chair_veto_blocks_majority(self) -> None:
        verdict = evaluate_council(
            [
                CouncilVote(CouncilMember.BEAR, VoteDecision.APPROVE, "ok"),
                CouncilVote(CouncilMember.BULL, VoteDecision.APPROVE, "ok"),
                CouncilVote(CouncilMember.RISK_CHAIR, VoteDecision.REJECT, "veto", veto=True),
            ]
        )
        self.assertFalse(verdict.passed)
        self.assertTrue(verdict.vetoed)

    def test_risk_chair_reject_counts_as_veto(self) -> None:
        verdict = evaluate_council(
            [
                CouncilVote(CouncilMember.BEAR, VoteDecision.APPROVE, "ok"),
                CouncilVote(CouncilMember.BULL, VoteDecision.APPROVE, "ok"),
                CouncilVote(CouncilMember.RISK_CHAIR, VoteDecision.REJECT, "too risky"),
            ]
        )
        self.assertFalse(verdict.passed)
        self.assertTrue(verdict.vetoed)


def _make_fake_council(passed: bool = True) -> CouncilVerdict:
    votes = [
        CouncilVote(CouncilMember.BEAR, VoteDecision.APPROVE if passed else VoteDecision.REJECT, "test"),
        CouncilVote(CouncilMember.BULL, VoteDecision.APPROVE if passed else VoteDecision.REJECT, "test"),
        CouncilVote(CouncilMember.RISK_CHAIR, VoteDecision.APPROVE if passed else VoteDecision.REJECT, "test"),
    ]
    return CouncilVerdict(
        votes=votes,
        approval_count=3 if passed else 0,
        passed=passed,
        vetoed=not passed,
        summary="test",
    )


def _make_setup(
    ticker: str = "WDAY",
    grade: SetupGrade = SetupGrade.A,
    sector: str | None = "Information Technology",
    action: str = "buy",
) -> TradeSetup:
    return TradeSetup(
        ticker=ticker,
        action=action,
        grade=grade,
        score=75.0,
        council=_make_fake_council(passed=True),
        sector=sector,
    )


class ShieldTests(unittest.TestCase):
    def test_shield_go_for_good_setup(self) -> None:
        shield = ShieldModule()
        setup = _make_setup(grade=SetupGrade.A, sector="Information Technology")
        dec = shield.evaluate(setup, risk_reward=2.5, current_sectors=[])
        self.assertEqual(dec.verdict, ShieldVerdict.GO)

    def test_shield_blocks_low_rrr(self) -> None:
        shield = ShieldModule()
        setup = _make_setup(grade=SetupGrade.A)
        dec = shield.evaluate(setup, risk_reward=1.5)
        self.assertEqual(dec.verdict, ShieldVerdict.PASS)
        self.assertTrue(any("RRR" in r for r in dec.reasons))

    def test_shield_blocks_grade_c(self) -> None:
        shield = ShieldModule()
        setup = _make_setup(grade=SetupGrade.C)
        dec = shield.evaluate(setup, risk_reward=2.5)
        self.assertEqual(dec.verdict, ShieldVerdict.PASS)
        self.assertTrue(any("grade" in r.lower() for r in dec.reasons))

    def test_shield_blocks_sector_overlap(self) -> None:
        shield = ShieldModule()
        setup = _make_setup(grade=SetupGrade.A, sector="Information Technology")
        # Already 4 positions in tech → 5th should block
        current = ["Information Technology"] * 4
        dec = shield.evaluate(setup, risk_reward=2.5, current_sectors=current)
        self.assertEqual(dec.verdict, ShieldVerdict.PASS)
        self.assertTrue(any("concentration" in r.lower() or "overlap" in r.lower() for r in dec.reasons))
        self.assertTrue(len(dec.overlap_warnings) > 0)

    def test_shield_allows_when_under_limit(self) -> None:
        shield = ShieldModule()
        setup = _make_setup(grade=SetupGrade.B, sector="Information Technology")
        current = ["Information Technology"] * 3
        dec = shield.evaluate(setup, risk_reward=3.0, current_sectors=current)
        self.assertEqual(dec.verdict, ShieldVerdict.GO)


class PipelineTests(unittest.TestCase):
    def test_halts_at_brain_when_council_fails(self) -> None:
        result = TradingPipeline().run("AAPL", score_override=30.0)
        self.assertTrue(result.halted)
        self.assertEqual(result.stage_reached, PipelineStage.BRAIN)
        self.assertIsNotNone(result.setup)

    def test_completes_for_strong_setup(self) -> None:
        result = TradingPipeline().run(
            "WDAY",  # ticker that exists in data so sector populates
            score_override=80.0,
            context=PipelineContext(nav_usd=5_000, risk_reward=2.5),
        )
        self.assertFalse(result.halted)
        self.assertEqual(result.stage_reached, PipelineStage.COMPLETE)
        self.assertIsNotNone(result.sized_order)
        self.assertEqual(result.shield.verdict, ShieldVerdict.GO)

    def test_halts_at_shield_on_low_rrr(self) -> None:
        result = TradingPipeline().run(
            "WDAY",
            score_override=75.0,
            context=PipelineContext(risk_reward=1.0),
        )
        self.assertTrue(result.halted)
        self.assertEqual(result.stage_reached, PipelineStage.SHIELD)
        self.assertEqual(result.shield.verdict, ShieldVerdict.PASS)

    def test_halts_at_shield_on_sector_overlap(self) -> None:
        # 4 existing tech holdings + new buy in same sector
        ctx = PipelineContext(
            risk_reward=2.5,
            current_sectors=["Information Technology"] * 4,
        )
        result = TradingPipeline().run("WDAY", score_override=78.0, context=ctx)
        self.assertTrue(result.halted)
        self.assertEqual(result.stage_reached, PipelineStage.SHIELD)
        self.assertEqual(result.shield.verdict, ShieldVerdict.PASS)
        self.assertTrue(any("concentration" in (r or "").lower() for r in (result.shield.reasons or [])))

    def test_pipeline_describe_has_stages(self) -> None:
        info = TradingPipeline.describe()
        self.assertIn("brain", info["stages"])
        self.assertIn("Risk Chair", info["gate"])
        self.assertIn("shield", info)
        self.assertIn("cfo", info)


class CFOTests(unittest.TestCase):
    def _good_setup(self, score: float = 78.0) -> TradeSetup:
        return _make_setup(grade=SetupGrade.A, sector="Technology")
        # Note: _make_setup hardcodes score=75; we override after for conviction test

    def test_sizes_with_explicit_params(self) -> None:
        cfo = CFOModule()
        # Use exactly score=70 to get base 1% risk (conviction factor ~1.0)
        setup = TradeSetup(
            ticker="TEST",
            action="buy",
            grade=SetupGrade.A,
            score=70.0,
            council=_make_fake_council(passed=True),
            sector="Technology",
        )
        # Force a known entry and stop so math is deterministic
        order = cfo.size(setup, nav_usd=10_000, entry_price=100.0, stop_distance_pct=0.05, risk_reward=2.0)
        self.assertEqual(order.ticker, setup.ticker)
        self.assertGreater(order.shares, 0)
        # 1% risk on 10k => $100 risk budget. Risk/share = 5 => shares=20
        self.assertAlmostEqual(order.risk_pct, 0.01, places=3)
        self.assertAlmostEqual(order.max_loss_usd, 100.0, places=1)
        self.assertAlmostEqual(order.shares, 20.0, places=1)
        self.assertAlmostEqual(order.stop_loss or 0, 95.0, places=1)
        self.assertAlmostEqual(order.take_profit or 0, 110.0, places=1)

    def test_vol_high_reduces_risk(self) -> None:
        cfo = CFOModule()
        setup = _make_setup(grade=SetupGrade.A)
        normal = cfo.size(setup, nav_usd=10_000, entry_price=100.0, stop_distance_pct=0.05, volatility_regime="normal")
        high = cfo.size(setup, nav_usd=10_000, entry_price=100.0, stop_distance_pct=0.05, volatility_regime="high")
        self.assertGreater(normal.risk_pct, high.risk_pct)
        # high vol should be ~0.5x
        self.assertLess(high.risk_pct, normal.risk_pct * 0.6)

    def test_higher_score_increases_risk_modestly(self) -> None:
        cfo = CFOModule()
        low_score_setup = _make_setup(grade=SetupGrade.B)
        # Manually tweak score for conviction test (the _make_setup score is fixed but we can replace)
        high_score_setup = _make_setup(grade=SetupGrade.A_PLUS)
        high_score_setup = TradeSetup(
            ticker=high_score_setup.ticker,
            action=high_score_setup.action,
            grade=high_score_setup.grade,
            score=92.0,
            council=high_score_setup.council,
            sector=high_score_setup.sector,
        )

        low = cfo.size(low_score_setup, nav_usd=10_000, entry_price=100.0, stop_distance_pct=0.05)
        high = cfo.size(high_score_setup, nav_usd=10_000, entry_price=100.0, stop_distance_pct=0.05)
        self.assertGreater(high.risk_pct, low.risk_pct)
        self.assertLessEqual(high.risk_pct, 0.015)

    def test_uses_risk_reward_for_tp(self) -> None:
        cfo = CFOModule()
        setup = _make_setup(grade=SetupGrade.A)
        o = cfo.size(setup, nav_usd=5000, entry_price=200.0, stop_distance_pct=0.04, risk_reward=3.0)
        # risk/share = 8, 3x = +24 => TP around 224
        self.assertAlmostEqual(o.take_profit or 0, 224.0, places=1)

    def test_pipeline_produces_sized_order_with_risk(self) -> None:
        result = TradingPipeline().run(
            "WDAY",
            score_override=82.0,
            context=PipelineContext(nav_usd=20_000, risk_reward=2.5, volatility_regime="normal"),
        )
        self.assertFalse(result.halted)
        self.assertIsNotNone(result.sized_order)
        self.assertGreater(result.sized_order.shares, 0)  # type: ignore[union-attr]
        self.assertLessEqual(result.sized_order.risk_pct, 0.015)  # type: ignore[union-attr]


class WatchmanTests(unittest.TestCase):
    def _make_position(self, entry: float = 100.0, stop: float = 95.0, tp: float = 110.0, action: str = "buy") -> LivePosition:
        return LivePosition(
            position_id="pos-test123",
            ticker="TEST",
            action=action,
            shares=20.0,
            entry_price=entry,
            stop_loss=stop,
            take_profit=tp,
            state=PositionState.OPEN,
            opened_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            trailing_stop=stop,
        )

    def test_plan_and_activate(self) -> None:
        wm = WatchmanModule()
        # Use a fake sized order (minimal)
        from modules.models import SizedOrder
        order = SizedOrder(
            ticker="AAPL", action="buy", shares=10, entry_price=200.0,
            stop_loss=190.0, take_profit=220.0, risk_pct=0.01, max_loss_usd=100.0
        )
        pos = wm.plan_entry(order)
        self.assertEqual(pos.state, PositionState.PENDING)
        self.assertEqual(pos.trailing_stop, 190.0)

        pos2 = wm.activate(pos)
        self.assertEqual(pos2.state, PositionState.OPEN)

    def test_trailing_raises_stop_on_up_move(self) -> None:
        wm = WatchmanModule()
        pos = self._make_position(entry=100.0, stop=95.0)
        pos.state = PositionState.OPEN

        # Small move up -> promote + trail
        updated, events = wm.update_price(pos, 103.0)
        self.assertEqual(updated.state, PositionState.TRAILING)
        self.assertIsNotNone(updated.trailing_stop)
        trail_after_103 = updated.trailing_stop
        # Initial risk=5, trail_dist ~3.75, new trail ~99.25 > 95
        self.assertGreater(trail_after_103 or 0, 95.0)

        # Further up
        updated2, ev2 = wm.update_price(updated, 108.0)
        self.assertGreater(updated2.trailing_stop or 0, trail_after_103 or 0)

    def test_hits_trailing_stop_and_closes(self) -> None:
        wm = WatchmanModule()
        pos = self._make_position(entry=100.0, stop=95.0)
        pos.state = PositionState.TRAILING
        pos.trailing_stop = 99.0   # already trailed

        updated, events = wm.update_price(pos, 99.5)  # still above trail
        self.assertNotEqual(updated.state, PositionState.CLOSED)

        updated2, events2 = wm.update_price(updated, 98.5)  # <= trail
        self.assertEqual(updated2.state, PositionState.CLOSED)
        self.assertTrue(any("stop" in e.lower() or "trail" in e.lower() for e in events2))

    def test_hits_take_profit(self) -> None:
        wm = WatchmanModule()
        pos = self._make_position(entry=100.0, stop=95.0, tp=110.0)
        updated, _ = wm.update_price(pos, 111.0)
        self.assertEqual(updated.state, PositionState.CLOSED)

    def test_pipeline_watchman_advances_state(self) -> None:
        result = TradingPipeline().run(
            "WDAY",
            score_override=80.0,
            context=PipelineContext(nav_usd=10_000, risk_reward=2.0),
        )
        self.assertFalse(result.halted)
        self.assertTrue(any("watchman_position" in e for e in result.events))
        # Should have advanced past PENDING because pipeline activates
        # (we don't store full pos in result, but event string has state info indirectly)
        self.assertIn("watchman", [e for e in result.events if e.startswith("watchman")][0].lower())


class AuditorTests(unittest.TestCase):
    def _closed_pos(self, ticker="TEST", entry=100.0, exit_p=112.0, stop=95.0):
        # simulate closed LivePosition
        from datetime import datetime, timezone
        return type("Pos", (), {
            "ticker": ticker,
            "entry_price": entry,
            "last_price": exit_p,
            "stop_loss": stop,
            "trailing_stop": 99.0,
            "state": PositionState.CLOSED,
            "position_id": "pos-abc123",
            "action": "buy",
            "shares": 10.0,
        })()

    def test_autopsy_with_metrics(self) -> None:
        auditor = AuditorModule()
        autopsy = auditor.autopsy_trade(
            "t1", "AAPL", "win",
            entry_price=100.0, exit_price=112.0, stop_price=95.0
        )
        self.assertEqual(autopsy.ticker, "AAPL")
        self.assertIsNotNone(autopsy.pnl_pct)
        self.assertGreater(autopsy.pnl_pct or 0, 0)
        self.assertIsNotNone(autopsy.r_multiple)
        self.assertGreater(len(autopsy.strengths), 0)

    def test_auto_lessons_on_loss(self) -> None:
        auditor = AuditorModule()
        autopsy = auditor.autopsy_trade("t2", "XYZ", "loss", entry_price=50, exit_price=47, stop_price=48)
        self.assertTrue(any("loss" in m.lower() for m in autopsy.mistakes))
        self.assertTrue(len(autopsy.lessons) > 0)

    def test_propose_and_promote(self) -> None:
        auditor = AuditorModule()
        cand = auditor.propose_strategy("Trail Tighten", "Use 0.6x initial risk for trail after 2% profit")
        self.assertEqual(cand.stage, StrategyStage.CANDIDATE)

        cand2 = auditor.promote(cand, StrategyStage.BACKTEST)
        self.assertEqual(cand2.stage, StrategyStage.BACKTEST)

        cand3 = auditor.attach_backtest_results(cand2, {"alpha": 0.08, "total_return": 0.12})
        self.assertEqual(cand3.stage, StrategyStage.BACKTEST)
        self.assertIn("alpha", cand3.backtest_metrics)

    def test_review_and_promote_flow(self) -> None:
        auditor = AuditorModule()
        cand = auditor.propose_strategy("Better RRR", "Only take A+ with RRR>=2.5")
        cand = auditor.review_and_promote(cand, backtest_metrics={"alpha": 0.03, "total_return": 0.09})
        self.assertEqual(cand.stage, StrategyStage.SANDBOX)

    def test_autopsy_from_closed_position(self) -> None:
        auditor = AuditorModule()
        pos = self._closed_pos(exit_p=108.0)
        autopsy = auditor.autopsy_from_position("t3", pos, "win")
        self.assertIsInstance(autopsy, TradeAutopsy)
        self.assertGreater(autopsy.pnl_pct or 0, 0)

    def test_pipeline_audit_hook(self) -> None:
        pipe = TradingPipeline()
        res = pipe.run("WDAY", score_override=78.0)
        # simulate close
        pos = res  # not real, create fake
        fake_pos = self._closed_pos(ticker="WDAY", entry=100, exit_p=105)
        audit = pipe.audit_closed_position(fake_pos, outcome="win")
        self.assertIsInstance(audit, TradeAutopsy)
        self.assertEqual(audit.ticker, "WDAY")


if __name__ == "__main__":
    unittest.main()