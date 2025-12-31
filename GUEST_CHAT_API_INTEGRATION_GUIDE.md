# Guest Chat API Integration Guide

## Overview

The guest chat system has been updated to use **token-based authentication** instead of PIN-based access. This provides better security and integrates with the existing guest booking system.

## Available Chat Endpoints

### Token-Based Guest Chat (NEW - Recommended)

#### 1. Get Guest Chat Context
```http
GET /api/chat/{hotel_slug}/guest/chat/context/?token={guest_token}
```

**Purpose**: Replace PIN-based flow, get chat context and Pusher channel info

**Response**:
```json
{
  "conversation_id": 55,
  "room_number": "112",
  "booking_id": "BK-2025-0123",
  "pusher": {
    "channel": "private-hotel-killarney-guest-chat-booking-BK-2025-0123",
    "event": "realtime_event"
  },
  "allowed_actions": {
    "can_chat": true
  },
  "current_staff_handler": {
    "name": "John Smith",
    "role": "Receptionist"
  },
  "assigned_room_id": 101
}
```

**Error Responses**:
- `400` - Token parameter missing
- `404` - Invalid token or hotel mismatch
- `403` - Guest not checked in
- `409` - No room assigned to booking

#### 2. Send Guest Message
```http
POST /api/chat/{hotel_slug}/guest/chat/messages/?token={guest_token}
```

**Body**:
```json
{
  "message": "Hello from guest!",
  "reply_to": 123  // optional - ID of message to reply to
}
```

**Response** (201 Created):
```json
{
  "id": 124,
  "message": "Hello from guest!",
  "sender_type": "guest",
  "guest_name": "Jane Doe",
  "timestamp": "2025-12-31T10:30:00Z",
  "conversation_id": 55,
  "room_number": 112,
  "reply_to": 123,
  "reply_to_message": {
    "id": 123,
    "message": "Previous message...",
    "sender_type": "staff"
  }
}
```

**Error Responses**:
- `400` - Empty message or invalid data
- `401` - Token parameter missing
- `403` - Guest not checked in
- `404` - Invalid token or hotel mismatch
- `409` - No room assigned

### Staff Chat Endpoints (Existing - Unchanged)

#### Get All Conversations
```http
GET /api/chat/{hotel_slug}/conversations/
```
*Requires staff authentication*

#### Get Messages in Conversation
```http
GET /api/chat/{hotel_slug}/conversations/{conversation_id}/messages/
```
*Query params: `limit`, `before_id` for pagination*

#### Send Message (Staff)
```http
POST /api/chat/{hotel_slug}/conversations/{conversation_id}/messages/send/
```
*Requires staff authentication*

### Legacy Endpoints (Deprecated)

❌ **Do NOT use these for guest portal**:
- `POST /api/chat/{hotel_slug}/messages/room/{room_number}/validate-chat-pin/`
- `POST /api/chat/{hotel_slug}/guest-session/room/{room_number}/initialize/`
- `GET /guest-session/{session_token}/validate/`

## Room Move Handling

### Booking-Scoped Channels (Current Implementation)

The chat system uses **booking-scoped channels** to ensure seamless communication even when guests are moved between rooms:

```
private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}
```

**Benefits**:
- ✅ **Room Move Transparent**: If staff moves guest from Room 101 → Room 202, chat continues on same channel
- ✅ **No Re-subscription Needed**: Guest's browser stays connected to same Pusher channel
- ✅ **Stable Connection**: Channel survives room reassignments, upgrades, and moves
- ✅ **Enhanced Security**: Private channels with booking-based authentication

**When Room Changes**:
1. Staff moves guest to different room
2. Guest's next API call returns new `room_number` in context
3. **Same Pusher channel continues working** - no interruption
4. Chat history and real-time messages flow seamlessly

### Implementation Notes

```javascript
// Channel subscription is stable across room moves
const context = await initializeGuestChat(hotelSlug, guestToken);
// context.pusher.channel = "private-hotel-killarney-guest-chat-booking-BK-2025-0123"

// This channel works regardless of which room guest is assigned to
pusherClient.subscribe(context.pusher.channel);

// Room number may change, but channel stays the same
// context.room_number could be "101" initially, then "202" after move
```

## Frontend Integration

### For GuestChatPortal Component

#### 1. Initialize Chat Context
```javascript
// Replace PIN validation with token-based context
async function initializeGuestChat(hotelSlug, guestToken) {
  try {
    const response = await fetch(`/api/chat/${hotelSlug}/guest/chat/context/?token=${guestToken}`);
    
    if (!response.ok) {
      throw new Error(`Chat access denied: ${response.status}`);
    }
    
    const context = await response.json();
    
    // Subscribe to Pusher channel
    const channel = pusherClient.subscribe(context.pusher.channel);
    
    // Listen for all events and route through eventBus
    channel.bind(context.pusher.event, handleRealtimeEvent);
    
    return context;
  } catch (error) {
    console.error('Failed to initialize guest chat:', error);
    throw error;
  }
}
```

#### 2. Send Messages
```javascript
async function sendGuestMessage(hotelSlug, guestToken, message, replyToId = null) {
  try {
    const response = await fetch(`/api/chat/${hotelSlug}/guest/chat/messages/?token=${guestToken}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message.trim(),
        reply_to: replyToId
      })
    });
    
    if (!response.ok) {
      throw new Error(`Failed to send message: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to send message:', error);
    throw error;
  }
}
```

#### 3. Handle Real-time Events
```javascript
// Route all realtime events through eventBus
function handleRealtimeEvent(eventData) {
  // Route based on event category and type
  if (eventData.category === 'guest_chat') {
    switch (eventData.type) {
      case 'message_created':
        handleNewMessage(eventData.payload);
        break;
      case 'unread_updated':
        handleUnreadUpdate(eventData.payload);
        break;
    }
  }
}

// Message received (from staff, guest, or system)
function handleNewMessage(messageData) {
  // Add message to chat UI with proper sender styling
  addMessageToChat(messageData);
  
  // Update unread counts if needed
  updateUnreadCount();
  
  // Scroll to bottom
  scrollToBottom();
}

// Unread count updated
function handleUnreadUpdate(unreadData) {
  // Update UI indicators
  updateUnreadIndicators(unreadData.unread_count);
}
```

#### 4. Render Message Senders
```javascript
function renderMessageSender(message) {
  switch (message.sender_type) {
    case 'staff':
      return message.staff_info ? message.staff_info.name : 'Staff';
    case 'guest':
      return 'Guest';
    case 'system':
      return null; // System messages use centered styling, no sender label
    default:
      return 'Unknown';
  }
}

function getMessageStyling(message) {
  switch (message.sender_type) {
    case 'staff':
      return 'staff-message';
    case 'guest':
      return 'guest-message';
    case 'system':
      return 'system-message centered'; // Centered system line styling
    default:
      return 'unknown-message';
  }
}
```

### Error Handling

```javascript
function handleChatError(error, response) {
  switch (response?.status) {
    case 400:
      return "Please check your message and try again.";
    case 401:
      return "Authentication required. Please refresh the page.";
    case 403:
      return "Chat access denied. You may not be checked in.";
    case 404:
      return "Chat session not found. Please refresh the page.";
    case 409:
      return "No room assigned. Please contact reception.";
    default:
      return "Unable to connect to chat. Please try again later.";
  }
}
```

## Migration from PIN-based Chat

### What to Remove
```javascript
// ❌ Remove PIN validation
// await validateChatPin(roomNumber, pin);

// ❌ Remove guest session initialization  
// await initializeGuestSession(roomNumber);

// ❌ Remove PIN-based channels
// const channel = `${hotelSlug}-room-${roomNumber}-chat`;
```

### What to Update
```javascript
// ✅ Update to token-based context
const context = await initializeGuestChat(hotelSlug, guestToken);

// ✅ Update channel subscription
const channel = pusherClient.subscribe(context.pusher.channel);

// ✅ Update message sending
await sendGuestMessage(hotelSlug, guestToken, message);
```

### What Stays the Same
- ✅ Pusher event handling (`guest_message_created`, `unread_updated`)
- ✅ Message display components and UI
- ✅ Staff chat functionality (completely unchanged)
- ✅ Message formatting and serialization

## Security & Authentication

### Token Validation Flow
1. **Frontend**: Includes `token` in query parameter
2. **Backend**: Validates token hash against database
3. **Backend**: Checks token expiration and status
4. **Backend**: Validates hotel match (anti-enumeration)
5. **Backend**: Ensures guest is checked in with assigned room
6. **Backend**: Updates `last_used_at` timestamp
7. **Backend**: Returns chat context or appropriate error

### Channel Naming Convention
- **Format**: `private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}`
- **Example**: `private-hotel-killarney-guest-chat-booking-BK-2025-0123`
- **Benefits**: 
  - Stable across room moves (guest doesn't need to resubscribe)
  - Maps 1:1 with bookings for security
  - Private channel for enhanced security
  - Survives room reassignments seamlessly

### Access Control Rules
- ✅ Token must be ACTIVE and not expired
- ✅ Token's booking must match hotel slug
- ✅ Guest must be checked in (`checked_in_at` not null)
- ✅ Guest must not be checked out (`checked_out_at` is null)
- ✅ Booking must have assigned room
- ✅ Booking status must not be cancelled

## Testing the Integration

### Test Cases
1. **Valid Token**: Should return chat context with pusher info
2. **Invalid Token**: Should return 404 error
3. **Not Checked In**: Should return 403 error
4. **No Room Assigned**: Should return 409 error
5. **Empty Message**: Should return 400 error
6. **Message with Reply**: Should create reply relationship

### Sample Test Data
```javascript
// Valid context response
{
  "conversation_id": 55,
  "room_number": "112", 
  "booking_id": "BK-2025-TEST",
  "pusher": {
    "channel": "private-hotel-test-guest-chat-booking-BK-2025-TEST",
    "event": "realtime_event"
  },
  "allowed_actions": {
    "can_chat": true
  },
  "current_staff_handler": null,
  "assigned_room_id": 101
}
```

### Staff Identity and System Messages

```javascript
// Staff message example
{
  "id": 124,
  "message": "Hello! How can I help you?",
  "sender_type": "staff",
  "staff_info": {
    "name": "John Smith",
    "role": "Receptionist", 
    "department": "Front Office"
  },
  "timestamp": "2025-12-31T10:30:00Z"
}

// System join message example
{
  "id": 125,
  "message": "John Smith has joined the conversation.",
  "sender_type": "system",
  "staff_info": null,
  "timestamp": "2025-12-31T10:29:30Z"
}
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|--------|----------|
| 404 on context endpoint | Invalid token or hotel mismatch | Check token validity and hotel slug |
| 403 access denied | Guest not checked in | Ensure guest has checked in |
| 409 no room assigned | Booking has no room | Contact reception to assign room |
| Messages not appearing | Wrong Pusher channel | Use channel from context response |
| Can't send messages | Token missing from request | Include token in query parameter |

### Debug Tips
1. Check browser network tab for actual request URLs
2. Verify token is included in query parameters
3. Check Pusher connection and channel subscription
4. Monitor backend logs for detailed error messages
5. Test with valid booking tokens from email links

## Architecture Summary

```
Guest Email Link → Token → Booking → In-house Check → assigned_room → Conversation → booking-scoped Pusher channel
```

- **Authentication**: Guest booking tokens (secure, time-limited)
- **Authorization**: Booking + in-house + assigned_room validation  
- **Real-time**: Private Pusher channels per booking (stable across room moves)
- **Notifications**: Integrated with existing NotificationManager
- **Backwards Compatible**: Staff chat unchanged, legacy endpoints available

This token-based approach provides better security than PIN-based access while maintaining the same user experience and real-time messaging capabilities.