# Guest Chat - Real-Time Message Deletion

## Overview
This document describes the real-time message deletion feature for guest chat windows. When staff deletes a message, guests see it removed instantly via Pusher events.

## Backend Implementation

### Pusher Channels Used
When a message is deleted, the backend broadcasts to **3 channels**:

1. **Conversation Channel**: `{hotel_slug}-conversation-{conversation_id}-chat`
   - For all participants (staff and guests viewing the conversation)

2. **Room Channel**: `{hotel_slug}-room-{room_number}-chat` ⭐ **NEW**
   - For the guest in that specific room
   - Critical for guest real-time updates

3. **Staff Channels**: `{hotel_slug}-staff-{staff_id}-chat`
   - Individual channels for each staff member

### Events Broadcast

#### Event Names
- `message-deleted` - Primary event name
- `message-removed` - Alias for backward compatibility

Both events are sent to ensure compatibility with different frontend implementations.

#### Event Payload

**Hard Delete:**
```json
{
  "message_id": 123,
  "hard_delete": true
}
```

**Soft Delete:**
```json
{
  "message_id": 123,
  "hard_delete": false,
  "message": {
    "id": 123,
    "message": "[Message deleted]",
    "is_deleted": true,
    "deleted_at": "2025-11-04T10:30:00Z",
    // ... other message fields
  }
}
```

## Frontend Integration (Guest Chat)

### 1. Subscribe to Room Channel

```javascript
// Guest chat initialization
const hotelSlug = 'hotel-killarney';
const roomNumber = '101';
const roomChannel = `${hotelSlug}-room-${roomNumber}-chat`;

const channel = pusher.subscribe(roomChannel);
```

### 2. Listen for Deletion Events

```javascript
// Primary event handler
channel.bind('message-deleted', (data) => {
  console.log('🗑️ Message deleted:', data);
  
  if (data.hard_delete) {
    // Hard delete - remove message completely from UI
    removeMessageFromUI(data.message_id);
  } else {
    // Soft delete - update message to show as deleted
    updateMessageAsDeleted(data.message_id, data.message);
  }
});

// Alias event (for compatibility)
channel.bind('message-removed', (data) => {
  console.log('🗑️ Message removed:', data);
  // Same handling as message-deleted
  if (data.hard_delete) {
    removeMessageFromUI(data.message_id);
  } else {
    updateMessageAsDeleted(data.message_id, data.message);
  }
});
```

### 3. Update UI Functions

#### Remove Message (Hard Delete)
```javascript
function removeMessageFromUI(messageId) {
  setMessages(prevMessages => 
    prevMessages.filter(msg => msg.id !== messageId)
  );
  
  console.log(`✅ Removed message ${messageId} from UI`);
}
```

#### Update Message (Soft Delete)
```javascript
function updateMessageAsDeleted(messageId, updatedMessage) {
  setMessages(prevMessages =>
    prevMessages.map(msg =>
      msg.id === messageId
        ? {
            ...msg,
            message: '[Message deleted]',
            is_deleted: true,
            deleted_at: updatedMessage.deleted_at,
            attachments: [] // Clear attachments
          }
        : msg
    )
  );
  
  console.log(`✅ Updated message ${messageId} as deleted`);
}
```

### 4. Complete React Hook Example

```javascript
import { useEffect } from 'react';
import pusher from './pusherConfig';

export function useGuestChatDeletion(hotelSlug, roomNumber, setMessages) {
  useEffect(() => {
    const roomChannel = `${hotelSlug}-room-${roomNumber}-chat`;
    const channel = pusher.subscribe(roomChannel);
    
    console.log(`🔔 Listening for deletions on: ${roomChannel}`);
    
    const handleMessageDeleted = (data) => {
      console.log('🗑️ Message deletion received:', data);
      
      if (data.hard_delete) {
        // Remove completely
        setMessages(prev => prev.filter(msg => msg.id !== data.message_id));
      } else {
        // Mark as deleted
        setMessages(prev =>
          prev.map(msg =>
            msg.id === data.message_id
              ? { ...msg, ...data.message, is_deleted: true }
              : msg
          )
        );
      }
    };
    
    // Bind both event names
    channel.bind('message-deleted', handleMessageDeleted);
    channel.bind('message-removed', handleMessageDeleted);
    
    // Cleanup
    return () => {
      channel.unbind('message-deleted', handleMessageDeleted);
      channel.unbind('message-removed', handleMessageDeleted);
      pusher.unsubscribe(roomChannel);
    };
  }, [hotelSlug, roomNumber, setMessages]);
}
```

### 5. Usage in Component

```javascript
function GuestChatWindow({ hotelSlug, roomNumber }) {
  const [messages, setMessages] = useState([]);
  
  // Subscribe to deletion events
  useGuestChatDeletion(hotelSlug, roomNumber, setMessages);
  
  return (
    <div className="chat-window">
      {messages.map(msg => (
        <Message 
          key={msg.id} 
          message={msg}
          isDeleted={msg.is_deleted}
        />
      ))}
    </div>
  );
}
```

## Testing

### Backend Console Output
When a message is deleted, you should see:
```
🗑️ DELETE REQUEST | message_id=123 | hotel=hotel-killarney | room=101
🗑️ CHANNELS | conversation=hotel-killarney-conversation-50-chat | guest=hotel-killarney-room-101-chat
🗑️ ROOM CHANNEL | hotel-killarney-room-101-chat
🗑️ SENDER | type=staff | is_staff=True | hard_delete=True
📡 BROADCASTING TO ROOM CHANNEL: hotel-killarney-room-101-chat
📦 PAYLOAD: {'message_id': 123, 'hard_delete': True}
✅ SENT message-deleted to hotel-killarney-room-101-chat
✅ SENT message-removed to hotel-killarney-room-101-chat
```

### Frontend Console Output
When guest receives deletion:
```
🔔 [GUEST PUSHER] WAITING FOR DELETION EVENTS on channel: hotel-killarney-room-101-chat
🗑️ Message deletion received: {message_id: 123, hard_delete: true}
✅ Removed message 123 from UI
```

## Troubleshooting

### Guest Not Seeing Deletions

1. **Check channel subscription**:
   ```javascript
   console.log('Subscribed to:', pusher.allChannels());
   // Should include: hotel-killarney-room-101-chat
   ```

2. **Verify event binding**:
   ```javascript
   channel.bind_global((event, data) => {
     console.log('All events:', event, data);
   });
   ```

3. **Check backend logs** - Ensure broadcasts are being sent

4. **Verify Pusher credentials** - App ID, Key, Secret must match

### Message Not Removed from UI

1. **Check message ID match**:
   ```javascript
   console.log('Looking for message:', data.message_id);
   console.log('Current messages:', messages.map(m => m.id));
   ```

2. **Verify state update**:
   ```javascript
   setMessages(prev => {
     console.log('Before:', prev.length);
     const updated = prev.filter(msg => msg.id !== data.message_id);
     console.log('After:', updated.length);
     return updated;
   });
   ```

3. **Check for duplicate subscriptions** - Multiple subscriptions can cause issues

## Related Files

- Backend: `chat/views.py` - `delete_message` function
- Backend: `chat/models.py` - `RoomMessage.soft_delete()` method
- Frontend: `useGuestChatPusher.js` - Pusher subscription hook
- Frontend: `GuestChatWindow.jsx` - Main guest chat component

## Channel Summary

| Channel | Purpose | Events |
|---------|---------|--------|
| `{hotel}-room-{room_number}-chat` | Guest-specific channel | `message-deleted`, `message-removed`, `new-staff-message` |
| `{hotel}-conversation-{conv_id}-chat` | Conversation-wide channel | `new-message`, `message-deleted`, `message-updated` |
| `{hotel}-staff-{staff_id}-chat` | Staff-specific channel | `new-guest-message`, `message-deleted` |

## Version History

- **v1.0** (Nov 4, 2025) - Initial implementation with room channel broadcasts for guest deletion events
