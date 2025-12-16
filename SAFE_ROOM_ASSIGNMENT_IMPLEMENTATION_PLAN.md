# Hotel-Scoped Safe Room Assignment System Implementation Plan

**Status**: Ready for Implementation  
**Date**: December 16, 2025  
**Goal**: Implement atomic, turnover-safe, overlap-preventing room assignment system

## Overview

This implementation creates a comprehensive room assignment system that:
- **Prevents double-booking** via date overlap enforcement and inventory blocking
- **Respects room turnover workflows** using `Room.is_bookable()` as single source of truth
- **Provides atomic safety** under concurrent operations with row-level locking
- **Enforces hotel scoping** with no cross-hotel data leakage
- **Maintains audit history** for all assignment operations

## Phase 0: Define Canonical Rules

### File: `room_bookings/constants.py` (NEW)
```python
# Single source of truth for room assignment business rules

# Booking statuses that can block room inventory (combine with timestamp checks)
# Only include PENDING_PAYMENT if business reserves inventory before payment
INVENTORY_BLOCKING_STATUSES = ["CONFIRMED"]  # CHECKED_IN status doesn't exist - use checked_in_at timestamp

# Booking statuses allowed for room assignment
ASSIGNABLE_BOOKING_STATUSES = ["CONFIRMED"]

# Non-blocking statuses (never block inventory)
NON_BLOCKING_STATUSES = ["CANCELLED", "COMPLETED", "NO_SHOW"]

# Room assignment operation types for audit logging
ASSIGNMENT_OPERATIONS = {
    'ASSIGNED': 'assigned',
    'REASSIGNED': 'reassigned', 
    'UNASSIGNED': 'unassigned'
}
```

### Integration Points
- Import in `room_bookings/models.py`, `services/`, `views.py`
- Use `Room.is_bookable()` everywhere (already implemented)
- Centralize date overlap logic to prevent inconsistencies

---

## Phase 1: Assignment Audit Fields Migration

### File: `room_bookings/models.py` - RoomBooking Model Extension
```python
class RoomBooking(models.Model):
    # ... existing fields ...
    
    # Room Assignment Audit Fields (ADD THESE)
    room_assigned_at = models.DateTimeField(null=True, blank=True)
    room_assigned_by = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='room_assignments'
    )
    assignment_notes = models.TextField(blank=True)
    
    # Optional: Track reassignments and unassignments separately
    room_reassigned_at = models.DateTimeField(null=True, blank=True)
    room_reassigned_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True, 
        related_name='room_reassignments'
    )
    
    # Better: Separate unassignment audit (don't reuse reassignment fields)
    room_unassigned_at = models.DateTimeField(null=True, blank=True)
    room_unassigned_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='room_unassignments'
    )
    
    # Optional: Version field for debugging concurrent access
    assignment_version = models.PositiveIntegerField(default=0)
```

### Migration Commands
```bash
python manage.py makemigrations room_bookings --name add_room_assignment_audit
python manage.py migrate
```

---

## Phase 1.5: Migration Safety Rules (MANDATORY)

### Critical Migration Hygiene to Prevent Crashes

**Problem**: Django `RunPython` functions must be defined **before** the `Migration` class, not after. Otherwise Python throws `NameError: name 'function_name' is not defined`.

#### ✅ REQUIRED Migration Pattern:
```python
# migrations/XXXX_your_migration.py
from django.db import migrations, models

# 1. ALWAYS define RunPython functions ABOVE Migration class
def your_data_migration_function(apps, schema_editor):
    """Your data migration logic"""
    Model = apps.get_model('app_name', 'ModelName')  # Use apps.get_model()
    for obj in Model.objects.all():
        # Your logic here
        obj.save(update_fields=['field_name'])  # Use update_fields for performance

def reverse_function(apps, schema_editor):
    """Optional reverse logic"""
    pass

# 2. Migration class comes AFTER function definitions
class Migration(migrations.Migration):
    dependencies = [
        ('your_app', '0013_previous_migration'),
    ]
    
    operations = [
        # 3. AddField operations BEFORE data migrations
        migrations.AddField(model_name='model', name='field', field=models.CharField(...)),
        
        # 4. Data migration AFTER schema changes
        migrations.RunPython(your_data_migration_function, reverse_code=reverse_function),
    ]
```

#### 🚨 Migration Safety Checklist:
- [ ] Functions defined **above** `Migration` class
- [ ] Use `apps.get_model()` (never import live models)
- [ ] Use `update_fields=[...]` for performance
- [ ] Put data migrations **after** `AddField` operations
- [ ] Always test migration sequence

#### Verification Commands (run after each migration):
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations app_name
python manage.py check
```

---

## Phase 2: Reusable Room Assignment Service Layer

### File: `room_bookings/services/__init__.py` (NEW)
```python
# Make services importable
from .room_assignment import *
```

### File: `room_bookings/services/room_assignment.py` (NEW)

#### Core Service Functions

```python
from django.db import transaction, models
from django.utils import timezone
from room_bookings.constants import INVENTORY_BLOCKING_STATUSES, ASSIGNABLE_BOOKING_STATUSES, NON_BLOCKING_STATUSES
from room_bookings.exceptions import RoomAssignmentError

class RoomAssignmentService:
    
    @staticmethod
    def find_available_rooms_for_booking(booking):
        """
        Returns rooms available for assignment to this booking.
        
        Filters:
        - Same hotel as booking
        - Matching room_type 
        - Room.is_bookable() == True
        - No overlap conflicts with INVENTORY_BLOCKING_STATUSES bookings
        
        Returns: QuerySet of Room objects sorted by room_number
        """
        from rooms.models import Room
        from room_bookings.models import RoomBooking
        
        # Get conflicting room IDs (rooms with overlapping bookings)
        # Blocks inventory if: status='CONFIRMED' AND checked_out_at IS NULL
        # OR checked_in_at IS NOT NULL AND checked_out_at IS NULL (in-house guest)
        conflicting_rooms = RoomBooking.objects.filter(
            assigned_room__isnull=False,
            # Use timestamp-based blocking logic (matches actual model schema)
            models.Q(
                status__in=INVENTORY_BLOCKING_STATUSES,  # CONFIRMED
                checked_out_at__isnull=True  # Not checked out
            ) | models.Q(
                checked_in_at__isnull=False,  # Checked in
                checked_out_at__isnull=True   # Not checked out
            ),
            # Overlap logic: (existing.check_in < booking.check_out) AND (existing.check_out > booking.check_in)
            check_in__lt=booking.check_out,
            check_out__gt=booking.check_in
        ).exclude(
            status__in=NON_BLOCKING_STATUSES  # Exclude cancelled/completed/no-show
        ).exclude(
            id=booking.id  # Don't conflict with self
        ).values_list('assigned_room_id', flat=True)
        
        return Room.objects.filter(
            hotel=booking.hotel,
            room_type=booking.room_type,
            # Replicate Room.is_bookable() logic as DB-filterable conditions
            room_status__in=['AVAILABLE', 'READY_FOR_GUEST'],
            is_active=True,
            is_out_of_order=False,
            maintenance_required=False
        ).exclude(
            id__in=conflicting_rooms
        ).order_by('room_number')
    
    @staticmethod 
    def assert_room_can_be_assigned(booking, room):
        """
        Validates that room can be safely assigned to booking.
        Raises RoomAssignmentError with structured error codes.
        """
        # Hotel scope validation
        if booking.hotel != room.hotel:
            raise RoomAssignmentError(
                code='HOTEL_MISMATCH',
                message=f'Room {room.room_number} belongs to different hotel'
            )
            
        # Defensive check: RoomType should be hotel-scoped
        if booking.room_type.hotel != booking.hotel:
            raise RoomAssignmentError(
                code='ROOM_TYPE_HOTEL_MISMATCH',
                message=f'Booking room type belongs to different hotel'
            )
        
        # Booking status validation
        if booking.status not in ASSIGNABLE_BOOKING_STATUSES:
            raise RoomAssignmentError(
                code='BOOKING_STATUS_NOT_ASSIGNABLE',
                message=f'Booking status {booking.status} is not assignable'
            )
            
        # Check-in status validation (use timestamp-based "in-house" concept)
        # In-house means: checked_in_at is not None AND checked_out_at is None
        if booking.checked_in_at is not None and booking.checked_out_at is None:
            raise RoomAssignmentError(
                code='BOOKING_ALREADY_CHECKED_IN',
                message='Cannot assign room to in-house guest (already checked in)'
            )
            
        # Room type validation
        if room.room_type != booking.room_type:
            raise RoomAssignmentError(
                code='ROOM_TYPE_MISMATCH', 
                message=f'Room type {room.room_type} does not match booking type {booking.room_type}'
            )
            
        # Room bookability validation
        if not room.is_bookable():
            raise RoomAssignmentError(
                code='ROOM_NOT_BOOKABLE',
                message=f'Room {room.room_number} is not bookable (status: {room.room_status})'
            )
            
        # Overlap conflict validation (using timestamp-based blocking)
        from room_bookings.models import RoomBooking
        conflicting_bookings = RoomBooking.objects.filter(
            assigned_room=room,
            # Same timestamp-based blocking logic as find_available_rooms
            models.Q(
                status__in=INVENTORY_BLOCKING_STATUSES,  # CONFIRMED
                checked_out_at__isnull=True  # Not checked out
            ) | models.Q(
                checked_in_at__isnull=False,  # Checked in
                checked_out_at__isnull=True   # Not checked out
            ),
            check_in__lt=booking.check_out,
            check_out__gt=booking.check_in
        ).exclude(
            status__in=NON_BLOCKING_STATUSES  # Exclude cancelled/completed/no-show
        ).exclude(id=booking.id)
        
        if conflicting_bookings.exists():
            raise RoomAssignmentError(
                code='ROOM_OVERLAP_CONFLICT',
                message=f'Room {room.room_number} has overlapping bookings',
                details={'conflicting_booking_ids': list(conflicting_bookings.values_list('id', flat=True))}
            )
    
    @classmethod
    @transaction.atomic
    def assign_room_atomic(cls, booking_id, room_id, staff_user, notes=None):
        """
        Atomically assign room to booking with full validation and audit logging.
        
        Returns: Updated RoomBooking instance
        Raises: RoomAssignmentError for validation failures
        """
        from room_bookings.models import RoomBooking
        from rooms.models import Room
        
        # Lock booking and room for update to prevent concurrent modifications
        booking = RoomBooking.objects.select_for_update().get(id=booking_id)
        room = Room.objects.select_for_update().get(id=room_id)
        
        # CRITICAL: Also lock potentially conflicting bookings to prevent race conditions
        # This ensures two concurrent assignments serialize on the conflict check
        potentially_conflicting = RoomBooking.objects.select_for_update().filter(
            assigned_room=room,
            models.Q(
                status__in=INVENTORY_BLOCKING_STATUSES,
                checked_out_at__isnull=True
            ) | models.Q(
                checked_in_at__isnull=False,
                checked_out_at__isnull=True
            ),
            check_in__lt=booking.check_out,
            check_out__gt=booking.check_in
        ).exclude(
            status__in=NON_BLOCKING_STATUSES
        ).exclude(id=booking.id)
        
        # Force evaluation of the locking query
        list(potentially_conflicting)
        
        # Re-run all validations inside transaction (critical for concurrent safety)
        cls.assert_room_can_be_assigned(booking, room)
        
        # Idempotent check: if already assigned to same room, return existing
        if booking.assigned_room_id == room_id:
            return booking
            
        # Handle reassignment (allowed only before check-in)
        if booking.assigned_room_id and booking.assigned_room_id != room_id:
            # Use proper in-house check: checked_in_at exists AND not checked_out_at
            if booking.checked_in_at and not booking.checked_out_at:
                raise RoomAssignmentError(
                    code='BOOKING_ALREADY_CHECKED_IN',
                    message='Cannot reassign room for in-house guest'
                )
            
            # Log reassignment audit
            booking.room_reassigned_at = timezone.now()
            booking.room_reassigned_by = staff_user
            booking.assignment_version += 1
        
        # Perform assignment
        booking.assigned_room = room
        booking.room_assigned_at = timezone.now()
        booking.room_assigned_by = staff_user
        booking.assignment_notes = notes or ''
        booking.assignment_version += 1
        booking.save()
        
        return booking
```

### File: `room_bookings/exceptions.py` (NEW)
```python
class RoomAssignmentError(Exception):
    """Structured exception for room assignment validation failures"""
    
    def __init__(self, code, message, details=None):
        self.code = code
        self.message = message 
        self.details = details or {}
        super().__init__(self.message)
```

---

## Phase 3: Staff API Endpoints

### File: `room_bookings/urls.py` - Add New URL Patterns
```python
# Add to staff_urlpatterns
path('hotels/<slug:hotel_slug>/bookings/<int:booking_id>/available-rooms/', 
     views.AvailableRoomsView.as_view(), name='available-rooms'),
path('hotels/<slug:hotel_slug>/bookings/<int:booking_id>/assign-room/',
     views.AssignRoomView.as_view(), name='assign-room'),
path('hotels/<slug:hotel_slug>/bookings/<int:booking_id>/unassign-room/',
     views.UnassignRoomView.as_view(), name='unassign-room'),
path('hotels/<slug:hotel_slug>/bookings/',
     views.StaffBookingListView.as_view(), name='staff-bookings-list'),
```

### File: `room_bookings/views.py` - New API Views

#### Available Rooms Endpoint
```python
class AvailableRoomsView(APIView):
    """GET /api/staff/hotels/{hotel_slug}/bookings/{booking_id}/available-rooms/"""
    
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get(self, request, hotel_slug, booking_id):
        booking = get_object_or_404(RoomBooking, id=booking_id, hotel__slug=hotel_slug)
        
        available_rooms = RoomAssignmentService.find_available_rooms_for_booking(booking)
        
        data = [{
            'id': room.id,
            'room_number': room.room_number,
            # floor field doesn't exist in Room model - removed
            'room_type': room.room_type.name,
            'room_status': room.room_status,
            'is_bookable': room.is_bookable()  # Method call OK in Python serialization
        } for room in available_rooms]
        
        return Response({'available_rooms': data})
```

#### Assign Room Endpoint  
```python
class AssignRoomView(APIView):
    """POST /api/staff/hotels/{hotel_slug}/bookings/{booking_id}/assign-room/"""
    
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def post(self, request, hotel_slug, booking_id):
        room_id = request.data.get('room_id')
        notes = request.data.get('notes', '')
        
        if not room_id:
            return Response(
                {'error': {'code': 'MISSING_ROOM_ID', 'message': 'room_id is required'}},
                status=400
            )
        
        try:
            booking = RoomAssignmentService.assign_room_atomic(
                booking_id=booking_id,
                room_id=room_id,
                staff_user=request.user.staff_profile,
                notes=notes
            )
            
            # Return updated booking with assigned room details
            serializer = RoomBookingDetailSerializer(booking)
            return Response(serializer.data)
            
        except RoomBooking.DoesNotExist:
            return Response(
                {'error': {'code': 'BOOKING_NOT_FOUND', 'message': 'Booking not found'}},
                status=404
            )
        except Room.DoesNotExist:
            return Response(
                {'error': {'code': 'ROOM_NOT_FOUND', 'message': 'Room not found'}},
                status=404
            )
        except RoomAssignmentError as e:
            status_code = 409 if e.code in ['ROOM_OVERLAP_CONFLICT', 'BOOKING_ALREADY_CHECKED_IN'] else 400
            return Response(
                {'error': {'code': e.code, 'message': e.message, 'details': e.details}},
                status=status_code
            )
```

#### Unassign Room Endpoint (Optional)
```python
class UnassignRoomView(APIView):
    """POST /api/staff/hotels/{hotel_slug}/bookings/{booking_id}/unassign-room/"""
    
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    @transaction.atomic
    def post(self, request, hotel_slug, booking_id):
        booking = get_object_or_404(
            RoomBooking.objects.select_for_update(),
            id=booking_id, 
            hotel__slug=hotel_slug
        )
        
        # Use proper in-house check: checked_in_at exists AND not checked_out_at  
        if booking.checked_in_at and not booking.checked_out_at:
            return Response(
                {'error': {'code': 'BOOKING_ALREADY_CHECKED_IN', 'message': 'Cannot unassign room for in-house guest'}},
                status=409
            )
        
        if not booking.assigned_room:
            return Response(
                {'error': {'code': 'NO_ROOM_ASSIGNED', 'message': 'No room currently assigned'}},
                status=400
            )
        
        # Audit log unassignment (use proper fields, not text concatenation)
        booking.assigned_room = None
        booking.room_unassigned_at = timezone.now()
        booking.room_unassigned_by = request.user.staff_profile
        if booking.assignment_notes:
            booking.assignment_notes += f"\n[UNASSIGNED: {timezone.now()} by {request.user.staff_profile}]"
        else:
            booking.assignment_notes = f"[UNASSIGNED: {timezone.now()} by {request.user.staff_profile}]"
        booking.save()
        
        return Response({'message': 'Room unassigned successfully'})
```

#### Enhanced Staff Bookings List
```python
class StaffBookingListView(APIView):
    """GET /api/staff/hotels/{hotel_slug}/bookings/"""
    
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel] 
    
    def get(self, request, hotel_slug):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        queryset = RoomBooking.objects.filter(hotel=hotel).select_related(
            'assigned_room', 'room_type', 'room_assigned_by'
        )
        
        # Query parameter filters
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        status = request.query_params.get('status')
        assigned = request.query_params.get('assigned')  # true/false
        arriving = request.query_params.get('arriving')  # today
        room_type = request.query_params.get('room_type')
        
        if from_date:
            queryset = queryset.filter(check_in__gte=from_date)
        if to_date:
            queryset = queryset.filter(check_out__lte=to_date)
        if status:
            queryset = queryset.filter(status=status)
        if assigned == 'true':
            queryset = queryset.filter(assigned_room__isnull=False)
        elif assigned == 'false':
            queryset = queryset.filter(assigned_room__isnull=True)
        if arriving == 'today':
            today = timezone.now().date()
            queryset = queryset.filter(check_in=today)
        if room_type:
            # Use room_type code instead of name (names can collide across hotels)
            queryset = queryset.filter(room_type__code=room_type)
            
        # Paginate and serialize
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = RoomBookingListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
```

---

## Phase 4: Structured Error Handling

### File: `room_bookings/serializers.py` - Error Response Serializers
```python
class ErrorResponseSerializer(serializers.Serializer):
    """Standardized error response format"""
    code = serializers.CharField()
    message = serializers.CharField() 
    details = serializers.DictField(required=False)

class RoomAssignmentErrorCodes:
    """Documentation of all possible error codes"""
    
    # 400 Bad Request
    ROOM_TYPE_MISMATCH = 'ROOM_TYPE_MISMATCH'
    ROOM_TYPE_HOTEL_MISMATCH = 'ROOM_TYPE_HOTEL_MISMATCH'  # Defensive validation
    ROOM_NOT_BOOKABLE = 'ROOM_NOT_BOOKABLE'
    MISSING_ROOM_ID = 'MISSING_ROOM_ID'
    
    # 404 Not Found  
    BOOKING_NOT_FOUND = 'BOOKING_NOT_FOUND'
    ROOM_NOT_FOUND = 'ROOM_NOT_FOUND'
    
    # 409 Conflict
    ROOM_OVERLAP_CONFLICT = 'ROOM_OVERLAP_CONFLICT'
    BOOKING_ALREADY_CHECKED_IN = 'BOOKING_ALREADY_CHECKED_IN'
    BOOKING_STATUS_NOT_ASSIGNABLE = 'BOOKING_STATUS_NOT_ASSIGNABLE'
    
    # 403 Forbidden (handled by permissions)
    HOTEL_SCOPE_VIOLATION = 'HOTEL_SCOPE_VIOLATION'
    INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS'
```

---

## Phase 4.5: Performance Optimization (Recommended)

### Database Indexes for Overlap Queries

The hot query path for room assignment involves checking overlapping bookings:
```sql
-- High-frequency query pattern
SELECT * FROM room_bookings 
WHERE assigned_room_id = ? 
  AND status IN ('CONFIRMED') 
  AND checked_out_at IS NULL
  AND check_in < ? AND check_out > ?
```

#### Recommended Composite Index:
```python
# Add to RoomBooking model Meta class
class Meta:
    indexes = [
        # Existing indexes...
        
        # Optimized for overlap conflict detection
        models.Index(
            fields=['assigned_room', 'status', 'check_in', 'check_out'],
            name='room_booking_overlap_idx',
            condition=models.Q(assigned_room__isnull=False)
        ),
        
        # Optimized for in-house guest queries
        models.Index(
            fields=['checked_in_at', 'checked_out_at'],
            name='room_booking_inhouse_idx',
            condition=models.Q(
                checked_in_at__isnull=False,
                checked_out_at__isnull=True
            )
        ),
    ]
```

#### Query Performance Benefits:
- Overlap detection: O(log n) instead of O(n) table scan
- In-house guest lookups: Indexed timestamp ranges
- Room availability: Direct index usage for assignment conflicts

### Migration Command:
```bash
python manage.py makemigrations room_bookings --name add_overlap_performance_indexes
```

---

## Phase 5: Comprehensive Test Suite

### File: `room_bookings/tests/test_room_assignment.py` (NEW)

#### Test Structure
```python
class TestRoomAssignmentService(TestCase):
    """Test core service layer logic"""
    
    def setUp(self):
        # Create test hotel, room types, rooms, staff, bookings
        pass
    
    def test_find_available_rooms_hotel_scoped(self):
        """Available rooms must be from same hotel only"""
        
    def test_find_available_rooms_excludes_non_bookable(self):
        """Dirty/maintenance/out-of-order rooms excluded"""
        
    def test_find_available_rooms_excludes_overlapping(self):
        """Rooms with overlapping INVENTORY_BLOCKING bookings excluded"""
        
    def test_assign_room_validates_hotel_scope(self):
        """Cannot assign room from different hotel"""
        
    def test_assign_room_validates_room_type_match(self):
        """Room type must match booking room type"""
        
    def test_assign_room_validates_bookable_status(self):
        """Cannot assign non-bookable rooms"""
        
    def test_assign_room_prevents_overlap_conflicts(self):
        """Cannot assign room with overlapping confirmed bookings"""
        
    def test_assign_room_is_idempotent(self):
        """Assigning same room twice returns success"""
        
    def test_assign_room_allows_reassignment_before_checkin(self):
        """Can reassign room before check-in with audit log"""
        
    def test_assign_room_blocks_reassignment_after_checkin(self):
        """Cannot reassign after checked_in_at is set"""

class TestRoomAssignmentConcurrency(TransactionTestCase):
    """Test concurrent access scenarios"""
    
    def test_concurrent_assignment_same_room(self):
        """Two parallel assignments to same room - one succeeds, one fails"""
        
    def test_concurrent_assignment_different_rooms(self):
        """Parallel assignments to different rooms both succeed"""

class TestRoomAssignmentAPIViews(TestCase):
    """Test API endpoint behavior"""
    
    def test_available_rooms_requires_staff_permissions(self):
        """Non-staff users get 403"""
        
    def test_available_rooms_hotel_scoped_access(self):
        """Staff from hotel A cannot access hotel B bookings"""
        
    def test_assign_room_structured_error_responses(self):
        """Errors return proper codes and messages"""
        
    def test_assign_room_audit_logging(self):
        """Assignment creates proper audit trail"""
        
    def test_unassign_room_before_checkin_allowed(self):
        """Can unassign room before check-in"""
        
    def test_unassign_room_after_checkin_blocked(self):
        """Cannot unassign room after check-in"""
        
    def test_staff_bookings_list_filters(self):
        """List endpoint respects all query parameters"""
```

#### Critical Concurrency Test
```python
def test_concurrent_room_assignment_race_condition(self):
    """
    CRITICAL TEST: Verify no double-booking under concurrent load
    
    Setup: 2 bookings, 1 available room, overlapping dates
    Action: Attempt to assign same room to both bookings simultaneously
    Expected: One succeeds (200), one fails (409 ROOM_OVERLAP_CONFLICT)
    """
    import threading
    
    booking1 = self.create_booking(check_in='2025-01-01', check_out='2025-01-03')
    booking2 = self.create_booking(check_in='2025-01-02', check_out='2025-01-04') 
    room = self.create_room()
    
    results = []
    
    def assign_room(booking_id):
        try:
            result = RoomAssignmentService.assign_room_atomic(
                booking_id=booking_id,
                room_id=room.id,
                staff_user=self.staff_user
            )
            results.append(('success', booking_id))
        except RoomAssignmentError as e:
            results.append(('error', e.code))
    
    # Run assignments concurrently
    thread1 = threading.Thread(target=assign_room, args=[booking1.id])
    thread2 = threading.Thread(target=assign_room, args=[booking2.id])
    
    thread1.start()
    thread2.start() 
    thread1.join()
    thread2.join()
    
    # Verify exactly one success, one conflict
    success_count = len([r for r in results if r[0] == 'success'])
    conflict_count = len([r for r in results if r[1] == 'ROOM_OVERLAP_CONFLICT'])
    
    self.assertEqual(success_count, 1)
    self.assertEqual(conflict_count, 1)
```

---

## Acceptance Criteria Checklist

### ✅ Security & Data Integrity
- [ ] **No double-booking possible**: Atomic assignment with overlap detection prevents concurrent race conditions
- [ ] **Hotel scoping enforced**: All endpoints validate `booking.hotel.slug == hotel_slug` 
- [ ] **Staff-only access**: `IsStaffMember` permission required for all assignment operations
- [ ] **Room state validation**: Dirty/maintenance/out-of-order rooms cannot be assigned

### ✅ Business Logic Compliance  
- [ ] **Turnover workflow respected**: Only `Room.is_bookable()` rooms can be assigned
- [ ] **Inventory blocking enforced**: Rooms with `CONFIRMED`/`CHECKED_IN` overlapping bookings unavailable
- [ ] **Room type matching**: Cannot assign room of different type than booking requires
- [ ] **Check-in constraints**: Room assignment/reassignment blocked after `checked_in_at` timestamp

### ✅ API Quality & UX
- [ ] **Structured error codes**: Frontend gets actionable error codes like `ROOM_OVERLAP_CONFLICT`
- [ ] **Idempotent operations**: Assigning same room twice returns success without changes  
- [ ] **Comprehensive filtering**: Staff can filter bookings by assignment status, dates, room type
- [ ] **Audit trail**: All assignments tracked with timestamp, staff user, and notes

### ✅ Technical Excellence
- [ ] **Atomic operations**: `transaction.atomic()` with `select_for_update()` prevents race conditions
- [ ] **Service layer separation**: Business logic centralized in reusable service functions
- [ ] **Comprehensive tests**: Edge cases, concurrency, permissions, and integration scenarios covered
- [ ] **Performance optimized**: Efficient queries with proper `select_related()` and indexed lookups

---

## Implementation Order

1. **Phase 0**: Create constants file and define canonical business rules
2. **Phase 1**: Add assignment audit fields with Django migration  
3. **Phase 2**: Build service layer with comprehensive validation and atomic assignment
4. **Phase 3**: Implement API endpoints following existing patterns
5. **Phase 4**: Add structured error handling and documentation
6. **Phase 5**: Create comprehensive test suite including concurrency tests

**Estimated Effort**: 3-4 development days with thorough testing

**Key Risk Mitigation**: The atomic service layer with row-level locking eliminates race conditions that could cause double-booking under concurrent staff operations.

---

## ✅ Canonical Inventory Blocking Rule (Matches Actual Model Schema)

**Use this rule everywhere you need "this booking blocks the room":**

### Blocks Inventory If:
```python
# Primary rule: Confirmed bookings that haven't checked out
(status == 'CONFIRMED' AND checked_out_at IS NULL)

OR 

# In-house guests: checked in but not checked out
(checked_in_at IS NOT NULL AND checked_out_at IS NULL)
```

### Optional Policy Switch:
- Include `PENDING_PAYMENT` in blocking statuses IF business reserves inventory during payment processing

### Never Block Inventory:
- `CANCELLED` - booking was cancelled
- `COMPLETED` - guest has fully checked out
- `NO_SHOW` - guest never arrived

### Implementation Pattern:
```python
# Use this Django Q expression everywhere
blocking_filter = models.Q(
    status__in=['CONFIRMED'],  # Add 'PENDING_PAYMENT' if needed
    checked_out_at__isnull=True
) | models.Q(
    checked_in_at__isnull=False,
    checked_out_at__isnull=True
)

# Always exclude non-blocking statuses
exclude_filter = models.Q(status__in=['CANCELLED', 'COMPLETED', 'NO_SHOW'])
```

This matches your actual model reality and handles the "in-house" concept properly using timestamps instead of non-existent status values.