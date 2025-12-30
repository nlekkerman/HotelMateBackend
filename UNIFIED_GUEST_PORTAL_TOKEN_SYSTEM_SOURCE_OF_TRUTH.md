# Unified Guest Portal Token System - Source of Truth

## Implementation Overview
**Date Created**: December 30, 2025
**Status**: In Implementation  
**Scope**: Token-only guest portal authentication (NO PIN support, no backward compatibility)

## Core Principle
**One booking = One ACTIVE token**  
A booking may have multiple tokens historically, but at most one ACTIVE token at a time. When booking is CHECKED IN, the active token enables guest chat and room service orders. Room is always derived live from current occupancy - never stored on token.

**Token Lifecycle:**
- Multiple tokens can exist per booking (re-issue, resend, guest loses link)
- Only one can be status='ACTIVE' at any time
- Old tokens become status='REVOKED' when new one issued
- Room is always derived live from current occupancy

## Model Extensions

### GuestBookingToken Model (booking/models.py)
**Extend existing model with:**
```python
# New fields to add
status = models.CharField(
    max_length=10,
    choices=[
        ('ACTIVE', 'Active'),
        ('REVOKED', 'Revoked'),
    ],
    default='ACTIVE'
)
revoked_at = models.DateTimeField(null=True, blank=True)
revoked_reason = models.CharField(max_length=50, null=True, blank=True)
# last_used_at already exists
# expires_at already exists - expiry computed from expires_at <= now()
```

**Token Validity Rules:**
- Token must be status='ACTIVE' 
- Token must not be expired (expires_at > now) - computed, not stored
- Only one ACTIVE token per booking at any time
- Booking access levels:
  - **Context endpoint**: Valid tokens work pre-arrival (read-only)
  - **Action endpoints**: Booking must be in-house:
    - booking.checked_in_at != null
    - booking.checked_out_at == null  
    - booking.status != 'CANCELLED'

## Core Service Function

### resolve_in_house_context(token, hotel_slug)
**Location**: booking/services.py
**Purpose**: Single validation function for all guest portal endpoints

**Logic Flow:**
1. Validate token is ACTIVE, not expired (computed from expires_at)
2. Ensure token.booking.hotel.slug == hotel_slug
3. For action endpoints: Ensure booking is in-house (checked_in_at != null, checked_out_at == null, status != CANCELLED)
4. Derive current room deterministically:
   ```python
   occupancy = booking.assigned_room  # Use existing assigned_room field
   # OR if using RoomOccupancy model:
   # occupancy = RoomOccupancy.objects.select_related("room")
   #     .filter(booking=booking, status='OCCUPIED')
   #     .order_by("-updated_at").first()
   ```
5. Return (booking, room, occupancy) OR raise appropriate HTTP error

**Race Condition Protection:**
- Room move operations use select_for_update() on occupancy
- Guest endpoints use regular reads (atomic room derivation)

**Error Responses:**
- 403 NOT_IN_HOUSE: Token valid but booking not currently in-house (action endpoints only)
- 409 ROOM_NOT_ASSIGNED: Token/booking valid but no active room occupancy
- 404 NOT_FOUND: Token invalid, expired, or hotel_slug mismatch (prevents enumeration)
- 401 UNAUTHORIZED: Alternative to 404 for invalid tokens (implementation choice)

## API Endpoints

### 1. Guest Context Endpoint
**GET** `/api/public/hotel/{hotel_slug}/guest/context/?token=...`
- Validates token (works pre-arrival for confirmed bookings)
- Returns booking summary + current room + allowed_actions booleans
- No side effects, safe for frequent polling
- **Access**: Valid tokens work pre-arrival; actions gated by allowed_actions
- **In-house guests**: allowed_actions = true for chat/room_service
- **Pre-arrival guests**: allowed_actions = false (read-only access)

**Response Format:**
```json
{
  "booking": {
    "booking_id": "BK-2025-0001",
    "primary_guest_name": "John Doe",
    "check_in_date": "2025-01-01", 
    "check_out_date": "2025-01-03",
    "status": "CONFIRMED"
  },
  "current_room": {
    "room_number": "112",
    "room_type": "Deluxe King",
    "floor": 1
  },
  "allowed_actions": {
    "can_chat": true,
    "can_order_room_service": true,
    "can_cancel": false
  }
}
```

### 2. Guest Chat Messages  
**POST** `/api/public/hotel/{hotel_slug}/guest/chat/messages/?token=...`
- Calls resolve_in_house_context(token, hotel_slug)
- Creates message linked to hotel, booking, room (FK snapshot)
- Stores room_number in metadata for audit trail
- Never accepts room_id from client

**Request Body:**
```json
{
  "message": "Hello, I need extra towels",
  "message_type": "TEXT"
}
```

**Message Record:**
- hotel (FK)
- booking (FK) 
- room (FK snapshot - current room at time of message)
- metadata: {"room_number": "112", "token_id": token_id}
- message content

### 3. Room Service Orders
**POST** `/api/public/hotel/{hotel_slug}/guest/room-service/orders/?token=...`
- Calls resolve_in_house_context(token, hotel_slug) 
- Creates order linked to hotel, booking, room (FK snapshot)
- Stores room_number in metadata for audit trail
- Never accepts room_id from client

**Request Body:**
```json
{
  "items": [
    {"menu_item_id": 123, "quantity": 2, "notes": "No onions"}
  ],
  "delivery_notes": "Please knock softly"
}
```

**Order Record:**
- hotel (FK)
- booking (FK)
- room (FK snapshot - current room at time of order)
- source = "GUEST_PORTAL_TOKEN"
- metadata: {"room_number": "112", "token_id": token_id}
- order items + delivery info

## Token Lifecycle Management

### Auto-Revocation Triggers
**Checkout Process (booking/services.py checkout_service):**
```python
# On successful checkout
GuestBookingToken.objects.filter(
    booking=booking,
    status='ACTIVE'
).update(
    status='REVOKED',
    revoked_at=timezone.now(),
    revoked_reason='CHECKOUT_COMPLETED'
)
```

**Booking Cancellation (signals or service):**
```python
# On booking cancellation  
GuestBookingToken.objects.filter(
    booking=booking,
    status='ACTIVE' 
).update(
    status='REVOKED',
    revoked_at=timezone.now(),
    revoked_reason='BOOKING_CANCELLED'
)
```

### Room Move Behavior
**Room moves are transparent to tokens:**
- Token stays the same
- resolve_in_house_context() always returns current room via live RoomOccupancy lookup
- Previous chat/orders remain linked to old room (correct historical audit)
- New chat/orders automatically use new room

## Database Schema Requirements

### Required Models/Fields
- **GuestBookingToken**: Extended with status, revoked_at, revoked_reason
- **RoomOccupancy**: Must exist with booking FK, room FK, status field
- **Chat Messages**: hotel FK, booking FK, room FK, metadata JSONField
- **Room Service Orders**: hotel FK, booking FK, room FK, source field, metadata JSONField

### Database Constraints  
**Critical constraints:**
```sql
-- Only one ACTIVE token per booking
UNIQUE(booking_id) WHERE status = 'ACTIVE'

-- If using RoomOccupancy model: Only one active occupancy per booking
UNIQUE(booking_id) WHERE status = 'OCCUPIED'

-- Current implementation: Use existing assigned_room field on RoomBooking
-- No additional constraints needed
```

## Security & Safety Measures

### Rate Limiting
- Per-token: 120 requests/minute for context endpoint (UI polling + reconnects)
- Per-token: 10 requests/minute for POST endpoints (chat/orders)
- Per-IP: 200 requests/minute across all endpoints
- Consider: Cache context response 5-10 seconds for better UX

### Input Validation
- Never accept room_id/room_number from client requests
- Hotel slug must exactly match token.booking.hotel.slug
- All JSON input validated against strict schemas
- Token format validation (proper length, character set)

### Audit Trail
- All actions store token_id and room snapshot in metadata
- last_used_at updated on every successful token validation
- Comprehensive logging of token lifecycle events

## Test Coverage Requirements

### Token Lifecycle Tests
- [x] Token creation and generation
- [x] Token expiry validation (computed from expires_at)
- [x] Token revocation (manual and auto)
- [x] Status transitions (ACTIVE → REVOKED)
- [x] Multiple tokens per booking (only one ACTIVE)
- [x] New token revokes old ACTIVE tokens

### In-House Validation Tests  
- [x] Context endpoint accessible pre-arrival (allowed_actions=false)
- [x] Checked-in booking enables actions (allowed_actions=true)
- [x] Not checked-in booking returns 403 for action endpoints
- [x] Checked-out booking returns 403 for action endpoints
- [x] Cancelled booking returns 404 
- [x] No room assignment returns 409 for action endpoints

### Room Move Tests
- [x] Token works after room move (live derivation)
- [x] Historical messages/orders retain old room snapshot
- [x] New messages/orders use new room
- [x] Multiple room moves handled correctly

### Endpoint Integration Tests
- [x] Context endpoint returns correct booking/room data
- [x] Chat messages created with proper relationships
- [x] Room service orders created with proper relationships
- [x] Hotel slug validation enforced
- [x] Rate limiting enforced

### Auto-Revocation Tests
- [x] Checkout revokes all active tokens for booking
- [x] Cancellation revokes all active tokens for booking  
- [x] Revoked tokens return 401 INVALID_TOKEN
- [x] Multiple tokens per booking handled correctly

## File Structure

```
booking/
├── models.py              # GuestBookingToken extensions
├── services.py            # resolve_in_house_context()
├── tests/
│   └── test_guest_tokens.py   # Token lifecycle tests

guests/
├── views.py               # Guest context endpoint
├── urls.py                # Guest URL routing
├── tests/
│   └── test_guest_endpoints.py  # Endpoint integration tests

chat/
├── models.py              # Chat message model updates
├── views.py               # Token-based chat endpoint  
├── tests/
│   └── test_guest_chat.py     # Chat-specific tests

room_service/
├── models.py              # Room service order model updates
├── views.py               # Token-based order endpoint
├── tests/
│   └── test_guest_orders.py   # Order-specific tests
```

## Implementation Priority

1. **Phase 1: Core Infrastructure**
   - Extend GuestBookingToken model
   - Create resolve_in_house_context service
   - Add basic token lifecycle tests

2. **Phase 2: API Endpoints**
   - Guest context endpoint
   - Guest chat messages endpoint
   - Room service orders endpoint

3. **Phase 3: Auto-Revocation** 
   - Checkout token revocation
   - Cancellation token revocation
   - Signal handlers

4. **Phase 4: Testing & Polish**
   - Comprehensive test suite
   - Rate limiting implementation
   - Documentation updates

## Success Criteria

✅ **Token-Only Authentication**: No PIN support, clean token-based auth  
✅ **Booking-Scoped Access**: One token per booking, room derived live  
✅ **In-House Validation**: Only checked-in bookings can access services  
✅ **Room Move Transparency**: Token continues working after room changes  
✅ **Audit Trail**: All actions tracked with room snapshots  
✅ **Auto-Revocation**: Tokens revoked on checkout/cancellation  
✅ **Comprehensive Testing**: Edge cases and integration scenarios covered  

---

**Next Steps**: Begin implementation with GuestBookingToken model extensions and resolve_in_house_context service function.