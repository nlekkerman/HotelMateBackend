# Pusher Real-time Events for Staff Attendance & Roster

This document explains how Pusher real-time events are handled for staff attendance and roster operations in the HotelMate system.

## 📡 Overview

The system uses Pusher WebSocket connections to provide real-time updates for:
- **Clock In/Out Status Changes**
- **Break Start/End Events** 
- **Roster Updates**
- **Staff Profile Changes**
- **Attendance Log Events**

All events are broadcasted through the `staff.pusher_utils.py` module to ensure consistency.

## 🔧 Backend Event Broadcasting

### Clock Status Updates

**Function:** `trigger_clock_status_update(hotel_slug, staff, action)`

**Channel:** `hotel-{hotel_slug}`
**Event:** `clock-status-updated`

```python
# Example usage in attendance views:
trigger_clock_status_update(hotel.slug, matched_staff, 'start_break')
trigger_clock_status_update(hotel.slug, matched_staff, 'end_break')
trigger_clock_status_update(hotel.slug, matched_staff, 'clock_in')
trigger_clock_status_update(hotel.slug, matched_staff, 'clock_out')
```

**Event Data Structure:**
```json
{
    "user_id": 456,
    "staff_id": 123,
    "duty_status": "on_break",
    "is_on_duty": true,
    "is_on_break": true,
    "status_label": "On Break",
    "clock_time": "2025-12-02T15:30:00Z",
    "first_name": "John",
    "last_name": "Doe",
    "action": "start_break",
    "department": "Front Desk",
    "department_slug": "front-desk",
    "current_status": {
        "status": "on_break",
        "label": "On Break",
        "is_on_break": true,
        "break_start": "2025-12-02T15:30:00Z",
        "total_break_minutes": 45
    }
}
```

### Actions Triggered

| Action | When Triggered | duty_status | is_on_duty |
|--------|---------------|-------------|------------|
| `clock_in` | Staff clocks in | `on_duty` | `true` |
| `clock_out` | Staff clocks out | `off_duty` | `false` |
| `start_break` | Staff starts break | `on_break` | `true` |
| `end_break` | Staff ends break | `on_duty` | `true` |

## 🎯 Frontend Integration

### React Component Setup

```javascript
import { useAttendanceRealtime } from "@/features/attendance/hooks/useAttendanceRealtime";

const MyComponent = () => {
  const { user } = useAuth();
  const hotelIdentifier = user?.hotel_slug;

  // Handle real-time attendance updates
  const handleAttendanceEvent = (event) => {
    const { type, payload } = event;
    
    if (type === 'clock-status-updated') {
      // Check if this update is for the current user
      const isCurrentUser = (user?.staff_id && payload.staff_id === user.staff_id) || 
                           (user?.id && payload.user_id === user.id);
      
      if (isCurrentUser) {
        // Update UI based on duty_status
        updateClockButton(payload.duty_status, payload.current_status);
        refreshStaffProfile();
      }
    }
  };

  // Initialize Pusher real-time updates
  useAttendanceRealtime(hotelIdentifier, handleAttendanceEvent);
};
```

### Button State Management

```javascript
const getClockButtonInfo = (staffProfile) => {
  if (!staffProfile?.current_status) {
    return { text: 'Clock In', color: '#28a745', isDanger: false };
  }
  
  const currentStatus = staffProfile.current_status;
  
  switch (currentStatus.status) {
    case 'off_duty':
      return { text: 'Clock In', color: '#28a745', isDanger: false };
      
    case 'on_duty':
      return { text: 'Start Break', color: '#ffc107', isDanger: false };
      
    case 'on_break':
      const breakTime = currentStatus.break_start 
        ? Math.round((Date.now() - new Date(currentStatus.break_start)) / 60000)
        : 0;
      return { 
        text: 'End Break', 
        subText: breakTime > 0 ? `(${breakTime} min)` : null,
        color: '#17a2b8', 
        isDanger: false 
      };
      
    default:
      return { text: 'Clock In', color: '#28a745', isDanger: false };
  }
};
```

## 🔄 Roster Updates

**Function:** `trigger_roster_update(hotel_slug, roster_data, action)`

**Channel:** `hotel-{hotel_slug}`
**Event:** `roster-updated`

**Actions:** `created`, `updated`, `deleted`, `bulk_updated`

```json
{
    "action": "updated",
    "roster_id": 789,
    "staff_id": 123,
    "staff_name": "John Doe",
    "shift_date": "2025-12-03",
    "shift_start": "09:00:00",
    "shift_end": "17:00:00",
    "department": "Front Desk",
    "location": "Reception",
    "timestamp": "2025-12-02T15:30:00Z"
}
```

## 👤 Staff Profile Updates

**Function:** `trigger_staff_profile_update(hotel_slug, staff, action)`

**Channel:** `hotel-{hotel_slug}`
**Event:** `staff-profile-updated`

**Actions:** `created`, `updated`, `deleted`

## 📋 Attendance Logs

**Function:** `trigger_attendance_log(hotel_slug, log_data, action)`

**Channel:** `hotel-{hotel_slug}`
**Event:** `attendance-logged`

**Actions:** `clock_in`, `clock_out`

Used for face recognition clock events and audit trails.

## 🎛️ Channel Structure

### Hotel-wide Events
- **Channel:** `hotel-{hotel_slug}` (e.g., `hotel-hotel-killarney`)
- **Subscribers:** All staff members in the hotel
- **Events:** Clock status, roster updates, profile changes

### Individual Staff Events
- **Channel:** `hotel-{hotel_slug}-staff-{staff_id}`
- **Subscribers:** Individual staff member
- **Events:** Personal notifications, navigation permissions

## ⚡ Real-time Flow Example

### Break Start Sequence

1. **User Action:** Staff clicks "Start Break" button
2. **API Call:** Frontend calls `/api/staff/hotel/{hotel_slug}/attendance/face-management/toggle-break/`
3. **Backend Processing:**
   ```python
   # Update database
   existing_log.is_on_break = True
   existing_log.break_start = now()
   existing_log.save()
   
   # Update staff status
   matched_staff.duty_status = 'on_break'
   matched_staff.save(update_fields=['duty_status'])
   
   # Trigger Pusher event
   trigger_clock_status_update(hotel.slug, matched_staff, 'start_break')
   ```
4. **Pusher Broadcast:** Event sent to `hotel-{hotel_slug}` channel
5. **Frontend Reception:** All connected staff receive the event
6. **UI Update:** Relevant staff members update their interface

## 🛡️ Security & Permissions

### Channel Authentication
- Hotel-wide channels require staff membership validation
- Individual staff channels require user identity verification

### Event Filtering
- Frontend components filter events by `staff_id` and `user_id`
- Only update UI for events relevant to the current user

### Data Privacy
- Personal break times and status only broadcast to hotel staff
- Sensitive data excluded from general broadcasts

## 🐛 Debugging Pusher Events

### Backend Logging
```python
import logging
logger = logging.getLogger(__name__)

# All Pusher events are logged with:
logger.info(f"Pusher: {event} triggered for staff {staff.id} in hotel {hotel_slug}")
logger.error(f"Pusher error: Failed to trigger {event} for staff {staff_id}: {e}")
```

### Frontend Debug Console
```javascript
// Enable Pusher logging
Pusher.logToConsole = true;

// Log all received events
const handleAttendanceEvent = (event) => {
  console.log("[Pusher] Attendance event received:", event);
  // ... handle event
};
```

### Common Issues

1. **Channel Mismatch:** Ensure frontend subscribes to `hotel-{hotel_slug}`, not custom channel names
2. **Event Name Mismatch:** Backend sends `clock-status-updated`, not `pusherClockStatusUpdate`
3. **Data Structure:** Event data is sent directly, not wrapped in `payload` object
4. **User Identification:** Match by both `staff_id` and `user_id` for reliability

## 📊 Event Flow Diagram

```
Clock Action → Backend API → Database Update → Pusher Event → Frontend Reception → UI Update
     ↓              ↓              ↓              ↓                ↓               ↓
Face/Button → attendance/views → duty_status → hotel-{slug} → useAttendance → Button Text
Recognition    face_views.py    current_status   channel       Realtime Hook    Profile Refresh
```

## 🔮 Future Enhancements

- **Batch Updates:** Group multiple roster changes into single events
- **Event Queuing:** Handle offline/reconnection scenarios
- **Performance Monitoring:** Track event delivery and processing times
- **Advanced Filtering:** More granular event subscriptions by department/role

---

**Note:** Always ensure your frontend Pusher integration matches the exact channel names, event names, and data structures defined in `staff/pusher_utils.py` for reliable real-time updates.