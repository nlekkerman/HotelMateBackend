# Room Operations Guide: Assignment, Reassignment, Move & Unassignment

This document explains the different room operations available in the HotelMate booking system, their use cases, technical implementation, and key differences.

## Overview of Room Operations

The system provides four distinct room operations, each designed for specific booking lifecycle stages:

| Operation | When Used | Guest Status | Purpose |
|-----------|-----------|--------------|---------|
| **Assignment** | Initial room allocation | Not checked in | Assign a room to a confirmed booking |
| **Reassignment** | Change before check-in | Not checked in | Change assigned room before arrival |
| **Move** | Change after check-in | In-house (checked in) | Transfer guest to different room |
| **Unassignment** | Remove room allocation | Not checked in | Remove room assignment |

---

## 1. Room Assignment

### Purpose
Initial allocation of a physical room to a confirmed booking before guest arrival.

### When Used
- Booking status is `CONFIRMED`
- Guest has NOT checked in (`checked_in_at` is NULL)
- No room currently assigned (`assigned_room` is NULL)

### Technical Implementation
- **Service**: `RoomAssignmentService.assign_room_atomic()`
- **Endpoint**: `POST /api/staff/hotels/{slug}/bookings/{booking_id}/safe-assign-room/`
- **Database Fields Updated**:
  - `assigned_room` → target room
  - `room_assigned_at` → current timestamp
  - `room_assigned_by` → staff user
  - `assignment_notes` → optional notes
  - `assignment_version` → incremented

### Validation Rules
- ✅ Booking must be `CONFIRMED` status
- ✅ Guest must NOT be checked in
- ✅ Room must be available (no conflicts)
- ✅ Room type must match booking
- ✅ Room must be bookable (`is_active=True`, `is_out_of_order=False`)
- ✅ Hotel scoping enforced
- ✅ Party completion required

### Example Usage
```json
POST /api/staff/hotels/grand-hotel/bookings/BK-2025-0001/safe-assign-room/
{
  "room_id": 101,
  "notes": "Guest requested quiet room"
}
```

---

## 2. Room Reassignment

### Purpose
Change the assigned room before guest check-in (pre-arrival room change).

### When Used
- Booking already has an assigned room
- Guest has NOT checked in (`checked_in_at` is NULL)
- Need to change to different room (upgrade, maintenance, etc.)

### Technical Implementation
- **Service**: `RoomAssignmentService.assign_room_atomic()` (same as assignment)
- **Endpoint**: `POST /api/staff/hotels/{slug}/bookings/{booking_id}/safe-assign-room/`
- **Database Fields Updated**:
  - `assigned_room` → new target room
  - `room_reassigned_at` → current timestamp  
  - `room_reassigned_by` → staff user
  - `assignment_version` → incremented

### Key Difference from Assignment
- Automatically detects existing assignment and logs as reassignment
- Updates `room_reassigned_at/by` fields instead of `room_assigned_at/by`
- Previous room is freed up for other bookings

### Validation Rules
- ✅ Same as assignment rules
- ✅ Guest must NOT be checked in (critical safety check)
- ✅ Can reassign multiple times before check-in

### Example Usage
```json
POST /api/staff/hotels/grand-hotel/bookings/BK-2025-0001/safe-assign-room/
{
  "room_id": 102,
  "notes": "Upgraded to suite due to loyalty status"
}
```

---

## 3. Room Move (NEW - In-House Transfer)

### Purpose
Transfer checked-in guest from one room to another while maintaining their stay.

### When Used
- Guest is IN-HOUSE (`checked_in_at` is NOT NULL, `checked_out_at` is NULL)
- Need to move due to: complaints, maintenance, upgrades, overbooking resolution

### Technical Implementation
- **Service**: `RoomMoveService.move_room_atomic()` (NEW)
- **Endpoint**: `POST /api/staff/hotels/{slug}/bookings/{booking_id}/move-room/`
- **Database Fields Updated**:
  - `assigned_room` → new room
  - `room_moved_at` → current timestamp
  - `room_moved_by` → staff user  
  - `room_moved_from` → original room
  - `room_move_reason` → reason for move
  - `room_move_notes` → additional notes
  - `assignment_version` → incremented

### Room Status Changes
- **From Room**: `is_occupied=False`, `room_status='CHECKOUT_DIRTY'`, `guest_fcm_token=None`
- **To Room**: `is_occupied=True`, `room_status='OCCUPIED'`

### Validation Rules  
- ✅ Booking must be checked in (`checked_in_at` NOT NULL)
- ✅ Booking must NOT be checked out (`checked_out_at` IS NULL)  
- ✅ Must have assigned room
- ✅ Target room must be different (idempotent if same)
- ✅ Target room availability and capacity checks
- ✅ Hotel scoping enforced

### Data Cleanup
- Removes guest chat sessions, conversations, room service orders from old room
- Transfers guest context to new room

### Realtime Events
- `booking_updated` event
- `room_updated` events for both rooms

### Example Usage
```json  
POST /api/staff/hotels/grand-hotel/bookings/BK-2025-0001/move-room/
{
  "to_room_id": 105,
  "reason": "Guest complaint about noise from construction",
  "notes": "Moved to quieter wing, comp breakfast provided"
}
```

---

## 4. Room Unassignment

### Purpose
Remove room assignment from a booking before guest arrival.

### When Used
- Need to free up assigned room
- Booking changes (cancellation, date change)
- Guest has NOT checked in

### Technical Implementation
- **Service**: Manual database update (no dedicated service)
- **Endpoint**: `POST /api/staff/hotels/{slug}/bookings/{booking_id}/unassign-room/`
- **Database Fields Updated**:
  - `assigned_room` → NULL
  - `room_unassigned_at` → current timestamp
  - `room_unassigned_by` → staff user
  - `assignment_notes` → append unassignment log

### Validation Rules
- ✅ Guest must NOT be checked in (safety check)
- ✅ Must have assigned room
- ✅ Hotel scoping enforced

### Example Usage
```json
POST /api/staff/hotels/grand-hotel/bookings/BK-2025-0001/unassign-room/
{}
```

---

## Operation Comparison Matrix

| Feature | Assignment | Reassignment | Move | Unassignment |
|---------|------------|--------------|------|-------------|
| **Guest Status** | Not checked in | Not checked in | Checked in | Not checked in |
| **Existing Room** | None | Has room | Has room | Has room |
| **Result** | Room assigned | Room changed | Room transferred | Room removed |
| **Safety Check** | ✅ Not in-house | ✅ Not in-house | ✅ In-house only | ✅ Not in-house |
| **Room Cleanup** | ❌ N/A | ❌ N/A | ✅ Full cleanup | ❌ N/A |
| **Audit Fields** | assigned_at/by | reassigned_at/by | moved_at/by/from | unassigned_at/by |
| **Realtime Events** | ✅ | ✅ | ✅ | ❌ |

---

## Technical Safety Mechanisms

### Concurrency Protection
All operations use `select_for_update()` to lock:
- Booking record
- Current room (if any)  
- Target room (if applicable)

### Atomic Transactions
All operations are wrapped in `@transaction.atomic` to ensure data consistency.

### Hotel Scoping
All operations validate that:
- Staff belongs to hotel
- Booking belongs to hotel
- Target room belongs to hotel

### Status Validation
Each operation has specific booking status requirements:
- **Assignment/Reassignment/Unassignment**: Guest NOT in-house
- **Move**: Guest IN-HOUSE only

---

## Admin Interface Integration

All operations are tracked in Django Admin:

### List View
- Room assignment status
- Room move history (🔄 101 → 102)
- Timestamps and staff attribution

### Detail View
- **Room Assignment** section: Current assignment details
- **Room Move History** section: Complete audit trail (collapsed)
- All timestamps and staff members logged

---

## API Response Examples

### Successful Assignment
```json
{
  "message": "Successfully assigned room to booking BK-2025-0001",
  "booking_id": "BK-2025-0001",
  "assigned_room": {
    "id": 101,
    "room_number": 101,
    "room_type": "Standard Double"
  },
  "room_assigned_at": "2025-12-29T14:30:00Z",
  "room_assigned_by": "John Smith"
}
```

### Successful Move  
```json
{
  "message": "Successfully moved booking BK-2025-0001 to room 105", 
  "booking_id": "BK-2025-0001",
  "assigned_room": {
    "id": 105,
    "room_number": 105,
    "room_type": "Standard Double"  
  },
  "room_moved_at": "2025-12-29T16:45:00Z",
  "room_moved_by": "Jane Doe",
  "room_moved_from": {
    "id": 101,
    "room_number": 101
  },
  "room_move_reason": "Guest complaint about noise"
}
```

### Error Response
```json
{
  "error": {
    "code": "BOOKING_ALREADY_CHECKED_IN",
    "message": "Cannot reassign room for in-house guest", 
    "details": {}
  }
}
```

---

## Best Practices

### 1. Operation Selection
- Use **Assignment** for initial room allocation
- Use **Reassignment** for pre-arrival changes  
- Use **Move** only for in-house transfers
- Use **Unassignment** to free up rooms

### 2. Documentation
- Always provide meaningful `reason` and `notes` for moves
- Document upgrades, complaints, maintenance issues
- Track compensation provided (comp breakfast, etc.)

### 3. Guest Communication
- Notify guests of room changes
- Provide new room key/access
- Update any printed materials

### 4. System Integration
- Room moves trigger realtime updates
- Housekeeping systems notified via events
- Chat/messaging systems cleared from old room

---

## Error Handling

### Common Validation Errors

| Error Code | Cause | Solution |
|------------|-------|----------|
| `BOOKING_NOT_FOUND` | Invalid booking ID | Verify booking exists |
| `ROOM_NOT_FOUND` | Invalid room ID | Check room availability |  
| `BOOKING_ALREADY_CHECKED_IN` | Trying to reassign in-house guest | Use move operation instead |
| `BOOKING_NOT_CHECKED_IN` | Trying to move non-in-house guest | Check guest in first |
| `ROOM_OCCUPIED` | Target room unavailable | Choose different room |
| `HOTEL_MISMATCH` | Cross-hotel operation | Ensure same hotel |
| `PARTY_INCOMPLETE` | Missing guest names | Complete party information |

### Resolution Steps
1. **Check booking status** - Verify guest check-in state
2. **Validate room availability** - Ensure target room is free
3. **Confirm hotel scoping** - Staff and resources match hotel
4. **Complete party data** - Ensure all guest names provided
5. **Use appropriate operation** - Assignment vs Reassignment vs Move

---

## Migration Path

For bookings created before the move system:
- Existing assignments continue to work
- Reassignments use existing logic
- Moves available only after implementation
- Historical data preserved in existing audit fields

This comprehensive system ensures safe, audited room operations throughout the entire guest lifecycle while maintaining data integrity and providing full operational visibility.