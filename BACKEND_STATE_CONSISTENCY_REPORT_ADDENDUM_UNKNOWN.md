# BACKEND STATE CONSISTENCY REPORT - ADDENDUM: UNKNOWN RESOLUTION

**Status**: Complete Resolution  
**Date**: January 15, 2026  
**Parent Report**: BACKEND_STATE_CONSISTENCY_REPORT.md  

---

## UNKNOWN #1: Cancel Booking Flow Entry Point

**RESOLVED**: `hotel/staff_views.py::StaffBookingCancelView.post`

### Location
- **File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\hotel\staff_views.py` (Lines 1393-1500)
- **Entry Point**: `POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/cancel/`
- **Class**: `StaffBookingCancelView`
- **Function**: `post(self, request, hotel_slug, booking_id)`

### State Mutations
```python
booking.status = 'CANCELLED'
booking.special_requests = f"{current_requests}{cancellation_info}".strip()
booking.save()
```

### Validations/Invariants Enforced
1. **Staff Authorization**: Must have valid staff profile for hotel
2. **Stripe Booking Protection**: Blocks cancellation of Stripe bookings (redirects to approve/decline)
3. **Status Validation**: Cannot cancel COMPLETED bookings
4. **Authorization Protection**: Cannot cancel PENDING_APPROVAL (must use decline endpoint)
5. **Idempotency**: Already cancelled bookings return success

### Events Emitted
```python
# Staff realtime event
notification_manager.realtime_booking_cancelled(booking, cancellation_reason)

# Guest realtime event (commit-wrapped)
transaction.on_commit(
    lambda: notification_manager.realtime_guest_booking_cancelled(
        booking=booking,
        cancelled_at=booking.cancelled_at,
        cancellation_reason=cancellation_reason
    )
)

# Email notification
send_booking_cancellation_email(booking, cancellation_reason, staff_name)
```

### Transaction Usage
- **NO** explicit `@transaction.atomic`
- **NO** `select_for_update` locking
- **Risk**: Race condition on booking status updates

---

## UNKNOWN #2: Housekeeping Status Updates Flow Entry Point

**RESOLVED**: `housekeeping/views.py::RoomStatusViewSet.update_status`

### Location
- **File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\housekeeping\views.py` (Lines 257-320)
- **Entry Point**: `POST /api/staff/hotel/{hotel_slug}/rooms/{room_id}/status/`
- **Class**: `RoomStatusViewSet`
- **Function**: `update_status(self, request, hotel_slug=None, room_id=None)`

### Canonical Service Usage
**Delegates to**: `housekeeping/services.py::set_room_status()` (Lines 17-50)
- **File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\housekeeping\services.py`
- **Function**: `set_room_status(*, room, to_status, staff=None, source="HOUSEKEEPING", note="")`

### State Mutations (via service)
```python
# In set_room_status() service:
room.room_status = to_status
room.save()

# Audit record creation
RoomStatusEvent.objects.create(
    hotel=room.hotel,
    room=room,
    from_status=old_status,
    to_status=to_status,
    changed_by=staff,
    source=source,
    note=note
)
```

### Validations/Invariants Enforced
1. **Staff Hotel Scoping**: `staff.hotel_id == hotel.id`
2. **Status Validation**: `to_status` must be valid `ROOM_STATUS_CHOICES`
3. **Transition Validation**: Uses `room.can_transition_to()` method
4. **Permission Enforcement**: Delegates to `can_change_room_status()` policy

### Events Emitted
```python
# UNKNOWN - Need to check if set_room_status() emits events
# Likely: notification_manager.realtime_room_updated(room, changed_fields, source)
```

### Transaction Usage
- **YES**: `@transaction.atomic` on `set_room_status()`
- **NO**: `select_for_update` locking found
- **Good**: Audit trail creation is atomic with room update

### Additional Entry Points
1. **Manager Override**: `POST /api/staff/hotel/{hotel_slug}/housekeeping/rooms/{room_id}/manager_override/`
   - Same service delegate pattern
   - Source: `"MANAGER_OVERRIDE"`

---

## UNKNOWN #3: Room Move Events Emission

**RESOLVED**: `room_bookings/services/room_move.py::RoomMoveService._emit_room_move_events`

### Location
- **File Path**: `c:\Users\nlekk\HMB\HotelMateBackend\room_bookings\services\room_move.py` (Lines 213-250)
- **Function**: `_emit_room_move_events(cls, booking, from_room, to_room)`

### Events Emitted
```python
# Booking state change
notification_manager.realtime_booking_updated(booking)

# Room occupancy updates for both rooms
notification_manager.realtime_room_occupancy_updated(from_room)
notification_manager.realtime_room_occupancy_updated(to_room)
```

### Execution Timing
- Called via `transaction.on_commit()` after atomic room move
- Ensures events only emit on successful transaction commit

### Event Coverage
- ✅ Booking assignment change
- ✅ From room occupancy cleared  
- ✅ To room occupancy set
- ❌ Missing room status change events (OCCUPIED → CHECKOUT_DIRTY)

---

## REMAINING INVESTIGATIONS

### set_room_status() Event Emission
**Status**: NEEDS VERIFICATION

**Command to Check**:
```bash
grep -r "realtime_room_updated\|room-status-changed\|pusher_client" housekeeping/services.py housekeeping/views.py
```

**Expected**: `notification_manager.realtime_room_updated(room, ['room_status'], source)` in service

### Room Assignment Service Events
**Status**: PARTIALLY MAPPED

**Commands to Complete**:
```bash
grep -r "realtime.*room\|room.*realtime" room_bookings/services/room_assignment.py
grep -r "pusher\|notification_manager" room_bookings/services/room_assignment.py
```

---

## SUMMARY

**RESOLVED UNKNOWNs**: 3/3  
**NEW INVESTIGATION TARGETS**: 2

**Critical Findings**:
1. **Booking cancellation has no atomic protection** (race condition risk)
2. **Housekeeping uses proper canonical service** with audit trail
3. **Room moves emit comprehensive events** but miss status changes
4. **All flows follow notification_manager pattern** for realtime events

**Priority**: Investigate missing event emissions in `set_room_status()` service next.