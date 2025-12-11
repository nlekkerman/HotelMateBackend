# FCM Frontend Integration Guide

## 🔥 Simple Guide: FCM → Normalize → Toast

### 🎯 It's Simple!
1. Get FCM notification 
2. Normalize it
3. Fire toast notification
That's it!

---

## 📱 Part 1: FCM Setup & Receiving Notifications

### 1.1 Firebase SDK Setup

```javascript
// Install Firebase SDK
npm install firebase

// firebase-config.js
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const firebaseConfig = {
  // Your Firebase config from Firebase Console
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

export { messaging };
```

### 1.2 Service Worker Setup

Create `public/firebase-messaging-sw.js`:

```javascript
// firebase-messaging-sw.js (in public folder)
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

firebase.initializeApp({
  // Same config as above
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('🔔 Background FCM message received:', payload);
  
  const { title, body, icon } = payload.notification || {};
  
  // Show notification
  self.registration.showNotification(title || 'New Message', {
    body: body || 'You have a new message',
    icon: icon || '/icon-192x192.png',
    badge: '/badge-72x72.png',
    tag: 'staff-chat',
    data: payload.data,
    actions: [
      { action: 'open', title: 'Open Chat' },
      { action: 'dismiss', title: 'Dismiss' }
    ]
  });
});
```

### 1.3 FCM Token Registration

```javascript
// fcm-service.js
import { messaging } from './firebase-config.js';
import { getToken, onMessage } from 'firebase/messaging';

class FCMService {
  async requestPermissionAndGetToken() {
    try {
      // Request notification permission
      const permission = await Notification.requestPermission();
      
      if (permission === 'granted') {
        console.log('✅ Notification permission granted');
        
        // Get FCM token
        const token = await getToken(messaging, {
          vapidKey: 'YOUR_VAPID_KEY' // Get from Firebase Console
        });
        
        if (token) {
          console.log('🔑 FCM Token:', token);
          await this.sendTokenToBackend(token);
          return token;
        }
      } else {
        console.log('❌ Notification permission denied');
      }
    } catch (error) {
      console.error('❌ FCM token error:', error);
    }
    
    return null;
  }
  
  async sendTokenToBackend(token) {
    try {
      // Send token to your backend
      const response = await fetch('/api/staff/fcm-token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${yourAuthToken}`
        },
        body: JSON.stringify({ fcm_token: token })
      });
      
      if (response.ok) {
        console.log('✅ FCM token sent to backend');
      }
    } catch (error) {
      console.error('❌ Failed to send FCM token to backend:', error);
    }
  }
  
  setupForegroundListener() {
    // Listen for foreground messages
    onMessage(messaging, (payload) => {
      console.log('🔔 FCM received!', payload);
      
      // 1. Show toast immediately 
      this.showInAppNotification(payload);
      
      // 2. Pass to eventBus for chat updates
      if (window.handleIncomingRealtimeEvent) {
        window.handleIncomingRealtimeEvent({
          source: 'fcm',
          payload: payload
        });
      }
    });
  }
  
  showInAppNotification(payload) {
    // 🔥 SIMPLE: Just show the toast!
    const { title, body } = payload.notification || {};
    
    // Show toast immediately when FCM received
    showToast({
      title: title || 'New Message', 
      message: body || 'You have a new message',
      type: 'info'
    });
  }
}

export const fcmService = new FCMService();
```

---

## 🚀 Part 2: Integration with EventBus

### 2.1 Initialize FCM in Your App

```javascript
// App.jsx or main.js
import { fcmService } from './services/fcm-service.js';

// Initialize FCM when app starts
async function initializeApp() {
  // Setup FCM
  await fcmService.requestPermissionAndGetToken();
  fcmService.setupForegroundListener();
  
  // Your other app initialization...
}

initializeApp();
```

### 2.2 EventBus Integration

Your `eventBus.js` needs a small fix for FCM message handling. Update the `normalizeFcmEvent` function:

```javascript
// eventBus.js - Fix FCM normalization
function normalizeFcmEvent(fcmPayload) {
  const data = fcmPayload?.data || {};
  
  // ✅ CRITICAL FIX: Handle "staff_chat_message" type from backend
  if (data.type === "staff_chat_message") {
    console.log('🔥 [FCM] Normalizing staff_chat_message:', data);
    return {
      category: "staff_chat",
      type: "realtime_staff_chat_message_created",
      payload: {
        id: data.message_id ? parseInt(data.message_id) : undefined,
        conversation_id: data.conversation_id ? parseInt(data.conversation_id) : undefined,
        sender_id: data.sender_id ? parseInt(data.sender_id) : undefined,
        sender_name: data.sender_name,
        message: fcmPayload?.notification?.body || data.message || "",
        timestamp: new Date().toISOString(),
        is_group: data.is_group === "True"
      },
      meta: {
        hotel_slug: data.hotel_slug,
        source: "fcm",
        event_id: `fcm-${Date.now()}`,
        ts: new Date().toISOString(),
        url: data.url,
        click_action: data.click_action
      }
    };
  }
  
  // Handle conversation count updates (sent via Pusher, not FCM)
  if (data.type === "staff_chat_conversations_with_unread") {
    return {
      category: "staff_chat", 
      type: "realtime_staff_chat_conversations_with_unread",
      payload: {
        conversations_with_unread_count: data.conversations_with_unread_count
          ? parseInt(data.conversations_with_unread_count)
          : (data.conversations_with_unread ? parseInt(data.conversations_with_unread) : 0)
      },
      meta: {
        hotel_slug: data.hotel_slug,
        source: "fcm",
        event_id: `fcm-${Date.now()}`,
        ts: new Date().toISOString()
      }
    };
  }
  
  console.warn('⚠️ [FCM] Unhandled FCM type:', data.type);
  return null;
}

// FCM integration in your app
handleIncomingRealtimeEvent({
  source: 'fcm',
  payload: fcmPayload // Raw FCM payload from Firebase
});
```

The eventBus will:
1. **Normalize FCM payload** using fixed `normalizeFcmEvent()`
2. **Route to chatStore** for message events  
3. **Update unread counts** for conversation count events
4. **Add to notification center** if needed

---

## 📊 Part 3: Unread Conversations Count Widget

### 3.1 Backend Data Structure

The backend sends conversation count updates via **Pusher** (not FCM):

```javascript
// Pusher event payload
{
  category: "staff_chat",
  type: "realtime_staff_chat_conversations_with_unread",
  payload: {
    staff_id: 36,
    conversations_with_unread: 3, // Number of conversations with unread messages
    updated_at: "2025-12-11T08:52:28Z"
  },
  meta: {
    event_id: "evt_123",
    ts: "2025-12-11T08:52:28Z"
  }
}
```

### 3.2 Chat Store Integration

Your `chatStore.jsx` should handle this via `dispatchUnreadCountsUpdate()`:

```javascript
// chatStore.jsx
import { create } from 'zustand';

const useChatStore = create((set, get) => ({
  // State
  conversations: [],
  totalUnreadCount: 0,
  conversationsWithUnreadCount: 0, // This is what you need for widget
  
  // Actions
  updateUnreadCounts: (payload) => {
    const { 
      conversationId,
      conversationUnread,
      totalUnread,
      isTotalUpdate 
    } = payload;
    
    set((state) => {
      const newState = { ...state };
      
      if (isTotalUpdate) {
        // Total unread count update
        newState.totalUnreadCount = totalUnread || 0;
      } else if (conversationId) {
        // Individual conversation update
        const conversation = newState.conversations.find(c => c.id === conversationId);
        if (conversation) {
          conversation.unread_count = conversationUnread || 0;
        }
      }
      
      // Calculate conversations with unread count
      newState.conversationsWithUnreadCount = newState.conversations.filter(
        conv => conv.unread_count > 0
      ).length;
      
      console.log('📊 Updated unread counts:', {
        totalUnread: newState.totalUnreadCount,
        conversationsWithUnread: newState.conversationsWithUnreadCount
      });
      
      return newState;
    });
  }
}));

// Export function for eventBus
export const dispatchUnreadCountsUpdate = (payload) => {
  useChatStore.getState().updateUnreadCounts(payload);
};

export const chatActions = {
  handleEvent: (event) => {
    const { type, payload } = event;
    
    switch (type) {
      case 'realtime_staff_chat_message_created':
        // Handle new message
        break;
        
      case 'realtime_staff_chat_conversations_with_unread':
        // Handle conversation count update
        dispatchUnreadCountsUpdate({
          isTotalUpdate: true,
          conversationsWithUnread: payload.conversations_with_unread
        });
        break;
        
      default:
        console.log('Unhandled chat event:', type);
    }
  }
};

export default useChatStore;
```

### 3.3 Popup Widget Component

```javascript
// MessengerWidget.jsx
import React from 'react';
import useChatStore from './stores/chatStore';

const MessengerWidget = () => {
  const { conversationsWithUnreadCount, totalUnreadCount } = useChatStore();
  
  // Use conversationsWithUnreadCount for the badge
  const badgeCount = conversationsWithUnreadCount;
  const showBadge = badgeCount > 0;
  
  return (
    <div className={`messenger-widget ${showBadge ? 'messenger-widget--unread' : ''}`}>
      <div className="messenger-widget__header">
        <span>Messages</span>
        {showBadge && (
          <span className="messenger-widget__badge">
            {badgeCount > 99 ? '99+' : badgeCount}
          </span>
        )}
      </div>
      
      {/* Your chat content */}
    </div>
  );
};

export default MessengerWidget;
```

---

## 🧪 Part 4: Testing & Debugging

### 4.1 Test FCM Reception

```javascript
// Add to your browser console for testing
window.testFCM = () => {
  // ✅ CORRECTED: Simulate exact FCM message format from backend
  if (window.handleIncomingRealtimeEvent) {
    window.handleIncomingRealtimeEvent({
      source: 'fcm',
      payload: {
        from: "1020698338972",
        messageId: "test-message-id",
        notification: {
          title: "💬 Test User",
          body: "Test message content"
        },
        data: {
          type: "staff_chat_message", // ✅ This is the correct type from backend
          click_action: "/staff-chat/hotel-killarney/conversation/100",
          hotel_slug: "hotel-killarney",
          url: "https://hotelsmates.com/staff-chat/hotel-killarney/conversation/100",
          is_group: "False",
          message_id: "123",
          conversation_id: "100", 
          sender_id: "36",
          sender_name: "Test User"
        }
      }
    });
  }
};

// Test conversation count update
window.testConversationCount = (count = 5) => {
  if (window.handleIncomingRealtimeEvent) {
    window.handleIncomingRealtimeEvent({
      source: 'pusher',
      channel: 'hotel-killarney.staff-36-notifications',
      eventName: 'realtime_staff_chat_conversations_with_unread',
      payload: {
        category: 'staff_chat',
        type: 'realtime_staff_chat_conversations_with_unread',
        payload: {
          staff_id: 36,
          conversations_with_unread: count,
          updated_at: new Date().toISOString()
        }
      }
    });
  }
};
```

### 4.2 Debug Logging

Add this to see what's happening:

```javascript
// In your component or store
useEffect(() => {
  console.log('🔍 Current unread state:', {
    totalUnreadCount,
    conversationsWithUnreadCount,
    showBadge: conversationsWithUnreadCount > 0
  });
}, [totalUnreadCount, conversationsWithUnreadCount]);
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: FCM Token Not Saved
**Problem:** Token generated but not reaching backend
**Solution:** Check network requests and ensure proper authentication

### Issue 2: Background Notifications Not Working
**Problem:** Service worker not registered
**Solution:** Ensure `firebase-messaging-sw.js` is in `public/` folder

### Issue 3: Unread Count Not Updating
**Problem:** Widget not reflecting changes
**Solution:** Check Zustand store updates and React component subscriptions

### Issue 4: FCM Events Not Being Processed
**Problem:** "No handler found for FCM type: staff_chat_message" 
**Solution:** Ensure `normalizeFcmEvent` handles `"staff_chat_message"` type correctly

### Issue 5: FCM vs Pusher Event Conflicts
**Problem:** Duplicate events or wrong counts
**Solution:** Use your eventBus - it handles both sources correctly

---

## 📋 Integration Checklist

- [ ] Firebase project setup with FCM enabled
- [ ] VAPID key configured
- [ ] Service worker (`firebase-messaging-sw.js`) in place
- [ ] FCM token registration implemented
- [ ] Foreground message listener setup
- [ ] EventBus integration completed
- [ ] Chat store handles unread count events
- [ ] Widget component subscribed to store
- [ ] Test functions working
- [ ] Backend FCM token endpoint ready

---

## 🚀 Quick Start Summary

1. **Setup Firebase** - Add config and service worker
2. **Request permission** - Get FCM token and send to backend
3. **Listen for messages** - Setup foreground listener
4. **Connect eventBus** - Use existing `handleIncomingRealtimeEvent()`
5. **Update widget** - Subscribe to `conversationsWithUnreadCount` from store
6. **Test everything** - Use debug functions to verify

Your backend FCM system is already working perfectly! This guide gets the frontend connected to receive and process those notifications properly.