# Guest ↔ Staff Chat — Realtime & Retrieval Logic Audit

> **Generated:** 2026-03-28  
> **Scope:** Full end-to-end audit of how messages are sent via realtime (Pusher) and how messages are retrieved (REST API) for both guest chat and staff-to-staff chat systems.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Guest Chat — Sending Messages (Realtime)](#2-guest-chat--sending-messages-realtime)
3. [Guest Chat — Retrieving Messages](#3-guest-chat--retrieving-messages)
4. [Staff-Facing Guest Chat — Sending & Retrieving](#4-staff-facing-guest-chat--sending--retrieving)
5. [Staff-to-Staff Chat — Sending Messages (Realtime)](#5-staff-to-staff-chat--sending-messages-realtime)
6. [Staff-to-Staff Chat — Retrieving Messages](#6-staff-to-staff-chat--retrieving-messages)
7. [Pusher Channel Architecture](#7-pusher-channel-architecture)
8. [Pusher Configuration & Client Setup](#8-pusher-configuration--client-setup)
9. [Authentication & Authorization](#9-authentication--authorization)
10. [NotificationManager — Central Realtime Hub](#10-notificationmanager--central-realtime-hub)
11. [FCM Push Notifications](#11-fcm-push-notifications)
12. [Read Receipts & Unread Tracking](#12-read-receipts--unread-tracking)
13. [Message Edit, Delete & Reply Flows](#13-message-edit-delete--reply-flows)
14. [File Attachments](#14-file-attachments)
15. [Data Models Reference](#15-data-models-reference)
16. [URL Routing Reference](#16-url-routing-reference)
17. [File Map](#17-file-map)

---

## 1. Architecture Overview

The backend has **two distinct chat systems** with a **shared realtime infrastructure**:

| System | App | Users | Channel Pattern | Auth |
|--------|-----|-------|-----------------|------|
| **Guest Chat** | `chat/` | Guest ↔ Staff | `private-hotel-{slug}-guest-chat-booking-{booking_id}` | Signed session grant (HMAC-SHA256) |
| **Staff Chat** | `staff_chat/` | Staff ↔ Staff | `{hotel_slug}-conversation-{conversation_id}-chat` | Django `IsAuthenticated` + staff profile |

**Shared infrastructure:**

- **Pusher** — All realtime events (open-app experience)
- **FCM (Firebase)** — Push notifications (closed-app experience)
- **NotificationManager** (`notifications/notification_manager.py`) — Single entry point for all realtime events
- **Pusher client** (`chat/utils.py`) — Shared Pusher SDK instance

```
┌──────────────┐     ┌──────────────────────┐     ┌─────────────┐
│  Guest App   │────▶│   Django REST API     │────▶│   Pusher    │
│  (Flutter)   │◀────│                       │◀────│   (Events)  │
└──────────────┘     │  NotificationManager  │     └─────────────┘
                     │                       │     ┌─────────────┐
┌──────────────┐     │  chat/views.py        │────▶│   FCM       │
│  Staff App   │────▶│  staff_chat/views.py  │     │   (Push)    │
│  (Flutter)   │◀────│  canonical_guest_*    │     └─────────────┘
└──────────────┘     └──────────────────────┘
```

---

## 2. Guest Chat — Sending Messages (Realtime)

### 2.1 Bootstrap (One-time setup)

**Endpoint:** `GET /api/guest/hotel/{slug}/chat/context?token=RAW_TOKEN`  
**View:** `GuestChatContextView` in `hotel/canonical_guest_chat_views.py`  
**Auth:** Raw guest booking token (used ONCE, never accepted again)

**Flow:**
1. Guest app sends raw booking token as query param
2. `resolve_guest_access()` validates token via SHA-256 hash lookup against `GuestBookingToken` or fallback `BookingManagementToken`
3. `issue_guest_chat_grant()` creates a signed HMAC-SHA256 session grant (4-hour TTL)
4. `Conversation.objects.get_or_create(booking=booking)` resolves/creates conversation
5. Returns **complete realtime config** to the guest app:

```json
{
  "conversation_id": 42,
  "chat_session": "<signed-grant-token>",
  "channel_name": "private-hotel-killarney-guest-chat-booking-BK-2025-0003",
  "events": {
    "message_created": "chat.message.created",
    "message_read": "chat.message.read"
  },
  "pusher": {
    "key": "<PUSHER_KEY>",
    "cluster": "eu",
    "auth_endpoint": "/api/guest/hotel/killarney/chat/pusher/auth"
  },
  "permissions": {
    "can_send": true,
    "can_read": true
  }
}
```

### 2.2 Pusher Auth (Channel subscription)

**Endpoint:** `POST /api/guest/hotel/{slug}/chat/pusher/auth`  
**View:** `GuestChatPusherAuthView` in `hotel/canonical_guest_chat_views.py`  
**Auth:** `X-Guest-Chat-Session` header (signed grant)

**Flow:**
1. Guest Pusher client sends `socket_id` + `channel_name`
2. View validates session grant via `validate_guest_chat_grant()`
3. Verifies `channel_name` matches expected `private-hotel-{slug}-guest-chat-booking-{booking_id}`
4. Generates HMAC-SHA256 auth signature: `PUSHER_KEY:signature`
5. Returns `{"auth": "key:sig", "channel_data": "..."}`
6. Guest can now subscribe to the private channel

### 2.3 Guest Sends a Message

**Endpoint:** `POST /api/guest/hotel/{slug}/chat/messages`  
**View:** `GuestChatSendMessageView.post()` in `hotel/canonical_guest_chat_views.py`  
**Auth:** `X-Guest-Chat-Session` header

**End-to-End Flow:**

```
Guest App → POST /chat/messages { message: "Need towels" }
    │
    ▼
1. validate_guest_chat_grant() → booking, room, conversation
2. Enforce in-house checks (checked_in, not checked_out, room assigned)
3. RoomMessage.objects.create(sender_type='guest', message=text, booking=booking, room=room)
    │
    ▼
4. notification_manager.realtime_guest_chat_message_created(message)
    │
    ├──▶ Build payload:
    │     { id, conversation_id (=booking_id), sender_role, message, room_number, ... }
    │
    ├──▶ Pusher trigger → channel: private-hotel-{slug}-guest-chat-booking-{booking_id}
    │     event: "chat.message.created"
    │     (Guest app receives this in realtime)
    │
    ├──▶ Pusher trigger → channel: {slug}-conversation-{conv_id}-chat
    │     event: "realtime_event"  
    │     (Staff chat interface receives this so staff see guest messages)
    │
    ├──▶ _notify_front_office_staff_of_guest_message()
    │     Target: Receptionists → Front Office → Any active staff
    │     Channel: {slug}.staff-{staff_id}-notifications
    │     Event: "new-guest-message"
    │     (Staff notification bell / badge)
    │
    └──▶ Response: { message_id, sent_at, conversation_id }
```

**Key architectural decisions:**
- `conversation_id` in the Pusher payload is always `booking_id` (string, e.g. `"BK-2025-0003"`), NOT the DB integer ID — this ensures the channel survives room changes
- The DB `conversation.id` is sent as `room_conversation_id` for legacy compatibility
- If no active booking exists for the room, the message is **silently dropped** by NotificationManager

### 2.4 Guest Chat Event Constants

Defined in `common/guest_chat_config.py` (single source of truth):

```python
# Channel pattern
def guest_chat_channel(hotel_slug, booking_id):
    return f"private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}"

# Frontend contract events
GUEST_CHAT_EVENTS = {
    "message_created": "chat.message.created",
    "message_read": "chat.message.read",
}

# Internal broadcast events
GUEST_CHAT_INTERNAL_EVENTS = {
    "message_deleted": "chat.message.deleted",
    "message_edited": "chat.message.edited",
    "unread_updated": "chat.unread.updated",
}
```

---

## 3. Guest Chat — Retrieving Messages

### 3.1 Get Messages (Guest-side)

**Endpoint:** `GET /api/guest/hotel/{slug}/chat/messages`  
**View:** `GuestChatSendMessageView.get()` in `hotel/canonical_guest_chat_views.py`  
**Auth:** `X-Guest-Chat-Session` header

**Query params:**
- `limit` — Max messages to return (default: 50)
- `before_id` — Cursor for pagination (load older messages)

**Logic:**
```python
messages_qs = conversation.messages.filter(
    is_deleted=False,
).select_related('reply_to').order_by('-timestamp')

if before_id:
    messages_qs = messages_qs.filter(id__lt=before_id)

messages = list(messages_qs[:limit])[::-1]  # Reverse to oldest-first
```

**Response:**
```json
{
  "messages": [ ...RoomMessageSerializer... ],
  "conversation_id": 42,
  "count": 20,
  "has_more": true
}
```

### 3.2 Get Messages (Staff-side, viewing guest conversations)

**Endpoint:** `GET /api/staff/hotel/{slug}/chat/{slug}/conversations/{id}/messages/`  
**View:** `get_conversation_messages()` in `chat/views.py`  
**Auth:** `IsAuthenticated` (Django staff auth)

**Query params:**
- `limit` — Messages per page (default: 10)
- `before_id` — Cursor pagination

**Logic:**
```python
messages_qs = conversation.messages.order_by('-timestamp')
if before_id:
    messages_qs = messages_qs.filter(id__lt=before_id)
messages = messages_qs[:limit][::-1]  # Reverse to oldest-first
```

### 3.3 Get Active Conversations (Staff dashboard)

**Endpoint:** `GET /api/staff/hotel/{slug}/chat/{slug}/conversations/`  
**View:** `get_active_conversations()` in `chat/views.py`

Returns all guest conversations for the hotel, ordered by most recent activity.

### 3.4 Get or Create Conversation from Room

**Endpoint:** `POST /api/staff/hotel/{slug}/chat/{slug}/conversations/from-room/{room_number}/`  
**View:** `get_or_create_conversation_from_room()` in `chat/views.py`

Staff opens a chat for a specific room. Returns existing conversation or creates a new one.

---

## 4. Staff-Facing Guest Chat — Sending & Retrieving

### 4.1 Staff Sends Message to Guest

**Endpoint:** `POST /api/staff/hotel/{slug}/chat/{slug}/conversations/{id}/messages/send/`  
**View:** `send_conversation_message()` in `chat/views.py`  
**Auth:** `IsAuthenticated`

**Flow:**
```
Staff App → POST /conversations/{id}/messages/send/ { message: "Towels on the way!" }
    │
    ▼
1. Determine sender: staff_profile → sender_type="staff"
2. RoomMessage.objects.create(sender_type='staff', staff=staff_instance, ...)
3. GuestConversationParticipant.get_or_create() — track staff as participant
4. If NEW participant → create system message "{Name} has joined the conversation"
    │
    ▼
5. notification_manager.realtime_guest_chat_message_created(message)
    │
    ├──▶ Pusher → booking-scoped channel → event: "chat.message.created"
    │     (Guest app receives this live)
    │
    ├──▶ FCM push to guest: room.guest_fcm_token
    │     title: "Reply from {staff_name}"
    │     body: message[:100]
    │
    └──▶ Response: { conversation_id, message: {...} }
```

**Staff assignment/handoff:**
- Any staff who sends a message becomes a participant
- System messages announce when a new staff member joins
- Previous handlers remain as participants (no removal)
- `GuestConversationParticipant` tracks join timestamps

---

## 5. Staff-to-Staff Chat — Sending Messages (Realtime)

### 5.1 Staff Sends Message

**Primary Endpoint:** `POST /api/staff/hotel/{slug}/staff_chat/conversations/{id}/send-message/`  
**View:** `send_message()` in `staff_chat/views_messages.py`  
**Auth:** `IsAuthenticated` + `IsStaffMember` + `IsSameHotel`

**End-to-End Flow:**

```
Staff App → POST /conversations/{id}/send-message/ { message: "Meeting at 3pm @John" }
    │
    ▼
1. Verify staff is participant of conversation
2. Parse @mentions from message text (regex: @(\w+(?:\s+\w+)?))
3. StaffChatMessage.objects.create(conversation, sender, message, reply_to)
4. message.mentions.set(mentioned_staff)
5. conversation.save()  — triggers updated_at for sort order
    │
    ▼
6. notification_manager.realtime_staff_chat_message_created(message)
    │
    ├──▶ Build payload:
    │     { id, conversation_id, message, sender_id, sender_name, sender_avatar,
    │       timestamp, images[], reply_to{}, has_attachments }
    │
    ├──▶ Pusher → channel: {slug}-conversation-{conv_id}-chat
    │     event: "realtime_staff_chat_message_created"
    │     (All conversation participants see this live)
    │
    ├──▶ For each participant (excluding sender):
    │     Pusher → channel: {slug}-staff-{staff_id}-notifications
    │     event: "realtime_staff_chat_unread_updated"
    │     payload: { unread_count, conversation_id }
    │     (Updates badge/unread count in sidebar)
    │
    │     If first unread in this conversation:
    │       event: "realtime_staff_chat_conversations_with_unread"  
    │       payload: { conversations_with_unread: N }
    │       (Updates conversation count badge)
    │
    ▼
7. notify_conversation_participants(message)  [FCM]
    │
    ├──▶ For each participant with fcm_token (excluding sender):
    │     FCM push: title="New Message from {name}", body=message[:200]
    │
    ├──▶ For each @mentioned staff:
    │     FCM push: title="{name} mentioned you", body=message[:200]
    │
    └──▶ Response: { success: true, message: {...serialized...} }
```

### 5.2 Legacy Send Endpoint

**Endpoint:** `POST /api/staff/hotel/{slug}/staff_chat/conversations/{pk}/send_message/`  
**View:** `StaffConversationViewSet.send_message()` in `staff_chat/views.py`

Same logic but routed through the ViewSet action. Kept for backward compatibility.

---

## 6. Staff-to-Staff Chat — Retrieving Messages

### 6.1 Get Conversations List

**Endpoint:** `GET /api/staff/hotel/{slug}/staff_chat/conversations/`  
**View:** `StaffConversationViewSet.list()` in `staff_chat/views.py`

Returns conversations where the staff is a participant, ordered by `-updated_at`. Supports search and ordering.

### 6.2 Get Conversation Detail

**Endpoint:** `GET /api/staff/hotel/{slug}/staff_chat/conversations/{id}/`  
**View:** `StaffConversationViewSet.retrieve()` in `staff_chat/views.py`

Returns conversation detail with last 50 messages via `StaffConversationDetailSerializer`.

### 6.3 Get Messages with Pagination

**Endpoint:** `GET /api/staff/hotel/{slug}/staff_chat/conversations/{id}/messages/`  
**View:** `get_conversation_messages()` in `staff_chat/views_messages.py`

Supports cursor-based pagination for infinite scroll on the frontend.

### 6.4 Get Unread Counts

**Endpoint:** `GET /api/staff/hotel/{slug}/staff_chat/conversations/unread-count/`  
**View:** `StaffConversationViewSet.unread_count()` in `staff_chat/views.py`

Returns total unread message count across all conversations for the requesting staff member.

**Endpoint:** `GET /api/staff/hotel/{slug}/staff_chat/conversations/conversations-with-unread-count/`  

Returns number of conversations that have at least one unread message (for badge count).

---

## 7. Pusher Channel Architecture

### 7.1 Guest Chat Channels

| Channel | Pattern | Purpose |
|---------|---------|---------|
| **Guest chat** | `private-hotel-{slug}-guest-chat-booking-{booking_id}` | All guest chat messages (both directions). Booking-scoped, survives room moves |
| **Staff conversation** | `{slug}-conversation-{conversation_id}-chat` | Staff sees guest messages in their chat interface |
| **Staff notifications** | `{slug}.staff-{staff_id}-notifications` | New guest message alerts for front office |

### 7.2 Staff Chat Channels

| Channel | Pattern | Purpose |
|---------|---------|---------|
| **Conversation** | `{slug}-conversation-{conversation_id}-chat` | Message events for all participants |
| **Staff notifications** | `{slug}-staff-{staff_id}-notifications` | Unread counts + conversation counts |

### 7.3 Event Names

**Guest Chat Events:**
| Event | Name | Trigger |
|-------|------|---------|
| Message created | `chat.message.created` | Guest/staff sends message |
| Message read | `chat.message.read` | Guest/staff marks messages read |
| Message deleted | `chat.message.deleted` | Message soft-deleted |
| Message edited | `chat.message.edited` | Message edited |
| Unread updated | `chat.unread.updated` | Unread count changes |
| New guest message | `new-guest-message` | Guest sends (→ staff notifications channel) |
| Read by staff | `messages-read-by-staff` | Staff reads messages (→ conversation channel) |

**Staff Chat Events:**
| Event | Name | Trigger |
|-------|------|---------|
| Message created | `realtime_staff_chat_message_created` | Staff sends message |
| Message edited | `realtime_staff_chat_message_edited` | Message edited |
| Unread updated | `realtime_staff_chat_unread_updated` | New message for participant |
| Conversations unread | `realtime_staff_chat_conversations_with_unread` | First unread in conversation |

---

## 8. Pusher Configuration & Client Setup

### 8.1 Settings

**File:** `HotelMateBackend/settings.py`

```python
PUSHER_APP_ID = env('PUSHER_APP_ID')
PUSHER_KEY = env('PUSHER_KEY')        # Public key (sent to frontend)
PUSHER_CLUSTER = env('PUSHER_CLUSTER')
PUSHER_SECRET = env('PUSHER_SECRET')  # Secret (auth signatures only)
```

### 8.2 Pusher Client (Server-side)

**File:** `chat/utils.py`

```python
import pusher
from django.conf import settings

pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)
```

This single `pusher_client` instance is imported by:
- `notifications/notification_manager.py` — for all realtime events
- `notifications/pusher_utils.py` — for department/role notifications
- `chat/views.py` — for direct read-receipt triggers (legacy)

### 8.3 Safe Trigger Pattern

All Pusher events go through `NotificationManager._safe_pusher_trigger()`:

```python
def _safe_pusher_trigger(self, channel, event, data):
    try:
        pusher_client.trigger(channel, event, data)
        return True
    except Exception as e:
        logger.error(f"Pusher failed: {channel} → {event}: {e}")
        return False
```

---

## 9. Authentication & Authorization

### 9.1 Guest Authentication (Token → Session Grant)

**Phase 1: Bootstrap** (one-time, raw token)
1. Guest receives a `GuestBookingToken` at booking creation
2. Token sent via `?token=` query param or `GuestToken` header (`common/guest_auth.py → TokenAuthenticationMixin`)
3. `resolve_guest_access()` (`common/guest_access.py`) hashes token with SHA-256, looks up in DB
4. Returns `GuestAccessContext` with booking, room, scopes

**Phase 2: Session grant** (all subsequent requests)
1. Bootstrap issues a signed grant via `issue_guest_chat_grant()` (`common/guest_chat_grant.py`)
2. Grant claims: `booking_id`, `hotel_slug`, `room_id`, `room_number`, `scope="guest_chat"`, `iat`
3. Signed with `django.core.signing` (HMAC-SHA256 via `SECRET_KEY`)
4. Max age: 4 hours (`GUEST_CHAT_GRANT_MAX_AGE_SECONDS`)
5. All subsequent requests use `X-Guest-Chat-Session` header (`ChatSessionAuthenticationMixin`)
6. `validate_guest_chat_grant()` verifies signature + expiry + hotel scope

**In-house enforcement (send only):**
- Must have `checked_in_at` set
- Must NOT have `checked_out_at` set
- Must have room assigned
- Read access is always allowed

### 9.2 Staff Authentication

- Standard Django `IsAuthenticated` permission
- `request.user.staff_profile` resolves the `Staff` model instance
- Staff chat adds: `IsStaffMember`, `IsConversationParticipant`, `IsMessageSender`, `IsSameHotel`, `CanDeleteMessage` (`staff_chat/permissions.py`)
- Hotel scoping: staff must belong to the same hotel as the URL's `hotel_slug`

### 9.3 Pusher Auth for Guests

**Endpoint:** `POST /api/guest/hotel/{slug}/chat/pusher/auth`

```python
# 1. Validate session grant
grant_ctx = validate_guest_chat_grant(session_str, hotel_slug)

# 2. Verify channel matches booking
expected = guest_chat_channel(hotel_slug, booking.booking_id)
assert channel_name == expected

# 3. Generate HMAC-SHA256 signature
string_to_sign = f"{socket_id}:{channel_name}:{channel_data_json}"
signature = hmac.new(PUSHER_SECRET, string_to_sign, sha256).hexdigest()

# 4. Return auth
{"auth": "PUSHER_KEY:signature", "channel_data": "..."}
```

---

## 10. NotificationManager — Central Realtime Hub

**File:** `notifications/notification_manager.py`  
**Singleton:** `notification_manager = NotificationManager()`

All realtime events are routed through this class. It provides:

### 10.1 Normalized Event Structure

Every Pusher event follows this envelope:

```json
{
  "category": "guest_chat | staff_chat | attendance | room_service | booking",
  "type": "event_type_string",
  "payload": { "...domain-specific data..." },
  "meta": {
    "hotel_slug": "killarney",
    "event_id": "uuid4",
    "ts": "ISO-8601",
    "scope": { "...targeting info..." }
  }
}
```

### 10.2 Guest Chat Methods

| Method | Purpose | Channel | Event |
|--------|---------|---------|-------|
| `realtime_guest_chat_message_created(message)` | New message (guest or staff) | booking channel | `chat.message.created` |
| `realtime_guest_chat_unread_updated(room, count)` | Unread count change | booking channel | `chat.unread.updated` |
| `realtime_guest_chat_message_deleted(...)` | Soft delete broadcast | booking channel | `chat.message.deleted` |
| `realtime_guest_chat_message_edited(message)` | Edit broadcast | booking channel | `chat.message.edited` |

### 10.3 Staff Chat Methods

| Method | Purpose | Channel | Event |
|--------|---------|---------|-------|
| `realtime_staff_chat_message_created(message)` | New message | conversation channel + notification channels | `realtime_staff_chat_message_created` |
| `realtime_staff_chat_message_edited(message)` | Edit broadcast | conversation channel | `realtime_staff_chat_message_edited` |
| `realtime_staff_chat_unread_updated(staff, conv)` | Unread count | staff notification channel | `realtime_staff_chat_unread_updated` |
| `realtime_staff_chat_conversations_with_unread(staff)` | Conversation count badge | staff notification channel | `realtime_staff_chat_conversations_with_unread` |

### 10.4 Internal Helper

`_notify_front_office_staff_of_guest_message(message, payload, hotel_slug)`:
- Target priority: Receptionists → Front Office dept → Any active staff
- Sends `new-guest-message` event to each staff member's notification channel
- Channel pattern: `{slug}.staff-{staff_id}-notifications`

---

## 11. FCM Push Notifications

### 11.1 Guest Chat FCM

**When staff replies to guest:**
```python
if sender_role == "staff" and message.room.guest_fcm_token:
    send_fcm_notification(
        token=message.room.guest_fcm_token,
        title=f"Reply from {sender_name}",
        body=message.message[:100],
        data={"type": "staff_reply", "room_number": ..., "conversation_id": ...}
    )
```
Triggered inside `realtime_guest_chat_message_created()`.

**When guest sends message (to staff):**
- FCM notifications to staff are handled via `_notify_front_office_staff_of_guest_message()` (Pusher only currently) and the legacy flow in `chat/views.py`.

### 11.2 Staff Chat FCM

**File:** `staff_chat/fcm_utils.py`

`notify_conversation_participants(message)`:
- Sends FCM to all participants (except sender) who have `fcm_token`
- Sends separate mention notifications to @mentioned staff
- Sends file-specific notifications for attachment messages

---

## 12. Read Receipts & Unread Tracking

### 12.1 Guest Chat Read Tracking

**Model fields on `RoomMessage`:**
- `read_by_staff` (bool) + `staff_read_at` (datetime)
- `read_by_guest` (bool) + `guest_read_at` (datetime)
- `status`: `pending` → `delivered` → `read`

**Staff marks read:**
`POST /api/staff/hotel/{slug}/chat/conversations/{id}/mark-read/`
- Updates `read_by_staff=True`, `staff_read_at=now`, `status='read'` on all unread guest messages
- Pusher → `{slug}-conversation-{conv_id}-chat` → event: `messages-read-by-staff`
- Clears `conversation.has_unread` flag
- Triggers `realtime_guest_chat_unread_updated(room, 0)`

**Guest marks read:**
`POST /api/guest/hotel/{slug}/chat/conversations/{id}/mark_read/`
- Updates `read_by_guest=True`, `guest_read_at=now`, `status='read'` on staff/system messages
- Broadcasts `chat.message.read` on the booking channel

### 12.2 Staff Chat Read Tracking

**Model:** `StaffChatMessage.read_by` — M2M to `Staff`

**Per-message read:**
`POST /api/staff/hotel/{slug}/staff_chat/messages/{id}/mark-as-read/`
- `message.mark_as_read_by(staff)` — adds staff to M2M
- Broadcasts read receipt via `pusher_utils.broadcast_read_receipt()`

**Bulk mark read:**
`POST /api/staff/hotel/{slug}/staff_chat/conversations/bulk-mark-as-read/`
- Marks all unread messages in specified conversations as read

**Unread count calculation:**
```python
def get_unread_count_for_staff(self, staff):
    return self.messages.filter(is_deleted=False).exclude(sender=staff).exclude(read_by=staff).count()
```

---

## 13. Message Edit, Delete & Reply Flows

### 13.1 Guest Chat

**Edit:** `PUT /api/staff/hotel/{slug}/chat/messages/{id}/update/` → `update_message()` in `chat/views.py`
- Updates message text, sets `is_edited=True`, `edited_at=now`
- Broadcasts via `realtime_guest_chat_message_edited(message)`

**Delete:** `DELETE /api/staff/hotel/{slug}/chat/messages/{id}/delete/` → `delete_message()` in `chat/views.py`  
- Soft delete: `message.soft_delete()` → sets `is_deleted=True`, replaces text with `[Message deleted]`
- Broadcasts via `realtime_guest_chat_message_deleted(...)`

**Reply:** `reply_to` field in POST body
- Creates FK to parent `RoomMessage`
- Serializer includes `reply_to_message` with preview data

### 13.2 Staff Chat

**Edit:** `PUT /api/staff/hotel/{slug}/staff_chat/messages/{id}/edit/` → `edit_message()`
- Only sender can edit
- Broadcasts via `realtime_staff_chat_message_edited(message)`

**Delete:** `DELETE /api/staff/hotel/{slug}/staff_chat/messages/{id}/delete/` → `delete_message()`
- Soft delete with placeholder text
- Permission: `CanDeleteMessage` (sender or admin)

**Reply:** `reply_to` field links to parent `StaffChatMessage`
- NotificationManager builds full reply preview with image attachments (up to 3)

**Reactions:** `POST /api/staff/hotel/{slug}/staff_chat/messages/{id}/react/`
- `StaffMessageReaction` model with emoji + staff FK
- Toggle behavior: add or remove

**Forward:** `POST /api/staff/hotel/{slug}/staff_chat/messages/{id}/forward/`
- Copies message to one or more conversations

---

## 14. File Attachments

### 14.1 Guest Chat Attachments

**Model:** `MessageAttachment` (in `chat/models.py`)
- `file`: CloudinaryField, max 50MB
- `thumbnail`: CloudinaryField for image previews
- `file_type`: image/document/video/audio/other
- `mime_type`: auto-detected

**Upload:** `POST /api/staff/hotel/{slug}/chat/conversations/{id}/upload-attachment/`

### 14.2 Staff Chat Attachments

**Model:** `StaffChatAttachment` (in `staff_chat/models.py`)
- `file`: CloudinaryField
- `file_type`: image/document/video/audio/other
- `file_name`, `file_size`, `mime_type`

**Upload:** `POST /api/staff/hotel/{slug}/staff_chat/conversations/{id}/upload/`
**Delete:** `DELETE /api/staff/hotel/{slug}/staff_chat/attachments/{id}/delete/`
**Get URL:** `GET /api/staff/hotel/{slug}/staff_chat/attachments/{id}/url/`

---

## 15. Data Models Reference

### 15.1 Guest Chat Models (`chat/models.py`)

**Conversation**
| Field | Type | Purpose |
|-------|------|---------|
| `room` | FK → Room | Optional room context |
| `booking` | FK → RoomBooking | Booking that owns this conversation |
| `participants_staff` | M2M → Staff | Staff in the conversation |
| `has_unread` | bool | Quick unread flag |

**RoomMessage**
| Field | Type | Purpose |
|-------|------|---------|
| `conversation` | FK → Conversation | Parent conversation |
| `room` | FK → Room | Room context |
| `booking` | FK → RoomBooking | Booking association |
| `sender_type` | char | `guest` / `staff` / `system` |
| `staff` | FK → Staff | Staff sender (null for guests) |
| `message` | text | Message content |
| `status` | char | `pending` / `delivered` / `read` |
| `read_by_staff` / `read_by_guest` | bool | Read flags |
| `staff_read_at` / `guest_read_at` | datetime | Read timestamps |
| `is_edited` / `is_deleted` | bool | Edit/delete flags |
| `reply_to` | FK → self | Reply parent |
| `staff_display_name` / `staff_role_name` | char | Auto-populated from staff profile |

**GuestConversationParticipant**
| Field | Type | Purpose |
|-------|------|---------|
| `conversation` | FK → Conversation | Which conversation |
| `staff` | FK → Staff | Which staff joined |
| `joined_at` | datetime | When they joined |

**MessageAttachment**
| Field | Type | Purpose |
|-------|------|---------|
| `message` | FK → RoomMessage | Parent message |
| `file` | CloudinaryField | The file |
| `file_type` | char | image/document/video/audio/other |
| `thumbnail` | CloudinaryField | Image preview |

### 15.2 Staff Chat Models (`staff_chat/models.py`)

**StaffConversation**
| Field | Type | Purpose |
|-------|------|---------|
| `hotel` | FK → Hotel | Hotel scope |
| `participants` | M2M → Staff | Chat members |
| `title` | char | Optional group name |
| `is_group` | bool | Auto-set based on participant count |
| `created_by` | FK → Staff | Creator |
| `group_avatar` | CloudinaryField | Group image |
| `is_archived` | bool | Hidden from main list |
| `has_unread` | bool | Quick unread flag |

**StaffChatMessage**
| Field | Type | Purpose |
|-------|------|---------|
| `conversation` | FK → StaffConversation | Parent conversation |
| `sender` | FK → Staff | Who sent it |
| `message` | text | Content |
| `read_by` | M2M → Staff | Multi-recipient read tracking |
| `mentions` | M2M → Staff | @mentioned staff |
| `reply_to` | FK → self | Reply parent |
| `is_edited` / `is_deleted` | bool | Edit/delete flags |
| `status` | char | `pending` / `delivered` / `read` |

**StaffChatAttachment**
| Field | Type | Purpose |
|-------|------|---------|
| `message` | FK → StaffChatMessage | Parent message |
| `file` | CloudinaryField | The file |
| `file_type` | char | image/document/video/audio/other |

**StaffMessageReaction**
| Field | Type | Purpose |
|-------|------|---------|
| `message` | FK → StaffChatMessage | Which message |
| `staff` | FK → Staff | Who reacted |
| `emoji` | char | Reaction emoji |

---

## 16. URL Routing Reference

### 16.1 Guest Chat URLs (from `guest_urls.py`)

| Method | Path | View | Purpose |
|--------|------|------|---------|
| GET | `/api/guest/hotel/{slug}/chat/context?token=` | `GuestChatContextView` | Bootstrap (one-time) |
| GET | `/api/guest/hotel/{slug}/chat/messages` | `GuestChatSendMessageView.get` | Retrieve messages |
| POST | `/api/guest/hotel/{slug}/chat/messages` | `GuestChatSendMessageView.post` | Send message |
| POST | `/api/guest/hotel/{slug}/chat/conversations/{id}/mark_read/` | `GuestChatMarkReadView` | Mark read |
| POST | `/api/guest/hotel/{slug}/chat/pusher/auth` | `GuestChatPusherAuthView` | Pusher channel auth |

### 16.2 Staff-Facing Guest Chat URLs (from `chat/urls.py`)

| Method | Path | View | Purpose |
|--------|------|------|---------|
| GET | `/{slug}/active-rooms/` | `get_active_rooms` | Rooms with conversations |
| GET | `/{slug}/conversations/` | `get_active_conversations` | All guest conversations |
| GET | `/{slug}/conversations/{id}/messages/` | `get_conversation_messages` | Paginated messages |
| POST | `/{slug}/conversations/{id}/messages/send/` | `send_conversation_message` | Staff sends to guest |
| POST | `/{slug}/conversations/from-room/{num}/` | `get_or_create_conversation_from_room` | Open chat for room |
| GET | `/{slug}/conversations/unread-count/` | `get_unread_count` | Unread per room |
| GET | `/hotels/{slug}/conversations/unread-count/` | `get_unread_conversation_count` | Unread conversations |
| POST | `/conversations/{id}/mark-read/` | `mark_conversation_read` | Mark read |
| POST | `/{slug}/conversations/{id}/assign-staff/` | `assign_staff_to_conversation` | Staff handoff |
| PUT | `/messages/{id}/update/` | `update_message` | Edit message |
| DELETE | `/messages/{id}/delete/` | `delete_message` | Soft delete |
| POST | `/{slug}/conversations/{id}/upload-attachment/` | `upload_message_attachment` | Upload file |
| DELETE | `/attachments/{id}/delete/` | `delete_attachment` | Remove file |
| POST | `/{slug}/save-fcm-token/` | `save_fcm_token` | Register FCM token |

### 16.3 Staff-to-Staff Chat URLs (from `staff_chat/urls.py`)

| Method | Path | View | Purpose |
|--------|------|------|---------|
| GET | `/staff-list/` | `StaffListViewSet` | Staff for chat UI |
| GET/POST | `/conversations/` | `StaffConversationViewSet` | List/create conversations |
| GET | `/conversations/{id}/` | `StaffConversationViewSet` | Conversation detail |
| POST | `/conversations/{id}/send-message/` | `send_message` | Send message |
| GET | `/conversations/{id}/messages/` | `get_conversation_messages` | Paginated messages |
| POST | `/messages/{id}/mark-as-read/` | `mark_message_as_read` | Mark individual read |
| PUT | `/messages/{id}/edit/` | `edit_message` | Edit message |
| DELETE | `/messages/{id}/delete/` | `delete_message` | Soft delete |
| POST | `/messages/{id}/react/` | `add_reaction` | Add reaction |
| DELETE | `/messages/{id}/react/{emoji}/` | `remove_reaction` | Remove reaction |
| POST | `/messages/{id}/forward/` | `forward_message` | Forward to conversations |
| POST | `/conversations/{id}/upload/` | `upload_attachments` | Upload files |
| DELETE | `/attachments/{id}/delete/` | `delete_attachment` | Remove file |
| GET | `/attachments/{id}/url/` | `get_attachment_url` | Get download URL |
| GET | `/conversations/unread-count/` | unread_count action | Total unread |
| GET | `/conversations/conversations-with-unread-count/` | conversations_with_unread_count | Conversations with unread |
| POST | `/conversations/bulk-mark-as-read/` | bulk_mark_as_read | Bulk mark read |

---

## 17. File Map

| File | Purpose |
|------|---------|
| `chat/models.py` | Guest chat data models (Conversation, RoomMessage, MessageAttachment) |
| `chat/views.py` | Staff-facing guest chat API (CRUD, send, read, handoff) |
| `chat/serializers.py` | Guest chat serializers (RoomMessageSerializer, etc.) |
| `chat/urls.py` | Staff-facing guest chat URL routing |
| `chat/utils.py` | Shared Pusher client instance |
| `hotel/canonical_guest_chat_views.py` | Guest-facing chat API (bootstrap, send, retrieve, mark-read, Pusher auth) |
| `common/guest_chat_config.py` | Channel names + event constants (single source of truth) |
| `common/guest_chat_grant.py` | Session grant issue + validate (HMAC-SHA256) |
| `common/guest_access.py` | Raw token → booking resolution (SHA-256 hash lookup) |
| `common/guest_auth.py` | Token extraction mixins + throttle classes |
| `staff_chat/models.py` | Staff chat data models (StaffConversation, StaffChatMessage, etc.) |
| `staff_chat/views.py` | Staff chat conversations ViewSet |
| `staff_chat/views_messages.py` | Staff chat message operations (send, edit, delete, react, forward) |
| `staff_chat/views_attachments.py` | Staff chat file upload/delete/URL |
| `staff_chat/urls.py` | Staff chat URL routing |
| `staff_chat/permissions.py` | Staff chat permissions (IsStaffMember, IsConversationParticipant, etc.) |
| `staff_chat/fcm_utils.py` | FCM push notifications for staff chat |
| `staff_chat/pusher_utils.py` | Legacy Pusher utils (mostly deprecated, use NotificationManager) |
| `notifications/notification_manager.py` | **Central realtime hub** — all Pusher + FCM events |
| `notifications/pusher_utils.py` | Department/role-based Pusher notifications |
| `notifications/fcm_service.py` | FCM service (send_fcm_notification, multicast) |
| `guest_urls.py` | Guest zone URL routing wrapper |
| `staff_urls.py` | Staff zone URL routing wrapper |
