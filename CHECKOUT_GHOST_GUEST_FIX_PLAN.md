# Checkout Ghost Guest Fix Implementation Plan

## Problem Statement

The checkout service (`checkout_booking`) has broken guest detachment logic. Current logic only detaches guests matching BOTH `booking=booking` AND `room=room`. When guests lose the booking link during corruption, this finds 0 rows and leaves "ghost" guests stuck in the room.

## Solution Overview

**Goal**: Fix checkout so it always clears the room of guests for the booking, even if guest↔booking links are corrupted.

**Core Logic**: During checkout, determine "affected guests" as:
- **(A)** All guests linked to the booking (booking guests), regardless of their room field  
- **(B)** All guests currently in the assigned room with `booking IS NULL` (orphan/ghost guests)

Then detach ALL affected guests from the room (`room=None`).

## Implementation Steps

### 1. Enhance Guest Detection Logic in `checkout_booking()`
**File**: [hotel/services/checkout.py](hotel/services/checkout.py)

Replace current query:
```python
# OLD (BROKEN):
guests = Guest.objects.filter(booking=booking, room=room)
```

With comprehensive detection:
```python
# NEW (ROBUST):
# A) All guests linked to booking
booking_guests = Guest.objects.filter(booking=booking)

# B) All orphaned guests currently in the assigned room  
orphaned_guests = Guest.objects.filter(room=room, booking__isnull=True)

# Union of affected guests
affected_guests = booking_guests.union(orphaned_guests)
# Note: The union queryset is used only to compute affected guest IDs;
# updates must be performed via a filtered queryset on those IDs.
```

### 2. Add Error-Level Logging for Invalid States
**Purpose**: Track when `booking IS NULL` guests exist in rooms (invalid state)

```python
if orphaned_guests.exists():
    orphaned_count = orphaned_guests.count()
    booking_count = booking_guests.count()
    logger.error(
        f"INVALID STATE: Found {orphaned_count} orphaned guests in room {room.room_number} "
        f"during checkout of booking {booking.booking_id}. "
        f"Booking guests: {booking_count}, Orphaned guests: {orphaned_count}. "
        f"Guest IDs: {list(orphaned_guests.values_list('id', flat=True))}"
    )
```

### 3. Detach All Affected Guests 
**Action**: Set `room=None` for ALL affected guests from both queries

```python
# Detach all affected guests from room
affected_guest_ids = list(affected_guests.values_list('id', flat=True))
detached_count = Guest.objects.filter(id__in=affected_guest_ids).update(room=None)

logger.info(f"Detached {detached_count} guests from room {room.room_number} during checkout")
```

### 4. Add Consistency Assertion After Detachment
**Purpose**: Verify room is completely cleared inside the transaction
**Critical**: If this assertion fails, checkout must abort — a room with remaining guests after checkout is a fatal invariant violation.

```python
# Consistency check: ensure no guests remain in room
remaining_guests = Guest.objects.filter(room=room)
if remaining_guests.exists():
    remaining_count = remaining_guests.count()
    logger.error(
        f"CONSISTENCY FAILURE: {remaining_count} guests still in room {room.room_number} "
        f"after checkout cleanup for booking {booking.booking_id}"
    )
    raise ValueError(f"Checkout failed: {remaining_count} guests still assigned to room")

logger.info(f"Verified room {room.room_number} completely cleared of guests")
```

### 5. Transaction Safety with Proper Locking
**Requirement**: Lock booking + room with `select_for_update()`

```python
with transaction.atomic():
    # Lock booking and room BEFORE running guest queries to prevent race conditions
    booking = RoomBooking.objects.select_for_update().get(id=booking.id)
    room = Room.objects.select_for_update().get(id=room.id)
    
    # Enhanced guest cleanup logic here
    # ... (steps 1-4 above)
    
    # Continue with existing checkout flow
    # Update booking status, room status, etc.
```

### 6. Bug Reproduction Test
**File**: [hotel/test/test_assignment_views.py](hotel/test/test_assignment_views.py)

```python
def test_checkout_with_ghost_guests(self):
    """
    Test checkout with corrupted guest-booking links.
    Scenario: Room 337 has guests with booking=NULL, 
    while booking guests have room=NULL.
    """
    # Setup: Create booking, room, guests with corrupted links
    booking = self.create_booking()
    room = self.create_room(room_number="337")
    
    # Create booking guests with room=NULL (corrupted state)
    booking_guest = self.create_guest(booking=booking, room=None)
    
    # Create orphaned guests in room with booking=NULL (ghost state) 
    ghost_guest = self.create_guest(booking=None, room=room)
    
    # Action: Checkout
    response = self.client.post(f'/api/staff/hotels/{self.hotel.slug}/room-bookings/{booking.booking_id}/check-out/')
    
    # Verify: Success response
    self.assertEqual(response.status_code, 200)
    
    # Verify: No guests remain in room
    remaining_guests = Guest.objects.filter(room=room)
    self.assertEqual(remaining_guests.count(), 0, "Room should have zero guests after checkout")
    
    # Verify: Booking completed
    booking.refresh_from_db()
    self.assertIsNotNone(booking.checked_out_at)
    self.assertEqual(booking.status, 'COMPLETED')
    
    # Verify: Room not occupied
    room.refresh_from_db()
    self.assertFalse(room.is_occupied)
```

### 7. One-Time Cleanup Management Command
**File**: `hotel/management/commands/cleanup_orphaned_guests.py`

```python
from django.core.management.base import BaseCommand
from hotel.models import Guest

class Command(BaseCommand):
    help = 'Clean up orphaned guests (room assigned but no booking)'
    
    def add_arguments(self, parser):
        parser.add_argument('--hotel-slug', help='Target specific hotel')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned without making changes')
    
    def handle(self, *args, **options):
        # Target: Guests with room assigned but no booking
        queryset = Guest.objects.filter(room__isnull=False, booking__isnull=True)
        
        if options['hotel_slug']:
            queryset = queryset.filter(hotel__slug=options['hotel_slug'])
        
        count = queryset.count()
        
        if options['dry_run']:
            self.stdout.write(f"Would clean up {count} orphaned guests")
            return
        
        # Execute cleanup
        updated = queryset.update(room=None)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned up {updated} orphaned guests')
        )
```

## Success Criteria

✅ **After checkout, room has zero guests assigned**
✅ **No more Room 337 ghosts** 
✅ **Invalid guest states are logged and tracked**
✅ **Checkout remains atomic and concurrency-safe**

## Files to Modify

1. **[hotel/services/checkout.py](hotel/services/checkout.py)** - Main checkout service enhancement
2. **[hotel/test/test_assignment_views.py](hotel/test/test_assignment_views.py)** - Add bug reproduction test
3. **`hotel/management/commands/cleanup_orphaned_guests.py`** - New cleanup command

## Risk Mitigation

- **Transaction Safety**: All changes remain within existing transaction boundaries
- **Idempotent Operations**: Checkout can still be called multiple times safely
- **Backward Compatibility**: No changes to API contracts or overall flow
- **Comprehensive Logging**: Error-level logs for tracking and debugging
- **Consistency Checks**: Runtime verification that rooms are properly cleared