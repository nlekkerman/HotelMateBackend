# Guest Chat Pusher Integration

## How Real-time Chat Works

### 1. Initial Setup
```javascript
// Get chat context with Pusher channel info
const context = await fetch(`/api/guest/hotel/${hotelSlug}/chat/context?token=${token}`);
```

**Response includes:**
```json
{
  "pusher": {
    "channel": "private-hotel-killarney-guest-chat-booking-BK-2025-0123",
    "event": "realtime_event"
  }
}
```

### 2. Subscribe to Pusher
```javascript
const pusher = new Pusher(PUSHER_KEY, { 
  encrypted: true,
  // CRITICAL: Pusher auth endpoint for private channels
  authEndpoint: `/api/guest/hotel/${hotelSlug}/chat/pusher/auth?token=${token}`,
  auth: {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
});

const channel = pusher.subscribe(context.pusher.channel);

// Listen for new messages
channel.bind('realtime_event', function(data) {
  if (data.type === 'chat_message') {
    addMessageToChat(data.message); // Instant UI update
  }
});
```

**Security Note**: The auth endpoint validates:
- ✅ Token matches hotel slug
- ✅ Channel name matches token's booking ID exactly  
- ✅ No wildcards or cross-booking access allowed

### 3. Send Messages
```javascript
// POST message - Pusher handles delivery automatically
await fetch(`/api/guest/hotel/${hotelSlug}/chat/messages?token=${token}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Hello!' })
});
// Message appears via Pusher, no manual UI update needed
```

## Backend Auto-Push
```python
# After creating message in views
message = RoomMessage.objects.create(...)

# Automatically triggers Pusher notification
notification_manager.realtime_guest_chat_message_created(message)
```

## When to Use GET Endpoint
- **Initial load**: Get recent message history
- **Reconnection**: Sync missed messages when Pusher drops
- **Pagination**: Load older messages on scroll

## Key Benefits
- ✅ **Real-time**: Messages appear instantly
- ✅ **Bidirectional**: Both guest & staff messages pushed
- ✅ **Efficient**: No polling/repeated API calls
- ✅ **Scalable**: WebSocket handles many users
- ✅ **Secure**: Private channel auth prevents cross-booking access

## Complete API Endpoints
1. **GET** `/api/guest/hotel/{hotel_slug}/chat/context?token=...` - Get chat setup
2. **GET** `/api/guest/hotel/{hotel_slug}/chat/messages?token=...` - Get messages (backup/initial load)
3. **POST** `/api/guest/hotel/{hotel_slug}/chat/messages?token=...` - Send message
4. **POST** `/api/guest/hotel/{hotel_slug}/chat/pusher/auth?token=...` - Pusher channel auth