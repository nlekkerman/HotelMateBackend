# Staff Chat: Message Delivery & Read Receipts System

## Overview

The staff chat system has a **comprehensive message delivery and read receipt tracking** system with real-time Pusher events.

---

## Message Status Flow

### 1. Message States

```python
STATUS_CHOICES = (
    ("pending", "Pending"),      # Message sending in progress
    ("delivered", "Delivered"),   # Message reached server
    ("read", "Read")              # Message read by all recipients
)
```

### 2. Database Schema

#### Message Fields
```python
class StaffChatMessage(models.Model):
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="delivered"
    )
    delivered_at = models.DateTimeField(default=timezone.now)
    
    # Read tracking (per participant)
    is_read = models.BooleanField(default=False)  # True when ALL read
    read_by = models.ManyToManyField(
        'staff.Staff',
        blank=True,
        related_name='read_staff_messages'
    )
```

#### Conversation Fields
```python
class StaffConversation(models.Model):
    has_unread = models.BooleanField(default=False)
    
    def get_unread_count_for_staff(self, staff):
        """Get unread message count for a specific staff member"""
        return self.messages.filter(
            is_deleted=False
        ).exclude(sender=staff).exclude(read_by=staff).count()
```

---

## How Read Receipts Work

### 1. Mark Message as Read

**Method:** `message.mark_as_read_by(staff)`

```python
def mark_as_read_by(self, staff):
    """Mark message as read by a specific staff member"""
    if staff != self.sender and not self.read_by.filter(id=staff.id).exists():
        self.read_by.add(staff)
        
        # Check if ALL participants (except sender) have read
        all_participants = self.conversation.participants.exclude(
            id=self.sender.id
        )
        if self.read_by.count() >= all_participants.count():
            self.is_read = True
            self.status = 'read'
            self.save(update_fields=['is_read', 'status'])
        
        return True
    return False
```

### 2. Mark Conversation as Read

**Endpoint:** `POST /api/staff-chat/<hotel_slug>/conversations/{id}/mark_as_read/`

**What it does:**
- Marks ALL unread messages in conversation as read
- Updates `read_by` ManyToMany field
- Changes message status to 'read' when all participants have read
- Broadcasts read receipt via Pusher

**Code:**
```python
@action(detail=True, methods=['post'])
def mark_as_read(self, request, pk=None, hotel_slug=None):
    conversation = self.get_object()
    staff = Staff.objects.get(user=request.user)
    
    # Get unread messages
    unread_messages = conversation.messages.filter(
        is_deleted=False
    ).exclude(sender=staff).exclude(read_by=staff)
    
    marked_message_ids = []
    for message in unread_messages:
        message.read_by.add(staff)
        marked_message_ids.append(message.id)
        
        # Check if ALL participants have read
        all_participants = conversation.participants.exclude(
            id=message.sender.id
        )
        if message.read_by.count() >= all_participants.count():
            message.is_read = True
            message.status = 'read'
            message.save(update_fields=['is_read', 'status'])
    
    # Broadcast read receipt
    broadcast_read_receipt(
        hotel_slug,
        conversation.id,
        {
            'staff_id': staff.id,
            'staff_name': f"{staff.first_name} {staff.last_name}",
            'message_ids': marked_message_ids,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({
        'success': True,
        'marked_count': len(marked_message_ids),
        'message_ids': marked_message_ids
    })
```

### 3. Bulk Mark as Read

**Endpoint:** `POST /api/staff-chat/<hotel_slug>/conversations/bulk-mark-as-read/`

**Purpose:** Mark multiple conversations as read in one request (performance optimization)

**Request:**
```json
{
  "conversation_ids": [1, 2, 3, 4, 5]
}
```

**Response:**
```json
{
  "success": true,
  "marked_conversations": 5,
  "total_messages_marked": 45
}
```

### 4. Get Unread Count

**Endpoint:** `GET /api/staff-chat/<hotel_slug>/conversations/unread-count/`

**Response:**
```json
{
  "total_unread": 42,
  "conversations_with_unread": 5,
  "breakdown": [
    {
      "conversation_id": 1,
      "unread_count": 15,
      "title": "Team Chat",
      "is_group": true
    },
    {
      "conversation_id": 2,
      "unread_count": 12,
      "title": "John Doe",
      "is_group": false
    }
  ]
}
```

---

## Pusher Real-Time Events

### Event 1: New Message

**Event:** `new-message`  
**Channel:** `{hotel_slug}-staff-conversation-{conversation_id}`

**Triggered when:** Message is sent

**Payload:**
```json
{
  "message_id": 123,
  "conversation_id": 45,
  "sender": {
    "id": 10,
    "name": "John Doe",
    "profile_image_url": "https://..."
  },
  "message": "Hello team!",
  "timestamp": "2025-11-22T10:30:00Z",
  "status": "delivered",
  "reply_to": null,
  "attachments": []
}
```

**Frontend Usage:**
```javascript
const channel = pusher.subscribe(
  `${hotelSlug}-staff-conversation-${conversationId}`
);

channel.bind('new-message', (data) => {
  // Add message to chat
  setMessages(prev => [...prev, data]);
  
  // Update conversation list
  updateConversationLastMessage(data.conversation_id, data);
  
  // Show notification if not in conversation
  if (!isCurrentConversation) {
    showNotification(`${data.sender.name}: ${data.message}`);
  }
});
```

---

### Event 2: Read Receipts

**Event:** `messages-read`  
**Channel:** `{hotel_slug}-staff-conversation-{conversation_id}`

**Triggered when:** Staff marks messages as read

**Payload:**
```json
{
  "staff_id": 10,
  "staff_name": "John Doe",
  "message_ids": [123, 124, 125, 126],
  "timestamp": "2025-11-22T10:35:00Z"
}
```

**Frontend Usage:**
```javascript
channel.bind('messages-read', (data) => {
  console.log(`${data.staff_name} read ${data.message_ids.length} messages`);
  
  // Update message read status
  setMessages(prev => prev.map(msg => 
    data.message_ids.includes(msg.id)
      ? { ...msg, read_by: [...msg.read_by, {
          id: data.staff_id,
          name: data.staff_name
        }]}
      : msg
  ));
  
  // Update UI to show double checkmarks
  updateReadReceipts(data.message_ids, data.staff_id);
});
```

---

### Event 3: Message Edited

**Event:** `message-edited`  
**Channel:** `{hotel_slug}-staff-conversation-{conversation_id}`

**Payload:**
```json
{
  "message_id": 123,
  "new_message": "Updated message text",
  "edited_at": "2025-11-22T10:40:00Z",
  "editor_id": 10,
  "editor_name": "John Doe"
}
```

---

### Event 4: Message Deleted

**Event:** `message-deleted`  
**Channel:** `{hotel_slug}-staff-conversation-{conversation_id}`

**Payload:**
```json
{
  "message_id": 123,
  "deleted_at": "2025-11-22T10:45:00Z",
  "deleted_by": {
    "id": 10,
    "name": "John Doe"
  }
}
```

---

### Event 5: Typing Indicator

**Event:** `user-typing`  
**Channel:** `{hotel_slug}-staff-conversation-{conversation_id}`

**Payload:**
```json
{
  "staff_id": 10,
  "staff_name": "John Doe",
  "is_typing": true,
  "timestamp": "2025-11-22T10:50:00Z"
}
```

**Frontend Usage:**
```javascript
channel.bind('user-typing', (data) => {
  if (data.is_typing) {
    showTypingIndicator(data.staff_name);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
      hideTypingIndicator(data.staff_id);
    }, 3000);
  } else {
    hideTypingIndicator(data.staff_id);
  }
});
```

---

### Event 6: Personal Notifications

**Channel:** `{hotel_slug}-staff-{staff_id}-notifications`

**Events:**
- `message-mention` - When mentioned with @name
- `new-conversation` - Added to new conversation

**Mention Payload:**
```json
{
  "message_id": 123,
  "conversation_id": 45,
  "mentioned_by": {
    "id": 15,
    "name": "Jane Smith"
  },
  "message_preview": "Hey @john, can you check...",
  "timestamp": "2025-11-22T11:00:00Z"
}
```

---

## Read Receipt Display Logic

### Single Checkmark (✓) - Delivered
```javascript
message.status === 'delivered' && message.read_by.length === 0
```

### Double Checkmark (✓✓) - Read by Some
```javascript
message.status === 'delivered' && message.read_by.length > 0
```

### Blue Double Checkmark (✓✓) - Read by All
```javascript
message.status === 'read' || message.is_read === true
```

### Display Who Read (Group Chats)
```javascript
const readByNames = message.read_by
  .map(staff => staff.name)
  .join(', ');

// "Read by John, Jane, and Sarah"
```

---

## Performance Optimizations

### 1. Bulk Operations
- `bulk_mark_as_read()` - Mark multiple conversations in one request
- Reduces API calls from N to 1

### 2. Prefetching
```python
messages = conversation.messages.filter(
    is_deleted=False
).select_related('sender').prefetch_related(
    'attachments', 'read_by'
).order_by('timestamp')
```

### 3. Conversation-Level Caching
```python
has_unread = models.BooleanField(default=False)
```
Quick flag to show unread badge without querying messages

---

## Frontend Integration Example

### React Hook for Message Tracking

```javascript
const useMessageTracking = (conversationId, hotelSlug) => {
  const [messages, setMessages] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  useEffect(() => {
    const pusher = new Pusher(process.env.REACT_APP_PUSHER_KEY, {
      cluster: process.env.REACT_APP_PUSHER_CLUSTER,
    });
    
    const channel = pusher.subscribe(
      `${hotelSlug}-staff-conversation-${conversationId}`
    );
    
    // New message
    channel.bind('new-message', (data) => {
      setMessages(prev => [...prev, data]);
      
      // Increment unread if not from current user
      if (data.sender.id !== currentStaffId) {
        setUnreadCount(prev => prev + 1);
      }
    });
    
    // Read receipts
    channel.bind('messages-read', (data) => {
      // Update read status
      setMessages(prev => prev.map(msg =>
        data.message_ids.includes(msg.id)
          ? {
              ...msg,
              read_by: [
                ...msg.read_by,
                { id: data.staff_id, name: data.staff_name }
              ]
            }
          : msg
      ));
      
      // Decrease unread count
      if (data.staff_id === currentStaffId) {
        setUnreadCount(0);
      }
    });
    
    return () => {
      channel.unbind_all();
      pusher.unsubscribe(
        `${hotelSlug}-staff-conversation-${conversationId}`
      );
    };
  }, [conversationId, hotelSlug]);
  
  // Mark as read when conversation is viewed
  const markAsRead = async () => {
    try {
      await api.post(
        `/staff-chat/${hotelSlug}/conversations/${conversationId}/mark_as_read/`
      );
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };
  
  return { messages, unreadCount, markAsRead };
};
```

---

## Summary

✅ **Delivered Status** - All messages get `status="delivered"` by default  
✅ **Read Tracking** - `read_by` ManyToMany tracks who read each message  
✅ **Read Receipts** - Real-time via Pusher `messages-read` event  
✅ **Bulk Operations** - Efficient bulk mark-as-read endpoint  
✅ **Unread Counts** - Conversation-level and system-wide unread counts  
✅ **Performance** - Optimized queries with prefetching  
✅ **Real-time** - All status changes broadcast via Pusher  

The system is **fully implemented and production-ready**! 🚀
