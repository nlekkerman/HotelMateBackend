# Realtime Sender Identity Audit — `chat.message.created` Payload

**Date:** 2026-03-28  
**Scope:** Strict code-truth audit of how `chat.message.created` realtime payload is built, and what is required to populate it with real guest/staff names.

---

## 1. EXACT FUNCTION THAT BUILDS THE REALTIME PAYLOAD

### The builder

**File:** `notifications/notification_manager.py`  
**Function:** `NotificationManager.realtime_guest_chat_message_created(self, message)` — line 685

This is the **only** function that builds and emits the `chat.message.created` realtime event. Every call chain converges here.

### Call chains

#### Guest sends message (canonical flow)

```
hotel/canonical_guest_chat_views.py → GuestChatSendMessageView.post()
  ├── RoomMessage.objects.create(booking=booking, room=room, sender_type='guest', ...)
  └── NotificationManager().realtime_guest_chat_message_created(message)
        ├── builds payload dict (HANDCRAFTED — not serializer)
        ├── _create_normalized_event() wraps in envelope
        ├── _notify_front_office_staff_of_guest_message() → per-staff Pusher
        ├── pusher_client.trigger(conversation_channel, "realtime_event", event_data) → staff chat UI
        └── _safe_pusher_trigger(booking_channel, "chat.message.created", event_data) → guest + staff
```

#### Staff sends message

```
chat/views.py → send_conversation_message()
  ├── RoomMessage.objects.create(room=room, sender_type='staff', staff=staff_instance, ...)
  │   ⚠️ NOTE: booking= NOT SET on this create call
  └── notification_manager.realtime_guest_chat_message_created(message)
        └── (same path as above)
```

#### System join message

```
chat/views.py → send_conversation_message() [staff branch]
  ├── GuestConversationParticipant.get_or_create()
  ├── RoomMessage.objects.create(sender_type='system', staff=None, ...)
  └── notification_manager.realtime_guest_chat_message_created(join_message)
        └── (same path as above)
```

---

## 2. WHERE `sender_name` IS CURRENTLY POPULATED

**Exact code** (notification_manager.py, lines 695-699):

```python
sender_role = message.sender_type  # "guest" or "staff"
sender_id = None
sender_name = "Guest"                 # ← HARDCODED DEFAULT

if sender_role == "staff" and message.staff:
    sender_id = message.staff.id
    sender_name = message.staff_display_name or f"{message.staff.first_name} {message.staff.last_name}"
```

### Logic by sender_type

| sender_type | sender_name result | sender_id result | Why |
|---|---|---|---|
| `"guest"` | `"Guest"` (hardcoded) | `None` | Code defaults to `"Guest"` and has **no branch** to resolve actual guest name |
| `"staff"` | Real name from `message.staff.first_name + last_name` or `message.staff_display_name` | `message.staff.id` | Staff FK is always set on staff messages. `staff_display_name` is auto-populated by `RoomMessage.save()` |
| `"system"` | `"Guest"` (hardcoded) | `None` | Falls through the default. `sender_role = "system"` doesn't match `"staff"`, so the if-block is skipped. System messages get `sender_name = "Guest"` — **wrong, should be `"System"` or null** |

### Root cause for guest messages showing `"Guest"`

There is literally **no code path** that resolves the actual guest name. The function receives a `message` object (RoomMessage instance) and:

1. Does NOT check `message.booking` (which has `primary_guest_name`)
2. Does NOT check the `current_booking` variable it queries 5 lines later for channel routing
3. Does NOT call any guest name helper

The `current_booking` is already queried at line 704 (`RoomBooking.objects.filter(assigned_room=message.room, ...)`). This booking has `primary_guest_name` available. The code just never uses it for `sender_name`.

---

## 3. IDENTITY DATA AVAILABLE AT EVENT-EMISSION TIME — GUEST MESSAGES

At the point where `realtime_guest_chat_message_created()` runs, the following objects are in scope:

### From the `message` argument (RoomMessage instance)

| Field | Available? | Value |
|---|---|---|
| `message.booking` | **DEPENDS ON CALL CHAIN** | ✅ Set to RoomBooking instance on guest canonical flow (`canonical_guest_chat_views.py` sets `booking=booking`). ❌ **NULL** on staff-initiated messages (`chat/views.py` does NOT pass `booking=`). |
| `message.booking.primary_first_name` | ✅ If booking FK set | Real first name |
| `message.booking.primary_last_name` | ✅ If booking FK set | Real last name |
| `message.booking.primary_guest_name` | ✅ If booking FK set | Property: `f"{primary_first_name} {primary_last_name}"` |
| `message.booking.guest_display_name` | ✅ If booking FK set | Property: `primary_guest_name or "Guest"` |
| `message.booking.primary_email` | ✅ If booking FK set | Guest email |
| `message.room` | ✅ Always set | Room instance |
| `message.conversation` | ✅ Always set | Conversation FK |
| `message.conversation.booking` | ✅ If conversation has booking FK | Another path to RoomBooking |

### From the `current_booking` variable queried inside the function

```python
current_booking = RoomBooking.objects.filter(
    assigned_room=message.room,
    checked_in_at__isnull=False,
    checked_out_at__isnull=True,
    status__in=['CONFIRMED', 'COMPLETED']
).first()
```

| Field | Available? | Value |
|---|---|---|
| `current_booking.primary_first_name` | ✅ | Real first name |
| `current_booking.primary_last_name` | ✅ | Real last name |
| `current_booking.primary_guest_name` | ✅ | `f"{first} {last}"` |
| `current_booking.guest_display_name` | ✅ | `primary_guest_name or "Guest"` |
| `current_booking.booking_id` | ✅ | Already used in payload |

**This booking is already loaded.** The query already happens. The guest name is RIGHT THERE and simply not used.

### Canonical helpers that exist

| Helper | File | Signature | Used where |
|---|---|---|---|
| `booking.primary_guest_name` | `hotel/models.py` line 1024 | `@property → f"{self.primary_first_name} {self.primary_last_name}"` | Used in `staff_views.py`, `payment_views.py`, `notification_manager.py` (other methods), `guest_urls.py` |
| `booking.guest_display_name` | `hotel/models.py` line 1128 | `@property → self.primary_guest_name or "Guest"` | Used in `email_service.py` |
| `RoomMessageSerializer.get_guest_name()` | `chat/serializers.py` line 114 | Queries RoomBooking from room, returns `primary_first_name + primary_last_name` | Used in message list API |
| `canonical_serializers.get_guest_display_name()` | `hotel/canonical_serializers.py` line 297 | Queries party PRIMARY role, returns `full_name` | Used in booking detail views |

---

## 4. IDENTITY DATA AVAILABLE AT EVENT-EMISSION TIME — STAFF MESSAGES

At the point where `realtime_guest_chat_message_created()` runs for staff messages:

### From the `message` argument

| Field | Available? | Value | Currently used? |
|---|---|---|---|
| `message.staff` | ✅ Always set for staff messages | Staff instance | ✅ Used |
| `message.staff.id` | ✅ | Integer | ✅ → `sender_id` |
| `message.staff.first_name` | ✅ | String | ✅ → `sender_name` fallback |
| `message.staff.last_name` | ✅ | String | ✅ → `sender_name` fallback |
| `message.staff_display_name` | ✅ Auto-set by `RoomMessage.save()` | Full name string | ✅ → `sender_name` primary |
| `message.staff_role_name` | ✅ Auto-set by `RoomMessage.save()` | Role name string | ❌ NOT used in payload |
| `message.staff.role` | ✅ If select_related | Role object | ❌ NOT used |
| `message.staff.department` | ✅ If select_related | Department object | ❌ NOT used |
| `message.staff.profile_image` | ✅ | Image field | ❌ NOT used |

### What the RoomMessageSerializer provides but realtime drops

The `RoomMessageSerializer.get_staff_info()` returns:
```python
{
    'name': staff_display_name or f"{first} {last}",
    'role': staff_role_name or role.name,
    'department': department.name,
    'profile_image': profile_image.url
}
```

**None of this is in the realtime payload.**

---

## 5. SERIALIZER VS HANDCRAFTED PAYLOAD

### Current state: HANDCRAFTED

The realtime payload is handcrafted in `realtime_guest_chat_message_created()` at line 722:

```python
payload = {
    'conversation_id': current_booking.booking_id,      # STRING (booking_id)
    'booking_id': current_booking.booking_id,            # STRING duplicate
    'room_conversation_id': message.conversation.id,     # INT (DB id)
    'id': message.id,                                    # INT
    'sender_role': sender_role,                          # "guest"/"staff"/"system"
    'sender_id': sender_id,                              # null / staff.id
    'sender_name': sender_name,                          # "Guest" / staff name
    'message': message.message,                          # text
    'timestamp': message.timestamp.isoformat(),          # ISO string
    'room_number': message.room.room_number,             # INT
    'is_staff_reply': sender_role == "staff",            # bool
    'has_attachments': message.attachments.exists(),     # bool (triggers query)
    'pin': getattr(message.room, 'pin', None)           # nullable
}
```

### What `RoomMessageSerializer` provides but realtime DROPS

| Serializer field | In realtime? | Notes |
|---|---|---|
| `sender_type` | ❌ Uses `sender_role` instead | Name mismatch |
| `staff_name` | ❌ | Dropped |
| `guest_name` | ❌ | Dropped (shows "Guest" instead) |
| `staff_info` | ❌ | Dropped entirely (name, role, department, profile_image) |
| `booking_id` | ⚠️ | Present but as `conversation_id` too (confusing) |
| `conversation_id` (numeric) | ❌ Uses `room_conversation_id` instead | Different field name |
| `read_by_staff` | ❌ | Dropped |
| `read_by_guest` | ❌ | Dropped |
| `is_edited` | ❌ | Dropped |
| `is_deleted` | ❌ | Dropped |
| `reply_to` | ❌ | Dropped |
| `reply_to_message` | ❌ | Dropped |
| `attachments` (full detail) | ❌ | Only `has_attachments` bool |
| `staff_display_name` | ❌ | Dropped |
| `staff_role_name` | ❌ | Dropped |
| `status` | ❌ | Dropped |
| `delivered_at` | ❌ | Dropped |

**Total serializer fields: 30. Realtime payload fields: 13. Drop rate: 57%.**

---

## 6. CANONICAL GUEST DISPLAY NAME HELPERS

### Helpers that already exist in the codebase

| Helper | Location | Logic | Safe for display? |
|---|---|---|---|
| `RoomBooking.primary_guest_name` | `hotel/models.py:1024` | `f"{self.primary_first_name} {self.primary_last_name}"` | ✅ Full name, no masking |
| `RoomBooking.guest_display_name` | `hotel/models.py:1128` | `self.primary_guest_name or "Guest"` | ✅ **Best candidate** — has fallback |
| `RoomMessageSerializer.get_guest_name()` | `chat/serializers.py:114` | Queries current booking by room → `primary_first_name + primary_last_name`. Fallback: legacy `guests_in_room` | ⚠️ Runs extra DB query |
| `ConversationSerializer.get_guest_name()` | `chat/serializers.py:302` | Same logic as above (duplicated) | ⚠️ Runs extra DB query |
| `StaffRoomBookingDetailSerializer.get_guest_display_name()` | `hotel/canonical_serializers.py:297` | Queries party PRIMARY role → `full_name` | Overkill for chat |

### No standalone utility function

There is **no** `get_guest_display_name(booking)` utility function. The logic is repeated in:
- Model properties (`primary_guest_name`, `guest_display_name`)
- Serializer methods (`get_guest_name`)
- Inline code (`f"Dear {booking.primary_guest_name or 'Guest'}"`)

The `booking.guest_display_name` property is the **canonical** answer — it's already the safest pattern with built-in fallback.

---

## 7. WHAT `sender_name` SHOULD BE FOR GUEST MESSAGES

### Current data flow

```
Guest bootstrap → resolve_guest_access() → booking (with primary_first_name, primary_last_name)
                                          ↓
Guest sends message → RoomMessage.create(booking=booking)
                                          ↓
NotificationManager → current_booking = RoomBooking.objects.filter(room=...).first()
                    → ✅ current_booking.primary_guest_name exists
                    → ❌ IGNORES IT, hardcodes "Guest"
```

### Recommendation based on code truth

**Use `current_booking.guest_display_name`** — which is `current_booking.primary_guest_name or "Guest"`.

Rationale:
- `primary_first_name` and `primary_last_name` are **REQUIRED fields** on `RoomBooking` (see model: `models.CharField(max_length=100, help_text="Primary guest first name (person staying)")` — no `blank=True`)
- `guest_display_name` already has a `"Guest"` fallback for safety
- This is the **same pattern** used by `email_service.py` for guest-facing emails
- Full name is already exposed in `RoomMessageSerializer.get_guest_name()` for API responses — the frontend already sees the real name in message lists
- No masking needed — the guest is chatting directly with hotel staff. Both parties know who the guest is.

---

## 8. ADDITIONAL FIELDS THAT CAN BE ADDED IMMEDIATELY

### Using already-loaded objects (ZERO new queries)

The following are available from `message` + `current_booking` which are already loaded:

| Field | Source | Extra query? | Should add? |
|---|---|---|---|
| `sender_name` (real guest) | `current_booking.guest_display_name` | ❌ No (already queried) | ✅ YES — fixes the "Guest" problem |
| `sender_type` | `message.sender_type` | ❌ No | ✅ YES — normalize `sender_role` → `sender_type` |
| `guest_name` | `current_booking.guest_display_name` | ❌ No | ✅ YES — matches serializer |
| `staff_name` | `message.staff_display_name` (already set on save) | ❌ No | ✅ YES — matches serializer |
| `staff_info` | Build from `message.staff`, `message.staff_role_name` | ❌ No (fields on message) | ✅ YES |
| `read_by_staff` | `message.read_by_staff` | ❌ No | ✅ YES (always `False` for new) |
| `read_by_guest` | `message.read_by_guest` | ❌ No | ✅ YES (always `False` for new) |
| `is_edited` | `message.is_edited` | ❌ No | ✅ YES (always `False` for new) |
| `is_deleted` | `message.is_deleted` | ❌ No | ✅ YES (always `False` for new) |
| `status` | `message.status` | ❌ No | ✅ YES (`"delivered"`) |
| `reply_to` | `message.reply_to_id` | ❌ No | ✅ YES |
| `booking_id` | `current_booking.booking_id` | ❌ No | Already present |
| `room_number` | `message.room.room_number` | ❌ No | Already present |
| `conversation_id` (numeric) | `message.conversation.id` | ❌ No | Already in `room_conversation_id` — should be normalized |

### Would require new query

| Field | Extra query needed | Worth it? |
|---|---|---|
| `staff_info.profile_image` URL | `message.staff.profile_image` — may need FK follow | ⚠️ Small, do with `select_related` |
| `staff_info.department` | `message.staff.department.name` — FK follow | ⚠️ Small, do with `select_related` |
| `attachments` (full detail) | `message.attachments.all()` — already called for `has_attachments` | ⚠️ Replace `.exists()` with fetch |
| `reply_to_message` (preview) | `message.reply_to` + its attachments | ⚠️ Extra query, defer to phase 2 |

---

## 9. DATABASE/QUERY IMPACT AUDIT

### Current queries in `realtime_guest_chat_message_created()`

| # | Query | Purpose | Lines |
|---|---|---|---|
| 1 | `RoomBooking.objects.filter(assigned_room=message.room, ...).first()` | Resolve current_booking for channel routing | 704-708 |
| 2 | `message.attachments.exists()` | Check has_attachments | 735 |
| 3 | `Staff.objects.filter(hotel=..., role__slug="receptionist", is_active=True)` | Find notification targets (guest msgs only) | 1425-1428 in `_notify_front_office_staff_of_guest_message` |

### If we add real sender names

**Query 1 (current_booking) already loads the booking.** Adding `current_booking.guest_display_name` to the payload = **ZERO additional queries**. It's a property computed from `primary_first_name` / `primary_last_name` which are already loaded by the filter.

**Staff name data** is already on the `message` object — `message.staff_display_name` and `message.staff_role_name` are auto-populated by `RoomMessage.save()`. **ZERO additional queries.**

### For `staff_info` with department/profile_image

Would need `message.staff.department` and `message.staff.profile_image`. These are FK follows. Can be solved by adding `select_related('staff__department', 'staff__role')` when the message is created/fetched. But since the message is freshly created in the same request, the staff instance is already loaded from `request.user.staff_profile`. The real concern:

- In `chat/views.py`: `staff_instance = getattr(request.user, "staff_profile", None)` — this loads `staff` but may not have `department`/`role` pre-loaded.
- Adding `.select_related('department', 'role')` to the staff lookup would fix it, but it's a change in the view, not the notification manager.

**Recommendation:** For min-change approach, use the already-available `message.staff_display_name` and `message.staff_role_name` (populated by `RoomMessage.save()`) and skip department/profile_image in phase 1.

---

## 10. FINAL OUTPUT

### ✅ Identity data already available NOW (zero changes needed to access)

- `current_booking.primary_guest_name` → real guest full name (from booking DB query already in the function)
- `current_booking.guest_display_name` → same with `"Guest"` fallback
- `current_booking.primary_first_name` / `primary_last_name` → individual name parts
- `message.staff.id` → staff numeric ID (already used)
- `message.staff_display_name` → staff full name (auto-set on save)
- `message.staff_role_name` → staff role name (auto-set on save)
- `message.staff.first_name` / `last_name` → fallback (already used)
- `message.read_by_staff` / `read_by_guest` → read status booleans
- `message.is_edited` / `message.is_deleted` → mutation flags
- `message.status` → delivery status
- `message.reply_to_id` → thread parent

### ⚠️ Data currently being LOST (available but not in payload)

| Lost field | Available via | Impact |
|---|---|---|
| **Real guest name** | `current_booking.guest_display_name` | Frontend shows "Guest" for all guest messages instead of "Jane Doe" |
| **Guest name on staff notification** | same | Staff notification badges show "Guest" instead of real name |
| `sender_type` (consistent naming) | `message.sender_type` | Frontend must map `sender_role` → `sender_type` |
| `staff_info` object | `message.staff_display_name` + `message.staff_role_name` | Frontend can't show staff role/avatar in realtime messages |
| `staff_name` | `message.staff_display_name` | No direct field match with serializer |
| `guest_name` | `current_booking.guest_display_name` | No direct field match with serializer |
| `read_by_staff` / `read_by_guest` | `message` fields | Frontend can't initialize read status from realtime event |
| `is_edited` / `is_deleted` | `message` fields | Frontend can't know if message arrived as edited/deleted |
| `reply_to` / `reply_to_message` | `message.reply_to_id` | Frontend can't render reply preview from realtime event |
| `status` | `message.status` | Frontend can't initialize delivery status |
| Attachment details | `message.attachments.all()` | Only `has_attachments` bool — no file URLs, names, types |

### ❌ What is WRONG with current realtime payload generation

1. **`sender_name` is hardcoded `"Guest"` for ALL guest messages.** The `current_booking` with the real name is already loaded 8 lines below where `sender_name` is set. The data is right there — it's just not used.

2. **System messages get `sender_name = "Guest"`.** The code has no branch for `sender_type == "system"`. System join messages like "John Smith has joined the conversation" get `sender_name = "Guest"` and `sender_role = "system"`.

3. **`sender_role` instead of `sender_type`.** API serializer uses `sender_type`. Realtime payload uses `sender_role`. Frontend must maintain a mapping layer for no reason.

4. **`conversation_id` is a string booking_id.** API serializer returns `conversation_id` as numeric DB ID. Realtime payload returns it as `"BK-NOWAYHOT-2026-0002"`. The numeric ID is buried in `room_conversation_id`.

5. **Payload shape is incompatible with `RoomMessageSerializer`.** The frontend cannot use the same data structure for API messages and realtime messages. Different field names (`sender_role` vs `sender_type`, `sender_name` vs `staff_name`/`guest_name`), missing fields, different ID formats.

6. **`_notify_front_office_staff_of_guest_message` also hardcodes `"Guest"`.** Line 1470: `"sender_name": "Guest"`. Staff notification badges show "Guest" instead of the actual guest name, even though the payload already contains the booking_id and the message object has booking FK.

7. **`has_attachments` triggers a separate `.exists()` query.** If we later want to include attachment details, we're already paying for a query — might as well fetch the actual data.

### 🚀 MINIMUM BACKEND CHANGES NEEDED

**Single file change: `notifications/notification_manager.py`**

**Change 1:** Fix `sender_name` for guest messages (3 lines)

Current (line 695-699):
```python
sender_role = message.sender_type
sender_id = None
sender_name = "Guest"

if sender_role == "staff" and message.staff:
    sender_id = message.staff.id
    sender_name = message.staff_display_name or f"{message.staff.first_name} {message.staff.last_name}"
```

Should be:
```python
sender_role = message.sender_type
sender_id = None
sender_name = "Guest"  # Fallback — overridden below for all sender types

if sender_role == "staff" and message.staff:
    sender_id = message.staff.id
    sender_name = message.staff_display_name or f"{message.staff.first_name} {message.staff.last_name}"
elif sender_role == "system":
    sender_name = "System"
# Guest name resolved after current_booking lookup (below)
```

Then after the `current_booking` query (after line 714), add:
```python
# Resolve real guest name from the booking we already loaded
if sender_role == "guest" and current_booking:
    sender_name = current_booking.guest_display_name  # "Jane Doe" or "Guest" fallback
```

**Change 2:** Enrich payload with already-available data (in the payload dict)

Add to the existing payload dict:
```python
'sender_type': sender_role,           # Alias for API consistency
'guest_name': current_booking.guest_display_name if current_booking else "Guest",
'staff_name': message.staff_display_name if message.staff else None,
'staff_info': {
    'name': message.staff_display_name or f"{message.staff.first_name} {message.staff.last_name}",
    'role': message.staff_role_name or (message.staff.role.name if message.staff and message.staff.role else 'Staff'),
} if sender_role == "staff" and message.staff else None,
'read_by_staff': message.read_by_staff,
'read_by_guest': message.read_by_guest,
'is_edited': message.is_edited,
'is_deleted': message.is_deleted,
'status': message.status,
'reply_to': message.reply_to_id,
```

**Change 3:** Fix staff notification sender_name

In `_notify_front_office_staff_of_guest_message()` (line 1470), change:
```python
"sender_name": "Guest",
```
to:
```python
"sender_name": payload.get('sender_name', 'Guest'),
```

This reuses the already-corrected `sender_name` from the payload.

**Total: ~15 lines changed in 1 file. Zero new DB queries. Zero new dependencies.**
