# Room Assignment and Reassignment Process Analysis

## Overview
This document analyzes how room assignment and reassignment works before and after checkout in the HotelMate system, including the different endpoints, services, and workflows involved.

## Current System Architecture

### 1. Room Assignment Services

#### Core Service: `RoomAssignmentService`
**Location**: `room_bookings/services/room_assignment.py`

The system uses a centralized `RoomAssignmentService` for atomic room assignments:

```python
@classmethod
@transaction.atomic
def assign_room_atomic(cls, booking_id, room_id, staff_user, notes=None):
    # Lock booking and room for update to prevent concurrent modifications
    booking = RoomBooking.objects.select_for_update().get(booking_id=booking_id)
    room = Room.objects.select_for_update().get(id=room_id)
    
    # Handle reassignment (allowed only before check-in)
    if booking.assigned_room_id and booking.assigned_room_id != room_id:
        if booking.checked_in_at and not booking.checked_out_at:
            raise RoomAssignmentError('Cannot reassign room for in-house guest')
        
        # Log reassignment audit
        booking.room_reassigned_at = timezone.now()
        booking.room_reassigned_by = staff_user
        booking.assignment_version += 1
    
    # Perform assignment
    booking.assigned_room = room
    booking.room_assigned_at = timezone.now()
    booking.room_assigned_by = staff_user
    booking.save()
```

### 2. Staff API Endpoints

#### A. Legacy Assignment Endpoint
**URL**: `POST /api/staff/hotels/{slug}/bookings/{booking_id}/assign-room/`  
**View**: `BookingAssignmentView.assign_room()`  
**Features**:
- Combines room assignment + check-in process
- Creates Guest objects immediately
- Triggers realtime notifications
- Updates room occupancy status

#### B. Safe Assignment Endpoint  
**URL**: `POST /api/staff/hotels/{slug}/bookings/{booking_id}/safe-assign-room/`  
**View**: `SafeAssignRoomView`  
**Features**:
- ONLY assigns room (no check-in side effects)
- No Guest creation
- No realtime events 
- Uses `RoomAssignmentService.assign_room_atomic()`

#### C. Unassign Room Endpoint
**URL**: `POST /api/staff/hotels/{slug}/bookings/{booking_id}/unassign-room/`  
**View**: `UnassignRoomView`  
**Features**:
- Removes room assignment before check-in
- Prevents unassignment after guest is in-house

## Room Reassignment Rules

### Before Check-In (Allowed)
```python
# Booking states where reassignment is allowed:
if not (booking.checked_in_at and not booking.checked_out_at):
    # Reassignment allowed - guest not in-house
    booking.room_reassigned_at = timezone.now()
    booking.room_reassigned_by = staff_user
    booking.assignment_version += 1
```

### After Check-In (Blocked)
```python
# In-house check: checked_in_at exists AND not checked_out_at
if booking.checked_in_at and not booking.checked_out_at:
    raise RoomAssignmentError('Cannot reassign room for in-house guest')
```

## Checkout Process and Room Release

### Checkout Service
**Location**: `room_bookings/services/checkout.py`

```python
def checkout_booking(*, booking, performed_by, source="staff_api"):
    with transaction.atomic():
        # Lock booking and room
        booking = booking.__class__.objects.select_for_update().get(id=booking.id)
        room = room.__class__.objects.select_for_update().get(id=room.id)
        
        # Update booking status
        booking.checked_out_at = timezone.now()
        booking.save()
        
        # Release room
        room.is_occupied = False
        room.room_status = 'CHECKOUT_DIRTY'
        room.guest_fcm_token = None
        room.save()
        
        # Cleanup guest sessions and data
        _cleanup_room_data(room, hotel)
        
        # Emit realtime events after commit
        transaction.on_commit(lambda: _emit_checkout_events(...))
```

## Assignment Tracking Fields

### RoomBooking Model Fields
```python
class RoomBooking(models.Model):
    # Current assignment
    assigned_room = ForeignKey(Room)
    room_assigned_at = DateTimeField()
    room_assigned_by = ForeignKey(Staff)
    assignment_notes = TextField()
    assignment_version = IntegerField(default=1)
    
    # Reassignment tracking
    room_reassigned_at = DateTimeField()
    room_reassigned_by = ForeignKey(Staff)
    
    # Unassignment tracking  
    room_unassigned_at = DateTimeField()
    room_unassigned_by = ForeignKey(Staff)
    
    # Check-in/out status
    checked_in_at = DateTimeField()
    checked_out_at = DateTimeField()
```

## Room Status Workflow

### 1. Initial Assignment
```
BOOKING: CONFIRMED → assigned_room set
ROOM: AVAILABLE → (still available until check-in)
```

### 2. Check-In Process  
```
BOOKING: checked_in_at set → Guest objects created
ROOM: is_occupied=True, room_status='OCCUPIED'
```

### 3. Checkout Process
```
BOOKING: checked_out_at set → Guests deactivated
ROOM: is_occupied=False, room_status='CHECKOUT_DIRTY'
```

### 4. Room Ready for Next Assignment
```
ROOM: room_status='READY' (via housekeeping workflow)
```

## Reassignment Scenarios

### Scenario 1: Pre-Check-In Reassignment
**Timeline**: Booking confirmed → Room assigned → Staff reassigns to different room → Check-in
```python
# ALLOWED: Guest not yet in-house
booking.assigned_room = new_room
booking.room_reassigned_at = now()
booking.room_reassigned_by = staff
booking.assignment_version += 1
```

### Scenario 2: Post-Check-In Reassignment Attempt  
**Timeline**: Booking confirmed → Room assigned → Check-in → Staff tries to reassign
```python
# BLOCKED: Guest is in-house
if booking.checked_in_at and not booking.checked_out_at:
    raise RoomAssignmentError('Cannot reassign room for in-house guest')
```

### Scenario 3: Post-Checkout Reassignment
**Timeline**: Check-in → Checkout → Staff assigns to new booking
```python
# ALLOWED: Room is now available after checkout
# Previous booking is no longer in-house (checked_out_at exists)
new_booking.assigned_room = room
```

## Available Rooms Logic

### Room Availability Query
**Location**: `RoomAssignmentService.find_available_rooms_for_booking()`

```python
# Exclude rooms with conflicting bookings
unavailable_rooms = Room.objects.filter(
    assignments__status__in=INVENTORY_BLOCKING_STATUSES,
    assignments__check_in_date__lt=booking.check_out_date,
    assignments__check_out_date__gt=booking.check_in_date
).values_list('id', flat=True)

available_rooms = Room.objects.filter(
    hotel=booking.hotel,
    is_active=True,
    is_out_of_order=False
).exclude(id__in=unavailable_rooms)
```

## Edge Cases and Considerations

### 1. Concurrent Assignment Prevention
- Uses `select_for_update()` on both booking and room
- Locks potentially conflicting bookings during assignment
- Atomic transactions prevent race conditions

### 2. Idempotent Operations
```python
# Assigning same room to same booking is idempotent
if booking.assigned_room_id == room_id:
    return booking  # No change needed
```

### 3. Capacity Validation
```python
party_total_count = booking.party.count()
if party_total_count > room.room_type.max_occupancy:
    raise ValidationError("Party size exceeds room capacity")
```

### 4. Status Constraints
```python
if booking.status != 'CONFIRMED':
    raise ValidationError("Booking must be CONFIRMED to assign room")
```

## Integration Points

### Realtime Notifications
- **Staff Events**: Room occupancy updates, booking status changes
- **Guest Events**: Room assignment notifications (without floor field)
- **Channel**: `hotel-{slug}.rooms` (staff), `private-guest-booking.{booking_id}` (guest)

### Housekeeping Integration  
- Checkout sets `room_status='CHECKOUT_DIRTY'`
- Housekeeping workflow moves to `'READY'` after cleaning
- Room becomes available for new assignments

### Admin Interface
- Shows booking assignments in room admin
- Color-coded status indicators:
  - 🔑 Blue: Room assigned, not checked in  
  - ✅ Green: Guest checked in
  - ❌ Red: Inconsistent state (occupied but no booking)

## Summary

The room assignment system follows a clear lifecycle:

1. **Assignment**: Room is reserved for booking (reversible before check-in)
2. **Check-in**: Guest moves in-house, room becomes occupied (no reassignment)  
3. **Checkout**: Room is released and becomes available for new assignments
4. **Housekeeping**: Room is cleaned and marked ready

The system prevents reassignment during the in-house period to maintain guest experience and data integrity, while allowing flexible pre-check-in management and immediate post-checkout availability for new bookings.