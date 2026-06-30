# AI Agent Trading Office

ทีม AI เทรดหุ้นเทค US แข่ง **Tech Titans** · Semi-Auto

## สองชุด Phase (สำคัญ)

- **Build B1–B4** — ระบบเดิมที่รันได้แล้ว (backtest, meeting, dashboard)
- **Arch A0–A6** — สถาปัตยกรรม 5 modules ใหม่ (ตอนนี้ถึง **A5 Auditor** ✅)

ดูรายละเอียด: [PROGRESS-LOG.md](PROGRESS-LOG.md) · [AGENTS.md](AGENTS.md)

## Quick Start

```bash
cd "/Users/kaaimac/Desktop/AI Agent trading Office"
pip3 install -r requirements.txt
cd dashboard && npm install && cd ..
./start.sh
```

- Dashboard: http://127.0.0.1:5173
- API: http://127.0.0.1:8080

คำสั่งกับ AI: `เริ่มโปรแกรม` / `หยุดโปรแกรม`

## คำสั่ง

```bash
./start.sh                    # API + Dashboard
python3 main.py               # Build: legacy weekly meeting
python3 -m backtest           # Build B1: backtest
python3 -m unittest discover -s tests -v
curl -X POST http://127.0.0.1:8080/api/council/evaluate \
  -H 'Content-Type: application/json' -d '{"ticker":"AAPL"}'   # Arch A1
```

Tests ครั้งแรก: `pip3 install -r requirements-dev.txt`

## เอกสาร

| ไฟล์ | เนื้อหา |
|------|--------|
| [AGENTS.md](AGENTS.md) | 5 modules, council, Arch roadmap |
| [TRADING-RULES.md](TRADING-RULES.md) | กฎเงินทุน + pipeline gates |
| [PROGRESS-LOG.md](PROGRESS-LOG.md) | Build B* / Arch A* status |

## Stack

Python · FastAPI · React/Vite · yfinance · Tech Titans CSV · LLM (optional)