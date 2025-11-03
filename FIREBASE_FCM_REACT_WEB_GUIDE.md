# Firebase Cloud Messaging (FCM) - React Web Integration Guide

## Overview
This guide explains how to integrate Firebase Cloud Messaging (FCM) push notifications in your **React Web App** to receive browser push notifications even when the tab is inactive or closed.

## What This Adds
- **Browser Push Notifications**: Porters receive desktop/browser notifications when tab is inactive
- **Dual Delivery System**: 
  - **Pusher**: Real-time updates when app tab is active ✅ (already working)
  - **FCM**: Browser push notifications when tab is inactive/closed ✅ (new)

---

## Backend Changes (Already Completed ✅)

The backend now:
1. ✅ Has `fcm_token` field in Staff model
2. ✅ Sends both Pusher AND FCM notifications for all porter alerts
3. ✅ Provides `/api/staff/save-fcm-token/` endpoint to save device tokens
4. ✅ Configured Firebase Admin SDK with credentials

---

## Frontend Implementation Steps

### Step 1: Install Firebase Dependencies

```bash
npm install firebase
# or
yarn add firebase
```

### Step 2: Configure Firebase in Your React App

#### Create Firebase Config File

Create `src/config/firebase.js`:

```javascript
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

// Your web app's Firebase configuration
// Get these values from Firebase Console: https://console.firebase.google.com/
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "hotel-mate-d878f.firebaseapp.com",
  projectId: "hotel-mate-d878f",
  storageBucket: "hotel-mate-d878f.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID",
  measurementId: "YOUR_MEASUREMENT_ID"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Cloud Messaging
const messaging = getMessaging(app);

export { messaging, getToken, onMessage };
```

**To get your Firebase config:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: **hotel-mate-d878f**
3. Click the gear icon → Project Settings
4. Scroll to "Your apps" → Web apps
5. If no web app exists, click "Add app" and select Web
6. Copy the `firebaseConfig` object

### Step 3: Create Firebase Service Worker

Create `public/firebase-messaging-sw.js`:

```javascript
// Firebase messaging service worker
// This runs in the background to receive notifications when tab is closed

importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// Initialize Firebase in service worker
firebase.initializeApp({
  apiKey: "YOUR_API_KEY",
  authDomain: "hotel-mate-d878f.firebaseapp.com",
  projectId: "hotel-mate-d878f",
  storageBucket: "hotel-mate-d878f.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('Background message received:', payload);
  
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/notification-icon.png',
    badge: '/badge-icon.png',
    tag: payload.data.type || 'notification',
    data: payload.data,
    requireInteraction: true, // Keeps notification visible until user interacts
  };

  return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  event.notification.close();

  const urlToOpen = event.notification.data.route || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url.includes(urlToOpen) && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window if not open
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});
```

### Step 4: Create Firebase Notification Service

Create `src/services/firebaseNotificationService.js`:

```javascript
import { messaging, getToken, onMessage } from '../config/firebase';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const VAPID_KEY = 'YOUR_VAPID_KEY'; // Get from Firebase Console → Cloud Messaging → Web Push certificates

class FirebaseNotificationService {
  
  /**
   * Request notification permission and get FCM token
   */
  async requestPermission() {
    try {
      const permission = await Notification.requestPermission();
      
      if (permission === 'granted') {
        console.log('Notification permission granted');
        await this.getFCMToken();
        return true;
      } else {
        console.log('Notification permission denied');
        return false;
      }
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }

  /**
   * Get FCM token and save to backend
   */
  async getFCMToken() {
    try {
      const token = await getToken(messaging, {
        vapidKey: VAPID_KEY
      });
      
      if (token) {
        console.log('FCM Token:', token);
        await this.saveFCMTokenToBackend(token);
        localStorage.setItem('fcm_token', token);
        return token;
      } else {
        console.log('No registration token available');
        return null;
      }
    } catch (error) {
      console.error('Error getting FCM token:', error);
      return null;
    }
  }

  /**
   * Save FCM token to backend
   */
  async saveFCMTokenToBackend(fcmToken) {
    try {
      const authToken = localStorage.getItem('auth_token'); // or however you store auth tokens
      
      const response = await axios.post(
        `${API_BASE_URL}/api/staff/save-fcm-token/`,
        { fcm_token: fcmToken },
        {
          headers: {
            'Authorization': `Token ${authToken}`,
            'Content-Type': 'application/json',
          },
        }
      );

      console.log('FCM token saved to backend:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error saving FCM token to backend:', error);
      throw error;
    }
  }

  /**
   * Set up foreground message handler (when tab is active)
   */
  setupForegroundMessageHandler(onMessageCallback) {
    return onMessage(messaging, (payload) => {
      console.log('Foreground message received:', payload);
      
      // Custom handler for when tab is active
      if (onMessageCallback) {
        onMessageCallback(payload);
      } else {
        // Default: show browser notification
        this.showBrowserNotification(payload);
      }
    });
  }

  /**
   * Show browser notification manually
   */
  showBrowserNotification(payload) {
    if (Notification.permission === 'granted') {
      const { title, body } = payload.notification || {};
      const options = {
        body: body,
        icon: '/notification-icon.png',
        badge: '/badge-icon.png',
        tag: payload.data?.type || 'notification',
        data: payload.data,
        requireInteraction: true,
      };

      new Notification(title, options);
    }
  }

  /**
   * Check if service worker is supported
   */
  isSupported() {
    return 'Notification' in window && 
           'serviceWorker' in navigator && 
           'PushManager' in window;
  }

  /**
   * Get current notification permission status
   */
  getPermissionStatus() {
    if (!('Notification' in window)) {
      return 'unsupported';
    }
    return Notification.permission;
  }
}

export default new FirebaseNotificationService();
```

### Step 5: Initialize Firebase in Your App

In your main `App.js` or `index.js`:

```javascript
import React, { useEffect } from 'react';
import firebaseNotificationService from './services/firebaseNotificationService';

function App() {
  useEffect(() => {
    // Check if browser supports notifications
    if (firebaseNotificationService.isSupported()) {
      // Request permission on app load (or after user login)
      firebaseNotificationService.requestPermission();

      // Set up foreground message handler
      const unsubscribe = firebaseNotificationService.setupForegroundMessageHandler(
        (payload) => {
          console.log('Received notification:', payload);
          
          // Custom handling - e.g., show in-app toast
          // toast.success(payload.notification.body);
          
          // Or play sound
          // new Audio('/notification-sound.mp3').play();
        }
      );

      // Cleanup
      return () => {
        if (unsubscribe) unsubscribe();
      };
    } else {
      console.warn('Push notifications not supported in this browser');
    }
  }, []);

  return (
    <div className="App">
      {/* Your app content */}
    </div>
  );
}

export default App;
```

### Step 6: Request Permission After Login (Recommended)

Better UX: Request permission after user logs in as a porter:

```javascript
// In your Login component or after successful authentication
import firebaseNotificationService from '../services/firebaseNotificationService';

const handleLoginSuccess = async (userData) => {
  // Save auth token
  localStorage.setItem('auth_token', userData.token);
  
  // Check if user is a porter
  if (userData.role === 'Porter' || userData.role?.slug === 'porter') {
    // Request notification permission for porters
    const permissionStatus = firebaseNotificationService.getPermissionStatus();
    
    if (permissionStatus === 'default') {
      // Show custom UI explaining why we need permission
      const userConsent = window.confirm(
        'Enable push notifications to receive order alerts even when the browser is closed?'
      );
      
      if (userConsent) {
        await firebaseNotificationService.requestPermission();
      }
    } else if (permissionStatus === 'granted') {
      // Permission already granted, just get token
      await firebaseNotificationService.getFCMToken();
    }
  }
};
```

### Step 7: Get VAPID Key from Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: **hotel-mate-d878f**
3. Click the gear icon → Project Settings
4. Go to "Cloud Messaging" tab
5. Scroll to "Web Push certificates"
6. Click "Generate key pair" if not already generated
7. Copy the "Key pair" value
8. Replace `YOUR_VAPID_KEY` in the code above

---

## Notification Types Your App Will Receive

### 1. Room Service Order
```json
{
  "notification": {
    "title": "🔔 New Room Service Order",
    "body": "Room 102 - €24.47"
  },
  "data": {
    "type": "room_service_order",
    "order_id": "465",
    "room_number": "102",
    "total_price": "24.47",
    "status": "pending",
    "route": "/orders/room-service"
  }
}
```

### 2. Breakfast Order
```json
{
  "notification": {
    "title": "🍳 New Breakfast Order",
    "body": "Room 305 - Delivery: 08:00"
  },
  "data": {
    "type": "breakfast_order",
    "order_id": "123",
    "room_number": "305",
    "delivery_time": "08:00",
    "status": "pending",
    "route": "/orders/breakfast"
  }
}
```

### 3. Order Count Update
```json
{
  "notification": {
    "title": "📋 Room Service Updates",
    "body": "5 pending order(s)"
  },
  "data": {
    "type": "order_count_update",
    "pending_count": "5",
    "order_type": "room_service_orders"
  }
}
```

---

## Browser Compatibility

### Supported Browsers:
- ✅ Chrome (Desktop & Mobile)
- ✅ Firefox (Desktop & Mobile)
- ✅ Edge (Desktop)
- ✅ Safari 16+ (macOS 13+)
- ✅ Opera (Desktop)

### Not Supported:
- ❌ Internet Explorer
- ❌ Safari on iOS (Apple doesn't support web push notifications on iPhone/iPad yet)

---

## Testing

### Test Notifications:

1. **Open your React app in browser**
2. **Login as a porter**
3. **Grant notification permissions**
4. **Check browser console** - you should see "FCM Token: ..."
5. **Close the browser tab** (or minimize it)
6. **Create a test order** from another browser/device
7. **You should receive a desktop notification!**

### Debug in Browser:

**Chrome DevTools:**
1. Open DevTools (F12)
2. Go to "Application" tab
3. Check "Service Workers" - should see `firebase-messaging-sw.js` active
4. Check "Storage" → "Local Storage" - should see `fcm_token`

**Test Service Worker:**
```javascript
// In browser console
navigator.serviceWorker.getRegistrations().then(registrations => {
  console.log('Registered service workers:', registrations);
});
```

---

## Environment Variables

Add to your `.env` file:

```env
REACT_APP_API_URL=https://your-backend-api.com
REACT_APP_FIREBASE_API_KEY=your_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=hotel-mate-d878f.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=hotel-mate-d878f
REACT_APP_FIREBASE_STORAGE_BUCKET=hotel-mate-d878f.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id
REACT_APP_FIREBASE_VAPID_KEY=your_vapid_key
```

Then update `firebase.js`:

```javascript
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID,
};
```

---

## Troubleshooting

### Notifications Not Received

1. **Check service worker is registered**:
   - Open DevTools → Application → Service Workers
   - Should see `firebase-messaging-sw.js` status: "activated"

2. **Check FCM token is saved**:
   - Check browser LocalStorage for `fcm_token`
   - Verify backend has token: Check staff profile in Django admin

3. **Check browser permissions**:
   - Click padlock icon in address bar
   - Ensure "Notifications" is set to "Allow"

4. **Check staff status**:
   - Staff must have `is_on_duty = True`
   - Staff must have `role = 'Porter'`
   - Staff must be `is_active = True`

### "Service worker not supported"

- Make sure you're using HTTPS (required for service workers)
- Localhost is exempt from HTTPS requirement for testing

### VAPID Key Error

- Make sure you generated Web Push certificates in Firebase Console
- Copy the key exactly (it starts with "B...")
- Don't confuse it with Server Key

---

## Production Deployment

### HTTPS Required

Firebase Cloud Messaging requires HTTPS in production. Make sure your app is deployed with SSL certificate.

### Register Service Worker Path

If your app is deployed to a subdirectory, update the service worker path:

```javascript
// In your React app
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/firebase-messaging-sw.js', {
    scope: '/'
  });
}
```

---

## Optional: Custom Notification UI

Instead of browser notifications, show custom in-app toast:

```javascript
// Install react-toastify or similar
import { toast } from 'react-toastify';

firebaseNotificationService.setupForegroundMessageHandler((payload) => {
  const { title, body } = payload.notification;
  
  toast.info(
    <div>
      <strong>{title}</strong>
      <p>{body}</p>
    </div>,
    {
      onClick: () => {
        // Navigate to order
        if (payload.data.route) {
          window.location.href = payload.data.route;
        }
      }
    }
  );
});
```

---

## Summary

Once implemented, your React web app will:
- ✅ Request notification permissions from users
- ✅ Get FCM token and save to backend
- ✅ Receive real-time updates via Pusher when tab is active
- ✅ Receive browser push notifications via FCM when tab is inactive/closed
- ✅ Handle notification clicks to navigate to orders

Porters will **never miss an order** - notifications work whether the browser is active, minimized, or completely closed! 🎉
