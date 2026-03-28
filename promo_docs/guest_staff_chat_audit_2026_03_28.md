# Guest ↔ Staff Chat — Production Backend Audit

**Date:** 2026-03-28  
**Scope:** Full stack audit of guest-to-staff chat system  
**Files audited:**
- `chat/models.py`, `chat/views.py`, `chat/serializers.py`, `chat/urls.py`, `chat/staff_urls.py`, `chat/utils.py`
- `hotel/canonical_guest_chat_views.py`
- `common/guest_access.py`, `common/guest_auth.py`, `common/guest_chat_grant.py`, `common/guest_chat_config.py`
- `bookings/services.py` → `resolve_chat_context_from_grant()`
- `notifications/notification_manager.py` → all `realtime_guest_chat_*` methods
- `guest_urls.py`, `staff_urls.py` (root level)

---

## 1. CHAT DOMAIN (GUEST ↔ STAFF)

### Conversation Model

| Field | Type | Notes |
|---|---|---|
| `room` | FK → Room | Nullable. Contextual metadata, updated on room moves |
| `booking` | FK → RoomBooking | Nullable. **Actual owner key** — conversation is keyed by booking |
| `participants_staff` | M2M → Staff | Legacy field. Separate `GuestConversationParticipant` model is the real participant tracker |
| `has_unread` | Boolean | Denormalized flag for staff sidebar |
| `created_at` / `updated_at` | DateTime | Auto timestamps |

**Creation logic:**
- **Guest bootstrap:** `Conversation.objects.get_or_create(booking=booking, defaults={"room": room})` in `GuestChatContextView.get()`
- **Staff-initiated:** `Conversation.objects.get_or_create(room=room)` in `get_or_create_conversation_from_room()` — **⚠️ uses room as key, not booking**

**Cardinality:**
- **1 conversation per booking** (canonical guest flow via bootstrap)
- Room moves update `conversation.room` without creating a new conversation
- ⚠️ Staff `get_or_create_conversation_from_room()` creates by **room**, not booking — this can create orphan conversations without a booking FK

### Participants

| Type | Identity | Auth mechanism |
|---|---|---|
| Guest | Anonymous (no Django User) | Token → chat_session grant (HMAC-signed, 4h TTL) |
| Staff | Authenticated Django User with `staff_profile` | JWT/Session (IsAuthenticated) |
| System | No sender | Automated join messages |

**Can multiple staff join?** ✅ Yes. `GuestConversationParticipant` tracks each staff member with `joined_at`. System "joined" messages are emitted. Latest `joined_at` = current handler.

**Can guest have multiple conversations?** No. Conversation is keyed by booking (`get_or_create`). One booking = one conversation.

### Message Model (`RoomMessage`)

| Field | Type | Notes |
|---|---|---|
| `conversation` | FK → Conversation | Required |
| `room` | FK → Room | Required (denormalized) |
| `booking` | FK → RoomBooking | Nullable — **only set on guest messages from canonical flow** |
| `sender_type` | CharField | `guest` / `staff` / `system` |
| `staff` | FK → Staff | Nullable. Set when sender_type=staff |
| `message` | TextField | Content |
| `timestamp` | DateTime | `default=timezone.now` |
| `staff_display_name` | CharField | Auto-populated on save if staff sender |
| `staff_role_name` | CharField | Auto-populated on save if staff sender |
| `status` | CharField | `pending` / `delivered` / `read` (default: delivered) |
| `read_by_staff` | Boolean | Per-message read tracking |
| `read_by_guest` | Boolean | Per-message read tracking |
| `staff_read_at` / `guest_read_at` | DateTime | Nullable timestamps |
| `is_edited` / `edited_at` | Boolean / DateTime | Edit tracking |
| `is_deleted` / `deleted_at` | Boolean / DateTime | Soft delete tracking |
| `reply_to` | Self-FK | Threading support |

**Content types:** Text + file attachments via `MessageAttachment` model (Cloudinary storage, 50MB limit, images/PDF/docs).

---

## 2. AUTH FLOW

### STEP 1 — Bootstrap (one-time)

```
GET /api/guest/hotel/{slug}/chat/context?token=RAW_TOKEN
```

Flow:
1. Extract raw token from `?token=` query param or `Authorization: GuestToken <token>` header
2. `resolve_guest_access(token, hotel_slug, required_scopes=["CHAT"])` — SHA-256 hash lookup (GBT first, BMT fallback)
3. Validates booking lifecycle (not cancelled/declined), checks guest is checked-in with room assigned
4. `issue_guest_chat_grant(booking, room)` — `django.core.signing.dumps()` with HMAC-SHA256, salt `"guest-chat-grant-v1"`, TTL = 4 hours
5. `Conversation.objects.get_or_create(booking=booking)` — creates or retrieves conversation
6. Returns full config:

```json
{
  "conversation_id": 42,
  "chat_session": "<signed_grant_string>",
  "channel_name": "private-hotel-{slug}-guest-chat-booking-{booking_id}",
  "events": {
    "message_created": "chat.message.created",
    "message_read": "chat.message.read"
  },
  "pusher": {
    "key": "<PUSHER_KEY>",
    "cluster": "<PUSHER_CLUSTER>",
    "auth_endpoint": "/api/guest/hotel/{slug}/chat/pusher/auth"
  },
  "permissions": {
    "can_send": true,
    "can_read": true
  }
}
```

### STEP 2 — All subsequent calls

Header: `X-Guest-Chat-Session: <chat_session>`

Internal resolution (`_resolve_from_request`):
1. Extract `X-Guest-Chat-Session` header
2. `validate_guest_chat_grant(session_str, hotel_slug)` — verifies HMAC signature, max age (4h), scope (`guest_chat`), hotel cross-check
3. `resolve_chat_context_from_grant(grant_ctx)` — looks up booking by `booking_id`, checks lifecycle, resolves conversation

### Validation Results

| Check | Status | Details |
|---|---|---|
| chat_session required on all post-bootstrap endpoints? | ✅ | `_resolve_from_request` returns 401 if missing |
| Any endpoints still using raw token after bootstrap? | ✅ | Only bootstrap accepts raw token. All others require `X-Guest-Chat-Session` |
| Expiration logic | ✅ | 4-hour TTL via `django.core.signing` `max_age`. Expired = `GRANT_EXPIRED` → re-bootstrap |
| Revocation | ⚠️ | **No explicit revocation mechanism.** Grant is stateless (signed payload). If booking is cancelled, `resolve_chat_context_from_grant` rejects it — but a checked-out guest's grant remains valid until TTL expires |
| Token reuse across devices | ⚠️ | Same raw token can bootstrap from multiple devices, each getting its own chat_session. Both sessions are valid simultaneously |

---

## 3. ENDPOINT CONTRACTS

### 3.1 Guest Endpoints (from `guest_urls.py`)

#### Bootstrap — Get Context

```
GET /api/guest/hotel/{slug}/chat/context?token=RAW_TOKEN
```

| | |
|---|---|
| **Auth** | Raw token via `?token=` or `Authorization: GuestToken <token>` |
| **Throttle** | `guest_burst` / `guest_sustained` |
| **Request** | Query param: `token` |
| **Response 200** | `{ conversation_id, chat_session, channel_name, events, pusher: { key, cluster, auth_endpoint }, permissions: { can_send, can_read } }` |
| **Errors** | 401 `TOKEN_REQUIRED`, 401 `INVALID_TOKEN`, 403 `MISSING_SCOPE`, 409 `NOT_CHECKED_IN` |

#### Get Messages

```
GET /api/guest/hotel/{slug}/chat/messages
Header: X-Guest-Chat-Session
```

| | |
|---|---|
| **Auth** | `X-Guest-Chat-Session` header |
| **Query params** | `limit` (default 50), `before_id` (cursor pagination) |
| **Response 200** | `{ messages: [...], conversation_id, count, has_more }` |
| **Message shape** | Full `RoomMessageSerializer` output (see §3.3) |

#### Send Message

```
POST /api/guest/hotel/{slug}/chat/messages
Header: X-Guest-Chat-Session
```

| | |
|---|---|
| **Auth** | `X-Guest-Chat-Session` header |
| **Body** | `{ message: "text", reply_to: <id> (optional) }` |
| **Response 201** | `{ message_id, sent_at, conversation_id }` |
| **Enforces** | Must be checked-in, not checked-out, room assigned |
| **Errors** | 403 `NOT_CHECKED_IN`, 403 `ALREADY_CHECKED_OUT`, 409 `NO_ROOM_ASSIGNED`, 400 empty message |

#### Mark Read

```
POST /api/guest/hotel/{slug}/chat/conversations/{id}/mark_read/
Header: X-Guest-Chat-Session
```

| | |
|---|---|
| **Auth** | `X-Guest-Chat-Session` header |
| **Body** | None |
| **Response 200** | `{ marked_read: <count> }` |
| **Validates** | conversation_id matches booking's conversation |
| **Broadcasts** | `chat.message.read` on booking channel |

#### Pusher Auth

```
POST /api/guest/hotel/{slug}/chat/pusher/auth
Header: X-Guest-Chat-Session
```

| | |
|---|---|
| **Auth** | `X-Guest-Chat-Session` header |
| **Body** | `{ socket_id, channel_name }` |
| **Response 200** | `{ auth: "<key>:<signature>", channel_data: "..." }` |
| **Validates** | Requested channel must match `private-hotel-{slug}-guest-chat-booking-{booking_id}` |

### 3.2 Staff Endpoints (from `chat/urls.py` / `chat/staff_urls.py`)

All require `IsAuthenticated` (JWT/Session) except where noted.

#### Get Active Conversations

```
GET /api/staff/hotel/{slug}/chat/conversations/
```

| | |
|---|---|
| **Auth** | `IsAuthenticated` |
| **Response** | `ConversationSerializer[]` — conversation list with guest name, unread counts, last message |

#### Get Conversation Messages

```
GET /api/staff/hotel/{slug}/chat/conversations/{id}/messages/
```

| | |
|---|---|
| **Auth** | `IsAuthenticated` |
| **Query params** | `limit` (default 10), `before_id` |
| **Response** | `RoomMessageSerializer[]` |

⚠️ **Contract mismatch:** Guest endpoint wraps in `{ messages: [...], count, has_more }`. Staff endpoint returns bare array.

⚠️ **Default limit:** Guest = 50, Staff = 10. Inconsistent.

#### Send Conversation Message

```
POST /api/staff/hotel/{slug}/chat/conversations/{id}/messages/send/
```

| | |
|---|---|
| **Auth** | `IsAuthenticated` |
| **Body** | `{ message: "text", reply_to: <id> (optional) }` |
| **Response** | `{ conversation_id, message: <serialized>, staff_info }` |
| **Side effects** | Creates `GuestConversationParticipant`, emits system join message if new staff, updates handler |

#### Mark Conversation Read

```
POST /api/chat/conversations/{id}/mark-read/
```

| | |
|---|---|
| **Auth** | `AllowAny` (detects staff vs guest via `request.user.staff_profile`) |
| **Response** | `{ conversation_id, marked_as_read: <count> }` |

⚠️ **DUPLICATE endpoint:** Guest has a separate `mark_read` at `/api/guest/hotel/{slug}/chat/conversations/{id}/mark_read/` with proper session validation. This staff endpoint at `AllowAny` is also reachable by guests without session validation.

#### Assign Staff to Conversation

```
POST /api/staff/hotel/{slug}/chat/conversations/{id}/assign-staff/
```

| | |
|---|---|
| **Auth** | `IsAuthenticated` |
| **Response** | `{ conversation_id, assigned_staff, participant_created, room_number, messages_marked_read }` |
| **Side effects** | Creates participant, marks all guest messages as read, clears unread flag |

#### Update Message

```
PATCH /api/chat/messages/{id}/update/
```

| | |
|---|---|
| **Auth** | `AllowAny` |
| **Body** | `{ message: "new text" }` |
| **Response** | `{ message: <serialized>, success: true }` |
| **Permissions** | Staff can edit their own. Guest can edit any guest message in same conversation. |
| **Broadcasts** | `chat.message.edited` via NotificationManager |

#### Delete Message

```
DELETE /api/chat/messages/{id}/delete/
```

| | |
|---|---|
| **Auth** | `AllowAny` |
| **Query params** | `hard_delete=true` (staff admin only) |
| **Response** | `{ success: true, hard_delete: bool, message_id or message }` |
| **Permissions** | Staff own msgs, staff can moderate guest msgs, guest can delete own msgs |
| **Broadcasts** | `chat.message.deleted` via NotificationManager |

#### Upload Attachment

```
POST /api/staff/hotel/{slug}/chat/conversations/{id}/upload-attachment/
```

| | |
|---|---|
| **Auth** | `AllowAny` |
| **Body** | Multipart: `files[]`, `message` (optional), `message_id` (optional), `reply_to` (optional) |
| **Limits** | 50MB per file, allowed extensions: jpg/jpeg/png/gif/webp/bmp/pdf/doc/docx/xls/xlsx/txt/csv |
| **Response** | `{ message: <serialized>, attachments: [...], success: true, warnings: [...] }` |

#### Delete Attachment

```
DELETE /api/chat/attachments/{id}/delete/
```

| | |
|---|---|
| **Auth** | `AllowAny` |
| **Response** | `{ success: true, attachment_id, message_id }` |
| **Broadcasts** | `attachment_deleted` to conversation + deletion channels via direct Pusher (NOT NotificationManager) |

#### Save FCM Token

```
POST /api/chat/{slug}/save-fcm-token/
```

| | |
|---|---|
| **Auth** | `AllowAny` |
| **Body** | `{ fcm_token, room_number }` |
| **Response** | `{ success: true, room_number, hotel_slug }` |

### 3.3 Serialized Message Shape (`RoomMessageSerializer`)

```json
{
  "id": 123,
  "conversation": 42,
  "conversation_id": 42,
  "room": 7,
  "room_number": 101,
  "booking": 5,
  "booking_id": "BK-2025-0003",
  "sender_type": "guest|staff|system",
  "staff": 12,
  "staff_name": "John Smith",
  "guest_name": "Jane Doe",
  "staff_info": {
    "name": "John Smith",
    "role": "Receptionist",
    "department": "Front Office",
    "profile_image": "https://..."
  },
  "message": "Hello!",
  "timestamp": "2026-03-28T10:00:00Z",
  "status": "delivered",
  "is_read_by_recipient": false,
  "read_at": null,
  "read_by_staff": false,
  "read_by_guest": false,
  "staff_read_at": null,
  "guest_read_at": null,
  "delivered_at": "2026-03-28T10:00:00Z",
  "staff_display_name": "John Smith",
  "staff_role_name": "Receptionist",
  "is_edited": false,
  "edited_at": null,
  "is_deleted": false,
  "deleted_at": null,
  "reply_to": 120,
  "reply_to_message": {
    "id": 120,
    "message": "Original message text...",
    "sender_type": "guest",
    "sender_name": "Guest",
    "timestamp": "2026-03-28T09:55:00Z",
    "has_attachments": false,
    "attachments": [],
    "attachment_count": 0
  },
  "attachments": [{
    "id": 1,
    "file": "cloudinary_id",
    "file_url": "https://res.cloudinary.com/...",
    "file_name": "photo.jpg",
    "file_type": "image",
    "file_size": 245000,
    "file_size_display": "239.3 KB",
    "mime_type": "image/jpeg",
    "thumbnail": null,
    "thumbnail_url": null,
    "uploaded_at": "2026-03-28T10:00:00Z"
  }],
  "has_attachments": true
}
```

### 3.4 Flagged Issues

| Issue | Severity | Details |
|---|---|---|
| **Response shape mismatch (get messages)** | ⚠️ Medium | Guest: `{ messages, count, has_more }`. Staff: bare array. Frontend must handle both. |
| **Default limit mismatch** | ⚠️ Low | Guest: 50. Staff: 10. |
| **Duplicate mark-read endpoints** | ⚠️ Medium | Staff `/chat/conversations/{id}/mark-read/` (AllowAny) and Guest `/guest/hotel/{slug}/chat/conversations/{id}/mark_read/` (session-validated). Guest could bypass session validation by hitting the staff endpoint. |
| **No guest upload endpoint** | ⚠️ Medium | `upload_message_attachment` is under staff URLs. No guest-facing upload endpoint exists in `guest_urls.py`. |
| **No reactions endpoint** | ℹ️ | No model or endpoint for emoji reactions. |
| **No typing indicators endpoint** | ℹ️ | No backend support for typing status. |

---

## 4. REALTIME EVENTS (PUSHER)

### Channels

| Channel Pattern | Scope | Subscribers |
|---|---|---|
| `private-hotel-{slug}-guest-chat-booking-{booking_id}` | Per-booking (canonical) | Guest (via Pusher auth) + Backend broadcasts |
| `{slug}-conversation-{id}-chat` | Per-conversation | Staff chat interface |
| `{slug}.staff-{id}-notifications` | Per-staff | Individual staff notification badges |
| `{slug}-room-{room_number}-deletions` | Per-room | Legacy deletion events |

### Events

#### `chat.message.created` → Booking channel

**Triggered by:** `NotificationManager.realtime_guest_chat_message_created()`  
**Received by:** Guest + Staff (if subscribed to booking channel)

```json
{
  "category": "guest_chat",
  "event_type": "guest_message_created | staff_message_created",
  "payload": {
    "conversation_id": "BK-2025-0003",
    "booking_id": "BK-2025-0003",
    "room_conversation_id": 42,
    "id": 123,
    "sender_role": "guest|staff",
    "sender_id": null | 12,
    "sender_name": "Guest | John Smith",
    "message": "Hello!",
    "timestamp": "2026-03-28T10:00:00Z",
    "room_number": 101,
    "is_staff_reply": false | true,
    "has_attachments": false,
    "pin": "1234"
  },
  "hotel_slug": "grand-hotel",
  "timestamp": "2026-03-28T10:00:00Z"
}
```

⚠️ **CONTRACT MISMATCH:** Realtime `conversation_id` = `booking_id` (string like `"BK-2025-0003"`). API serializer `conversation_id` = numeric DB ID (42). Frontend must reconcile. The `room_conversation_id` field carries the numeric ID.

⚠️ **Payload shape mismatch:** Realtime payload uses `sender_role`, `sender_name`, `sender_id`. API serializer uses `sender_type`, `staff_name`, `guest_name`, `staff_info`. No direct mapping.

#### `chat.message.read` → Booking channel

**Triggered by:** Guest `mark_read` endpoint  
**Received by:** Staff

```json
{
  "conversation_id": 42,
  "booking_id": "BK-2025-0003",
  "marked_read": 5,
  "read_at": "2026-03-28T10:05:00Z"
}
```

#### `messages-read-by-staff` → Conversation channel

**Triggered by:** Staff `mark_conversation_read` and `assign_staff_to_conversation`  
**Received by:** Guest (if subscribed to conversation channel)

```json
{
  "message_ids": [120, 121, 122],
  "read_at": "2026-03-28T10:05:00Z",
  "staff_name": "John Smith",
  "conversation_id": 42
}
```

⚠️ **Channel split:** Guest read receipts → booking channel (`chat.message.read`). Staff read receipts → conversation channel (`messages-read-by-staff`). Guest must subscribe to BOTH channels to see staff read receipts — but Pusher auth only validates the booking channel. **Guest may NOT receive staff read receipts.**

#### `chat.message.deleted` → Booking channel

**Triggered by:** `NotificationManager.realtime_guest_chat_message_deleted()`

```json
{
  "payload": {
    "message_id": 123,
    "conversation_id": "BK-2025-0003",
    "booking_id": "BK-2025-0003",
    "room_conversation_id": 42,
    "room_number": 101,
    "deleted_by": "staff|guest|system",
    "deleter_name": "John Smith",
    "deleter_id": 12,
    "deleted_at": "2026-03-28T10:10:00Z"
  }
}
```

#### `chat.message.edited` → Booking channel

**Triggered by:** `NotificationManager.realtime_guest_chat_message_edited()`

```json
{
  "payload": {
    "message_id": 123,
    "conversation_id": "BK-2025-0003",
    "booking_id": "BK-2025-0003",
    "room_conversation_id": 42,
    "room_number": 101,
    "message_text": "Edited text",
    "edited_by": "staff|guest",
    "editor_name": "John Smith",
    "editor_id": 12,
    "edited_at": "2026-03-28T10:08:00Z",
    "is_edited": true
  }
}
```

#### `chat.unread.updated` → Booking channel

**Triggered by:** `NotificationManager.realtime_guest_chat_unread_updated()`

```json
{
  "payload": {
    "room_number": 101,
    "conversation_id": "BK-2025-0003",
    "booking_id": "BK-2025-0003",
    "unread_count": 0,
    "updated_at": "2026-03-28T10:05:00Z"
  }
}
```

#### `new-guest-message` → Staff notification channels

**Triggered by:** `_notify_front_office_staff_of_guest_message()`  
**Received by:** Each front-office staff member individually

```json
{
  "type": "guest_message",
  "message_id": 123,
  "conversation_id": 42,
  "booking_id": "BK-2025-0003",
  "room_number": 101,
  "guest_message": "Hello! I need...",
  "sender_name": "Guest",
  "timestamp": "2026-03-28T10:00:00Z"
}
```

#### `realtime_event` → Staff conversation channel

**Triggered by:** Guest messages also sent to `{slug}-conversation-{id}-chat`  
**Purpose:** Staff chat interface real-time updates

#### `attachment_deleted` → Conversation + Deletion channels

**Triggered by:** `delete_attachment()` — direct Pusher (NOT NotificationManager)  
**Received by:** Staff + possibly Guest

```json
{
  "attachment_id": 1,
  "message_id": 123,
  "deleted_by": "staff|guest",
  "original_sender": "staff",
  "staff_id": 12,
  "staff_name": "John Smith",
  "timestamp": "2026-03-28T10:10:00Z"
}
```

### Missing Events

| Event | Status | Impact |
|---|---|---|
| Typing indicators | ❌ Not implemented | No "Guest is typing..." UX |
| Reaction events | ❌ Not implemented | No emoji reactions support |
| Online/presence | ❌ Not implemented | No online status indicators |
| Staff joined (realtime) | ✅ Exists | System message created + broadcast |

---

## 5. MESSAGE FEATURES SUPPORT

| Feature | Status | Details |
|---|---|---|
| Text messages | ✅ **SUPPORTED** | Full support both directions |
| Images / attachments | ⚠️ **PARTIAL** | Model + staff upload endpoint exist. **No guest upload endpoint.** Cloudinary storage. 50MB limit. |
| Reply (threading) | ✅ **SUPPORTED** | `reply_to` FK with serialized preview (3 attachment previews, 100 char text truncation) |
| Reactions (likes/emojis) | ❌ **NOT IMPLEMENTED** | No model, no endpoint, no events |
| Message editing | ✅ **SUPPORTED** | `PATCH /api/chat/messages/{id}/update/` with `is_edited` + `edited_at` tracking |
| Message deletion | ✅ **SUPPORTED** | Soft delete (default) + hard delete (admin staff). Text replaced with `[Message deleted]` / `[File deleted]` |
| System messages | ✅ **SUPPORTED** | `sender_type="system"` for staff join events. Auto-created when new staff enters conversation. |
| Read receipts | ✅ **SUPPORTED** | Per-message `read_by_staff`/`read_by_guest` + timestamps |

---

## 6. READ STATUS SYSTEM

### Data Model

**Per-message tracking:**
- `read_by_staff` (Boolean) + `staff_read_at` (DateTime)
- `read_by_guest` (Boolean) + `guest_read_at` (DateTime)
- `status` field: `pending` → `delivered` → `read`

**Per-conversation denormalized:**
- `Conversation.has_unread` (Boolean) — tracks if any guest messages unread by staff

### How `message_read` is Triggered

**Guest reads staff messages:**
1. Guest calls `POST /api/guest/hotel/{slug}/chat/conversations/{id}/mark_read/`
2. All messages where `sender_type IN ('staff', 'system')` AND `read_by_guest=False` → bulk updated
3. `has_unread` cleared on conversation
4. `chat.message.read` event broadcast on booking channel

**Staff reads guest messages:**
1. Staff calls `POST /api/chat/conversations/{id}/mark-read/` OR `POST .../assign-staff/`
2. All messages where `sender_type='guest'` AND `read_by_staff=False` → bulk updated
3. `has_unread` cleared on conversation
4. `messages-read-by-staff` event on conversation channel

### Issues Identified

| Issue | Severity | Details |
|---|---|---|
| **Race condition: concurrent staff reads** | ⚠️ Medium | Two staff members calling `assign_staff_to_conversation` simultaneously. Both do `filter(read_by_staff=False).update(...)`. Second call gets `updated_count=0`. No harm, but Pusher event fires twice. |
| **Desync: `has_unread` flag** | ⚠️ Medium | `has_unread` is a denormalized Boolean. If a message arrives between read + flag-clear, the flag stays `False` but unread messages exist. No periodic reconciliation. |
| **Staff read receipt not reaching guest** | ❌ High | Staff read receipts go to `{slug}-conversation-{id}-chat` channel. Guest subscribes and auth'd only on `private-hotel-{slug}-guest-chat-booking-{booking_id}`. **Guest never sees "Read" status for their own messages.** |
| **Double mark-read on staff open** | ⚠️ Low | `assign_staff_to_conversation` marks read + `send_conversation_message` (staff) also triggers participant check. Opening then immediately sending = redundant DB write. |
| **`status` field disconnect** | ⚠️ Low | `status` field on message updated to `'read'` during mark-read, but it's a single value — if staff reads but guest hasn't, status is `'read'` even though guest hasn't read. The boolean fields are the truth. |

---

## 7. EDGE CASES

### chat_session is missing

```
X-Guest-Chat-Session header absent
→ 401 { error: "Guest chat session is required", code: "SESSION_REQUIRED" }
```
✅ Properly handled by `_resolve_from_request()`.

### Token valid but no conversation exists

```
Bootstrap: resolve_guest_access succeeds → Conversation.get_or_create(booking=booking)
→ Creates new conversation automatically. Never returns "no conversation" error.
```
✅ Auto-creation handles this.

### Guest reconnects from another device

```
Same raw token → new bootstrap → new chat_session grant issued
→ Both sessions valid (stateless grants, no session store)
→ Both subscribe to same booking channel via Pusher
→ Both see same messages
```
⚠️ **No session invalidation.** Old device keeps receiving events until grant expires (4h). No "max concurrent sessions" limit.

### Multiple staff read/send at same time

```
Staff A sends message while Staff B marks read:
→ No transaction isolation. Staff A's message may be immediately marked read by Staff B's concurrent update.
→ GuestConversationParticipant prevents duplicate joins (unique_together).
→ "Current handler" determined by latest joined_at — last-write-wins.
```
⚠️ No locking. Acceptable for hotel chat volume.

### Guest checked out during active chat

```
chat_session grant still valid for up to 4 hours.
→ GET messages: still works (resolve_chat_context_from_grant doesn't check checkout for reads)
→ POST send: blocked (checked_out_at validation in GuestChatSendMessageView)
→ Realtime: NotificationManager drops events if no active booking found
```
✅ Read access preserved. Write blocked. Events stop.

---

## 8. SECURITY

### Cross-guest access (Can guest access another guest's chat?)

❌ **Not possible in canonical flow.**
- `chat_session` grant contains `booking_id` signed with SECRET_KEY
- Grant is validated and cross-checked against URL `hotel_slug`
- Conversation resolved from grant's `booking_id` — cannot request another booking's conversation
- Pusher auth validates channel matches booking

### Cross-hotel access (Can staff access wrong hotel?)

✅ **Mostly protected.**
- Staff endpoints check `conversation.room.hotel.slug != hotel_slug` → 400
- `get_active_conversations` filters by `room__hotel=hotel`
- **⚠️ Exception:** `update_message`, `delete_message`, `delete_attachment` look up by message/attachment ID without hotel scoping. Staff authenticated via `IsAuthenticated` but not hotel-scoped — a staff member from Hotel A could theoretically PATCH a message in Hotel B by ID.

### Is chat_session guessable?

❌ **Not guessable.**
- `django.core.signing` uses HMAC-SHA256 with `SECRET_KEY` as key
- Salt: `"guest-chat-grant-v1"`
- Payload is timestamped (iat) + expires after 4 hours
- Cannot forge without SECRET_KEY

### Channel auth validation

✅ **Properly validated.**
- Guest Pusher auth endpoint validates session grant → extracts booking_id → computes expected channel → compares to requested channel
- HMAC-SHA256 signature computed server-side for Pusher
- Rejects channel_name mismatch with `CHANNEL_MISMATCH` error

### Critical Security Issues

| Issue | Severity | Details |
|---|---|---|
| **`update_message` has no hotel scoping** | ❌ Critical | `AllowAny` + no hotel validation. Any authenticated staff from any hotel can edit by message ID. Guest edit has no room/booking validation either — any anonymous request can edit any guest message. |
| **`delete_message` has no hotel scoping** | ❌ Critical | Same as above. `AllowAny` with message ID lookup only. Guest can potentially delete messages from other rooms. |
| **`delete_attachment` has no hotel scoping** | ❌ Critical | Same pattern. Attachment ID only, no booking/hotel cross-check. |
| **`mark_conversation_read` (staff URL) is AllowAny** | ⚠️ High | No session validation for guest callers. Anyone with a conversation ID can mark messages read. |
| **`upload_message_attachment` is AllowAny** | ⚠️ High | No session validation for guest callers. Someone could upload files to any conversation by ID. |
| **`save_fcm_token` is AllowAny, no auth** | ⚠️ Medium | Anyone who knows hotel_slug + room_number can overwrite the FCM token, hijacking push notifications for that room. |
| **Guest edit allows any guest message** | ⚠️ Medium | In `update_message`, guest edit path has `pass` for permissions — no room/conversation validation. |

---

## 9. PERFORMANCE

### Message Pagination

| Endpoint | Default limit | Cursor | Notes |
|---|---|---|---|
| Guest GET messages | 50 | `before_id` | Reverse chronological, cursor-based. `has_more` calculated via `count()` — **extra query**. |
| Staff GET messages | 10 | `before_id` | Same pattern. No `has_more` — frontend must detect end. |

⚠️ `has_more` uses `messages_qs.count()` which runs a full count query on each request. Should use `limit + 1` fetch pattern instead.

### DB Writes Per Message

**Guest sends message:**
1. `RoomMessage.objects.create()` — 1 INSERT
2. `Conversation.has_unread = True` → `save()` — 1 UPDATE (if not already unread)
3. `NotificationManager.realtime_guest_chat_message_created()` — 1 SELECT (active booking lookup)
4. Staff notification query — 1 SELECT (reception/front-office staff)
5. N Pusher triggers (1 per staff member + 1 booking channel)

**Staff sends message:**
1. `RoomMessage.objects.create()` — 1 INSERT
2. `GuestConversationParticipant.get_or_create()` — 1 SELECT + maybe 1 INSERT
3. If new participant: system message `RoomMessage.objects.create()` — 1 INSERT + 1 Pusher trigger
4. Handler change check — 1 SELECT
5. `NotificationManager.realtime_guest_chat_message_created()` — 1 SELECT (booking) + 1 Pusher + maybe FCM

**Total: 3-6 DB operations per message.** Acceptable for hotel chat volume.

### Read Receipt Overhead

**Guest marks read:**
- 1 bulk UPDATE (all unread staff/system messages)
- 1 UPDATE (conversation.has_unread)
- 1 Pusher trigger

**Staff marks read (assign-staff):**
- 1 SELECT (participant check)
- 1 possible INSERT (participant)
- 1 bulk UPDATE (unread guest messages)
- 1 UPDATE (conversation.has_unread)
- 1 Pusher trigger

**Acceptable overhead.** No N+1 queries in read status operations.

### Serializer N+1 Risks

⚠️ `ConversationSerializer.get_guest_name()` and `get_guest_id()` each run a DB query per conversation. With 50 active conversations, that's 100 extra queries. Missing `select_related` / annotation.

⚠️ `RoomMessageSerializer.get_guest_name()` same issue — DB query per message for guest name resolution.

⚠️ `get_reply_to_message()` accesses `obj.reply_to.attachments.all()[:3]` — potential N+1 on reply attachments. `select_related('reply_to')` exists in guest view but `prefetch_related('reply_to__attachments')` is missing.

---

## 10. FINAL VERDICT

### ✅ Solid Parts

- **Auth flow architecture** — Token → signed grant → session header is well-designed. HMAC-SHA256 via django.core.signing is cryptographically sound. 4-hour TTL is reasonable.
- **Booking-scoped conversations** — Conversations keyed by booking survive room moves. Channel naming is canonical (`private-hotel-{slug}-guest-chat-booking-{booking_id}`).
- **Message feature richness** — Reply threading, soft/hard delete, edit tracking, file attachments with Cloudinary all implemented.
- **System join messages** — Auto-generated when new staff enters conversation. Good UX signal.
- **Pusher auth** — Proper HMAC signature generation. Channel-to-booking cross-validation.
- **Throttling** — Guest endpoints have burst + sustained rate limiting.
- **NotificationManager unification** — Centralized realtime event emission. Events are normalized with consistent structure.

### ⚠️ Risky Areas

- **Realtime payload vs API serializer mismatch** — `conversation_id` in events = booking_id (string), in API = numeric DB ID. `sender_role` vs `sender_type`. Frontend must maintain mapping layer.
- **Staff read receipts not reaching guest** — Staff reads broadcast to conversation channel, guest only subscribes to booking channel. Guest never sees "Read" checkmarks.
- **No guest file upload endpoint** — Upload exists on staff URLs only. Guest cannot share photos.
- **`has_unread` denormalization** — No reconciliation mechanism. Can drift out of sync.
- **Session grant not revocable** — Checked-out guest retains read access until grant expires.
- **N+1 serializer queries** — `ConversationSerializer` and `RoomMessageSerializer` run per-object DB queries for guest name resolution.
- **`get_or_create_conversation_from_room` creates room-keyed conversations** — Inconsistent with booking-keyed canonical flow. Can create orphan conversations without booking FK.

### ❌ Broken / Missing

- **`update_message`, `delete_message`, `delete_attachment` have ZERO authorization gating** — AllowAny + no hotel/booking scoping. Any anonymous request can edit/delete any message by guessing the integer ID. **Critical security vulnerability.**
- **`mark_conversation_read` (staff URL) is AllowAny without session validation** — Anyone with conversation ID can mark messages read.
- **`upload_message_attachment` (staff URL) is AllowAny** — Anyone can upload files to any conversation.
- **`save_fcm_token` allows FCM token hijacking** — No auth, just hotel_slug + room_number.
- **Attachment deletion uses direct Pusher, not NotificationManager** — Bypasses the unified event architecture. Events go to legacy channels that guest may not subscribe to.
- **`delete_message` / `delete_attachment` emit to legacy channels** — `{slug}-room-{room_number}-deletions` and `{slug}-conversation-{id}-chat` instead of canonical booking channel.
- **Internal events not in bootstrap response** — `GUEST_CHAT_INTERNAL_EVENTS` (deleted, edited, unread_updated) are NOT returned in bootstrap `events` payload. Guest frontend must hardcode these event names.

### 🚀 What MUST Be Built Next (Priority Order)

1. **🔒 Add hotel + ownership scoping to `update_message`, `delete_message`, `delete_attachment`** — Cross-check message belongs to caller's hotel. Validate guest ownership via session grant. This is a P0 security fix.

2. **🔒 Add session validation to `mark_conversation_read`, `upload_message_attachment`** — Guest callers MUST present valid `X-Guest-Chat-Session`. Staff callers validated via `IsAuthenticated` + hotel match.

3. **🔒 Secure `save_fcm_token`** — Require either staff auth or guest session to save token.

4. **📡 Fix staff read receipts for guest** — Broadcast `messages-read-by-staff` to booking channel (not just conversation channel) so guest actually receives it.

5. **📡 Include internal events in bootstrap response** — Return `GUEST_CHAT_INTERNAL_EVENTS` alongside `GUEST_CHAT_EVENTS` so guest frontend knows all event names.

6. **📡 Migrate attachment deletion to NotificationManager** — Use booking channel for consistency. Remove legacy channel broadcasts.

7. **📤 Add guest file upload endpoint** — `POST /api/guest/hotel/{slug}/chat/upload` with session validation.

8. **📐 Normalize API response shape** — Staff GET messages should return `{ messages, count, has_more }` matching guest contract. Align default limits.

9. **⚡ Fix N+1 serializer queries** — Add `select_related`/`prefetch_related` for guest name resolution and reply attachments.

10. **📐 Normalize realtime payload** — Align `conversation_id` (use numeric DB ID everywhere), `sender_role`→`sender_type`, include full message serializer shape in events.
