# BACKEND STATE CONSISTENCY REPORT

**Status**: Factual Analysis  
**Date**: January 15, 2026  
**Scope**: Cross-domain state management analysis  

---

## A. Executive Summary

### What is Canonical Today
The HotelMate backend has **distributed state management** across six domains without a clear single source of truth. **Multiple overlapping boolean flags and enums** create potential for contradictions:

- **Booking lifecycle**: Managed via `RoomBooking.status` (8 states) + timestamps
- **Room occupancy**: Split between `Room.is_occupied` (boolean) + `Room.room_status` (7 states)  
- **Housekeeping/turnover**: Controlled by `Room.room_status` workflow states
- **Payment state**: Mix of `RoomBooking.status`, timestamps, and Stripe references
- **Guest party/precheckin**: Separate `BookingGuest` table + JSON payloads on booking
- **Realtime events**: Scattered Pusher triggers with no standardized schema

### Biggest Consistency Risks
1. **Boolean vs Status Conflicts**: `Room.is_occupied=False` while `RoomBooking.status=IN_HOUSE` 
2. **Payment State Drift**: `paid_at` set without `status=CONFIRMED` transition
3. **Occupancy Authority Ambiguity**: Room assignment can happen without room status validation
4. **Ghost Assignments**: Room assigned to multiple bookings via race conditions
5. **Housekeeping Bypass**: Rooms marked `OCCUPIED` while `room_status=CHECKOUT_DIRTY`

---

## B. Current Data Model Map

### 1. Booking Domain (`hotel/models.py`)

**Primary Model**: `RoomBooking` (Lines 588-950)
```python
# Status Authority (PRIMARY TRUTH)
status = CharField(choices=STATUS_CHOICES, default='PENDING_PAYMENT')
STATUS_CHOICES = [
    ('PENDING_PAYMENT', 'Pending Payment'),
    ('PENDING_APPROVAL', 'Pending Staff Approval'),  
    ('CONFIRMED', 'Confirmed'),
    ('DECLINED', 'Declined'),
    ('CANCELLED', 'Cancelled'),
    ('CANCELLED_DRAFT', 'Cancelled Draft'),
    ('COMPLETED', 'Completed'),
    ('NO_SHOW', 'No Show'),
]

# Derived Workflow States
checked_in_at = DateTimeField(null=True)      # DERIVED from check-in action
checked_out_at = DateTimeField(null=True)     # DERIVED from checkout action

# Assignment State (WORKFLOW FIELD)
assigned_room = ForeignKey(Room, null=True)
room_assigned_at = DateTimeField(null=True)
room_assigned_by = ForeignKey(Staff, null=True)
```

**Authority**: Booking lifecycle, payment completion, guest capacity
**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\hotel\models.py`

### 2. Room Domain (`rooms/models.py`)

**Primary Model**: `Room` (Lines 37-100)
```python
# Occupancy Authority (CONFLICTING WITH BOOKING)
is_occupied = BooleanField(default=False)     # BOOLEAN FLAG

# Turnover Workflow Authority (PRIMARY FOR HOUSEKEEPING)
room_status = CharField(choices=ROOM_STATUS_CHOICES, default='READY_FOR_GUEST')
ROOM_STATUS_CHOICES = [
    ('OCCUPIED', 'Occupied'),
    ('CHECKOUT_DIRTY', 'Checkout Dirty'),
    ('CLEANING_IN_PROGRESS', 'Cleaning in Progress'),
    ('CLEANED_UNINSPECTED', 'Cleaned Uninspected'), 
    ('MAINTENANCE_REQUIRED', 'Maintenance Required'),
    ('OUT_OF_ORDER', 'Out of Order'),
    ('READY_FOR_GUEST', 'Ready for Guest'),
]

# Hard Override Flags
is_active = BooleanField(default=True)        # MASTER SWITCH
is_out_of_order = BooleanField(default=False) # HARD OVERRIDE
maintenance_required = BooleanField(default=False)
```

**Authority**: Physical room state, housekeeping workflow, maintenance status
**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\rooms\models.py`

### 3. Housekeeping Domain (`housekeeping/models.py`)

**Audit Model**: `RoomStatusEvent` (Lines 6-60)
```python
# Immutable Audit Trail
from_status = CharField(max_length=20)
to_status = CharField(max_length=20) 
changed_by = ForeignKey(Staff, null=True)
source = CharField(choices=SOURCE_CHOICES, default='HOUSEKEEPING')
SOURCE_CHOICES = [
    ('HOUSEKEEPING', 'Housekeeping'),
    ('FRONT_DESK', 'Front Desk'),
    ('SYSTEM', 'System'),
    ('MANAGER_OVERRIDE', 'Manager Override'),
]
```

**Task Model**: `HousekeepingTask` (Lines 80-160)
```python
status = CharField(choices=STATUS_CHOICES, default='OPEN')
STATUS_CHOICES = [
    ('OPEN', 'Open'),
    ('IN_PROGRESS', 'In Progress'),
    ('DONE', 'Done'),
    ('CANCELLED', 'Cancelled'),
]
```

**Authority**: Room status transition audit trail, task management
**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\housekeeping\models.py`

### 4. Payment Domain (`hotel/models.py`, `hotel/payment_views.py`)

**Fields on RoomBooking**:
```python
# Payment State (MIXED AUTHORITY)
payment_reference = CharField(max_length=200)     # Stripe session/intent ID
payment_provider = CharField(max_length=50)       # "stripe"
paid_at = DateTimeField(null=True)                # PAYMENT COMPLETION TIMESTAMP
payment_authorized_at = DateTimeField(null=True)  # AUTHORIZATION TIMESTAMP  
payment_intent_id = CharField(max_length=200)     # Stripe PaymentIntent ID
```

**Webhook Idempotency Model**: `StripeWebhookEvent`
```python
event_id = CharField(max_length=200, unique=True)
event_type = CharField(max_length=50)
status = CharField(default='RECEIVED')  # RECEIVED, PROCESSED, FAILED
```

**Authority**: Payment processing, Stripe synchronization
**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\hotel\payment_views.py`

### 5. Guest Party/Precheckin Domain (`hotel/models.py`)

**Party Model**: `BookingGuest` (Lines 99-150)
```python
booking = ForeignKey(RoomBooking, related_name='party')
role = CharField(choices=[('PRIMARY', 'Primary'), ('COMPANION', 'Companion')])
first_name = CharField(max_length=100)
last_name = CharField(max_length=100)
is_staying = BooleanField(default=True)
precheckin_payload = JSONField(default=dict)  # Individual guest data
```

**Token Model**: `BookingPrecheckinToken` 
```python
booking = ForeignKey(RoomBooking, related_name='precheckin_tokens')
token_hash = CharField(max_length=64)  # SHA256 only
expires_at = DateTimeField()
used_at = DateTimeField(null=True)
config_snapshot_enabled = JSONField(default=dict)
config_snapshot_required = JSONField(default=dict)
```

**Booking-Level State**:
```python
# RoomBooking model
precheckin_payload = JSONField(default=dict)          # Booking-level data
precheckin_submitted_at = DateTimeField(null=True)    # Completion timestamp
```

**Authority**: Guest party composition, precheckin form completion
**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\hotel\models.py`

### 6. Realtime Events Domain (`notifications/notification_manager.py`)

**Event Structure** (Lines 66-150):
```python
def _create_normalized_event(category, event_type, payload, hotel, scope=None):
    return {
        "category": category,      # "rooms", "booking", "staff_chat"
        "type": event_type,        # "room_updated", "booking_checked_in"  
        "payload": payload,        # Domain-specific data
        "meta": {
            "event_id": str(uuid.uuid4()),
            "hotel_slug": hotel.slug,
            "ts": timezone.now().isoformat(),
            "scope": scope or {}
        }
    }
```

**Channel Patterns**:
- Hotel Staff: `{hotel_slug}.rooms`, `hotel-{hotel_slug}`
- Guest Booking: `private-guest-booking.{booking_id}`
- Staff Personal: `{hotel_slug}-staff-{staff_id}-notifications`

**Authority**: Cross-domain event broadcasting, UI state synchronization
**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\notifications\notification_manager.py`

---

## C. Transition Inventory (Current Flows)

### 1. Create Booking Flow
**Entry Point**: `hotel/public_views.py::CreateBookingView`
**Transaction Boundaries**: Single atomic transaction
**State Changes**:
- `RoomBooking.status = 'PENDING_PAYMENT'`
- `BookingGuest` PRIMARY record created
- `RoomBooking.payment_reference = null`

**Events Emitted**: None (missing realtime booking created event)
**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\hotel\public_views.py`

### 2. Submit Payment / Confirm Booking Flow
**Entry Point**: `hotel/payment_views.py::StripeWebhookView.process_checkout_completed`
**Transaction Boundaries**: Atomic with idempotency check
**State Changes**:
- `RoomBooking.payment_authorized_at = now()`
- `RoomBooking.status = 'PENDING_APPROVAL'` (NOT CONFIRMED!)
- `RoomBooking.payment_intent_id = stripe_id`
- `StripeWebhookEvent.status = 'PROCESSED'`

**Events Emitted**: 
- `notification_manager.realtime_booking_updated(booking)` (staff)
- `notification_manager.realtime_guest_booking_payment_required()` (guest)

**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\hotel\payment_views.py` (Lines 334-480)

### 3. Cancel Booking Flow
**Entry Point**: `hotel/staff_views.py::BookingDetailView.patch` (status update)
**Transaction Boundaries**: Single transaction
**State Changes**:
- `RoomBooking.status = 'CANCELLED'`
- `RoomBooking.assigned_room = null` (if assigned)

**Events Emitted**: `notification_manager.realtime_booking_updated(booking)`
**File Path**: **UNKNOWN** - need to locate cancellation endpoint

### 4. Check-in Flow
**Entry Point**: `hotel/staff_views.py::BookingCheckInView.post`
**Transaction Boundaries**: Atomic transaction with select_for_update
**State Changes**:
- `RoomBooking.checked_in_at = now()`
- `Room.is_occupied = True`
- `Room.room_status = 'OCCUPIED'`
- `Guest` records created via `Guest.get_or_create(booking_guest=...)`
- `GuestBookingToken` generated for chat access

**Events Emitted**: 
- `notification_manager.realtime_booking_checked_in(booking, room.room_number)`
- `notification_manager.realtime_room_occupancy_updated(room)`

**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\hotel\staff_views.py` (Lines 2547-2650)

### 5. Check-out Flow
**Entry Point**: `hotel/staff_views.py::BookingCheckOutView.post` OR `room_bookings/services/checkout.py`
**Transaction Boundaries**: Atomic with select_for_update locks
**State Changes**:
- `RoomBooking.checked_out_at = now()`
- `RoomBooking.status = 'COMPLETED'`
- `Room.is_occupied = False`
- `Room.room_status = 'CHECKOUT_DIRTY'`
- `Room.guest_fcm_token = null`
- `GuestChatSession.is_active = False`

**Events Emitted**:
- `notification_manager.realtime_booking_checked_out(booking, room_number)`
- `notification_manager.realtime_room_occupancy_updated(room)`
- `pusher_client.trigger(f'hotel-{hotel.slug}', 'room-status-changed')`

**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\room_bookings\services\checkout.py` (Lines 200-250)

### 6. Room Move / Reassignment Flow  
**Entry Point**: `room_bookings/services/room_move.py::RoomMoveService._execute_room_move`
**Transaction Boundaries**: Atomic room lock + booking update
**State Changes**:
- `RoomBooking.assigned_room = to_room`
- `RoomBooking.room_moved_at = now()`
- `RoomBooking.room_moved_by = staff`
- `from_room.is_occupied = False`
- `from_room.room_status = 'CHECKOUT_DIRTY'`
- `to_room.is_occupied = True`
- `to_room.room_status = 'OCCUPIED'`

**Events Emitted**: **UNKNOWN** - need to check if move emits events
**File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\room_bookings\services\room_move.py` (Lines 163-200)

### 7. Housekeeping Status Updates Flow
**Entry Point**: `housekeeping/views.py` OR room status API endpoints
**Transaction Boundaries**: Single transaction
**State Changes**:
- `Room.room_status = new_status`
- `RoomStatusEvent` audit record created
- Timestamps: `last_cleaned_at`, `last_inspected_at`

**Events Emitted**: 
- `notification_manager.realtime_room_updated(room, changed_fields, source)`

**File Path**: **UNKNOWN** - need to locate housekeeping status update endpoints

---

## D. Consistency Risks / Illegal Combinations

### 1. **Booking IN_HOUSE + Room READY_FOR_GUEST**
**Risk**: Booking shows as checked-in but room is available for assignment
**Code Path**: Check-in flow if room status validation is bypassed
```python
# hotel/staff_views.py::BookingCheckInView
# RISK: No validation that room.room_status == 'READY_FOR_GUEST'
booking.checked_in_at = now()  # Sets IN_HOUSE state
room.room_status = 'OCCUPIED'  # But what if room was CHECKOUT_DIRTY?
```
**Fix Location**: `c:\Users\nlekk\HMB\HotelMateBackend\hotel\staff_views.py` (Line ~2580)

### 2. **Room is_occupied=False while Booking IN_HOUSE**
**Risk**: Room appears available while guest is staying
**Code Path**: Room move service resets occupancy without updating booking
```python
# room_bookings/services/room_move.py::RoomMoveService
from_room.is_occupied = False  # Clears occupancy flag
# RISK: If booking update fails, booking still shows IN_HOUSE
```
**Fix Location**: `c:\Users\nlekk\HMB\HotelMateBackend\room_bookings\services\room_move.py` (Line ~180)

### 3. **Housekeeping READY while Room Occupied**
**Risk**: Room shows as ready for cleaning while guest is inside
**Code Path**: Manual room status override bypassing occupancy check
```python
# RISK: Direct room_status update without checking is_occupied
Room.objects.filter(id=room_id).update(room_status='READY_FOR_GUEST')
# Should validate: is_occupied=False AND no active booking
```
**Fix Location**: All room status update endpoints need occupancy validation

### 4. **Booking CANCELLED with Active Room Assignment**
**Risk**: Room remains blocked by cancelled booking
**Code Path**: Booking cancellation without room cleanup
```python
# RISK: Status update without assignment cleanup
booking.status = 'CANCELLED'
# MISSING: booking.assigned_room = None
```
**Fix Location**: Booking cancellation endpoints need assignment cleanup

### 5. **Multiple Active Stays in Same Room**
**Risk**: Race condition allows double-booking
**Code Path**: Room assignment service without proper locking
```python
# room_bookings/services/room_assignment.py
# RISK: Two concurrent assignments to same room
room = Room.objects.select_for_update().get(id=room_id)  # Good
booking1.assigned_room = room  # Thread 1
booking2.assigned_room = room  # Thread 2 - should fail but doesn't
```
**Fix Location**: `c:\Users\nlekk\HMB\HotelMateBackend\room_bookings\services\room_assignment.py` (Line ~162)

---

## E. Source of Truth Assessment

### Occupancy Axis
**Current Owner**: **SPLIT AUTHORITY** between Room and Booking
- `Room.is_occupied` = Physical occupancy flag
- `RoomBooking.checked_in_at != null AND checked_out_at == null` = Booking in-house status
- **Problem**: These can diverge, no clear authority

**Recommendation**: Booking should be source of truth, Room.is_occupied becomes derived

### Readiness Axis  
**Current Owner**: `Room.room_status` workflow
- Authority: Housekeeping domain
- States: CHECKOUT_DIRTY → CLEANING_IN_PROGRESS → CLEANED_UNINSPECTED → READY_FOR_GUEST
- **Status**: Well-defined, good authority

### Booking Lifecycle Axis
**Current Owner**: `RoomBooking.status` 
- Authority: Booking domain
- Clear progression: PENDING_PAYMENT → CONFIRMED → COMPLETED
- **Status**: Good primary authority, but payment state can drift

### Payment Status Axis
**Current Owner**: **MIXED AUTHORITY**
- `RoomBooking.status` for booking workflow
- `paid_at`/`payment_authorized_at` for payment completion
- Stripe webhook events for external sync
- **Problem**: Payment can be authorized without status transition

### Duplicated/Derived State Without Strict Recompute

1. **Room.is_occupied**: Should be derived from active booking count
2. **RoomBooking assignment fields**: Multiple audit timestamps without clear authority
3. **Guest records**: Duplicated from BookingGuest without strict 1:1 mapping
4. **Room availability**: Mixed boolean flags + status without clear derivation rules

---

## F. Recommendations (NOT Implementation)

### 1. Canonical Separation of Axes

**Occupancy Axis** (Source: Booking Domain)
```
AVAILABLE → ASSIGNED → IN_HOUSE → DEPARTED
- ASSIGNED: booking.assigned_room != null, checked_in_at == null  
- IN_HOUSE: checked_in_at != null, checked_out_at == null
- DEPARTED: checked_out_at != null
```

**Turnover Axis** (Source: Housekeeping Domain)  
```
CHECKOUT_DIRTY → CLEANING → CLEANED → INSPECTED → READY
- Independent of occupancy
- Blocks new assignments until READY
```

**Operational Constraints** (Source: Room Domain)
```
ACTIVE → INACTIVE, OUT_OF_ORDER → AVAILABLE
- Hard overrides that prevent booking
- Independent of occupancy and turnover
```

### 2. Fields to Become Derived vs Authoritative

**Make Derived**:
- `Room.is_occupied` ← COUNT(active_bookings) > 0
- Room availability ← `is_active AND NOT is_out_of_order AND room_status=READY`
- Booking in-house status ← `checked_in_at != null AND checked_out_at == null`

**Keep Authoritative**:
- `RoomBooking.status` (booking lifecycle)
- `Room.room_status` (turnover workflow) 
- `RoomBooking.assigned_room` (room assignment)
- Payment timestamps (payment completion)

### 3. Server-Side Invariants to Enforce

1. **Single Active Assignment**: `UNIQUE(assigned_room) WHERE checked_in_at IS NULL`
2. **Occupancy Consistency**: `Room.is_occupied = EXISTS(active_bookings)`
3. **Assignment Prerequisites**: `assigned_room.room_status = 'READY_FOR_GUEST'`
4. **Payment-Status Consistency**: `status='CONFIRMED' IMPLIES paid_at IS NOT NULL`
5. **Party Completion**: `room_assigned IMPLIES party_complete = True`

### 4. Reconciliation Job Plan

**Daily Consistency Check**:
```sql
-- Find occupancy inconsistencies
SELECT r.id, r.room_number, r.is_occupied, COUNT(b.id) as active_bookings
FROM rooms_room r
LEFT JOIN hotel_roombooking b ON r.id = b.assigned_room_id 
WHERE b.checked_in_at IS NOT NULL AND b.checked_out_at IS NULL
HAVING r.is_occupied != (COUNT(b.id) > 0);

-- Find assignment conflicts  
SELECT assigned_room_id, COUNT(*) 
FROM hotel_roombooking 
WHERE assigned_room_id IS NOT NULL AND checked_out_at IS NULL
GROUP BY assigned_room_id HAVING COUNT(*) > 1;

-- Find payment-status drift
SELECT booking_id, status, paid_at, payment_authorized_at
FROM hotel_roombooking 
WHERE (status='CONFIRMED' AND paid_at IS NULL) 
   OR (status='PENDING_PAYMENT' AND paid_at IS NOT NULL);
```

**Auto-Fix Actions**:
- Sync `Room.is_occupied` with active booking count
- Clear stale room assignments from completed bookings
- Set missing `paid_at` for CONFIRMED bookings with payment_authorized_at
- Emit corrective Pusher events for drift detection

---

## Summary

The current system has **working but fragmented state management** with multiple potential contradiction points. The biggest immediate risks are **occupancy authority splits** and **assignment race conditions**. A systematic approach to make room occupancy derived from bookings and strengthen transaction boundaries would eliminate most consistency risks.

**Priority Order**:
1. Fix occupancy authority (Booking → Room)
2. Strengthen room assignment atomicity  
3. Add payment-status invariant enforcement
4. Implement daily reconciliation monitoring
5. Standardize realtime event emission patterns