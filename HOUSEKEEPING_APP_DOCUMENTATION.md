# HotelMate Housekeeping App Documentation

**Version**: 1.0  
**Date**: December 20, 2025  
**Status**: Production Ready ✅  

## Overview

The HotelMate Housekeeping App is a comprehensive Django application that manages room turnover workflows, staff task assignments, and maintains complete audit trails for all room status changes. It serves as the **single source of truth** for housekeeping operations while integrating seamlessly with existing Room, Staff, and Hotel models.

## 🎯 Core Features

### 1. **Canonical Room Status Management**
- **Single Function Control**: All room status changes flow through one canonical `set_room_status()` function
- **Audit Trail**: Every status change creates an immutable `RoomStatusEvent` record
- **Permission Enforcement**: Role-based access control for different staff types
- **State Machine Validation**: Leverages existing `Room.can_transition_to()` validation
- **Automatic Field Updates**: Updates cleaning times, inspection times, and maintenance flags

### 2. **Workflow Task Management**
- **Task Types**: TURNOVER, STAYOVER, INSPECTION, DEEP_CLEAN, AMENITY
- **Status Tracking**: OPEN → IN_PROGRESS → DONE/CANCELLED
- **Priority Levels**: HIGH, MED, LOW with SLA tracking
- **Staff Assignment**: Manager-controlled task assignment system
- **Overdue Detection**: Automatic SLA violation detection based on priority

### 3. **Role-Based Permissions**
- **Managers**: Can override any valid room transition (requires notes)
- **Housekeeping Staff**: Normal cleaning workflow permissions
- **Front Desk**: Limited permissions (cannot set cleaning statuses)
- **Hotel Scoping**: All operations scoped to staff member's hotel

### 4. **Real-Time Dashboard**
- **Room Status Overview**: Visual counts and grouping by status
- **My Tasks**: Staff member's assigned tasks
- **Open Tasks**: Available tasks for managers
- **Maintenance Alerts**: Rooms requiring maintenance attention

---

## 🏗️ Technical Architecture

### Models

#### `RoomStatusEvent` - Audit Trail
```python
# Immutable record of every room status change
- hotel: FK to Hotel (CASCADE)
- room: FK to Room (CASCADE)  
- from_status/to_status: CharField (20)
- changed_by: FK to Staff (SET_NULL)
- source: HOUSEKEEPING|FRONT_DESK|SYSTEM|MANAGER_OVERRIDE
- note: TextField (required for MANAGER_OVERRIDE)
- created_at: DateTime (auto)
```

#### `HousekeepingTask` - Workflow Management
```python
# Task assignment and tracking
- hotel: FK to Hotel (CASCADE)
- room: FK to Room (CASCADE)
- booking: FK to RoomBooking (SET_NULL, optional)
- task_type: TURNOVER|STAYOVER|INSPECTION|DEEP_CLEAN|AMENITY
- status: OPEN|IN_PROGRESS|DONE|CANCELLED
- priority: HIGH|MED|LOW
- assigned_to: FK to Staff (SET_NULL)
- created_by: FK to Staff (SET_NULL)
- note: TextField
- timestamps: created_at, started_at, completed_at
```

### Services Layer

#### `set_room_status()` - Canonical Function
**The ONLY function allowed to change `room.room_status`**

```python
@transaction.atomic
def set_room_status(*, room, to_status, staff=None, source="HOUSEKEEPING", note=""):
    # 1. Validate transition using Room.can_transition_to()
    # 2. Enforce role-based permissions
    # 3. Create immutable RoomStatusEvent audit record
    # 4. Update Room fields based on status:
    #    - CLEANING_IN_PROGRESS: Add turnover note
    #    - CLEANED_UNINSPECTED: Set last_cleaned_at, cleaned_by_staff
    #    - READY_FOR_GUEST: Set last_inspected_at, inspected_by_staff
    #    - MAINTENANCE_REQUIRED: Set maintenance_required=True
    # 5. Save Room with minimal field updates
    return room
```

---

## 🔌 API Endpoints

All endpoints require **staff authentication** and **hotel scoping** via `/api/staff/hotel/{hotel_slug}/housekeeping/`

### Dashboard
```http
GET /api/staff/hotel/{hotel_slug}/housekeeping/dashboard/
```
**Response:**
```json
{
  "counts": {"AVAILABLE": 3, "CHECKOUT_DIRTY": 2, "CLEANING_IN_PROGRESS": 1},
  "rooms_by_status": {
    "CHECKOUT_DIRTY": [
      {"id": 1, "room_number": "101", "maintenance_required": false}
    ]
  },
  "my_open_tasks": [...],
  "open_tasks": [...],
  "total_rooms": 25
}
```

### Task Management
```http
GET  /api/staff/hotel/{hotel_slug}/housekeeping/tasks/
POST /api/staff/hotel/{hotel_slug}/housekeeping/tasks/
```
**Query Filters**: `status`, `task_type`, `assigned_to=me`

**POST Body:**
```json
{
  "room": 1,
  "task_type": "TURNOVER", 
  "priority": "HIGH",
  "note": "Guest checkout - deep clean needed"
}
```

### Task Assignment
```http
POST /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{task_id}/assign/
```
**Body:**
```json
{
  "assigned_to_id": 5,
  "note": "Assigned for morning shift"
}
```

### Task Actions
```http
POST /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{task_id}/start/
POST /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{task_id}/complete/
```

### Room Status Management
```http
POST /api/staff/hotel/{hotel_slug}/rooms/{room_id}/status/
```
**Body:**
```json
{
  "to_status": "CLEANING_IN_PROGRESS",
  "source": "HOUSEKEEPING", 
  "note": "Starting turnover cleaning"
}
```

### Status History
```http
GET /api/staff/hotel/{hotel_slug}/rooms/{room_id}/status-history/
```
**Response:**
```json
{
  "room": {"id": 1, "room_number": "101", "current_status": "READY_FOR_GUEST"},
  "status_history": [
    {
      "from_status": "CLEANED_UNINSPECTED",
      "to_status": "READY_FOR_GUEST", 
      "changed_by_name": "Jane Smith",
      "source": "HOUSEKEEPING",
      "created_at": "2025-12-20T10:30:00Z"
    }
  ]
}
```

---

## 👥 Permission Matrix

| Role | Dashboard | Create Tasks | Assign Tasks | Room Status Changes |
|------|-----------|--------------|--------------|-------------------|
| **Manager** | ✅ | ✅ | ✅ | ✅ Any valid transition (note required for overrides) |
| **Housekeeping** | ✅ | ✅ | ❌ | ✅ Normal cleaning workflow only |
| **Front Desk** | ❌ | ✅ | ❌ | ❌ Cannot set cleaning-related statuses |
| **Other Staff** | ❌ | ✅ | ❌ | ❌ Very limited permissions |

### Housekeeping Workflow Permissions
```
CHECKOUT_DIRTY → CLEANING_IN_PROGRESS → CLEANED_UNINSPECTED → READY_FOR_GUEST
     ↓                    ↓                       ↓
MAINTENANCE_REQUIRED ←────────────────────────────
```

---

## 🎨 Admin Interface

### HousekeepingTask Admin
- **Color-coded status badges** (Open=Blue, In Progress=Yellow, Done=Green)
- **Priority indicators** (High=Red, Med=Yellow, Low=Green) 
- **Overdue alerts** with SLA violation warnings
- **Quick filters** by hotel, status, task_type, priority
- **Staff assignment links** to staff profiles
- **Room links** to room management

### RoomStatusEvent Admin
- **Immutable audit trail** (no add/edit/delete permissions)
- **Source color coding** (Manager Override=Red, System=Gray)
- **Status transition arrows** showing from → to changes
- **Staff attribution** with profile links
- **Searchable by room, staff, notes**

---

## 🚀 Usage Examples

### Example 1: Guest Checkout Workflow
```python
# 1. Guest checks out (handled by existing checkout process)
room = Room.objects.get(room_number="101")

# 2. Set room to dirty (via API or system)
set_room_status(
    room=room,
    to_status="CHECKOUT_DIRTY", 
    staff=front_desk_staff,
    source="FRONT_DESK",
    note="Guest checked out at 11:00 AM"
)

# 3. Create turnover task (optional - can be automatic in future)
task = create_turnover_task(
    room=room,
    priority="HIGH",
    note="VIP guest checkout - thorough cleaning needed"
)

# 4. Housekeeping starts cleaning
set_room_status(
    room=room,
    to_status="CLEANING_IN_PROGRESS",
    staff=housekeeper,
    note="Started deep cleaning"
)

# 5. Cleaning completed
set_room_status(
    room=room,
    to_status="CLEANED_UNINSPECTED", 
    staff=housekeeper,
    note="Cleaning completed, ready for inspection"
)

# 6. Inspection passed
set_room_status(
    room=room,
    to_status="READY_FOR_GUEST",
    staff=supervisor,
    note="Inspection passed - room ready for next guest"
)
```

### Example 2: Manager Override
```python
# Emergency situation - need to ready room immediately
set_room_status(
    room=room,
    to_status="READY_FOR_GUEST",
    staff=manager,
    source="MANAGER_OVERRIDE", 
    note="Emergency override for VIP arrival - room inspected by manager"
)
```

### Example 3: Maintenance Request
```python
# Housekeeping flags maintenance issue
set_room_status(
    room=room,
    to_status="MAINTENANCE_REQUIRED",
    staff=housekeeper,
    note="AC not working - reported to maintenance"
)
```

---

## 🔧 Integration Points

### With Existing Models
- **rooms.Room**: Leverages existing status field and transition validation
- **staff.Staff**: Uses existing access_level, department, role for permissions
- **hotel.Hotel**: Maintains hotel scoping for multi-tenant architecture
- **hotel.RoomBooking**: Optional linking for task context

### Future Integration Opportunities
- **Automatic Task Creation**: Hook into checkout process to auto-create turnover tasks
- **Real-time Notifications**: WebSocket updates for status changes
- **Mobile App Integration**: API-ready for mobile housekeeping apps
- **Inventory Management**: Link with stock_tracker for supply management
- **Guest Communication**: Integration with guest messaging for room readiness

---

## 📊 Reporting Capabilities

### Available Data Points
- **Room Status History**: Complete audit trail with timestamps
- **Staff Performance**: Tasks completed, average completion times
- **SLA Compliance**: Overdue task tracking by priority
- **Status Distribution**: Room counts by status over time
- **Maintenance Patterns**: Frequency of maintenance requests by room

### Sample Queries
```python
# Rooms cleaned by staff member this week
events = RoomStatusEvent.objects.filter(
    changed_by=staff,
    to_status="CLEANED_UNINSPECTED",
    created_at__gte=week_ago
).count()

# Average task completion time by priority
from django.db.models import Avg
avg_times = HousekeepingTask.objects.filter(
    status="DONE"
).values('priority').annotate(
    avg_duration=Avg('completed_at') - Avg('created_at')
)

# Maintenance request trends
maintenance_events = RoomStatusEvent.objects.filter(
    to_status="MAINTENANCE_REQUIRED",
    created_at__gte=month_ago
).values('room').annotate(count=Count('id'))
```

---

## 🛡️ Security Features

### Authentication & Authorization
- **Staff-only access**: All endpoints require staff authentication
- **Hotel scoping**: Automatic filtering by staff's assigned hotel
- **Role-based permissions**: Different capabilities based on staff role
- **Audit trail**: Immutable record of who changed what and when

### Data Validation
- **State machine compliance**: Validates all transitions through Room model
- **Hotel consistency**: Ensures all related objects belong to same hotel
- **Permission checks**: Validates staff can perform requested actions
- **Input sanitization**: Proper validation of all user inputs

---

## 📈 Performance Considerations

### Database Optimization
- **Indexes**: Optimized for common queries (hotel+status, staff+tasks, room+history)
- **Select Related**: Minimizes database queries in views and admin
- **Efficient Filtering**: Hotel scoping at database level
- **Minimal Updates**: Only saves changed fields to reduce database load

### Scalability Features  
- **Hotel-based partitioning**: Natural multi-tenant architecture
- **Audit retention**: Consider archiving old events for large datasets
- **Task cleanup**: Automatic cleanup of completed tasks after retention period
- **Caching opportunities**: Room status counts for dashboard performance

---

## 🎯 Next Steps & Roadmap

### Phase 2 - Automation
- **Checkout Hooks**: Automatically create turnover tasks on guest checkout
- **Check-in Integration**: Validate room readiness before guest check-in
- **Inventory Integration**: Track cleaning supply usage per task

### Phase 3 - Real-time Features
- **WebSocket Updates**: Live dashboard updates for status changes
- **Push Notifications**: Mobile alerts for task assignments
- **Live Chat**: Staff communication within task context

### Phase 4 - Analytics & Intelligence
- **Predictive Analytics**: Estimate cleaning times based on historical data
- **Performance Dashboards**: Staff efficiency and SLA compliance reporting
- **Maintenance Prediction**: Identify rooms likely to need maintenance

### Phase 5 - Mobile & External
- **Mobile App**: Native iOS/Android app for housekeeping staff
- **Third-party Integrations**: PMS, maintenance management systems
- **Guest Notifications**: Inform guests when room is ready

---

## 🔍 Troubleshooting

### Common Issues

**Permission Denied for Room Status Change**
- Check staff belongs to same hotel as room
- Verify staff role has appropriate permissions 
- For manager overrides, ensure note is provided

**Task Assignment Fails**
- Only managers can assign tasks (configurable)
- Ensure assigned staff belongs to same hotel
- Check task is in OPEN status

**Status History Empty**
- Events are only created through `set_room_status()` function
- Direct database updates bypass audit trail
- Check hotel scoping in queries

### Debugging Tips
```python
# Check room transition validity
room.can_transition_to("READY_FOR_GUEST")

# Validate staff permissions
from housekeeping.policy import can_change_room_status
can_change, error = can_change_room_status(staff, room, "CLEANING_IN_PROGRESS")

# View recent status changes
recent_events = RoomStatusEvent.objects.filter(
    room=room
).order_by('-created_at')[:10]
```

---

## 📝 Summary

The HotelMate Housekeeping App provides a **production-ready, comprehensive solution** for managing hotel room turnover workflows. With its canonical service architecture, comprehensive audit trails, and role-based permissions, it ensures data integrity while providing the flexibility needed for real-world hotel operations.

**Key Benefits:**
- ✅ **Single Source of Truth**: All room status changes go through one controlled function
- ✅ **Complete Audit Trail**: Every change is tracked with who, when, and why
- ✅ **Role-Based Security**: Appropriate permissions for different staff types  
- ✅ **Real-time Dashboard**: Visual overview of room statuses and tasks
- ✅ **Task Management**: Structured workflow for housekeeping operations
- ✅ **Admin Interface**: Rich management tools with color-coded displays
- ✅ **API Ready**: RESTful endpoints for mobile apps and integrations
- ✅ **Test Coverage**: Comprehensive tests for reliability

The app is ready for immediate use and designed to scale with your hotel's growing needs.