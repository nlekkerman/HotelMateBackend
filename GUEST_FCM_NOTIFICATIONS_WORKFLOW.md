# Guest FCM Push Notifications - Complete Workflow Guide

## Overview

Anonymous guests can now receive **Firebase push notifications** even when the browser is closed! The FCM token is saved per room, so whoever verifies with the room PIN gets notifications.

---

## Complete Workflow

```
1. Guest scans QR code → Opens /room-service/{hotel-slug}/{room-number}
2. Guest enters PIN → Backend validates PIN ✅
3. Frontend requests notification permission → User allows
4. Frontend gets FCM token from Firebase
5. Frontend sends token to backend → Saves to Room.guest_fcm_token
6. Guest browses menu and places order
7. Porter changes order status → Backend sends:
   - Pusher notification (if browser open)
   - FCM push notification (if browser closed) 📱
8. Guest receives notification on their device!
```

---

## Backend Changes (Already Done ✅)

### 1. Room Model
```python
# rooms/models.py
class Room(models.Model):
    # ... existing fields ...
    guest_fcm_token = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="FCM token for push notifications to guest"
    )
```

### 2. New API Endpoint
```
POST /api/room_services/{hotel-slug}/room/{room-number}/save-fcm-token/
Body: { "fcm_token": "fXYZ..." }
Response: { "success": true, "message": "FCM token saved successfully" }
```

### 3. Order Status Update
When porter changes order status, backend now sends:
- ✅ Pusher to room channel (real-time if browser open)
- ✅ FCM push notification (works even if browser closed)

---

## Frontend Implementation

### Step 1: Update Verification Page

Modify `src/pages/RoomServiceVerification.jsx`:

```javascript
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { requestFCMPermission } from '../utils/fcm';
import api from '../api';

function RoomServiceVerification() {
  const { hotelSlug, roomNumber } = useParams();
  const navigate = useNavigate();
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleVerifyPin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // 1. Verify PIN
      const response = await api.post(
        `/api/room_services/${hotelSlug}/${roomNumber}/validate-pin/`,
        { pin }
      );

      if (response.data.valid) {
        // 2. Store verification
        sessionStorage.setItem(`verified_${hotelSlug}_${roomNumber}`, 'true');
        
        // 3. Request FCM permission and save token
        try {
          const fcmToken = await requestFCMPermission();
          
          if (fcmToken) {
            // Save FCM token to backend
            await api.post(
              `/api/room_services/${hotelSlug}/room/${roomNumber}/save-fcm-token/`,
              { fcm_token: fcmToken }
            );
            console.log('✅ FCM token saved successfully');
          }
        } catch (fcmError) {
          // FCM is optional - don't block if it fails
          console.warn('FCM permission denied or failed:', fcmError);
        }
        
        // 4. Redirect to menu
        navigate(`/room-service/${hotelSlug}/${roomNumber}/menu`);
      }
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Invalid PIN. Please try again.');
      } else {
        setError('Verification failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="verification-page">
      <div className="verification-card">
        <h1>🏨 Room Service</h1>
        <p>Room {roomNumber}</p>
        
        <form onSubmit={handleVerifyPin}>
          <div className="form-group">
            <label>Enter your room PIN:</label>
            <input
              type="password"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength="4"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              placeholder="****"
              required
              autoFocus
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading || pin.length < 4}>
            {loading ? 'Verifying...' : 'Continue'}
          </button>
        </form>

        <p className="help-text">
          Your PIN is located on your room key card or welcome letter.
        </p>
        
        <p className="notification-info">
          💡 You'll be asked to allow notifications to receive order updates
        </p>
      </div>
    </div>
  );
}

export default RoomServiceVerification;
```

---

### Step 2: Create FCM Utility

Create `src/utils/fcm.js`:

```javascript
import { messaging, getToken } from '../config/firebase';

const VAPID_KEY = 'YOUR_VAPID_KEY_FROM_FIREBASE_CONSOLE';

export const requestFCMPermission = async () => {
  try {
    // Check if browser supports notifications
    if (!('Notification' in window)) {
      console.log('This browser does not support notifications');
      return null;
    }

    // Check if service workers are supported
    if (!('serviceWorker' in navigator)) {
      console.log('Service workers not supported');
      return null;
    }

    // Register service worker
    const registration = await navigator.serviceWorker.register(
      '/firebase-messaging-sw.js'
    );
    console.log('Service worker registered:', registration);

    // Request permission
    const permission = await Notification.requestPermission();
    
    if (permission === 'granted') {
      console.log('Notification permission granted');
      
      // Get FCM token
      const token = await getToken(messaging, {
        vapidKey: VAPID_KEY,
        serviceWorkerRegistration: registration
      });

      if (token) {
        console.log('FCM Token:', token);
        return token;
      } else {
        console.log('No registration token available');
        return null;
      }
    } else {
      console.log('Notification permission denied');
      return null;
    }
  } catch (error) {
    console.error('Error getting FCM permission:', error);
    return null;
  }
};
```

---

### Step 3: Keep Firebase Service Worker

Your existing `public/firebase-messaging-sw.js` handles background notifications:

```javascript
// Give the service worker access to Firebase Messaging
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

// Initialize Firebase
firebase.initializeApp({
  apiKey: "YOUR_API_KEY",
  authDomain: "hotel-mate-d878f.firebaseapp.com",
  projectId: "hotel-mate-d878f",
  storageBucket: "hotel-mate-d878f.firebasestorage.app",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('Received background message:', payload);

  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/notification-icon.png',
    badge: '/badge-icon.png',
    tag: 'room-service-order',
    data: payload.data,
    requireInteraction: true,
    vibrate: [200, 100, 200]
  };

  return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  event.notification.close();

  // Open the app if not already open
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if ('focus' in client) {
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow('/');
        }
      })
  );
});
```

---

## How It Works

### When Guest is Browsing (Browser Open)
- Pusher sends real-time update
- UI updates instantly
- No push notification needed

### When Guest Closes Browser
- Order status changes
- Backend finds Room by room_number
- Backend gets Room.guest_fcm_token
- Firebase sends push notification to guest's device 📱
- Guest sees notification even with browser closed!

---

## Testing

### 1. Test PIN Verification & FCM Token Saving
```bash
# Terminal 1: Watch backend logs
python manage.py runserver

# Browser Console:
1. Visit: http://localhost:5173/room-service/hotel-killarney/102
2. Enter PIN: 1234
3. Check console for:
   - "Service worker registered"
   - "Notification permission granted"
   - "FCM Token: fXYZ..."
   - "✅ FCM token saved successfully"

# Backend logs should show:
# "FCM token saved for room 102 at Hotel Killarney"
```

### 2. Test Push Notification
```bash
# Place an order as guest
# Then change order status as porter
# Guest should receive:
# - Pusher update (if browser open)
# - Push notification (if browser closed)
```

### 3. Verify Token Saved
```python
# Django shell
from rooms.models import Room
room = Room.objects.get(hotel__slug='hotel-killarney', room_number=102)
print(room.guest_fcm_token)  # Should show the token
```

---

## Important Notes

### Token Persistence
- ✅ **Per Room**: Token is saved to Room model
- ✅ **Survives Checkout**: Token stays until next guest overwrites it
- ✅ **Multiple Devices**: Last device to verify gets notifications
- ⚠️ **Privacy**: Token is replaced when next guest verifies

### Security
- ✅ PIN required before FCM permission request
- ✅ Token saved only after successful PIN verification
- ✅ No personal data stored (anonymous)
- ✅ SessionStorage for verification (expires on browser close)

### Browser Compatibility
- ✅ Chrome/Edge (Desktop & Mobile)
- ✅ Firefox (Desktop & Mobile)
- ❌ Safari (requires different implementation)

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/room_services/{hotel-slug}/{room-number}/validate-pin/` | POST | Verify room PIN |
| `/api/room_services/{hotel-slug}/room/{room-number}/save-fcm-token/` | POST | Save FCM token to room |
| `/api/room_services/{hotel-slug}/orders/` | POST | Create order |

---

## Notification Types

### Pusher (Real-time)
**Channel:** `{hotel-slug}-room-{room-number}`  
**Event:** `order-status-update`  
**When:** Browser is open  
**Requires:** Nothing (anonymous)

### FCM (Push Notification)
**Token Stored:** `Room.guest_fcm_token`  
**When:** Browser is closed  
**Requires:** Notification permission

---

## Success Indicators

When everything works:
1. ✅ PIN verified successfully
2. ✅ Permission popup appears
3. ✅ User grants permission
4. ✅ FCM token obtained
5. ✅ Token saved to backend
6. ✅ Guest places order
7. ✅ Porter changes status
8. ✅ Guest receives push notification 📱

---

## Troubleshooting

**No permission popup?**
- Check if notifications are blocked in browser settings
- Clear site data and try again

**Token not saving?**
- Check network tab for POST to `/save-fcm-token/`
- Verify response is 200 OK
- Check backend logs

**No push notifications?**
- Close browser completely (not just tab)
- Verify token is in database
- Check Heroku logs for FCM send confirmation
- Test with `send_manual_fcm_test.py`

---

You now have **full push notification support for anonymous guests!** 🎉

The backend is ready. Just implement the frontend changes above!
