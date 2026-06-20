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

### สถานะ logic ปัจจุบัน
- Agent ทุกตัวยังใช้ **placeholder scoring** (รอเชื่อมข้อมูลจริง)
- Portfolio Manager ใช้ **rule-based** ตัดสินใจ (รอ Grok API)
- ยังไม่มี Backtest Engine

### แผนพัฒนาต่อ (Roadmap) — ทำตามลำดับนี้

> **ครั้งถัดไปที่กลับมาทำ: เริ่มจาก Phase 1**

#### Phase 1 — Backtest Engine (สำคัญที่สุด) ← เริ่มที่นี่
เป้าหมาย: จำลองพอร์ตตามกฎ TRADING-RULES.md แล้วเทียบกับ Tech Titans

- [ ] สร้างโฟลเดอร์ `backtest/` — engine จำลองพอร์ต
  - เงินทุน 305 USD วันที่ 1 ของเดือน
  - ปรับพอร์ตได้ทุกสัปดาห์ (ใช้เงินสด + เงินจากขายเท่านั้น ระหว่างเดือน)
  - เทรดเฉพาะหุ้นเทค (NYSE + Nasdaq)
- [ ] โหลดข้อมูล benchmark จาก `data/tech_titans_history_template.csv` (733 แถว)
- [ ] รัน backtest ย้อนหลัง แล้วคำนวณ return / alpha เทียบ Tech Titans
- [ ] เชื่อม **Backtester & Evaluator** กับผล backtest จริง
  - ส่ง `portfolio_return`, `benchmark_return` เข้า `context.extra`
- [ ] แสดงผลเบื้องต้นบน Dashboard (หรือ terminal report)

#### Phase 2 — ข้อมูลจริงให้ Agent
เป้าหมาย: แทน placeholder scoring ด้วยข้อมูลจริง

- [ ] **Financial Analyst** — ใช้ metric จาก CSV (PE, margin, revenue, FCF yield ฯลฯ)
- [ ] **Market Researcher** — ดึงราคาหุ้น historical (yfinance / API อื่น)
- [ ] **News Researcher** — ข่าว + sentiment (Grok API หรือ news API)
- [ ] **Risk Manager** — น้ำหนักพอร์ตจริงจาก backtest engine

#### Phase 3 — Grok API + Semi-Auto
เป้าหมาย: ให้ agent อภิปรายและตัดสินใจด้วย LLM + คนอนุมัติก่อน execute

- [ ] ผสาน **Grok 4.3 API** ให้ Portfolio Manager อภิปรายจาก report จริง (แทน rule-based)
- [ ] เพิ่มปุ่ม **Approve / Reject** บน Dashboard (semi-auto mode)
- [ ] บันทึกสถานะอนุมัติลง Decision Log (`approved: true/false`)

#### Phase 4 — ปรับปรุง Dashboard
เป้าหมาย: ทำให้ monitor และควบคุมระบบได้ครบจาก UI

- [ ] กราฟ performance AI Agent vs Tech Titans
- [ ] แสดงพอร์ตปัจจุบัน (holdings, cash, return)
- [ ] ปุ่มรัน backtest ย้อนหลังจาก UI
- [ ] ปรับปรุง Pixel Office ให้สะท้อนสถานะ backtest/live ได้ชัดขึ้น

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
- Multi-Agent + Dashboard พร้อมใช้งาน (placeholder data)
- CSV Tech Titans 733 แถว พร้อมสำหรับ Phase 1 Backtest
- Meeting transcript บันทึกครบ 4 phase (opening → report → deliberation → decision)
- **ถัดไป: Phase 1 — Backtest Engine** (ดู Roadmap ด้านบน)
