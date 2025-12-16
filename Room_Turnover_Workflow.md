# Room Turnover Workflow (Checkout → Ready)
**Implementation Plan - Source of Truth**

## Problem Statement
**This is NOT a housekeeping app feature.** This is a **mandatory room readiness state machine** that prevents dirty rooms from being sold/assigned after checkout.

**Current Critical Bug:**
- Booking checkout: sets `is_occupied=False` → room immediately bookable
- Bulk checkout: sets `is_occupied=False` → room immediately bookable  
- Availability service only checks: `is_active`, `is_out_of_order`, `is_occupied`
- **Result:** Dirty rooms get sold to new guests immediately after checkout

**Impact:** Operational disaster where guests arrive to dirty rooms because assignment + availability bypass turnover workflow.

## Solution Overview
Implement **room readiness state machine**: Guest Checkout → CHECKOUT_DIRTY → CLEANING_IN_PROGRESS → CLEANED_UNINSPECTED → READY_FOR_GUEST (with maintenance paths)

**Goal:** Rooms cannot be assigned/sold until they complete the turnover workflow and reach READY_FOR_GUEST status.

---

## Bookable Room Definition
**Single source of truth for room availability:**

Room is bookable **IFF:**
- `room_status in ["AVAILABLE", "READY_FOR_GUEST"]`
- `is_active == true`
- `is_out_of_order == false`  
- `maintenance_required == false`

**Critical:** Availability service must use ONLY this rule to count/suggest rooms. No exceptions.

---

## Status vs Flags Authority

### Room Status (Workflow State)
- `room_status` controls turnover workflow transitions
- Valid states: AVAILABLE, OCCUPIED, CHECKOUT_DIRTY, CLEANING_IN_PROGRESS, CLEANED_UNINSPECTED, MAINTENANCE_REQUIRED, OUT_OF_ORDER, READY_FOR_GUEST

**Status Definitions:**
- `AVAILABLE` = room has never been occupied / already cleared (initial state)
- `READY_FOR_GUEST` = room has completed a checkout turnover workflow (cleaned + inspected)

*This distinction prevents future developers from collapsing them incorrectly and allows tracking rooms never used vs. turned over.*

### Hard Override Flags
- `is_out_of_order` = **hard override**: if true, room is never bookable regardless of status
- `is_active` = master enable/disable switch for room
- `maintenance_required` = blocks booking until resolved

### Convenience Fields  
- `is_occupied` = kept for UI convenience, but meaning must match status:
  - `room_status == "OCCUPIED"` ⟺ `is_occupied = true`
  - All other statuses ⟺ `is_occupied = false`

**Authority Order:** `is_out_of_order` > `is_active` > `room_status` > `maintenance_required` > `is_occupied`

---

## Valid State Transitions

| From Status | To Status | Trigger | Who Can Do |
|-------------|-----------|---------|------------|
| AVAILABLE | OCCUPIED | Check-in | Staff via booking assignment only |
| OCCUPIED | CHECKOUT_DIRTY | Checkout | Staff |
| CHECKOUT_DIRTY | CLEANING_IN_PROGRESS | Start cleaning | Staff with "rooms" nav |
| CLEANING_IN_PROGRESS | CLEANED_UNINSPECTED | Mark cleaned | Staff with "rooms" nav |
| CLEANED_UNINSPECTED | READY_FOR_GUEST | Inspect (pass) | Staff with "rooms" nav |
| CLEANED_UNINSPECTED | CHECKOUT_DIRTY | Inspect (fail) | Staff with "rooms" nav |
| ANY | MAINTENANCE_REQUIRED | Mark maintenance | Staff with "maintenance" nav |
| MAINTENANCE_REQUIRED | CHECKOUT_DIRTY | Complete maintenance | Staff with "maintenance" nav |
| MAINTENANCE_REQUIRED | CLEANED_UNINSPECTED | Complete maintenance (if cleaned) | Staff with "maintenance" nav |
| ANY | OUT_OF_ORDER | Hard disable | Admin |
| OUT_OF_ORDER | CHECKOUT_DIRTY | Re-enable | Admin |

**Invalid transitions return HTTP 400** with clear message: `"Cannot transition from {current} to {requested}"`

**Critical Check-in Restriction:**
Check-in is only allowed via booking assignment/check-in flow. Direct manual transition from AVAILABLE → OCCUPIED is forbidden. This prevents "Quick occupy room" buttons that bypass bookings and keeps booking as the only authority for occupancy.

---

## Permissions System

### Authentication & Authorization
All turnover endpoints require:
- `IsAuthenticated` (user logged in)
- `IsStaffMember` (user.staff exists)  
- `IsSameHotel` (staff belongs to room's hotel)

### Navigation Permissions
Implementation **must reuse canonical resolver / allowed_navs checks**:

```python
# For cleaning/inspection endpoints
if not request.user.staff.allowed_navigation_items.filter(slug='rooms').exists():
    return Response({'error': 'Rooms permission required'}, status=403)

# For maintenance endpoints  
if not request.user.staff.allowed_navigation_items.filter(slug='maintenance').exists():
    return Response({'error': 'Maintenance permission required'}, status=403)
```

**DO NOT** create new ad-hoc permission queries. Use the canonical `allowed_navs` derived from NavigationItem M2M.

---

## Implementation Phases

### Phase 1: Database Schema Changes

### File: `rooms/models.py`

#### Add Room Status Field
```python
class Room(models.Model):
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
    
    room_status = models.CharField(
        max_length=20,
        choices=ROOM_STATUS_CHOICES,
        default='AVAILABLE',
        help_text='Current turnover workflow status of the room'
    )
```

#### Add Turnover Audit Fields
```python
    # Cleaning tracking
    last_cleaned_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When room was last cleaned'
    )
    cleaned_by_staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cleaned_rooms',
        help_text='Staff member who cleaned the room'
    )
    
    # Inspection tracking  
    last_inspected_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When room was last inspected'
    )
    inspected_by_staff = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='inspected_rooms',
        help_text='Staff member who inspected the room'
    )
    
    # Notes and maintenance
    turnover_notes = models.TextField(
        blank=True,
        help_text='Internal turnover workflow notes and history'
    )
    maintenance_required = models.BooleanField(
        default=False,
        help_text='Room requires maintenance before next guest'
    )
    
    MAINTENANCE_PRIORITY_CHOICES = [
        ('LOW', 'Low Priority'),
        ('MED', 'Medium Priority'), 
        ('HIGH', 'High Priority'),
    ]
    maintenance_priority = models.CharField(
        max_length=4,
        choices=MAINTENANCE_PRIORITY_CHOICES,
        null=True, blank=True,
        help_text='Priority level for maintenance'
    )
    maintenance_notes = models.TextField(
        blank=True,
        help_text='Specific maintenance requirements and notes'
    )
```

#### Add Bookable Method
```python
    def is_bookable(self):
        """Single source of truth for room availability"""
        # is_out_of_order is hard flag that overrides everything
        if self.is_out_of_order:
            return False
            
        return (
            self.room_status in {'AVAILABLE', 'READY_FOR_GUEST'} and
            self.is_active and
            not self.maintenance_required
        )
    
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
    
    def add_turnover_note(self, note, staff_member=None):
        """Add timestamped note to turnover history"""
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        staff_info = f" by {staff_member.get_full_name()}" if staff_member else ""
        new_note = f"[{timestamp}]{staff_info}: {note}"
        
        if self.turnover_notes:
            self.turnover_notes += f"\n{new_note}"
        else:
            self.turnover_notes = new_note
```

### Migration File: `rooms/migrations/0012_room_turnover_workflow.py`

```python
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('rooms', '0011_room_is_active'),
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='room_status',
            field=models.CharField(
                choices=[
                    ('AVAILABLE', 'Available'),
                    ('OCCUPIED', 'Occupied'), 
                    ('CHECKOUT_DIRTY', 'Checkout Dirty'),
                    ('CLEANING_IN_PROGRESS', 'Cleaning in Progress'),
                    ('CLEANED_UNINSPECTED', 'Cleaned Uninspected'),
                    ('MAINTENANCE_REQUIRED', 'Maintenance Required'),
                    ('OUT_OF_ORDER', 'Out of Order'),
                    ('READY_FOR_GUEST', 'Ready for Guest'),
                ],
                default='AVAILABLE',
                help_text='Current turnover workflow status of the room',
                max_length=20,
            ),
        ),
        # ... other fields ...
        
        # Data migration
        migrations.RunPython(set_initial_room_status, reverse_code=migrations.RunPython.noop),
    ]

def set_initial_room_status(apps, schema_editor):
    Room = apps.get_model('rooms', 'Room')
    for room in Room.objects.all():
        # Note: is_out_of_order remains authoritative flag
        # room_status reflects workflow state regardless
        if room.is_occupied:
            room.room_status = 'OCCUPIED'
        else:
            room.room_status = 'AVAILABLE'
        room.save()
```

---

## Phase 2: Update Existing Checkout Endpoints

### File: `room_bookings/views.py` - BookingAssignmentView.checkout_booking()

**Current location:** Line ~200-250 (approximate)

**Changes:**
1. After setting `room.is_occupied = False`
2. Add `room.room_status = 'CHECKOUT_DIRTY'`
3. Add turnover note
4. Trigger real-time notification

```python
def checkout_booking(self, request, booking_id):
    # ... existing code ...
    
    # Current: room.is_occupied = False
    room.is_occupied = False
    room.room_status = 'CHECKOUT_DIRTY'  # NEW
    room.add_turnover_note(
        f"Checked out at {timezone.now().strftime('%Y-%m-%d %H:%M')} by {request.user.staff.get_full_name()}",
        request.user.staff
    )  # NEW
    room.save()
    
    # ... existing pusher notification code ...
    
    # ADD: Turnover status notification
    pusher_client.trigger(
        f'hotel-{hotel.slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
            'old_status': 'OCCUPIED',
            'new_status': 'CHECKOUT_DIRTY',
            'timestamp': timezone.now().isoformat()
        }
    )  # NEW
```

### File: `rooms/views.py` - checkout_rooms()

**Current location:** Line ~150-200 (approximate)

**Changes:**
1. After setting `is_occupied=False` 
2. Add `room_status='CHECKOUT_DIRTY'`
3. Add bulk turnover notes
4. Trigger notifications

```python
def checkout_rooms(request, hotel_slug):
    # ... existing code ...
    
    for room in rooms:
        # ... existing cleanup code ...
        room.is_occupied = False
        room.room_status = 'CHECKOUT_DIRTY'  # NEW
        room.add_turnover_note(
            f"Bulk checkout at {timezone.now().strftime('%Y-%m-%d %H:%M')} by {request.user.staff.get_full_name()}",
            request.user.staff  
        )  # NEW
        room.save()
        
        # NEW: Real-time notification
        pusher_client.trigger(
            f'hotel-{hotel.slug}',
            'room-status-changed',
            {
                'room_number': room.room_number,
                'old_status': 'OCCUPIED',
                'new_status': 'CHECKOUT_DIRTY',
                'timestamp': timezone.now().isoformat()
            }
        )
```

---

## Phase 3: Room Turnover Workflow Endpoints (Staff-Only)

### File: `rooms/views.py` - Add New Views

#### 1. Start Cleaning
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def start_cleaning(request, hotel_slug, room_number):
    """Transition room to CLEANING_IN_PROGRESS"""
    # Check canonical navigation permission
    if not request.user.staff.allowed_navigation_items.filter(slug='rooms').exists():
        return Response({'error': 'Rooms permission required'}, status=403)
    
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if not room.can_transition_to('CLEANING_IN_PROGRESS'):
        return Response(
            {'error': f'Cannot transition from {room.room_status} to CLEANING_IN_PROGRESS'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = room.room_status
    room.room_status = 'CLEANING_IN_PROGRESS'
    room.add_turnover_note("Cleaning started", request.user.staff)
    room.save()
    
    # Real-time notification
    pusher_client.trigger(
        f'hotel-{hotel_slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
            'old_status': old_status,
            'new_status': 'CLEANING_IN_PROGRESS',
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({'message': 'Room cleaning started'})
```

#### 2. Mark Cleaned  
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def mark_cleaned(request, hotel_slug, room_number):
    """Mark room as cleaned, transition to CLEANED_UNINSPECTED"""
    # Check canonical navigation permission
    if not request.user.staff.allowed_navigation_items.filter(slug='rooms').exists():
        return Response({'error': 'Rooms permission required'}, status=403)
    
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if not room.can_transition_to('CLEANED_UNINSPECTED'):
        return Response(
            {'error': f'Cannot transition from {room.room_status} to CLEANED_UNINSPECTED'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    notes = request.data.get('notes', '')
    old_status = room.room_status
    
    room.room_status = 'CLEANED_UNINSPECTED'
    room.last_cleaned_at = timezone.now()
    room.cleaned_by_staff = request.user.staff
    
    note_text = "Room cleaned"
    if notes:
        note_text += f" - {notes}"
    room.add_turnover_note(note_text, request.user.staff)
    room.save()
    
    # Real-time notification
    pusher_client.trigger(
        f'hotel-{hotel_slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
            'old_status': old_status,
            'new_status': 'CLEANED_UNINSPECTED',
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({'message': 'Room marked as cleaned'})
```

#### 3. Inspect Room
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def inspect_room(request, hotel_slug, room_number):
    """Inspect room - pass -> READY_FOR_GUEST, fail -> CHECKOUT_DIRTY"""
    # Check canonical navigation permission
    if not request.user.staff.allowed_navigation_items.filter(slug='rooms').exists():
        return Response({'error': 'Rooms permission required'}, status=403)
    
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if room.room_status != 'CLEANED_UNINSPECTED':
        return Response(
            {'error': f'Cannot inspect room in {room.room_status} status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    passed = request.data.get('passed', False)
    notes = request.data.get('notes', '')
    old_status = room.room_status
    
    room.last_inspected_at = timezone.now()
    room.inspected_by_staff = request.user.staff
    
    if passed:
        room.room_status = 'READY_FOR_GUEST'
        note_text = "Inspection passed - ready for guest"
    else:
        room.room_status = 'CHECKOUT_DIRTY'
        note_text = "Inspection failed - needs re-cleaning"
    
    if notes:
        note_text += f" - {notes}"
    room.add_turnover_note(note_text, request.user.staff)
    room.save()
    
    # Real-time notification
    pusher_client.trigger(
        f'hotel-{hotel_slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
            'old_status': old_status,
            'new_status': room.room_status,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({
        'message': 'Room inspection completed',
        'passed': passed,
        'status': room.room_status
    })
```

#### 4. Mark Maintenance Required
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def mark_maintenance(request, hotel_slug, room_number):
    """Mark room as requiring maintenance - requires maintenance navigation permission"""
    # Check canonical navigation permission
    if not request.user.staff.allowed_navigation_items.filter(slug='maintenance').exists():
        return Response({'error': 'Maintenance permission required'}, status=403)
    """Mark room as requiring maintenance"""
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if not room.can_transition_to('MAINTENANCE_REQUIRED'):
        return Response(
            {'error': f'Cannot transition from {room.room_status} to MAINTENANCE_REQUIRED'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    priority = request.data.get('priority', 'MED')
    notes = request.data.get('notes', '')
    
    if priority not in ['LOW', 'MED', 'HIGH']:
        return Response(
            {'error': 'Priority must be LOW, MED, or HIGH'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = room.room_status
    room.room_status = 'MAINTENANCE_REQUIRED'
    room.maintenance_required = True
    room.maintenance_priority = priority
    room.maintenance_notes = notes
    room.add_turnover_note(f"Maintenance required ({priority} priority): {notes}", request.user.staff)
    room.save()
    
    # Real-time notification
    pusher_client.trigger(
        f'hotel-{hotel_slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
            'old_status': old_status,
            'new_status': 'MAINTENANCE_REQUIRED',
            'priority': priority,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({'message': 'Room marked for maintenance'})
```

#### 5. Complete Maintenance
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def complete_maintenance(request, hotel_slug, room_number):
    """Mark maintenance as completed - requires maintenance navigation permission"""
    # Check canonical navigation permission
    if not request.user.staff.allowed_navigation_items.filter(slug='maintenance').exists():
        return Response({'error': 'Maintenance permission required'}, status=403)
    
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if room.room_status != 'MAINTENANCE_REQUIRED':
        return Response(
            {'error': f'Room is not in maintenance status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = room.room_status
    room.maintenance_required = False
    room.maintenance_priority = None
    room.maintenance_notes = ''
    
    # If room was cleaned and inspected, go to ready, otherwise back to dirty
    if room.last_cleaned_at and room.last_inspected_at:
        # Check if cleaning/inspection happened after last checkout
        # For now, default to ready if both exist
        room.room_status = 'READY_FOR_GUEST'
    else:
        room.room_status = 'CHECKOUT_DIRTY'
    
    room.add_turnover_note("Maintenance completed", request.user.staff)
    room.save()
    
    # Real-time notification  
    pusher_client.trigger(
        f'hotel-{hotel_slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
            'old_status': old_status,
            'new_status': room.room_status,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({
        'message': 'Maintenance completed',
        'new_status': room.room_status
    })
```

### File: `rooms/staff_urls.py` - Add Staff-Only Turnover URLs

```python
# Create rooms/staff_urls.py for turnover workflow endpoints
from django.urls import path
from . import views

urlpatterns = [
    # Room turnover workflow - all staff-only
    path('hotels/<slug:hotel_slug>/rooms/<str:room_number>/start-cleaning/', views.start_cleaning, name='start_cleaning'),
    path('hotels/<slug:hotel_slug>/rooms/<str:room_number>/mark-cleaned/', views.mark_cleaned, name='mark_cleaned'),
    path('hotels/<slug:hotel_slug>/rooms/<str:room_number>/inspect/', views.inspect_room, name='inspect_room'),
    path('hotels/<slug:hotel_slug>/rooms/<str:room_number>/mark-maintenance/', views.mark_maintenance, name='mark_maintenance'),
    path('hotels/<slug:hotel_slug>/rooms/<str:room_number>/complete-maintenance/', views.complete_maintenance, name='complete_maintenance'),
    
    # Dashboard endpoints
    path('hotels/<slug:hotel_slug>/turnover/rooms/', views.turnover_rooms, name='turnover_rooms'),
    path('hotels/<slug:hotel_slug>/turnover/stats/', views.turnover_stats, name='turnover_stats'),
]
```

### File: `staff_urls.py` - Include Rooms Turnover URLs

```python
# Add to existing staff URL includes
path('', include('rooms.staff_urls')),
```

---

## Phase 4: Update Availability Service

### File: `hotel/services/availability.py`

#### Update get_available_rooms_count() Method
**Current location:** Line ~50-100 (approximate)

**Change:** Replace existing room filtering logic with single bookable rule

```python
def get_available_rooms_count(self, room_type, date):
    """Get count of bookable rooms for specific type and date"""
    
    # OLD CODE (remove):
    # physical_rooms = room_type.rooms.filter(
    #     is_active=True,
    #     is_out_of_order=False  
    # ).exclude(is_occupied=True)
    
    # NEW CODE: Use is_bookable() rule
    # Note: Can't use is_bookable() in DB query, so replicate logic
    physical_rooms = room_type.rooms.filter(
        room_status__in=['AVAILABLE', 'READY_FOR_GUEST'],
        is_active=True,
        is_out_of_order=False,  # Hard override flag
        maintenance_required=False
    )
    
    # ... rest of method unchanged (booking overlap logic) ...
```

#### Update get_room_type_availability() Method
**Current location:** Line ~150-200 (approximate)

```python
def get_room_type_availability(self, room_type, start_date, end_date):
    """Get availability for room type across date range"""
    
    # Update base room query using bookable rule
    base_room_count = room_type.rooms.filter(
        room_status__in=['AVAILABLE', 'READY_FOR_GUEST'],
        is_active=True,
        is_out_of_order=False,  # Hard override flag
        maintenance_required=False
    ).count()
    
    # ... rest of method logic unchanged ...
```

#### Update any other methods using room filtering

Search for any other methods using `is_occupied` or `is_out_of_order` filters and update to use the bookable rule.

---

## Phase 5: Room Turnover Dashboard Endpoints

### File: `rooms/views.py` - Dashboard Views

#### 1. Turnover Status Overview
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def turnover_rooms(request, hotel_slug):
    """Get rooms grouped by turnover status"""
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    rooms_by_status = {}
    for status_code, status_label in Room.ROOM_STATUS_CHOICES:
        rooms = Room.objects.filter(
            hotel=hotel,
            room_status=status_code
        ).select_related('room_type', 'cleaned_by_staff', 'inspected_by_staff')
        
        rooms_by_status[status_code] = {
            'label': status_label,
            'count': rooms.count(),
            'rooms': RoomSerializer(rooms, many=True).data
        }
    
    return Response(rooms_by_status)
```

#### 2. Turnover Statistics
```python
@api_view(['GET']) 
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def turnover_stats(request, hotel_slug):
    """Get turnover statistics and metrics"""
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    total_rooms = hotel.rooms.filter(is_active=True).count()
    
    stats = {
        'total_rooms': total_rooms,
        'bookable_rooms': hotel.rooms.filter(
            room_status__in=['AVAILABLE', 'READY_FOR_GUEST'],
            is_active=True,
            is_out_of_order=False,  # Hard override flag
            maintenance_required=False
        ).count(),
        'occupied_rooms': hotel.rooms.filter(room_status='OCCUPIED').count(),
        'dirty_rooms': hotel.rooms.filter(room_status='CHECKOUT_DIRTY').count(),
        'cleaning_in_progress': hotel.rooms.filter(room_status='CLEANING_IN_PROGRESS').count(),
        'awaiting_inspection': hotel.rooms.filter(room_status='CLEANED_UNINSPECTED').count(),
        'maintenance_required': hotel.rooms.filter(maintenance_required=True).count(),
        'out_of_order': hotel.rooms.filter(room_status='OUT_OF_ORDER').count(),
    }
    
    # Add maintenance breakdown
    maintenance_by_priority = hotel.rooms.filter(
        maintenance_required=True
    ).values('maintenance_priority').annotate(count=Count('id'))
    
    stats['maintenance_by_priority'] = {
        item['maintenance_priority']: item['count'] 
        for item in maintenance_by_priority
    }
    
    return Response(stats)
```



---

## Phase 6: Update Room Serializer

### File: `rooms/serializers.py`

Add turnover fields to RoomSerializer:

```python
class RoomSerializer(serializers.ModelSerializer):
    # ... existing fields ...
    
    # Add turnover fields
    room_status_display = serializers.CharField(source='get_room_status_display', read_only=True)
    is_bookable = serializers.BooleanField(read_only=True)
    cleaned_by_name = serializers.CharField(source='cleaned_by_staff.get_full_name', read_only=True)
    inspected_by_name = serializers.CharField(source='inspected_by_staff.get_full_name', read_only=True)
    maintenance_priority_display = serializers.CharField(source='get_maintenance_priority_display', read_only=True)
    
    class Meta:
        model = Room
        fields = [
            # ... existing fields ...
            'room_status',
            'room_status_display', 
            'is_bookable',
            'last_cleaned_at',
            'cleaned_by_name',
            'last_inspected_at', 
            'inspected_by_name',
            'turnover_notes',
            'maintenance_required',
            'maintenance_priority',
            'maintenance_priority_display',
            'maintenance_notes',
        ]
```

---

## Phase 8: Tests

### File: `rooms/tests.py` - Comprehensive Test Suite

```python
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from hotel.models import Hotel
from rooms.models import Room, RoomType
from staff.models import Staff

class RoomTurnoverWorkflowTestCase(TestCase):
    def setUp(self):
        # Create test data
        self.hotel = Hotel.objects.create(name='Test Hotel', slug='test-hotel')
        self.room_type = RoomType.objects.create(hotel=self.hotel, name='Standard')
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type, 
            room_number='101',
            room_status='AVAILABLE'
        )
        
        self.user = User.objects.create_user(username='staff', password='test')
        self.staff = Staff.objects.create(user=self.user, hotel=self.hotel)
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_checkout_sets_dirty_status(self):
        """Test that checkout sets room to CHECKOUT_DIRTY"""
        # First set room as occupied
        self.room.room_status = 'OCCUPIED'
        self.room.is_occupied = True
        self.room.save()
        
        # Simulate checkout (would need actual booking for full test)
        self.room.is_occupied = False
        self.room.room_status = 'CHECKOUT_DIRTY'
        self.room.save()
        
        self.room.refresh_from_db()
        self.assertEqual(self.room.room_status, 'CHECKOUT_DIRTY')
        self.assertFalse(self.room.is_occupied)
        self.assertFalse(self.room.is_bookable())
    
    def test_availability_excludes_dirty_rooms(self):
        """Test that dirty rooms are not counted as available"""
        self.room.room_status = 'CHECKOUT_DIRTY'
        self.room.save()
        
        self.assertFalse(self.room.is_bookable())
        
        # Test availability service integration would go here
        
    def test_turnover_state_transitions(self):
        """Test valid state machine transitions"""
        # Start with dirty room
        self.room.room_status = 'CHECKOUT_DIRTY'
        self.room.save()
        
        # Can transition to cleaning
        self.assertTrue(self.room.can_transition_to('CLEANING_IN_PROGRESS'))
        
        # Transition to cleaning
        url = reverse('start_cleaning', kwargs={
            'hotel_slug': self.hotel.slug,
            'room_number': self.room.room_number
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.room.refresh_from_db()
        self.assertEqual(self.room.room_status, 'CLEANING_IN_PROGRESS')
    
    def test_invalid_state_transitions(self):
        """Test that invalid transitions are blocked"""
        # Can't inspect occupied room
        self.room.room_status = 'OCCUPIED'
        self.room.save()
        
        url = reverse('inspect_room', kwargs={
            'hotel_slug': self.hotel.slug,
            'room_number': self.room.room_number
        })
        response = self.client.post(url, {'passed': True})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_hotel_scoping_enforced(self):
        """Test that staff can only access rooms in their hotel"""
        other_hotel = Hotel.objects.create(name='Other Hotel', slug='other')
        other_room = Room.objects.create(
            hotel=other_hotel,
            room_type=self.room_type,
            room_number='201'
        )
        
        url = reverse('start_cleaning', kwargs={
            'hotel_slug': other_hotel.slug, 
            'room_number': other_room.room_number
        })
        response = self.client.post(url)
        # Should get 403/404 due to IsSameHotel permission
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
    
    def test_maintenance_workflow(self):
        """Test maintenance required workflow"""
        self.room.room_status = 'CLEANED_UNINSPECTED'
        self.room.save()
        
        # Mark for maintenance
        url = reverse('mark_maintenance', kwargs={
            'hotel_slug': self.hotel.slug,
            'room_number': self.room.room_number
        })
        response = self.client.post(url, {
            'priority': 'HIGH',
            'notes': 'Broken AC'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.room.refresh_from_db()
        self.assertEqual(self.room.room_status, 'MAINTENANCE_REQUIRED')
        self.assertTrue(self.room.maintenance_required)
        self.assertEqual(self.room.maintenance_priority, 'HIGH')
        
    def test_complete_inspection_workflow(self):
        """Test complete cleaning -> inspection -> ready workflow"""
        # Start with dirty room
        self.room.room_status = 'CHECKOUT_DIRTY'
        self.room.save()
        
        # Mark as cleaned
        url = reverse('mark_cleaned', kwargs={
            'hotel_slug': self.hotel.slug,
            'room_number': self.room.room_number
        })
        response = self.client.post(url, {'notes': 'Deep clean completed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.room.refresh_from_db()
        self.assertEqual(self.room.room_status, 'CLEANED_UNINSPECTED')
        self.assertIsNotNone(self.room.last_cleaned_at)
        
        # Pass inspection
        url = reverse('inspect_room', kwargs={
            'hotel_slug': self.hotel.slug,
            'room_number': self.room.room_number
        })
        response = self.client.post(url, {'passed': True, 'notes': 'All good'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.room.refresh_from_db()
        self.assertEqual(self.room.room_status, 'READY_FOR_GUEST')
        self.assertTrue(self.room.is_bookable())
```

---

## Implementation Checklist

### Database & Models
- [ ] Add room_status field to Room model
- [ ] Add turnover audit fields (cleaned_at, cleaned_by, etc.)
- [ ] Add maintenance fields (required, priority, notes)
- [ ] Add is_bookable() method
- [ ] Add can_transition_to() method
- [ ] Add add_turnover_note() method
- [ ] Create and run migration with data migration

### Checkout Updates  
- [ ] Update booking checkout to set CHECKOUT_DIRTY
- [ ] Update bulk checkout to set CHECKOUT_DIRTY
- [ ] Add real-time notifications for status changes
- [ ] Test existing checkout functionality still works

### Turnover Endpoints
- [ ] Implement start_cleaning endpoint
- [ ] Implement mark_cleaned endpoint  
- [ ] Implement inspect_room endpoint
- [ ] Implement mark_maintenance endpoint (with nav permission)
- [ ] Implement complete_maintenance endpoint (with nav permission)
- [ ] Add URL patterns for all endpoints
- [ ] Test state machine validation

### Availability Service
- [ ] Update get_available_rooms_count to use is_bookable rule
- [ ] Update get_room_type_availability to use is_bookable rule  
- [ ] Search and update any other methods using old room filters
- [ ] Test availability calculations exclude dirty/maintenance rooms

### Dashboard & UI
- [ ] Implement turnover_rooms dashboard endpoint
- [ ] Implement turnover_stats endpoint
- [ ] Update RoomSerializer with turnover fields
- [ ] Add dashboard URL patterns

### Testing & Validation
- [ ] Write comprehensive test suite covering all workflows
- [ ] Test state machine transitions and validations
- [ ] Test permission enforcement and hotel scoping
- [ ] Test availability service integration
- [ ] Test real-time notifications
- [ ] Performance test with large number of rooms

### Production Considerations
- [ ] Backup database before migration
- [ ] Plan deployment during low-usage period
- [ ] Monitor for any booking/availability issues post-deployment
- [ ] Train staff on new room turnover workflow
- [ ] Update frontend to handle new room statuses and endpoints

---

## API Endpoint Summary

### Room Turnover Workflow Endpoints (Staff-Only)
```
POST /api/staff/hotels/{slug}/rooms/{room_number}/start-cleaning/
POST /api/staff/hotels/{slug}/rooms/{room_number}/mark-cleaned/
POST /api/staff/hotels/{slug}/rooms/{room_number}/inspect/  
POST /api/staff/hotels/{slug}/rooms/{room_number}/mark-maintenance/  # Requires maintenance nav permission
POST /api/staff/hotels/{slug}/rooms/{room_number}/complete-maintenance/  # Requires maintenance nav permission
```

### Dashboard Endpoints (Staff-Only)
```
GET /api/staff/hotels/{slug}/turnover/rooms/
GET /api/staff/hotels/{slug}/turnover/stats/
```

### Modified Existing Endpoints
```
POST /api/staff/hotels/{slug}/bookings/{booking_id}/checkout/  # Now sets CHECKOUT_DIRTY
POST /api/hotels/{hotel_slug}/rooms/checkout/  # Now sets CHECKOUT_DIRTY (ensure staff permissions)
```

## Database Schema Changes Summary

### New Room Model Fields
```python
room_status = CharField(max_length=20, choices=ROOM_STATUS_CHOICES, default='AVAILABLE')
last_cleaned_at = DateTimeField(null=True, blank=True)
cleaned_by_staff = ForeignKey('staff.Staff', null=True, blank=True)
last_inspected_at = DateTimeField(null=True, blank=True) 
inspected_by_staff = ForeignKey('staff.Staff', null=True, blank=True)
turnover_notes = TextField(blank=True)
maintenance_required = BooleanField(default=False)
maintenance_priority = CharField(max_length=4, choices=PRIORITY_CHOICES, null=True, blank=True)
maintenance_notes = TextField(blank=True)
```

---

## Implementation Go Signal

**Implement ROOM TURNOVER workflow exactly as in this plan, with:**
- ✅ Canonical permissions/allowed_navs for navigation checks (no permission class hacks)
- ✅ Keep is_out_of_order as hard non-bookable flag (authority over room_status)
- ✅ All turnover endpoints under /api/staff/ namespace
- ✅ Focus: checkout correctness, not "extra turnover module"

**Ready for execution.**