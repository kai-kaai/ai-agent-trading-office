# AI Agent Trading Office

โปรเจคสร้างทีม AI Agent สำหรับเทรดหุ้นอเมริกา โดยมีเป้าหมายแข่งกับ **Tech Titans** ของ investing.com

## เป้าหมายหลัก

- Multi-Agent System ปรับพอร์ตได้ **ทุกสัปดาห์** (Tech Titans ปรับเดือนละครั้ง)
- Backtest เทียบ Tech Titans ก่อน live
- โหมด **Semi-Auto** — PM เสนอ trades, คนอนุมัติก่อน execute
- Portfolio Manager ใช้ **LLM** (Grok / OpenAI / DeepSeek / Claude / Ollama) หรือ rule-based fallback

## สถานะปัจจุบัน (2026-06-20)

| Phase | สถานะ | รายละเอียด |
|-------|--------|------------|
| ข้อมูล Tech Titans | ✅ | CSV 733 แถว, 49 เดือน |
| Multi-Agent + Dashboard | ✅ | 6 agents, 5 แท็บ UI |
| Phase 1 Backtest | ✅ | AI vs Tech Titans, แท็บ Backtest |
| Phase 2 Real Data | ✅ | CSV + yfinance |
| Phase 3 Semi-Auto + LLM | ✅ | Approve/Reject, multi-provider |
| Phase 4 Dashboard++ | ⏳ | กราฟ, holdings view |

ดูความคืบหน้าและคู่มือครบใน **[PROGRESS-LOG.md](PROGRESS-LOG.md)**

## Quick Start

```bash
cd "/Users/kaaimac/Desktop/AI Agent trading Office"
pip3 install -r requirements.txt
cd dashboard && npm install && cd ..
./start.sh
```

เปิด http://127.0.0.1:5173

> **คำสั่งสั้น ๆ กับ AI:** พิมพ์ `เริ่มโปรแกรม` ให้ assistant รัน `./start.sh` ให้เอง — ดูรายละเอียดใน [PROGRESS-LOG.md](PROGRESS-LOG.md)

## คำสั่งที่ใช้บ่อย

```bash
./start.sh                    # รัน API + Dashboard
python3 main.py               # รัน meeting ผ่าน terminal
python3 -m backtest           # backtest 6 เดือน
python3 -m backtest --months 12
```

## ตั้งค่า LLM (ไม่บังคับ)

ระบบรันได้โดยไม่ต้องมี API key — PM จะใช้ rule-based

```bash
cp .env.example .env
# แก้ .env แล้ว restart ./start.sh
```

รองรับ: `grok`, `openai`, `deepseek`, `anthropic`, `ollama` — ดูตัวอย่างใน `.env.example`

## โครงสร้าง Agent

| Agent | หน้าที่ | แหล่งข้อมูล |
|-------|---------|-------------|
| Portfolio Manager | ประชุม, ตัดสินใจ, LLM deliberation | LLM หรือ rule-based |
| Financial Analyst | วิเคราะห์ fundamental | Tech Titans CSV |
| Market Researcher | Technical analysis | yfinance |
| News Researcher | News sentiment | yfinance headlines |
| Risk Manager | ความเสี่ยง, concentration | backtest engine |
| Backtester & Evaluator | เทียบ Tech Titans | backtest module |

## เอกสารอ้างอิง

- [PROGRESS-LOG.md](PROGRESS-LOG.md) — ความคืบหน้า + คู่มือใช้งานครบ
- [AGENTS.md](AGENTS.md) — โครงสร้าง agent และ workflow
- [TRADING-RULES.md](TRADING-RULES.md) — กฎการเทรด (305 USD/เดือน, weekly rebalance)
- [.env.example](.env.example) — ตัวอย่าง config LLM

## Tech Stack

- **Backend:** Python 3, FastAPI, uvicorn
- **Frontend:** React + Vite
- **Data:** Tech Titans CSV, yfinance
- **LLM:** xAI Grok (default), OpenAI-compatible APIs, Anthropic Claude