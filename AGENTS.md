# AI Agent Trading Office — Architecture

ตลาด: **หุ้นเทค US** · Benchmark: **Tech Titans** · โหมด: **Semi-Auto**

## Phase คืออะไร?

| ชุด | ชื่อ | ใช้เมื่อ |
|-----|------|---------|
| **Build B1–B4** | ระบบเดิม (เสร็จแล้ว) | backtest, meeting 6 agents, dashboard |
| **Arch A0–A6** | สถาปัตยกรรม 5 modules | Brain → Shield → CFO → Watchman → Auditor |

รายละเอียดสถานะ: [PROGRESS-LOG.md](PROGRESS-LOG.md)

## Pipeline (Arch — บังคับ)

```
Scan/Setup → Brain → Shield → CFO → Watchman → (Auditor หลังปิดไม้)
```

**Gate:** ทุกสัญญาณต้องผ่าน **The Brain** ก่อนเสมอ

## 5 Modules

| Module | ชื่อ | หน้าที่ |
|--------|------|--------|
| `modules/brain/` | The Brain | AI Council + scanners + A+ Setup |
| `modules/shield/` | The Shield | RRR, sector overlap, GO/PASS |
| `modules/cfo/` | The CFO | shares จาก % risk, volatility |
| `modules/watchman/` | The Watchman | trailing stop (paper → live) |
| `modules/auditor/` | The Auditor | autopsy → backtest → sandbox → live |

## AI Council (Arch A1 — Brain)

| สมาชิก | บทบาท |
|--------|--------|
| Bear | มองแง่ลบ |
| Bull | มองแง่บวก |
| Risk Chair | บริหารความเสี่ยง — **VETO ได้** |

**ผ่านสภา:** APPROVE ≥ 2/3 และ Risk Chair ไม่ veto

## Scanners (Arch A1)

| แนวคิด | หุ้น US | น้ำหนัก |
|--------|---------|--------|
| Fundamental | Tech Titans CSV | 25% |
| CSM → Sector | เทียบ QQQ | 20% |
| SMC → Structure | SMA, RSI, 52w | 30% |
| News | yfinance | 25% |

## Legacy Build (B1–B4)

Meeting รายสัปดาห์: `agents/` + `core/orchestrator.py` — ยังใช้ได้

| Agent เดิม | → Module ใหม่ |
|------------|--------------|
| Financial Analyst | Brain |
| Market / News Researcher | Brain |
| Risk Manager | Brain + CFO + Shield |
| Portfolio Manager | Shield |
| Backtester | Auditor |

## Arch Roadmap

| Arch | สถานะ | เนื้อหา |
|------|--------|--------|
| A0 Foundation | ✅ | models, pipeline, docs |
| A1 Brain | ✅ | Council + scanners + API |
| A2 Shield | ✅ | RRR, overlap |
| A3 CFO | ✅ | sizing |
| A4 Watchman | ✅ | paper, trailing |
| A5 Auditor | ✅ | autopsy loop |
| A6 Dashboard | ⏳ | 5-module UI |

## โค้ดหลัก

```
modules/              # Arch A0+
  brain/              # Arch A1 ✅
  pipeline.py
agents/               # Build B1–B3 legacy
backtest/             # Build B1
server/app.py         # /api/council/evaluate, /api/pipeline/run
```