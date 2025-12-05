# ⚠️ OUTDATED - Staff-to-Staff Chat Pusher Usage Guide - DO NOT USE

## 🚫 **THIS DOCUMENTATION IS OBSOLETE**

**❌ DO NOT USE THE CODE IN THIS FILE ❌**

This documentation contains **outdated patterns** that are incompatible with the current realtime architecture:

### Problems with this guide:
1. **Event naming**: Uses `'message-created'` (hyphenated) - should be `'message_created'` (underscore)
2. **Direct Pusher binding**: Shows manual channel subscription - should use `subscribeToStaffChatConversation()`
3. **Wrong payload structure**: Uses `data.payload` - should be `data.data` in eventBus flow
4. **Legacy architecture**: Bypasses eventBus → chatStore flow

### ✅ **Use this instead:**
**See: `FRONTEND_UNIFIED_REALTIME_INTEGRATION_GUIDE.md`** for the correct, current implementation.

---

## 📡 ~~Sending Staff Chat Messages with Realtime Events~~ (OUTDATED)

### 1. Create Message & Trigger Realtime Event
```python
from notifications.notification_manager import notification_manager

# Create the staff chat message
message = StaffChatMessage.objects.create(
    conversation=conversation,
    sender=staff,
    message="Your message text"
)

# Trigger realtime event via NotificationManager
notification_manager.realtime_staff_chat_message_created(message)
```

### 2. Frontend Receives on Channel
```javascript
// Frontend subscribes to staff chat channel
const channel = pusher.subscribe('hotel-killarney.staff-chat.123');

// Listen for new messages
channel.bind('message-created', function(data) {
    console.log('New staff message:', data.payload);
    // data.payload contains: message_id, sender_name, text, etc.
});
```

### 3. Channel Format
- **Channel**: `hotel-{hotel_slug}.staff-chat.{conversation_id}`
- **Event**: `message-created`
- **Data**: Normalized event with payload containing message details

### 4. Complete Example in Views
```python
# In staff_chat/views_messages.py
message = StaffChatMessage.objects.create(
    conversation=conversation,
    sender=staff,
    message=message_text
)

# This triggers Pusher automatically via NotificationManager
broadcast_new_message(hotel_slug, conversation.id, message)
```

---

## 🚫 **END OF OUTDATED CONTENT**

**⚠️ REMINDER: This entire file is OBSOLETE**

**✅ For current implementation, see:**
- `FRONTEND_UNIFIED_REALTIME_INTEGRATION_GUIDE.md`
- Use `subscribeToStaffChatConversation(hotelSlug, conversationId)` 
- Events are `'message_created'` (underscore, not hyphen)
- Payload is at `event.data.data`, not `event.payload`
- Everything routes through eventBus → chatStore

**❌ DO NOT USE THE PATTERNS IN THIS FILE**