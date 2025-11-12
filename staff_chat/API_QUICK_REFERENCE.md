# Staff Chat API Quick Reference

## 🔥 Most Common Endpoints

### Get Unread Count (App Badge)
```http
GET /api/staff-chat/{hotel_slug}/conversations/unread-count/
```
Returns total unread messages across all conversations.

### Mark Conversation as Read
```http
POST /api/staff-chat/{hotel_slug}/conversations/{id}/mark_as_read/
```
Marks all messages in a conversation as read.

### Bulk Mark as Read
```http
POST /api/staff-chat/{hotel_slug}/conversations/bulk-mark-as-read/
Content-Type: application/json

{
  "conversation_ids": [1, 2, 3, 4, 5]
}
```
Mark multiple conversations as read in one call.

### Send Message with Mentions
```http
POST /api/staff-chat/{hotel_slug}/conversations/{id}/send-message/
Content-Type: application/json

{
  "message": "Hey @John, can you check this?",
  "reply_to": 123  // optional
}
```
Sends message, automatically detects @mentions, sends FCM.

### Upload File with Message
```http
POST /api/staff-chat/{hotel_slug}/conversations/{id}/upload/
Content-Type: multipart/form-data

files: [File, File]
message: "Here are the documents"
reply_to: 123  // optional
```
Uploads files with optional text message.

---

## 📱 Pusher Events to Listen For

### Conversation Channel: `{hotel_slug}-staff-conversation-{id}`

#### new-message
```json
{
  "id": 123,
  "sender_info": {...},
  "message": "Hello!",
  "timestamp": "2025-11-12T10:30:00Z",
  "attachments": [...],
  "mentions": [...]
}
```

#### messages-read
```json
{
  "staff_id": 42,
  "staff_name": "John Smith",
  "message_ids": [123, 124, 125],
  "timestamp": "2025-11-12T10:30:00Z"
}
```

#### message-edited
```json
{
  "id": 123,
  "message": "Updated text",
  "is_edited": true,
  "edited_at": "2025-11-12T10:30:00Z"
}
```

#### message-deleted
```json
{
  "message_id": 123,
  "hard_delete": false,
  "deleted_by": 42,
  "timestamp": "2025-11-12T10:30:00Z"
}
```

#### message-reaction
```json
{
  "message_id": 123,
  "action": "add",  // or "remove"
  "reaction": {
    "id": 5,
    "emoji": "👍",
    "staff": 42,
    "staff_name": "John Smith"
  }
}
```

#### user-typing
```json
{
  "staff_id": 42,
  "staff_name": "John Smith",
  "is_typing": true
}
```

### Personal Channel: `{hotel_slug}-staff-{staff_id}-notifications`

#### message-mention
```json
{
  "conversation_id": 7,
  "message_id": 123,
  "sender_id": 42,
  "sender_name": "John Smith",
  "message": "Hey @you, check this!"
}
```

#### new-conversation
```json
{
  "conversation_id": 7,
  "created_by_id": 42,
  "created_by_name": "John Smith",
  "is_group": true,
  "title": "Project Team"
}
```

---

## 🔔 FCM Notification Data

### Message Notification
```json
{
  "type": "staff_chat_message",
  "conversation_id": "7",
  "sender_id": "42",
  "sender_name": "John Smith",
  "is_group": "true",
  "hotel_slug": "hilton-downtown",
  "click_action": "/staff-chat/hilton-downtown/conversation/7",
  "url": "https://hotelsmates.com/staff-chat/hilton-downtown/conversation/7"
}
```

### Mention Notification (High Priority)
```json
{
  "type": "staff_chat_mention",
  "conversation_id": "7",
  "sender_id": "42",
  "sender_name": "John Smith",
  "mentioned_staff_id": "15",
  "is_group": "true",
  "hotel_slug": "hilton-downtown",
  "priority": "high",
  "click_action": "/staff-chat/hilton-downtown/conversation/7",
  "url": "https://hotelsmates.com/staff-chat/hilton-downtown/conversation/7"
}
```

### File Notification
```json
{
  "type": "staff_chat_file",
  "conversation_id": "7",
  "sender_id": "42",
  "sender_name": "John Smith",
  "file_count": "3",
  "has_attachments": "true",
  "is_group": "false",
  "hotel_slug": "hilton-downtown",
  "click_action": "/staff-chat/hilton-downtown/conversation/7",
  "url": "https://hotelsmates.com/staff-chat/hilton-downtown/conversation/7"
}
```

---

## 💾 Serializer Response Examples

### Conversation List Item
```json
{
  "id": 7,
  "title": "Project Team",
  "display_title": "Project Team",
  "is_group": true,
  "participants_info": [
    {
      "id": 42,
      "name": "John Smith",
      "avatar": "https://...",
      "is_on_duty": true
    }
  ],
  "last_message": {
    "id": 123,
    "message": "Let's meet at 3pm",
    "sender_id": 42,
    "sender_name": "John Smith",
    "timestamp": "2025-11-12T10:30:00Z",
    "has_attachments": false
  },
  "unread_count": 5,
  "has_unread": true,
  "created_at": "2025-11-10T09:00:00Z",
  "updated_at": "2025-11-12T10:30:00Z"
}
```

### Message Detail
```json
{
  "id": 123,
  "conversation": 7,
  "sender_info": {
    "id": 42,
    "name": "John Smith",
    "avatar": "https://...",
    "department": "Reception",
    "is_on_duty": true
  },
  "message": "Hey @Sarah, check this out!",
  "timestamp": "2025-11-12T10:30:00Z",
  "status": "delivered",
  "is_read": false,
  "read_by_count": 2,
  "read_by_list": [
    {
      "id": 15,
      "name": "Sarah Williams",
      "avatar": "https://..."
    }
  ],
  "is_read_by_current_user": true,
  "is_edited": false,
  "is_deleted": false,
  "reply_to_message": {
    "id": 122,
    "message": "What time is the meeting?",
    "sender_name": "Sarah Williams",
    "timestamp": "2025-11-12T10:25:00Z"
  },
  "attachments": [
    {
      "id": 5,
      "file_name": "report.pdf",
      "file_type": "pdf",
      "file_size": 524288,
      "file_url": "https://...",
      "uploaded_at": "2025-11-12T10:30:00Z"
    }
  ],
  "reactions": [
    {
      "id": 8,
      "emoji": "👍",
      "staff": 15,
      "staff_name": "Sarah Williams",
      "created_at": "2025-11-12T10:31:00Z"
    }
  ],
  "reaction_summary": {
    "👍": 3,
    "❤️": 1
  },
  "mentioned_staff": [
    {
      "id": 15,
      "name": "Sarah Williams",
      "avatar": "https://..."
    }
  ]
}
```

---

## 🎨 UI Components to Build

### 1. Unread Badge
```javascript
// On app header/nav
<Badge count={totalUnread}>
  <ChatIcon />
</Badge>
```

### 2. Conversation List Item
```javascript
<ConversationItem>
  <Avatar src={displayAvatar} />
  <div>
    <Title>{displayTitle}</Title>
    <LastMessage>{lastMessage.message}</LastMessage>
  </div>
  {unreadCount > 0 && <Badge count={unreadCount} />}
</ConversationItem>
```

### 3. Message Bubble
```javascript
<MessageBubble 
  isOwn={message.sender.id === currentUserId}
  hasReply={!!message.reply_to_message}
>
  {message.reply_to_message && (
    <ReplyPreview message={message.reply_to_message} />
  )}
  
  <MessageText>{message.message}</MessageText>
  
  {message.attachments.map(att => (
    <Attachment key={att.id} {...att} />
  ))}
  
  <MessageFooter>
    <Timestamp>{message.timestamp}</Timestamp>
    {isOwn && (
      <ReadReceipts>
        {message.read_by_list.map(staff => (
          <Avatar key={staff.id} src={staff.avatar} size="xs" />
        ))}
      </ReadReceipts>
    )}
  </MessageFooter>
  
  <ReactionBar reactions={message.reaction_summary} />
</MessageBubble>
```

### 4. Read Receipts Tooltip
```javascript
<Tooltip>
  <ReadByList>
    Read by:
    {message.read_by_list.map(staff => (
      <li key={staff.id}>{staff.name}</li>
    ))}
  </ReadByList>
</Tooltip>
```

### 5. Mark All as Read Button
```javascript
<Button onClick={handleMarkAllAsRead}>
  Mark All as Read ({conversationsWithUnread})
</Button>
```

---

## ⚡ Performance Tips

1. **Paginate Messages**
   ```http
   GET /messages/?limit=50&before_id=123
   ```
   Load 50 at a time, use `before_id` for infinite scroll.

2. **Debounce Typing Indicators**
   ```javascript
   const sendTyping = debounce(() => {
     pusher.trigger('user-typing', { is_typing: true });
   }, 500);
   ```

3. **Batch Mark as Read**
   Only call mark-as-read when:
   - User opens conversation
   - User scrolls to bottom
   - App returns to foreground

4. **Cache Unread Counts**
   ```javascript
   // Refresh every 30 seconds or on Pusher event
   const unreadCache = useSWR('/unread-count/', {
     refreshInterval: 30000
   });
   ```

5. **Optimize Pusher Subscriptions**
   ```javascript
   // Only subscribe to active conversations
   useEffect(() => {
     if (isConversationOpen) {
       const channel = pusher.subscribe(`${hotelSlug}-staff-conversation-${id}`);
       return () => channel.unsubscribe();
     }
   }, [isConversationOpen]);
   ```

---

## 🔒 Security Checklist

- ✅ Verify user is conversation participant before showing messages
- ✅ Only allow editing own messages
- ✅ Only allow deleting own messages (or manager override)
- ✅ Validate hotel_slug matches user's hotel
- ✅ Sanitize message content before display
- ✅ Rate limit message sending
- ✅ Validate file types and sizes before upload
- ✅ Use signed URLs for file downloads (if using private storage)

---

## 📞 Support

For issues or questions:
1. Check `ENHANCEMENTS_SUMMARY.md` for detailed documentation
2. Review model definitions in `models.py`
3. Check view implementations in `views.py` and `views_messages.py`
4. Test endpoints using Postman/Thunder Client
5. Check Django logs for errors

---

**Happy Chatting! 💬**
