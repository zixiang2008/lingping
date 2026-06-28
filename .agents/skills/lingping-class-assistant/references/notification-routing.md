# Notification routing

Use exactly one primary delivery path for each reminder.

1. Hermes: use only when `hermes gateway status` succeeds and `notification.hermes_channel` is configured. Discover the installed CLI's exact send syntax with `hermes send --help`; do not assume a command from another Hermes version. Send one Chinese message and retain Google Calendar as a silent backup event.
2. Google Calendar: create a popup reminder 60 minutes before every booked course. This is the default when Hermes is unavailable.
3. macOS notification/alarm: use only when Google Calendar is unavailable or the user explicitly selects it. A notification is not durable if the Mac is asleep; explain this limitation. Optional sound must be explicitly enabled by the user.
4. In-thread automation notification: use only when none of the above is configured and the automation product can deliver to the current user.

Never send through Hermes and also create an active Google popup when `avoid_duplicates` is true. In that mode, keep the calendar event but remove its popup only after a real Hermes test message succeeds. If Hermes later becomes unhealthy, restore the Google popup before relying on it as fallback.

All reminder text must be Chinese and include course title, start time in the configured timezone, online/offline form, location or meeting link when available, and teacher.
