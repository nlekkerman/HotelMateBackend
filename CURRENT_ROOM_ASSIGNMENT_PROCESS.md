# Current Room Assignment Process for Check-In
**Backend Source of Truth - December 2025**

## Overview

This document describes the **current canonical process** for finding and assigning rooms to bookings during check-in. This is the active, non-legacy system used in production.

---

## 🏠 Room Assignment Architecture

### Core Service: `RoomAssignmentService`
**Location**: [`room_bookings/services/room_assignment.py`](room_bookings/services/room_assignment.py)

The canonical room assignment logic is centralized in a dedicated service class that handles:
- Finding available rooms for bookings
- Validating room assignment eligibility 
- Atomic room assignment with concurrency safety
- Conflict detection and overlap prevention

---

## 🔍 Room Finding Process

### 1. Available Rooms Discovery

**Method**: `RoomAssignmentService.find_available_rooms_for_booking(booking)`

**Process**:
1. **Hotel Scope**: Filter rooms belonging to same hotel as booking
2. **Room Type Match**: Only rooms matching `booking.room_type`
3. **Bookability Check**: Apply `room.is_bookable()` logic
4. **Conflict Detection**: Exclude rooms with overlapping bookings

#### Room Bookability Rules

**Source**: [`rooms/models.py`](rooms/models.py#L112) - `Room.is_bookable()` method

A room is bookable **IF AND ONLY IF**:
```python
def is_bookable(self):
    # Hard override flag
    if self.is_out_of_order:
        return False
        
    return (
        self.room_status == 'READY_FOR_GUEST' and  # CANONICAL STATUS
        self.is_active and
        not self.maintenance_required
    )
```

**Key Points**:
- **ONLY `READY_FOR_GUEST`** status rooms are bookable (not `AVAILABLE`)
- `AVAILABLE` is legacy status, treated as `READY_FOR_GUEST` in some contexts
- `is_out_of_order` is a hard override that makes room unbookable regardless of other flags

#### Conflict Detection Logic

**Blocking Conditions** - A room is considered blocked/unavailable if it has overlapping bookings that meet:

```python
blocking_filter = models.Q(
    status__in=['CONFIRMED'],     # CONFIRMED bookings block inventory
    checked_out_at__isnull=True   # Not checked out yet
) | models.Q(
    checked_in_at__isnull=False,  # Checked in guests  
    checked_out_at__isnull=True   # Not checked out yet (in-house)
)
```

**Date Overlap Logic**:
```python
# Standard interval overlap: (existing.check_in < booking.check_out) AND (existing.check_out > booking.check_in)
check_in__lt=booking.check_out,
check_out__gt=booking.check_in
```

**Non-Blocking Statuses**: `["CANCELLED", "COMPLETED", "NO_SHOW"]`

---

## ✅ Room Assignment Validation

### 2. Assignment Eligibility Check

**Method**: `RoomAssignmentService.assert_room_can_be_assigned(booking, room)`

**Validation Rules**:

1. **Hotel Scope Validation**
   - Room must belong to same hotel as booking
   - Booking's room type must belong to same hotel

2. **Booking Status Validation**  
   - Booking status must be in `ASSIGNABLE_BOOKING_STATUSES = ["CONFIRMED"]`

3. **Check-in Status Validation**
   - Cannot assign room if guest already checked in (in-house)
   - In-house defined as: `checked_in_at IS NOT NULL AND checked_out_at IS NULL`

4. **Room Type Matching**
   - `room.room_type` must exactly match `booking.room_type`

5. **Room Bookability**
   - Room must pass `room.is_bookable()` check

6. **Overlap Conflict Check**
   - No overlapping bookings that would block inventory
   - Same logic as room finding process

---

## 🔒 Atomic Assignment Process

### 3. Safe Room Assignment

**Method**: `RoomAssignmentService.assign_room_atomic(booking_id, room_id, staff_user, notes=None)`

**Concurrency Safety Features**:

1. **Database Locking**:
   ```python
   # Lock booking and room for update
   booking = RoomBooking.objects.select_for_update().get(id=booking_id)
   room = Room.objects.select_for_update().get(id=room_id)
   
   # Lock potentially conflicting bookings
   potentially_conflicting = RoomBooking.objects.select_for_update().filter(
       assigned_room=room,
       # ... overlap conditions
   )
   ```

2. **Transaction Atomicity**:
   - Entire assignment wrapped in `@transaction.atomic`
   - Validations re-run inside transaction for consistency

3. **Idempotent Operations**:
   - If room already assigned to same booking, returns existing
   - Handles reassignment scenarios safely

4. **Audit Trail**:
   ```python
   booking.assigned_room = room
   booking.room_assigned_at = timezone.now()
   booking.room_assigned_by = staff_user
   booking.assignment_notes = notes or ''
   booking.assignment_version += 1
   ```

---

## 🌐 API Endpoints

### Current Check-In Endpoints

#### 1. Safe Assignment Endpoint (RECOMMENDED)
```
POST /api/staff/hotels/{hotel_slug}/bookings/{booking_id}/safe-assign-room/
```
**Body**: `{"room_id": 123, "notes": "Optional notes"}`
**Features**:
- Uses `RoomAssignmentService.assign_room_atomic()`
- Full concurrency safety
- Structured error responses
- Party completion validation

#### 2. Legacy Assignment Endpoint  
```
POST /api/staff/hotels/{hotel_slug}/bookings/{booking_id}/assign-room/
```
**Body**: `{"room_number": 203}`
**Features**:
- Direct room validation and assignment
- Manual database operations  
- Creates/updates Guest records
- Updates room occupancy status

#### 3. Available Rooms Query
```
GET /api/staff/hotels/{hotel_slug}/bookings/{booking_id}/available-rooms/
```
**Response**: List of rooms available for the specific booking
**Uses**: `RoomAssignmentService.find_available_rooms_for_booking()`

---

## 📊 Room Status Management

### Status Transitions During Assignment

1. **Pre-Assignment**: Room is `READY_FOR_GUEST`
2. **Assignment**: Room assigned to booking (`assigned_room` field set)
3. **Check-In**: 
   - `booking.checked_in_at = timezone.now()`
   - `room.room_status = 'OCCUPIED'`
   - `room.is_occupied = True`

### Legacy Status Handling

**Important**: `AVAILABLE` status still exists in some databases but:
- Treated as equivalent to `READY_FOR_GUEST` in business logic
- Should be migrated to `READY_FOR_GUEST` 
- Room assignment service currently filters for `READY_FOR_GUEST` only
- Migration available: [`rooms/migrations/0016_convert_available_to_ready_for_guest.py`](rooms/migrations/0016_convert_available_to_ready_for_guest.py)

---

## 🎯 Key Business Rules

### Room Assignment Prerequisites

1. **Booking Requirements**:
   - Status: `CONFIRMED`
   - Party information complete (`party_complete = True`)
   - Primary guest name present

2. **Room Requirements**:
   - Status: `READY_FOR_GUEST` (canonical ready state)
   - `is_active = True`
   - `is_out_of_order = False`  
   - `maintenance_required = False`
   - Correct room type matching booking

3. **Conflict Prevention**:
   - No overlapping confirmed/in-house bookings
   - Atomic assignment prevents double-booking
   - Database-level constraints ensure data integrity

### Error Handling

**Structured Error Codes** (from `RoomAssignmentService`):
- `HOTEL_MISMATCH`: Room belongs to different hotel
- `BOOKING_STATUS_NOT_ASSIGNABLE`: Booking not in CONFIRMED state
- `BOOKING_ALREADY_CHECKED_IN`: Cannot assign to in-house guest
- `ROOM_TYPE_MISMATCH`: Room type doesn't match booking
- `ROOM_NOT_BOOKABLE`: Room not in ready state
- `ROOM_OVERLAP_CONFLICT`: Overlapping booking exists

---

## 🔧 Implementation Status

### Current State (December 2025)

✅ **Active**: `RoomAssignmentService` - canonical service layer  
✅ **Active**: Safe assignment endpoint with concurrency protection  
✅ **Active**: Room status `READY_FOR_GUEST` as bookable state  
⚠️ **Legacy**: Direct assignment endpoint (still functional)  
⚠️ **Legacy**: `AVAILABLE` status (being migrated)  

### Recommended Usage

**For New Development**:
1. Use `RoomAssignmentService.find_available_rooms_for_booking()` for room discovery
2. Use `RoomAssignmentService.assign_room_atomic()` for assignments  
3. Use `/safe-assign-room/` API endpoint
4. Filter rooms by `room_status = 'READY_FOR_GUEST'`

**Migration Path**:
1. Convert all `AVAILABLE` rooms to `READY_FOR_GUEST`
2. Update frontend to use new endpoint
3. Deprecate legacy assignment logic

---

## 📁 File References

### Core Implementation Files
- [`room_bookings/services/room_assignment.py`](room_bookings/services/room_assignment.py) - Main service
- [`room_bookings/constants.py`](room_bookings/constants.py) - Business rule constants  
- [`rooms/models.py`](rooms/models.py#L112) - Room.is_bookable() method
- [`hotel/staff_views.py`](hotel/staff_views.py#L2029) - SafeAssignRoomView endpoint

### Supporting Files
- [`room_bookings/exceptions.py`](room_bookings/exceptions.py) - RoomAssignmentError
- [`ROOM_STATUS_CANONICAL_TRUTH.md`](ROOM_STATUS_CANONICAL_TRUTH.md) - Status documentation
- [`SAFE_ROOM_ASSIGNMENT_IMPLEMENTATION_PLAN.md`](SAFE_ROOM_ASSIGNMENT_IMPLEMENTATION_PLAN.md) - Implementation guide

---

**Document Status**: ✅ Current as of December 20, 2025  
**Next Review**: When room assignment logic changes  
**Maintained by**: Backend development team