# Staff Chat Avatar Integration Guide

## ✅ **Yes, we ARE sending user avatar images in staff chat messages!**

### **Avatar URLs are included in:**

1. **Staff Chat Messages** (`realtime_staff_chat_message_created`)
   - `payload.sender_avatar` - Message sender's profile image URL
   - `payload.reply_to.sender_avatar` - Original message sender's avatar (for replies)

2. **Staff Chat Message Edits** (`realtime_staff_chat_message_edited`)
   - `payload.sender_avatar` - Editor's profile image URL

3. **Typing Indicators** (`realtime_staff_chat_typing`) 
   - `payload.staff_avatar` - Typing user's profile image URL

4. **Staff Mentions** (`realtime_staff_chat_staff_mentioned`)
   - `payload.mentioned_staff_avatar` - Mentioned staff's avatar
   - `payload.sender_avatar` - Sender's avatar

---

## 📡 **Pusher Channel & Events**

### **Channel**: `{hotel_slug}.staff-chat.{conversation_id}`

### **Event Data Structure with Avatars**:

#### **Message Created Event**:
```json
{
  "category": "staff_chat",
  "type": "realtime_staff_chat_message_created",
  "payload": {
    "id": 123,
    "conversation_id": 45,
    "message": "Hello team! 👋",
    "sender_id": 67,
    "sender_name": "John Smith", 
    "sender_avatar": "https://res.cloudinary.com/hotelmate/image/upload/v123/profile-images/staff67.jpg",
    "timestamp": "2025-12-11T10:30:00Z",
    "attachments": [],
    "reply_to": {
      "id": 120,
      "message": "Previous message...",
      "sender_id": 42,
      "sender_name": "Jane Doe",
      "sender_avatar": "https://res.cloudinary.com/hotelmate/image/upload/v456/profile-images/staff42.jpg",
      "timestamp": "2025-12-11T10:25:00Z"
    },
    "is_reply_to_attachment": false
  },
  "meta": {
    "hotel_slug": "hotel-killarney",
    "event_id": "uuid-12345",
    "ts": "2025-12-11T10:30:00Z"
  }
}
```

#### **Typing Indicator Event**:
```json
{
  "category": "staff_chat", 
  "type": "realtime_staff_chat_typing",
  "payload": {
    "conversation_id": 45,
    "staff_id": 67,
    "staff_name": "John Smith",
    "staff_avatar": "https://res.cloudinary.com/hotelmate/image/upload/v123/profile-images/staff67.jpg",
    "is_typing": true,
    "timestamp": "2025-12-11T10:30:15Z"
  }
}
```

#### **Staff Mention Event**:
```json
{
  "category": "staff_chat",
  "type": "realtime_staff_chat_staff_mentioned", 
  "payload": {
    "conversation_id": 45,
    "message_id": 123,
    "mentioned_staff_id": 89,
    "mentioned_staff_name": "Sarah Wilson",
    "mentioned_staff_avatar": "https://res.cloudinary.com/hotelmate/image/upload/v789/profile-images/staff89.jpg",
    "sender_id": 67,
    "sender_name": "John Smith",
    "sender_avatar": "https://res.cloudinary.com/hotelmate/image/upload/v123/profile-images/staff67.jpg",
    "message": "Hey @Sarah, can you handle room 101?",
    "timestamp": "2025-12-11T10:30:00Z"
  }
}
```

---

## 🖥️ **Frontend Implementation**

### **1. Subscribe to Staff Chat Channel**

```javascript
// Initialize Pusher connection
const pusher = new Pusher('your-pusher-key', {
  cluster: 'your-cluster', 
  encrypted: true
});

// Subscribe to conversation channel
const hotelSlug = 'hotel-killarney';
const conversationId = 45;
const chatChannel = pusher.subscribe(`${hotelSlug}.staff-chat.${conversationId}`);
```

### **2. Handle Message Events with Avatars**

```javascript
// Listen for new messages
chatChannel.bind('realtime_staff_chat_message_created', function(eventData) {
  console.log('💬 New staff message with avatar:', eventData);
  
  const message = eventData.payload;
  
  // Create message element with avatar
  displayChatMessage({
    id: message.id,
    senderName: message.sender_name,
    senderAvatar: message.sender_avatar || '/images/default-staff-avatar.png',
    content: message.message,
    timestamp: message.timestamp,
    replyTo: message.reply_to ? {
      senderName: message.reply_to.sender_name,
      senderAvatar: message.reply_to.sender_avatar || '/images/default-staff-avatar.png', 
      content: message.reply_to.message
    } : null
  });
});

// Listen for typing indicators
chatChannel.bind('realtime_staff_chat_typing', function(eventData) {
  const typing = eventData.payload;
  
  if (typing.is_typing) {
    showTypingIndicator({
      staffName: typing.staff_name,
      staffAvatar: typing.staff_avatar || '/images/default-staff-avatar.png'
    });
  } else {
    hideTypingIndicator(typing.staff_id);
  }
});
```

### **3. Display Messages with Avatar UI**

```javascript
function displayChatMessage(messageData) {
  const messageElement = document.createElement('div');
  messageElement.className = 'chat-message';
  messageElement.innerHTML = `
    <div class="message-header">
      <img src="${messageData.senderAvatar}" 
           alt="${messageData.senderName}"
           class="sender-avatar"
           onerror="this.src='/images/default-staff-avatar.png'">
      <span class="sender-name">${messageData.senderName}</span>
      <span class="message-time">${formatTime(messageData.timestamp)}</span>
    </div>
    
    ${messageData.replyTo ? `
      <div class="reply-to-message">
        <img src="${messageData.replyTo.senderAvatar}" 
             alt="${messageData.replyTo.senderName}"
             class="reply-avatar">
        <div class="reply-content">
          <strong>${messageData.replyTo.senderName}</strong>
          <p>${messageData.replyTo.content}</p>
        </div>
      </div>
    ` : ''}
    
    <div class="message-content">${messageData.content}</div>
  `;
  
  // Append to chat container
  document.getElementById('chat-messages').appendChild(messageElement);
  
  // Scroll to bottom
  messageElement.scrollIntoView({ behavior: 'smooth' });
}
```

### **4. Handle Staff Mentions with Avatars**

```javascript
// Listen for mentions
const personalChannel = pusher.subscribe(`${hotelSlug}.staff-${currentStaffId}-notifications`);

personalChannel.bind('realtime_staff_chat_staff_mentioned', function(eventData) {
  const mention = eventData.payload;
  
  // Show mention notification with sender's avatar
  showMentionNotification({
    senderName: mention.sender_name,
    senderAvatar: mention.sender_avatar || '/images/default-staff-avatar.png',
    message: mention.message,
    conversationId: mention.conversation_id
  });
});

function showMentionNotification(mentionData) {
  // Create toast notification
  const toast = document.createElement('div');
  toast.className = 'mention-toast';
  toast.innerHTML = `
    <img src="${mentionData.senderAvatar}" 
         alt="${mentionData.senderName}"
         class="mention-avatar">
    <div class="mention-content">
      <strong>${mentionData.senderName} mentioned you:</strong>
      <p>${mentionData.message}</p>
    </div>
    <button onclick="openConversation(${mentionData.conversationId})">
      View Message
    </button>
  `;
  
  document.body.appendChild(toast);
  
  // Auto-remove after 5 seconds
  setTimeout(() => toast.remove(), 5000);
}
```

---

## 🎨 **CSS Avatar Styling**

```css
/* Sender avatars in messages */
.sender-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e0e0e0;
  margin-right: 12px;
  flex-shrink: 0;
}

/* Reply-to avatars (smaller) */
.reply-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
  margin-right: 8px;
}

/* Typing indicator avatars */
.typing-avatar {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  object-fit: cover;
  margin-right: 6px;
}

/* Mention notification avatars */
.mention-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  margin-right: 10px;
}

/* Avatar fallback when image fails to load */
.sender-avatar[src="/images/default-staff-avatar.png"],
.reply-avatar[src="/images/default-staff-avatar.png"] {
  background-color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
}

/* Online status indicator on avatars */
.avatar-container {
  position: relative;
  display: inline-block;
}

.avatar-container::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  background-color: #28a745;
  border: 2px solid white;
  border-radius: 50%;
}
```

---

## 🔍 **Avatar Fallback Strategy**

### **Avatar URL Handling**:

1. **Primary**: Use `sender_avatar` URL from Pusher event
2. **Fallback**: Use `/images/default-staff-avatar.png` if null
3. **Error Fallback**: Use `onerror` attribute to switch to default
4. **Initials Option**: Generate avatar with staff initials if no image

```javascript
function getAvatarUrl(staff) {
  // Try profile image URL first
  if (staff.sender_avatar) {
    return staff.sender_avatar;
  }
  
  // Generate initials avatar as fallback
  return generateInitialsAvatar(staff.sender_name);
}

function generateInitialsAvatar(fullName) {
  const initials = fullName
    .split(' ')
    .map(name => name[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
  
  // Return data URL with colored background
  const canvas = document.createElement('canvas');
  canvas.width = 40;
  canvas.height = 40;
  const ctx = canvas.getContext('2d');
  
  // Random background color based on name
  const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'];
  const colorIndex = fullName.length % colors.length;
  ctx.fillStyle = colors[colorIndex];
  ctx.fillRect(0, 0, 40, 40);
  
  // White text
  ctx.fillStyle = 'white';
  ctx.font = 'bold 16px Arial';
  ctx.textAlign = 'center';
  ctx.fillText(initials, 20, 26);
  
  return canvas.toDataURL();
}
```

---

## 🧪 **Testing Avatar Integration**

### **Test Avatar URLs**:

1. **Create Staff with Profile Images**: Upload test images via admin
2. **Send Test Messages**: Create messages and verify avatar URLs in Pusher events  
3. **Check Browser Network**: Monitor WebSocket traffic for avatar data
4. **Test Fallbacks**: Remove profile images and verify default behavior

### **Debug Pusher Avatar Events**:
```javascript
// Enable Pusher logging
Pusher.logToConsole = true;

// Log all staff chat events with avatar info
chatChannel.bind_global(function(eventName, data) {
  if (eventName.includes('staff_chat')) {
    console.log('Staff Chat Event:', eventName);
    console.log('Avatar URLs:', {
      senderAvatar: data.payload?.sender_avatar,
      replyAvatar: data.payload?.reply_to?.sender_avatar,
      staffAvatar: data.payload?.staff_avatar
    });
  }
});
```

---

## ✅ **Summary**

**Avatar images ARE being sent in staff chat Pusher notifications!** 

- ✅ Message sender avatars included
- ✅ Reply-to sender avatars included  
- ✅ Typing indicator avatars included
- ✅ Staff mention avatars included
- ✅ Cloudinary URLs ready for frontend use
- ✅ Fallback handling for missing images
- ✅ Consistent across all chat events

The frontend team has everything needed to display rich staff chat with profile images! 🎉