# Complete Staff Chat Message Flow Logic

## Message Creation Flow

### 1. Frontend API Call
```
POST /api/staff-chat/{hotel_slug}/conversations/{conversation_id}/send-message/
```
**Body:**
```json
{
  "message": "Hello world",
  "reply_to": 123  // optional
}
```

### 2. Backend View Handler
**File:** `staff_chat/views_messages.py` - `send_message()` function (line ~115)

**Process:**
1. Validate conversation and staff permissions
2. Extract message text and reply_to from request
3. Parse @mentions from message content
4. Create `StaffChatMessage` object in database
5. Add mentions to message
6. Update conversation `has_unread = True`
7. Serialize message data
8. **TRIGGER PUSHER EVENTS** (line 259)
9. Send FCM notifications to participants

### 3. Pusher Event Triggering
**File:** `notifications/notification_manager.py` - `realtime_staff_chat_message_created()` (line 188)

**Debug Flow:**
```python
# 1. Log message creation
self.logger.info(f"🔥 PUSHER DEBUG: Starting realtime_staff_chat_message_created for message {message.id}")
self.logger.info(f"🔥 PUSHER DEBUG: Hotel slug = {message.sender.hotel.slug}")
self.logger.info(f"🔥 PUSHER DEBUG: Conversation ID = {message.conversation.id}")

# 2. Build payload
payload = {
    'id': message.id,
    'conversation_id': message.conversation.id,
    'text': message.message,  # Message content
    'sender_id': message.sender.id,
    'sender_name': message.sender.get_full_name(),
    'timestamp': message.timestamp.isoformat(),
    'attachments': getattr(message, 'attachments', []),
    'is_system_message': getattr(message, 'is_system_message', False)
}

# 3. Create normalized event structure
event_data = {
    "category": "staff_chat",
    "type": "message_created",
    "payload": payload,
    "meta": {
        "hotel_slug": hotel.slug,
        "event_id": str(uuid.uuid4()),
        "ts": timezone.now().isoformat(),
        "scope": {'conversation_id': conversation.id, 'sender_id': sender.id}
    }
}
```

### 4. Dual Channel Broadcasting

#### A. Conversation Channel (All Participants)
```python
# Channel: "hotel-killarney.staff-chat.100"
# Event: "realtime_staff_chat_message_created"
# Purpose: Display message in conversation UI

conversation_channel = f"{hotel_slug}.staff-chat.{message.conversation.id}"
conversation_sent = pusher_client.trigger(conversation_channel, "realtime_staff_chat_message_created", event_data)
```

#### B. Individual Notification Channels (Other Participants)
```python
# Channels: "hotel-killarney.staff-45-notifications", "hotel-killarney.staff-67-notifications"
# Event: "realtime_staff_chat_message_created" 
# Purpose: Update unread counts, show notifications

for participant in message.conversation.participants.exclude(id=message.sender.id):
    notification_channel = f"{hotel_slug}.staff-{participant.id}-notifications"
    pusher_client.trigger(notification_channel, "realtime_staff_chat_message_created", event_data)
```

## Frontend Event Handling

### 1. Channel Subscriptions
**File:** Frontend `channelRegistry.js`

```javascript
// Subscribe to conversation channel
const conversationChannel = `hotel-killarney.staff-chat.${conversationId}`;
pusher.subscribe(conversationChannel);

// Subscribe to personal notifications
const notificationChannel = `hotel-killarney.staff-${staffId}-notifications`;
pusher.subscribe(notificationChannel);
```

### 2. Event Processing
**File:** Frontend `eventBus.js`

```javascript
// Listen for "realtime_staff_chat_message_created" events
// Extract payload.text, payload.sender_name, etc.
// Update conversation UI in real-time
```

## Key Files Involved

| File | Purpose | Key Functions |
|------|---------|---------------|
| `staff_chat/views_messages.py` | API endpoint handler | `send_message()` - Creates message and triggers events |
| `notifications/notification_manager.py` | Pusher event manager | `realtime_staff_chat_message_created()` - Broadcasts events |
| `staff_chat/models.py` | Database models | `StaffChatMessage` - Message storage |
| `staff_chat/serializers.py` | Data serialization | `StaffChatMessageSerializer` - API response format |

## Debug Points

### Backend Logs to Check
```
🔥 PUSHER DEBUG: Starting realtime_staff_chat_message_created for message X
🔥 PUSHER DEBUG: Hotel slug = hotel-killarney
🔥 PUSHER DEBUG: Conversation ID = 100
🔥 PUSHER DEBUG: Sending to conversation channel: hotel-killarney.staff-chat.100
🔥 PUSHER DEBUG: Found X participants to notify
🔥 PUSHER DEBUG: Sending to participant Y on channel: hotel-killarney.staff-Y-notifications
✅ Pusher event sent: hotel-killarney.staff-chat.100 → realtime_staff_chat_message_created
```

### Frontend Logs to Check
```
📡 Incoming realtime event: {channel: 'hotel-killarney.staff-chat.100', eventName: 'realtime_staff_chat_message_created'}
💬 [MessageBubble] New message received: {text: 'Hello world', sender_name: 'John Doe'}
```

## Troubleshooting Common Issues

### 1. Messages Not Appearing in Real-Time
**Check:** Backend Pusher debug logs - Are events being sent?
**Check:** Frontend channel subscriptions - Are you subscribed to the right channels?
**Check:** Event names - Frontend listening for `realtime_staff_chat_message_created`?

### 2. Channel Name Mismatches  
**Backend sends to:** `hotel-killarney.staff-chat.100`
**Frontend subscribes to:** Must match exactly

### 3. Payload Field Mismatches
**Backend sends:** `payload.text` (contains message content)
**Frontend expects:** Check what field name frontend is reading

### 4. FCM Works But Pusher Doesn't
**Indicates:** Message creation is successful, Pusher events are the problem
**Check:** Pusher credentials, channel names, event processing

## Message Creation Success Criteria

✅ **Database:** Message saved to `StaffChatMessage` table
✅ **FCM:** Push notification sent to other participants  
✅ **Pusher Events:** Both conversation and notification channels triggered
✅ **Frontend:** Message appears instantly in conversation UI
✅ **Unread Counts:** Updated for other participants in real-time

## Event Payload Structure

```json
{
  "category": "staff_chat",
  "type": "message_created",
  "payload": {
    "id": 534,
    "conversation_id": 100,
    "text": "Hello world",
    "sender_id": 45,
    "sender_name": "John Doe",
    "timestamp": "2025-12-08T16:30:00Z",
    "attachments": [],
    "is_system_message": false
  },
  "meta": {
    "hotel_slug": "hotel-killarney",
    "event_id": "abc-123-def",
    "ts": "2025-12-08T16:30:00Z",
    "scope": {
      "conversation_id": 100,
      "sender_id": 45
    }
  }
}
```