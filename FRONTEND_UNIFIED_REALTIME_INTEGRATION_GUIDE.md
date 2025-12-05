# 📡 Frontend Integration Guide: Unified Realtime Backend Architecture

## 🎯 Overview

The backend has been fully modernized with a **unified realtime layer** that matches your frontend's eventBus + domain store architecture. All 5 migrated domains now emit **normalized events** through a centralized NotificationManager.

## 📋 What Changed in Backend

### ✅ Completed Backend Modernization

1. **Centralized NotificationManager** handles all realtime events for 5 domains
2. **Normalized Event Structure** - all events now follow consistent format
3. **Consistent Channel Naming** - standardized channel patterns
4. **Complete Payloads** - no additional API calls needed for store updates
5. **Error Handling** - robust logging without breaking API flows

### 🔧 Migrated Domains

- ✅ **attendance** - Clock in/out, duty status updates
- ✅ **staff_chat** - Message creation, editing, mentions, typing
- ✅ **guest_chat** - Guest messages, staff replies, unread counts
- ✅ **room_service** - Order creation, status updates
- ✅ **booking** - Booking creation, updates, cancellations

## 📡 New Event Structure

All events now use this **normalized format**:

```javascript
{
  "category": "attendance|staff_chat|guest_chat|room_service|booking",
  "type": "event_type",
  "payload": {
    // Complete domain-specific data
    // No additional API fetch needed
  },
  "meta": {
    "hotel_slug": "hotel-killarney",
    "event_id": "uuid4-string",
    "ts": "2025-12-05T14:30:00Z",
    "scope": {
      // Optional targeting info
    }
  }
}
```

## 🔀 Channel Naming (Updated)

### New Standardized Channels

```javascript
// Attendance (hotel-wide)
"hotel-{slug}.attendance"

// Staff Chat (conversation-specific)  
"hotel-{slug}.staff-chat.{conversation_id}"

// Guest Chat (room/pin-specific)
"hotel-{slug}.guest-chat.{room_pin}"

// Room Service (hotel-wide)
"hotel-{slug}.room-service"

// Booking (hotel-wide)
"hotel-{slug}.booking"

// Staff Personal Notifications
"hotel-{slug}.staff-{staff_id}-notifications"
```

### Migration from Old Channels

| Old Channel | New Channel |
|-------------|-------------|
| `{hotel_slug}-attendance` | `hotel-{hotel_slug}.attendance` |
| `{hotel_slug}-staff-chat-{id}` | `hotel-{hotel_slug}.staff-chat.{id}` |
| `{hotel_slug}-room-{number}-chat` | `hotel-{hotel_slug}.guest-chat.{pin}` |
| `{hotel_slug}-room-service` | `hotel-{hotel_slug}.room-service` |
| `{hotel_slug}-bookings` | `hotel-{hotel_slug}.booking` |

## 📋 Event Types by Domain

### 1. Attendance Events

**Channel**: `hotel-{slug}.attendance`

```javascript
// Clock Status Update
{
  "category": "attendance",
  "type": "clock_status_updated",
  "payload": {
    "staff_id": 123,
    "staff_name": "John Doe",
    "user_id": 456,
    "department": "Front Office",
    "department_slug": "front-office", 
    "role": "Receptionist",
    "role_slug": "receptionist",
    "duty_status": "on_duty|off_duty|on_break",
    "action": "clock_in|clock_out|start_break|end_break",
    "timestamp": "2025-12-05T14:30:00Z",
    "source": "facial_recognition|manual|mobile",
    "is_on_duty": true,
    "is_on_break": false,
    "current_status": { /* current status object */ }
  }
}
```

**Frontend Integration**:
```javascript
// Subscribe to attendance updates
eventBus.subscribe('hotel-killarney.attendance', (event) => {
  if (event.category === 'attendance' && event.type === 'clock_status_updated') {
    attendanceStore.updateStaffStatus(event.payload);
  }
});
```

### 2. Staff Chat Events

**Channel**: `hotel-{slug}.staff-chat.{conversation_id}`

```javascript
// Message Created
{
  "category": "staff_chat",
  "type": "message_created",
  "payload": {
    "conversation_id": 789,
    "message_id": 101112,
    "sender_id": 123,
    "sender_name": "John Doe",
    "text": "Hello team!",
    "created_at": "2025-12-05T14:30:00Z",
    "updated_at": "2025-12-05T14:30:00Z",
    "attachments": [],
    "is_system_message": false
  }
}

// Message Edited
{
  "category": "staff_chat", 
  "type": "message_edited",
  "payload": {
    "conversation_id": 789,
    "message_id": 101112,
    "sender_id": 123,
    "sender_name": "John Doe", 
    "text": "Hello team! (edited)",
    "created_at": "2025-12-05T14:30:00Z",
    "updated_at": "2025-12-05T14:35:00Z",
    "edited": true
  }
}

// Message Deleted
{
  "category": "staff_chat",
  "type": "message_deleted", 
  "payload": {
    "conversation_id": 789,
    "message_id": 101112,
    "deleted_at": "2025-12-05T14:40:00Z"
  }
}
```

**Staff Mentions** (Personal Channel): `hotel-{slug}.staff-{staff_id}-notifications`

```javascript
// Staff Mentioned
{
  "category": "staff_chat",
  "type": "staff_mentioned",
  "payload": {
    "conversation_id": 789,
    "message_id": 101112,
    "mentioned_staff_id": 456,
    "mentioned_staff_name": "Jane Smith",
    "sender_id": 123,
    "sender_name": "John Doe",
    "text": "@jane.smith Can you handle this?",
    "created_at": "2025-12-05T14:30:00Z"
  }
}
```

**Typing Indicators** (Ephemeral):
```javascript
// Typing Indicator
{
  "conversation_id": 789,
  "staff_id": 123,
  "staff_name": "John Doe",
  "is_typing": true,
  "timestamp": "2025-12-05T14:30:00Z"
}
```

**Frontend Integration**:
```javascript
// Subscribe to staff chat
eventBus.subscribe('hotel-killarney.staff-chat.789', (event) => {
  if (event.category === 'staff_chat') {
    switch (event.type) {
      case 'message_created':
        staffChatStore.addMessage(event.payload);
        break;
      case 'message_edited':
        staffChatStore.updateMessage(event.payload);
        break;
      case 'message_deleted':
        staffChatStore.removeMessage(event.payload.message_id);
        break;
    }
  }
});

// Subscribe to personal notifications
eventBus.subscribe('hotel-killarney.staff-123-notifications', (event) => {
  if (event.category === 'staff_chat' && event.type === 'staff_mentioned') {
    staffChatStore.addMention(event.payload);
  }
});
```

### 3. Guest Chat Events

**Channel**: `hotel-{slug}.guest-chat.{room_pin}`

```javascript
// Guest Message Created
{
  "category": "guest_chat",
  "type": "guest_message_created",
  "payload": {
    "conversation_id": "room-101",
    "message_id": 201112,
    "sender_role": "guest",
    "sender_id": null,
    "sender_name": "Guest", 
    "text": "Can I get extra towels?",
    "created_at": "2025-12-05T14:30:00Z",
    "room_number": "101",
    "is_staff_reply": false,
    "attachments": [],
    "pin": "1234"
  }
}

// Staff Reply Created  
{
  "category": "guest_chat",
  "type": "staff_message_created", 
  "payload": {
    "conversation_id": "room-101",
    "message_id": 201113,
    "sender_role": "staff",
    "sender_id": 123,
    "sender_name": "John Doe",
    "text": "Of course! We'll send them right up.",
    "created_at": "2025-12-05T14:32:00Z", 
    "room_number": "101",
    "is_staff_reply": true,
    "attachments": [],
    "pin": "1234"
  }
}

// Unread Count Updated
{
  "category": "guest_chat",
  "type": "unread_updated",
  "payload": {
    "room_number": "101", 
    "conversation_id": "room-101",
    "unread_count": 2,
    "updated_at": "2025-12-05T14:30:00Z"
  }
}
```

**Frontend Integration**:
```javascript
// Subscribe to guest chat for room 101
eventBus.subscribe('hotel-killarney.guest-chat.1234', (event) => {
  if (event.category === 'guest_chat') {
    switch (event.type) {
      case 'guest_message_created':
      case 'staff_message_created':
        guestChatStore.addMessage(event.payload);
        break;
      case 'unread_updated':
        guestChatStore.updateUnreadCount(event.payload);
        break;
    }
  }
});
```

### 4. Room Service Events

**Channel**: `hotel-{slug}.room-service`

```javascript
// Order Created
{
  "category": "room_service",
  "type": "order_created",
  "payload": {
    "order_id": 301112,
    "room_number": "101",
    "status": "pending",
    "total_price": 45.50,
    "created_at": "2025-12-05T14:30:00Z",
    "updated_at": "2025-12-05T14:30:00Z", 
    "items": [
      {
        "id": 1,
        "name": "Caesar Salad",
        "quantity": 2,
        "price": 15.00,
        "total": 30.00
      },
      {
        "id": 2, 
        "name": "Garlic Bread",
        "quantity": 1,
        "price": 8.50,
        "total": 8.50
      }
    ],
    "special_instructions": "Extra dressing on the side",
    "estimated_delivery": "2025-12-05T15:00:00Z",
    "priority": "normal"
  }
}

// Order Updated
{
  "category": "room_service",
  "type": "order_updated", 
  "payload": {
    "order_id": 301112,
    "room_number": "101",
    "status": "preparing", // pending -> preparing -> ready -> delivered
    "total_price": 45.50,
    "created_at": "2025-12-05T14:30:00Z",
    "updated_at": "2025-12-05T14:35:00Z",
    "items": [ /* same as above */ ],
    "special_instructions": "Extra dressing on the side",
    "estimated_delivery": "2025-12-05T14:50:00Z"
  }
}
```

**Frontend Integration**:
```javascript
// Subscribe to room service updates
eventBus.subscribe('hotel-killarney.room-service', (event) => {
  if (event.category === 'room_service') {
    switch (event.type) {
      case 'order_created':
        roomServiceStore.addOrder(event.payload);
        break;
      case 'order_updated':
        roomServiceStore.updateOrder(event.payload);
        break;
    }
  }
});
```

### 5. Booking Events

**Channel**: `hotel-{slug}.booking`

```javascript
// Booking Created
{
  "category": "booking",
  "type": "booking_created",
  "payload": {
    "booking_id": "BK-2025-001234",
    "confirmation_number": "CONF-789",
    "guest_name": "Alice Johnson", 
    "guest_email": "alice@example.com",
    "guest_phone": "+1-555-0123",
    "room": "201",
    "room_type": "Deluxe Suite",
    "check_in": "2025-12-10T15:00:00Z", 
    "check_out": "2025-12-13T11:00:00Z",
    "nights": 3,
    "total_price": 450.00,
    "status": "confirmed",
    "created_at": "2025-12-05T14:30:00Z",
    "special_requests": "Late check-in requested",
    "adults": 2,
    "children": 0
  }
}

// Booking Updated  
{
  "category": "booking",
  "type": "booking_updated",
  "payload": {
    "booking_id": "BK-2025-001234",
    "confirmation_number": "CONF-789", 
    "guest_name": "Alice Johnson",
    "room": "203", // Changed room
    "check_in": "2025-12-10T15:00:00Z",
    "check_out": "2025-12-13T11:00:00Z", 
    "status": "confirmed",
    "updated_at": "2025-12-05T14:35:00Z"
  }
}

// Booking Cancelled
{
  "category": "booking", 
  "type": "booking_cancelled",
  "payload": {
    "booking_id": "BK-2025-001234",
    "confirmation_number": "CONF-789",
    "guest_name": "Alice Johnson",
    "room": "203",
    "check_in": "2025-12-10T15:00:00Z",
    "check_out": "2025-12-13T11:00:00Z",
    "status": "cancelled",
    "cancellation_reason": "Guest requested cancellation",
    "cancelled_at": "2025-12-05T14:40:00Z"
  }
}
```

**Frontend Integration**:
```javascript
// Subscribe to booking updates
eventBus.subscribe('hotel-killarney.booking', (event) => {
  if (event.category === 'booking') {
    switch (event.type) {
      case 'booking_created':
        bookingStore.addBooking(event.payload);
        break;
      case 'booking_updated': 
        bookingStore.updateBooking(event.payload);
        break;
      case 'booking_cancelled':
        bookingStore.cancelBooking(event.payload);
        break;
    }
  }
});
```

## 🔧 Implementation Steps

### 1. Update Channel Subscriptions

Replace old channel names with new standardized ones:

```javascript
// OLD
pusher.subscribe('killarney-attendance');
pusher.subscribe('killarney-staff-chat-789');
pusher.subscribe('killarney-room-101-chat');

// NEW
pusher.subscribe('hotel-killarney.attendance');
pusher.subscribe('hotel-killarney.staff-chat.789');  
pusher.subscribe('hotel-killarney.guest-chat.1234');
```

### 2. Update Event Handlers

Modify handlers to use the new normalized structure:

```javascript
// OLD
pusher.bind('clock-status-updated', (data) => {
  // data was direct payload
  attendanceStore.update(data);
});

// NEW
pusher.bind('clock-status-updated', (event) => {
  // event now has category/type/payload/meta structure
  if (event.category === 'attendance' && event.type === 'clock_status_updated') {
    attendanceStore.update(event.payload);
  }
});
```

### 3. Leverage Complete Payloads

The new payloads contain complete data - no additional API calls needed:

```javascript
// OLD - Required additional API call
pusher.bind('new-order', (data) => {
  // data only had order_id, needed to fetch full order
  fetchOrderDetails(data.order_id).then(order => {
    roomServiceStore.addOrder(order);
  });
});

// NEW - Complete data provided
pusher.bind('order-created', (event) => {
  // event.payload has complete order data
  roomServiceStore.addOrder(event.payload);
});
```

### 4. Use Event Metadata

Leverage the meta information for debugging and filtering:

```javascript
pusher.bind('message-created', (event) => {
  console.log(`Event ID: ${event.meta.event_id}`);
  console.log(`Timestamp: ${event.meta.ts}`);
  console.log(`Hotel: ${event.meta.hotel_slug}`);
  
  // Use scope for filtering if needed
  if (event.meta.scope?.staff_id === currentUser.staff_id) {
    // This event is relevant to current user
  }
});
```

## ⚠️ Breaking Changes

### Channel Names
- All channel names now use `hotel-{slug}.domain` format
- Update all Pusher subscriptions accordingly

### Event Structure  
- Events now wrapped in `{category, type, payload, meta}` structure
- Update event handlers to access `event.payload` instead of direct data

### Event Names
- Some event names may have changed (check each domain)
- Payload structure is more comprehensive and consistent

## 🐛 Troubleshooting

### Not Receiving Events
1. Check channel name format: `hotel-{slug}.{domain}`
2. Verify you're listening for correct event names
3. Check console for subscription errors

### Missing Data in Payloads
1. Payloads now contain complete data - check `event.payload`
2. No additional API calls should be needed
3. If data missing, report to backend team

### Performance Issues
1. New events contain more data but eliminate API calls
2. Consider unsubscribing from unused channels
3. Use event filtering in handlers if needed

## 📞 Support

- **Backend Issues**: Contact backend team
- **Event Structure Questions**: Reference this guide
- **Missing Events**: Check backend logs for errors
- **Channel Subscriptions**: Verify channel name format

---

**✅ The backend unified realtime architecture is now live and ready for frontend integration!**

All 5 domains (attendance, staff_chat, guest_chat, room_service, booking) now emit consistent, normalized events with complete payloads through standardized channels.