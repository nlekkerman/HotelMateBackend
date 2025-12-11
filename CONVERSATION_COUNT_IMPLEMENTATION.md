# 🔢 Staff Chat Conversation Count Implementation

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

### Widget Badge (Conversation Count)
```javascript
// Listen for conversation count updates
pusher.bind('realtime_staff_chat_conversations_with_unread', (data) => {
  const conversationCount = data.payload.conversations_with_unread;
  updateChatWidgetBadge(conversationCount); // Show "5 conversations"
});
```

### Individual List Items (Message Count)
```javascript
// Existing - still works the same
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