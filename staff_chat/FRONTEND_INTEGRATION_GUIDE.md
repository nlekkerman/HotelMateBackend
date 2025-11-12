# Staff Chat Frontend Integration Guide

## 🚀 Quick Start

Your backend is ready! Here's everything your frontend team needs to integrate the staff chat.

---

## 📡 API Endpoints

Base URL: `/api/staff-chat/{hotel_slug}/`

### **Authentication**
All endpoints require:
```javascript
headers: {
  'Authorization': 'Token {user_auth_token}',
  'Content-Type': 'application/json'
}
```

---

## 🔑 Core Endpoints

### 1. Get Unread Count (App Badge)
```javascript
GET /api/staff-chat/{hotel_slug}/conversations/unread-count/

Response:
{
  "total_unread": 42,
  "conversations_with_unread": 5,
  "breakdown": [
    {
      "conversation_id": 7,
      "unread_count": 15,
      "title": "Team Chat",
      "is_group": true
    }
  ]
}
```

**Usage:**
```javascript
// Update app badge
const { total_unread } = await fetchUnreadCount();
setBadgeCount(total_unread);
```

---

### 2. Get Conversation List
```javascript
GET /api/staff-chat/{hotel_slug}/conversations/

Response:
{
  "results": [
    {
      "id": 7,
      "display_title": "Team Chat",
      "display_avatar": "https://...",
      "is_group": true,
      "participants_info": [...],
      "last_message": {
        "message": "Let's meet at 3pm",
        "sender_name": "John Smith",
        "timestamp": "2025-11-12T10:30:00Z"
      },
      "unread_count": 5,
      "has_unread": true,
      "updated_at": "2025-11-12T10:30:00Z"
    }
  ]
}
```

---

### 3. Get Messages (Paginated)
```javascript
GET /api/staff-chat/{hotel_slug}/conversations/{id}/messages/
Query: ?limit=50&before_id=123

Response:
{
  "messages": [
    {
      "id": 123,
      "sender_info": {
        "id": 42,
        "name": "John Smith",
        "avatar": "https://...",
        "is_on_duty": true
      },
      "message": "Hey @Sarah, check this!",
      "timestamp": "2025-11-12T10:30:00Z",
      "is_read_by_current_user": false,
      "read_by_count": 2,
      "read_by_list": [...],
      "attachments": [...],
      "reactions": [...],
      "reply_to_message": {...},
      "mentioned_staff": [...]
    }
  ],
  "count": 50,
  "has_more": true
}
```

**Infinite Scroll:**
```javascript
// Load initial messages
const { messages } = await fetchMessages(conversationId, { limit: 50 });

// Load more (older messages)
const oldestMessageId = messages[0].id;
const { messages: olderMessages } = await fetchMessages(conversationId, {
  limit: 50,
  before_id: oldestMessageId
});
```

---

### 4. Send Message
```javascript
POST /api/staff-chat/{hotel_slug}/conversations/{id}/send-message/

Body:
{
  "message": "Hey @John, check this out!",
  "reply_to": 122  // optional
}

Response:
{
  "id": 123,
  "message": "Hey @John, check this out!",
  "sender_info": {...},
  "timestamp": "2025-11-12T10:30:00Z",
  ...
}
```

**With @Mentions:**
- Backend auto-detects @mentions
- Sends high-priority FCM to mentioned users
- No special syntax needed, just use @Name

---

### 5. Mark as Read
```javascript
// Mark entire conversation as read
POST /api/staff-chat/{hotel_slug}/conversations/{id}/mark_as_read/

Response:
{
  "success": true,
  "marked_count": 15,
  "message_ids": [123, 124, 125, ...]
}
```

```javascript
// Mark individual message as read
POST /api/staff-chat/{hotel_slug}/messages/{id}/mark-as-read/

Response:
{
  "success": true,
  "was_unread": true,
  "message": {...}  // updated message with read status
}
```

**When to call:**
- When user opens conversation
- When user scrolls to bottom
- When app returns to foreground (if conversation is open)

---

### 6. Bulk Mark as Read
```javascript
POST /api/staff-chat/{hotel_slug}/conversations/bulk-mark-as-read/

Body:
{
  "conversation_ids": [1, 2, 3, 4, 5]
}

Response:
{
  "success": true,
  "marked_conversations": 5,
  "total_messages_marked": 45
}
```

**For "Mark All as Read" button**

---

### 7. Upload Files
```javascript
POST /api/staff-chat/{hotel_slug}/conversations/{id}/upload/
Content-Type: multipart/form-data

Body:
{
  files: [File, File],           // multiple files
  message: "Here are the docs",  // optional text
  reply_to: 123                  // optional
}

Response:
{
  "success": true,
  "message": {...},              // created message
  "attachments": [...]           // uploaded files
}
```

**Supported formats:**
- Images: jpg, jpeg, png, gif, webp, bmp
- Documents: pdf, doc, docx, xls, xlsx, txt, csv
- Max size: 50MB per file

---

### 8. Add Reaction
```javascript
POST /api/staff-chat/{hotel_slug}/messages/{id}/react/

Body:
{
  "emoji": "👍"
}

Response:
{
  "id": 5,
  "emoji": "👍",
  "staff": 42,
  "staff_name": "John Smith",
  "created_at": "2025-11-12T10:30:00Z"
}
```

**Available emojis:**
👍 ❤️ 😊 😂 😮 😢 🎉 🔥 ✅ 👏

**Note:** Each user can only have one reaction per message (adding a new one removes the old one)

---

### 9. Create Conversation
```javascript
POST /api/staff-chat/{hotel_slug}/conversations/

Body:
{
  "participant_ids": [5, 8, 12],  // other participants (not including self)
  "title": "Project Team"         // optional (recommended for groups)
}

Response:
{
  "id": 7,
  "title": "Project Team",
  "is_group": true,
  "participants_info": [...],
  "created_at": "2025-11-12T10:30:00Z"
}
```

**Note:** Backend prevents duplicate 1-on-1 conversations automatically

---

## 📱 Real-time with Pusher

### Setup
```javascript
import Pusher from 'pusher-js';

const pusher = new Pusher('6744ef8e4ff09af2a849', {
  cluster: 'eu',
  encrypted: true
});
```

### Subscribe to Channels

#### 1. Conversation Channel
```javascript
const conversationChannel = pusher.subscribe(
  `${hotelSlug}-staff-conversation-${conversationId}`
);

// New message
conversationChannel.bind('new-message', (data) => {
  addMessageToUI(data);
  playNotificationSound();
});

// Messages marked as read
conversationChannel.bind('messages-read', (data) => {
  const { staff_id, staff_name, message_ids } = data;
  updateReadReceipts(message_ids, staff_id, staff_name);
});

// Message edited
conversationChannel.bind('message-edited', (data) => {
  updateMessageInUI(data);
});

// Message deleted
conversationChannel.bind('message-deleted', (data) => {
  removeMessageFromUI(data.message_id);
});

// Reaction added/removed
conversationChannel.bind('message-reaction', (data) => {
  if (data.action === 'add') {
    addReactionToUI(data.message_id, data.reaction);
  } else {
    removeReactionFromUI(data.message_id, data.reaction);
  }
});

// User typing
conversationChannel.bind('user-typing', (data) => {
  showTypingIndicator(data.staff_name);
});
```

#### 2. Personal Notification Channel
```javascript
const personalChannel = pusher.subscribe(
  `${hotelSlug}-staff-${staffId}-notifications`
);

// @Mention notification
personalChannel.bind('message-mention', (data) => {
  showHighPriorityNotification(data);
  refreshUnreadCount();
});

// Added to new conversation
personalChannel.bind('new-conversation', (data) => {
  addConversationToList(data);
  showNotification(`Added to ${data.title}`);
});
```

### Unsubscribe
```javascript
// When leaving conversation
conversationChannel.unsubscribe();

// When logging out
pusher.unsubscribe(`${hotelSlug}-staff-${staffId}-notifications`);
```

---

## 🔔 FCM Push Notifications

### Setup (React Native)
```javascript
import messaging from '@react-native-firebase/messaging';

// Request permission
async function requestPermission() {
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;
  
  if (enabled) {
    console.log('Authorization status:', authStatus);
    return true;
  }
  return false;
}

// Get FCM token
async function getFCMToken() {
  const token = await messaging().getToken();
  return token;
}

// Save token to backend
async function registerFCMToken() {
  const token = await getFCMToken();
  
  await fetch(`/api/staff/${staffId}/update-fcm-token/`, {
    method: 'POST',
    headers: {
      'Authorization': `Token ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ fcm_token: token })
  });
}

// Call on login
await requestPermission();
await registerFCMToken();
```

### Handle Notifications
```javascript
// Foreground notifications
messaging().onMessage(async remoteMessage => {
  const { type, conversation_id } = remoteMessage.data;
  
  if (type === 'staff_chat_message') {
    // Show in-app notification
    showInAppNotification(remoteMessage.notification);
    
    // If conversation is open, mark as read
    if (currentConversationId === conversation_id) {
      markConversationAsRead(conversation_id);
    } else {
      // Update badge
      refreshUnreadCount();
    }
  }
  
  if (type === 'staff_chat_mention') {
    // High priority notification
    showHighPriorityNotification(remoteMessage);
  }
});

// Background/Quit notifications (user taps notification)
messaging().onNotificationOpenedApp(remoteMessage => {
  const { conversation_id, hotel_slug } = remoteMessage.data;
  
  // Navigate to conversation
  navigation.navigate('StaffChat', {
    hotelSlug: hotel_slug,
    conversationId: conversation_id
  });
});

// App opened from quit state by notification
messaging()
  .getInitialNotification()
  .then(remoteMessage => {
    if (remoteMessage) {
      const { conversation_id, hotel_slug } = remoteMessage.data;
      navigation.navigate('StaffChat', {
        hotelSlug: hotel_slug,
        conversationId: conversation_id
      });
    }
  });
```

### Notification Data Payload
```javascript
// Message notification
{
  type: "staff_chat_message",
  conversation_id: "7",
  sender_id: "42",
  sender_name: "John Smith",
  is_group: "true",
  hotel_slug: "hilton-downtown",
  url: "https://hotelsmates.com/staff-chat/hilton-downtown/conversation/7"
}

// Mention notification (high priority)
{
  type: "staff_chat_mention",
  conversation_id: "7",
  sender_id: "42",
  sender_name: "John Smith",
  mentioned_staff_id: "15",
  priority: "high",
  hotel_slug: "hilton-downtown",
  url: "https://hotelsmates.com/staff-chat/hilton-downtown/conversation/7"
}

// File notification
{
  type: "staff_chat_file",
  conversation_id: "7",
  sender_id: "42",
  file_count: "3",
  has_attachments: "true",
  hotel_slug: "hilton-downtown",
  url: "https://hotelsmates.com/staff-chat/hilton-downtown/conversation/7"
}
```

---

## 🎨 UI Components

### 1. Conversation List Item
```jsx
<ConversationItem
  title={displayTitle}
  avatar={displayAvatar}
  lastMessage={lastMessage.message}
  timestamp={lastMessage.timestamp}
  unreadCount={unreadCount}
  isGroup={isGroup}
  onPress={() => openConversation(id)}
/>
```

### 2. Message Bubble
```jsx
<MessageBubble
  isOwn={message.sender_info.id === currentUserId}
  message={message.message}
  timestamp={message.timestamp}
  senderName={message.sender_info.name}
  senderAvatar={message.sender_info.avatar}
  attachments={message.attachments}
  reactions={message.reactions}
  readByList={message.read_by_list}
  replyTo={message.reply_to_message}
  onReply={() => setReplyTo(message)}
  onReact={(emoji) => addReaction(message.id, emoji)}
/>
```

### 3. Read Receipts
```jsx
{isOwnMessage && (
  <ReadReceipts>
    {message.read_by_list.map(staff => (
      <Avatar
        key={staff.id}
        src={staff.avatar}
        size="xs"
        title={staff.name}
      />
    ))}
    <Text>Read by {message.read_by_count}</Text>
  </ReadReceipts>
)}
```

### 4. Unread Badge
```jsx
<Badge count={totalUnread} max={99}>
  <ChatIcon />
</Badge>
```

### 5. Typing Indicator
```jsx
{typingUsers.length > 0 && (
  <TypingIndicator>
    {typingUsers.map(u => u.name).join(', ')} 
    {typingUsers.length === 1 ? ' is' : ' are'} typing...
  </TypingIndicator>
)}
```

---

## ⚡ Performance Best Practices

### 1. Pagination
```javascript
// Load 50 messages initially
const initialMessages = await fetchMessages(conversationId, { limit: 50 });

// Infinite scroll - load more when scrolling up
const loadMore = async () => {
  const oldestId = messages[0].id;
  const olderMessages = await fetchMessages(conversationId, {
    limit: 50,
    before_id: oldestId
  });
  setMessages([...olderMessages, ...messages]);
};
```

### 2. Debounce Typing Indicators
```javascript
import { debounce } from 'lodash';

const sendTyping = debounce(() => {
  pusher.trigger('user-typing', {
    staff_id: currentUserId,
    staff_name: currentUserName,
    is_typing: true
  });
}, 500);

// Stop typing after 3 seconds of inactivity
const stopTyping = debounce(() => {
  pusher.trigger('user-typing', {
    staff_id: currentUserId,
    is_typing: false
  });
}, 3000);

const handleTextChange = (text) => {
  setMessageText(text);
  sendTyping();
  stopTyping();
};
```

### 3. Batch Mark as Read
```javascript
// Only mark as read when:
// - User opens conversation
// - User scrolls to bottom
// - App returns to foreground

useEffect(() => {
  if (isConversationOpen && isAtBottom) {
    markConversationAsRead(conversationId);
  }
}, [isConversationOpen, isAtBottom]);
```

### 4. Cache Unread Counts
```javascript
// Refresh every 30 seconds or on events
const { data: unreadData } = useSWR(
  `/api/staff-chat/${hotelSlug}/conversations/unread-count/`,
  fetcher,
  { refreshInterval: 30000 }
);

// Or use Pusher events to refresh immediately
personalChannel.bind('new-message', () => {
  mutate();  // Refresh unread count
});
```

### 5. Optimize Pusher Subscriptions
```javascript
// Only subscribe to active conversation
useEffect(() => {
  if (conversationId) {
    const channel = pusher.subscribe(
      `${hotelSlug}-staff-conversation-${conversationId}`
    );
    
    // Bind events...
    
    return () => {
      channel.unsubscribe();
    };
  }
}, [conversationId]);
```

---

## 🐛 Common Issues & Solutions

### Issue: Messages not appearing in real-time
**Solution:** Check Pusher subscription and channel name
```javascript
// Verify channel name format
console.log('Channel:', `${hotelSlug}-staff-conversation-${conversationId}`);

// Check if subscribed
console.log('Subscribed:', pusher.channel(`${hotelSlug}-staff-conversation-${conversationId}`));
```

### Issue: Unread count not updating
**Solution:** Ensure you're calling refresh after marking as read
```javascript
await markConversationAsRead(conversationId);
await refreshUnreadCount();  // ← Important!
```

### Issue: FCM not working
**Solution:**
1. Check FCM token is registered: `staff.fcm_token` in database
2. Verify Firebase credentials in backend `.env`
3. Test token validity in Firebase Console
4. Check device notification permissions

### Issue: Duplicate messages
**Solution:** Check if you're subscribing multiple times
```javascript
// ✗ Wrong - subscribes multiple times
conversationChannel.bind('new-message', handleMessage);
conversationChannel.bind('new-message', handleMessage);

// ✓ Correct - unsubscribe before resubscribing
useEffect(() => {
  const channel = pusher.subscribe(channelName);
  channel.bind('new-message', handleMessage);
  
  return () => {
    channel.unbind('new-message', handleMessage);
    channel.unsubscribe();
  };
}, [conversationId]);
```

---

## 📋 Checklist for Launch

### Backend ✅
- [x] All endpoints implemented
- [x] Pusher configured in `.env`
- [x] FCM configured in `.env`
- [x] Hotel isolation verified
- [x] Permissions implemented
- [x] Real-time broadcasting working

### Frontend
- [ ] Implement conversation list
- [ ] Implement message view
- [ ] Integrate Pusher for real-time
- [ ] Setup FCM for push notifications
- [ ] Implement unread badges
- [ ] Add file upload
- [ ] Add reactions
- [ ] Add @mentions UI
- [ ] Test on iOS
- [ ] Test on Android

---

## 🔗 Quick Links

- **API Base:** `/api/staff-chat/{hotel_slug}/`
- **Pusher Cluster:** `eu`
- **Pusher Key:** `6744ef8e4ff09af2a849`
- **Firebase Project:** `hotel-mate-d878f`

---

## 💬 Support

For issues or questions:
1. Check `ENHANCEMENTS_SUMMARY.md` for detailed backend documentation
2. Check `API_QUICK_REFERENCE.md` for API examples
3. Review Pusher Dashboard for real-time event logs
4. Check Firebase Console for FCM delivery logs

---

**Happy Coding! 🚀**
