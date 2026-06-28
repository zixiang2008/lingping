<div align="center">

# Lingping.Skills

### ผู้ช่วยตารางเรียน ปฏิทิน และการแจ้งเตือนสำหรับ Lingping Club

[简体中文](README.md) · [English](README.en.md) · [ไทย](README.th.md)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Agent Skill](https://img.shields.io/badge/Agent-Skill-111827)
![Languages](https://img.shields.io/badge/UI-中文%20%7C%20English%20%7C%20ไทย-0F766E)
![License](https://img.shields.io/badge/License-MIT-2563EB)

</div>

---

Lingping.Skills คือ Agent Skill สำหรับสมาชิก Lingping Club ระบบอ่านตารางเรียนและการจอง แปลงเวลาเป็นเขตเวลาที่ตั้งค่าไว้ ซิงค์กิจกรรมที่เข้าเกณฑ์ไปยัง Google Calendar และแจ้งเตือนก่อนเรียนหนึ่งชั่วโมงผ่าน Hermes, Google Calendar หรือการแจ้งเตือนของ macOS

## ความสามารถ

- สรุปคอร์สภาษาอังกฤษของวันพรุ่งนี้และการจองปัจจุบันทุกวัน
- ซิงค์คอร์สที่ลงทะเบียนแล้วทั้งหมดไปยัง Google Calendar และตั้งสถานะไม่ว่าง
- แจ้งเตือนคอร์สที่ลงทะเบียนแล้วล่วงหน้า 60 นาที
- ซิงค์คอร์สภาษาอังกฤษแบบออนไซต์และกิจกรรมแลกเปลี่ยนภาษาอังกฤษในเชียงใหม่เป็นกิจกรรมอ้างอิงแบบว่าง
- บันทึกเนื้อหาคอร์ส ผู้สอน สถานะ จำนวนที่นั่ง แหล่งที่มา และ Session ID ในรายละเอียดกิจกรรม
- อัปเดตแบบเพิ่มข้อมูลโดยใช้ Lingping Session ID เพื่อป้องกันรายการซ้ำ
- รองรับข้อความส่วนติดต่อภาษาจีน อังกฤษ และไทยด้วย `zh-CN`, `en`, `th`
- เลือกช่องทางแจ้งเตือนอัตโนมัติ: Hermes → Google Calendar → macOS
- งานอัตโนมัติเป็นแบบอ่านอย่างเดียว ไม่ลงทะเบียน ยกเลิก หรือลบกิจกรรมเอง

## กฎการซิงค์ปฏิทิน

| ประเภท | ซิงค์ | แจ้งเตือน | สถานะเวลา |
| --- | --- | --- | --- |
| คอร์สที่ลงทะเบียนแล้วทุกภาษา | ใช่ | 60 นาที | ไม่ว่าง |
| คอร์สภาษาอังกฤษออนไซต์ในเชียงใหม่ที่ยังไม่ได้ลงทะเบียน | ใช่ | ไม่มี | ว่าง |
| กิจกรรมแลกเปลี่ยนภาษาอังกฤษออฟไลน์ที่ยังไม่ได้ลงทะเบียน | ใช่ | ไม่มี | ว่าง |
| คอร์สอื่นที่ยังไม่ได้ลงทะเบียน | ไม่ | — | — |

## การติดตั้ง

```bash
mkdir -p ~/.codex/skills
cp -R .agents/skills/lingping-class-assistant ~/.codex/skills/
mkdir -p ~/.config/lingping
cp .agents/skills/lingping-class-assistant/references/config.example.json \
  ~/.config/lingping/config.json
```

## การตั้งค่า

```json
{
  "lingping_username": "your-lingping-email@example.com",
  "timezone": "Asia/Bangkok",
  "language": "th",
  "calendar_id": "primary",
  "notification": {
    "mode": "auto",
    "hermes_channel": "",
    "fallbacks": ["google_calendar", "macos_notification"],
    "avoid_duplicates": true
  }
}
```

เชื่อมต่อ Google Calendar ผ่าน OAuth อย่างเป็นทางการของ Agent ที่ใช้งาน ห้ามเก็บรหัสผ่าน Google, Cookie, access token หรือ OAuth secret ใน repository

## คำสั่งหลัก

```bash
SCRIPT="${CODEX_HOME:-$HOME/.codex}/skills/lingping-class-assistant/scripts/lingping.py"
python3 "$SCRIPT" self-test
python3 "$SCRIPT" daily --language th
python3 "$SCRIPT" bookings --language th
python3 "$SCRIPT" calendar-json --language th
python3 "$SCRIPT" notification-status --language th
python3 "$SCRIPT" reminders --language th
```

ตัวเลือก `--language` รองรับ `zh-CN`, `en`, `th` หากไม่ระบุ ระบบจะใช้ค่า `language` จากไฟล์ config

## งานอัตโนมัติที่แนะนำ

- ทุกวันเวลา 21:00: สร้างสรุปวันถัดไป อัปเดต Google Calendar และตรวจสอบช่องทางแจ้งเตือน
- ทุก 5 นาที: ตรวจสอบคอร์สที่ใกล้เริ่มเมื่อ Hermes หรือการแจ้งเตือนในเครื่องเป็นช่องทางหลัก หาก Google Calendar เป็นช่องทางหลักให้จบการทำงานแบบเงียบ

## ความปลอดภัยและข้อจำกัด

- บัญชีส่วนบุคคลอยู่ใน `~/.config/lingping/config.json` และไม่ถูก commit
- ไม่ลบกิจกรรมในปฏิทินโดยอัตโนมัติ
- หากโครงสร้างเว็บไซต์ Lingping เปลี่ยน อาจต้องอัปเดต catalog หรือ field mapping
- ช่วงตารางเรียนเป็นไปตามเว็บไซต์ ปัจจุบันประมาณเก้าวัน
- Hermes ต้องผ่าน health check และทดสอบส่งข้อความจริงก่อนเป็นช่องทางหลัก

ดูขั้นตอนสำหรับ Agent ที่ [`SKILL.md`](.agents/skills/lingping-class-assistant/SKILL.md) และรายละเอียดการเชื่อมต่อในโฟลเดอร์ `references/`

## ใบอนุญาต

MIT ชื่อ Lingping Club, Google Calendar และ Hermes เป็นของเจ้าของที่เกี่ยวข้อง โครงการนี้เป็น Skill อิสระสำหรับงานอัตโนมัติ
