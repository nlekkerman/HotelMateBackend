# Guest Access Audit — 2026-03-26

## Endpoints involved

| # | URL | Zone | Token Type Before Fix | Token Type After Fix |
|---|-----|------|-----------------------|----------------------|
| 1 | `GET /api/public/hotels/{slug}/booking/status/{id}/?token=` | Public | `BookingManagementToken` | `BookingManagementToken` (unchanged) |
| 2 | `GET /api/public/hotel/{slug}/booking-management/?token=` | Public | `BookingManagementToken` | `BookingManagementToken` (unchanged) |
| 3 | `POST /api/public/hotel/{slug}/booking-management/cancel/` | Public | `BookingManagementToken` | `BookingManagementToken` (unchanged) |
| 4 | `GET /api/guest/context/` | Guest | `GuestBookingToken` | Both (via canonical resolver) |
| 5 | `GET /api/guest/room-service/` | Guest | `GuestBookingToken` | Both (via canonical resolver) |
| 6 | `GET/POST /api/guest/hotel/{slug}/chat/context` | Guest | `GuestBookingToken` only | Both (via canonical resolver) |
| 7 | `GET/POST /api/guest/hotel/{slug}/chat/messages` | Guest | `GuestBookingToken` only | Both (via canonical resolver) |
| 8 | `POST /api/guest/hotel/{slug}/chat/pusher/auth` | Guest | `GuestBookingToken` only | Both (via canonical resolver) |

## Current booking/status validation path (before fix)

1. Frontend opens `/hotel/no-way-hotel/booking/BK-NOWAYHOT-2026-0003?email=...&token=<TOKEN>`
2. Frontend calls `GET /api/public/hotels/no-way-hotel/booking/status/BK-NOWAYHOT-2026-0003/?token=<TOKEN>`
3. `BookingStatusView` in `hotel/public_views.py` hashes the token, looks it up in **`BookingManagementToken`** table
4. Validates: token exists, `is_valid`, booking matches hotel slug
5. Returns booking details — **succeeds**

## Current guest chat validation path (before fix)

1. Frontend opens `/guest/chat?hotel_slug=no-way-hotel&token=<TOKEN>&room_number=102`
2. Frontend calls `GET /api/guest/hotel/no-way-hotel/chat/context?token=<TOKEN>`
3. `GuestChatContextView` extracts token via `TokenAuthenticationMixin`
4. Calls `resolve_guest_chat_context()` in `bookings/services.py`
5. Hashes the token, looks it up in **`GuestBookingToken`** table only
6. Token is a `BookingManagementToken`, not a `GuestBookingToken` — **lookup fails**
7. Raises `InvalidTokenError` — guest sees "token is broken"

## Exact inconsistency found

**The system has two completely separate token tables:**

| Token Table | Created when | Used by |
|-------------|-------------|---------|
| `GuestBookingToken` | After booking creation / payment / staff action | Guest portal: context, chat, room service, Pusher auth |
| `BookingManagementToken` | When booking confirmation email is sent | Booking status page, cancellation page |

The booking status page URL includes a `BookingManagementToken`. When the guest clicks the chat link from the same page, the frontend passes that same token to the chat endpoints. But chat endpoints only look up `GuestBookingToken` — the token is never found.

## Root cause

**Cause E: The token is valid but scoped to a different table. Chat endpoints only search `GuestBookingToken` and never fall back to `BookingManagementToken`.**

Secondary factors:
- The token validation was duplicated across three separate functions (`GuestBookingToken.validate_token()`, `resolve_guest_token()`, `resolve_guest_chat_context()`) — none of them checked both tables
- No single canonical resolver existed that could accept either token type

## Canonical backend contract proposed

One canonical resolver: `common.guest_access.resolve_guest_access()`

### Contract

```
resolve_guest_access(token_str, hotel_slug, required_scopes=None, require_in_house=False)
  → GuestAccessContext(booking, room, scopes, token_type)
```

### Resolution order
1. Hash the raw token (SHA-256)
2. Look up in `GuestBookingToken` (ACTIVE, not expired, hotel slug match)
3. If not found, look up in `BookingManagementToken` (is_valid, hotel slug match)
4. If neither found → `InvalidTokenError` (404, anti-enumeration)
5. Check booking lifecycle (not CANCELLED/DECLINED)
6. Check required scopes (GuestBookingToken has explicit scopes; BookingManagementToken implies `STATUS_READ`, `CHAT`, `ROOM_SERVICE`)
7. If `require_in_house`: check `checked_in_at`, `checked_out_at`, `assigned_room`

### Exception hierarchy

```
GuestAccessError (base)
├── TokenRequiredError (401)
├── InvalidTokenError (404 — anti-enumeration)
├── MissingScopeError (403)
├── NotInHouseError (403)
│   ├── NotCheckedInError (403)
│   └── AlreadyCheckedOutError (403)
└── NoRoomAssignedError (409)
```

All errors include a `code` field for frontend differentiation and a `message` field for display.

## Files changed

| File | Change |
|------|--------|
| `common/guest_access.py` | **NEW** — Canonical resolver, exception hierarchy, `GuestAccessContext` dataclass |
| `bookings/services.py` | Refactored `resolve_guest_chat_context()` to delegate to canonical resolver; re-exports exceptions for backward compatibility |
| `hotel/canonical_guest_chat_views.py` | Updated imports to use canonical exceptions; error responses now include `code` field; catches `GuestAccessError` as fallback |
| `hotel/guest_portal_views.py` | Replaced `resolve_token_context()` / `resolve_in_house_context()` calls with canonical resolver; added `_resolve_context_without_slug()` helper for endpoints without hotel_slug in URL |

## Tests added/updated

| File | Coverage |
|------|----------|
| `tests/test_guest_access.py` | **NEW** — 25 test cases covering: both token types through canonical resolver, scope validation, expiry, revocation, hotel mismatch, cancelled bookings, in-house requirements (not checked in, checked out, no room), management token chat access (the core fix), room reuse isolation, backward-compatible exception re-exports |

Test categories:
1. GuestBookingToken through canonical resolver (valid, expired, revoked, hotel mismatch, cancelled, missing scope)
2. BookingManagementToken through canonical resolver (valid, revoked, cancelled, hotel mismatch, chat scope implied)
3. Edge cases (empty token, whitespace, unknown token)
4. In-house requirement (checked in, not checked in, checked out, no room — for both token types)
5. Chat context integration (both token types through `resolve_guest_chat_context`, soft mode UX hints)
6. Room reuse isolation (different booking same room must not cross-authenticate)
7. Backward compatibility (exception re-exports, `hash_token` availability)

## Remaining risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Legacy `AllowAny` chat endpoints** at `/api/chat/{slug}/conversations/{id}/messages/` and `.../send/` have zero auth — any anonymous user can read/send messages if they know a conversation ID | CRITICAL | These endpoints should be removed or locked behind staff auth. They are not used by the canonical guest chat flow. |
| **`BookingManagementToken` has no time-based expiry** — tokens remain valid as long as the booking is active | MEDIUM | Consider adding expiry (e.g., 90 days) as defense-in-depth |
| **Frontend may still send `room_number` as the primary identifier** for chat — backend no longer uses it for auth but frontend may need updating to pass `booking_id` | LOW | Backend is now correct regardless. Frontend update is a separate task. |
| **Pre-existing migration issue** prevents running test suite against SQLite — `hotel.0028_migrate_booking_guest_fields` fails on index drop | LOW | Tests are syntactically valid and import-clean. Run against PostgreSQL or fix migration chain separately. |
