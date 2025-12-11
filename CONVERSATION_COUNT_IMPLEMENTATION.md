# 🔢 Staff Chat Conversation Count Implementation

## API Endpoints

### Get Initial Conversation Counted
**GET** `/api/staff-chat/{hotel_slug}/conversations/conversations-with-unread-count/`

**Response:**
```json
{
  "conversations_with_unread": 5,
  "updated_at": "2025-12-11T10:30:00Z"
}
```

### Get Detailed Unread Info
**GET** `/api/staff-chat/{hotel_slug}/conversations/unread-count/`

**Response:**
```json
{
  "total_unread": 42,
  "conversations_with_unread": 5,
  "breakdown": [...]
}
```

## New Pusher Event

### `realtime_staff_chat_conversations_with_unread`
**Channel:** `{hotel_slug}.staff-{staff_id}-notifications`

**Payload:**
```json
{
  "category": "staff_chat",
  "type": "realtime_staff_chat_conversations_with_unread",
  "payload": {
    "staff_id": 123,
    "conversations_with_unread": 5,
    "updated_at": "2025-12-11T10:30:00Z"
  }
}
```

## Frontend Integration

### 1. Get Initial Count (on load/login)
```javascript
// Get current conversation count when app starts
const response = await fetch('/api/staff-chat/{hotel_slug}/conversations/conversations-with-unread-count/');
const { conversations_with_unread } = await response.json();
updateChatWidgetBadge(conversations_with_unread);
```

### 2. Listen for Real-time Updates
```javascript
// Widget Badge (Conversation Count)
pusher.bind('realtime_staff_chat_conversations_with_unread', (data) => {
  const conversationCount = data.payload.conversations_with_unread;
  updateChatWidgetBadge(conversationCount); // Show "5 conversations"
});

// Individual List Items (Message Count) - existing
pusher.bind('realtime_staff_chat_unread_updated', (data) => {
  const messageCount = data.payload.unread_count;
  updateConversationItem(data.payload.conversation_id, messageCount); // Show "3 messages"
});
```

## When Events Fire

| Action | Conversation Count Event | Message Count Event |
|--------|-------------------------|---------------------|
| **New message in existing conversation** | ❌ No | ✅ Yes |
| **First message in new conversation** | ✅ Yes (+1) | ✅ Yes |
| **Read all messages in conversation** | ✅ Yes (-1) | ✅ Yes |
| **Read some messages (conversation still has unread)** | ❌ No | ✅ Yes |

## Result
- **Widget Badge**: Shows number of conversations with unread messages
- **List Items**: Shows number of unread messages per conversation
- **Both update automatically in real-time**