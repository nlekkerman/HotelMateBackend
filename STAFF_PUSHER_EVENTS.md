# Staff Real-Time Events with Pusher

## Overview

All staff-related operations now broadcast real-time updates via Pusher to keep all connected clients synchronized.

## Channel Structure

### Hotel-Wide Channel
`hotel-{hotel_slug}` - Broadcasts events to all staff in the hotel

### Staff-Specific Channel
`hotel-{hotel_slug}-staff-{staff_id}` - Personal channel for individual staff member

---

## Event Types

### 1. Clock Status Updates

**Event Name:** `clock-status-updated`

**Channel:** `hotel-{hotel_slug}`

**Triggered When:**
- Staff clocks in (via face recognition or manual)
- Staff clocks out (via face recognition or manual)

**Payload:**
```json
{
  "user_id": 123,
  "staff_id": 456,
  "is_on_duty": true,
  "clock_time": "2025-11-22T14:30:00.000Z",
  "first_name": "John",
  "last_name": "Doe",
  "action": "clock_in",
  "department": "Food & Beverage",
  "department_slug": "food-and-beverage"
}
```

**Frontend Usage:**
```javascript
const channel = pusher.subscribe(`hotel-${hotelSlug}`);

channel.bind('clock-status-updated', (data) => {
  console.log(`${data.first_name} ${data.last_name} ${data.action}`);
  
  // Update staff status in UI
  if (data.user_id === currentUser.id) {
    setIsOnDuty(data.is_on_duty);
  }
});
```

---

### 2. Attendance Logs

**Event Name:** `attendance-logged`

**Channel:** `hotel-{hotel_slug}`

**Triggered When:**
- Clock in/out via face recognition
- Manual attendance log created

**Payload:**
```json
{
  "action": "clock_in",
  "log_id": 789,
  "staff_id": 456,
  "staff_name": "John Doe",
  "department": "Food & Beverage",
  "time": "2025-11-22T14:30:00.000Z",
  "verified_by_face": true,
  "timestamp": "2025-11-22T14:30:00.000Z"
}
```

---

### 3. Staff Profile Updates

**Event Name:** `staff-profile-updated`

**Channel:** `hotel-{hotel_slug}`

**Triggered When:**
- New staff member created
- Staff profile updated (name, department, role, etc.)
- Staff member deleted/deactivated

**Payload:**
```json
{
  "staff_id": 456,
  "user_id": 123,
  "action": "updated",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "department": "Food & Beverage",
  "department_slug": "food-and-beverage",
  "role": "Server",
  "role_slug": "server",
  "is_active": true,
  "is_on_duty": false,
  "access_level": "regular_staff",
  "timestamp": "2025-11-22T14:30:00.000Z"
}
```

**Actions:**
- `created` - New staff profile
- `updated` - Profile modified
- `deleted` - Profile removed

---

### 4. Registration Updates

**Event Name:** `staff-registration-updated`

**Channel:** `hotel-{hotel_slug}`

**Triggered When:**
- User registers with registration code (pending)
- Manager approves registration (creates staff profile)

**Payload:**
```json
{
  "action": "pending",
  "user_id": 123,
  "username": "johndoe",
  "registration_code": "ABC12345",
  "staff_id": null,
  "timestamp": "2025-11-22T14:30:00.000Z"
}
```

**Actions:**
- `pending` - User registered, awaiting approval
- `approved` - Staff profile created
- `rejected` - Registration denied (not implemented)

---

### 5. Navigation Permissions

**Event Name:** `navigation-permissions-updated`

**Channel:** `hotel-{hotel_slug}-staff-{staff_id}`

**Triggered When:**
- Super admin updates staff navigation permissions

**Payload:**
```json
{
  "staff_id": 456,
  "navigation_items": ["home", "chat", "roster", "clock"],
  "timestamp": "2025-11-22T14:30:00.000Z"
}
```

**Frontend Usage:**
```javascript
const channel = pusher.subscribe(`hotel-${hotelSlug}-staff-${staffId}`);

channel.bind('navigation-permissions-updated', (data) => {
  // Update allowed navigation items
  setAllowedNavs(data.navigation_items);
  console.log('Navigation permissions updated:', data.navigation_items);
});
```

---

### 6. Roster Updates

**Event Name:** `roster-updated`

**Channel:** `hotel-{hotel_slug}`

**Triggered When:**
- Shift created/updated/deleted
- Bulk roster operations

**Payload:**
```json
{
  "action": "created",
  "roster_id": 1234,
  "staff_id": 456,
  "staff_name": "John Doe",
  "shift_date": "2025-11-25",
  "shift_start": "09:00",
  "shift_end": "17:00",
  "department": "Food & Beverage",
  "location": "Main Dining",
  "timestamp": "2025-11-22T14:30:00.000Z"
}
```

**Actions:**
- `created` - New shift added
- `updated` - Shift modified
- `deleted` - Shift removed
- `bulk_updated` - Multiple shifts changed

---

### 7. Department/Role Updates

**Event Names:** `department-updated`, `role-updated`

**Channel:** `hotel-{hotel_slug}`

**Triggered When:**
- Department or role created/updated/deleted

**Payload:**
```json
{
  "action": "updated",
  "id": 5,
  "name": "Food & Beverage",
  "slug": "food-and-beverage",
  "timestamp": "2025-11-22T14:30:00.000Z"
}
```

---

## Frontend Integration Example

### React Hook for Staff Events

```javascript
import { useEffect } from 'react';
import Pusher from 'pusher-js';

const usePusherStaffEvents = (hotelSlug, staffId, callbacks) => {
  useEffect(() => {
    if (!hotelSlug) return;

    const pusher = new Pusher(process.env.REACT_APP_PUSHER_KEY, {
      cluster: process.env.REACT_APP_PUSHER_CLUSTER,
    });

    // Subscribe to hotel-wide channel
    const hotelChannel = pusher.subscribe(`hotel-${hotelSlug}`);

    // Clock status updates
    hotelChannel.bind('clock-status-updated', (data) => {
      console.log('[Pusher] Clock status:', data);
      callbacks?.onClockStatus?.(data);
    });

    // Staff profile updates
    hotelChannel.bind('staff-profile-updated', (data) => {
      console.log('[Pusher] Staff profile:', data);
      callbacks?.onStaffProfile?.(data);
    });

    // Attendance logs
    hotelChannel.bind('attendance-logged', (data) => {
      console.log('[Pusher] Attendance log:', data);
      callbacks?.onAttendance?.(data);
    });

    // Roster updates
    hotelChannel.bind('roster-updated', (data) => {
      console.log('[Pusher] Roster updated:', data);
      callbacks?.onRoster?.(data);
    });

    // Registration updates
    hotelChannel.bind('staff-registration-updated', (data) => {
      console.log('[Pusher] Registration:', data);
      callbacks?.onRegistration?.(data);
    });

    // Staff-specific channel (if staffId provided)
    let staffChannel;
    if (staffId) {
      staffChannel = pusher.subscribe(`hotel-${hotelSlug}-staff-${staffId}`);
      
      staffChannel.bind('navigation-permissions-updated', (data) => {
        console.log('[Pusher] Navigation perms:', data);
        callbacks?.onNavigationPerms?.(data);
      });
    }

    // Cleanup
    return () => {
      hotelChannel.unbind_all();
      pusher.unsubscribe(`hotel-${hotelSlug}`);
      
      if (staffChannel) {
        staffChannel.unbind_all();
        pusher.unsubscribe(`hotel-${hotelSlug}-staff-${staffId}`);
      }
    };
  }, [hotelSlug, staffId, callbacks]);
};

export default usePusherStaffEvents;
```

### Usage in Component

```javascript
import usePusherStaffEvents from './hooks/usePusherStaffEvents';

function StaffDashboard() {
  const [isOnDuty, setIsOnDuty] = useState(false);
  const [staffList, setStaffList] = useState([]);
  
  usePusherStaffEvents(hotelSlug, staffId, {
    onClockStatus: (data) => {
      if (data.staff_id === staffId) {
        setIsOnDuty(data.is_on_duty);
      }
      
      // Update staff list
      setStaffList(prev => prev.map(staff => 
        staff.id === data.staff_id 
          ? { ...staff, is_on_duty: data.is_on_duty }
          : staff
      ));
    },
    
    onStaffProfile: (data) => {
      if (data.action === 'created') {
        setStaffList(prev => [...prev, data]);
      } else if (data.action === 'updated') {
        setStaffList(prev => prev.map(staff =>
          staff.id === data.staff_id ? { ...staff, ...data } : staff
        ));
      } else if (data.action === 'deleted') {
        setStaffList(prev => prev.filter(staff => staff.id !== data.staff_id));
      }
    },
    
    onNavigationPerms: (data) => {
      setAllowedNavs(data.navigation_items);
    }
  });
  
  return <div>{/* Your UI */}</div>;
}
```

---

## Testing

### Backend Test (Django Shell)
```python
from staff.pusher_utils import trigger_clock_status_update
from staff.models import Staff

staff = Staff.objects.first()
trigger_clock_status_update('hotel-killarney', staff, 'clock_in')
```

### Frontend Test (Browser Console)
```javascript
// Check Pusher connection
console.log(pusher.connection.state);

// Subscribe and listen
const channel = pusher.subscribe('hotel-killarney');
channel.bind('clock-status-updated', (data) => {
  console.log('Received:', data);
});
```

### Pusher Dashboard
1. Go to https://dashboard.pusher.com
2. Select your app
3. Open Debug Console
4. Perform action (clock in/out)
5. Verify event appears in console

---

## Benefits

✅ **Real-time updates** - No polling needed  
✅ **Multi-device sync** - Changes reflect instantly everywhere  
✅ **Scalable** - Pusher handles connection management  
✅ **Reliable** - Automatic reconnection and event buffering  
✅ **Efficient** - Only affected clients receive updates  

---

## Implementation Notes

- All Pusher calls are wrapped in try-catch to prevent failures
- Errors are logged but don't block operations
- Events include timestamps for ordering
- All string fields use safe defaults for None values
- Hotel slug is always required for channel naming
