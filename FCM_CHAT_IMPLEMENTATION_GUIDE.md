# 📱 FCM Message Handling & Chat Features Implementation Guide

This comprehensive guide covers FCM event handling, message read status tracking, reply functionality, and real-time chat features for the HotelMate system.

## 🔥 FCM Event Structure & Handling

### 1. FCM Message Types

Your backend sends FCM messages with these types in the `data` field:

```javascript
// Guest Chat FCM
{
  "type": "new_chat_message",     // Staff message to guest
  "type": "guest_message",        // Guest message to staff
  
  // Staff Chat FCM  
  "type": "staff_chat_message",   // New staff message
  "type": "staff_chat_mention",   // @mention notification
  "type": "staff_chat_new_conversation", // Added to group
  
  // Room Service FCM
  "type": "room_service_order",   // New order for porter/kitchen
  
  // Booking FCM
  "type": "booking_confirmation", // Booking confirmed
  "type": "booking_cancellation"  // Booking cancelled
}
```

### 2. FCM Payload Structure

```javascript
// Complete FCM payload structure
{
  "from": "1020698338972",
  "messageId": "6e623646-3527-44bb-b89c-0345acd62e6c",
  "notification": {
    "title": "💬 John Doe",
    "body": "Hello, how can I help you?"
  },
  "data": {
    // Core identification
    "type": "new_chat_message",
    "hotel_slug": "hotel-killarney",
    
    // Chat-specific data
    "conversation_id": "123",
    "room_number": "101",
    "message_id": "456",
    "sender_type": "staff",
    "sender_id": "789",
    "staff_name": "John Doe",
    
    // Navigation
    "click_action": "/chat/hotel-killarney/room/101",
    "route": "/chat/hotel-killarney/room/101",
    "url": "https://hotelsmates.com/chat/hotel-killarney/room/101"
  }
}
```

### 3. FCM to EventBus Transformation

```javascript
function transformFCMEvent(fcmEvent) {
  const { payload } = fcmEvent;
  const fcmData = payload.data || {};
  const notification = payload.notification || {};
  
  // Map FCM types to event structure
  const eventMapping = {
    'new_chat_message': {
      category: 'guest_chat',
      type: 'staff_message_created',
      channel: `hotel-${fcmData.hotel_slug}.guest-chat.${fcmData.room_number}`
    },
    'guest_message': {
      category: 'guest_chat',
      type: 'guest_message_created', 
      channel: `hotel-${fcmData.hotel_slug}.guest-chat.${fcmData.conversation_id}`
    },
    'staff_chat_message': {
      category: 'staff_chat',
      type: 'message_created',
      channel: `hotel-${fcmData.hotel_slug}.staff-chat.${fcmData.conversation_id}`
    },
    'staff_chat_mention': {
      category: 'staff_chat', 
      type: 'staff_mentioned',
      channel: `hotel-${fcmData.hotel_slug}.staff-${fcmData.mentioned_staff_id}-notifications`
    }
  };
  
  const mapping = eventMapping[fcmData.type] || {
    category: 'system',
    type: 'fcm_message',
    channel: `hotel-${fcmData.hotel_slug || 'unknown'}.system`
  };
  
  return {
    source: 'fcm',
    channel: mapping.channel,
    eventName: mapping.type,
    payload: {
      category: mapping.category,
      type: mapping.type,
      payload: {
        // FCM notification
        title: notification.title,
        body: notification.body,
        // All FCM data
        ...fcmData,
        // Metadata
        fcm_message_id: payload.messageId,
        received_at: new Date().toISOString()
      },
      meta: {
        hotel_slug: fcmData.hotel_slug || 'unknown',
        event_id: payload.messageId,
        ts: new Date().toISOString(),
        scope: { fcm_source: true }
      }
    }
  };
}
```

## 👁️ Message Read Status Implementation

### 1. Backend Read Status Models

#### Guest Chat (RoomMessage)
```python
# chat/models.py
class RoomMessage(models.Model):
    # Read tracking
    read_by_staff = models.BooleanField(default=False)
    read_by_guest = models.BooleanField(default=False)
    staff_read_at = models.DateTimeField(null=True, blank=True)
    guest_read_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(
        choices=[
            ("pending", "Pending"),
            ("delivered", "Delivered"), 
            ("read", "Read")
        ],
        default="delivered"
    )
```

#### Staff Chat (StaffChatMessage)
```python
# staff_chat/models.py
class StaffChatMessage(models.Model):
    # Multi-participant read tracking
    is_read = models.BooleanField(default=False)  # True when ALL read
    read_by = models.ManyToManyField(
        'staff.Staff',
        related_name='read_staff_messages'
    )
    
    def mark_as_read_by(self, staff):
        """Mark as read by specific staff member"""
        if staff != self.sender:
            self.read_by.add(staff)
            
            # Check if ALL participants have read
            all_participants = self.conversation.participants.exclude(
                id=self.sender.id
            )
            if self.read_by.count() >= all_participants.count():
                self.is_read = True
                self.status = 'read'
                self.save()
```

### 2. Mark as Read API Endpoints

#### Guest Chat - Mark Conversation Read
```javascript
// API: POST /api/chat/conversations/{id}/mark-read/
const markGuestChatRead = async (conversationId) => {
  try {
    const response = await fetch(`/api/chat/conversations/${conversationId}/mark-read/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const result = await response.json();
    // result.marked_as_read = number of messages marked
    return result;
  } catch (error) {
    console.error('Failed to mark conversation as read:', error);
  }
};
```

#### Staff Chat - Mark Conversation Read
```javascript
// API: POST /api/staff-chat/{hotel_slug}/conversations/{id}/mark_as_read/
const markStaffChatRead = async (hotelSlug, conversationId) => {
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/conversations/${conversationId}/mark_as_read/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const result = await response.json();
    // result.marked_count = number of messages marked
    // result.message_ids = array of marked message IDs
    return result;
  } catch (error) {
    console.error('Failed to mark staff chat as read:', error);
  }
};
```

#### Staff Chat - Mark Individual Message Read
```javascript
// API: POST /api/staff-chat/{hotel_slug}/messages/{id}/mark-as-read/
const markStaffMessageRead = async (hotelSlug, messageId) => {
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/messages/${messageId}/mark-as-read/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const result = await response.json();
    // result.message contains updated message with read status
    return result;
  } catch (error) {
    console.error('Failed to mark message as read:', error);
  }
};
```

### 3. Read Receipt Real-time Events

#### Guest Chat Read Receipts
```javascript
// Listen for read receipts in guest chat
eventBus.subscribe(`hotel-${hotelSlug}-conversation-${conversationId}-chat`, (event) => {
  if (event.event === 'messages-read-by-staff') {
    // Staff read guest messages
    const { message_ids, read_at, staff_name } = event.data;
    updateMessageReadStatus(message_ids, 'read_by_staff', true);
    showReadReceipt(message_ids, `Read by ${staff_name} at ${read_at}`);
  }
  
  if (event.event === 'messages-read-by-guest') {
    // Guest read staff messages  
    const { message_ids, read_at } = event.data;
    updateMessageReadStatus(message_ids, 'read_by_guest', true);
    showReadReceipt(message_ids, `Read by guest at ${read_at}`);
  }
});
```

#### Staff Chat Read Receipts
```javascript
// Listen for staff chat read receipts
eventBus.subscribe(`hotel-${hotelSlug}.staff-chat.${conversationId}`, (event) => {
  if (event.event === 'read_receipt') {
    const { staff_id, staff_name, message_ids, timestamp } = event.data;
    
    // Update read status for these messages
    message_ids.forEach(messageId => {
      updateStaffMessageReadBy(messageId, staff_id, staff_name, timestamp);
    });
  }
});

function updateStaffMessageReadBy(messageId, staffId, staffName, timestamp) {
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
  if (messageElement) {
    // Add read indicator
    const readIndicator = messageElement.querySelector('.read-by-list');
    if (readIndicator) {
      const readerBadge = document.createElement('span');
      readerBadge.className = 'reader-badge';
      readerBadge.textContent = staffName;
      readerBadge.title = `Read at ${timestamp}`;
      readIndicator.appendChild(readerBadge);
    }
  }
}
```

## 💬 Reply Functionality

### 1. Backend Reply Structure

```python
# Both guest and staff chat models support replies
class RoomMessage(models.Model):
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='replies'
    )

class StaffChatMessage(models.Model):
    reply_to = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='replies'
    )
```

### 2. Send Reply API

#### Guest Chat Reply
```javascript
// API: POST /api/chat/{hotel_slug}/conversations/{id}/messages/
const sendGuestChatReply = async (hotelSlug, conversationId, messageText, replyToId = null) => {
  const payload = {
    message: messageText,
    sender_type: 'staff', // or 'guest'
  };
  
  if (replyToId) {
    payload.reply_to = replyToId;
  }
  
  try {
    const response = await fetch(
      `/api/chat/${hotelSlug}/conversations/${conversationId}/messages/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      }
    );
    
    return await response.json();
  } catch (error) {
    console.error('Failed to send reply:', error);
  }
};
```

#### Staff Chat Reply
```javascript
// API: POST /api/staff-chat/{hotel_slug}/conversations/{id}/messages/
const sendStaffChatReply = async (hotelSlug, conversationId, messageText, replyToId = null) => {
  const payload = {
    message: messageText,
    mentions: [], // Array of staff IDs to mention
  };
  
  if (replyToId) {
    payload.reply_to = replyToId;
  }
  
  try {
    const response = await fetch(
      `/api/staff-chat/${hotelSlug}/conversations/${conversationId}/messages/`,
      {
        method: 'POST', 
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      }
    );
    
    return await response.json();
  } catch (error) {
    console.error('Failed to send staff chat reply:', error);
  }
};
```

### 3. Reply UI Implementation

#### Reply Context Display
```javascript
function showReplyContext(message) {
  const replyContext = document.getElementById('reply-context');
  
  if (message.reply_to_message) {
    replyContext.innerHTML = `
      <div class="reply-context-bar">
        <div class="reply-to-indicator">
          <i class="icon-reply"></i>
          <span class="replying-to">Replying to ${message.reply_to_message.sender}</span>
          <button class="cancel-reply" onclick="cancelReply()">×</button>
        </div>
        <div class="reply-preview">
          ${message.reply_to_message.message}
        </div>
      </div>
    `;
    replyContext.style.display = 'block';
  } else {
    replyContext.style.display = 'none';
  }
}

function cancelReply() {
  document.getElementById('reply-context').style.display = 'none';
  currentReplyToId = null;
}
```

#### Message Reply Threading
```javascript
function renderMessageWithReplies(message) {
  return `
    <div class="message" data-message-id="${message.id}">
      ${message.reply_to_message ? `
        <div class="reply-reference">
          <div class="reply-line"></div>
          <div class="reply-to-message">
            <span class="reply-sender">${message.reply_to_message.sender}</span>
            <span class="reply-text">${message.reply_to_message.message}</span>
          </div>
        </div>
      ` : ''}
      
      <div class="message-content">
        <div class="message-header">
          <span class="sender-name">${message.sender_name}</span>
          <span class="timestamp">${formatTime(message.timestamp)}</span>
        </div>
        
        <div class="message-text">${message.message}</div>
        
        <div class="message-actions">
          <button class="reply-btn" onclick="startReply(${message.id})">
            <i class="icon-reply"></i> Reply
          </button>
          
          ${message.read_by_list ? `
            <div class="read-indicators">
              ${message.read_by_list.map(reader => `
                <span class="read-by" title="Read by ${reader.name}">
                  ${reader.name}
                </span>
              `).join('')}
            </div>
          ` : ''}
        </div>
      </div>
    </div>
  `;
}

function startReply(messageId) {
  const message = findMessageById(messageId);
  currentReplyToId = messageId;
  showReplyContext(message);
  
  // Focus message input
  document.getElementById('message-input').focus();
}
```

## 🔔 FCM Click Actions & Deep Linking

### 1. FCM Click Action Handling

```javascript
// Handle FCM notification clicks
firebase.messaging().onMessage((payload) => {
  console.log('FCM foreground message received:', payload);
  
  // Transform and route through eventBus
  const transformedEvent = transformFCMEvent({
    source: 'fcm',
    payload: payload
  });
  
  eventBus.emit('pusher:message', transformedEvent.payload);
});

// Handle notification clicks when app is in background
firebase.messaging().onNotificationClick((payload) => {
  console.log('FCM notification clicked:', payload);
  
  const data = payload.data;
  
  // Navigate based on FCM data
  if (data.route) {
    navigateTo(data.route);
  } else if (data.url) {
    window.open(data.url, '_blank');
  } else {
    // Fallback navigation based on type
    switch (data.type) {
      case 'new_chat_message':
      case 'guest_message':
        navigateTo(`/chat/${data.hotel_slug}/room/${data.room_number}`);
        break;
        
      case 'staff_chat_message':
      case 'staff_chat_mention':
        navigateTo(`/staff-chat/${data.hotel_slug}/conversation/${data.conversation_id}`);
        break;
        
      case 'room_service_order':
        navigateTo(`/orders/room-service`);
        break;
        
      case 'booking_confirmation':
      case 'booking_cancellation':
        navigateTo(`/bookings/${data.booking_id}`);
        break;
    }
  }
});
```

### 2. Auto-mark as Read on Navigation

```javascript
function navigateToChat(hotelSlug, conversationId, type = 'guest') {
  // Navigate to chat
  if (type === 'guest') {
    router.push(`/chat/${hotelSlug}/room/${conversationId}`);
  } else {
    router.push(`/staff-chat/${hotelSlug}/conversation/${conversationId}`);
  }
  
  // Auto-mark as read after navigation
  setTimeout(() => {
    if (type === 'guest') {
      markGuestChatRead(conversationId);
    } else {
      markStaffChatRead(hotelSlug, conversationId);
    }
  }, 1000);
}
```

## 🎯 Complete Integration Example

```javascript
class ChatManager {
  constructor(hotelSlug) {
    this.hotelSlug = hotelSlug;
    this.currentConversationId = null;
    this.currentReplyToId = null;
    
    this.initEventListeners();
    this.initFCMHandling();
  }
  
  initEventListeners() {
    // Guest chat events
    eventBus.subscribe(`hotel-${this.hotelSlug}.guest-chat.*`, (event) => {
      this.handleGuestChatEvent(event);
    });
    
    // Staff chat events  
    eventBus.subscribe(`hotel-${this.hotelSlug}.staff-chat.*`, (event) => {
      this.handleStaffChatEvent(event);
    });
  }
  
  initFCMHandling() {
    eventBus.on('incoming_realtime_event', (event) => {
      if (event.source === 'fcm') {
        const transformed = transformFCMEvent(event);
        eventBus.emit('pusher:message', transformed.payload);
      }
    });
  }
  
  async sendMessage(conversationId, message, replyToId = null, type = 'guest') {
    try {
      let result;
      if (type === 'guest') {
        result = await sendGuestChatReply(this.hotelSlug, conversationId, message, replyToId);
      } else {
        result = await sendStaffChatReply(this.hotelSlug, conversationId, message, replyToId);
      }
      
      this.cancelReply();
      return result;
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  }
  
  async markAsRead(conversationId, type = 'guest') {
    try {
      if (type === 'guest') {
        await markGuestChatRead(conversationId);
      } else {
        await markStaffChatRead(this.hotelSlug, conversationId);
      }
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  }
  
  startReply(messageId) {
    this.currentReplyToId = messageId;
    // Update UI to show reply context
  }
  
  cancelReply() {
    this.currentReplyToId = null;
    // Hide reply context UI
  }
  
  handleGuestChatEvent(event) {
    const { type, payload } = event;
    
    switch (type) {
      case 'guest_message_created':
      case 'staff_message_created':
        this.addMessageToUI(payload);
        break;
        
      case 'unread_updated':
        this.updateUnreadCount(payload.unread_count);
        break;
    }
  }
  
  handleStaffChatEvent(event) {
    const { type, payload } = event;
    
    switch (type) {
      case 'message_created':
        this.addMessageToUI(payload);
        break;
        
      case 'read_receipt':
        this.updateReadReceipts(payload);
        break;
        
      case 'staff_mentioned':
        this.handleMention(payload);
        break;
    }
  }
}

// Initialize chat manager
const chatManager = new ChatManager('hotel-killarney');
```

This guide covers the complete implementation of FCM handling, read status tracking, and reply functionality for your HotelMate chat system. The backend provides comprehensive APIs and real-time events, while the frontend transformation layer ensures FCM messages integrate seamlessly with your existing eventBus architecture.