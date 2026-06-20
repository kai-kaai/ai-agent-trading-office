# Project Progress Log - AI Agent Trading Office

ไฟล์นี้ใช้บันทึกความคืบหน้าคร่าว ๆ ของโปรเจค เพื่อให้สามารถต่อยอดได้เมื่อกลับมาคุยใหม่

## 2026-06-19

- สร้างโฟลเดอร์โปรเจคที่ Desktop
- สร้างไฟล์ README.md (ภาพรวมโปรเจค)
- สร้างไฟล์ AGENTS.md (โครงสร้าง Agent)
- สร้างไฟล์ TRADING-RULES.md (กฎการเทรด)
  - เงินทุน 305 USD ทุกวันที่ 1
  - Tech Titans ปรับเดือนละครั้ง
  - Agent ปรับได้ทุกสัปดาห์ (semi-auto)
  - ขอบเขต: หุ้นเทคโนโลยีทั้ง NYSE และ Nasdaq (เหมือน Tech Titans จริง ๆ)
- ตกลงแนวทางการพัฒนา: เริ่มจาก Backtest ก่อน
- ยังรอข้อมูล Historical Tech Titans จากผู้ใช้
- ได้รับภาพ screenshot แรก (May 2026) และบันทึกข้อมูลลง CSV ครบทุกคอลัมน์

## สถานะปัจจุบัน
- ยังอยู่ในขั้นตอนวางแผนและเตรียมข้อมูล
- มีข้อมูล Tech Titans เดือนพฤษภาคม 2026 แล้ว 15 ตัว

---
*ไฟล์นี้จะถูกอัพเดทเรื่อย ๆ*
## 2026-06-19 (ต่อ)
- ได้รับ screenshot เดือนมีนาคม 2026 (Mar 2026)
- บันทึกข้อมูลหุ้น 17 ตัวลง CSV เรียบร้อยแล้ว
- CSV ปัจจุบันมีข้อมูล 3 เดือน: มีนาคม, เมษายน, พฤษภาคม 2026

## สถานะล่าสุด
- มีข้อมูล Tech Titans ครบ 3 เดือนแล้ว
- พร้อมที่จะเริ่มขั้นตอนต่อไป (Backtest หรือสร้าง Agent)

## 2026-06-19 (อัพเดท)
- Screenshot เดือนมีนาคม 2026 อยู่ที่: ~/Documents/screenshot/SCR-20260619-rwgm.png
- ตรวจสอบจำนวนหุ้นแต่ละเดือน:
  - มีนาคม 2026: 15 ตัว (ครบ)
  - เมษายน 2026: 15 ตัว (ครบ)
  - พฤษภาคม 2026: 15 ตัว (ครบ)
- แก้ไขปัญหา newline หายตอน append ข้อมูล (บรรทัด April ติดกับ March)

## 2026-06-19 (ต่อ)
- ได้รับ screenshot เดือนกุมภาพันธ์ 2026 จาก ~/Documents/screenshot/SCR-20260619-sbpf.png
- เพิ่มข้อมูล 15 ตัว เดือนกุมภาพันธ์ 2026 ลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล 4 เดือน: กุมภาพันธ์, มีนาคม, เมษายน, พฤษภาคม 2026

## 2026-06-19 (ต่อ)
- ได้รับ screenshot เดือนมกราคม 2026 จาก ~/Documents/screenshot/SCR-20260619-scou.png
- เพิ่มข้อมูล 15 ตัว เดือนมกราคม 2026 ลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล 5 เดือน: มกราคม ถึง พฤษภาคม 2026

## 2026-06-19 (ต่อ)
- ส่ง screenshot 4 เดือนพร้อมกัน (Sep, Oct, Nov, Dec 2025)
- เพิ่มข้อมูลครบ 4 เดือน (60 แถว) ลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล 9 เดือน (มกราคม 2025 ถึง ธันวาคม 2025 + มกราคม-พฤษภาคม 2026)

## 2026-06-19 (ต่อ)
- ส่ง screenshot อีก 4 เดือน (May, Jun, Jul, Aug 2025)
- เพิ่มข้อมูลครบ 4 เดือน (60 แถว) ลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล 13 เดือน (พฤษภาคม 2025 ถึง พฤษภาคม 2026)

## 2026-06-19 (ต่อ)
- ส่ง screenshot อีก 4 เดือน (Jan, Feb, Mar, Apr 2025)
- เพิ่มข้อมูลครบ 4 เดือน (60 แถว) ลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล **17 เดือน** (มกราคม 2025 ถึง พฤษภาคม 2026) ครบ 1 ปีเต็ม

## 2026-06-19 (ต่อ)
- เรียงลำดับข้อมูลใน CSV ใหม่ โดยให้เดือนล่าสุดอยู่บนสุด (descending order)
- ปัจจุบันมีข้อมูล 255 แถว (17 เดือน)

## 2026-06-19 (ต่อ)
- ส่ง screenshot ปี 2024 ทั้ง 12 เดือน (Jan–Apr 2024 ประมวลผลแล้ว 4 เดือนแรก)
- เพิ่มข้อมูล 4 เดือน (มกราคม – เมษายน 2024) ลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล 21 เดือน (มกราคม 2024 ถึง พฤษภาคม 2026)

## 2026-06-19 (ต่อ)
- ประมวลผลครบ 12 เดือนของปี 2024 (มกราคม – สิงหาคม 2024 เพิ่มเติม)
- เพิ่มข้อมูล 8 เดือน (พฤษภาคม – สิงหาคม 2024) ลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล **25 เดือน** (มกราคม 2024 ถึง พฤษภาคม 2026) ครบ 1 ปี 5 เดือน

## 2026-06-19 (ต่อ)
- ประมวลผลครบ 12 เดือนของปี 2024 (กันยายน – ธันวาคม 2024 เพิ่มเติม)
- เพิ่มข้อมูล 4 เดือนสุดท้าย (กันยายน – ธันวาคม 2024) ลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล **29 เดือน** (มกราคม 2024 ถึง พฤษภาคม 2026) ครบ 1 ปี 5 เดือน

## 2026-06-19 (ต่อ)
- เรียงลำดับข้อมูลใน CSV ใหม่ โดยให้เดือนล่าสุดอยู่บนสุด (descending order)
- ปัจจุบันมีข้อมูล 434 แถว (29 เดือน)

## 2026-06-19 (ต่อ)
- ส่ง screenshot ปี 2023 4 เดือน (กันยายน – ธันวาคม 2023)
- เพิ่มข้อมูล 4 เดือนลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล 33 เดือน (กันยายน 2023 ถึง พฤษภาคม 2026)

## 2026-06-19 (ต่อ)
- ส่ง screenshot ปี 2023 อีก 4 เดือน (พฤษภาคม – สิงหาคม 2023)
- เพิ่มข้อมูล 4 เดือนลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล 37 เดือน (พฤษภาคม 2023 ถึง พฤษภาคม 2026)

## 2026-06-19 (ต่อ)
- ส่ง screenshot ปี 2023 อีก 4 เดือน (มกราคม – เมษายน 2023)
- เพิ่มข้อมูล 4 เดือนลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล 41 เดือน (มกราคม 2023 ถึง พฤษภาคม 2026)

## 2026-06-19 (ต่อ)
- เรียงลำดับข้อมูลใน CSV ใหม่ โดยให้เดือนล่าสุดอยู่บนสุด (descending order)
- ปัจจุบันมีข้อมูล 613 แถว (41 เดือน)

## 2026-06-19 (ต่อ)
- ส่ง screenshot ปี 2022 4 เดือน (กันยายน – ธันวาคม 2022)
- เพิ่มข้อมูล 4 เดือนลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล 45 เดือน (กันยายน 2022 ถึง พฤษภาคม 2026)

## 2026-06-19 (ต่อ)
- ส่ง screenshot ปี 2022 อีก 4 เดือน (พฤษภาคม – สิงหาคม 2022)
- เพิ่มข้อมูล 4 เดือนลง CSV เรียบร้อย
- CSV ปัจจุบันมีข้อมูล 49 เดือน (พฤษภาคม 2022 ถึง พฤษภาคม 2026)

## 2026-06-19 (ต่อ)
- เรียงลำดับข้อมูลใน CSV ใหม่ โดยให้เดือนล่าสุดอยู่บนสุด (descending order) อีกครั้ง
- ปัจจุบันมีข้อมูล 747 แถว (ข้อมูลย้อนหลังหลายปี)

## 2026-06-19 (ต่อ)
- ลบข้อมูลเดือนมกราคม 2022 ออกจาก CSV เรียบร้อย (14 แถว)
- CSV ปัจจุบันมีข้อมูล 733 แถว

## 2026-06-20

### โครงสร้าง Multi-Agent System
- แยก `core/` (models, base_agent, orchestrator, decision_log) กับ `agents/` (role implementations)
- สร้าง Agent ครบ 6 roles ตาม AGENTS.md:
  - Portfolio Manager, Financial Analyst, News Researcher
  - Market Researcher, Risk Manager, Backtester & Evaluator
- สร้าง `agents/registry.py` สำหรับลงทะเบียนและขยาย agent
- Decision Log บันทึกทั้ง JSON + Markdown พร้อม meeting transcript (4 phases)

### Web UI & Dashboard
- สร้าง `server/` — FastAPI REST API + WebSocket (pixel-agents protocol bridge)
- สร้าง `dashboard/` — React + Vite dashboard
  - แท็บ: Pixel Office, Live Meeting, Agents, Decision Log
- สร้าง `start.sh` สำหรับรันผ่าน terminal (ไม่ต้องใช้ VS Code)
- ทดสอบเปิด Dashboard ที่ http://127.0.0.1:5173 สำเร็จ

### Phase 1 — Backtest Engine ✅ (เสร็จ 2026-06-20)

เป้าหมาย: จำลองพอร์ตตามกฎ TRADING-RULES.md แล้วเทียบกับ Tech Titans

- [x] สร้างโฟลเดอร์ `backtest/` — engine จำลองพอร์ต
- [x] โหลดข้อมูล benchmark จาก `data/tech_titans_history_template.csv` (733 แถว, 49 เดือน)
- [x] รัน backtest 6 เดือน คำนวณ return / alpha เทียบ Tech Titans
- [x] เชื่อม **Backtester & Evaluator** กับผล backtest จริง (`context.extra`)
- [x] แสดงผลบน Dashboard แท็บ **Backtest** + CLI `python3 -m backtest`

**ผล backtest ล่าสุด (ธ.ค. 2025 – พ.ค. 2026):**
- AI Agent: -3.79% | Tech Titans: -1.36% | Alpha: -2.42%
- ใช้ market cap จาก CSV เป็น price proxy (offline-friendly)

**ไฟล์สำคัญ:** `backtest/engine.py`, `backtest/strategy.py`, `backtest/context.py`

---

### Phase 2 — ข้อมูลจริงให้ Agent ✅ (เสร็จ 2026-06-20)

- [x] **Financial Analyst** — คะแนนจาก CSV (PE, FCF yield, margin ฯลฯ) ผ่าน `core/data/fundamentals.py`
- [x] **Market Researcher** — RSI, SMA, trend จาก **yfinance** ผ่าน `core/data/market_data.py`
- [x] **News Researcher** — headline sentiment จาก yfinance + momentum fallback ผ่าน `core/data/news.py`
- [x] **Risk Manager** — น้ำหนักพอร์ต + drawdown จาก backtest engine ผ่าน `core/data/context_builder.py`

**หมายเหตุ:** พอร์ตใน meeting ใช้ราคา CSV (สอดคล้อง backtest); yfinance ใช้เฉพาะ technical/news

---

### Phase 3 — LLM + Semi-Auto ✅ (เสร็จ 2026-06-20)

- [x] Portfolio Manager อภิปรายด้วย LLM (fallback rule-based เมื่อไม่มี key)
- [x] ปุ่ม **Approve / Reject** บน Dashboard (semi-auto mode)
- [x] บันทึกสถานะอนุมัติลง Decision Log (`approved`, `approval_status`)

**API อนุมัติ:**
- `GET /api/meetings/pending`
- `POST /api/meetings/{meeting_id}/approve` body: `{"approved": true|false}`

---

### Multi-Provider LLM ✅ (เสร็จ 2026-06-20)

รองรับหลาย provider ผ่าน `core/llm/` — ไม่บังคับใช้ Grok อย่างเดียว

| Provider | Env Key | Model เริ่มต้น |
|----------|---------|----------------|
| grok | `XAI_API_KEY` | grok-4.3 |
| openai | `OPENAI_API_KEY` | gpt-4o |
| deepseek | `DEEPSEEK_API_KEY` | deepseek-chat |
| anthropic | `ANTHROPIC_API_KEY` | claude-sonnet-4-6 |
| ollama | ไม่ต้องมี key | llama3.1 |

- ไม่มี API key → ระบบรันได้, PM ใช้ rule-based
- Auto-detect provider จาก key ที่มี (ถ้าไม่ตั้ง `LLM_PROVIDER`)
- ดู `.env.example` สำหรับตัวอย่าง config ครบ

---

### Phase 4 — ปรับปรุง Dashboard ← ถัดไป

เป้าหมาย: ทำให้ monitor และควบคุมระบบได้ครบจาก UI

- [ ] กราฟ performance AI Agent vs Tech Titans (time series)
- [ ] แสดงพอร์ตปัจจุบัน (holdings, cash, return) บน Dashboard
- [ ] ปรับปรุง Pixel Office ให้สะท้อนสถานะ backtest/live ได้ชัดขึ้น
- [x] ปุ่มรัน backtest ย้อนหลังจาก UI (แท็บ Backtest มีแล้ว)

### วิธีรัน server เมื่อกลับมาทำต่อ

**แบบง่าย (แนะนำ) — คำสั่งเดียว:**
```bash
cd "/Users/kaaimac/Desktop/AI Agent trading Office"
./start.sh
```
แล้วเปิด browser: http://127.0.0.1:5173
(อย่าปิด Terminal ที่รัน start.sh อยู่)

**แบบแยก 2 Terminal (ถ้า start.sh มีปัญหา):**

Terminal 1 — API backend:
```bash
cd "/Users/kaaimac/Desktop/AI Agent trading Office"
python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8080
```

Terminal 2 — React dashboard:
```bash
cd "/Users/kaaimac/Desktop/AI Agent trading Office/dashboard"
npm run dev
```
แล้วเปิด http://127.0.0.1:5173

**ถ้า port ถูกใช้อยู่แล้ว:**
```bash
lsof -ti:8080 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
```

**รัน meeting ผ่าน terminal (ไม่เปิด browser):**
```bash
cd "/Users/kaaimac/Desktop/AI Agent trading Office"
python3 main.py
```

## สถานะล่าสุด (2026-06-20)

### สรุปสั้น ๆ
- ✅ Phase 1–3 + Multi-Provider LLM เสร็จแล้ว
- ⏳ **ถัดไป: Phase 4** — กราฟ performance, holdings view, ปรับ Pixel Office
- ระบบรันได้โดย **ไม่ต้องมี API key** (rule-based PM)
- ใส่ LLM key แล้ว PM จะฉลาดขึ้น (เลือก provider ได้)

### โครงสร้างโปรเจค (ปัจจุบัน)

```
AI Agent trading Office/
├── agents/           # Agent 6 roles + portfolio_manager
├── backtest/         # Backtest engine (Phase 1)
├── core/
│   ├── data/         # fundamentals, market_data, news, context_builder
│   ├── llm/          # multi-provider LLM (grok, openai, deepseek, anthropic, ollama)
│   ├── models.py, orchestrator.py, decision_log.py
├── dashboard/        # React + Vite (แท็บ: Office, Meeting, Backtest, Agents, Logs)
├── data/
│   └── tech_titans_history_template.csv   # 733 แถว
├── logs/decisions/   # JSON + Markdown meeting logs
├── server/           # FastAPI + WebSocket
├── main.py           # CLI meeting
├── start.sh          # รัน API + Dashboard
├── .env.example      # ตัวอย่าง config LLM
├── AGENTS.md, TRADING-RULES.md, README.md
└── PROGRESS-LOG.md   # ไฟล์นี้
```

### Dependencies

```bash
pip3 install -r requirements.txt   # fastapi, uvicorn, yfinance
cd dashboard && npm install          # ครั้งแรกเท่านั้น
```

`requirements.txt`: fastapi, uvicorn, websockets, yfinance

---

## คู่มือใช้งานด่วน (Quick Reference)

### คำสั่งสำหรับ AI Assistant (สำคัญ)

> **ถ้าผู้ใช้พิมพ์ว่า `เริ่มโปรแกรม`** — ให้ assistant รันคำสั่งนี้เองทันที (ไม่ต้องบอกให้ user รัน):

```bash
lsof -ti:8080 | xargs kill -9 2>/dev/null; lsof -ti:5173 | xargs kill -9 2>/dev/null; cd "/Users/kaaimac/Desktop/AI Agent trading Office" && ./start.sh
```

รันใน background แล้วแจ้ง user ว่าเปิดได้ที่:
- Dashboard: http://127.0.0.1:5173
- API: http://127.0.0.1:8080

> **ถ้าผู้ใช้พิมพ์ว่า `หยุดโปรแกรม`** — ให้ assistant รัน:

```bash
lsof -ti:8080 | xargs kill -9 2>/dev/null; lsof -ti:5173 | xargs kill -9 2>/dev/null
```

---

### รันระบบ (ด้วยตัวเอง)

```bash
cd "/Users/kaaimac/Desktop/AI Agent trading Office"
./start.sh
```

- Dashboard: http://127.0.0.1:5173
- API: http://127.0.0.1:8080
- อย่าปิด Terminal ที่รัน start.sh

**ถ้า port ถูกใช้:**
```bash
lsof -ti:8080 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
```

### รัน Backtest

```bash
python3 -m backtest              # default 6 เดือน
python3 -m backtest --months 12
```

หรือ Dashboard → แท็บ **Backtest** → Run Backtest

### รัน Meeting

**ผ่าน Dashboard:** แท็บ Live Meeting → Run Weekly Meeting → Approve/Reject

**ผ่าน Terminal:**
```bash
python3 main.py
```

### ตั้งค่า LLM (ไม่บังคับ)

```bash
cp .env.example .env
# แก้ .env ใส่ provider + API key
./start.sh   # restart
```

ตัวอย่าง DeepSeek:
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxxxxxx
```

ตรวจสอบสถานะ: `curl http://127.0.0.1:8080/api/status`

### API Endpoints สำคัญ

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET | `/api/health` | health check |
| GET | `/api/status` | LLM provider, semi-auto status |
| GET | `/api/agents` | รายชื่อ agent |
| POST | `/api/meetings/run` | รัน weekly meeting |
| GET | `/api/meetings` | รายการ meeting log |
| GET | `/api/meetings/pending` | meeting รออนุมัติ |
| POST | `/api/meetings/{id}/approve` | อนุมัติ/ปฏิเสธ |
| POST | `/api/backtest/run` | รัน backtest |
| GET | `/api/backtest/latest` | ผล backtest ล่าสุด |
| WS | `/ws` | Pixel Agents WebSocket |

### Dashboard แท็บ

| แท็บ | หน้าที่ |
|------|--------|
| Pixel Office | ออฟฟิศ pixel + meeting ย่อ |
| Live Meeting | transcript + Approve/Reject |
| Backtest | AI vs Tech Titans metrics |
| Agents | รายละเอียด agent |
| Decision Log | ประวัติ meeting JSON/MD |

### Meeting Flow (4 phases)

1. **Opening** — Portfolio Manager สรุปพอร์ต
2. **Report** — Agent 5 ตัวส่งรายงาน (ข้อมูลจริง)
3. **Deliberation** — PM สังเคราะห์ (LLM หรือ rule-based)
4. **Decision** — PM เสนอ trades → รอ human Approve/Reject

### กฎการเทรด (สรุป)

ดูรายละเอียดใน `TRADING-RULES.md`

- เงินทุน **305 USD** วันที่ 1 ของเดือน
- AI Agent ปรับพอร์ตได้ **ทุกสัปดาห์** (Tech Titans ปรับเดือนละครั้ง)
- ระหว่างเดือน ใช้เฉพาะเงินสด + เงินจากขาย
- เทรดเฉพาะหุ้นเทค NYSE + Nasdaq, สูงสุด 15 ตัว
- เป้าหมายแข่ง Tech Titans 6 เดือน

### ข้อมูล Tech Titans CSV

- ไฟล์: `data/tech_titans_history_template.csv`
- 733 แถว, 49 เดือน (พ.ค. 2022 – พ.ค. 2026)
- ~15 หุ้น/เดือน, 147 tickers รวม
- คอลัมน์: PE, FCF yield, operating margin, market cap ฯลฯ

### Troubleshooting

| ปัญหา | แก้ไข |
|-------|-------|
| Port ถูกใช้ | kill 8080/5173 แล้ว `./start.sh` |
| LLM OFF | ปกติ — ใส่ key ใน `.env` ถ้าต้องการ |
| yfinance ช้า | ครั้งแรกดึงข้อมูล ~5–10 วินาที |
| Meeting ไม่ขึ้น | ตรวจ WebSocket ที่ `/ws` |
| Backtest ติดลบ | ปรับ strategy ใน `backtest/strategy.py` |

---

## บันทึกเพิ่มเติม

- Git repo อยู่ในโปรเจคแล้ว (มี `.gitignore`)
- Decision logs ถูก gitignore (`logs/decisions/*.json`) — เก็บ local
- `.env` ถูก gitignore — อย่า commit API key

### Session log

- **2026-06-20** — หยุดโปรแกรมชั่วคราว (ปิด port 8080 + 5173) รอทำ Phase 4 ต่อ
- **ถัดไป:** Phase 4 — กราฟ performance, holdings view, ปรับ Pixel Office
