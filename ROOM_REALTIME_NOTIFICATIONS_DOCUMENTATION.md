# Room Realtime Notifications Documentation

**Version**: 1.0  
**Date**: December 20, 2025  
**Status**: Production Ready ✅  

## Overview

The Room Realtime Notifications system provides instant updates to frontend clients when room operational states change. This system extends the existing HotelMate realtime infrastructure to support comprehensive room status updates, maintenance alerts, and housekeeping workflow changes.

## 🎯 Key Features

### Real-time Room Updates
- **Instant Status Changes**: Room status transitions broadcast immediately
- **Maintenance Alerts**: Real-time maintenance flag updates
- **Cleaning Progress**: Live housekeeping workflow updates
- **Occupancy Changes**: Guest check-in/check-out status updates
- **Out-of-Order Notifications**: Immediate alerts for room availability changes

### Frontend Integration
- **Consistent Channel Pattern**: Uses existing `{hotel_slug}.rooms` channel
- **Normalized Events**: Follows established event envelope structure
- **Full Room Snapshot**: Complete room state for efficient UI updates
- **Change Tracking**: Specific field changes identified for optimized rendering

---

## 🏗️ Technical Implementation

### NotificationManager Extension

#### New Method: `realtime_room_updated()`
```python
def realtime_room_updated(self, room, changed_fields=None, source="system"):
    """
    Emit normalized room updated event for operational updates.
    
    Args:
        room: Room instance
        changed_fields: List of field names that were changed
        source: Source of the change ("housekeeping", "front_desk", etc.)
    """
```

### Event Structure

#### Channel
```
{hotel_slug}.rooms
```

#### Event Name
```
room_updated
```

#### Full Event Payload
```json
{
  "category": "rooms",
  "type": "room_updated",
  "payload": {
    "room_number": "101",
    "room_status": "CLEANING_IN_PROGRESS",
    "is_occupied": false,
    "is_out_of_order": false,
    "maintenance_required": true,
    "maintenance_priority": "HIGH", 
    "maintenance_notes": "AC not working",
    "last_cleaned_at": "2025-12-20T10:30:00Z",
    "last_inspected_at": null,
    "changed_fields": ["room_status", "maintenance_required"],
    "room_type": "Standard Room",
    "max_occupancy": 2,
    "guests_in_room": 0
  },
  "meta": {
    "hotel_slug": "hotel-killarney",
    "event_id": "uuid-here",
    "ts": "2025-12-20T10:30:00Z",
    "scope": {
      "room_number": "101"
    }
  }
}
```

---

## 🔌 Usage Patterns

### Basic Room Status Update
```python
from django.db import transaction
from notifications.notification_manager import NotificationManager

# After room status change
transaction.on_commit(
    lambda: NotificationManager().realtime_room_updated(
        room=room,
        changed_fields=["room_status"],
        source="housekeeping"
    )
)
```

### Maintenance Flag Update
```python
# When maintenance is required
transaction.on_commit(
    lambda: NotificationManager().realtime_room_updated(
        room=room,
        changed_fields=["maintenance_required", "maintenance_priority", "maintenance_notes"],
        source="housekeeping"
    )
)
```

### Housekeeping Workflow Integration
The housekeeping service automatically emits notifications:

```python
# In housekeeping/services.py - set_room_status()
transaction.on_commit(
    lambda: notification_manager.realtime_room_updated(
        room=room,
        changed_fields=fields_to_update,
        source=source.lower()
    )
)
```

---

## 🎨 Frontend Integration

### JavaScript/TypeScript Example
```javascript
// Subscribe to room updates
const channel = pusher.subscribe(`${hotelSlug}.rooms`);

channel.bind('room_updated', (data) => {
  const { payload, meta } = data;
  
  console.log(`Room ${payload.room_number} updated:`, payload.changed_fields);
  
  // Update room card in UI
  updateRoomCard(payload.room_number, {
    status: payload.room_status,
    maintenanceRequired: payload.maintenance_required,
    lastCleaned: payload.last_cleaned_at,
    changedFields: payload.changed_fields
  });
  
  // Show specific notifications
  if (payload.changed_fields.includes('maintenance_required') && payload.maintenance_required) {
    showMaintenanceAlert(payload.room_number, payload.maintenance_priority);
  }
  
  if (payload.changed_fields.includes('room_status')) {
    showStatusUpdate(payload.room_number, payload.room_status);
  }
});
```

### React Hook Example
```tsx
import { useEffect, useState } from 'react';
import { pusher } from './pusher-config';

export const useRoomUpdates = (hotelSlug: string) => {
  const [roomUpdates, setRoomUpdates] = useState<RoomUpdate[]>([]);
  
  useEffect(() => {
    const channel = pusher.subscribe(`${hotelSlug}.rooms`);
    
    channel.bind('room_updated', (data: RoomUpdateEvent) => {
      setRoomUpdates(prev => [...prev, {
        roomNumber: data.payload.room_number,
        status: data.payload.room_status,
        changedFields: data.payload.changed_fields,
        timestamp: data.meta.ts
      }]);
    });
    
    return () => {
      pusher.unsubscribe(`${hotelSlug}.rooms`);
    };
  }, [hotelSlug]);
  
  return roomUpdates;
};
```

---

## 📊 Event Types & Triggers

### Room Status Changes
| From Status | To Status | Triggered By | Changed Fields |
|------------|-----------|--------------|----------------|
| `CHECKOUT_DIRTY` | `CLEANING_IN_PROGRESS` | Housekeeping | `["room_status"]` |
| `CLEANING_IN_PROGRESS` | `CLEANED_UNINSPECTED` | Housekeeping | `["room_status", "last_cleaned_at", "cleaned_by_staff"]` |
| `CLEANED_UNINSPECTED` | `READY_FOR_GUEST` | Supervisor | `["room_status", "last_inspected_at", "inspected_by_staff"]` |
| Any Status | `MAINTENANCE_REQUIRED` | Any Staff | `["room_status", "maintenance_required", "maintenance_notes"]` |

### Maintenance Updates
| Change Type | Trigger | Changed Fields |
|-------------|---------|----------------|
| Flag Maintenance | Staff Report | `["maintenance_required", "maintenance_priority", "maintenance_notes"]` |
| Update Priority | Manager Override | `["maintenance_priority", "maintenance_notes"]` |
| Clear Maintenance | Completion | `["maintenance_required", "maintenance_notes"]` |

### Out-of-Order Changes
| Change Type | Trigger | Changed Fields |
|-------------|---------|----------------|
| Set OOO | System/Manager | `["is_out_of_order", "room_status"]` |
| Clear OOO | System/Manager | `["is_out_of_order", "room_status"]` |

---

## 🛡️ Safety & Reliability

### Transaction Safety
- **Commit-Only Events**: Notifications only sent after successful database commits
- **Atomic Operations**: Room updates and notifications happen atomically
- **Rollback Protection**: Failed transactions don't trigger notifications

### Error Handling
```python
def _safe_pusher_trigger(self, channel: str, event: str, data: dict) -> bool:
    """Safely trigger Pusher event with error handling."""
    try:
        pusher_client.trigger(channel, event, data)
        return True
    except Exception as e:
        self.logger.error(f"Pusher failed: {channel} → {event}: {e}")
        return False
```

### Hotel Scoping
- **Channel Isolation**: Each hotel has separate realtime channels
- **Data Filtering**: Room data automatically scoped to hotel context
- **Permission Boundaries**: Staff can only receive updates for their hotel

---

## 🔍 Monitoring & Debugging

### Logging
```python
# Notification manager logs all events
self.logger.info(f"🏨 Realtime room updated: Room {room.room_number} - {changed_fields}")
```

### Debug Output
```python
# Enable debug printing
print(f"🚨 ACTUALLY SENDING PUSHER EVENT: Channel={channel}, Event={event}")
print(f"✅ Pusher event CONFIRMED SENT: {channel} → {event}")
```

### Common Issues & Solutions

**No Events Received**
- Verify hotel slug in channel subscription
- Check Pusher connection status
- Confirm room belongs to correct hotel

**Partial Data Updates**
- Ensure `changed_fields` parameter is accurate
- Verify room model has latest data before notification
- Check for transaction commit timing

**Performance Issues**
- Monitor notification frequency
- Use `changed_fields` filtering in frontend
- Consider debouncing rapid updates

---

## 🚀 Integration Examples

### Housekeeping Dashboard
```javascript
// Real-time housekeeping dashboard
channel.bind('room_updated', (data) => {
  const { payload } = data;
  
  // Update room status counts
  if (payload.changed_fields.includes('room_status')) {
    updateStatusCounts(payload.room_status, payload.room_number);
  }
  
  // Update maintenance queue
  if (payload.maintenance_required) {
    addToMaintenanceQueue(payload);
  }
  
  // Update cleaning progress
  if (payload.room_status === 'CLEANING_IN_PROGRESS') {
    startCleaningTimer(payload.room_number);
  }
});
```

### Staff Mobile App
```javascript
// Mobile notifications for staff
channel.bind('room_updated', (data) => {
  const { payload } = data;
  
  // Push notification for assigned tasks
  if (payload.maintenance_required && isAssignedToRoom(payload.room_number)) {
    showPushNotification(`Maintenance required in Room ${payload.room_number}`);
  }
  
  // Update task list
  if (payload.room_status === 'READY_FOR_GUEST') {
    completeCleaningTask(payload.room_number);
  }
});
```

### Guest Communication System
```javascript
// Guest room readiness notifications
channel.bind('room_updated', (data) => {
  const { payload } = data;
  
  if (payload.changed_fields.includes('room_status') && payload.room_status === 'READY_FOR_GUEST') {
    const guestBooking = findGuestBooking(payload.room_number);
    if (guestBooking) {
      notifyGuestRoomReady(guestBooking.guest_id, payload.room_number);
    }
  }
});
```

---

## 📈 Performance Considerations

### Event Frequency
- **Batching**: Consider batching rapid successive updates
- **Filtering**: Use `changed_fields` to minimize unnecessary UI updates
- **Debouncing**: Implement client-side debouncing for high-frequency changes

### Payload Optimization
- **Minimal Data**: Only essential room snapshot included
- **Efficient Serialization**: Native Django field access without extra queries
- **Smart Caching**: Room type data included when already available

### Scalability
- **Hotel Isolation**: Each hotel operates on separate channels
- **Connection Management**: Pusher handles connection scaling automatically
- **Event Retention**: No server-side event storage for realtime events

---

## 🎛️ Configuration

### Environment Variables
```env
# Pusher configuration (existing)
PUSHER_APP_ID=your_app_id
PUSHER_KEY=your_key
PUSHER_SECRET=your_secret
PUSHER_CLUSTER=your_cluster
```

### Django Settings
```python
# In settings.py - no additional configuration needed
# Uses existing Pusher setup from notifications app
```

---

## 🔮 Future Enhancements

### Planned Features
- **Batch Room Updates**: Multiple room status changes in single event
- **Historical Event Replay**: Replay missed events on reconnection
- **Custom Event Filtering**: Client-side event filtering by room criteria
- **WebSocket Fallback**: Alternative transport for Pusher failures

### Integration Opportunities
- **Property Management Systems**: Sync with external PMS platforms
- **IoT Sensors**: Room occupancy detection via smart sensors
- **Mobile Maintenance Apps**: Direct integration with maintenance tracking
- **Guest Apps**: Real-time room readiness for guest check-in

---

## 📝 Testing

### Test Coverage
- **5 comprehensive test cases** in `notifications/test_room_realtime.py`
- **Payload structure validation**
- **Channel naming verification**
- **Error handling scenarios**
- **Integration with existing systems**

### Manual Testing
```python
# Test realtime notifications manually
from notifications.notification_manager import NotificationManager
from rooms.models import Room

room = Room.objects.get(room_number="101")
nm = NotificationManager()

# Trigger test notification
nm.realtime_room_updated(
    room=room,
    changed_fields=["room_status"],
    source="test"
)
```

---

## 📋 Summary

The Room Realtime Notifications system provides a robust, scalable solution for real-time room operational updates in HotelMate. Built on the existing Pusher infrastructure, it ensures instant communication of room status changes, maintenance requirements, and housekeeping progress to frontend clients.

**Key Benefits:**
- ✅ **Instant Updates**: Real-time room status synchronization across all clients
- ✅ **Complete Coverage**: All room operational changes trigger notifications  
- ✅ **Transaction Safe**: Events only sent after successful database commits
- ✅ **Hotel Scoped**: Proper multi-tenant isolation and security
- ✅ **Frontend Ready**: Normalized event structure for easy consumption
- ✅ **Change Tracking**: Precise field-level change identification
- ✅ **Error Resilient**: Graceful handling of network and service failures
- ✅ **Performance Optimized**: Minimal payload size and efficient data access

The system is production-ready and seamlessly integrates with the existing housekeeping workflow management system.