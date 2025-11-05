# Chat Channel Architecture

## Overview
This document describes the Pusher channel architecture for the hotel chat system, including the new dedicated deletion channels introduced to fix guest UI update issues.

## Channel Types

### 1. Conversation Channel
**Format:** `{hotel_slug}-conversation-{conversation_id}-chat`

**Purpose:** General conversation events for all participants (staff and guests)

**Events:**
- `new-message` - New message added to conversation
- `message-updated` - Message edited
- `message-deleted` - Message soft/hard deleted (legacy)
- `message-removed` - Message deleted (alias)
- `messages-read-by-staff` - Staff read guest messages
- `messages-read-by-guest` - Guest read staff messages
- `conversation-unread` - Conversation marked as unread
- `conversation-read` - Conversation marked as read
- `attachment-deleted` - File attachment removed (legacy)

**Used By:** All participants viewing the conversation

---

### 2. Room Channel (Guest-specific)
**Format:** `{hotel_slug}-room-{room_number}-chat`

**Purpose:** Real-time updates for guests in a specific room

**Events:**
- `new-message` - Guest's own messages echoed back
- `new-staff-message` - Staff sent a message to the guest
- `message-delivered` - Message delivery confirmation
- `staff-assigned` - New staff member assigned to handle chat
- `message-deleted` - Message deletion (legacy)
- `message-removed` - Message deletion (alias)

**Used By:** Guest UI in specific room

---

### 3. 🆕 Deletion Channel (NEW)
**Format:** `{hotel_slug}-room-{room_number}-deletions`

**Purpose:** **Dedicated channel for content deletion events to ensure reliable real-time updates**

**Events:**
- `content-deleted` - Message or content deleted (message_id, hard_delete, attachment_ids)
- `attachment-deleted` - File attachment removed (attachment_id, message_id)

**Used By:** Guest UI for immediate deletion updates

**Why Created:**
- Previous implementation used shared channels causing guests not to see deletions
- Dedicated channel ensures clear event handling
- Prevents subscription conflicts
- Better separation of concerns

**Payload Example:**
```json
{
  "message_id": 123,
  "hard_delete": true,
  "attachment_ids": [456, 457],
  "deleted_by": "staff",
  "original_sender": "guest",
  "staff_id": 42,
  "staff_name": "John Smith"
}
```

**Fields:**
- `message_id` - ID of the deleted message
- `hard_delete` - true = remove completely, false = soft delete with "[Message deleted]"
- `attachment_ids` - Array of attachment IDs to remove from UI
- `deleted_by` - "staff" or "guest" (who performed the deletion)
- `original_sender` - "staff" or "guest" (who originally sent the message)
- `staff_id` - ID of staff who deleted (null if guest deleted)
- `staff_name` - Name of staff who deleted (null if guest deleted)

---

### 4. Staff Individual Channel
**Format:** `{hotel_slug}-staff-{staff_id}-chat`

**Purpose:** Personal notifications for individual staff members

**Events:**
- `new-guest-message` - Guest sent a message
- `message-deleted` - Message was deleted
- `message-removed` - Message was deleted (alias)

**Used By:** Individual staff member's UI

---

## Event Flow Examples

### Message Sending (Staff → Guest)
1. Staff sends message via `POST /api/chat/{hotel_slug}/conversation/{conv_id}/messages/`
2. Backend broadcasts to:
   - ✅ Conversation channel: `new-message`
   - ✅ Room channel: `new-staff-message`
   - ✅ Guest FCM notification (if token available)

### Message Sending (Guest → Staff)
1. Guest sends message via `POST /api/chat/{hotel_slug}/conversation/{conv_id}/messages/`
2. Backend broadcasts to:
   - ✅ Conversation channel: `new-message`
   - ✅ Room channel: `new-message` (echo back to guest)
   - ✅ Staff individual channels: `new-guest-message`
   - ✅ Staff FCM notifications (receptionists/front-office)

### 🆕 Message Deletion - All Scenarios

#### Scenario 1: Staff deletes their own message
1. Staff deletes via `DELETE /api/chat/messages/{message_id}/delete/`
2. Payload: `deleted_by: "staff"`, `original_sender: "staff"`
3. UI: Show "[Message deleted]" or remove completely
4. Broadcasts to all channels (conversation, room, deletion, staff)

#### Scenario 2: Staff deletes guest's message (moderation)
1. Staff deletes via `DELETE /api/chat/messages/{message_id}/delete/`
2. Payload: `deleted_by: "staff"`, `original_sender: "guest"`
3. Guest UI: Show "[Message removed by staff]" with notification
4. Staff UI: Show "[Message removed]"
5. Broadcasts to all channels

#### Scenario 3: Guest deletes their own message
1. Guest deletes via `DELETE /api/chat/messages/{message_id}/delete/`
2. Payload: `deleted_by: "guest"`, `original_sender: "guest"`
3. Guest UI: Show "[You deleted this message]"
4. Staff UI: Show "[Message deleted by guest]"
5. Broadcasts to all channels

**Key Point:** The `deleted_by` and `original_sender` fields allow frontends to display contextually appropriate messages and notifications.

### Attachment Deletion
1. User deletes attachment via `DELETE /api/chat/attachments/{attachment_id}/delete/`
2. Backend broadcasts to:
   - ✅ Conversation channel: `attachment-deleted`
   - ✅ **Deletion channel: `attachment-deleted`** ← NEW!

---

## Frontend Integration

### Guest UI Subscription (React Example)
```javascript
// Subscribe to room channel for general messages
const roomChannel = pusher.subscribe(
  `${hotelSlug}-room-${roomNumber}-chat`
);

// Subscribe to DELETION CHANNEL for reliable deletion updates
const deletionChannel = pusher.subscribe(
  `${hotelSlug}-room-${roomNumber}-deletions`
);

// Handle deletion events with context
deletionChannel.bind('content-deleted', (data) => {
  const { 
    message_id, 
    hard_delete, 
    attachment_ids,
    deleted_by,      // "staff" or "guest"
    original_sender, // "staff" or "guest"
    staff_name 
  } = data;
  
  console.log(`🗑️ Deletion: ${original_sender} message deleted by ${deleted_by}`);
  
  if (hard_delete) {
    // Remove message completely
    setMessages(prev => prev.filter(m => m.id !== message_id));
    
    // Show notification based on who deleted
    if (deleted_by === 'staff' && original_sender === 'guest') {
      showNotification(`Staff removed your message`, 'info');
    }
  } else {
    // Soft delete - show different text based on context
    let deletedText = '[Message deleted]';
    
    // Customize message based on deletion context
    if (deleted_by === 'staff' && original_sender === 'guest') {
      deletedText = '[Message removed by staff]';
    } else if (deleted_by === 'guest' && original_sender === 'guest') {
      deletedText = '[You deleted this message]';
    }
    
    setMessages(prev => prev.map(m => 
      m.id === message_id 
        ? { 
            ...m, 
            message: deletedText, 
            is_deleted: true,
            deleted_by,
            original_sender
          }
        : m
    ));
  }
  
  // Clean up attachments
  if (attachment_ids?.length > 0) {
    attachment_ids.forEach(id => removeAttachment(id));
  }
});

// Handle attachment deletions
deletionChannel.bind('attachment-deleted', (data) => {
  const { attachment_id, message_id } = data;
  removeAttachmentFromMessage(message_id, attachment_id);
});
```

### Staff UI Subscription (React Example)
```javascript
// Subscribe to conversation channel
const conversationChannel = pusher.subscribe(
  `${hotelSlug}-conversation-${conversationId}-chat`
);

// Subscribe to staff personal channel
const staffChannel = pusher.subscribe(
  `${hotelSlug}-staff-${staffId}-chat`
);

// Handle new messages from guests
staffChannel.bind('new-guest-message', (data) => {
  // Add message to conversation
  addMessageToConversation(data);
  
  // Show notification
  showNotification(`New message from Room ${data.room_number}`);
});

// Handle deletions with context
conversationChannel.bind('message-deleted', (data) => {
  const { 
    message_id, 
    hard_delete, 
    deleted_by, 
    original_sender,
    staff_name 
  } = data;
  
  if (hard_delete) {
    // Remove completely
    setMessages(prev => prev.filter(m => m.id !== message_id));
  } else {
    // Soft delete with contextual message
    let deletedText = '[Message deleted]';
    
    if (deleted_by === 'guest' && original_sender === 'guest') {
      deletedText = '[Message deleted by guest]';
    } else if (deleted_by === 'staff' && original_sender === 'guest') {
      deletedText = `[Message removed by ${staff_name || 'staff'}]`;
    } else if (deleted_by === 'staff' && original_sender === 'staff') {
      deletedText = staff_name 
        ? `[Message deleted by ${staff_name}]`
        : '[Message deleted]';
    }
    
    setMessages(prev => prev.map(m => 
      m.id === message_id 
        ? { ...m, message: deletedText, is_deleted: true }
        : m
    ));
  }
});
```

---

## Migration Guide

### For Guest UI Developers
**ACTION REQUIRED:** Subscribe to the new deletion channel

1. Add deletion channel subscription:
```javascript
const deletionChannel = pusher.subscribe(
  `${hotelSlug}-room-${roomNumber}-deletions`
);
```

2. Listen for `content-deleted` event:
```javascript
deletionChannel.bind('content-deleted', handleDeletion);
```

3. Listen for `attachment-deleted` event:
```javascript
deletionChannel.bind('attachment-deleted', handleAttachmentDeletion);
```

### Backward Compatibility
- Old events (`message-deleted`, `message-removed`) still broadcast to conversation and room channels
- New deletion channel provides additional reliability
- Frontend can listen to both for transition period

---

## Channel Summary Table

| Channel | Purpose | Who Subscribes | Key Events |
|---------|---------|----------------|------------|
| `conversation-{id}-chat` | General conversation | All participants | `new-message`, `message-updated`, read receipts |
| `room-{number}-chat` | Room-specific messages | Guest UI | `new-staff-message`, `staff-assigned` |
| `room-{number}-deletions` 🆕 | **Deletion events** | **Guest UI** | **`content-deleted`, `attachment-deleted`** |
| `staff-{id}-chat` | Staff personal | Individual staff | `new-guest-message`, notifications |

---

## Deletion Scenarios Reference

| Scenario | deleted_by | original_sender | Guest UI Shows | Staff UI Shows | Use Case |
|----------|------------|-----------------|----------------|----------------|----------|
| Guest deletes own message | `guest` | `guest` | "[You deleted this message]" | "[Message deleted by guest]" | Guest removes their message |
| Staff deletes own message | `staff` | `staff` | "[Message deleted]" | "[Message deleted by {name}]" | Staff removes their message |
| Staff deletes guest message | `staff` | `guest` | "[Message removed by staff]" | "[Message removed by {name}]" | **Moderation** |

### Frontend Logic Example
```javascript
function getDeletedMessageText(deleted_by, original_sender, staff_name, isGuestView) {
  // For guest UI
  if (isGuestView) {
    if (deleted_by === 'guest' && original_sender === 'guest') {
      return '[You deleted this message]';
    }
    if (deleted_by === 'staff' && original_sender === 'guest') {
      return '[Message removed by staff]';
    }
    if (deleted_by === 'staff' && original_sender === 'staff') {
      return '[Message deleted]';
    }
  }
  
  // For staff UI
  if (deleted_by === 'guest' && original_sender === 'guest') {
    return '[Message deleted by guest]';
  }
  if (deleted_by === 'staff') {
    return staff_name 
      ? `[Message deleted by ${staff_name}]`
      : '[Message deleted]';
  }
  
  return '[Message deleted]';
}
```

## Benefits of New Architecture

### Problem Solved
- ❌ **Before:** Guest UI did not see image/message deletions from staff
- ✅ **After:** Dedicated deletion channel + context info ensures proper updates

### Advantages
1. **Clear Separation:** Deletion events isolated from other chat events
2. **Reliable Updates:** No channel subscription conflicts
3. **Better Debugging:** Easy to trace deletion-specific issues
4. **Contextual UI:** Know who deleted what for appropriate messaging
5. **Moderation Support:** Staff can delete guest messages with clear feedback
6. **Scalable:** Can add more specialized channels (shares, reactions, etc.)
7. **Backward Compatible:** Old channels still work during transition

---

## Future Enhancements

### Potential Additional Channels
1. **Reply Channel:** `{hotel}-room-{number}-replies`
   - For threaded message replies
   - Event: `reply-added`, `reply-deleted`

2. **Reaction Channel:** `{hotel}-room-{number}-reactions`
   - For message reactions/emoji
   - Event: `reaction-added`, `reaction-removed`

3. **Typing Indicator Channel:** `{hotel}-room-{number}-typing`
   - For "user is typing..." indicators
   - Event: `user-typing`, `user-stopped-typing`

4. **Share Channel:** `{hotel}-room-{number}-shares`
   - For shared content/messages
   - Event: `content-shared`, `share-revoked`

---

## Testing

### Test Deletion Channel
```bash
# Use the test endpoint
POST /api/chat/test/{hotel_slug}/room/{room_number}/test-deletion/
Body: {
  "message_id": 123,
  "hard_delete": true
}
```

### Expected Console Output (Backend)
```
🗑️ DELETE REQUEST | message_id=123 | hotel=hotel-killarney | room=101
🗑️ DELETION CHANNEL | hotel-killarney-room-101-deletions
📡 BROADCASTING TO DELETION CHANNEL
   Channel: hotel-killarney-room-101-deletions
✅ SENT content-deleted to hotel-killarney-room-101-deletions
```

### Expected Console Output (Guest UI)
```
🔔 Subscribed to deletion channel: hotel-killarney-room-101-deletions
🗑️ Deletion event received: {message_id: 123, hard_delete: true}
✅ Message removed from UI
```

---

## Related Files
- Backend: `chat/views.py` - Pusher broadcast logic
- Backend: `chat/utils.py` - Pusher client configuration
- Backend: `docs/CHAT_MESSAGE_DELETION_REAL_TIME_GUEST.md` - Previous implementation
- Frontend: Guest chat component (needs update to subscribe to deletion channel)

---

## Version History
- **v2.0** (Nov 5, 2025) - Introduced dedicated deletion channel
- **v1.0** (Nov 4, 2025) - Original multi-channel architecture
