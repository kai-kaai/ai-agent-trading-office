# Trading Rules

> Phase ในไฟล์นี้: **Build** = กฎพอร์ตเดิม · **Arch** = pipeline 5 modules ใหม่

## Capital (Build)
- **305 USD** วันที่ 1 ของทุกเดือน
- ระหว่างเดือน: เงินสด + เงินจากขายเท่านั้น

## Tech Titans — Benchmark (Build)
- ปรับพอร์ต **เดือนละ 1 ครั้ง**
- ~15 หุ้นเทค · ขาย 5 / ซื้อใหม่ 5 + 305 USD

## AI Agent (Build)
- ปรับพอร์ต **ทุกสัปดาห์**
- หุ้นเทค NYSE + Nasdaq · สูงสุด 15 ตัว
- เป้าหมาย: แข่ง Tech Titans 6 เดือน

## Arch Pipeline Gates (ทุกไม้ใหม่)

| ขั้น | Module | กฎ |
|------|--------|-----|
| A1 | Brain | Council 2/3 approve, Risk Chair ไม่ veto |
| A2 | Shield | RRR + sector overlap → GO |
| A3 | CFO | ขนาดหุ้นจาก % risk NAV |
| A4 | Watchman | ดูแลหลังเปิด (paper ก่อน) |
| A5 | Auditor | autopsy → กลยุทธ์ใหม่ |

## Strategy Promotion (Arch A5)

```
Candidate → Backtest → Paper 30 วัน → Live (semi-auto approve)
```

Fail ขั้นใด → reject

## Rule-Based Fallback Mode
- หากไม่มีการติดตั้ง LLM ระบบจะประเมินคะแนนของหุ้น Watchlist จากตัวแทน 3 ด้าน (พื้นฐาน, ข่าว, เทคนิคัล) โดยมีเกณฑ์:
  - **BUY**: คะแนนเฉลี่ยรวมกัน $\ge 60$ คะแนน (ปรับปรุงเพื่อความกระฉับกระเฉงในการลงเงิน)
  - **SELL**: คะแนนเฉลี่ยรวมกัน $< 40$ คะแนน
  - เงินสดคงเหลือจะเฉลี่ยเท่ากัน (Equal-Weight) เพื่อซื้อหุ้นผ่านเกณฑ์เหล่านั้น

---
*อัปเดต: 1 กรกฎาคม 2026*