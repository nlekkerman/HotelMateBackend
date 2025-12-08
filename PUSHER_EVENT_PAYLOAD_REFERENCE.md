# Pusher Event Payload Reference

## Staff Chat Message Created Event

### **WHEN IS THIS EVENT SENT?**
The `realtime_staff_chat_message_created` event is triggered **IMMEDIATELY AFTER** a staff member successfully sends a message via the API endpoint:

```
POST /api/staff-chat/<hotel_slug>/conversations/<id>/send-message/
```

**Sequence:**
1. Staff member sends message via API
2. Message is created in database (`StaffChatMessage.objects.create()`)
3. **IMMEDIATELY** calls `notification_manager.realtime_staff_chat_message_created(message)`
4. Pusher event is broadcast to all conversation participants

### Event Name
```
"realtime_staff_chat_message_created"
```

### Channel Names
```
- Conversation Channel: "killarney.staff-chat.{conversation_id}"
- Notification Channel: "killarney.staff-{staff_id}-notifications"
```

### Complete Payload Structure
```json
{
  "category": "staff_chat",
  "type": "message_created",
  "payload": {
    "id": 123,
    "conversation_id": 100,
    "text": "Hello world",
    "sender_id": 45,
    "sender_name": "John Doe",
    "timestamp": "2025-12-08T14:30:00Z",
    "attachments": [],
    "is_system_message": false
  },
  "meta": {
    "hotel_slug": "killarney",
    "event_id": "uuid-string",
    "ts": "2025-12-08T14:30:00Z",
    "scope": {
      "conversation_id": 100,
      "sender_id": 45
    }
  }
}
```

### Payload Fields Explanation
| Field | Type | Description |
|-------|------|-------------|
| `payload.id` | Number | Message ID |
| `payload.conversation_id` | Number | Conversation ID |
| `payload.text` | String | Message content |
| `payload.sender_id` | Number | Staff ID who sent the message |
| `payload.sender_name` | String | Full name of sender |
| `payload.timestamp` | String | ISO-8601 timestamp |
| `payload.attachments` | Array | List of attachments (if any) |
| `payload.is_system_message` | Boolean | Whether it's a system message |

### Event Broadcasting
1. **Conversation Channel**: All participants receive message for display
2. **Notification Channels**: Other participants receive notifications for unread counts

### Frontend Event Handling
The frontend should:
1. Listen for event name: `"realtime_staff_chat_message_created"`
2. Extract message data from `event.payload`
3. Add message to conversation UI
4. Update unread counts for other participants

### Channel Pattern
- Hotel slug: `killarney`
- Staff chat: `killarney.staff-chat.{conversationId}`
- Staff notifications: `killarney.staff-{staffId}-notifications`