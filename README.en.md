<div align="center">

# Lingping.Skills

### Courses, calendar sync, and smart reminders for Lingping Club

[简体中文](README.md) · [English](README.en.md) · [ไทย](README.th.md)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Agent Skill](https://img.shields.io/badge/Agent-Skill-111827)
![Languages](https://img.shields.io/badge/UI-中文%20%7C%20English%20%7C%20ไทย-0F766E)
![License](https://img.shields.io/badge/License-MIT-2563EB)

</div>

---

Lingping.Skills is an Agent Skill for Lingping Club members. It reads upcoming courses and bookings, converts times to the configured timezone, synchronizes eligible events to Google Calendar, and routes one-hour reminders through Hermes, Google Calendar, or macOS notifications.

## Features

- Daily summary of tomorrow's English courses and current bookings.
- Sync every booked course to Google Calendar as busy.
- Add a 60-minute reminder to booked courses.
- Sync unbooked in-person English classes and English language exchanges in Chiang Mai as transparent reference events.
- Store course content, teacher, status, available seats, source, and Session ID in event notes.
- Incremental updates keyed by Lingping Session ID to prevent duplicates.
- Chinese, English, and Thai interface text via `zh-CN`, `en`, and `th`.
- Automatic notification routing: Hermes → Google Calendar → macOS notification.
- Read-only scheduled operation: no automatic booking, cancellation, or calendar deletion.

## Calendar policy

| Event type | Synced | Reminder | Availability |
| --- | --- | --- | --- |
| Booked courses in any language | Yes | 60 minutes | Busy |
| Unbooked in-person English in Chiang Mai | Yes | None | Free |
| Unbooked offline English language exchange | Yes | None | Free |
| Other unbooked courses | No | — | — |

## Install

```bash
mkdir -p ~/.codex/skills
cp -R .agents/skills/lingping-class-assistant ~/.codex/skills/
mkdir -p ~/.config/lingping
cp .agents/skills/lingping-class-assistant/references/config.example.json \
  ~/.config/lingping/config.json
```

The `.agents/skills/` layout can also be used as a portable project skill. Claude Code, Cursor, and OpenCode support related Agent Skills locations, but calendar connectors and automation capabilities vary by host.

## Configure

```json
{
  "lingping_username": "your-lingping-email@example.com",
  "timezone": "Asia/Bangkok",
  "language": "en",
  "calendar_id": "primary",
  "notification": {
    "mode": "auto",
    "hermes_channel": "",
    "fallbacks": ["google_calendar", "macos_notification"],
    "avoid_duplicates": true
  }
}
```

Authorize Google Calendar through the host Agent's official OAuth connector. Never store Google passwords, cookies, access tokens, or OAuth secrets in this repository.

## Commands

```bash
SCRIPT="${CODEX_HOME:-$HOME/.codex}/skills/lingping-class-assistant/scripts/lingping.py"
python3 "$SCRIPT" self-test
python3 "$SCRIPT" daily --language en
python3 "$SCRIPT" bookings --language en
python3 "$SCRIPT" calendar-json --language en
python3 "$SCRIPT" notification-status --language en
python3 "$SCRIPT" reminders --language en
```

The `--language` override accepts `zh-CN`, `en`, or `th`. Without it, the script uses `language` from the config file.

## Recommended automation

- Daily at 21:00: generate the next-day summary, update Google Calendar, and check notification health.
- Every five minutes: check imminent classes only when Hermes or a local notification is the primary route. Exit silently when Google Calendar handles reminders.

## Safety and limitations

- Personal accounts stay in `~/.config/lingping/config.json` and are not committed.
- The script discovers the public Lingping web-client configuration at runtime instead of storing it in the repository.
- Existing calendar events are never deleted automatically.
- Lingping site changes may require catalog or field-mapping updates.
- The visible schedule window follows the website's current range, approximately nine days.
- Hermes must pass a gateway health check and a real test message before becoming the primary route.

See [`SKILL.md`](.agents/skills/lingping-class-assistant/SKILL.md) for the agent workflow and the files under `references/` for integration details.

## License

MIT. Lingping Club, Google Calendar, and Hermes are trademarks or names belonging to their respective owners. This is an independent automation Skill.
