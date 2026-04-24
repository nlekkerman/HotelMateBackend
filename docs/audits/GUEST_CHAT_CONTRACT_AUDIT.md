# Guest Realtime Chat — Backend Contract Audit

**Date:** 2026-03-27  
**Scope:** Strict frontend contract enforcement audit  
**Status:** VIOLATIONS FOUND

---

## 1. BOOTSTRAP CONTRACT AUDIT

**Contract endpoint:** `GET /api/guest/hotel/{slug}/chat/context?token=RAW_TOKEN`

**Actual endpoint:** `GET /api/guest/context/?token=RAW_TOKEN`

### ❌ FAIL — Bootstrap endpoint does NOT match contract URL

The bootstrap endpoint is `GuestContextView` at `/api/guest/context/` (no hotel slug in URL).  
The contract expects `/api/guest/hotel/{slug}/chat/context?token=RAW_TOKEN`.

| Contract Field | Returned? | Actual Field Path | File | Line |
|---|---|---|---|---|
| `conversation_id` | ❌ NO | Not returned | `hotel/guest_portal_views.py` | L91–L129 |
| `chat_session` | ⚠️ PARTIAL | `guest_chat.session` (nested, wrong key) | `hotel/guest_portal_views.py` | L121 |
| `channel_name` | ❌ NO | Not returned at bootstrap | `hotel/guest_portal_views.py` | L91–L129 |
| `events.message_created` | ❌ NO | Not returned | `hotel/guest_portal_views.py` | L91–L129 |
| `events.message_read` | ❌ NO | Not returned | `hotel/guest_portal_views.py` | L91–L129 |
| `pusher.key` | ❌ NO | Not returned | `hotel/guest_portal_views.py` | L91–L129 |
| `pusher.cluster` | ❌ NO | Not returned | `hotel/guest_portal_views.py` | L91–L129 |
| `pusher.auth_endpoint` | ❌ NO | Not returned | `hotel/guest_portal_views.py` | L91–L129 |

### Actual bootstrap response shape (`hotel/guest_portal_views.py` L99–L129):

```json
{
  "booking_id": "BK-2025-0003",
  "hotel_slug": "test-hotel",
  "assigned_room": { "room_number": "101", "room_type_name": "Standard Room" },
  "guest_name": "John Doe",
  "check_in": "2025-01-15",
  "check_out": "2025-01-17",
  "status": "CHECKED_IN",
  "party_size": 2,
  "is_checked_in": true,
  "is_checked_out": false,
  "allowed_actions": ["chat", "room_service", "view_booking"],
  "guest_chat": {
    "enabled": true,
    "disabled_reason": null,
    "session": "<signed_grant_string>"
  }
}
```

### Missing vs contract:

| Contract Field | Status |
|---|---|
| `conversation_id` | **MISSING** — not returned at bootstrap at all |
| `chat_session` | **WRONG KEY** — nested as `guest_chat.session`, contract expects top-level `chat_session` |
| `channel_name` | **MISSING** — not returned at bootstrap |
| `events.message_created` | **MISSING** — not returned at bootstrap |
| `events.message_read` | **MISSING** — not returned at bootstrap |
| `pusher.key` | **MISSING** — not returned at bootstrap |
| `pusher.cluster` | **MISSING** — not returned at bootstrap |
| `pusher.auth_endpoint` | **MISSING** — not returned at bootstrap |

**Note:** A second endpoint `GuestChatContextView` at `/api/guest/hotel/{slug}/chat/context` does return *some* channel info, but it requires `X-Guest-Chat-Session` header (session-authenticated), NOT raw token. It is a post-bootstrap endpoint, not the bootstrap itself. And even that endpoint returns the wrong shape (see Section 8).

---

## 2. SESSION ISSUANCE AUDIT

### ✅ PASS — Session issuance is correctly implemented

| Check | Status | Detail |
|---|---|---|
| Session minted during bootstrap | ✅ | `issue_guest_chat_grant()` called in `GuestContextView.get()` at `hotel/guest_portal_views.py` L108 |
| Session is stable for post-bootstrap | ✅ | Signed with Django `signing.dumps()`, HMAC-SHA256, 4-hour TTL |
| Tied to guest/booking/hotel | ✅ | Claims include `bid` (booking_id), `hs` (hotel_slug), `rid` (room_id), `rn` (room_number), `sc` (scope) |
| Not just raw token renamed | ✅ | Completely different — signed JWT-like payload via `common/guest_chat_grant.py` L98–L113 |
| Not null/optional on success | ⚠️ CONDITIONAL | Session is ONLY issued if `chat_eligible` is True (`hotel/guest_portal_views.py` L106–L109). If booking status is not `CONFIRMED` or `CHECKED_IN`, session is `null`. |

**Issuance source:** `common/guest_chat_grant.py` → `issue_guest_chat_grant()` (L98–L113)  
**Validation source:** `common/guest_chat_grant.py` → `validate_guest_chat_grant()` (L122–L170)

### ⚠️ RISK: Conditional issuance

`chat_session` is only issued when `'CHAT' in ctx.scopes and booking.status in ('CONFIRMED', 'CHECKED_IN')` (`hotel/guest_portal_views.py` L103–L104). If the booking is in any other status, `chat_session` is `null`. The frontend must handle this gracefully. This is acceptable behavior but must be documented in the contract as a conditional field.

---

## 3. POST-BOOTSTRAP AUTH AUDIT

### ✅ PASS — All post-bootstrap endpoints use session-only auth

| Endpoint | URL | Auth Mechanism | Token Accepted? | File | Line |
|---|---|---|---|---|---|
| Chat Context | `GET /api/guest/hotel/{slug}/chat/context` | `X-Guest-Chat-Session` | ❌ No | `hotel/canonical_guest_chat_views.py` | L97–L112 |
| Get Messages | `GET /api/guest/hotel/{slug}/chat/messages` | `X-Guest-Chat-Session` | ❌ No | `hotel/canonical_guest_chat_views.py` | L162–L200 |
| Send Message | `POST /api/guest/hotel/{slug}/chat/messages` | `X-Guest-Chat-Session` | ❌ No | `hotel/canonical_guest_chat_views.py` | L202–L277 |
| Mark Read | `POST /api/guest/hotel/{slug}/chat/conversations/{id}/mark_read/` | `X-Guest-Chat-Session` | ❌ No | `hotel/canonical_guest_chat_views.py` | L280–L342 |
| Pusher Auth | `POST /api/guest/hotel/{slug}/chat/pusher/auth` | `X-Guest-Chat-Session` | ❌ No | `hotel/canonical_guest_chat_views.py` | L345–L390 |

All five endpoints use `ChatSessionAuthenticationMixin` which reads ONLY from `HTTP_X_GUEST_CHAT_SESSION` (`common/guest_auth.py` L53–L57). No token extraction, no fallback.

The shared `_resolve_from_request()` helper (`hotel/canonical_guest_chat_views.py` L67–L83) calls `validate_guest_chat_grant()` which is purely session-based.

---

## 4. LEGACY PATH AUDIT

### ❌ FAIL — Multiple active legacy paths exist

| Legacy Code Path | Location | Classification | Risk |
|---|---|---|---|
| **`PusherAuthView._handle_guest_auth()`** — accepts raw token for Pusher auth | `notifications/views.py` L106–L170 | **ACTIVE PRODUCTION RISK** | Guest can authorize Pusher channels via raw token at `/api/notifications/pusher/auth/` bypassing session requirement |
| **`PusherAuthView` legacy channel format** — supports `private-guest-booking.{id}` | `notifications/views.py` L130–L135 | **ACTIVE PRODUCTION RISK** | Legacy channel naming pattern still accepted |
| **`send_conversation_message()`** — `AllowAny` guest send via staff chat URL | `chat/views.py` L88–L335 | **ACTIVE PRODUCTION RISK** | Guest can send messages at `/api/chat/{slug}/conversations/{id}/messages/send/` with zero auth. No token, no session. `AllowAny` with no guest identity validation. |
| **`get_conversation_messages()`** — `AllowAny` message fetch via staff chat URL | `chat/views.py` L62–L82 | **ACTIVE PRODUCTION RISK** | Anyone can fetch messages at `/api/chat/{slug}/conversations/{id}/messages/` with zero auth |
| **`get_or_create_conversation_from_room()`** — `AllowAny` conversation creation | `chat/views.py` L338–L357 | **ACTIVE PRODUCTION RISK** | Anyone can create conversations at `/api/chat/{slug}/conversations/from-room/{room}/` |
| **`upload_message_attachment()`** uses direct Pusher channels: `{slug}-staff-{id}-chat`, `{slug}-room-{num}-chat`** | `chat/views.py` L1149, L1201 | **ACTIVE PRODUCTION RISK** | Legacy non-booking-scoped channels still actively used for file upload notifications |
| **`notify_staff_new_guest_message()`** — deprecated method | `notifications/notification_manager.py` L2053–L2064 | DEAD CODE | Returns empty results, logs deprecation warning. Safe but should be removed. |
| **`notify_guest_staff_reply()`** — deprecated method | `notifications/notification_manager.py` L2067–L2075 | DEAD CODE | Returns empty results, logs deprecation warning. Safe but should be removed. |
| **`notify_staff_new_message()` module-level function** | `notifications/notification_manager.py` L2409–L2412 | DEAD CODE | Deprecated wrapper, logs warning. |
| **`resolve_guest_chat_context` / `GuestChatAccessError` imports in test file** | `chat/tests/test_token_auth.py` L19–L22 | **IMPORT RISK** | Tests import `resolve_guest_chat_context` and `GuestChatAccessError` from `bookings/services.py`, but these names do NOT exist in current `bookings/services.py`. Tests will fail with `ImportError`. |
| **`realtime_guest_chat_message_deleted()` uses `current_booking` before definition** | `notifications/notification_manager.py` L863 | **ACTIVE PRODUCTION BUG** | `payload` references `current_booking.booking_id` at L863 before `current_booking` is defined at L878. `NameError` on every guest message delete. |

### Critical: Unprotected legacy endpoints

The chat app's `urls.py` exposes ALL its views at `/api/chat/` (see `HotelMateBackend/urls.py` L62). These include:

- `/api/chat/{slug}/conversations/{id}/messages/` — `AllowAny`, zero auth required to READ messages
- `/api/chat/{slug}/conversations/{id}/messages/send/` — `AllowAny`, zero auth to SEND messages
- `/api/chat/{slug}/conversations/from-room/{room}/` — `AllowAny`, zero auth to CREATE conversations

These are **completely open endpoints** that bypass the entire token/session architecture. Any unauthenticated client can read, create, and send messages.

---

## 5. CHANNEL NAMING AUDIT

### ⚠️ PARTIAL PASS — Canonical channel exists but multiple patterns coexist

**Canonical channel formula:**
```
private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}
```

| Location | Channel Pattern | Canonical? |
|---|---|---|
| `hotel/canonical_guest_chat_views.py` L133–L135 | `private-hotel-{slug}-guest-chat-booking-{booking_id}` | ✅ |
| `hotel/canonical_guest_chat_views.py` L416–L418 (pusher auth) | `private-hotel-{slug}-guest-chat-booking-{booking_id}` | ✅ |
| `notifications/notification_manager.py` L748 | `private-hotel-{slug}-guest-chat-booking-{booking_id}` | ✅ |
| `notifications/notification_manager.py` L823 | `private-hotel-{slug}-guest-chat-booking-{booking_id}` | ✅ |
| `notifications/notification_manager.py` L903 | `private-hotel-{slug}-guest-chat-booking-{booking_id}` | ✅ |
| `notifications/notification_manager.py` L965 | `private-hotel-{slug}-guest-chat-booking-{booking_id}` | ✅ |
| `notifications/views.py` L126–L131 | `private-hotel-{slug}-guest-chat-booking-{booking_id}` | ✅ |
| **`notifications/views.py` L132–L135** | **`private-guest-booking.{booking_id}`** | **❌ LEGACY** |
| **`chat/views.py` L851** | **`{slug}-room-{room_number}-chat`** | **❌ LEGACY** |
| **`chat/views.py` L1149** | **`{slug}-staff-{staff_id}-chat`** | **❌ LEGACY** |
| **`chat/views.py` L1201** | **`{slug}-room-{room_number}-chat`** | **❌ LEGACY** |
| `notifications/notification_manager.py` L770 (staff conv channel) | `{slug}-conversation-{conv_id}-chat` | N/A (staff channel, not guest) |

### ❌ FAIL: Bootstrap does not return `channel_name`

The bootstrap endpoint (`GuestContextView` in `hotel/guest_portal_views.py`) does NOT return `channel_name` at all.

The post-bootstrap context view (`GuestChatContextView` in `hotel/canonical_guest_chat_views.py` L133–L152) returns it as `pusher.channel` instead of the contract-required top-level `channel_name`.

### ❌ FAIL: No centralized channel naming function

The channel name `f"private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}"` is constructed as inline f-strings in **6+ separate locations**. There is no single function like `get_guest_chat_channel(hotel_slug, booking_id)`.

---

## 6. EVENT NAMING AUDIT

### ❌ FAIL — Contract event names not returned; multiple event patterns exist

**Contract requires bootstrap to return:**
```json
{
  "events": {
    "message_created": "<canonical_name>",
    "message_read": "<canonical_name>"
  }
}
```

**Bootstrap returns:** Nothing. No `events` object at all.

**Post-bootstrap context view returns:** `pusher.event: "realtime_event"` — a single generic event name, not the contract's `events.message_created` / `events.message_read` structure.

### Actual event names emitted by backend:

| Broadcast Method | Pusher Event Name | Normalized `type` Field | File | Line |
|---|---|---|---|---|
| `realtime_guest_chat_message_created` | `"realtime_event"` | `"guest_message_created"` or `"staff_message_created"` | `notification_manager.py` | L784 |
| `realtime_guest_chat_unread_updated` | `"realtime_event"` | `"unread_updated"` | `notification_manager.py` | L829 |
| `realtime_guest_chat_message_deleted` | `"realtime_event"` | `"message_deleted"` | `notification_manager.py` | L912 |
| `realtime_guest_chat_message_edited` | `"realtime_event"` | `"message_edited"` | `notification_manager.py` | L967 |
| **`upload_message_attachment` (staff→guest)** | **`"new-staff-message"`** | N/A (raw payload) | `chat/views.py` | L1207 |
| **`upload_message_attachment` (guest→staff)** | **`"new-guest-message"`** | N/A (raw payload) | `chat/views.py` | L1155 |

### Issues:

1. **All canonical broadcasts use a single generic event name `"realtime_event"`** — the actual event type is inside the payload `type` field. The contract expects named events like `message_created` / `message_read`. The frontend must parse `data.type` to distinguish events, which is different from the contract.

2. **No `message_read` event exists for guest chat.** The `realtime_staff_chat_messages_read` method (L2311) is staff-scoped only. When a guest marks messages read via `GuestChatMarkReadView`, **no Pusher event is emitted**.

3. **File upload notifications in `chat/views.py` still use legacy event names** (`new-staff-message`, `new-guest-message`) on legacy channels.

---

## 7. PUSHER AUTH AUDIT

### ⚠️ PARTIAL PASS — Two auth endpoints exist with different auth mechanisms

**Contract expects:** `pusher.auth_endpoint` returned at bootstrap, using `X-Guest-Chat-Session`.

### Endpoint 1: Canonical (Session-based) ✅
- **URL:** `POST /api/guest/hotel/{slug}/chat/pusher/auth`
- **Auth:** `X-Guest-Chat-Session` header only
- **Channel validation:** Checks `channel_name == expected_channel` (L421)
- **Token fallback:** None
- **File:** `hotel/canonical_guest_chat_views.py` L345–L490

### Endpoint 2: Legacy (Token-based) ❌
- **URL:** `POST /api/notifications/pusher/auth/`
- **Auth:** Raw guest token via `?token=`, body `token`, body `guest_token`, or `GuestToken` header (`notifications/views.py` L43–L50)
- **Channel validation:** Regex-based, accepts both canonical AND legacy `private-guest-booking.{id}` format
- **Token fallback:** THIS IS the token fallback — it's a completely separate endpoint using raw tokens
- **File:** `notifications/views.py` L22–L195

### ❌ FAIL: `pusher.auth_endpoint` not returned at bootstrap

Bootstrap does not return a `pusher` object at all, so the frontend cannot know which auth endpoint to use.

### ❌ FAIL: Legacy token-based Pusher auth is still active

`/api/notifications/pusher/auth/` accepts raw guest tokens for channel authorization, completely bypassing the session model. This is a production-active alternative auth path.

---

## 8. SERIALIZER / RESPONSE SHAPE AUDIT

### ❌ FAIL — Response shape does not match contract

**Contract expects (bootstrap):**
```json
{
  "conversation_id": "string",
  "chat_session": "string",
  "channel_name": "string",
  "events": {
    "message_created": "string",
    "message_read": "string"
  },
  "pusher": {
    "key": "string",
    "cluster": "string",
    "auth_endpoint": "string"
  }
}
```

**Actual bootstrap response** (`hotel/guest_portal_views.py` L99–L129):
```json
{
  "booking_id": "BK-2025-0003",
  "hotel_slug": "test-hotel",
  "assigned_room": {},
  "guest_name": "...",
  "check_in": "...",
  "check_out": "...",
  "status": "...",
  "party_size": 2,
  "is_checked_in": true,
  "is_checked_out": false,
  "allowed_actions": [],
  "guest_chat": {
    "enabled": true,
    "disabled_reason": null,
    "session": "<grant_string>"
  }
}
```

| Contract Field | Actual Field | Match? |
|---|---|---|
| `conversation_id` | Not present | ❌ MISSING |
| `chat_session` | `guest_chat.session` | ❌ WRONG KEY — nested, should be top-level `chat_session` |
| `channel_name` | Not present | ❌ MISSING |
| `events.message_created` | Not present | ❌ MISSING |
| `events.message_read` | Not present | ❌ MISSING |
| `pusher.key` | Not present | ❌ MISSING |
| `pusher.cluster` | Not present | ❌ MISSING |
| `pusher.auth_endpoint` | Not present | ❌ MISSING |

**Post-bootstrap context view** (`hotel/canonical_guest_chat_views.py` L113–L158) returns:
```json
{
  "conversation_id": 42,
  "booking_id": "BK-2025-0003",
  "room_number": "101",
  "assigned_room_id": 7,
  "allowed_actions": ["chat"],
  "pusher": {
    "channel": "private-hotel-...",
    "event": "realtime_event"
  }
}
```

This is closer but still wrong:
- `pusher.channel` should be top-level `channel_name`
- `pusher.event` should be `events.message_created` / `events.message_read`
- Missing `pusher.key`, `pusher.cluster`, `pusher.auth_endpoint`
- This endpoint requires session auth — frontend can't get channel info without already having a session

---

## 9. SERVICE LAYER OWNERSHIP AUDIT

### ⚠️ PARTIAL PASS — Clear ownership for auth, scattered elsewhere

| Concern | Owner | Location | Clean? |
|---|---|---|---|
| Token validation | `resolve_guest_access()` | `common/guest_access.py` | ✅ Single source |
| Session issuance | `issue_guest_chat_grant()` | `common/guest_chat_grant.py` | ✅ Single source |
| Session validation | `validate_guest_chat_grant()` | `common/guest_chat_grant.py` | ✅ Single source |
| Grant→Booking resolution | `resolve_chat_context_from_grant()` | `bookings/services.py` | ✅ Single source |
| Channel naming | Inline f-string in 6+ places | Multiple files | ❌ Duplicated |
| Event naming | Inline strings in NotificationManager | `notification_manager.py` | ⚠️ Centralized in one class but spread across methods |
| Broadcast publishing | `NotificationManager._safe_pusher_trigger()` | `notification_manager.py` | ⚠️ Canonical path is centralized, but `chat/views.py` still triggers Pusher directly |
| Endpoint auth | `ChatSessionAuthenticationMixin` | `common/guest_auth.py` | ✅ Single source |

### Duplication risks:
1. **Channel naming:** `f"private-hotel-{slug}-guest-chat-booking-{booking_id}"` in `canonical_guest_chat_views.py` (×2), `notification_manager.py` (×4). Should be a single function.
2. **Pusher auth signature generation:** `_generate_pusher_auth()` is duplicated in `notifications/views.py` L173–L195 AND `hotel/canonical_guest_chat_views.py` L469–L490. Identical logic, two copies.
3. **Direct Pusher calls in `chat/views.py`:** `upload_message_attachment()` at L1149–L1216 calls `pusher_client.trigger()` directly with legacy channel names, bypassing `NotificationManager`.

---

## 10. FAILURE MODE AUDIT

| Failure Case | Status Code | Error Body | Contract-Safe? |
|---|---|---|---|
| Invalid raw token at bootstrap | 401 | `{"error": "INVALID_TOKEN", "detail": "Invalid or expired token"}` | ✅ |
| Missing token at bootstrap | 401 | `{"error": "MISSING_TOKEN", "detail": "Token required for guest access"}` | ✅ |
| Valid bootstrap but cancelled booking | 401 | `{"error": "INVALID_TOKEN", "detail": "Invalid or expired token"}` | ✅ (anti-enumeration) |
| Valid bootstrap but chat not eligible | 200 | `{"guest_chat": {"enabled": false, "session": null, "disabled_reason": "..."}}` | ⚠️ Returns 200 with null session — frontend must check `guest_chat.enabled` |
| Post-bootstrap missing `X-Guest-Chat-Session` | 401 | `{"error": "Guest chat session is required", "code": "SESSION_REQUIRED"}` | ✅ |
| Post-bootstrap expired session | 401 | `{"error": "Guest chat grant has expired — re-bootstrap required", "code": "GRANT_EXPIRED"}` | ✅ |
| Post-bootstrap invalid session | 401 | `{"error": "Invalid guest chat grant", "code": "GRANT_INVALID"}` | ✅ |
| Post-bootstrap hotel mismatch | 403 | `{"error": "Grant does not match this hotel", "code": "GRANT_HOTEL_MISMATCH"}` | ✅ |
| Pusher auth wrong channel | 403 | `{"error": "Channel does not match booking", "code": "CHANNEL_MISMATCH"}` | ✅ |
| Mark read wrong conversation_id | 403 | `{"error": "Conversation does not match booking", "code": "CONVERSATION_MISMATCH"}` | ✅ |
| Send message not checked in | 403 | `{"error": "Guest has not checked in yet", "code": "NOT_CHECKED_IN"}` | ✅ |
| Send message already checked out | 403 | `{"error": "Guest has already checked out", "code": "ALREADY_CHECKED_OUT"}` | ✅ |
| Send message no room | 409 | `{"error": "No room assigned to this booking", "code": "NO_ROOM_ASSIGNED"}` | ✅ |
| **Guest message delete (any)** | **500** | **`NameError: current_booking`** | **❌ CRASH** |
| Conversation not found on grant resolution | 200 | Auto-creates via `get_or_create` | ✅ (self-healing) |
| Booking not found on grant resolution | 401 | `{"error": "Invalid or expired token", "code": "INVALID_TOKEN"}` | ✅ |

### ❌ FAIL: `realtime_guest_chat_message_deleted()` crashes with `NameError`

In `notifications/notification_manager.py` L863, the payload references `current_booking.booking_id` but `current_booking` is not defined until L878. This causes a `NameError` on every guest message deletion, resulting in a 500 to the client.

---

## ✅ PASSED

| Area | Detail |
|---|---|
| Session issuance mechanism | Signed grants with HMAC-SHA256, booking-bound, hotel-cross-validated, 4h TTL |
| Session validation | Proper signature, expiry, scope, and hotel checks in `validate_guest_chat_grant()` |
| Post-bootstrap endpoint auth | All 5 canonical endpoints use `ChatSessionAuthenticationMixin` only |
| Token isolation | Canonical post-bootstrap views do not accept raw tokens at all |
| Booking resolution from grant | `resolve_chat_context_from_grant()` is clean, single-purpose |
| Error responses (canonical endpoints) | Typed error codes, appropriate HTTP status, machine-parseable |
| Conversation scoping | Booking-keyed conversations, room is metadata only |
| Broadcast channel formula | Canonical broadcasts all use `private-hotel-{slug}-guest-chat-booking-{id}` |

---

## ❌ VIOLATIONS

| # | File | Line(s) | Issue | Contract Impact |
|---|---|---|---|---|
| V1 | `hotel/guest_portal_views.py` | L99–L129 | Bootstrap response missing `conversation_id`, `channel_name`, `events`, `pusher` (key/cluster/auth_endpoint) | **Frontend cannot subscribe to realtime, cannot auth Pusher, cannot know channel** |
| V2 | `hotel/guest_portal_views.py` | L121 | `chat_session` returned as `guest_chat.session` instead of top-level `chat_session` | **Frontend gets null when reading `response.chat_session`** |
| V3 | `hotel/canonical_guest_chat_views.py` | L148–L153 | Context view returns `pusher.channel` + `pusher.event` instead of contract-required `channel_name` + `events` | **Frontend field mapping breaks** |
| V4 | `hotel/canonical_guest_chat_views.py` | L148–L153 | Context view missing `pusher.key`, `pusher.cluster`, `pusher.auth_endpoint` | **Frontend cannot initialize Pusher client** |
| V5 | `notifications/views.py` | L22–L170 | Legacy `PusherAuthView` at `/api/notifications/pusher/auth/` accepts raw token | **Bypasses session requirement — security violation** |
| V6 | `notifications/views.py` | L132–L135 | Legacy channel format `private-guest-booking.{id}` still accepted | **Alternate channel naming still authorized** |
| V7 | `chat/views.py` | L62–L82 | `get_conversation_messages()` — `AllowAny`, no auth at all | **Anyone can read all chat messages** |
| V8 | `chat/views.py` | L88–L335 | `send_conversation_message()` — `AllowAny`, no auth at all | **Anyone can send messages as guest** |
| V9 | `chat/views.py` | L338–L357 | `get_or_create_conversation_from_room()` — `AllowAny`, no auth | **Anyone can create conversations** |
| V10 | `chat/views.py` | L1149, L1201, L1207 | File uploads use legacy channels + legacy event names via direct `pusher_client.trigger()` | **Bypasses notification architecture** |
| V11 | `notifications/notification_manager.py` | L863 | `current_booking` used before defined in `realtime_guest_chat_message_deleted()` | **500 crash on every message delete** |
| V12 | Multiple files | 6+ locations | Channel name constructed inline, no centralized function | **Drift risk between bootstrap/auth/broadcast** |
| V13 | `notifications/notification_manager.py` | All broadcast methods | All events emitted as `"realtime_event"` — no `message_read` event exists for guest chat | **Contract `events.message_read` has no backend implementation** |
| V14 | `chat/tests/test_token_auth.py` | L19–L22 | Imports `resolve_guest_chat_context`, `GuestChatAccessError` from `bookings/services.py` — these don't exist | **Tests broken with ImportError** |

---

## 🔧 REQUIRED FIXES

Ordered by execution priority:

### P0 — Production Crashes

**Fix 1: `NameError` in message deletion** (`notifications/notification_manager.py` L831–L912)

Move the `current_booking` query (L878–L883) to BEFORE the `payload` construction (L860). The payload at L863 references `current_booking.booking_id` before it exists.

### P1 — Security: Open Endpoints

**Fix 2: Protect or remove legacy chat endpoints** (`chat/views.py`)

The endpoints at `/api/chat/{slug}/conversations/{id}/messages/` and `/api/chat/{slug}/conversations/{id}/messages/send/` use `@permission_classes([AllowAny])` with zero guest identity verification. Either:
- Change to `@permission_classes([IsAuthenticated])` (staff-only), OR
- Remove these FBVs entirely if they are only used by the old guest flow

**Fix 3: Remove or restrict legacy Pusher auth** (`notifications/views.py`)

`PusherAuthView._handle_guest_auth()` accepts raw tokens. Either:
- Remove the guest token path entirely (force all guest Pusher auth through the canonical `/api/guest/hotel/{slug}/chat/pusher/auth` endpoint), OR
- At minimum, add deprecation logging and a kill-switch

### P2 — Contract Alignment

**Fix 4: Add missing fields to bootstrap response** (`hotel/guest_portal_views.py` L99–L129)

Add to the response context:
```python
context['conversation_id'] = ...  # resolve or create conversation during bootstrap
context['chat_session'] = chat_session  # top-level, not nested
context['channel_name'] = f"private-hotel-{booking.hotel.slug}-guest-chat-booking-{booking.booking_id}"
context['events'] = {
    'message_created': 'realtime_event',  # or define new named events
    'message_read': 'realtime_event',
}
context['pusher'] = {
    'key': settings.PUSHER_KEY,
    'cluster': settings.PUSHER_CLUSTER,
    'auth_endpoint': f'/api/guest/hotel/{booking.hotel.slug}/chat/pusher/auth',
}
```

**Fix 5: Flatten `chat_session` to top-level** (`hotel/guest_portal_views.py`)

Move from `guest_chat.session` to top-level `chat_session` in bootstrap response.

### P3 — Architecture Cleanup

**Fix 6: Extract channel naming function**

Create a single function:
```python
def guest_chat_channel(hotel_slug: str, booking_id: str) -> str:
    return f"private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}"
```

Replace all 6+ inline constructions.

**Fix 7: Remove legacy channel format** (`notifications/views.py` L132–L135)

Remove the `private-guest-booking.{id}` regex match branch.

**Fix 8: Fix file upload broadcast path** (`chat/views.py` L1149–L1216)

Replace direct `pusher_client.trigger()` calls with `notification_manager.realtime_guest_chat_message_created(message)` (which is already called earlier in the same function at L1131).

**Fix 9: Add `message_read` broadcast**

In `GuestChatMarkReadView.post()` (`hotel/canonical_guest_chat_views.py` L318), after updating message read status, emit a `realtime_event` with type `message_read` to the booking channel.

**Fix 10: Fix broken test imports** (`chat/tests/test_token_auth.py` L19–L22)

Update imports to match current code — `resolve_guest_chat_context` and `GuestChatAccessError` no longer exist in `bookings/services.py`.

### P4 — Dead Code Removal

**Fix 11:** Remove deprecated methods:
- `notify_staff_new_guest_message()` (L2053)
- `notify_guest_staff_reply()` (L2067)
- `notify_staff_new_message()` module-level function (L2409)

---

## ⚠️ RISK LEVEL

### **HIGH**

Reasons:
1. **Open endpoints** (`chat/views.py`) allow unauthenticated message read/write — this is a real security vulnerability, not theoretical
2. **Production crash** (`NameError`) on every message deletion
3. **Bootstrap response** is fundamentally misaligned — frontend gets none of the fields it needs to initialize realtime
4. **Dual Pusher auth paths** undermine the session-only model

---

## 🧱 CONTRACT BREAKPOINTS

Points where the frontend will completely fail:

| # | Breakpoint | Impact |
|---|---|---|
| 1 | Bootstrap returns no `channel_name` | Frontend cannot subscribe to Pusher channel |
| 2 | Bootstrap returns no `pusher.key` / `pusher.cluster` | Frontend cannot initialize Pusher client |
| 3 | Bootstrap returns no `pusher.auth_endpoint` | Frontend cannot authenticate private channel |
| 4 | Bootstrap returns no `events` object | Frontend does not know which events to listen for |
| 5 | `chat_session` is nested at `guest_chat.session` instead of top-level `chat_session` | Frontend reads `undefined` when accessing `response.chat_session` |
| 6 | Bootstrap returns no `conversation_id` | Frontend cannot call mark_read (requires conversation_id in URL) |
| 7 | No `message_read` event is ever broadcast | Frontend realtime read receipts will never fire |

---

## 🔄 FRONTEND ALIGNMENT SUMMARY

| Operation | Can Frontend Safely Do This? | Detail |
|---|---|---|
| **Bootstrap** | ⚠️ PARTIAL | Token is accepted, session is issued, but response shape is wrong — frontend gets session buried at `guest_chat.session` and missing all Pusher/channel/event info |
| **Obtain `chat_session`** | ⚠️ PARTIAL | Session exists in response but at wrong key path (`guest_chat.session` vs `chat_session`) |
| **Subscribe to realtime** | ❌ NO | Bootstrap does not return `channel_name`, `pusher.key`, `pusher.cluster`, or `pusher.auth_endpoint` |
| **Receive events** | ❌ NO | Cannot subscribe (see above). Even if hardcoded, `events` object is not returned, and `message_read` event does not exist |
| **Send messages** | ✅ YES (if session obtained) | `POST /api/guest/hotel/{slug}/chat/messages` works correctly with `X-Guest-Chat-Session` |
| **Fetch messages** | ✅ YES (if session obtained) | `GET /api/guest/hotel/{slug}/chat/messages` works correctly with `X-Guest-Chat-Session` |
| **Mark read** | ⚠️ PARTIAL | Endpoint works, but frontend needs `conversation_id` from bootstrap (not provided) and no realtime event is emitted |

---

*End of audit.*
