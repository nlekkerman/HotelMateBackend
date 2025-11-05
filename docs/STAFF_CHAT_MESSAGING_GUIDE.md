# Staff Chat Messaging System - Frontend Integration Guide

## Overview

The Staff Chat system provides **real-time messaging** between staff members with support for:
- ✅ **1-on-1 conversations** and **group chats**
- ✅ **Send, edit, delete messages** with real-time updates
- ✅ **Reply to messages** (quote/reply functionality)
- ✅ **Emoji reactions** (👍, ❤️, 😊, etc.)
- ✅ **File attachments** (images, PDFs, documents)
- ✅ **@Mentions** with notifications
- ✅ **Read receipts** (who read each message)
- ✅ **Pusher real-time events** (instant message delivery)
- ✅ **FCM push notifications** (mobile notifications)

---

## Base URL

All endpoints are prefixed with:
```
/api/staff-chat/<hotel_slug>/
```

---

## 1. Send a Message

### Endpoint
```http
POST /api/staff-chat/{hotel_slug}/conversations/{conversation_id}/send-message/
```

### Headers
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Request Body
```json
{
  "message": "Hello! How can I help?",
  "reply_to": 123  // Optional: ID of message you're replying to
}
```

### Response (201 Created)
```json
{
  "id": 456,
  "conversation": 1,
  "sender": 10,
  "sender_info": {
    "id": 10,
    "first_name": "John",
    "last_name": "Smith",
    "full_name": "John Smith",
    "email": "john@hotel.com",
    "avatar_url": "https://...",
    "role_name": "Receptionist",
    "department_name": "Front Office",
    "is_online": true
  },
  "sender_name": "John Smith",
  "message": "Hello! How can I help?",
  "timestamp": "2025-11-05T14:30:00Z",
  "status": "delivered",
  "delivered_at": "2025-11-05T14:30:00Z",
  "is_read": false,
  "read_by": [],
  "read_by_count": 0,
  "is_read_by_current_user": true,
  "is_edited": false,
  "edited_at": null,
  "is_deleted": false,
  "deleted_at": null,
  "reply_to": 123,
  "reply_to_message": {
    "id": 123,
    "message": "Can someone help with room 305?",
    "sender_name": "Sarah Johnson",
    "sender_avatar": "https://...",
    "timestamp": "2025-11-05T14:25:00Z",
    "is_deleted": false,
    "attachments_preview": []
  },
  "attachments": [],
  "has_attachments": false,
  "reactions": [],
  "reaction_summary": {},
  "mentions": [],
  "mentioned_staff": []
}
```

### Frontend Implementation Example
```javascript
async function sendMessage(hotelSlug, conversationId, messageText, replyToId = null) {
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/conversations/${conversationId}/send-message/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: messageText,
          reply_to: replyToId
        })
      }
    );
    
    if (!response.ok) throw new Error('Failed to send message');
    
    const message = await response.json();
    console.log('Message sent:', message);
    
    // Add message to UI immediately (optimistic update)
    // Pusher will confirm delivery to other participants
    return message;
    
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
}

// Usage
sendMessage('hotel-plaza', 42, 'Hello team!');

// With reply
sendMessage('hotel-plaza', 42, 'I can help!', 123);
```

---

## 2. Get Messages (with Pagination)

### Endpoint
```http
GET /api/staff-chat/{hotel_slug}/conversations/{conversation_id}/messages/
```

### Query Parameters
- `limit` (optional): Number of messages to load (default: 50)
- `before_id` (optional): Load messages older than this message ID (for pagination)

### Request
```http
GET /api/staff-chat/hotel-plaza/conversations/42/messages/?limit=50&before_id=200
Authorization: Bearer <access_token>
```

### Response (200 OK)
```json
{
  "messages": [
    {
      "id": 150,
      "sender_info": { /* ... */ },
      "message": "Good morning team!",
      "timestamp": "2025-11-05T09:00:00Z",
      "is_read_by_current_user": true,
      "read_by_count": 3,
      "reactions": [
        {
          "id": 1,
          "emoji": "👍",
          "staff": 11,
          "staff_name": "Jane Doe",
          "staff_avatar": "https://...",
          "created_at": "2025-11-05T09:01:00Z"
        }
      ],
      "reaction_summary": {
        "👍": 3,
        "❤️": 1
      },
      "attachments": [],
      "reply_to_message": null
    },
    // ... more messages
  ],
  "count": 50,
  "has_more": true
}
```

### Frontend Implementation Example
```javascript
async function loadMessages(hotelSlug, conversationId, limit = 50, beforeId = null) {
  const params = new URLSearchParams({
    limit: limit.toString()
  });
  
  if (beforeId) {
    params.append('before_id', beforeId.toString());
  }
  
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/conversations/${conversationId}/messages/?${params}`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    
    if (!response.ok) throw new Error('Failed to load messages');
    
    const data = await response.json();
    console.log(`Loaded ${data.count} messages, has more: ${data.has_more}`);
    
    return data;
    
  } catch (error) {
    console.error('Error loading messages:', error);
    throw error;
  }
}

// Initial load
const initialMessages = await loadMessages('hotel-plaza', 42);

// Load more (pagination)
const oldestMessageId = initialMessages.messages[0].id;
const olderMessages = await loadMessages('hotel-plaza', 42, 50, oldestMessageId);
```

---

## 3. Edit a Message

### Endpoint
```http
PATCH /api/staff-chat/{hotel_slug}/messages/{message_id}/edit/
```

### Request Body
```json
{
  "message": "Updated message text"
}
```

### Response (200 OK)
```json
{
  "id": 456,
  "message": "Updated message text",
  "is_edited": true,
  "edited_at": "2025-11-05T14:35:00Z",
  // ... rest of message fields
}
```

### Frontend Implementation
```javascript
async function editMessage(hotelSlug, messageId, newText) {
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/messages/${messageId}/edit/`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: newText
        })
      }
    );
    
    if (!response.ok) throw new Error('Failed to edit message');
    
    const updatedMessage = await response.json();
    console.log('Message edited:', updatedMessage);
    
    return updatedMessage;
    
  } catch (error) {
    console.error('Error editing message:', error);
    throw error;
  }
}

// Usage
editMessage('hotel-plaza', 456, 'Corrected message text');
```

---

## 4. Delete a Message

### Endpoint
```http
DELETE /api/staff-chat/{hotel_slug}/messages/{message_id}/delete/
```

### Query Parameters
- `hard_delete=true` (optional): Permanently delete (managers only)

### Soft Delete Request
```http
DELETE /api/staff-chat/hotel-plaza/messages/456/delete/
Authorization: Bearer <access_token>
```

### Hard Delete Request (Managers Only)
```http
DELETE /api/staff-chat/hotel-plaza/messages/456/delete/?hard_delete=true
Authorization: Bearer <access_token>
```

### Response - Soft Delete (200 OK)
```json
{
  "success": true,
  "hard_delete": false,
  "message": {
    "id": 456,
    "message": "[Message deleted]",
    "is_deleted": true,
    "deleted_at": "2025-11-05T14:40:00Z"
  }
}
```

### Response - Hard Delete (200 OK)
```json
{
  "success": true,
  "hard_delete": true,
  "message_id": 456
}
```

### Frontend Implementation
```javascript
async function deleteMessage(hotelSlug, messageId, hardDelete = false) {
  const params = hardDelete ? '?hard_delete=true' : '';
  
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/messages/${messageId}/delete/${params}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    
    if (!response.ok) throw new Error('Failed to delete message');
    
    const result = await response.json();
    console.log('Message deleted:', result);
    
    if (result.hard_delete) {
      // Remove message completely from UI
      removeMessageFromUI(messageId);
    } else {
      // Update message to show "[Message deleted]"
      updateMessageInUI(result.message);
    }
    
    return result;
    
  } catch (error) {
    console.error('Error deleting message:', error);
    throw error;
  }
}

// Soft delete (own messages)
deleteMessage('hotel-plaza', 456);

// Hard delete (managers only)
deleteMessage('hotel-plaza', 456, true);
```

---

## 5. Add Emoji Reaction

### Endpoint
```http
POST /api/staff-chat/{hotel_slug}/messages/{message_id}/react/
```

### Available Emojis
`👍`, `❤️`, `😊`, `😂`, `😮`, `😢`, `🎉`, `🔥`, `✅`, `👏`

### Request Body
```json
{
  "emoji": "👍"
}
```

### Response (201 Created)
```json
{
  "id": 789,
  "emoji": "👍",
  "staff": 10,
  "staff_name": "John Smith",
  "staff_avatar": "https://...",
  "created_at": "2025-11-05T14:45:00Z"
}
```

### Frontend Implementation
```javascript
async function addReaction(hotelSlug, messageId, emoji) {
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/messages/${messageId}/react/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ emoji })
      }
    );
    
    if (!response.ok) throw new Error('Failed to add reaction');
    
    const reaction = await response.json();
    console.log('Reaction added:', reaction);
    
    return reaction;
    
  } catch (error) {
    console.error('Error adding reaction:', error);
    throw error;
  }
}

// Usage
addReaction('hotel-plaza', 456, '👍');
```

---

## 6. Remove Emoji Reaction

### Endpoint
```http
DELETE /api/staff-chat/{hotel_slug}/messages/{message_id}/react/{emoji}/
```

### Request
```http
DELETE /api/staff-chat/hotel-plaza/messages/456/react/👍/
Authorization: Bearer <access_token>
```

### Response (200 OK)
```json
{
  "message": "Reaction removed"
}
```

### Frontend Implementation
```javascript
async function removeReaction(hotelSlug, messageId, emoji) {
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/messages/${messageId}/react/${encodeURIComponent(emoji)}/`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    
    if (!response.ok) throw new Error('Failed to remove reaction');
    
    const result = await response.json();
    console.log('Reaction removed:', result);
    
    return result;
    
  } catch (error) {
    console.error('Error removing reaction:', error);
    throw error;
  }
}

// Usage
removeReaction('hotel-plaza', 456, '👍');
```

---

## 7. Upload File Attachments

### Endpoint
```http
POST /api/staff-chat/{hotel_slug}/conversations/{conversation_id}/upload/
```

### Headers
```http
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

### Form Data
- `files`: Array of files (max 10 files, 50MB each)
- `message_id` (optional): Existing message ID to attach files to
- `message` (optional): Message text if creating new message
- `reply_to` (optional): Message ID this is replying to

### Supported File Types
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.txt`, `.csv`

### Response (201 Created)
```json
{
  "message": {
    "id": 460,
    "message": "Check out these reports",
    "attachments": [
      {
        "id": 100,
        "file_name": "monthly-report.pdf",
        "file_type": "pdf",
        "file_size": 2048576,
        "file_size_display": "2.0 MB",
        "mime_type": "application/pdf",
        "file_url": "https://res.cloudinary.com/.../monthly-report.pdf",
        "thumbnail_url": null,
        "uploaded_at": "2025-11-05T14:50:00Z",
        "uploader_name": "John Smith"
      }
    ],
    "has_attachments": true
  },
  "attachments": [ /* same as above */ ],
  "success": true,
  "warnings": []
}
```

### Frontend Implementation
```javascript
async function uploadFiles(hotelSlug, conversationId, files, messageText = null, replyToId = null) {
  const formData = new FormData();
  
  // Add files
  files.forEach(file => {
    formData.append('files', file);
  });
  
  // Optional: message text
  if (messageText) {
    formData.append('message', messageText);
  }
  
  // Optional: reply to
  if (replyToId) {
    formData.append('reply_to', replyToId);
  }
  
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/conversations/${conversationId}/upload/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`
          // Don't set Content-Type, browser will set it with boundary
        },
        body: formData
      }
    );
    
    if (!response.ok) throw new Error('Failed to upload files');
    
    const result = await response.json();
    console.log('Files uploaded:', result);
    
    return result;
    
  } catch (error) {
    console.error('Error uploading files:', error);
    throw error;
  }
}

// Usage with file input
const fileInput = document.getElementById('file-input');
fileInput.addEventListener('change', async (e) => {
  const files = Array.from(e.target.files);
  await uploadFiles('hotel-plaza', 42, files, 'Here are the files you requested');
});

// Usage with drag & drop
dropZone.addEventListener('drop', async (e) => {
  e.preventDefault();
  const files = Array.from(e.dataTransfer.files);
  await uploadFiles('hotel-plaza', 42, files);
});
```

---

## 8. Delete File Attachment

### Endpoint
```http
DELETE /api/staff-chat/{hotel_slug}/attachments/{attachment_id}/delete/
```

### Response (200 OK)
```json
{
  "success": true,
  "attachment_id": 100,
  "message_id": 460
}
```

### Frontend Implementation
```javascript
async function deleteAttachment(hotelSlug, attachmentId) {
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/attachments/${attachmentId}/delete/`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    
    if (!response.ok) throw new Error('Failed to delete attachment');
    
    const result = await response.json();
    console.log('Attachment deleted:', result);
    
    return result;
    
  } catch (error) {
    console.error('Error deleting attachment:', error);
    throw error;
  }
}

// Usage
deleteAttachment('hotel-plaza', 100);
```

---

## 9. Pusher Real-Time Events

### Setup Pusher Client

```javascript
import Pusher from 'pusher-js';

const pusher = new Pusher(PUSHER_KEY, {
  cluster: PUSHER_CLUSTER,
  encrypted: true
});

// Subscribe to conversation channel
const conversationChannel = pusher.subscribe(
  `${hotelSlug}-staff-conversation-${conversationId}`
);
```

### Event: New Message

```javascript
conversationChannel.bind('new-message', (data) => {
  console.log('New message received:', data);
  
  // Add message to UI
  addMessageToUI(data);
  
  // Play notification sound
  if (data.sender !== currentUserId) {
    playNotificationSound();
  }
  
  // Update conversation list
  updateConversationPreview(data.conversation, data);
});
```

### Event: Message Edited

```javascript
conversationChannel.bind('message-edited', (data) => {
  console.log('Message edited:', data);
  
  // Update message in UI
  updateMessageInUI(data);
  
  // Show "edited" indicator
  showEditedIndicator(data.id, data.edited_at);
});
```

### Event: Message Deleted

```javascript
conversationChannel.bind('message-deleted', (data) => {
  console.log('Message deleted:', data);
  
  if (data.hard_delete) {
    // Remove message completely from UI
    removeMessageFromUI(data.message_id);
  } else {
    // Update message to show "[Message deleted]"
    updateMessageInUI(data.message);
  }
});
```

### Event: Message Reaction

```javascript
conversationChannel.bind('message-reaction', (data) => {
  console.log('Reaction update:', data);
  
  if (data.action === 'add') {
    // Add reaction to message
    addReactionToMessage(data.message_id, data.reaction);
  } else if (data.action === 'remove') {
    // Remove reaction from message
    removeReactionFromMessage(data.message_id, data.reaction);
  }
  
  // Update reaction summary
  updateReactionSummary(data.message_id);
});
```

### Event: Attachment Uploaded

```javascript
conversationChannel.bind('attachment-uploaded', (data) => {
  console.log('Attachment uploaded:', data);
  
  // Add attachments to message
  addAttachmentsToMessage(data.message_id, data.attachments);
});
```

### Event: Attachment Deleted

```javascript
conversationChannel.bind('attachment-deleted', (data) => {
  console.log('Attachment deleted:', data);
  
  // Remove attachment from UI
  removeAttachmentFromUI(data.attachment_id);
});
```

---

## 10. Complete Chat Component Example

```javascript
class StaffChatComponent {
  constructor(hotelSlug, conversationId, accessToken) {
    this.hotelSlug = hotelSlug;
    this.conversationId = conversationId;
    this.accessToken = accessToken;
    this.messages = [];
    this.isLoadingMore = false;
    
    this.initPusher();
    this.loadInitialMessages();
  }
  
  initPusher() {
    this.pusher = new Pusher(PUSHER_KEY, {
      cluster: PUSHER_CLUSTER,
      encrypted: true
    });
    
    this.channel = this.pusher.subscribe(
      `${this.hotelSlug}-staff-conversation-${this.conversationId}`
    );
    
    // Bind all events
    this.channel.bind('new-message', this.handleNewMessage.bind(this));
    this.channel.bind('message-edited', this.handleMessageEdited.bind(this));
    this.channel.bind('message-deleted', this.handleMessageDeleted.bind(this));
    this.channel.bind('message-reaction', this.handleReaction.bind(this));
  }
  
  async loadInitialMessages() {
    try {
      const response = await fetch(
        `/api/staff-chat/${this.hotelSlug}/conversations/${this.conversationId}/messages/?limit=50`,
        {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`
          }
        }
      );
      
      const data = await response.json();
      this.messages = data.messages;
      this.renderMessages();
      
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  }
  
  async sendMessage(text, replyToId = null) {
    try {
      const response = await fetch(
        `/api/staff-chat/${this.hotelSlug}/conversations/${this.conversationId}/send-message/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: text,
            reply_to: replyToId
          })
        }
      );
      
      const message = await response.json();
      
      // Optimistically add to UI
      this.messages.push(message);
      this.renderMessages();
      
      // Clear input
      this.clearMessageInput();
      
    } catch (error) {
      console.error('Error sending message:', error);
      this.showError('Failed to send message');
    }
  }
  
  handleNewMessage(data) {
    // Check if message already exists (avoid duplicates)
    const exists = this.messages.find(m => m.id === data.id);
    if (!exists) {
      this.messages.push(data);
      this.renderMessages();
      this.scrollToBottom();
      
      // Play notification sound for messages from others
      if (data.sender !== this.currentUserId) {
        this.playNotificationSound();
      }
    }
  }
  
  handleMessageEdited(data) {
    const index = this.messages.findIndex(m => m.id === data.id);
    if (index !== -1) {
      this.messages[index] = data;
      this.renderMessages();
    }
  }
  
  handleMessageDeleted(data) {
    if (data.hard_delete) {
      // Remove completely
      this.messages = this.messages.filter(m => m.id !== data.message_id);
    } else {
      // Update to show deleted
      const index = this.messages.findIndex(m => m.id === data.message.id);
      if (index !== -1) {
        this.messages[index] = data.message;
      }
    }
    this.renderMessages();
  }
  
  handleReaction(data) {
    const message = this.messages.find(m => m.id === data.message_id);
    if (message) {
      if (data.action === 'add') {
        message.reactions.push(data.reaction);
      } else {
        message.reactions = message.reactions.filter(
          r => r.id !== data.reaction.id
        );
      }
      this.updateMessageReactions(message.id);
    }
  }
  
  async addReaction(messageId, emoji) {
    try {
      await fetch(
        `/api/staff-chat/${this.hotelSlug}/messages/${messageId}/react/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ emoji })
        }
      );
    } catch (error) {
      console.error('Error adding reaction:', error);
    }
  }
  
  renderMessages() {
    // Implement your UI rendering logic
    const container = document.getElementById('messages-container');
    container.innerHTML = '';
    
    this.messages.forEach(message => {
      const messageElement = this.createMessageElement(message);
      container.appendChild(messageElement);
    });
  }
  
  createMessageElement(message) {
    // Create message DOM element with all features
    const div = document.createElement('div');
    div.className = 'message';
    div.dataset.messageId = message.id;
    
    // Add sender info, timestamp, reactions, etc.
    // ... your UI implementation
    
    return div;
  }
}

// Usage
const chat = new StaffChatComponent('hotel-plaza', 42, accessToken);
```

---

## Summary

### Available Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Send Message | POST | `/conversations/{id}/send-message/` |
| Get Messages | GET | `/conversations/{id}/messages/` |
| Edit Message | PATCH | `/messages/{id}/edit/` |
| Delete Message | DELETE | `/messages/{id}/delete/` |
| Add Reaction | POST | `/messages/{id}/react/` |
| Remove Reaction | DELETE | `/messages/{id}/react/{emoji}/` |
| Upload Files | POST | `/conversations/{id}/upload/` |
| Delete Attachment | DELETE | `/attachments/{id}/delete/` |

### Key Features Implemented

✅ **Real-time messaging** with Pusher  
✅ **Message CRUD** (create, edit, delete)  
✅ **Reply to messages** with preview  
✅ **Emoji reactions** (10 types)  
✅ **File attachments** (images, PDFs, docs)  
✅ **@Mentions** with auto-detection  
✅ **Read receipts** tracking  
✅ **FCM push notifications**  
✅ **Pagination** for message loading  
✅ **Group chat** support  

---

## Next Steps

To complete the full chat system, you can also implement:
- Read receipts tracking (mark messages as read)
- Typing indicators (show when someone is typing)
- Online/offline status
- Conversation management (create, archive, search)
- Notification preferences

All backend APIs are ready and documented! 🎉
