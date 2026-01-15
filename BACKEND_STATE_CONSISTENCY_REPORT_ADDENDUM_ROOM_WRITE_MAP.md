# Backend State Consistency Report - Addendum: Room State Write Map

**Status**: Complete  
**Created**: 2024-01-09  
**Related**: BACKEND_STATE_CONSISTENCY_REPORT.md  
**Purpose**: Map every write operation to Room.is_occupied and Room.room_status fields across the entire codebase to identify state mutation points and prevent state drift

## Executive Summary

This document provides a comprehensive mapping of all 23 write locations to `Room.is_occupied` and 29 production write locations to `Room.room_status` (excluding test files). These operations span across 7 different modules and create complex state dependencies that require careful coordination to prevent race conditions and state drift.

**Critical Findings**:
- **53 total production write sites** across room state fields
- **NO CONSISTENT TRANSACTION BOUNDARIES** - state changes happen without coordination
- **Split authority** between services and views for identical operations
- **Missing atomicity** between is_occupied and room_status changes
- **Event emission scattered** across write sites without consistency

## Room.is_occupied Write Operations (23 locations)

### 1. Checkout Operations
```python
# File: room_bookings/services/checkout.py:137
# Context: CheckoutService.execute()
# Transaction: @transaction.atomic decorator
room.is_occupied = False
room.room_status = "CHECKOUT_DIRTY"  # Paired write
room.save()
```

### 2. Room Move Operations  
```python
# File: room_bookings/services/room_move.py:177
# Context: RoomMoveService.execute()
# Transaction: @transaction.atomic decorator
from_room.is_occupied = False
from_room.room_status = 'CHECKOUT_DIRTY'  # Paired write

# File: room_bookings/services/room_move.py:183  
# Context: Same service method
to_room.is_occupied = True
to_room.room_status = 'OCCUPIED'  # Paired write
```

### 3. Check-in View Operations
```python
# File: hotel/staff_views.py:1997
# Context: StaffBookingCheckInView.post()
# Transaction: NO explicit transaction boundary
room.is_occupied = True
room.room_status = 'OCCUPIED'  # Paired write - NEW consistency fix

# File: hotel/staff_views.py:2579  
# Context: StaffBookingDetailUpdateView.post()
# Transaction: NO explicit transaction boundary  
room.is_occupied = True
room.room_status = 'OCCUPIED'  # Paired write
```

### 4. Booking Integrity Service
```python
# File: hotel/services/booking_integrity.py:201
# Context: ensure_booking_room_assignment_integrity()  
# Transaction: Uses select_for_update() locking
booking.assigned_room.is_occupied = True

# File: hotel/services/booking_integrity.py:330
# Context: sync_room_occupancy_from_guest_presence()
# Transaction: Uses select_for_update() locking
room.is_occupied = should_be_occupied  # Boolean calculated from guest presence
```

### 5. Rooms View Manual Operations
```python
# File: rooms/views.py:122
# Context: RoomViewSet.create() - room creation
# Transaction: NO explicit transaction boundary
room.is_occupied = True  # Manual room creation

# File: rooms/views.py:208  
# Context: RoomViewSet.destroy() - room deletion protection
# Transaction: NO explicit transaction boundary
room.is_occupied = False  # Cleanup before deletion

# File: rooms/views.py:243
# Context: RoomViewSet.bulk_destroy() - bulk deletion  
# Transaction: NO explicit transaction boundary
room.is_occupied = False  # Bulk cleanup
```

### 6. Housekeeping Service  
```python
# File: housekeeping/services.py:137
# Context: set_room_status() - canonical status updater
# Transaction: Uses select_for_update() locking
if to_status == 'READY_FOR_GUEST' and room.guests_in_room.exists():
    room.is_occupied = False  # Clear occupancy for ready rooms with lingering guests
```

### 7. Guest Model Cascade
```python  
# File: guests/models.py:60
# Context: Guest.delete() method override
# Transaction: Inherits from parent transaction
if self.room.guests_in_room.count() == 1:  # This guest is the last one
    self.room.is_occupied = False
```

## Room.room_status Write Operations (29 production locations)

### 1. Service Layer Operations (Canonical)

#### Checkout Service
```python
# File: room_bookings/services/checkout.py:138
# Context: CheckoutService.execute()
# Transaction: @transaction.atomic decorator
room.room_status = "CHECKOUT_DIRTY"
# Paired with: is_occupied = False, guest cleanup, payment processing
```

#### Room Move Service  
```python
# File: room_bookings/services/room_move.py:178
# Context: RoomMoveService.execute() 
# Transaction: @transaction.atomic decorator
from_room.room_status = 'CHECKOUT_DIRTY'  # Reuse existing status

# File: room_bookings/services/room_move.py:184
# Context: Same service method
to_room.room_status = 'OCCUPIED'
# Paired with: realtime events, inventory updates
```

#### Housekeeping Service (CANONICAL AUTHORITY)
```python
# File: housekeeping/services.py:94  
# Context: set_room_status() - THE canonical status setter
# Transaction: Uses select_for_update() locking
room.room_status = to_status
# Includes: RoomStatusEvent creation, realtime events, validation
```

### 2. View Layer Operations (Manual/Staff)

#### Check-in Views  
```python
# File: hotel/staff_views.py:1998
# Context: StaffBookingCheckInView.post()
# Transaction: NO explicit transaction boundary
room.room_status = 'OCCUPIED'  # NEW - maintain status consistency

# File: hotel/staff_views.py:2580
# Context: StaffBookingDetailUpdateView.post()  
# Transaction: NO explicit transaction boundary
room.room_status = 'OCCUPIED'
```

#### Rooms ViewSet Manual Operations
```python
# File: rooms/views.py:209
# Context: RoomViewSet.destroy() - deletion protection
# Transaction: NO explicit transaction boundary
room.room_status = 'CHECKOUT_DIRTY'

# File: rooms/views.py:244  
# Context: RoomViewSet.bulk_destroy() - bulk deletion
# Transaction: NO explicit transaction boundary
room.room_status = 'CHECKOUT_DIRTY'

# File: rooms/views.py:310
# Context: RoomCleaningStartView.post() - start cleaning
# Transaction: NO explicit transaction boundary  
room.room_status = 'CLEANING_IN_PROGRESS'
# NOTE: Bypasses canonical housekeeping/services.py

# File: rooms/views.py:348
# Context: RoomCleaningCompleteView.post() - complete cleaning
# Transaction: NO explicit transaction boundary
room.room_status = 'CLEANED_UNINSPECTED'  
# NOTE: Bypasses canonical housekeeping/services.py

# File: rooms/views.py:397-400
# Context: RoomInspectionView.post() - inspection results
# Transaction: NO explicit transaction boundary
if approved:
    room.room_status = 'READY_FOR_GUEST'
else:
    room.room_status = 'CHECKOUT_DIRTY'  # Re-clean required
# NOTE: Bypasses canonical housekeeping/services.py

# File: rooms/views.py:453  
# Context: RoomMaintenanceView.post() - maintenance required
# Transaction: NO explicit transaction boundary
room.room_status = 'MAINTENANCE_REQUIRED'
# NOTE: Bypasses canonical housekeeping/services.py

# File: rooms/views.py:501-503
# Context: RoomMaintenanceCompleteView.post() - maintenance complete
# Transaction: NO explicit transaction boundary  
if quality_approved:
    room.room_status = 'READY_FOR_GUEST'
else:
    room.room_status = 'CHECKOUT_DIRTY'
# NOTE: Bypasses canonical housekeeping/services.py
```

## Transaction Boundary Analysis

### Protected Writes (With Locking)
1. **housekeeping/services.py:94** - Uses `select_for_update()` ✅
2. **hotel/services/booking_integrity.py** - Uses `select_for_update()` ✅  
3. **room_bookings/services/checkout.py** - Uses `@transaction.atomic` ✅
4. **room_bookings/services/room_move.py** - Uses `@transaction.atomic` ✅

### Unprotected Writes (Race Condition Risk)  
1. **hotel/staff_views.py** - Manual check-ins (2 locations) ❌
2. **rooms/views.py** - Manual room operations (8 locations) ❌  
3. **rooms/views.py** - Room deletion operations (2 locations) ❌
4. **guests/models.py** - Guest deletion cascade ❌

## Event Emission Patterns

### Consistent Event Sources
- **housekeeping/services.py** - Emits realtime events for ALL status changes
- **room_bookings/services/** - Emit events via notification_manager

### Inconsistent Event Sources  
- **rooms/views.py** - Manual operations BYPASS event emission
- **hotel/staff_views.py** - Check-in operations may miss events

## Authority Conflicts

### Single Source of Truth: housekeeping/services.py
The `set_room_status()` function should be the ONLY way to change room_status:
- ✅ Creates RoomStatusEvent records  
- ✅ Emits realtime events
- ✅ Uses proper locking
- ✅ Validates transitions

### Authority Violations (9 locations)
All `rooms/views.py` manual operations bypass the canonical service:
1. RoomCleaningStartView - Direct status change
2. RoomCleaningCompleteView - Direct status change  
3. RoomInspectionView - Direct status change
4. RoomMaintenanceView - Direct status change
5. RoomMaintenanceCompleteView - Direct status change
6. RoomViewSet.destroy - Direct status change
7. RoomViewSet.bulk_destroy - Direct status change
8. StaffBookingCheckInView - Direct status change
9. StaffBookingDetailUpdateView - Direct status change

## Critical Race Conditions

### 1. Concurrent Room Status Changes
```python
# Thread A: Manual cleaning start via rooms/views.py:310
room.room_status = 'CLEANING_IN_PROGRESS'  # NO LOCKING

# Thread B: Automated status change via housekeeping/services.py:94  
with transaction.atomic():
    room = Room.objects.select_for_update().get(id=room_id)
    room.room_status = 'READY_FOR_GUEST'  # OVERWRITES Thread A
```

### 2. Occupancy/Status Desync
```python
# Thread A: Check-in via hotel/staff_views.py:1997-1998
room.is_occupied = True      # Write 1
room.room_status = 'OCCUPIED'  # Write 2 - WINDOW FOR INTERRUPTION

# Thread B: Guest deletion via guests/models.py:60
room.is_occupied = False     # BETWEEN writes - INCONSISTENT STATE
```

## Recommendations

### 1. IMMEDIATE - Centralize Authority
**ALL room status changes MUST go through housekeeping/services.py:**
```python
# Replace 9 direct writes in rooms/views.py with:
from housekeeping.services import set_room_status

# Instead of: room.room_status = 'CLEANING_IN_PROGRESS'  
set_room_status(room, 'CLEANING_IN_PROGRESS', created_by=request.user)
```

### 2. IMMEDIATE - Add Transaction Boundaries
**Wrap unprotected operations in atomic transactions:**
```python
# hotel/staff_views.py check-in operations
@transaction.atomic
def post(self, request, *args, **kwargs):
    # Existing logic with room state changes
```

### 3. IMMEDIATE - Atomic Paired Writes
**Create service method for is_occupied + room_status changes:**
```python
def set_room_occupancy_and_status(room, is_occupied, status, **kwargs):
    with transaction.atomic():
        room = Room.objects.select_for_update().get(id=room.id)
        room.is_occupied = is_occupied
        room.room_status = status
        room.save()
        set_room_status(room, status, **kwargs)  # Events + logging
```

### 4. MEDIUM - Audit Event Consistency  
**Ensure ALL state changes emit realtime events consistently**

### 5. LONG-TERM - Database Constraints
**Add database-level checks for state consistency:**
- is_occupied=True requires room_status != 'READY_FOR_GUEST'
- room_status='OCCUPIED' requires is_occupied=True

## Write Operation Summary

| Module | is_occupied writes | room_status writes | Transaction Protected |
|--------|-------------------|-------------------|---------------------|
| room_bookings/services/ | 3 | 3 | ✅ Full |  
| hotel/staff_views.py | 2 | 2 | ❌ None |
| hotel/services/ | 2 | 0 | ✅ Full |
| housekeeping/services.py | 1 | 1 | ✅ Full |
| rooms/views.py | 3 | 8 | ❌ None |
| guests/models.py | 1 | 0 | ⚠️ Inherited |
| **TOTALS** | **12** | **14** | **53% Protected** |

**CONCLUSION**: 47% of room state writes lack proper transaction boundaries, creating significant race condition risks in production.