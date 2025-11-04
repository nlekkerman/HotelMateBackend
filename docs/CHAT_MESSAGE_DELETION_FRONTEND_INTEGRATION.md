# Chat Message Deletion - Frontend Integration Guide

**Last Updated:** November 4, 2025  
**Backend API Version:** v1  
**Status:** ✅ Server-side implemented and ready

---

## Overview

This document provides complete frontend integration instructions for handling message deletion in the chat system. The backend now emits **two event names** for maximum compatibility:
- `message-deleted` (primary)
- `message-removed` (secondary/alias)

Both events carry identical payloads and are sent to multiple Pusher channels to ensure all participants (guests, staff) see deletions in real-time.

---

## Backend Changes Summary

### What was fixed:
1. **Dual event emission**: Server now triggers both `message-deleted` AND `message-removed` events
2. **Multiple channel broadcasts**: Events sent to:
   - Conversation channel (all participants)
   - Guest-specific channel
   - Individual staff channels
3. **Consistent payload structure** for both hard and soft deletes

### Files modified:
- `chat/views.py` - `delete_message()` function (lines ~1050-1285)

---

## Pusher Event Specifications

### Event Names
Listen for **EITHER** of these events (or both for redundancy):
```javascript
channel.bind('message-deleted', handleMessageDeleted);
channel.bind('message-removed', handleMessageDeleted); // Alias
```

### Channels to Subscribe To

#### For Guests:
```javascript
const guestChannel = `${hotelSlug}-room-${roomNumber}-chat`;
```

#### For Staff:
```javascript
const conversationChannel = `${hotelSlug}-conversation-${conversationId}-chat`;
const staffChannel = `${hotelSlug}-staff-${staffId}-chat`;
```

---

## Event Payload Structure

### Hard Delete Payload
```json
{
  "message_id": 668,
  "hard_delete": true
}
```

### Soft Delete Payload
```json
{
  "message_id": 668,
  "hard_delete": false,
  "message": {
    "id": 668,
    "conversation": 50,
    "room": 101,
    "sender_type": "guest",
    "staff": null,
    "message": "[Message deleted]",
    "timestamp": "2025-11-04T23:02:16.123456Z",
    "staff_display_name": null,
    "staff_role_name": null,
    "status": "delivered",
    "read_by_staff": false,
    "read_by_guest": false,
    "staff_read_at": null,
    "guest_read_at": null,
    "delivered_at": "2025-11-04T23:02:16.123456Z",
    "is_edited": false,
    "edited_at": null,
    "is_deleted": true,
    "deleted_at": "2025-11-04T23:05:30.789012Z",
    "reply_to": null,
    "reply_to_message": null,
    "attachments": []
  }
}
```

---

## Frontend Implementation

### Step 1: Subscribe to Pusher Channels

#### Guest Client Example:
```javascript
import Pusher from 'pusher-js';

// Initialize Pusher
const pusher = new Pusher('YOUR_PUSHER_KEY', {
  cluster: 'YOUR_CLUSTER',
  encrypted: true
});

// Subscribe to guest room channel
const hotelSlug = 'hotel-killarney';
const roomNumber = '101';
const guestChannel = pusher.subscribe(`${hotelSlug}-room-${roomNumber}-chat`);

// Bind to deletion events
guestChannel.bind('message-deleted', handleMessageDeleted);
guestChannel.bind('message-removed', handleMessageDeleted); // Redundant but safe
```

#### Staff Client Example:
```javascript
// Subscribe to conversation channel
const conversationId = '50';
const conversationChannel = pusher.subscribe(
  `${hotelSlug}-conversation-${conversationId}-chat`
);

conversationChannel.bind('message-deleted', handleMessageDeleted);
conversationChannel.bind('message-removed', handleMessageDeleted);
```

---

### Step 2: Implement Message Deletion Handler

#### Basic Handler (React/Vue/Plain JS):
```javascript
function handleMessageDeleted(data) {
  console.log('🗑️ Message deletion event received:', data);
  
  // Extract message ID
  const messageId = data.message_id || (data.message && data.message.id);
  
  if (!messageId) {
    console.error('❌ No message_id in deletion event payload');
    return;
  }
  
  if (data.hard_delete) {
    // HARD DELETE: Remove message from DOM completely
    console.log(`💥 Hard deleting message ${messageId}`);
    removeMessageFromDOM(messageId);
  } else {
    // SOFT DELETE: Update message to show "[Message deleted]"
    console.log(`🔄 Soft deleting message ${messageId}`);
    updateMessageToDeleted(messageId, data.message);
  }
}

function removeMessageFromDOM(messageId) {
  // Find and remove message element
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
  
  if (messageElement) {
    // Optional: Add fade-out animation
    messageElement.classList.add('removing');
    
    setTimeout(() => {
      messageElement.remove();
      console.log(`✅ Message ${messageId} removed from DOM`);
    }, 300); // Wait for animation
  } else {
    console.warn(`⚠️ Message ${messageId} not found in DOM`);
  }
}

function updateMessageToDeleted(messageId, messageData) {
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
  
  if (!messageElement) {
    console.warn(`⚠️ Message ${messageId} not found in DOM`);
    return;
  }
  
  // Update message text
  const messageBody = messageElement.querySelector('.message-body');
  if (messageBody) {
    messageBody.textContent = messageData.message || '[Message deleted]';
    messageBody.classList.add('deleted-message');
  }
  
  // Mark entire message as deleted
  messageElement.classList.add('message-deleted');
  
  // Remove any action buttons (edit, delete, reply)
  const actionButtons = messageElement.querySelectorAll('.message-actions');
  actionButtons.forEach(btn => btn.remove());
  
  console.log(`✅ Message ${messageId} updated to deleted state`);
}
```

---

### Step 3: React/Next.js Example (with useState)

```javascript
import { useEffect, useState } from 'react';
import Pusher from 'pusher-js';

function ChatWindow({ hotelSlug, conversationId, roomNumber, isGuest }) {
  const [messages, setMessages] = useState([]);
  
  useEffect(() => {
    const pusher = new Pusher(process.env.NEXT_PUBLIC_PUSHER_KEY, {
      cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER,
    });
    
    // Choose channel based on user type
    const channelName = isGuest 
      ? `${hotelSlug}-room-${roomNumber}-chat`
      : `${hotelSlug}-conversation-${conversationId}-chat`;
    
    const channel = pusher.subscribe(channelName);
    
    // Handle message deletion
    const handleMessageDeleted = (data) => {
      const messageId = data.message_id;
      
      if (data.hard_delete) {
        // Remove message from state
        setMessages(prev => prev.filter(msg => msg.id !== messageId));
      } else {
        // Update message to show deleted state
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, ...data.message, is_deleted: true }
            : msg
        ));
      }
    };
    
    channel.bind('message-deleted', handleMessageDeleted);
    channel.bind('message-removed', handleMessageDeleted); // Redundant but safe
    
    return () => {
      channel.unbind('message-deleted', handleMessageDeleted);
      channel.unbind('message-removed', handleMessageDeleted);
      pusher.unsubscribe(channelName);
    };
  }, [hotelSlug, conversationId, roomNumber, isGuest]);
  
  return (
    <div className="chat-messages">
      {messages.map(msg => (
        <div 
          key={msg.id} 
          data-message-id={msg.id}
          className={msg.is_deleted ? 'message message-deleted' : 'message'}
        >
          <div className={msg.is_deleted ? 'message-body deleted' : 'message-body'}>
            {msg.message}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

### Step 4: Vue.js Example (with Composition API)

```javascript
<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import Pusher from 'pusher-js';

const props = defineProps({
  hotelSlug: String,
  conversationId: Number,
  roomNumber: String,
  isGuest: Boolean
});

const messages = ref([]);
let pusher = null;
let channel = null;

const handleMessageDeleted = (data) => {
  const messageId = data.message_id;
  
  if (data.hard_delete) {
    // Remove message
    messages.value = messages.value.filter(msg => msg.id !== messageId);
  } else {
    // Update to deleted state
    const index = messages.value.findIndex(msg => msg.id === messageId);
    if (index !== -1) {
      messages.value[index] = {
        ...messages.value[index],
        ...data.message,
        is_deleted: true
      };
    }
  }
};

onMounted(() => {
  pusher = new Pusher(import.meta.env.VITE_PUSHER_KEY, {
    cluster: import.meta.env.VITE_PUSHER_CLUSTER,
  });
  
  const channelName = props.isGuest 
    ? `${props.hotelSlug}-room-${props.roomNumber}-chat`
    : `${props.hotelSlug}-conversation-${props.conversationId}-chat`;
  
  channel = pusher.subscribe(channelName);
  channel.bind('message-deleted', handleMessageDeleted);
  channel.bind('message-removed', handleMessageDeleted);
});

onUnmounted(() => {
  if (channel) {
    channel.unbind('message-deleted', handleMessageDeleted);
    channel.unbind('message-removed', handleMessageDeleted);
    pusher.unsubscribe(channel.name);
  }
});
</script>

<template>
  <div class="chat-messages">
    <div 
      v-for="msg in messages" 
      :key="msg.id"
      :data-message-id="msg.id"
      :class="['message', { 'message-deleted': msg.is_deleted }]"
    >
      <div :class="['message-body', { 'deleted': msg.is_deleted }]">
        {{ msg.message }}
      </div>
    </div>
  </div>
</template>
```

---

## CSS Styling Suggestions

Add visual feedback for deleted messages:

```css
/* Soft-deleted message styling */
.message-deleted {
  opacity: 0.6;
  background-color: #f5f5f5;
}

.message-body.deleted-message {
  font-style: italic;
  color: #999;
}

/* Hard-delete animation */
.message.removing {
  opacity: 0;
  transform: translateX(-20px);
  transition: all 0.3s ease-out;
}

/* Hide action buttons for deleted messages */
.message-deleted .message-actions {
  display: none;
}
```

---

## Testing & Debugging

### 1. Check Pusher Connection
Open browser console and verify Pusher connection:
```javascript
pusher.connection.bind('connected', () => {
  console.log('✅ Pusher connected');
});

pusher.connection.bind('error', (err) => {
  console.error('❌ Pusher error:', err);
});
```

### 2. Monitor WebSocket Frames
1. Open DevTools → Network tab
2. Filter by `WS` (WebSocket)
3. Find Pusher connection
4. Click → Messages/Frames tab
5. Delete a message
6. Look for incoming frames with `message-deleted` or `message-removed` event

Expected frame structure:
```json
{
  "event": "message-deleted",
  "data": "{\"message_id\":668,\"hard_delete\":false,\"message\":{...}}",
  "channel": "hotel-killarney-conversation-50-chat"
}
```

### 3. Console Logging
Add comprehensive logging to your handler:
```javascript
function handleMessageDeleted(data) {
  console.group('🗑️ Message Deletion Event');
  console.log('Event data:', data);
  console.log('Message ID:', data.message_id);
  console.log('Hard delete:', data.hard_delete);
  console.log('Message object:', data.message);
  console.groupEnd();
  
  // ... rest of handler
}
```

### 4. Common Issues & Solutions

#### Issue: Event received but UI not updating
**Solution:** Check your DOM selectors match actual HTML structure
```javascript
// ❌ Wrong: querySelector might not match
const el = document.querySelector(`#message-${messageId}`);

// ✅ Correct: Use data attribute
const el = document.querySelector(`[data-message-id="${messageId}"]`);
```

#### Issue: Multiple deletions when one expected
**Solution:** Only bind event handlers once, unbind on cleanup
```javascript
// ✅ React useEffect cleanup
useEffect(() => {
  channel.bind('message-deleted', handler);
  return () => channel.unbind('message-deleted', handler); // Cleanup!
}, []);
```

#### Issue: Guest sees deletion but staff doesn't (or vice versa)
**Solution:** Verify you're subscribed to correct channel for user type
```javascript
// Guest: room channel
const channel = `${hotelSlug}-room-${roomNumber}-chat`;

// Staff: conversation channel
const channel = `${hotelSlug}-conversation-${conversationId}-chat`;
```

---

## API Endpoint Reference

### DELETE Message Endpoint
```
DELETE /api/chat/messages/{message_id}/delete/
```

**Query Parameters:**
- `hard_delete=true` (optional) - Permanently delete (admin/manager only)

**Response (Success):**
```json
{
  "success": true,
  "hard_delete": false,
  "message_id": 668,
  "message": { /* full message object */ }
}
```

**Response (Error - 403):**
```json
{
  "error": "You don't have permission to delete this message"
}
```

---

## Channel Summary Table

| User Type | Channel Pattern | Event Names | Purpose |
|-----------|----------------|-------------|---------|
| Guest | `{hotel}-room-{room_number}-chat` | `message-deleted`, `message-removed` | Guest sees their own + staff deletions |
| Staff (Conversation) | `{hotel}-conversation-{conversation_id}-chat` | `message-deleted`, `message-removed` | All staff + guest see deletions |
| Staff (Personal) | `{hotel}-staff-{staff_id}-chat` | `message-deleted`, `message-removed` | Individual staff notifications |

---

## Quick Start Checklist

- [ ] Install Pusher client library (`npm install pusher-js`)
- [ ] Subscribe to correct channel based on user type
- [ ] Bind to BOTH `message-deleted` AND `message-removed` events
- [ ] Implement handler that checks `hard_delete` flag
- [ ] For hard delete: remove message from DOM/state
- [ ] For soft delete: update message text and style
- [ ] Test by deleting a message in the app
- [ ] Check browser console for event logs
- [ ] Inspect WebSocket frames in Network tab
- [ ] Add CSS styling for deleted messages
- [ ] Add error handling for missing message IDs

---

## Production Checklist

- [ ] Error boundaries around Pusher event handlers
- [ ] Reconnection logic for dropped connections
- [ ] Rate limiting for rapid deletion events
- [ ] Accessibility: Screen reader announcements for deletions
- [ ] Loading states during deletion API calls
- [ ] Optimistic UI updates (remove immediately, rollback on error)
- [ ] Batch updates for multiple simultaneous deletions
- [ ] Logging/monitoring for Pusher connection issues

---

## Support & Questions

- **Backend API:** See `chat/views.py` - `delete_message()` function
- **Pusher Docs:** https://pusher.com/docs/channels/
- **Channel Naming:** See `CHAT_REPLY_FUNCTIONALITY.md` for other events

**Last Verified:** November 4, 2025  
**Backend Commit:** main branch, `delete_message()` now emits dual events
