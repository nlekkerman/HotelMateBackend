# Staff Chat Enhancements Summary

## Overview
The staff chat system has been enhanced with comprehensive user integration, FCM notifications, seen/read status tracking, and message count management - providing a complete enterprise-grade chat experience similar to WhatsApp/Slack for group and 1-on-1 conversations.

---

## ✅ Already Implemented Features

### 1. **User & Staff Integration**
- **Staff Model** has `user` field (OneToOneField with Django User)
- **FCM Token Storage** in Staff model (`fcm_token` field)
- Staff profile linked to Django authentication system

### 2. **FCM Push Notifications** 
Located in: `staff_chat/fcm_utils.py`

**Available notification types:**
- `send_new_message_notification()` - New message alerts
- `send_mention_notification()` - @mention alerts (high priority)
- `send_new_conversation_notification()` - Added to conversation
- `send_file_attachment_notification()` - File shared alerts
- `notify_conversation_participants()` - Bulk notify all participants

**Features:**
- Automatic FCM integration in `send_message` view
- Smart mention detection (@firstname or @firstname lastname)
- File attachment notifications with type detection
- Deep linking to specific conversations
- Excludes sender from notifications

### 3. **Read Receipt System**
**Models** (`staff_chat/models.py`):
- `read_by` ManyToManyField on `StaffChatMessage`
- `is_read` boolean flag (all participants read)
- `mark_as_read_by(staff)` method
- `get_unread_count_for_staff(staff)` on conversation

**Message Status:**
- `pending` - Sending in progress
- `delivered` - Reached server
- `read` - Read by all participants

### 4. **Real-time Features (Pusher)**
Located in: `staff_chat/pusher_utils.py`

**Broadcast events:**
- `new-message` - New messages
- `message-edited` - Message edits
- `message-deleted` - Message deletions
- `message-reaction` - Emoji reactions
- `messages-read` - Read receipts
- `user-typing` - Typing indicators
- `message-mention` - Personal mention notifications
- `attachment-uploaded` - File uploads
- `attachment-deleted` - File deletions

**Channels:**
- Conversation channels: `{hotel_slug}-staff-conversation-{id}`
- Personal channels: `{hotel_slug}-staff-{staff_id}-notifications`

### 5. **Message Features**
- **Replies** - Thread support with `reply_to` field
- **Mentions** - @user tagging with auto-detection
- **Reactions** - 10 emoji reactions per message
- **Attachments** - Images, PDFs, documents (50MB max)
- **Edit** - Edit own messages (marked as edited)
- **Delete** - Soft/hard delete with permissions
- **Forward** - Forward to multiple conversations

### 6. **Conversation Management**
- **1-on-1 Conversations** - Auto-created, unique per pair
- **Group Chats** - Multiple participants, custom titles
- **Participant Management** - Add/remove members
- **Archive** - Hide conversations without deleting
- **Smart Deduplication** - Prevents duplicate 1-on-1 chats

---

## 🆕 New Enhancements Added

### 1. **Enhanced Read Receipt Broadcasting**
**Location:** `staff_chat/views.py` - `mark_as_read()` action

**Improvements:**
- ✅ Broadcasts read receipts via Pusher when messages are marked as read
- ✅ Returns marked message IDs for client-side updates
- ✅ Updates message status to 'read' when all participants read
- ✅ Real-time read receipt updates for all participants

**Request:**
```http
POST /api/staff-chat/{hotel_slug}/conversations/{id}/mark_as_read/
```

**Response:**
```json
{
  "success": true,
  "marked_count": 15,
  "message_ids": [123, 124, 125, ...]
}
```

**Pusher Event:**
```json
{
  "staff_id": 42,
  "staff_name": "John Smith",
  "message_ids": [123, 124, 125],
  "timestamp": "2025-11-12T10:30:00Z"
}
```

---

### 2. **Bulk Mark as Read**
**Location:** `staff_chat/views.py` - `bulk_mark_as_read()` action

**Purpose:** Mark multiple conversations as read in one API call - perfect for "Mark All as Read" functionality.

**Request:**
```http
POST /api/staff-chat/{hotel_slug}/conversations/bulk-mark-as-read/
Content-Type: application/json

{
  "conversation_ids": [1, 2, 3, 5, 8, 13]
}
```

**Response:**
```json
{
  "success": true,
  "marked_conversations": 6,
  "total_messages_marked": 45
}
```

**Features:**
- ✅ Marks all unread messages across multiple conversations
- ✅ Broadcasts read receipts for each conversation
- ✅ Only marks conversations where user is participant
- ✅ Returns summary of marked conversations and messages

---

### 3. **Global Unread Count**
**Location:** `staff_chat/views.py` - `unread_count()` action

**Purpose:** Get total unread count across ALL conversations for app badge display.

**Request:**
```http
GET /api/staff-chat/{hotel_slug}/conversations/unread-count/
```

**Response:**
```json
{
  "total_unread": 42,
  "conversations_with_unread": 5,
  "breakdown": [
    {
      "conversation_id": 7,
      "unread_count": 15,
      "title": "Team Chat",
      "is_group": true
    },
    {
      "conversation_id": 3,
      "unread_count": 12,
      "title": "John Doe",
      "is_group": false
    },
    {
      "conversation_id": 5,
      "unread_count": 8,
      "title": "Sarah Williams",
      "is_group": false
    }
  ]
}
```

**Features:**
- ✅ Single API call for badge count
- ✅ Per-conversation breakdown sorted by unread count
- ✅ Display-friendly titles (participant names or group titles)
- ✅ Distinguishes between group and 1-on-1 chats

**Use Cases:**
- App badge numbers
- Notification center badges
- "You have 42 unread messages" displays
- Prioritized conversation list

---

### 4. **Individual Message Read Tracking**
**Location:** `staff_chat/views_messages.py` - `mark_message_as_read()`

**Purpose:** Mark a single message as read - useful for progressive loading or individual message visibility tracking.

**Request:**
```http
POST /api/staff-chat/{hotel_slug}/messages/{message_id}/mark-as-read/
```

**Response:**
```json
{
  "success": true,
  "was_unread": true,
  "message": {
    "id": 123,
    "message": "Hello team!",
    "is_read_by_current_user": true,
    "read_by_count": 3,
    "read_by_list": [
      {
        "id": 5,
        "name": "John Smith",
        "avatar": "https://..."
      }
    ],
    ...
  }
}
```

**Features:**
- ✅ Mark individual messages as read
- ✅ Returns updated message with read status
- ✅ Broadcasts read receipt to participants
- ✅ Idempotent (safe to call multiple times)

**Use Cases:**
- Progressive message loading
- Individual message visibility tracking
- Read receipts in group chats
- "Seen by" indicators

---

## 🔄 Updated Endpoints Summary

### **Conversation Endpoints**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/conversations/` | List all conversations |
| POST | `/conversations/` | Create new conversation |
| GET | `/conversations/{id}/` | Get conversation details |
| POST | `/conversations/{id}/mark_as_read/` | Mark conversation as read ✨ |
| GET | `/conversations/unread-count/` | Get global unread count 🆕 |
| POST | `/conversations/bulk-mark-as-read/` | Bulk mark as read 🆕 |
| GET | `/conversations/for-forwarding/` | List for forward UI |

### **Message Endpoints**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/conversations/{id}/send-message/` | Send message |
| GET | `/conversations/{id}/messages/` | Get messages (paginated) |
| POST | `/messages/{id}/mark-as-read/` | Mark message as read 🆕 |
| PATCH | `/messages/{id}/edit/` | Edit message |
| DELETE | `/messages/{id}/delete/` | Delete message |
| POST | `/messages/{id}/react/` | Add reaction |
| DELETE | `/messages/{id}/react/{emoji}/` | Remove reaction |
| POST | `/messages/{id}/forward/` | Forward message |

### **Attachment Endpoints**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/conversations/{id}/upload/` | Upload files |
| DELETE | `/attachments/{id}/delete/` | Delete attachment |
| GET | `/attachments/{id}/url/` | Get attachment URL |

---

## 📊 Data Flow Examples

### Sending a Message
```
1. Client sends message → POST /send-message/
2. Server creates message in DB
3. Server detects @mentions
4. Server broadcasts via Pusher → new-message event
5. Server sends FCM to participants (excludes sender)
6. Server sends FCM to mentioned users (high priority)
7. Response returned to sender
```

### Reading Messages
```
1. Client opens conversation
2. Client calls → POST /mark_as_read/
3. Server marks messages as read in DB
4. Server broadcasts read receipt via Pusher
5. Other clients receive read receipt
6. UI updates "Seen by John" indicators
```

### Checking Unread Count
```
1. App loads → GET /unread-count/
2. Server calculates across all conversations
3. Returns total + breakdown
4. Client displays badge: "42 unread"
5. Client can show prioritized list
```

---

## 🔔 Notification Strategy

### When to Send FCM

**Always:**
- New messages (except from self)
- @mentions (high priority)
- New conversation invites
- File attachments

**Never:**
- Messages you sent yourself
- Messages you've already read
- From archived conversations
- When user has no FCM token

### Notification Priority
```
High Priority:
- @mentions
- Direct messages (1-on-1)

Normal Priority:
- Group messages
- File shares
```

---

## 💡 Frontend Integration Guide

### 1. **Display Unread Badges**
```javascript
// On app load/resume
const response = await fetch(
  `/api/staff-chat/${hotelSlug}/conversations/unread-count/`
);
const { total_unread, breakdown } = await response.json();

// Update app badge
updateAppBadge(total_unread);

// Show per-conversation badges
breakdown.forEach(conv => {
  updateConversationBadge(conv.conversation_id, conv.unread_count);
});
```

### 2. **Mark as Read When Viewing**
```javascript
// When user opens a conversation
async function openConversation(conversationId) {
  // Load messages
  const messages = await loadMessages(conversationId);
  
  // Mark as read
  await fetch(
    `/api/staff-chat/${hotelSlug}/conversations/${conversationId}/mark_as_read/`,
    { method: 'POST' }
  );
  
  // Listen for new messages
  pusherChannel.bind('new-message', handleNewMessage);
  pusherChannel.bind('messages-read', handleReadReceipt);
}
```

### 3. **Mark All as Read**
```javascript
// "Mark All as Read" button
async function markAllAsRead() {
  const unreadConversationIds = getUnreadConversationIds();
  
  const response = await fetch(
    `/api/staff-chat/${hotelSlug}/conversations/bulk-mark-as-read/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_ids: unreadConversationIds })
    }
  );
  
  const { marked_conversations } = await response.json();
  showNotification(`Marked ${marked_conversations} conversations as read`);
}
```

### 4. **Handle Read Receipts**
```javascript
// Listen for read receipts
pusherChannel.bind('messages-read', (data) => {
  const { staff_id, staff_name, message_ids } = data;
  
  // Update UI to show "Read by [staff_name]"
  message_ids.forEach(msgId => {
    updateMessageReadStatus(msgId, staff_id, staff_name);
  });
});
```

### 5. **Handle FCM Notifications**
```javascript
// When FCM notification received
onMessageReceived((notification) => {
  const { type, conversation_id, sender_id } = notification.data;
  
  if (type === 'staff_chat_message') {
    // Show notification
    showNotification(notification.title, notification.body);
    
    // If conversation is open, mark as read
    if (isConversationOpen(conversation_id)) {
      markConversationAsRead(conversation_id);
    } else {
      // Increment badge
      incrementUnreadCount();
    }
  }
  
  if (type === 'staff_chat_mention') {
    // High priority notification
    showHighPriorityNotification(notification);
  }
});
```

---

## 🎯 Best Practices

### Performance
- ✅ Use pagination for message loading (`limit` & `before_id`)
- ✅ Cache unread counts locally, refresh periodically
- ✅ Mark as read in batches when possible
- ✅ Use Pusher for real-time updates instead of polling

### User Experience
- ✅ Show "Seen by" with avatars in group chats
- ✅ Display typing indicators
- ✅ Highlight @mentions in messages
- ✅ Show unread badge counts prominently
- ✅ Auto-mark as read when messages are visible

### Notifications
- ✅ Request FCM permission on first launch
- ✅ Store FCM token on login
- ✅ Update token on device change
- ✅ Allow users to customize notification preferences
- ✅ Mute archived conversations

---

## 🔐 Permissions

All endpoints require:
- ✅ `IsAuthenticated` - User must be logged in
- ✅ `IsStaffMember` - User must have staff profile
- ✅ `IsSameHotel` - Staff must belong to the hotel in URL
- ✅ `IsConversationParticipant` - For conversation-specific actions

---

## 🐛 Troubleshooting

### Messages not marked as read
- Check user is participant in conversation
- Verify mark_as_read endpoint is called
- Check Pusher connection for read receipts

### FCM not received
- Verify staff has valid `fcm_token` in database
- Check FCM service configuration
- Ensure user hasn't disabled notifications
- Check device notification permissions

### Unread count incorrect
- Call `/unread-count/` endpoint to refresh
- Check database for orphaned read_by relationships
- Verify conversation participant membership

---

## 📝 Migration Notes

No database migrations are required! All enhancements use existing models and fields:
- `read_by` ManyToManyField (already exists)
- `fcm_token` field on Staff (already exists)
- `user` field on Staff (already exists)

---

## 🚀 Future Enhancements (Optional)

Consider adding:
- [ ] Message search functionality
- [ ] Voice message support
- [ ] Video message support
- [ ] Message pinning in groups
- [ ] User blocking/muting
- [ ] Message scheduling
- [ ] Read receipt timestamps per user
- [ ] "Delivered" vs "Read" distinction
- [ ] Online/offline status indicators
- [ ] Last seen timestamps
- [ ] Message encryption (E2E)

---

## 📚 Related Documentation

- FCM Setup: `/notifications/README.md`
- Pusher Setup: `/chat/README.md`
- Staff Model: `/staff/models.py`
- API Documentation: Auto-generated via DRF

---

**Last Updated:** November 12, 2025
**Version:** 2.0
**Status:** ✅ Production Ready
