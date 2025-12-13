# OPUS INPUT — BACKEND EXPORT PACK (HotelMate Booking/Party/Rooms)

Purpose:
Provide Claude Opus with *real, canonical backend outputs* so it can generate a frontend spec
without inventing fields, endpoints, or event types.

Rules:
- Paste REAL outputs from dev backend (Postman/curl/browser devtools).
- DO NOT redact field names.
- If values are sensitive, replace values only (keep keys).
- Include at least 1 example per section.
- Always include hotel_slug in every example context.

---

## 0) Environment Context (required)
Paste:
- hotel_slug used for all examples: `<hotel_slug>`
- Backend base URL: `<base_url>`
- Auth type (choose one):
  - Bearer token header (Authorization: Bearer xxx)
  - Session cookie
  - None (dev)
- Any required headers besides auth:
  - e.g. `X-Hotel-Slug`, `X-Request-Id`, etc.

---

## 1) Staff API Endpoints (exact paths + methods) — REQUIRED
List every staff endpoint involved in bookings/party/check-in/out.

Format exactly like:

### Bookings
- `GET /api/staff/hotels/{hotel_slug}/hotel/bookings/` (query params: page, status, date_from, date_to, search, etc)
- `GET /api/staff/hotels/{hotel_slug}/hotel/bookings/{booking_id}/`
- `PATCH /api/staff/hotels/{hotel_slug}/hotel/bookings/{booking_id}/party/`
- `POST /api/staff/hotels/{hotel_slug}/hotel/bookings/{booking_id}/check-in/`
- `POST /api/staff/hotels/{hotel_slug}/hotel/bookings/{booking_id}/check-out/`

### Rooms (only if used in UI Phase 1)
- `GET /api/staff/hotels/{hotel_slug}/hotel/rooms/`
- `GET /api/staff/hotels/{hotel_slug}/hotel/rooms/{room_id}/`
- Any "assign room" endpoint if separate from check-in

Add notes:
- expected status codes (200/201/400/403/404)
- validation error shape (example below)

---

## 2) Staff Booking List — REAL JSON (one response) — REQUIRED
Call the staff booking list endpoint and paste:
- full response JSON (preferred)
OR
- minimum: one item + any pagination wrapper

Include:
- the exact request URL used (with query params)
- response status code

Paste here:
```json
PASTE_BOOKING_LIST_RESPONSE_JSON
```

---

## 3) Staff Booking Detail — REAL JSON (one response) — REQUIRED

Pick one booking_id from the list and call booking detail endpoint.

Include:
- exact request URL used
- status code

Paste here:
```json
PASTE_BOOKING_DETAIL_RESPONSE_JSON
```

Must include (if present in serializer):
- party grouped (PRIMARY + companions)
- in-house guests grouped
- room assignment info
- booking status fields (checked-in/out indicators)
- capacity-related fields if returned

---

## 4) Party Update (PRIMARY + companions) — REQUEST + RESPONSE — REQUIRED

Perform a party update via PATCH.

Include:
- exact request URL
- request body JSON
- response JSON
- status code
- include a failure example if possible (e.g. second PRIMARY rejected)

Paste request:
```json
PASTE_PARTY_UPDATE_REQUEST_JSON
```

Paste success response:
```json
PASTE_PARTY_UPDATE_RESPONSE_JSON
```

Paste failure response (if available):
```json
PASTE_PARTY_UPDATE_FAILURE_RESPONSE_JSON
```

---

## 5) Check-in — REQUEST + RESPONSE (success + failure) — REQUIRED

Perform check-in for a booking that is not checked-in yet.

Include:
- exact request URL
- request body JSON (even if empty {})
- success response JSON
- failure response JSON (capacity exceeded, invalid state, etc.)
- status codes

Paste request:
```json
PASTE_CHECKIN_REQUEST_JSON
```

Paste success response:
```json
PASTE_CHECKIN_SUCCESS_RESPONSE_JSON
```

Paste failure response:
```json
PASTE_CHECKIN_FAILURE_RESPONSE_JSON
```

---

## 6) Check-out — REQUEST + RESPONSE — REQUIRED

Perform check-out for a checked-in booking.

Include:
- exact request URL
- request body JSON (even if empty)
- success response JSON
- failure response JSON if possible
- status codes

Paste request:
```json
PASTE_CHECKOUT_REQUEST_JSON
```

Paste success response:
```json
PASTE_CHECKOUT_SUCCESS_RESPONSE_JSON
```

Paste failure response (if available):
```json
PASTE_CHECKOUT_FAILURE_RESPONSE_JSON
```

---

## 7) Realtime Events — RAW ENVELOPES (2–3 examples) — REQUIRED

We need the EXACT realtime envelope shape emitted by NotificationManager.

Provide:
- channel name used (must show hotel_slug): `{hotel_slug}.booking` or `{hotel_slug}.rooms`
- event name (if Pusher has an outer event name)
- full event JSON envelope:
  `{ category, type, payload, meta }`

Minimum examples:
1. booking created OR updated
2. party updated OR check-in
3. room status updated (if used)

Paste each as:

### Example 1
- Channel: ...
- Event name (if applicable): ...
```json
PASTE_REALTIME_EVENT_EXAMPLE_1
```

### Example 2
- Channel: ...
- Event name (if applicable): ...
```json
PASTE_REALTIME_EVENT_EXAMPLE_2
```

### Example 3
- Channel: ...
- Event name (if applicable): ...
```json
PASTE_REALTIME_EVENT_EXAMPLE_3
```

**IMPORTANT:**
- `meta` should include an `id` for dedupe (preferred: `meta.event_id`)
- `meta` should include `timestamp`/`version` if present

---

## 8) Standard Error Shape (one example) — REQUIRED

Paste any common 400 validation error response from staff APIs.

```json
PASTE_STANDARD_VALIDATION_ERROR_JSON
```

---

## 9) Notes on Invariants (short list) — OPTIONAL BUT VERY HELPFUL

Write bullet points (no code) about rules you enforce in backend:
- exactly one PRIMARY
- capacity validation timing (on check-in?)
- guest.room as single source of truth
- what check-in does to create in-house guests
- what check-out does to clear them

---

**END OF EXPORT PACK**

---

## How to actually *get* these outputs (quick, practical)
- Use **Postman/Insomnia** or even your browser network tab from DRF browsable API.
- For realtime envelopes:
  - Temporarily log/print the notification payload in backend NotificationManager **once** in dev
  - Or subscribe with a tiny node script to the Pusher channel and log events

If you paste your **staff booking list URL** and tell me if you're using **Pusher**, I can also give you a tiny "listen and dump events" script — but the MD above is enough to start.
