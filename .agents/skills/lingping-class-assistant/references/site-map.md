# Lingping integration map

- Public site: `https://lingpingclub.com`
- API base currently advertised by `config.js`: `https://api.lingpingclub.com`
- Public client configuration: `/config.js`
- Public login behavior: `/js/auth.js`
- Booking behavior: `/js/booking.js`
- Schedule endpoint used by the site: `GET /reading-sessions?fromDate=YYYY-MM-DD&toDate=YYYY-MM-DD&level=LEVEL_ID`
- Future bookings endpoint used by the site: `GET /bookings/future/user/USER_ID`

Catalog IDs observed on 2026-06-29:

- Community online: `695c763e2d652e065db71030`
- Community Chiang Mai: `67eab5b337cd4b56a080743f`
- English online: `6982e63b245037c5977a9390`

Treat IDs as implementation details that may change. Repair them by inspecting the site's location selector and membership switch. Deduplicate sessions by `_id` when catalogs overlap.

