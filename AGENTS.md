# AI Agent Trading Office - Agent Structure

เอกสารนี้อธิบายโครงสร้างของทีม Agent ในโปรเจค

## หลักการออกแบบ
- ใช้แนวคิด "AI Office" แบบมีแผนกและ role ชัดเจน
- แต่ละ Agent มีหน้าที่เฉพาะเจาะจง
- มี Portfolio Manager เป็นผู้ตัดสินใจหลัก
- ทุกครั้งที่ปรับพอร์ตจะมีการ "ประชุม" กัน

## Agent Roles (Phase 1 - Backtest)

### 1. Portfolio Manager (CEO)
- รับผิดชอบการตัดสินใจสุดท้าย
- เรียกประชุม agent อื่น ๆ
- สรุปข้อมูลและออกคำสั่งปรับพอร์ต
- รับผิดชอบ Decision Log

### 2. Financial Analyst
- วิเคราะห์งบการเงินของหุ้นที่สนใจ
- ดู metric สำคัญ: EPS, Revenue growth, Debt ratio, Profit margin
- ให้คะแนนพื้นฐานของแต่ละหุ้น

### 3. News Researcher
- ค้นหาข่าวและข้อมูลล่าสุดของบริษัท
- วิเคราะห์ sentiment จากข่าว
- รายงานเหตุการณ์สำคัญที่อาจกระทบราคา

### 4. Market Researcher
- วิเคราะห์ราคาและ technical indicator
- ดู trend, sector rotation, market condition โดยรวม
- ประเมินจังหวะการเข้า/ออก

### 5. Risk Manager
- ควบคุมความเสี่ยงของพอร์ต
- แนะนำ position sizing
- ตรวจสอบ sector concentration และ drawdown

### 6. Backtester & Evaluator
- รับผิดชอบการทดสอบย้อนหลัง
- วัดผล performance เทียบกับ Tech Titans
- วิเคราะห์ว่าการตัดสินใจแต่ละครั้งดีหรือไม่

## กระบวนการทำงาน (Weekly Cycle)
1. Portfolio Manager เรียกประชุม
2. แต่ละ Agent ส่งรายงาน
3. ประชุมและอภิปราย
4. Portfolio Manager ตัดสินใจ
5. บันทึกเหตุผลลง Decision Log
6. สรุปผลการปรับพอร์ต

---
*เอกสารนี้จะถูกปรับปรุงเมื่อมีการเพิ่ม agent หรือเปลี่ยน role*