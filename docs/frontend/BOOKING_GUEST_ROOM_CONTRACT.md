# BOOKING GUEST ROOM CONTRACT

> **Phase 4 Integration Contract** — Staff Dashboard Booking Management  
> Generated: 2025-12-13  
> Backend: HotelMateBackend (Django)  
> Frontend Target: React Staff Dashboard

---

## 1. Glossary (Frontend-Friendly)

| Term | Definition |
|------|------------|
| **Room** | Physical hotel room with `room_number`, `is_occupied`, `is_active`, `is_out_of_order`. Linked to a `RoomType` for capacity. |
| **Guest** | In-house person currently staying at the hotel. Has `room` FK pointing to their assigned Room. The **only source of truth** for room assignment. |
| **RoomBooking** | A reservation record. Contains booking metadata, dates, booker info, primary staying guest info, and status. |
| **BookingGuest** | Party member on a RoomBooking. Represents someone who WILL stay (pre-arrival). Converted to `Guest` at check-in. |
| **Party** | The full set of BookingGuest records for a RoomBooking. Always has exactly 1 PRIMARY + 0..N COMPANIONs. |
| **PRIMARY** | The main staying guest for a booking (role on BookingGuest, guest_type on Guest). |
| **COMPANION** | Additional party member traveling with the PRIMARY guest. |
| **In-house guest** | A `Guest` record with `room != null` and valid check-in/check-out dates. Created from BookingGuest at check-in. |
| **Booker** | Person who made/paid for the booking. May NOT be staying (e.g., company booking, gift). Stored on RoomBooking `booker_*` fields. |
| **Check-in** | Staff action that: assigns a Room, creates Guest records from BookingGuest party, marks room occupied. |
| **Check-out** | Staff action that: detaches Guests from Room (sets `room=null`), marks room unoccupied, sets booking to COMPLETED. |
| **Assign-room** | Synonym for check-in in the current system. Single endpoint handles both concepts. |

---

## 2. Source-of-Truth Rules (Critical)

### 2.1 Guest.room is THE ONLY Source for Room Assignment

```
RULE: To know who is in a room, query Guest.room FK
```

- **DO** use `Guest.objects.filter(room=room)` to get occupants
- **DO** use `room.guests_in_room.all()` (reverse FK from Guest model)
- **DO NOT** infer room assignment from any other model
- **DO NOT** use or expect `Room.guests` M2M (it does not exist)

### 2.2 Models Frontend Must NOT Use for Room Assignment

| Model/Field | Why Not |
|-------------|---------|
| `RoomBooking.assigned_room` | Only indicates which room was assigned to booking, NOT who is currently in room |
| `BookingGuest` | Party members are pre-arrival. They become Guests at check-in |
| Any legacy `Room.guests` | Removed. Does not exist. |

### 2.3 Booker vs Primary Staying Guest

```python
# Booker (may NOT stay)
RoomBooking.booker_type     # 'SELF' | 'THIRD_PARTY' | 'COMPANY'
RoomBooking.booker_first_name
RoomBooking.booker_last_name
RoomBooking.booker_email
RoomBooking.booker_phone
RoomBooking.booker_company  # For COMPANY bookings

# Primary Staying Guest (ALWAYS stays)
RoomBooking.primary_first_name  # Required
RoomBooking.primary_last_name   # Required
RoomBooking.primary_email
RoomBooking.primary_phone
```

- When `booker_type == 'SELF'`: booker IS the primary guest (booker_* fields may be empty)
- When `booker_type == 'THIRD_PARTY'`: booker made booking for someone else (gift, travel agent)
- When `booker_type == 'COMPANY'`: corporate booking, `booker_company` should be set

### 2.4 Party vs In-House Guests

| Concept | Model | When Created | Room Assigned |
|---------|-------|--------------|---------------|
| Party | `BookingGuest` | At booking time or before check-in | No |
| In-house | `Guest` | At check-in | Yes (`Guest.room`) |

**Relationship:**
- `BookingGuest` → becomes → `Guest` during check-in
- `Guest.booking_guest` FK links back to original party member (idempotency key)

### 2.5 What Gets Created/Updated on Check-in

1. `RoomBooking.assigned_room` ← set to selected Room
2. `RoomBooking.checked_in_at` ← timestamp
3. `Room.is_occupied` ← `true`
4. For EACH `BookingGuest` in party:
   - Create `Guest` record with:
     - `room` = assigned room
     - `booking` = the RoomBooking
     - `booking_guest` = the source BookingGuest (idempotency)
     - `guest_type` = BookingGuest.role ('PRIMARY' or 'COMPANION')
     - `check_in_date`, `check_out_date` from booking
   - PRIMARY Guest: `primary_guest = null`
   - COMPANION Guests: `primary_guest = <the PRIMARY Guest>`

### 2.6 What Gets Updated on Check-out

1. All `Guest` records linked to booking: `room` ← `null`
2. `Room.is_occupied` ← `false`
3. `RoomBooking.checked_out_at` ← timestamp
4. `RoomBooking.status` ← `'COMPLETED'`

**Note:** Guest records are NOT deleted on checkout. They remain for history with `room=null`.

---

## 3. Staff API Surface (Integration List)

### 3.1 Booking List

| Property | Value |
|----------|-------|
| **Method** | `GET` |
| **Path** | `/api/staff/hotel/{hotel_slug}/bookings/` |
| **Query Params** | `status`, `start_date`, `end_date` (all optional) |
| **Success** | `200 OK` |
| **Response** | Array of `StaffRoomBookingListSerializer` objects |

### 3.2 Booking Detail

| Property | Value |
|----------|-------|
| **Method** | `GET` |
| **Path** | `/api/staff/hotel/{hotel_slug}/bookings/{booking_id}/` |
| **Success** | `200 OK` |
| **Error** | `404 Not Found` if booking doesn't exist |
| **Response** | `StaffRoomBookingDetailSerializer` object |

### 3.3 Party List

| Property | Value |
|----------|-------|
| **Method** | `GET` |
| **Path** | `/api/hotel/staff/{hotel_slug}/bookings/{booking_id}/party/` |
| **Success** | `200 OK` |
| **Response** | `BookingPartyGroupedSerializer` object |

### 3.4 Party Update (Companions)

| Property | Value |
|----------|-------|
| **Method** | `PUT` |
| **Path** | `/api/hotel/staff/{hotel_slug}/bookings/{booking_id}/party/companions/` |
| **Body** | `{ "companions": [{ "id?": number, "first_name": string, "last_name": string, "email?": string, "phone?": string }] }` |
| **Success** | `200 OK` with updated party |
| **Error 400** | If booking already checked in |
| **Error 400** | If companion missing first_name or last_name |
| **Error 404** | If companion id not found |

### 3.5 Check-in (Assign Room)

| Property | Value |
|----------|-------|
| **Method** | `POST` |
| **Path** | `/api/hotel/staff/{hotel_slug}/bookings/{booking_id}/assign-room/` |
| **Body** | `{ "room_number": number }` |
| **Success** | `200 OK` with message + full booking detail |
| **Error 400** | `{ "error": "Booking must be CONFIRMED..." }` - wrong status |
| **Error 400** | `{ "error": "capacity_exceeded", "message": "...", "party_total_count": N, "max_occupancy": M }` |
| **Error 400** | Room not active, out of order, or already occupied |
| **Error 404** | Room or booking not found |

### 3.6 Check-out

| Property | Value |
|----------|-------|
| **Method** | `POST` |
| **Path** | `/api/hotel/staff/{hotel_slug}/bookings/{booking_id}/checkout/` |
| **Body** | `{}` (empty) |
| **Success** | `200 OK` with message + `guests_detached` count + full booking detail |
| **Error 400** | If booking has no assigned room |

### 3.7 Rooms List

| Property | Value |
|----------|-------|
| **Method** | `GET` |
| **Path** | `/api/staff/hotel/{hotel_slug}/rooms/` |
| **Success** | `200 OK` |
| **Response** | Paginated list of rooms with occupancy state |

### 3.8 Error Response Shape (Validation)

All validation errors follow this pattern:

```json
{
  "error": "short_error_code_or_message",
  "message": "Human readable explanation (optional)",
  "field_name": "value that caused error (optional)"
}
```

For capacity errors specifically:

```json
{
  "error": "capacity_exceeded",
  "message": "Party size (4) exceeds room capacity (2)",
  "party_total_count": 4,
  "max_occupancy": 2
}
```

---

## 4. Serializer Contracts (Exact Field Map)

### 4.1 StaffRoomBookingListSerializer

Minimal data for list views. **Real Django serializer output:**

```json
{
  "booking_id": "BK-2025-0005",
  "confirmation_number": "HOT-2025-0005",
  "status": "PENDING_PAYMENT",
  "check_in": "2025-12-01",
  "check_out": "2025-12-07",
  "nights": 6,
  "assigned_room_number": null,
  "booker_type": "SELF",
  "booker_summary": "Self",
  "primary_guest_name": "Nikola Simic",
  "party_total_count": 1,
  "created_at": "2025-12-01T11:29:35.934635Z",
  "updated_at": "2025-12-13T13:26:16.793982Z"
}
```

**Field Types:**
- `booking_id`, `confirmation_number`, `status`, `booker_type`, `booker_summary`, `primary_guest_name`: string
- `check_in`, `check_out`: ISO date string
- `nights`, `party_total_count`: number
- `assigned_room_number`: number | null
- `created_at`, `updated_at`: ISO datetime string

### 4.2 StaffRoomBookingDetailSerializer

Full data for detail views. All fields are **read-only**. **Real Django serializer output:**

```json
{
  "booking_id": "BK-2025-0005",
  "confirmation_number": "HOT-2025-0005",
  "status": "PENDING_PAYMENT",
  "check_in": "2025-12-01",
  "check_out": "2025-12-07",
  "nights": 6,
  "adults": 2,
  "children": 0,
  "total_amount": "850.20",
  "currency": "EUR",
  "special_requests": "",
  "promo_code": "",
  "payment_reference": "",
  "payment_provider": "",
  "paid_at": null,
  "checked_in_at": null,
  "checked_out_at": null,
  "created_at": "2025-12-01T11:29:35.934635Z",
  "updated_at": "2025-12-13T13:26:16.793982Z",
  "internal_notes": "",
  "booker": {
    "type": "SELF",
    "first_name": "",
    "last_name": "",
    "company": "",
    "email": "",
    "phone": ""
  },
  "primary_guest": {
    "first_name": "Nikola",
    "last_name": "Simic",
    "email": "nlekkerman@gmail.com",
    "phone": "0830945102"
  },
  "party": {
    "primary": {
      "id": 1,
      "role": "PRIMARY",
      "first_name": "Nikola",
      "last_name": "Simic",
      "full_name": "Nikola Simic",
      "email": "nlekkerman@gmail.com",
      "phone": "0830945102",
      "is_staying": true,
      "created_at": "2025-12-13T13:58:39.259842Z"
    },
    "companions": [],
    "total_count": 1
  },
  "in_house": {
    "primary": null,
    "companions": [],
    "walkins": [],
    "total_count": 0
  },
  "room": null,
  "flags": {
    "is_checked_in": false,
    "can_check_in": false,
    "can_check_out": false,
    "can_edit_party": true
  }
}
```
```

### 4.3 Field Structure Notes

The detail serializer includes nested objects as shown in the real output above:

**party object structure** (from BookingPartyGroupedSerializer):
- `primary`: Single PRIMARY party member object or null
- `companions`: Array of COMPANION party member objects  
- `total_count`: Total number of party members

**in_house object structure** (from InHouseGuestsGroupedSerializer):
- `primary`: Primary in-house guest object or null (only after check-in)
- `companions`: Array of companion in-house guests
- `walkins`: Array of walk-in guests (manual additions by staff)
- `total_count`: Total in-house guests

**room object structure** (from RoomSummary):
- Only populated after room assignment
- Contains: `room_number`, `is_occupied`, `is_active`, `is_out_of_order`, `room_type_id`, `room_type_name`

**flags object structure** (computed booleans):
- `is_checked_in`: Has assigned room + checked_in_at timestamp, no checked_out_at
- `can_check_in`: Status is CONFIRMED, not checked in, not checked out
- `can_check_out`: Is checked in, not checked out  
- `can_edit_party`: Status not CANCELLED/COMPLETED, not checked out

---

## 5. Lifecycle State Machine (Frontend Must Follow)

### 5.1 Booking States

```
┌─────────────────────────────────────────────────────────────────┐
│                         BOOKING LIFECYCLE                        │
└─────────────────────────────────────────────────────────────────┘

  PENDING_PAYMENT ─────► CONFIRMED ─────► COMPLETED
        │                    │                ▲
        │                    │                │
        ▼                    ▼                │
    CANCELLED           (check-in)            │
                             │                │
                             ▼                │
                        CHECKED_IN ──────────►┘
                        (implicit)        (check-out)
```

### 5.2 State Definitions

| State | assigned_room | checked_in_at | checked_out_at | flags |
|-------|---------------|---------------|----------------|-------|
| PENDING_PAYMENT | null | null | null | can_check_in: false |
| CONFIRMED (pre-arrival) | null | null | null | can_check_in: true, can_edit_party: true |
| Checked-in | Room | timestamp | null | is_checked_in: true, can_check_out: true, can_edit_party: false |
| COMPLETED | Room | timestamp | timestamp | is_checked_in: false |
| CANCELLED | null | null | null | all false |

### 5.3 State Transitions

| Transition | Endpoint | Status Change | Field Changes |
|------------|----------|---------------|---------------|
| Confirm booking | `/confirm/` | PENDING_PAYMENT → CONFIRMED | status |
| Check-in | `/assign-room/` | (no status change) | assigned_room, checked_in_at, creates Guests |
| Check-out | `/checkout/` | → COMPLETED | status, checked_out_at, Guest.room=null |
| Cancel | `/cancel/` | → CANCELLED | status, cancellation fields |

### 5.4 UI Must Disable/Enable Based on flags

```javascript
// Button states derived from flags
const canShowCheckInButton = flags.can_check_in;
const canShowCheckOutButton = flags.can_check_out;
const canShowEditPartyButton = flags.can_edit_party;
const showGuestListNotParty = flags.is_checked_in;
```

---

## 6. Capacity + Validation Rules (Frontend Constraints)

### 6.1 When Capacity Is Validated

Capacity validation occurs at **check-in time** (assign-room endpoint).

```python
# Backend validation logic
if room.room_type and room.room_type.max_occupancy:
    party_total_count = booking.party.count()
    if party_total_count > room.room_type.max_occupancy:
        # Returns 400 with capacity_exceeded error
```

### 6.2 Capacity Error Response

```json
{
  "error": "capacity_exceeded",
  "message": "Party size (4) exceeds room capacity (2)",
  "party_total_count": 4,
  "max_occupancy": 2
}
```

### 6.3 What Frontend Must Prevent

| Rule | Frontend Action |
|------|-----------------|
| **Multiple PRIMARY** | Never allow creating second PRIMARY in party UI |
| **Party > room capacity** | Show warning before check-in if party_total_count > selected room's max_occupancy |
| **Empty party** | At least PRIMARY must exist before check-in |
| **Invalid companion data** | Validate first_name + last_name required |

### 6.4 Backend Auto-Heal Behavior

The `booking_integrity` service runs guardrails that may auto-fix:

| Issue | Auto-Heal Action | Realtime Event |
|-------|------------------|----------------|
| Missing PRIMARY BookingGuest | Creates from booking.primary_* fields | `booking_party_healed` |
| Multiple PRIMARY BookingGuest | Keeps most recent, demotes others to COMPANION | `booking_party_healed` |
| PRIMARY name mismatch | Updates to match booking.primary_* | `booking_party_healed` |
| Missing in-house Guest | Creates from BookingGuest | `booking_guests_healed` |
| Wrong room/hotel on Guest | Corrects to match booking | `booking_guests_healed` |
| is_occupied flag wrong | Corrects based on Guest.room presence | `room_occupancy_updated` |

**Frontend reaction to auto-heal:** 
- Listen for `*_healed` events on booking channel
- Re-render affected components from event payload
- Do NOT trigger full refetch loop

---

## 7. Realtime Contract (Frontend Subscription + Mapping)

### 7.1 Channels

| Channel Pattern | Purpose |
|-----------------|---------|
| `{hotel_slug}.booking` | All booking-related events |
| `{hotel_slug}.rooms` | Room occupancy changes |

**Example:** For hotel with slug `killarney-park`:
- `killarney-park.booking`
- `killarney-park.rooms`

### 7.2 Normalized Event Envelope

ALL events use this structure:

```javascript
// RealtimeEvent object structure
{
  category: 'booking', // or 'guest_management', 'attendance', 'staff_chat', 'guest_chat', 'room_service'
  type: 'string',      // Event type constant
  payload: {},         // Domain-specific data
  meta: {
    hotel_slug: 'string',
    event_id: 'string',    // UUID for deduplication
    ts: 'string',          // ISO timestamp
    scope: {}              // Targeting info
  }
}
```

### 7.3 Booking Channel Events

**Verified event types from NotificationManager:**

| Event Type | Channel | When Emitted | Minimal Payload Fields |
|------------|---------|--------------|------------------------|
| `booking_created` | `{slug}.booking` | New booking created | booking_id, confirmation_number, primary_guest_name, check_in, check_out, status |
| `booking_updated` | `{slug}.booking` | Booking details changed | booking_id, confirmation_number, status, assigned_room_number, updated_at |
| `booking_party_updated` | `{slug}.booking` | Party members added/removed/changed | booking_id, primary, companions, total_count |
| `booking_checked_in` | `{slug}.booking` | Check-in completed | Full StaffRoomBookingDetailSerializer output + checked_in_at |
| `booking_checked_out` | `{slug}.booking` | Check-out completed | Full StaffRoomBookingDetailSerializer output + checked_out_at |
| `booking_cancelled` | `{slug}.booking` | Booking cancelled | booking_id, cancellation_reason, cancelled_at |
| `booking_party_healed` | `{slug}.booking` | Auto-heal fixed party | booking_id, primary, companions, total_count |
| `booking_guests_healed` | `{slug}.booking` | Auto-heal fixed in-house guests | booking_id, in_house object |
| `booking_integrity_healed` | `{slug}.booking` | Batch integrity run | bookings_processed, changes summary |

### 7.4 Rooms Channel Events

**Verified event types from NotificationManager:**

| Event Type | Channel | When Emitted | Minimal Payload Fields |
|------------|---------|--------------|------------------------|
| `room_occupancy_updated` | `{slug}.rooms` | Room occupancy changed | room_number, is_occupied, current_occupancy, guests_in_room[], current_booking |

### 7.5 Event Payload Examples

**booking_party_updated:**
```json
{
  "category": "booking",
  "type": "booking_party_updated",
  "payload": {
    "booking_id": "BK-2025-0001",
    "confirmation_number": "KIL-2025-0001",
    "status": "CONFIRMED",
    "assigned_room_number": null,
    "primary": {
      "id": 1,
      "role": "PRIMARY",
      "first_name": "Jane",
      "last_name": "Doe",
      "full_name": "Jane Doe",
      "email": "jane@example.com",
      "phone": "",
      "is_staying": true,
      "created_at": "2025-01-01T10:00:00Z"
    },
    "companions": [
      { "id": 2, "role": "COMPANION", "first_name": "Kid", "last_name": "Doe", ... }
    ],
    "total_count": 2,
    "updated_at": "2025-01-05T14:30:00Z"
  },
  "meta": {
    "hotel_slug": "killarney-park",
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "ts": "2025-01-05T14:30:00.123456Z",
    "scope": { "booking_id": "BK-2025-0001" }
  }
}
```

**room_occupancy_updated:**
```json
{
  "category": "guest_management",
  "type": "room_occupancy_updated",
  "payload": {
    "room_number": 203,
    "is_occupied": true,
    "room_type": "Deluxe Suite",
    "max_occupancy": 4,
    "current_occupancy": 2,
    "guests_in_room": [
      { "id": 1, "first_name": "Jane", "last_name": "Doe", "guest_type": "PRIMARY", "id_pin": "ab12" },
      { "id": 2, "first_name": "Kid", "last_name": "Doe", "guest_type": "COMPANION", "id_pin": "cd34" }
    ],
    "current_booking": { /* StaffRoomBookingDetailSerializer output */ }
  },
  "meta": {
    "hotel_slug": "killarney-park",
    "event_id": "660e8400-e29b-41d4-a716-446655440001",
    "ts": "2025-01-05T14:31:00.123456Z",
    "scope": { "room_number": 203 }
  }
}
```

### 7.6 Deduplication Rule

Use `meta.event_id` (UUID) to deduplicate:

```javascript
const processedEventIds = new Set();

function handleEvent(event) {
  if (processedEventIds.has(event.meta.event_id)) {
    return; // Already processed
  }
  processedEventIds.add(event.meta.event_id);
  // Process event...
}
```

### 7.7 Ordering/Version Guidance

- Events include `meta.ts` (ISO timestamp) for ordering
- For same-entity events, prefer latest `ts`
- No explicit version field; rely on `ts` for conflict resolution
- If unsure, refetch entity detail after receiving event

---

## 8. "Frontend Do / Don't" Checklist

### ✅ DO

| Rule | Rationale |
|------|-----------|
| Use booking detail serializer as source of truth after mutations | Endpoint returns complete, consistent state |
| Update store from realtime events without refetch loops | Events contain full payload; avoid unnecessary API calls |
| Treat backend response as authoritative | Backend enforces all validation; trust the response |
| Use `Guest.room` grouping from `in_house` object | Only source of truth for room occupancy |
| Check `flags` object before showing action buttons | Prevents invalid state transitions |
| Use `meta.event_id` for event deduplication | Prevents duplicate processing |
| Display `party` for pre-check-in, `in_house` for post-check-in | Different data models for different states |
| Validate companion data client-side before PUT | Better UX; backend validates anyway |
| Show capacity warning before attempting check-in | Prevent predictable 400 errors |

### ❌ DON'T

| Anti-Pattern | Why It's Wrong |
|--------------|----------------|
| Infer room assignment from `RoomBooking.assigned_room` alone | That's booking metadata, not current room state |
| Keep legacy `Room.guests` logic | Field doesn't exist; will cause errors |
| Refetch on every realtime event | Wastes bandwidth; events have full payload |
| Invent missing fields | If serializer doesn't return it, it doesn't exist |
| Allow multiple PRIMARY in party UI | Backend enforces unique constraint |
| Edit party after check-in | Use guest management endpoints instead |
| Store booker info as guest info | Booker may not be staying |
| Assume all BookingGuests become Guests | Only happens at check-in |
| Ignore `flags` object | Contains pre-computed state logic |
| Create custom room assignment logic | Backend handles all assignment; just call endpoint |

---

## 9. Open Questions / Requires Confirmation

| Item | Question | Impact |
|------|----------|--------|

| **Rooms List for Selection** | What endpoint should frontend use to get available rooms for check-in selection? | Check-in flow UI |
| **Room Availability Filter** | Should room list endpoint support filtering by `is_occupied=false`? | Room selection UX |
| **NO_SHOW Status** | Is there a staff action to mark booking as NO_SHOW? What endpoint? | State machine completeness |
| **Batch Party Update** | Can companions be updated after check-in via any endpoint? | Edge case handling |
| **Guest PIN Assignment** | When is `Guest.id_pin` generated? Automatically at check-in? | Display logic |
| **Pagination** | What pagination format is used for booking list? PageNumber? Cursor? | List implementation |

---

## Appendix A: Quick Reference Card

### Endpoint Cheat Sheet

**Factual Django URLs from staff_urls.py and hotel/urls.py:**

```
# Bookings (from staff_urls.py)
GET  /api/staff/hotel/{slug}/bookings/                          → List
GET  /api/staff/hotel/{slug}/bookings/{id}/                     → Detail
POST /api/staff/hotel/{slug}/bookings/{id}/confirm/             → Confirm

# Party (from hotel/urls.py)
GET  /api/hotel/staff/{slug}/bookings/{id}/party/               → Get party
PUT  /api/hotel/staff/{slug}/bookings/{id}/party/companions/    → Update companions

# Check-in/out (from hotel/urls.py)
POST /api/hotel/staff/{slug}/bookings/{id}/assign-room/         → Check-in
POST /api/hotel/staff/{slug}/bookings/{id}/checkout/            → Check-out

# Rooms (from staff_hotel_router)
GET  /api/staff/hotel/{slug}/rooms/                             → List rooms
```

### Pusher Channel Pattern

```javascript
const bookingChannel = `${hotelSlug}.booking`;
const roomsChannel = `${hotelSlug}.rooms`;
```

### Status Values

```javascript
// BookingStatus possible values:
// 'PENDING_PAYMENT', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW'

// BookerType possible values:
// 'SELF', 'THIRD_PARTY', 'COMPANY'

// BookingGuestRole possible values:
// 'PRIMARY', 'COMPANION'

// GuestType possible values:
// 'PRIMARY', 'COMPANION', 'WALKIN'
```

---

*End of Contract Document*
