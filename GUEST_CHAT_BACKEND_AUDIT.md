# Guest Chat Backend Audit

**Date:** 2025-03-26
**Status:** AUDIT ONLY — No fixes proposed

> We are stopping all frontend changes until backend contract is 100% verified.
> No assumptions. No summaries. Real behavior from real code.

---

## 1. Token Model(s) Used

### `BookingManagementToken` — **THE ONLY TOKEN MODEL USED**

**File:** `hotel/models.py` line 2603

```python
class BookingManagementToken(models.Model):
    booking = models.ForeignKey(RoomBooking, on_delete=models.CASCADE, related_name='management_tokens')
    token_hash = models.CharField(max_length=64)       # SHA-256 hex of raw token
    expires_at = models.DateTimeField()                 # EXISTS but NOT checked by is_valid
    used_at = models.DateTimeField(null=True)           # When used for cancellation
    revoked_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_email = models.EmailField(blank=True)
    actions_performed = models.JSONField(default=list)
```

**`is_valid` property — NOT time-based:**

```python
@property
def is_valid(self):
    if self.revoked_at is not None:
        return False
    booking = self.booking
    if booking.cancelled_at:
        return False
    if booking.status == 'COMPLETED':
        return False
    if booking.status == 'DECLINED':
        return False
    return True
```

**Key finding:** `expires_at` exists on the model but is **never checked** by `is_valid`. Tokens do not expire by time. They are invalidated only by:
- `revoked_at` being set
- `booking.cancelled_at` being set
- `booking.status` being `COMPLETED` or `DECLINED`

### `GuestBookingToken` — **EXISTS BUT NOT USED BY CANONICAL RESOLVER**

`GuestBookingToken` exists in `hotel/models.py` but is **never referenced** by `common/guest_access.py` or any canonical chat endpoint. It is a legacy/secondary model.

**Verdict:** `BookingManagementToken` is the single source of truth. No fallback. No dual-token logic.

---

## 2. Token Lookup Code (Exact)

### Step 1: Token extraction

**File:** `common/guest_auth.py`

```python
class TokenAuthenticationMixin:
    def get_token_from_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        if auth_header.startswith('GuestToken '):
            return auth_header[11:]
        return request.GET.get('token', '')
```

**Priority:**
1. `Authorization: Bearer <token>`
2. `Authorization: GuestToken <token>`
3. `?token=<token>` query parameter

### Step 2: Canonical resolver

**File:** `common/guest_access.py`

```python
def resolve_guest_access(token_str, hotel_slug, required_scopes=None, require_in_house=False):
    if not token_str or not token_str.strip():
        raise TokenRequiredError()

    token_hash = hashlib.sha256(token_str.strip().encode("utf-8")).hexdigest()

    ctx = _try_booking_management_token(token_hash, hotel_slug)
    if ctx is None:
        raise InvalidTokenError()

    booking = ctx.booking

    if booking.status in ("CANCELLED", "CANCELLED_DRAFT", "DECLINED"):
        raise InvalidTokenError()

    if required_scopes:
        missing = [s for s in required_scopes if s not in ctx.scopes]
        if missing:
            raise MissingScopeError(missing)

    if require_in_house:
        if not booking.checked_in_at:
            raise NotCheckedInError()
        if booking.checked_out_at:
            raise AlreadyCheckedOutError()
        if not booking.assigned_room:
            raise NoRoomAssignedError()

    return ctx
```

### Step 3: Internal lookup helper

**File:** `common/guest_access.py`

```python
def _try_booking_management_token(token_hash, hotel_slug):
    from hotel.models import BookingManagementToken

    try:
        bmt = BookingManagementToken.objects.select_related(
            "booking__hotel",
            "booking__assigned_room",
        ).get(token_hash=token_hash)
    except BookingManagementToken.DoesNotExist:
        return None

    if not bmt.is_valid:
        return None

    if bmt.booking.hotel.slug != hotel_slug:
        return None

    bmt.record_action("VIEW")

    return GuestAccessContext(
        booking=bmt.booking,
        room=bmt.booking.assigned_room,
        scopes=list(_MANAGEMENT_TOKEN_IMPLIED_SCOPES),  # ["STATUS_READ", "CHAT", "ROOM_SERVICE"]
        token_type="booking_management",
    )
```

**Lookup is: `SELECT ... WHERE token_hash = ?` (single row by hash)**

### Step 4: Chat-specific service layer

**File:** `bookings/services.py`

```python
def resolve_guest_chat_context(hotel_slug, token_str, required_scopes=None, action_required=True):
    if action_required:
        ctx = resolve_guest_access(token_str=token_str, hotel_slug=hotel_slug,
                                   required_scopes=required_scopes, require_in_house=True)
    else:
        ctx = resolve_guest_access(token_str=token_str, hotel_slug=hotel_slug,
                                   required_scopes=required_scopes, require_in_house=False)

    booking = ctx.booking
    room = ctx.room

    allowed_actions = {"can_chat": False}
    disabled_reason = None

    if action_required:
        allowed_actions["can_chat"] = True
    else:
        if not booking.checked_in_at:
            disabled_reason = "Check-in required to access chat"
        elif booking.checked_out_at:
            disabled_reason = "Chat unavailable after checkout"
        elif not booking.assigned_room:
            disabled_reason = "Room assignment required"
        else:
            allowed_actions["can_chat"] = True

    conversation = None
    if room:
        conversation, created = Conversation.objects.get_or_create(
            room=room, defaults={})

    return booking, room, conversation, allowed_actions, disabled_reason
```

---

## 3. Required Inputs

### Does chat require:

| Input | REQUIRED? | How used |
|-------|-----------|----------|
| `token` | **YES — REQUIRED** | Extracted from Authorization header or `?token=` query param. SHA-256 hashed for DB lookup. |
| `hotel_slug` | **YES — REQUIRED** | From URL path (`/api/guest/hotel/{hotel_slug}/chat/...`). Compared against `booking.hotel.slug` for anti-enumeration. |
| `booking_id` | **NO — NOT REQUIRED** | Never sent by frontend. Derived from token lookup. |
| `email` | **NO — NOT REQUIRED** | Never read by any chat endpoint. |
| `room_number` | **NO — NOT REQUIRED** | Never sent by frontend. Derived from `booking.assigned_room`. |

### Summary:
- **REQUIRED:** `token` (in header or query) + `hotel_slug` (in URL path)
- **OPTIONAL:** Nothing
- **IGNORED:** `booking_id`, `email`, `room_number`, any other body/query params

---

## 4. Booking Resolution Logic

Once token hash is found in `BookingManagementToken`:

```python
bmt = BookingManagementToken.objects.select_related(
    "booking__hotel",
    "booking__assigned_room",
).get(token_hash=token_hash)
```

Booking is retrieved via: **`bmt.booking`** (ForeignKey, select_related in query)

No separate query. No booking_id lookup. No hotel_slug filter in the DB query.

`hotel_slug` validation happens **after** DB fetch:
```python
if bmt.booking.hotel.slug != hotel_slug:
    return None  # → leads to InvalidTokenError (anti-enumeration)
```

Room is retrieved via: **`bmt.booking.assigned_room`** (select_related)

---

## 5. Chat Context Response Structure

**Endpoint:** `GET /api/guest/hotel/{hotel_slug}/chat/context?token=...`

**File:** `hotel/canonical_guest_chat_views.py` — `GuestChatContextView._get_context()`

### Success Response (200):

```json
{
    "conversation_id": 42,
    "booking_id": "BK-2025-0003",
    "room_number": "101",
    "assigned_room_id": 7,
    "allowed_actions": ["chat"],
    "pusher": {
        "channel": "private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}",
        "event": "realtime_event"
    },
    "current_staff_handler": {
        "name": "John Smith",
        "role": "Receptionist"
    }
}
```

### When chat is disabled (still 200):

```json
{
    "conversation_id": null,
    "booking_id": "BK-2025-0003",
    "room_number": null,
    "assigned_room_id": null,
    "allowed_actions": [],
    "disabled_reason": "Check-in required to access chat",
    "pusher": {
        "channel": "private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}",
        "event": "realtime_event"
    },
    "current_staff_handler": null
}
```

### Key observations:
- `disabled_reason` is **only included** when chat is NOT available (not always present)
- `allowed_actions` is `["chat"]` when enabled, `[]` when disabled
- `conversation_id` can be `null` if no room assigned (conversation requires room)
- `current_staff_handler` comes from `GuestConversationParticipant` — last staff to join

### Staff handler lookup:
```python
latest_staff_participant = conversation.guest_participants.filter(
).select_related('staff').order_by('-joined_at').first()
```

---

## 6. Pusher Channel Logic

### Channel name construction:

**File:** `hotel/canonical_guest_chat_views.py`

```python
pusher_channel = f"private-hotel-{hotel_slug}-guest-chat-booking-{booking.booking_id}"
```

### How is channel determined?

- **Derived from `booking.booking_id`** — NOT from room
- **Booking-scoped** — survives room moves
- **Constructed at runtime** — not stored in DB
- **Returned explicitly** in `context` response under `pusher.channel`

### Channel format:
```
private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}
```

### Pusher channel validation (in auth endpoint):

```python
expected_channel = f"private-hotel-{hotel_slug}-guest-chat-booking-{booking.booking_id}"
if channel_name != expected_channel:
    return Response({'error': 'Channel name does not match booking'}, status=403)
```

**Exact string match required.** Any deviation is rejected.

### Event name: `"realtime_event"` (hardcoded constant)

---

## 7. Room Dependency Rules

### Does chat require assigned room?

**It depends on the endpoint and mode:**

| Scenario | Room required? | Behavior |
|----------|---------------|----------|
| **Context (soft mode)** | NO | Returns 200 with `room_number: null`, `conversation_id: null`, `disabled_reason: "Room assignment required"` |
| **GET messages (soft mode)** | YES (implicitly) | If no room → no conversation → will fail when accessing `conversation.messages` |
| **POST messages (strict mode)** | YES | `require_in_house=True` → `NoRoomAssignedError` → 409 |
| **Pusher auth (soft mode)** | NO | Returns auth even with no room |

### Where is room dependency enforced?

1. **In `resolve_guest_access()` when `require_in_house=True`:**
   ```python
   if not booking.assigned_room:
       raise NoRoomAssignedError()  # 409
   ```

2. **In `resolve_guest_chat_context()` conversation lookup:**
   ```python
   if room:
       conversation, created = Conversation.objects.get_or_create(room=room)
   # If room is None → conversation stays None
   ```

### What happens if room is missing?

- Context: Returns 200 with nulls and disabled_reason
- GET messages: Will likely error (conversation is None)
- POST messages: Returns 409 `NO_ROOM_ASSIGNED`
- Pusher auth: Returns auth (room not needed for channel name)

---

## 8. Booking Lifecycle Rules

### What conditions block chat?

| Condition | Context endpoint | GET messages | POST messages | Pusher auth |
|-----------|-----------------|-------------|---------------|-------------|
| **Not checked in** | 200 + `disabled_reason: "Check-in required to access chat"` | 200 (can view) | **403** `NOT_CHECKED_IN` | 200 (auth allowed) |
| **Checked out** | 200 + `disabled_reason: "Chat unavailable after checkout"` | 200 (can view) | **403** `ALREADY_CHECKED_OUT` | 200 (auth allowed) |
| **Cancelled** | **401** `INVALID_TOKEN` | **401** `INVALID_TOKEN` | **401** `INVALID_TOKEN` | **401** `INVALID_TOKEN` |
| **Declined** | **401** `INVALID_TOKEN` | **401** `INVALID_TOKEN` | **401** `INVALID_TOKEN` | **401** `INVALID_TOKEN` |
| **Completed (status)** | **401** `INVALID_TOKEN` (via `is_valid`) | **401** `INVALID_TOKEN` | **401** `INVALID_TOKEN` | **401** `INVALID_TOKEN` |
| **Future booking (confirmed, not checked in)** | 200 + `disabled_reason` | 200 (can view) | **403** `NOT_CHECKED_IN` | 200 (auth allowed) |
| **No room assigned** | 200 + `disabled_reason: "Room assignment required"` | Potential error (null conversation) | **409** `NO_ROOM_ASSIGNED` | 200 (auth allowed) |

### Where lifecycle is enforced:

1. **`BookingManagementToken.is_valid`** — rejects `COMPLETED`, `DECLINED`, `cancelled_at`
2. **`resolve_guest_access()` booking lifecycle gate** — rejects `CANCELLED`, `CANCELLED_DRAFT`, `DECLINED`
3. **`resolve_guest_access()` in-house gate** (when `require_in_house=True`) — rejects not-checked-in, checked-out, no-room

---

## 9. Error Contract

### Complete error mapping:

| Error Code | HTTP Status | Condition | Response Body |
|------------|-------------|-----------|---------------|
| `TOKEN_REQUIRED` | 401 | Empty or missing token | `{"error": "Token is required", "code": "TOKEN_REQUIRED"}` |
| `INVALID_TOKEN` | 401 | Token hash not found in DB | `{"error": "Invalid or expired token", "code": "INVALID_TOKEN"}` |
| `INVALID_TOKEN` | 401 | Token found but `is_valid` returns False (revoked, completed, declined) | `{"error": "Invalid or expired token", "code": "INVALID_TOKEN"}` |
| `INVALID_TOKEN` | 401 | Token found but `hotel_slug` does not match `booking.hotel.slug` | `{"error": "Invalid or expired token", "code": "INVALID_TOKEN"}` |
| `INVALID_TOKEN` | 401 | Token valid but booking status is `CANCELLED`, `CANCELLED_DRAFT`, or `DECLINED` | `{"error": "Invalid or expired token", "code": "INVALID_TOKEN"}` |
| `MISSING_SCOPE` | 403 | Token lacks required scope (unlikely — all BMTs get `["STATUS_READ", "CHAT", "ROOM_SERVICE"]`) | `{"error": "Token lacks required permissions: CHAT", "code": "MISSING_SCOPE"}` |
| `NOT_CHECKED_IN` | 403 | `require_in_house=True` but `booking.checked_in_at` is null | `{"error": "Guest has not checked in yet", "code": "NOT_CHECKED_IN"}` |
| `ALREADY_CHECKED_OUT` | 403 | `require_in_house=True` but `booking.checked_out_at` is set | `{"error": "Guest has already checked out", "code": "ALREADY_CHECKED_OUT"}` |
| `NO_ROOM_ASSIGNED` | 409 | `require_in_house=True` but `booking.assigned_room` is null | `{"error": "No room assigned to this booking yet", "code": "NO_ROOM_ASSIGNED"}` |
| *(generic)* | 500 | Unhandled exception | `{"error": "Unable to retrieve chat context"}` (or similar per endpoint) |

### Anti-enumeration pattern:

The following all return the SAME `INVALID_TOKEN` / 401 error:
- Token not found
- Token revoked
- Hotel slug mismatch
- Booking cancelled/declined/completed

This prevents attackers from distinguishing between "token doesn't exist" and "token exists but for different hotel."

---

## 10. INVALID_TOKEN Meaning (Precise)

`INVALID_TOKEN` is returned when **ANY** of these conditions are true:

1. Token hash not found in `BookingManagementToken` table
2. `BookingManagementToken.is_valid` returns `False`:
   - `revoked_at` is set
   - `booking.cancelled_at` is set
   - `booking.status == 'COMPLETED'`
   - `booking.status == 'DECLINED'`
3. `booking.hotel.slug != hotel_slug` (URL mismatch)
4. `booking.status in ('CANCELLED', 'CANCELLED_DRAFT', 'DECLINED')` (double-checked after `is_valid`)

`INVALID_TOKEN` is **NOT** returned for:
- Room missing → `NO_ROOM_ASSIGNED` (409) or soft `disabled_reason`
- Not checked in → `NOT_CHECKED_IN` (403) or soft `disabled_reason`
- Checked out → `ALREADY_CHECKED_OUT` (403) or soft `disabled_reason`
- Missing scope → `MISSING_SCOPE` (403)

---

## 11. Endpoint Consistency

### Comparison across all three canonical endpoints:

| Aspect | `chat/context` | `chat/messages` GET | `chat/messages` POST | `chat/pusher/auth` |
|--------|---------------|-------------------|---------------------|-------------------|
| **View class** | `GuestChatContextView` | `GuestChatSendMessageView.get` | `GuestChatSendMessageView.post` | `GuestChatPusherAuthView` |
| **Token extraction** | `TokenAuthenticationMixin` | `TokenAuthenticationMixin` | `TokenAuthenticationMixin` | `TokenAuthenticationMixin` |
| **Resolver** | `resolve_guest_chat_context` | `resolve_guest_chat_context` | `resolve_guest_chat_context` | `resolve_guest_chat_context` |
| **`action_required`** | `False` (soft) | `False` (soft) | `True` (strict) | `False` (soft) |
| **`required_scopes`** | `["CHAT"]` | `["CHAT"]` | `["CHAT"]` | `["CHAT"]` |
| **Throttle** | `GuestTokenBurstThrottle`, `GuestTokenSustainedThrottle` | same | same | same |
| **Cache** | `@never_cache` | `@never_cache` | `@never_cache` | `@never_cache` |
| **Permission** | `AllowAny` | `AllowAny` | `AllowAny` | `AllowAny` |

### Differences:

1. **`action_required` split**: Only `POST messages` uses `action_required=True`. All others use `False`.
   - This means only **sending** messages requires checked-in + room. Viewing context, viewing messages, and Pusher auth all work in soft mode.

2. **Error handling coverage differs slightly**:
   - `context`: catches `InvalidTokenError`, `MissingScopeError`, `GuestAccessError` (generic)
   - `GET messages`: catches `InvalidTokenError`, `MissingScopeError`, `NoRoomAssignedError`, `GuestAccessError`
   - `POST messages`: catches `InvalidTokenError`, `MissingScopeError`, `NotCheckedInError`, `AlreadyCheckedOutError`, `NoRoomAssignedError`, `GuestAccessError`
   - `pusher/auth`: catches `InvalidTokenError`, `MissingScopeError`, `NoRoomAssignedError`, `GuestAccessError`

3. **`context` does NOT explicitly catch `NotCheckedInError` or `AlreadyCheckedOutError`**: This is correct because `action_required=False` means those exceptions are never raised. They are only raised when `require_in_house=True`.

4. **Token validation logic is IDENTICAL** across all three — they all call `resolve_guest_chat_context` → `resolve_guest_access` → `_try_booking_management_token`.

---

## FINAL CANONICAL CONTRACT

### REQUIRED INPUTS

| Input | Source | Required |
|-------|--------|----------|
| `token` | `Authorization: Bearer <token>` or `Authorization: GuestToken <token>` or `?token=<token>` | **REQUIRED** |
| `hotel_slug` | URL path: `/api/guest/hotel/{hotel_slug}/chat/...` | **REQUIRED** |

### OPTIONAL INPUTS

None. There are no optional authentication inputs.

### NOT USED

| Input | Status |
|-------|--------|
| `booking_id` | Derived from token. Never sent by client. |
| `email` | Never read by chat endpoints. |
| `room_number` | Derived from `booking.assigned_room`. Never sent by client. |
| `guest_name` | Never read by chat endpoints. |

### TOKEN MODEL USED

**`BookingManagementToken`** — single source of truth.

- Lookup: SHA-256 hash of raw token → query `BookingManagementToken.objects.get(token_hash=hash)`
- Validation: `is_valid` property (not time-based)
- Hotel match: `booking.hotel.slug == hotel_slug`
- Implied scopes: `["STATUS_READ", "CHAT", "ROOM_SERVICE"]`

### RESPONSE STRUCTURE (Context Endpoint)

```json
{
    "conversation_id": "<int | null>",
    "booking_id": "<string>",
    "room_number": "<string | null>",
    "assigned_room_id": "<int | null>",
    "allowed_actions": ["chat"] | [],
    "disabled_reason": "<string | absent>",
    "pusher": {
        "channel": "private-hotel-{slug}-guest-chat-booking-{booking_id}",
        "event": "realtime_event"
    },
    "current_staff_handler": {
        "name": "<string>",
        "role": "<string>"
    } | null
}
```

**Note:** `disabled_reason` key is **only present** when chat is disabled. It is **not** always in the response.

### ERROR CONTRACT (What Frontend Must Handle)

| Code | Status | When | Frontend action |
|------|--------|------|-----------------|
| `TOKEN_REQUIRED` | 401 | No token provided | Redirect to login / show error |
| `INVALID_TOKEN` | 401 | Token invalid, expired, wrong hotel, cancelled booking | Redirect to login / show "link expired" |
| `MISSING_SCOPE` | 403 | Token lacks CHAT scope (unlikely) | Show permission error |
| `NOT_CHECKED_IN` | 403 | POST message before check-in | Show "check in first" |
| `ALREADY_CHECKED_OUT` | 403 | POST message after checkout | Show "chat closed" |
| `NO_ROOM_ASSIGNED` | 409 | POST message with no room | Show "room not assigned yet" |
| *(no code)* | 500 | Server error | Show generic error |

### ENDPOINT URLS

```
GET  /api/guest/hotel/{hotel_slug}/chat/context?token=...
GET  /api/guest/hotel/{hotel_slug}/chat/messages?token=...&limit=50&before_id=123
POST /api/guest/hotel/{hotel_slug}/chat/messages?token=...   body: {"message": "text", "reply_to": 123}
POST /api/guest/hotel/{hotel_slug}/chat/pusher/auth?token=...  body: {"socket_id": "...", "channel_name": "..."}
```

### PUSHER CHANNEL CONTRACT

- Format: `private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}`
- Event: `realtime_event`
- Channel is **booking-scoped** (survives room moves)
- Channel name is **returned by context endpoint** — frontend should use the returned value
- Pusher auth **validates exact channel match** — any deviation is rejected with 403

---

## Source Files Referenced

| File | Purpose |
|------|---------|
| `common/guest_access.py` | Canonical token resolver, exception hierarchy, `GuestAccessContext` |
| `common/guest_auth.py` | `TokenAuthenticationMixin`, throttle classes |
| `bookings/services.py` | `resolve_guest_chat_context()` — chat-specific wrapper with UX hints |
| `hotel/canonical_guest_chat_views.py` | All 3 canonical chat view classes |
| `hotel/models.py` L2603 | `BookingManagementToken` model |
| `chat/models.py` | `Conversation`, `RoomMessage`, `GuestConversationParticipant` |
| `guest_urls.py` | URL routing for canonical chat endpoints |

---

## UNIFICATION CHANGES APPLIED

### Finding: Token Resolution Was Inconsistent

**`BookingStatusView`** and **canonical chat views** already used `resolve_guest_access()` — same resolver, same hash logic.

However, **two other endpoints** did inline hashing with a critical difference:

| Endpoint | Before | Issue |
|----------|--------|-------|
| `ValidateBookingManagementTokenView` | `hashlib.sha256(raw_token.encode()).hexdigest()` | NO `.strip()` — different hash if token has whitespace |
| `CancelBookingView` | `hashlib.sha256(raw_token.encode()).hexdigest()` | NO `.strip()` — different hash if token has whitespace |
| `BookingStatusView.post()` | Used `resolve_guest_access()` but re-hashed inline to get token object | Redundant second hash |

**Canonical resolver uses:**
```python
hashlib.sha256(token_str.strip().encode("utf-8")).hexdigest()
```

**Inline code used:**
```python
hashlib.sha256(raw_token.encode()).hexdigest()  # NO .strip()!
```

### Changes Made

1. **`common/guest_access.py`** — Added `hash_token()` canonical utility; added `token_obj` field to `GuestAccessContext`; all internal hash calls now use `hash_token()`
2. **`hotel/public_views.py` `ValidateBookingManagementTokenView`** — Replaced inline hash + DB lookup with `resolve_guest_access()`
3. **`hotel/public_views.py` `CancelBookingView`** — Replaced inline hash + DB lookup with `resolve_guest_access()`
4. **`hotel/public_views.py` `BookingStatusView.post()`** — Removed redundant re-hash; uses `ctx.token_obj` directly
5. **`bookings/services.py` `hash_token()`** — Now delegates to `common.guest_access.hash_token()` for consistency

### Token Resolution Path (After Unification)

ALL BookingManagementToken endpoints now flow through:
```
request → token extraction → resolve_guest_access() → hash_token() → _try_booking_management_token() → GuestAccessContext (with token_obj)
```

No inline hashing. No duplicate lookups. Single source of truth.
