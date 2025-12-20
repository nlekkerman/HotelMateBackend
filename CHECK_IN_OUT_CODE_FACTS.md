# Django Project Code-Level Facts for Check-In/Out Implementation

**Date**: December 20, 2025  
**Purpose**: Data collection for check-in/out implementation  
**Status**: Fact-finding complete ✅  

## A) Room Model + Status Machine

**File**: `rooms/models.py`

### ROOM_STATUS_CHOICES Exact Values
```python
ROOM_STATUS_CHOICES = [
    ('AVAILABLE', 'Available'),
    ('OCCUPIED', 'Occupied'),
    ('CHECKOUT_DIRTY', 'Checkout Dirty'),
    ('CLEANING_IN_PROGRESS', 'Cleaning in Progress'),
    ('CLEANED_UNINSPECTED', 'Cleaned Uninspected'), 
    ('MAINTENANCE_REQUIRED', 'Maintenance Required'),
    ('OUT_OF_ORDER', 'Out of Order'),
    ('READY_FOR_GUEST', 'Ready for Guest'),
]
```

### Key Status Mappings
- **READY_FOR_GUEST**: `'READY_FOR_GUEST'`
- **OCCUPIED**: `'OCCUPIED'`
- **CHECKOUT_DIRTY**: `'CHECKOUT_DIRTY'`

### State Machine Implementation
```python
def can_transition_to(self, new_status):
    """Validate state machine transitions"""
    valid_transitions = {
        'AVAILABLE': ['OCCUPIED', 'MAINTENANCE_REQUIRED', 'OUT_OF_ORDER'],
        'OCCUPIED': ['CHECKOUT_DIRTY'],
        'CHECKOUT_DIRTY': ['CLEANING_IN_PROGRESS', 'CLEANED_UNINSPECTED', 'MAINTENANCE_REQUIRED'],
        'CLEANING_IN_PROGRESS': ['CLEANED_UNINSPECTED', 'CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED'],
        'CLEANED_UNINSPECTED': ['READY_FOR_GUEST', 'CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED'],
        'MAINTENANCE_REQUIRED': ['CHECKOUT_DIRTY', 'OUT_OF_ORDER'],
        'OUT_OF_ORDER': ['CHECKOUT_DIRTY'],
        'READY_FOR_GUEST': ['OCCUPIED', 'MAINTENANCE_REQUIRED', 'OUT_OF_ORDER'],
    }
    return new_status in valid_transitions.get(self.room_status, [])
```

### Fields Updated on Check-In/Out
- `room_status` - Primary workflow state
- `is_occupied` - Boolean flag for quick queries
- `last_cleaned_at` - Timestamp when room was last cleaned
- `last_inspected_at` - Timestamp when room was last inspected
- `cleaned_by_staff` - FK to Staff who cleaned
- `inspected_by_staff` - FK to Staff who inspected

### Turnover Notes Signature
```python
def add_turnover_note(self, note, staff_member=None):
    """Add timestamped note to turnover history"""
    from django.utils import timezone
    timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
    staff_info = f" by {staff_member.get_full_name()}" if staff_member else ""
    new_note = f"[{timestamp}]{staff_info}: {note}"
    
    if self.turnover_notes:
        self.turnover_notes += f"\n{new_note}"
    else:
        self.turnover_notes = new_note
    self.save()
```

---

## B) RoomBooking Model + Eligibility Fields

**File**: `hotel/models.py`

### STATUS_CHOICES Exact Values
```python
STATUS_CHOICES = [
    ('PENDING_PAYMENT', 'Pending Payment'),
    ('PENDING_APPROVAL', 'Pending Staff Approval'),
    ('CONFIRMED', 'Confirmed'),
    ('DECLINED', 'Declined'),
    ('CANCELLED', 'Cancelled'),
    ('COMPLETED', 'Completed'),
    ('NO_SHOW', 'No Show'),
]
```

### Check-In/Out Field Names
- `checked_in_at` - DateTimeField, null=True, blank=True
- `checked_out_at` - DateTimeField, null=True, blank=True

### Assignment Fields (Audit Trail)
- `assigned_room` - FK to Room, null=True, blank=True
- `room_assigned_at` - DateTimeField for audit
- `room_assigned_by` - FK to Staff for audit
- `room_reassigned_at` - DateTimeField for audit
- `room_unassigned_at` - DateTimeField for audit

### Stay Date Fields
- `check_in` - DateField (required)
- `check_out` - DateField (required)

### Payment Fields (Eligibility Markers)
- `paid_at` - DateTimeField, null=True, blank=True
- `payment_status` - Not directly stored (derived from paid_at)
- `payment_provider` - CharField, max_length=50, blank=True
- `payment_provider_metadata` - CharField, max_length=200, blank=True

### Party Relation Access Pattern
- `party` - Related name for BookingGuest instances
- Access via: `booking.party.all()` or `booking.party.filter(role='PRIMARY')`

---

## C) BookingGuest Model (Party Source)

**File**: `hotel/models.py`

### Role Enum Values
```python
ROLE_CHOICES = [
    ('PRIMARY', 'Primary Staying Guest'),
    ('COMPANION', 'Companion'),
]
```
- Field name: `role`

### Fields Copied to Guest
- `first_name` - CharField, max_length=100
- `last_name` - CharField, max_length=100
- `email` - EmailField, blank=True
- `phone_number` - CharField, max_length=30, blank=True
- `guest_data` - JSONField for additional guest-specific data

### Unique Identifier for Idempotency
- **Constraint**: `unique_primary_per_booking` - Only one PRIMARY per booking
- **Idempotency key**: `(booking, role='PRIMARY')` for PRIMARY guests
- **Link field**: `booking_guest` FK in Guest model for 1:1 mapping

---

## D) Guest Model (In-House Reality)

**File**: `guests/models.py`

### FK Fields
- `booking` - FK to RoomBooking, null=True, blank=True, related_name='guests'
- `booking_guest` - FK to BookingGuest, null=True, blank=True, related_name='in_house_guest'
- `room` - FK to Room, null=True, blank=True, related_name='guests_in_room'
- `hotel` - FK to Hotel, on_delete=CASCADE, null=True, blank=True

### Unique Constraints
- **None found** - Uses natural uniqueness through PK
- Relies on application-level logic for booking_guest 1:1 mapping

### Active/In-House Marker
```python
@property
def in_house(self):
    today = timezone.now().date()
    return self.check_in_date and self.check_out_date and self.check_in_date <= today <= self.check_out_date
```

### ⚠️ CRITICAL: Guest.delete() Modifies room.is_occupied
```python
def delete(self, *args, **kwargs):
    # Set room to unoccupied if this guest is assigned a room
    if self.room:
        self.room.is_occupied = False
        self.room.save()
    super().delete(*args, **kwargs)
```

---

## E) Guest Session/Portal Access

**File**: `chat/models.py`

### Guest Session Model Found: GuestChatSession
- `session_id` - UUIDField, unique=True (primary identifier)
- `conversation` - FK to Conversation
- `room` - FK to Room
- `is_active` - BooleanField, default=True
- `expires_at` - DateTimeField (auto-expires after 7 days)

### Session Revocation Methods
- Set `is_active=False`
- Check `expires_at` property method
- Found in `chat/services.py` - session management utilities

**Recommendation**: Create `guests.services.revoke_guest_portal_sessions(guest)` for consistency

---

## F) NotificationManager Realtime Room Update

**File Path**: `notifications/notification_manager.py`

### ✅ Existing Method: realtime_room_updated()
```python
def realtime_room_updated(self, room, changed_fields=None, source="system"):
    """Emit normalized room updated event for operational updates."""
    # Method already exists and is fully implemented
```

### Rooms Event Payload Schema
- **Full room snapshot** with changed_fields array
- **Channel**: `{hotel_slug}.rooms`
- **Event**: `room_updated`
- **Category**: `rooms`

### Transaction.on_commit Usage (Already Implemented)
```python
from django.db import transaction
transaction.on_commit(
    lambda: notification_manager.realtime_room_updated(
        room=room,
        changed_fields=fields_to_update,
        source=source.lower()
    )
)
```

---

## G) Staff Routing - Where Check-In/Out Endpoints Should Live

**Main Staff Routing File**: `staff_urls.py`

### Current Pattern
- **Format**: `/api/staff/hotel/<hotel_slug>/<app_name>/`
- **Example**: `/api/staff/hotel/hotel-killarney/room-bookings/`

### Turnover Endpoints Location
- **File**: `rooms/staff_urls.py`
- **Paths**: Room-specific operations like start-cleaning, etc.

### Correct Place for New Check-In/Out Endpoints

#### Option 1: Room-Related Operations
- **File**: `rooms/staff_urls.py` 
- **Pattern**: `/api/staff/hotel/{hotel_slug}/rooms/{room_number}/check-in/`

#### Option 2: Booking-Related Operations  
- **File**: `room_bookings/staff_urls.py`
- **Pattern**: `/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/check-in/`

#### Option 3: Housekeeping Integration
- **File**: `housekeeping/staff_urls.py`
- **Pattern**: `/api/staff/hotel/{hotel_slug}/housekeeping/rooms/{room_id}/check-in/`

### ✅ Existing Check-In/Out Endpoints Found
- **File**: `room_bookings/staff_views.py`
- **Methods**: Check-in process (BookingAssignmentView)
- **Methods**: Checkout process (BookingAssignmentView)

---

## H) Summary: Code-Level Facts

### Room Statuses
- **Values**: 8 statuses from AVAILABLE to READY_FOR_GUEST
- **Check-in flow**: READY_FOR_GUEST → OCCUPIED
- **Check-out flow**: OCCUPIED → CHECKOUT_DIRTY

### RoomBooking Statuses + Fields
- **Eligible status**: CONFIRMED (must be paid: paid_at not null)
- **Check-in fields**: checked_in_at, checked_out_at
- **Payment validation**: booking.paid_at is not None

### BookingGuest Fields + Role Values
- **Roles**: PRIMARY, COMPANION
- **Copy fields**: first_name, last_name, email, phone_number, guest_data
- **Idempotency**: booking_guest FK provides 1:1 mapping

### Guest Model Mapping + Constraints
- **Key FKs**: booking, booking_guest, room, hotel
- **No unique constraints** - relies on application logic
- **⚠️ WARNING**: Guest.delete() automatically sets room.is_occupied = False

### Guest Session Revocation
- **Exists**: GuestChatSession with is_active flag
- **Method needed**: Create revoke_guest_portal_sessions() service function

### NotificationManager Rooms Events
- **Method exists**: realtime_room_updated() fully implemented
- **Payload**: Full room snapshot with changed_fields
- **Usage**: Already integrated with transaction.on_commit

### Where to Place Endpoints
- **Recommended**: `room_bookings/staff_urls.py` (booking-centric operations)
- **Alternative**: `rooms/staff_urls.py` (room-centric operations)
- **Note**: Existing check-in/out logic found in BookingAssignmentView

---

## Unknowns/Gaps Identified

1. **Guest portal session model** - Only found GuestChatSession, may need broader guest session management
2. **Idempotency handling** - Need to verify booking_guest → guest mapping is enforced at application level
3. **Permission validation** - Need to identify which staff roles can perform check-in/out
4. **Concurrent check-in handling** - No database constraints prevent double check-ins

---

## Next Steps Recommended

1. **Extend existing BookingAssignmentView** rather than creating new endpoints
2. **Use housekeeping.services.set_room_status()** for room status changes
3. **Leverage existing realtime_room_updated()** for notifications
4. **Create guest session revocation service** for portal security
5. **Add booking_guest unique constraint** for data integrity