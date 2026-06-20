# AI Agent Trading Office

โปรเจคสร้างทีม AI Agent สำหรับเทรดหุ้นอเมริกา โดยมีเป้าหมายแข่งกับ Tech Titans ของ investing.com

## เป้าหมายหลัก
- สร้าง Multi-Agent System ที่สามารถปรับพอร์ตได้ **ทุกสัปดาห์** (Tech Titans ปรับเดือนละครั้ง)
- ใช้ Grok 4.3 API เป็นหลัก
- เริ่มต้นด้วยการ Backtest ก่อน
- ใช้โหมด Semi-Auto (ต้องมีคนอนุมัติก่อน)

## สถานะปัจจุบัน
- ยังอยู่ในขั้นตอนวางแผนและออกแบบระบบ
- ยังไม่มีข้อมูล historical data ของ Tech Titans

## แนวทางการพัฒนา
1. Backtesting ก่อน
2. สร้าง Multi-Agent แบบ Semi-Auto
3. รันในเครื่อง local ก่อน
4. เก็บ Decision Log เพื่อให้ agent เรียนรู้จากประวัติการตัดสินใจ

## โครงสร้าง Agent (เบื้องต้น)
- Portfolio Manager (หัวหน้า)
- Financial Analyst
- News Researcher
- Market Researcher
- Risk Manager
- Backtester & Evaluator

---
*เอกสารนี้จะถูกอัพเดทเรื่อย ๆ ตามความคืบหน้าของโปรเจค*