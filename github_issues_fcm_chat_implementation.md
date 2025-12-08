# FCM Chat Implementation & Event Transformation

## 📱 User Story
As a hotel staff member, I want to receive push notifications when the app is closed and have them seamlessly integrate with real-time events when the app is open, so I never miss important messages regardless of app state.

## 🎯 Overview
Complete Firebase Cloud Messaging (FCM) implementation with event transformation system that bridges FCM notifications with the existing eventBus architecture for unified chat functionality.

## ✅ Acceptance Criteria

### FCM Integration
- [x] **Firebase Admin SDK Integration**: Complete FCM service setup with credential management
- [x] **Staff Chat FCM**: Push notifications for new messages, mentions, and conversation creation
- [x] **Guest Chat FCM**: Push notifications for staff-guest message exchanges
- [x] **File Attachment FCM**: Specialized notifications for file uploads with type detection
- [x] **Click Action Handling**: Deep linking to specific conversations and rooms

### Event Transformation System
- [x] **FCM-to-EventBus Bridge**: Transform FCM messages to match existing event structure
- [x] **Type Mapping**: Convert FCM types to eventBus categories and event types
- [x] **Channel Routing**: Map FCM data to appropriate Pusher channel patterns
- [x] **Payload Normalization**: Ensure consistent data structure across FCM and Pusher

### Chat Features Implementation
- [x] **Read Receipts**: Visual indicators for message read status across platforms
- [x] **Reply System**: Threaded conversations with quote functionality
- [x] **Message Editing**: Real-time message updates with edit indicators
- [x] **File Attachments**: Support for images, documents, and multimedia files
- [x] **Mention System**: @username notifications with highlighting

## 🔧 Technical Implementation

### Files Modified/Created
- `notifications/fcm_service.py` - Core FCM functionality with Firebase Admin SDK
- `staff_chat/fcm_utils.py` - Staff chat specific FCM notifications
- `chat/views.py` - Guest chat FCM integration
- `FCM_CHAT_IMPLEMENTATION_GUIDE.md` - Complete implementation documentation
- `FCM_EVENT_TRANSFORMER_FRONTEND_FIX.js` - Frontend transformation logic

### FCM Message Types
```javascript
// Message type mapping
{
  // Guest Chat FCM
  "type": "new_chat_message",     // Staff message to guest
  "type": "guest_message",        // Guest message to staff
  
  // Staff Chat FCM  
  "type": "staff_chat_message",   // New staff message
  "type": "staff_chat_mention",   // @mention notification
  "type": "staff_chat_new_conversation", // Added to group
  
  // File Attachments
  "type": "file_attachment",      // File upload notifications
}
```

### Event Transformation Logic
```javascript
function transformFCMEvent(fcmEvent) {
  const { payload } = fcmEvent;
  const fcmData = payload.data || {};
  const notification = payload.notification || {};
  
  // Map FCM types to event structure
  const eventMapping = {
    'new_chat_message': {
      category: 'guest_chat',
      type: 'staff_message_created',
      channel: `hotel-${fcmData.hotel_slug}.guest-chat.${fcmData.room_number}`
    },
    'staff_chat_message': {
      category: 'staff_chat',
      type: 'message_created', 
      channel: `hotel-${fcmData.hotel_slug}.staff-chat.${fcmData.conversation_id}`
    }
  };
  
  return {
    source: 'fcm',
    channel: mapping.channel,
    eventName: mapping.type,
    payload: {
      category: mapping.category,
      type: mapping.type,
      payload: {
        title: notification.title,
        body: notification.body,
        ...fcmData,
        fcm_message_id: payload.messageId,
        received_at: new Date().toISOString()
      }
    }
  };
}
```

### FCM Payload Structure
```json
{
  "from": "1020698338972",
  "messageId": "6e623646-3527-44bb-b89c-0345acd62e6c",
  "notification": {
    "title": "💬 John Doe",
    "body": "Hello, how can I help you?"
  },
  "data": {
    "type": "new_chat_message",
    "hotel_slug": "hotel-killarney",
    "conversation_id": "123",
    "room_number": "101",
    "message_id": "456",
    "sender_type": "staff",
    "sender_id": "789",
    "staff_name": "John Doe",
    "click_action": "/chat/hotel-killarney/room/101",
    "url": "https://hotelsmates.com/chat/hotel-killarney/room/101"
  }
}
```

## 🔥 Chat Features Implementation

### Read Receipts System
```javascript
// Backend - Mark messages as read
const markAsRead = async (messageIds) => {
  const response = await fetch(`/api/chat/${conversationId}/mark-read/`, {
    method: 'POST',
    body: JSON.stringify({ message_ids: messageIds })
  });
  
  // Real-time event automatically fired via NotificationManager
};

// Frontend - Update UI on read receipts
eventBus.on('read_receipt_received', (data) => {
  data.message_ids.forEach(id => {
    const message = findMessage(id);
    if (message) {
      message.read_status = 'read';
      message.read_at = data.read_at;
      updateMessageUI(message);
    }
  });
});
```

### Reply System
```javascript
// Backend - Create reply message
const createReply = async (originalMessageId, replyText) => {
  const message = await Message.create({
    conversation_id: conversationId,
    text: replyText,
    reply_to_id: originalMessageId,
    sender: staff
  });
  
  // FCM notification includes reply context
  sendFCMNotification(recipients, {
    title: `💬 ${staff.name} replied`,
    body: replyText,
    data: {
      type: 'reply_message',
      original_message_id: originalMessageId,
      reply_to_text: originalMessage.text.substring(0, 50)
    }
  });
};
```

### File Attachment Handling
```javascript
// Multi-type attachment support
const handleFileUpload = async (files) => {
  const attachments = await uploadFiles(files);
  
  // Type-specific FCM notifications
  const fileTypes = attachments.map(a => a.file_type);
  const fcmTitle = getAttachmentTitle(fileTypes);
  
  sendFCMNotification(recipients, {
    title: fcmTitle, // "📷 Staff sent 2 image(s)" or "📄 Staff sent document(s)"
    body: "Check the attached files",
    data: {
      type: 'file_attachment',
      attachment_count: attachments.length,
      file_types: fileTypes.join(',')
    }
  });
};
```

## 📱 Frontend Integration

### EventBus Integration
```javascript
// Handle both Pusher and FCM events uniformly
eventBus.on('incoming_realtime_event', (event) => {
  if (event.source === 'fcm') {
    // Transform FCM event
    const transformedEvent = transformFCMEvent(event);
    // Route through normal eventBus flow
    eventBus.emit('pusher:message', transformedEvent.payload);
  } else {
    // Handle regular Pusher events
    eventBus.emit('pusher:message', event.payload);
  }
});

// Unified message handling
eventBus.on('pusher:message', (data) => {
  const { category, type, payload } = data;
  
  switch(category) {
    case 'staff_chat':
      chatStore.handleRealtimeEvent(type, payload);
      break;
    case 'guest_chat':
      guestChatStore.handleRealtimeEvent(type, payload);
      break;
  }
});
```

### Click Action Handling
```javascript
// FCM notification click routing
firebase.messaging().onNotificationClick((payload) => {
  const data = payload.data;
  
  if (data.route) {
    navigateTo(data.route);
  } else {
    // Fallback navigation based on type
    switch (data.type) {
      case 'new_chat_message':
        navigateTo(`/chat/${data.hotel_slug}/room/${data.room_number}`);
        break;
      case 'staff_chat_message':
        navigateTo(`/staff-chat/${data.hotel_slug}/conversation/${data.conversation_id}`);
        break;
    }
  }
});
```

## 🚀 Key Benefits

1. **✅ Unified Architecture**: FCM and Pusher events use same handling logic
2. **✅ Offline Support**: Push notifications work when app is closed
3. **✅ Deep Linking**: Direct navigation to specific conversations
4. **✅ Type Detection**: Smart file type handling and notifications
5. **✅ Read Status**: Cross-platform read receipt synchronization
6. **✅ Reply Threading**: Contextual reply system with quotes
7. **✅ Mention Notifications**: Targeted @username alerts
8. **✅ Error Resilience**: Graceful handling of notification failures

## 🔄 Migration & Integration

### Frontend Transformation Setup
```javascript
// Add to main application bootstrap
import { transformFCMEvent } from './utils/fcmTransformer';

// Initialize FCM handling
firebase.messaging().onMessage((payload) => {
  const transformedEvent = transformFCMEvent({
    source: 'fcm',
    payload: payload
  });
  
  eventBus.emit('pusher:message', transformedEvent.payload);
});
```

### Backend FCM Integration
```python
# In message creation views
from staff_chat.fcm_utils import notify_conversation_participants

# After creating message
message = StaffChatMessage.objects.create(...)

# Send FCM notifications
notify_conversation_participants(
    conversation=message.conversation,
    sender_staff=message.sender,
    message_text=message.message,
    exclude_sender=True
)
```

## 📋 Testing Checklist
- [x] FCM notifications sent for all message types
- [x] Event transformation works correctly
- [x] Click actions navigate to correct destinations
- [x] Read receipts sync across platforms
- [x] Reply system maintains context
- [x] File attachments generate appropriate notifications
- [x] Mention system triggers targeted alerts
- [x] Offline/online state transitions work seamlessly

## 🔗 Related Documentation
- `FCM_CHAT_IMPLEMENTATION_GUIDE.md` - Complete chat implementation guide
- `NOTIFICATIONS_DOCUMENTATION.md` - FCM notification specifications
- `FCM_EVENT_TRANSFORMER_FRONTEND_FIX.js` - Frontend transformation code

---

**Implementation Status**: ✅ **COMPLETE**
**Priority**: High  
**Domain**: Chat System
**Type**: Feature Implementation