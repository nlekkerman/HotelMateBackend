# HOUSEKEEPING APP IMPLEMENTATION PLAN

**Date**: December 20, 2025  
**Objective**: Implement a canonical Django app for HotelMate's housekeeping workflow management  
**Scope**: Room turnover workflow + audit trails while keeping `rooms.Room.room_status` as single source of truth  

## ARCHITECTURE OVERVIEW

The housekeeping app manages room status transitions through a canonical service layer while maintaining complete audit trails. All status changes flow through one controlled function that enforces business rules, permissions, and data integrity.

### SOURCE OF TRUTH MODELS (Already Exist)
- **rooms.Room**: `room_status` + `ROOM_STATUS_CHOICES`, state machine validation, cleaning/inspection fields
- **staff.Staff**: hotel scoping, department/role relationships, access_level permissions
- **hotel.Hotel**: tenant boundaries via slug-based routing
- **hotel.RoomBooking**: room assignments and occupancy tracking

### HARD CONSTRAINTS
1. All endpoints require staff authentication + hotel scoping
2. NEVER write `room.room_status = ...` outside canonical service
3. Every status change requires validation + audit + permission enforcement
4. Existing Room/Staff/Hotel models remain unchanged

---

## DELIVERABLES BREAKDOWN

### A. MODELS (`housekeeping/models.py`)

#### 1. RoomStatusEvent (Immutable Audit Trail)
```python
class RoomStatusEvent(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE)
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey('staff.Staff', null=True, blank=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=20, choices=[
        ('HOUSEKEEPING', 'Housekeeping'),
        ('FRONT_DESK', 'Front Desk'),
        ('SYSTEM', 'System'),
        ('MANAGER_OVERRIDE', 'Manager Override'),
    ])
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 2. HousekeepingTask (Workflow Management)
```python
class HousekeepingTask(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE)
    booking = models.ForeignKey('hotel.RoomBooking', null=True, blank=True, on_delete=models.SET_NULL)
    task_type = models.CharField(max_length=20, choices=[
        ('TURNOVER', 'Turnover'),
        ('STAYOVER', 'Stayover'), 
        ('INSPECTION', 'Inspection'),
        ('DEEP_CLEAN', 'Deep Clean'),
        ('AMENITY', 'Amenity'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
        ('CANCELLED', 'Cancelled'),
    ])
    priority = models.CharField(max_length=5, choices=[
        ('LOW', 'Low'),
        ('MED', 'Medium'), 
        ('HIGH', 'High'),
    ])
    assigned_to = models.ForeignKey('staff.Staff', null=True, blank=True, on_delete=models.SET_NULL)
    note = models.TextField(blank=True, default="")
    created_by = models.ForeignKey('staff.Staff', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
```

### B. PERMISSIONS + POLICIES (`housekeeping/policy.py`)

#### Permission Functions
- `is_manager(staff)` → `staff.access_level in {'staff_admin', 'super_staff_admin'}`
- `is_housekeeping(staff)` → Check `department.slug == "housekeeping"` OR `role.slug == "housekeeping"`
- `can_change_room_status(staff, room, to_status, source, note)` → Role-based transition rules

#### Permission Rules Matrix
| Role | Allowed Transitions | Special Requirements |
|------|-------------------|---------------------|
| Manager | Any valid Room transition | Note required for MANAGER_OVERRIDE |
| Housekeeping | Normal cleaning workflow | CHECKOUT_DIRTY → CLEANING_IN_PROGRESS → CLEANED_UNINSPECTED → READY_FOR_GUEST |
| Front Desk | Limited | Cannot set READY_FOR_GUEST, CLEANED_UNINSPECTED, CLEANING_IN_PROGRESS |

### C. CANONICAL SERVICE (`housekeeping/services.py`)

#### Core Function: `set_room_status()`
```python
@transaction.atomic
def set_room_status(*, room, to_status, staff=None, source="HOUSEKEEPING", note="") -> Room:
    """Single source of truth for all room status changes"""
    # 1. Validate to_status in ROOM_STATUS_CHOICES
    # 2. Enforce room.can_transition_to(to_status)
    # 3. Enforce can_change_room_status() permissions
    # 4. Create RoomStatusEvent audit record
    # 5. Update Room fields based on to_status:
    #    - CLEANING_IN_PROGRESS: add turnover note
    #    - CLEANED_UNINSPECTED: set last_cleaned_at, cleaned_by_staff
    #    - READY_FOR_GUEST: set last_inspected_at, inspected_by_staff
    #    - MAINTENANCE_REQUIRED: set maintenance_required=True
    # 6. Save room.room_status = to_status
```

### D. API ENDPOINTS (`housekeeping/views.py` + `housekeeping/staff_urls.py`)

#### Staff API Endpoints
1. **Dashboard**: `GET /api/staff/hotel/{hotel_slug}/housekeeping/dashboard/`
   - Room counts by status
   - Rooms grouped by status with details
   - Staff member's assigned tasks
   
2. **Tasks Management**: `GET/POST /api/staff/hotel/{hotel_slug}/housekeeping/tasks/`
   - List/create housekeeping tasks
   - Filters: status, task_type, assigned_to=me
   
3. **Task Assignment**: `POST /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{task_id}/assign/`
   - Manager assigns tasks to staff members
   
4. **Room Status Update**: `POST /api/staff/hotel/{hotel_slug}/rooms/{room_id}/status/`
   - Canonical status changes via service layer
   - Body: `{"to_status": "...", "source": "...", "note": "..."}`
   
5. **Status History**: `GET /api/staff/hotel/{hotel_slug}/rooms/{room_id}/status-history/`
   - Audit trail of all status changes for a room

### E. SERIALIZERS (`housekeeping/serializers.py`)

- `HousekeepingTaskSerializer` - List/detail/create tasks
- `HousekeepingTaskAssignSerializer` - Task assignment with hotel validation
- `RoomStatusUpdateSerializer` - Status changes with source/note validation
- `RoomStatusEventSerializer` - Read-only audit records

### F. ADMIN INTERFACE (`housekeeping/admin.py`)

- `HousekeepingTask` admin with filters for hotel, status, task_type, assigned_to
- `RoomStatusEvent` admin with filters for hotel, room, source, changed_by

### G. TESTING (`housekeeping/tests/test_housekeeping.py`)

#### Test Coverage
1. **Service Layer Tests**
   - Invalid transition rejection
   - Permission enforcement by role
   - Manager override note requirement
   - Audit record creation
   
2. **API Integration Tests**  
   - Hotel scoping enforcement
   - Authentication requirements
   - Role-based endpoint access
   - Data validation and error handling

---

## IMPLEMENTATION SEQUENCE

1. **Foundation**: Create app structure + models + migrations
2. **Business Logic**: Implement policy functions + canonical service
3. **API Layer**: Build serializers + views + URL routing
4. **Admin & Testing**: Register admin interfaces + comprehensive tests
5. **Integration**: Wire into main staff URL routing

---

## INTEGRATION NOTES

- **Phase 1**: Build standalone housekeeping app (this plan)
- **Phase 2**: Add checkout hooks to auto-create turnover tasks (future)  
- **Phase 3**: Real-time updates and notification system (future)

The app will integrate seamlessly with existing Room status management while providing structured workflow management and complete audit trails for housekeeping operations.