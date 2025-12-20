# BACKEND CHECK-IN CHECKOUT SOURCE OF TRUTH

**Version**: 1.0  
**Date**: December 20, 2025  
**Status**: Planning Complete - Ready for Implementation ✅  
**Source**: CHECK_IN_OUT_CODE_FACTS.md analysis  

## Overview

This document defines the canonical implementation for staff-initiated guest check-in and checkout functionality in HotelMate. All implementation must follow these verified facts from the existing codebase and business rules defined herein.

---

## Verified Facts from Codebase

### Room Status Machine
**File**: `rooms/models.py`

**ROOM_STATUS_CHOICES**:
```
'AVAILABLE' → 'OCCUPIED' → 'CHECKOUT_DIRTY'
'READY_FOR_GUEST' → 'OCCUPIED' → 'CHECKOUT_DIRTY'
```

**Critical Transitions**:
- Check-in: `READY_FOR_GUEST` → `OCCUPIED` (valid)
- Check-out: `OCCUPIED` → `CHECKOUT_DIRTY` (valid)
- **Validation**: Must use `room.can_transition_to(new_status)` before any status change

### RoomBooking Model
**File**: `hotel/models.py`

**Eligibility Fields**:
- `status` must be `'CONFIRMED'`
- `paid_at` must not be null (payment completed)
- `assigned_room` must not be null (room pre-assigned)
- `checked_in_at` / `checked_out_at` for state tracking

**STATUS_CHOICES**: `PENDING_PAYMENT`, `PENDING_APPROVAL`, `CONFIRMED`, `DECLINED`, `CANCELLED`, `COMPLETED`, `NO_SHOW`

### BookingGuest → Guest Mapping
**BookingGuest Model**: `hotel/models.py`
- **Roles**: `PRIMARY`, `COMPANION`
- **Copy fields**: `first_name`, `last_name`, `email`, `phone_number`, `guest_data`

**Guest Model**: `guests/models.py`  
- **Key FKs**: `booking`, `booking_guest`, `room`, `hotel`
- **Idempotency**: `Guest.get_or_create(booking_guest=...)`
- **⚠️ CRITICAL BUG**: `Guest.delete()` automatically sets `room.is_occupied = False`

### Guest Portal Sessions
**Model**: `GuestChatSession` in `chat/models.py`
- **Fields**: `session_id`, `room`, `conversation`, `is_active`, `expires_at`
- **Revocation**: Set `is_active = False` for sessions where `room = checkout_room`

### Realtime Notifications
**File**: `notifications/notification_manager.py`
- **Method**: `realtime_room_updated(room, changed_fields=None, source="system")` ✅ EXISTS
- **Channel**: `{hotel_slug}.rooms`
- **Event**: `room_updated`
- **Requirement**: Must use `transaction.on_commit()` for consistency

### Staff URL Routing
**Main File**: `staff_urls.py`
- **Pattern**: `/api/staff/hotel/<str:hotel_slug>/...` (singular "hotel")
- **Target File**: `rooms/staff_urls.py` (room-centric operations)
- **Existing**: `BookingAssignmentView` in `room_bookings/staff_views.py` has partial check-in logic

---

## Canonical Endpoints

### Check-In Endpoint
```
POST /api/staff/hotel/<str:hotel_slug>/rooms/<str:room_number>/checkin/
```

### Check-Out Endpoint  
```
POST /api/staff/hotel/<str:hotel_slug>/rooms/<str:room_number>/checkout/
```

**Implementation Location**: Add to `rooms/staff_urls.py` and implement in `rooms/staff_views.py`  
**Rationale**: Check-in/out are room-centric operations (not booking-centric), matching turnover workflow and realtime room channels

---

## Business Rules

### Permission Rules
- **Staff Authentication**: Required (existing `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`)
- **Hotel Scoping**: Staff can only operate on rooms in their assigned hotel
- **Access Control**: Front desk and managers can perform check-in/out operations

### Deterministic Booking Selection Rules

#### Check-In Booking Selection
```python
eligible_booking = RoomBooking.objects.filter(
    hotel=room.hotel,
    assigned_room=room,
    status='CONFIRMED',
    paid_at__isnull=False,
    check_in__lte=today,  # Check-in date today or earlier
    check_out__gt=today,  # Check-out date after today
    checked_in_at__isnull=True,  # Not already checked in
).select_for_update().order_by("check_in", "created_at", "id").first()
```

#### Check-Out Booking Selection
```python
active_booking = RoomBooking.objects.filter(
    hotel=room.hotel,
    assigned_room=room,
    checked_in_at__isnull=False,  # Must be checked in
    checked_out_at__isnull=True,  # Not already checked out
).select_for_update().order_by("-checked_in_at", "-id").first()
```

### Eligibility Checks

#### Check-In Eligibility
1. Room status must be `READY_FOR_GUEST`
2. Room must allow transition to `OCCUPIED`
3. Booking must be `CONFIRMED` with `paid_at` not null
4. Booking check-in window: `check_in <= today < check_out` (allows late arrivals)
5. Booking must have `assigned_room = room`
6. Booking must not already be checked in (`checked_in_at` is null)

#### Check-Out Eligibility  
1. Room status must be `OCCUPIED`
2. Room must allow transition to `CHECKOUT_DIRTY`
3. Must have active booking (checked in but not checked out)
4. Booking must be in same hotel as room

### State Transition Enforcement
- **Room Status**: Use `housekeeping.services.set_room_status()` if available, otherwise set `room.room_status` directly after validating `room.can_transition_to(new_status)` and logging turnover notes
- **Validation**: Always call `room.can_transition_to(new_status)` first
- **Audit Trail**: `RoomStatusEvent` creation via canonical service (if using housekeeping service) or manual logging

### Idempotent Guest Creation
```python
# For each BookingGuest in the party
guest, created = Guest.objects.get_or_create(
    booking_guest=booking_guest,
    defaults={
        'booking': booking,
        'room': room,
        'hotel': room.hotel,
        'first_name': booking_guest.first_name,
        'last_name': booking_guest.last_name,
        'email': booking_guest.email,
        'phone_number': booking_guest.phone_number,
        'guest_data': booking_guest.guest_data,
    }
)
```

### Checkout Access Revocation
```python
# Deactivate all guest chat sessions for this room
GuestChatSession.objects.filter(
    room=room,
    is_active=True
).update(is_active=False)

# Guest records are preserved for audit/analytics
# Room occupancy controlled by Room.is_occupied only
```

### Transaction Safety
- **Atomicity**: All operations must be wrapped in `transaction.atomic()`
- **Locking**: Use `select_for_update()` on Room and RoomBooking
- **Realtime**: Use `transaction.on_commit()` for notifications

---

## Field-Level Writes

### Check-In Process Writes

#### Room Table
- `room_status`: `'READY_FOR_GUEST'` → `'OCCUPIED'`
- `is_occupied`: `False` → `True`

#### RoomBooking Table  
- `checked_in_at`: `null` → `timezone.now()`

#### Guest Table (for each party member)
- **Create new records** via `Guest.objects.get_or_create(booking_guest=...)`
- `booking`: Set to booking instance
- `booking_guest`: Set to BookingGuest instance (1:1 mapping)
- `room`: Set to room instance
- `hotel`: Set to room.hotel
- Copy fields: `first_name`, `last_name`, `email`, `phone_number`, `guest_data`

### Check-Out Process Writes

#### Room Table
- `room_status`: `'OCCUPIED'` → `'CHECKOUT_DIRTY'`  
- `is_occupied`: `True` → `False`

#### RoomBooking Table
- `checked_out_at`: `null` → `timezone.now()`
- `status`: `'CONFIRMED'` → `'COMPLETED'`

#### Guest Table
- **Keep Guest records** for audit/historical purposes (do NOT delete)
- **Access Revocation**: Guest portal access is revoked via session management, not Guest deletion
- **Occupancy Status**: Room occupancy controlled by Room.is_occupied and booking timestamps only

#### GuestChatSession Table
- `is_active`: `True` → `False` (for all sessions where room = checkout_room)

---

## API Contract

### Check-In Request
```http
POST /api/staff/hotel/hotel-killarney/rooms/101/checkin/
Content-Type: application/json
Authorization: Token <staff-token>

{}
```

### Check-In Response (Success)
```json
{
  "success": true,
  "message": "Check-in completed successfully",
  "data": {
    "booking": {
      "id": 123,
      "booking_id": "BK-2025-0001",
      "checked_in_at": "2025-12-20T15:30:00Z",
      "party_size": 2
    },
    "room": {
      "id": 456,
      "room_number": "101",
      "room_status": "OCCUPIED",
      "is_occupied": true
    },
    "guests": [
      {
        "id": 789,
        "first_name": "John",
        "last_name": "Smith", 
        "role": "PRIMARY"
      },
      {
        "id": 790,
        "first_name": "Jane",
        "last_name": "Smith",
        "role": "COMPANION"  
      }
    ]
  }
}
```

### Check-Out Request  
```http
POST /api/staff/hotel/hotel-killarney/rooms/101/checkout/
Content-Type: application/json
Authorization: Token <staff-token>

{}
```

### Check-Out Response (Success)
```json
{
  "success": true,
  "message": "Check-out completed successfully", 
  "data": {
    "booking": {
      "id": 123,
      "booking_id": "BK-2025-0001",
      "checked_out_at": "2025-12-20T11:00:00Z",
      "status": "COMPLETED"
    },
    "room": {
      "id": 456,
      "room_number": "101", 
      "room_status": "CHECKOUT_DIRTY",
      "is_occupied": false
    }
  }
}
```

### Error Responses

#### 400 Bad Request - No Eligible Booking
```json
{
  "success": false,
  "error": "NO_ELIGIBLE_BOOKING",
  "message": "No eligible booking found for check-in. Room must have a confirmed, paid booking for today.",
  "details": {
    "room_number": "101",
    "room_status": "READY_FOR_GUEST",
    "eligible_bookings_count": 0
  }
}
```

#### 400 Bad Request - Invalid Room Status
```json
{
  "success": false,
  "error": "INVALID_ROOM_STATUS", 
  "message": "Room status 'OCCUPIED' cannot transition to 'OCCUPIED'.",
  "details": {
    "room_number": "101",
    "current_status": "OCCUPIED",
    "attempted_status": "OCCUPIED"
  }
}
```

#### 400 Bad Request - Already Checked In
```json
{
  "success": false,
  "error": "ALREADY_CHECKED_IN",
  "message": "Booking BK-2025-0001 is already checked in.",
  "details": {
    "booking_id": "BK-2025-0001", 
    "checked_in_at": "2025-12-20T10:00:00Z"
  }
}
```

#### 403 Forbidden - Hotel Scope
```json
{
  "success": false,
  "error": "HOTEL_ACCESS_DENIED",
  "message": "Staff member does not have access to this hotel."
}
```

#### 404 Not Found - Room
```json
{
  "success": false,
  "error": "ROOM_NOT_FOUND", 
  "message": "Room '999' not found in hotel 'hotel-killarney'."
}
```

---

## Realtime Notifications

### Check-In Notification
```python
transaction.on_commit(
    lambda: NotificationManager().realtime_room_updated(
        room=room,
        changed_fields=['room_status', 'is_occupied'],  # Must include both fields
        source='check_in'
    )
)
```

### Check-Out Notification
```python
transaction.on_commit(
    lambda: NotificationManager().realtime_room_updated(
        room=room, 
        changed_fields=['room_status', 'is_occupied'],  # Must include both fields
        source='check_out'
    )
)
```

**Event Structure**:
- **Channel**: `hotel-killarney.rooms`
- **Event**: `room_updated`
- **Category**: `rooms`
- **Payload**: Full room snapshot with `changed_fields` array

---

## Risks & TODOs

### High Priority Risks

#### 1. Guest.delete() Bug Risk (RESOLVED)
- **Issue**: `Guest.delete()` automatically sets `room.is_occupied = False`
- **Resolution**: ✅ **Do NOT delete Guest records on checkout** - preserve for audit/analytics
- **Access Control**: Revoke guest portal access via session management only
- **Occupancy Control**: Room occupancy managed by Room.is_occupied and booking timestamps

#### 2. Missing Unique Constraint  
- **Issue**: No database constraint prevents multiple Guest records for same BookingGuest
- **Risk**: Race conditions could create duplicate guests
- **TODO**: Add `UniqueConstraint` on `Guest.booking_guest` field

#### 3. Concurrent Check-In Race Condition
- **Issue**: Multiple staff could attempt check-in simultaneously
- **Risk**: Double check-in or inconsistent state
- **Mitigation**: Use `select_for_update()` on Room and RoomBooking

### Medium Priority TODOs

#### 1. Booking Status Management
- **Current**: No "IN_HOUSE" status in RoomBooking.STATUS_CHOICES
- **IN_HOUSE Logic**: Booking is in-house when `checked_in_at != null && checked_out_at == null`
- **Impact**: Must rely on timestamp fields for in-house detection
- **Consideration**: Add IN_HOUSE status or document reliance on timestamps

#### 2. Session Management Enhancement  
- **Current**: Only GuestChatSession found
- **TODO**: Create broader `guests.services.revoke_guest_portal_sessions(guest)` service
- **Scope**: May need to handle multiple session types

#### 3. Legacy Endpoint Cleanup
- **Issue**: Existing `BookingAssignmentView` has partial check-in logic
- **TODO**: Remove or refactor to avoid confusion with new canonical endpoints
- **Files**: Review `room_bookings/staff_urls.py` and `public_urls.py` for legacy checkout URLs

---

## Test Plan

### Unit Tests Required

#### Model Tests
- [ ] Room status transition validation via `can_transition_to()`
- [ ] Guest creation idempotency via `booking_guest` FK
- [ ] BookingGuest → Guest field mapping accuracy
- [ ] Guest.delete() room occupancy side effect

#### Service Tests  
- [ ] Check-in business rule validation
- [ ] Check-out business rule validation
- [ ] Deterministic booking selection queries
- [ ] Session revocation completeness

#### API Integration Tests
- [ ] Check-in happy path with 2-guest party
- [ ] Check-out happy path with session cleanup  
- [ ] Error handling: no eligible booking
- [ ] Error handling: invalid room status
- [ ] Error handling: already checked in/out
- [ ] Hotel scoping enforcement
- [ ] Concurrent access handling

#### Realtime Tests
- [ ] Check-in triggers `room_updated` event
- [ ] Check-out triggers `room_updated` event  
- [ ] Event payload contains correct `changed_fields`
- [ ] Events sent after transaction commit only

### Performance Tests
- [ ] Concurrent check-in attempts (race condition testing)
- [ ] Large party check-in (10+ guests)
- [ ] High-frequency check-in/out operations

### Security Tests
- [ ] Cross-hotel access prevention
- [ ] Unauthenticated access rejection
- [ ] SQL injection prevention in room_number parameter

---

## Implementation Checklist

### Phase 1: Core Endpoints
- [ ] Create check-in view in `rooms/staff_views.py`
- [ ] Create check-out view in `rooms/staff_views.py`  
- [ ] Add URL patterns to `rooms/staff_urls.py`
- [ ] Implement business rule validation
- [ ] Add select_for_update locking

### Phase 2: Guest Management
- [ ] Implement idempotent guest creation
- [ ] Handle BookingGuest → Guest field mapping
- [ ] Create session revocation service
- [ ] Add error handling and validation

### Phase 3: Integration
- [ ] Integrate with `housekeeping.services.set_room_status()`
- [ ] Add realtime notifications via `NotificationManager`
- [ ] Implement comprehensive error responses
- [ ] Add transaction.atomic wrapping

### Phase 4: Testing & Cleanup
- [ ] Write comprehensive test suite
- [ ] Performance testing for concurrent access
- [ ] Remove/refactor legacy check-in logic
- [ ] Documentation and deployment notes

---

## Final Notes

This specification provides a complete, deterministic implementation plan based on verified codebase facts. All business rules, API contracts, and technical requirements are designed to integrate seamlessly with existing HotelMate architecture while maintaining data consistency and audit trails.

**Key Integration Points**:
- Leverages existing `housekeeping.services.set_room_status()` for canonical room updates
- Uses existing `NotificationManager.realtime_room_updated()` for real-time events  
- Follows established staff URL routing patterns in `staff_urls.py`
- Maintains compatibility with existing Room status machine and booking lifecycle

**Success Criteria**:
- Zero data inconsistencies between Room, RoomBooking, and Guest models
- Complete audit trail via RoomStatusEvent and booking timestamps
- Real-time UI updates via Pusher notifications
- Robust error handling with clear staff feedback
- Production-ready performance with concurrent access support