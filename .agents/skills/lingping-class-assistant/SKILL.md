---
name: lingping-class-assistant
description: Synchronize Lingping Club courses, bookings, multilingual reminders, Hermes messaging, system notifications, and Google Calendar for any configured member. Use when asked about Lingping.Skills, Chinese/English/Thai output, lingpingclub.com, tomorrow's classes, Chiang Mai in-person English events, current bookings, calendar synchronization, notification routing, nightly updates, or one-hour-before-class reminders.
---

# Lingping.Skills

Use the bundled collector as the source of truth. Present dates and times in the configured timezone. Write user-facing results in the configured language: Simplified Chinese (`zh-CN`), English (`en`), or Thai (`th`).

## Configuration and boundaries

- Website: `https://lingpingclub.com`
- Read `~/.config/lingping/config.json`. If missing, copy the shape from [references/config.example.json](references/config.example.json) and ask only for the member's Lingping username and target Google Calendar.
- Read `language` from the same config. Default to `zh-CN`. Accept `--language zh-CN|en|th` as a one-run override.
- Read schedules and bookings without asking for a password. The site's own public client performs username-only login; the collector discovers the current public client credentials at runtime.
- Connect Google Calendar through official OAuth/connector authorization. Never ask for, use, store, or repeat a Google password.
- Never book or cancel a class unless Elvis explicitly asks and confirms the exact class. This skill's scheduled routines are read-only.
- Do not print API keys, access tokens, or internal user IDs.

## Run commands

Set the script path once:

```bash
SCRIPT="${CODEX_HOME:-$HOME/.codex}/skills/lingping-class-assistant/scripts/lingping.py"
```

### Nightly update

```bash
python3 "$SCRIPT" daily
```

Language examples:

```bash
python3 "$SCRIPT" daily --language zh-CN
python3 "$SCRIPT" daily --language en
python3 "$SCRIPT" daily --language th
```

Return the command output as-is unless a short error explanation is needed. The report includes:

1. Tomorrow's complete English schedule visible across relevant Lingping catalogs.
2. Chiang Mai in-person English choices, including availability and location.
3. Online English choices.
4. Current future bookings, clearly marking tomorrow's bookings.

If no class exists in a category, report `暂无` rather than omitting the category.

### Current bookings

```bash
python3 "$SCRIPT" bookings
```

### Reminder check

```bash
python3 "$SCRIPT" reminders
```

The command emits a reminder only for a booked class beginning in 55–65 minutes. It stores sent session IDs locally to avoid duplicate reminders. If it prints nothing, send nothing.

For a manually requested fresh check that should ignore deduplication:

```bash
python3 "$SCRIPT" reminders --force
```

### Notification routing

Inspect the active route before enabling or changing reminders:

```bash
python3 "$SCRIPT" notification-status
```

In `auto` mode, select the first healthy route in this order:

1. Hermes bound communication channel.
2. Google Calendar popup 60 minutes before the booked course.
3. macOS local notification/alarm.
4. Current-thread automation notification when supported.

Use one primary route per reminder. Keep calendar events synchronized regardless of route. If `avoid_duplicates` is true, do not deliver the same reminder through multiple clients. Never consider Hermes ready merely because a binary exists; require a successful health check and a configured destination. Read [references/notification-routing.md](references/notification-routing.md) before changing routing or sending a Hermes test.

### Google Calendar synchronization

First generate the desired event set:

```bash
python3 "$SCRIPT" calendar-json
```

Use the Google Calendar connector for all reads and writes. Synchronize a bounded rolling window matching the returned items:

1. Search that window for events containing `来源：https://lingpingclub.com`.
2. Match events by the `Lingping Session ID` stored in the description. If an event already exists, update it rather than creating a duplicate.
3. For every booked item, create/update an opaque event titled `【已报名】课程名`, preserve its time and location, and set `reminders.use_default=false` with one popup override at 60 minutes.
4. For unbooked items, include only Chiang Mai in-person English classes and offline English language-exchange activities. Create/update a transparent event titled `【未报名】课程名` with `reminders.use_default=false` and no overrides.
5. Write descriptions in the configured language containing course content, teacher, booking status, seats when available, source URL, and `Lingping Session ID: <source_id>`.
6. If an existing Lingping calendar event no longer appears in the current desired set, do not delete it automatically. Report it for review unless the user explicitly authorizes deletion.
7. Before bulk creation, verify the authenticated Google profile and target calendar. The Google account password is never part of this workflow.

All calendar-facing status text and reminders must use the configured language. Preserve the original Lingping course title and source description when no authoritative translation exists.

## Automation contract

Configure two recurring jobs in `Asia/Bangkok`:

- At 21:00 daily: invoke this skill and run the nightly update.
- After the nightly update: run Google Calendar synchronization for the returned rolling window.
- Every 5 minutes: invoke this skill and run the reminder check; forward output only when non-empty.

The five-minute check gives a practical one-hour reminder window while handling classes whose start minute is not aligned to an hourly schedule. Do not report that automations exist unless the automation tool confirms creation.

## Failure handling

- Retry a transient network or 5xx failure once.
- If login or schema parsing fails, state that Lingping could not be synchronized and include the short error, without exposing credentials.
- If the website changes, inspect its current `config.js`, `js/auth.js`, homepage filters, and `js/booking.js`; then update the collector and re-run its self-test.
- See [references/site-map.md](references/site-map.md) only when repairing or extending the integration.
