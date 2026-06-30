# Progress Log

## คำอธิบาย Phase (อ่านก่อน)

โปรเจคมี **2 ชุด Phase** — อย่าสับสน:

| คำเรียก | ช่วง | ความหมาย |
|---------|------|----------|
| **Build B1–B4** | มิ.ย. 2026 | สร้างระบบเดิม: backtest, data, semi-auto, dashboard |
| **Arch A0–A6** | มิ.ย. 2026+ | สถาปัตยกรรมใหม่ 5 modules (Brain → Auditor) |

## สถานะล่าสุด (2026-06-25)

### Build (ระบบเดิม) — เสร็จหมด

| Build | สถานะ | เนื้อหา |
|-------|--------|--------|
| B1 Backtest | ✅ | AI vs Tech Titans, CLI + UI |
| B2 Real Data | ✅ | CSV + yfinance agents |
| B3 Semi-Auto + LLM | ✅ | Approve/Reject, multi-provider |
| B4 Dashboard++ | ✅ | Performance chart, holdings, Pixel Office |

### Arch (สถาปัตยกรรมใหม่)

| Arch | สถานะ | เนื้อหา |
|------|--------|--------|
| A0 Foundation | ✅ | `modules/`, pipeline skeleton, docs |
| A1 Brain | ✅ | scanners, AI Council, APIs |
| A2 Shield | ✅ | RRR >= 2.0, min grade B, sector overlap (max 4 per sector) |
| A3 CFO | ✅ | 1% risk NAV (vol scaled + conviction), dynamic stops, RRR TP |
| A4 Watchman | ✅ | plan/activate + trailing stop (paper), state machine, exit detection |
| A5 Auditor | ✅ | autopsy (auto lessons + metrics), promotion loop, backtest attach |
| A6 Dashboard | ✅ | 5-module UI |

### อื่น ๆ

| ส่วน | สถานะ |
|------|--------|
| Tech Titans CSV | ✅ 733 แถว, 49 เดือน |
| Legacy meeting (6 agents) | ✅ ยังใช้ได้ (`agents/`) |

## Arch A1 — Brain (เสร็จ)

- Scanners: fundamental, sector strength (vs QQQ), structure, news
- เกรด A+ จาก composite score
- Council: LLM หรือ rule-based · โหวต 2/3 + Risk Chair veto
- API: `POST /api/council/evaluate`, `POST /api/pipeline/run`

## Arch A2 — Shield (เสร็จ)

- RRR gate: ต้อง ≥ 2.0
- Grade gate: อย่างน้อย B (C ถูกบล็อก)
- Sector overlap: สำหรับ BUY ถ้าภาคเดียวกันเกิน 4 ตำแหน่ง → PASS
- PipelineContext รองรับ current_sectors
- Verdict: GO / PASS (พร้อม overlap_warnings และ reasons)

## Arch A3 — CFO (เสร็จ)

- Risk 1% NAV ต่อไม้ (base)
- Volatility scaling: high regime ลดเหลือ 0.5×
- Conviction boost จาก setup.score (แต่ไม่เกิน 1.5%)
- ดึงราคาจริงจาก market data service
- Stop distance อัตโนมัติตาม regime + recent move (wider ใน high vol)
- TP ใช้ risk_reward จาก context (สอดคล้องกับ Shield)
- API / pipeline ส่ง risk_reward ต่อเนื่อง

## Arch A4 — Watchman (เสร็จ)

- plan_entry จาก SizedOrder (initial trailing = stop_loss)
- activate: PENDING → OPEN (paper fill simulation)
- update_price(current_price): 
  - ตรวจ hard stop / take_profit → CLOSED
  - promote OPEN → TRAILING เมื่อมีกำไร
  - ปรับ trailing_stop ขึ้น (long) หรือลง (short) ตามราคา
  - ใช้ initial risk distance (จาก CFO) เป็นฐาน trail
- States: PENDING → OPEN → TRAILING → CLOSED
- paper_mode รองรับ (เริ่มด้วย paper ก่อน live)
- LivePosition มี action + helper (unrealized_pnl_pct)

## Arch A5 — Auditor (เสร็จ)

- autopsy_trade: รับราคา entry/exit/stop → คำนวณ pnl_pct + r_multiple อัตโนมัติ
- _auto_analyze: สร้าง lessons/mistakes/strengths จาก outcome + metrics (rule-based)
- propose_strategy → StrategyCandidate (เริ่มที่ CANDIDATE)
- promote / attach_backtest_results / review_and_promote: จัดการ pipeline CANDIDATE → BACKTEST → SANDBOX → LIVE
- autopsy_from_position: รับ LivePosition (ปิดแล้ว) + setup context
- pipeline มี audit_closed_position() hook สำหรับ post-watchman
- ใช้ backtest_metrics จาก BacktestEngine ได้

## ถัดไป

**Arch A7 Production Release** — Connect sandbox paper trading to real API endpoints for Live execution.

## Quick Reference

### เริ่ม/หยุด (ให้ AI รัน)

```bash
# เริ่ม
lsof -ti:8080 | xargs kill -9 2>/dev/null; lsof -ti:5173 | xargs kill -9 2>/dev/null
cd "/Users/kaaimac/Desktop/AI Agent trading Office" && ./start.sh

# หยุด
lsof -ti:8080 | xargs kill -9 2>/dev/null; lsof -ti:5173 | xargs kill -9 2>/dev/null
```

### API สำคัญ

| Method | Path |
|--------|------|
| GET | `/api/health` |
| GET | `/api/status` |
| GET | `/api/pipeline/info` |
| POST | `/api/council/evaluate` |
| POST | `/api/pipeline/run` |
| POST | `/api/meetings/run` |
| POST | `/api/meetings/{id}/approve` |
| POST | `/api/backtest/run` |
| GET | `/api/portfolio/latest` |

### Changelog

- **2026-06-25** — Arch A6 Rebalance Trigger & Paper Portfolio: Integrated "Initiate AI Agent Rebalance Meeting" button, loading/progress visual states, and pending rebalance cards to automatically execute approved trades at live Market Open prices via yfinance.
- **2026-06-25** — Arch A6 Dashboard: 5-module UI visualization with interactive active position trailing stops simulator, real scanners breakdown, and autopsy reviews
- **2026-06-25** — Arch A5 Auditor: rich autopsy + auto lessons, r-multiple, strategy promotion loop (CANDIDATE→LIVE), pipeline hook
- **2026-06-25** — Arch A4 Watchman: trailing stops, state machine, activate + update_price, paper-first
- **2026-06-25** — Arch A3 CFO: volatility-aware 1% risk sizing, dynamic stops, RRR TP
- **2026-06-25** — Arch A2 Shield: RRR, grade, sector overlap + current_sectors support
- **2026-06-25** — Arch A1 Brain + rename phase docs (Build vs Arch)
- **2026-06-25** — Arch A0 foundation, slim docs
- **2026-06-21** — Build B4 tests
- **2026-06-20** — Build B1–B3, dashboard, LLM