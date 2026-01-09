# Frontend Pusher Channels Guide - Staff Guest Chat Notifications

## Overview

After implementing staff notifications for guest messages, here are the Pusher channels your frontend needs to listen to:

## 🏢 **Staff Frontend Channels**

### 1. **Conversation Channels** (Message Display)
**Purpose**: Display guest messages in real-time within the chat interface

```javascript
// For each conversation the staff member is viewing
const conversationChannel = pusher.subscribe(`${hotelSlug}-conversation-${conversationId}-chat`);

conversationChannel.bind('realtime_event', (data) => {
    // Handle guest messages appearing in chat
    if (data.event_type === 'guest_message_created') {
        const message = data.payload;
        addMessageToConversation({
            id: message.id,
            sender_type: 'guest',
            sender_name: 'Guest',
            message: message.message,
            timestamp: message.timestamp,
            room_number: message.room_number
        });
    }
});
```

### 2. **Staff Notification Channels** (Alerts & Badges)
**Purpose**: Show notification alerts when guests send messages

```javascript
// Personal staff notification channel
const notificationChannel = pusher.subscribe(`${hotelSlug}.staff-${staffId}-notifications`);

notificationChannel.bind('new-guest-message', (data) => {
    // Show notification alert/badge
    showGuestMessageAlert({
        title: `New message from Room ${data.room_number}`,
        body: data.guest_message,
        conversationId: data.conversation_id,
        bookingId: data.booking_id
    });
    
    // Update unread count badges
    updateConversationUnreadCount(data.conversation_id);
});

// Also handle existing unread count updates
notificationChannel.bind('realtime_staff_chat_unread_updated', (data) => {
    updateUnreadCounts(data.payload);
});
```

## 👤 **Guest Frontend Channels**
**Purpose**: Receive staff replies (no changes needed)

```javascript
// Guest booking channel (existing implementation)
const guestChannel = pusher.subscribe(`private-hotel-${hotelSlug}-guest-chat-booking-${bookingId}`);

guestChannel.bind('realtime_event', (data) => {
    // Handle staff replies
    if (data.event_type === 'staff_message_created') {
        addMessageToChat(data.payload);
    }
});
```

## 📱 **Implementation Examples**

### Staff Chat Component Setup
```javascript
class StaffChatComponent {
    constructor(hotelSlug, staffId, conversationId) {
        this.hotelSlug = hotelSlug;
        this.staffId = staffId;
        this.conversationId = conversationId;
        this.setupPusherChannels();
    }
    
    setupPusherChannels() {
        // 1. Conversation channel for real-time messages
        this.conversationChannel = pusher.subscribe(
            `${this.hotelSlug}-conversation-${this.conversationId}-chat`
        );
        
        this.conversationChannel.bind('realtime_event', (data) => {
            this.handleConversationEvent(data);
        });
        
        // 2. Personal notification channel for alerts
        this.notificationChannel = pusher.subscribe(
            `${this.hotelSlug}.staff-${this.staffId}-notifications`
        );
        
        this.notificationChannel.bind('new-guest-message', (data) => {
            this.handleGuestMessageNotification(data);
        });
    }
    
    handleConversationEvent(data) {
        if (data.event_type === 'guest_message_created') {
            // Add message to current conversation view
            this.addMessageToUI(data.payload);
        }
    }
    
    handleGuestMessageNotification(data) {
        // Show notification if not currently viewing this conversation
        if (data.conversation_id !== this.conversationId) {
            this.showNotificationBadge(data);
        }
    }
}
```

### Staff Dashboard/List Setup
```javascript
class StaffDashboard {
    constructor(hotelSlug, staffId) {
        this.hotelSlug = hotelSlug;
        this.staffId = staffId;
        this.setupNotificationChannel();
    }
    
    setupNotificationChannel() {
        this.notificationChannel = pusher.subscribe(
            `${this.hotelSlug}.staff-${this.staffId}-notifications`
        );
        
        // Guest message notifications
        this.notificationChannel.bind('new-guest-message', (data) => {
            this.showGuestMessageAlert(data);
            this.updateConversationList();
        });
        
        // Unread count updates
        this.notificationChannel.bind('realtime_staff_chat_unread_updated', (data) => {
            this.updateUnreadBadges(data.payload);
        });
    }
    
    showGuestMessageAlert(data) {
        // Show toast/alert notification
        this.showToast({
            title: `Guest Message - Room ${data.room_number}`,
            message: data.guest_message,
            action: () => this.openConversation(data.conversation_id)
        });
    }
}
```

## 🔧 **Channel Summary Table**

| Frontend Component | Channel Pattern | Event | Purpose |
|-------------------|-----------------|-------|---------|
| Staff Chat Interface | `{hotelSlug}-conversation-{conversationId}-chat` | `realtime_event` | Show guest messages in chat |
| Staff Notifications | `{hotelSlug}.staff-{staffId}-notifications` | `new-guest-message` | Alert staff of new messages |
| Staff Unread Counts | `{hotelSlug}.staff-{staffId}-notifications` | `realtime_staff_chat_unread_updated` | Update unread badges |
| Guest Chat | `private-hotel-{hotelSlug}-guest-chat-booking-{bookingId}` | `realtime_event` | Receive staff replies |

## ✅ **Testing Checklist**

1. **Guest sends message** → Staff sees it in conversation channel
2. **Guest sends message** → Staff gets notification alert  
3. **Staff opens conversation** → Unread count updates
4. **Staff replies** → Guest receives reply immediately
5. **Multiple staff members** → All get notifications, one handles assignment

## 🚨 **Important Notes**

- Staff must listen to **both** conversation AND notification channels
- Conversation channels show the actual messages
- Notification channels show alerts/badges
- Guest channels remain unchanged
- Assignment happens when staff clicks on conversation (existing endpoint)