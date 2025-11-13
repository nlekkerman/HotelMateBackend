# Pusher Implementation Guide: Staff-to-Guest Chat

## Overview
The staff-to-guest chat (`chat` app) uses **the same Pusher approach** as staff-to-staff chat (`staff_chat` app). Both share the same `pusher_client` instance from `chat/utils.py`.

---

## ✅ Confirmed: Same Pusher Configuration

### Backend Setup (Already Done)
```python
# chat/utils.py (shared by both apps)
pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)
```

Both `chat/views.py` (staff-to-guest) and `staff_chat/pusher_utils.py` (staff-to-staff) import and use this **same pusher_client**.

---

## 🎯 Channel Naming Patterns

### Staff-to-Guest Chat Channels

| Channel Type | Pattern | Example | Purpose |
|-------------|---------|---------|---------|
| **Conversation** | `{hotel_slug}-conversation-{conversation_id}-chat` | `hotel-abc-conversation-123-chat` | All messages in a conversation (both staff & guest) |
| **Guest Room** | `{hotel_slug}-room-{room_number}-chat` | `hotel-abc-room-101-chat` | Guest-specific channel for their room |
| **Staff Personal** | `{hotel_slug}-staff-{staff_id}-chat` | `hotel-abc-staff-5-chat` | Individual staff notifications |
| **Deletion** | `{hotel_slug}-room-{room_number}-deletions` | `hotel-abc-room-101-deletions` | Dedicated channel for deletion events |

### Staff-to-Staff Chat Channels

| Channel Type | Pattern | Example | Purpose |
|-------------|---------|---------|---------|
| **Conversation** | `{hotel_slug}-staff-conversation-{conversation_id}` | `hotel-abc-staff-conversation-456` | All messages in staff conversation |
| **Staff Notifications** | `{hotel_slug}-staff-{staff_id}-notifications` | `hotel-abc-staff-5-notifications` | Personal staff notifications |

---

## 📡 Real-Time Events Reference

### Staff-to-Guest Chat Events

#### 1. New Messages

**Event: `new-message`**
```javascript
// Channel: {hotel_slug}-conversation-{conversation_id}-chat
{
  "message_id": 789,
  "conversation_id": 123,
  "sender_type": "guest" | "staff",
  "staff": { ... } | null,
  "message": "Hello!",
  "timestamp": "2024-01-15T10:30:00Z",
  "reply_to": { ... } | null,
  "attachments": [...],
  "is_edited": false,
  "is_deleted": false,
  "read_by_staff": false,
  "read_by_guest": false
}
```

**Specialized Events:**
- `new-guest-message` - Sent to staff personal channels when guest sends message
- `new-staff-message` - Sent to guest room channel when staff replies

#### 2. Message Delivered

**Event: `message-delivered`**
```javascript
// Channel: {hotel_slug}-conversation-{conversation_id}-chat
{
  "message_id": 789,
  "delivered_at": "2024-01-15T10:30:01Z",
  "status": "delivered"
}
```

#### 3. Read Receipts

**Event: `messages-read-by-staff`**
```javascript
// Channel: {hotel_slug}-conversation-{conversation_id}-chat
{
  "message_ids": [789, 790, 791],
  "read_at": "2024-01-15T10:35:00Z",
  "staff_name": "John Smith",
  "conversation_id": 123
}
```

**Event: `messages-read-by-guest`**
```javascript
// Channel: {hotel_slug}-conversation-{conversation_id}-chat
{
  "message_ids": [792, 793],
  "read_at": "2024-01-15T10:36:00Z",
  "room_number": "101"
}
```

#### 4. Staff Assignment

**Event: `staff-assigned`**
```javascript
// Channel: {hotel_slug}-room-{room_number}-chat
{
  "staff_name": "John Smith",
  "staff_role": "Receptionist",
  "conversation_id": 123
}
```

#### 5. Message Deletion

**Event: `message-deleted` / `message-removed`**
```javascript
// Channels: 
// - {hotel_slug}-conversation-{conversation_id}-chat
// - {hotel_slug}-room-{room_number}-chat
// - {hotel_slug}-room-{room_number}-deletions (NEW)
{
  "message_id": 789,
  "hard_delete": true | false,
  "soft_delete": false | true,
  "attachment_ids": [1, 2],
  "deleted_by": "staff" | "guest",
  "original_sender": "staff" | "guest",
  "staff_id": 5,
  "staff_name": "John Smith",
  "timestamp": "2024-01-15T10:40:00Z",
  
  // Only for soft_delete=true:
  "message": { 
    "id": 789,
    "message": "[Message deleted]",
    "is_deleted": true,
    ...
  }
}
```

**Event: `content-deleted`** (on deletion channel)
```javascript
// Channel: {hotel_slug}-room-{room_number}-deletions
// Same payload as message-deleted
```

#### 6. Message Editing

**Event: `message-updated`**
```javascript
// Channel: {hotel_slug}-conversation-{conversation_id}-chat
{
  "id": 789,
  "message": "Updated message text",
  "is_edited": true,
  "edited_at": "2024-01-15T10:45:00Z",
  ...
}
```

#### 7. Attachment Operations

**Event: `attachment-deleted`**
```javascript
// Channels:
// - {hotel_slug}-conversation-{conversation_id}-chat
// - {hotel_slug}-room-{room_number}-deletions
{
  "attachment_id": 42,
  "message_id": 789,
  "deleted_by": "staff" | "guest",
  "original_sender": "staff" | "guest",
  "staff_id": 5,
  "staff_name": "John Smith",
  "timestamp": "2024-01-15T10:50:00Z"
}
```

#### 8. Conversation Status

**Event: `conversation-unread`**
```javascript
// Channel: {hotel_slug}-conversation-{conversation_id}-chat
{
  "conversation_id": 123,
  "room_number": "101"
}
```

**Event: `conversation-read`**
```javascript
// Channel: {hotel_slug}-conversation-{conversation_id}-chat
{
  "conversation_id": 123,
  "room_number": "101"
}
```

---

## 🚀 Frontend Implementation Instructions

### 1. Install Pusher Client
```bash
npm install pusher-js
# or
yarn add pusher-js
```

### 2. Initialize Pusher (React Example)

```javascript
// utils/pusher.js
import Pusher from 'pusher-js';

// Get these from your environment variables
const pusher = new Pusher(process.env.REACT_APP_PUSHER_KEY, {
  cluster: process.env.REACT_APP_PUSHER_CLUSTER,
  encrypted: true,
  authEndpoint: '/api/pusher/auth', // If using private channels
});

export default pusher;
```

### 3. Subscribe to Channels

#### For Guest Chat View (QR Code Entry)
```javascript
import pusher from './utils/pusher';
import { useEffect, useState } from 'react';

function GuestChatView({ hotelSlug, roomNumber, conversationId }) {
  const [messages, setMessages] = useState([]);
  
  useEffect(() => {
    // Subscribe to room channel (for staff messages)
    const guestChannel = pusher.subscribe(
      `${hotelSlug}-room-${roomNumber}-chat`
    );
    
    // Subscribe to conversation channel (for all events)
    const conversationChannel = pusher.subscribe(
      `${hotelSlug}-conversation-${conversationId}-chat`
    );
    
    // Subscribe to deletion channel (NEW - for reliable deletion handling)
    const deletionChannel = pusher.subscribe(
      `${hotelSlug}-room-${roomNumber}-deletions`
    );
    
    // Listen for new messages from staff
    guestChannel.bind('new-staff-message', (data) => {
      console.log('Staff sent message:', data);
      setMessages(prev => [...prev, data]);
      
      // Show notification if chat is not focused
      if (document.hidden) {
        showNotification('New message from hotel staff', data.message);
      }
    });
    
    // Listen for your own messages echoed back
    guestChannel.bind('new-message', (data) => {
      if (data.sender_type === 'guest') {
        console.log('Your message confirmed:', data);
        updateMessageStatus(data.message_id, 'delivered');
      }
    });
    
    // Listen for read receipts
    conversationChannel.bind('messages-read-by-staff', (data) => {
      console.log('Staff read your messages:', data.message_ids);
      markMessagesAsRead(data.message_ids);
    });
    
    // Listen for staff assignment
    guestChannel.bind('staff-assigned', (data) => {
      console.log('Staff assigned:', data.staff_name);
      showNotification(`${data.staff_name} is now assisting you`);
      updateCurrentStaff(data);
    });
    
    // Listen for message deletions (primary)
    conversationChannel.bind('message-deleted', (data) => {
      handleMessageDeletion(data);
    });
    
    // Listen for message deletions (dedicated channel - more reliable)
    deletionChannel.bind('content-deleted', (data) => {
      console.log('⚠️ Content deleted (via dedicated channel):', data);
      handleMessageDeletion(data);
    });
    
    // Alternative deletion event name (for compatibility)
    conversationChannel.bind('message-removed', (data) => {
      handleMessageDeletion(data);
    });
    
    // Listen for attachment deletions
    conversationChannel.bind('attachment-deleted', (data) => {
      console.log('Attachment deleted:', data);
      removeAttachmentFromMessage(data.message_id, data.attachment_id);
    });
    
    deletionChannel.bind('attachment-deleted', (data) => {
      console.log('⚠️ Attachment deleted (via dedicated channel):', data);
      removeAttachmentFromMessage(data.message_id, data.attachment_id);
    });
    
    // Listen for message edits
    conversationChannel.bind('message-updated', (data) => {
      console.log('Message edited:', data);
      updateMessage(data);
    });
    
    // Cleanup
    return () => {
      guestChannel.unbind_all();
      conversationChannel.unbind_all();
      deletionChannel.unbind_all();
      pusher.unsubscribe(`${hotelSlug}-room-${roomNumber}-chat`);
      pusher.unsubscribe(`${hotelSlug}-conversation-${conversationId}-chat`);
      pusher.unsubscribe(`${hotelSlug}-room-${roomNumber}-deletions`);
    };
  }, [hotelSlug, roomNumber, conversationId]);
  
  const handleMessageDeletion = (data) => {
    if (data.hard_delete) {
      // Remove message completely from UI
      removeMessage(data.message_id);
      
      // Also remove all attachments
      if (data.attachment_ids?.length > 0) {
        data.attachment_ids.forEach(attachmentId => {
          removeAttachmentFromMessage(data.message_id, attachmentId);
        });
      }
    } else {
      // Soft delete - update message to show "[Message deleted]"
      updateMessage(data.message);
    }
  };
  
  // ... rest of component
}
```

#### For Staff Chat View
```javascript
function StaffChatView({ hotelSlug, conversationId, staffId }) {
  const [messages, setMessages] = useState([]);
  
  useEffect(() => {
    // Subscribe to conversation channel
    const conversationChannel = pusher.subscribe(
      `${hotelSlug}-conversation-${conversationId}-chat`
    );
    
    // Subscribe to personal notification channel
    const notificationChannel = pusher.subscribe(
      `${hotelSlug}-staff-${staffId}-chat`
    );
    
    // Listen for new messages from guest
    notificationChannel.bind('new-guest-message', (data) => {
      console.log('Guest sent message:', data);
      
      // Only add if it's for THIS conversation
      if (data.conversation_id === conversationId) {
        setMessages(prev => [...prev, data]);
      }
      
      // Show notification
      showNotification(`New message from Room ${data.room_number}`, data.message);
      
      // Update badge count
      incrementUnreadCount();
    });
    
    // Listen for all messages in conversation
    conversationChannel.bind('new-message', (data) => {
      console.log('New message in conversation:', data);
      setMessages(prev => [...prev, data]);
    });
    
    // Listen for read receipts
    conversationChannel.bind('messages-read-by-guest', (data) => {
      console.log('Guest read your messages:', data.message_ids);
      markMessagesAsRead(data.message_ids);
    });
    
    // Listen for message status updates
    conversationChannel.bind('message-delivered', (data) => {
      updateMessageStatus(data.message_id, 'delivered');
    });
    
    // Listen for deletions
    conversationChannel.bind('message-deleted', (data) => {
      if (data.hard_delete) {
        removeMessage(data.message_id);
      } else {
        updateMessage(data.message);
      }
    });
    
    // Alternative deletion event
    conversationChannel.bind('message-removed', (data) => {
      if (data.hard_delete) {
        removeMessage(data.message_id);
      } else {
        updateMessage(data.message);
      }
    });
    
    // Listen for attachment deletions
    conversationChannel.bind('attachment-deleted', (data) => {
      removeAttachmentFromMessage(data.message_id, data.attachment_id);
    });
    
    // Listen for edits
    conversationChannel.bind('message-updated', (data) => {
      updateMessage(data);
    });
    
    // Listen for conversation status changes
    conversationChannel.bind('conversation-unread', (data) => {
      markConversationUnread(data.conversation_id);
    });
    
    conversationChannel.bind('conversation-read', (data) => {
      markConversationRead(data.conversation_id);
    });
    
    // Cleanup
    return () => {
      conversationChannel.unbind_all();
      notificationChannel.unbind_all();
      pusher.unsubscribe(`${hotelSlug}-conversation-${conversationId}-chat`);
      pusher.unsubscribe(`${hotelSlug}-staff-${staffId}-chat`);
    };
  }, [hotelSlug, conversationId, staffId]);
  
  // ... rest of component
}
```

### 4. Handle Deletion Events (IMPORTANT)

```javascript
// utils/messageHandlers.js

/**
 * Unified deletion handler for both hard and soft deletes
 * Works with both 'message-deleted' and 'message-removed' events
 */
export const handleMessageDeletion = (data, setMessages) => {
  console.log('🗑️ Handling deletion:', data);
  
  if (data.hard_delete) {
    // HARD DELETE: Remove message completely
    setMessages(prevMessages => 
      prevMessages.filter(msg => msg.id !== data.message_id)
    );
    
    // Also remove any associated attachments
    if (data.attachment_ids?.length > 0) {
      console.log(`Removed ${data.attachment_ids.length} attachments`);
    }
    
    console.log(`✅ Hard deleted message ${data.message_id}`);
  } else {
    // SOFT DELETE: Update message to show deletion text
    setMessages(prevMessages => 
      prevMessages.map(msg => 
        msg.id === data.message_id
          ? {
              ...msg,
              message: data.message?.message || '[Message deleted]',
              is_deleted: true,
              deleted_at: data.timestamp,
              attachments: [] // Clear attachments
            }
          : msg
      )
    );
    
    console.log(`✅ Soft deleted message ${data.message_id}`);
  }
  
  // Show notification if deletion was by another user
  const currentUserType = getCurrentUserType(); // 'staff' or 'guest'
  if (data.deleted_by !== currentUserType) {
    const deleter = data.staff_name || 'Staff member';
    showToast(`${deleter} deleted a message`);
  }
};

/**
 * Handle attachment deletion
 */
export const handleAttachmentDeletion = (data, setMessages) => {
  console.log('📎 Handling attachment deletion:', data);
  
  setMessages(prevMessages => 
    prevMessages.map(msg => {
      if (msg.id === data.message_id) {
        const updatedAttachments = msg.attachments.filter(
          att => att.id !== data.attachment_id
        );
        
        return {
          ...msg,
          attachments: updatedAttachments
        };
      }
      return msg;
    })
  );
  
  console.log(`✅ Removed attachment ${data.attachment_id} from message ${data.message_id}`);
};

/**
 * Subscribe to ALL deletion events for maximum reliability
 */
export const subscribeToDeletions = (
  pusher,
  hotelSlug,
  roomNumber,
  conversationId,
  handlers
) => {
  // 1. Conversation channel (primary)
  const conversationChannel = pusher.subscribe(
    `${hotelSlug}-conversation-${conversationId}-chat`
  );
  
  // 2. Deletion channel (dedicated - most reliable)
  const deletionChannel = pusher.subscribe(
    `${hotelSlug}-room-${roomNumber}-deletions`
  );
  
  // Bind to all possible deletion event names
  const events = ['message-deleted', 'message-removed', 'content-deleted'];
  
  events.forEach(eventName => {
    conversationChannel.bind(eventName, handlers.onMessageDelete);
    if (deletionChannel) {
      deletionChannel.bind(eventName, handlers.onMessageDelete);
    }
  });
  
  // Attachment deletions
  conversationChannel.bind('attachment-deleted', handlers.onAttachmentDelete);
  if (deletionChannel) {
    deletionChannel.bind('attachment-deleted', handlers.onAttachmentDelete);
  }
  
  return () => {
    conversationChannel.unbind_all();
    if (deletionChannel) deletionChannel.unbind_all();
    pusher.unsubscribe(`${hotelSlug}-conversation-${conversationId}-chat`);
    pusher.unsubscribe(`${hotelSlug}-room-${roomNumber}-deletions`);
  };
};
```

### 5. Mark Messages as Read When Opening Conversation

#### Guest Side
```javascript
const markAsRead = async (conversationId) => {
  try {
    await axios.post(
      `/api/chat/${hotelSlug}/conversation/${conversationId}/mark-as-read/`
    );
    console.log('Messages marked as read by guest');
  } catch (error) {
    console.error('Failed to mark as read:', error);
  }
};

// Call when conversation is opened or messages are visible
useEffect(() => {
  if (conversationId && isVisible) {
    markAsRead(conversationId);
  }
}, [conversationId, isVisible]);
```

#### Staff Side
```javascript
const markAsRead = async (conversationId) => {
  try {
    await axios.post(
      `/api/chat/${hotelSlug}/conversation/${conversationId}/mark-as-read/`,
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    console.log('Messages marked as read by staff');
  } catch (error) {
    console.error('Failed to mark as read:', error);
  }
};
```

---

## 🔐 Security Notes

1. **Guest Access**: Guests access chat via QR code + PIN validation (no auth token needed)
2. **Staff Access**: Staff must be authenticated (`IsAuthenticated` permission)
3. **Channel Privacy**: Consider using Pusher private channels for sensitive conversations
4. **FCM Tokens**: Both staff and guests can receive push notifications when app is closed

---

## 🧪 Testing Pusher Events

### Test Endpoint for Deletion
```bash
# Test deletion broadcast to guest channel
POST /api/chat/test/{hotel_slug}/room/{room_number}/test-deletion/
{
  "message_id": 999,
  "hard_delete": true
}
```

### Manual Testing Checklist
- [ ] Guest sends message → Staff receives notification
- [ ] Staff replies → Guest sees message instantly
- [ ] Staff opens conversation → Guest messages marked as read
- [ ] Guest opens chat → Staff messages marked as read
- [ ] Staff deletes message → Guest sees deletion
- [ ] Guest deletes message → Staff sees deletion
- [ ] Staff edits message → Guest sees edit
- [ ] File upload → Both see attachment instantly
- [ ] Staff assigned → Guest sees staff name update

---

## 📊 Key Differences Between Chat Types

| Feature | Staff-to-Guest | Staff-to-Staff |
|---------|---------------|----------------|
| Authentication | Guest: PIN, Staff: Token | Both: Token |
| Channel Pattern | `conversation-{id}-chat` | `staff-conversation-{id}` |
| Notification Channel | `staff-{id}-chat` | `staff-{id}-notifications` |
| Read Receipts | Per user type (staff/guest) | Per individual staff |
| FCM Push | Both supported | Staff only |
| Session Management | GuestChatSession model | Not needed |

---

## 🚨 Common Pitfalls to Avoid

1. **Don't forget to unsubscribe**: Always unbind and unsubscribe in cleanup
2. **Handle both event names**: Listen for both `message-deleted` AND `message-removed`
3. **Use the deletion channel**: Subscribe to `{hotel}-room-{number}-deletions` for most reliable deletion events
4. **Check conversation ID**: When receiving notifications, verify it matches current conversation
5. **Duplicate prevention**: Use message IDs to prevent showing duplicates
6. **Connection status**: Monitor Pusher connection state and show UI indicator
7. **Rate limiting**: Backend has rate limiting on API endpoints

---

## 📞 Support

If you encounter issues:
1. Check browser console for Pusher connection logs
2. Verify environment variables are set correctly
3. Test with Pusher Debug Console (https://dashboard.pusher.com)
4. Check backend logs for Pusher trigger failures
5. Ensure correct channel names (typos cause silent failures)

---

## 🎯 Summary for Frontend Team

**YES, it's the same Pusher approach!** 

Both staff-to-guest and staff-to-staff chat use:
- ✅ Same `pusher_client` instance
- ✅ Same Pusher configuration
- ✅ Similar channel patterns
- ✅ Similar event types
- ✅ Real-time message delivery
- ✅ Read receipts
- ✅ Typing indicators (if implemented)
- ✅ Message deletion/editing
- ✅ File attachments

**Main differences:**
- Different channel naming conventions
- Guest chat has room-specific channels
- Staff chat has personal notification channels
- Guest chat requires PIN validation
- Guest chat supports anonymous sessions

**Frontend Implementation:**
1. Install `pusher-js`
2. Initialize with Pusher credentials
3. Subscribe to relevant channels based on chat type
4. Bind to event handlers
5. Clean up on unmount

That's it! The patterns are nearly identical between both chat types. 🚀
