# Quick Guide: How to Save FCM Token to Backend

## API Endpoint

**URL**: `POST /api/staff/save-fcm-token/`

**Authentication**: Required (Token-based)

**Request Body**:
```json
{
  "fcm_token": "your_browser_fcm_token_here"
}
```

**Success Response** (200 OK):
```json
{
  "message": "FCM token saved successfully",
  "staff_id": 36,
  "has_fcm_token": true
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "FCM token is required"
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Staff profile not found for this user"
}
```

---

## Frontend Implementation (React)

### Step 1: Get FCM Token from Firebase

After Firebase is initialized and user grants permission:

```javascript
import { getToken } from 'firebase/messaging';
import { messaging } from '../config/firebase';

const VAPID_KEY = 'YOUR_VAPID_KEY'; // From Firebase Console

async function getFCMToken() {
  try {
    const token = await getToken(messaging, {
      vapidKey: VAPID_KEY
    });
    
    if (token) {
      console.log('FCM Token:', token);
      return token;
    } else {
      console.log('No token available');
      return null;
    }
  } catch (error) {
    console.error('Error getting FCM token:', error);
    return null;
  }
}
```

### Step 2: Send Token to Backend

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

async function saveFCMTokenToBackend(fcmToken) {
  try {
    // Get auth token from wherever you store it
    const authToken = localStorage.getItem('auth_token');
    // or: const authToken = cookies.get('auth_token');
    // or: const authToken = sessionStorage.getItem('auth_token');
    
    const response = await axios.post(
      `${API_BASE_URL}/api/staff/save-fcm-token/`,
      {
        fcm_token: fcmToken
      },
      {
        headers: {
          'Authorization': `Token ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    console.log('✅ FCM token saved:', response.data);
    return response.data;
    
  } catch (error) {
    console.error('❌ Error saving FCM token:', error.response?.data || error);
    throw error;
  }
}
```

### Step 3: Complete Flow (After User Login)

```javascript
// After successful login, request notification permission and save token
async function setupNotifications() {
  try {
    // Request notification permission
    const permission = await Notification.requestPermission();
    
    if (permission === 'granted') {
      console.log('✓ Notification permission granted');
      
      // Get FCM token
      const fcmToken = await getFCMToken();
      
      if (fcmToken) {
        // Save to backend
        await saveFCMTokenToBackend(fcmToken);
        
        // Also save locally for reference
        localStorage.setItem('fcm_token', fcmToken);
        
        console.log('✅ Push notifications enabled!');
      }
    } else {
      console.log('❌ Notification permission denied');
    }
  } catch (error) {
    console.error('Error setting up notifications:', error);
  }
}

// Call this after login
async function handleLoginSuccess(userData) {
  // Save auth token first
  localStorage.setItem('auth_token', userData.token);
  
  // Then set up notifications (for porters only)
  if (userData.role === 'Porter' || userData.role?.slug === 'porter') {
    await setupNotifications();
  }
}
```

---

## Using Fetch Instead of Axios

If you prefer `fetch` over `axios`:

```javascript
async function saveFCMTokenToBackend(fcmToken) {
  try {
    const authToken = localStorage.getItem('auth_token');
    
    const response = await fetch(
      `${API_BASE_URL}/api/staff/save-fcm-token/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Token ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fcm_token: fcmToken
        })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to save FCM token');
    }

    const data = await response.json();
    console.log('✅ FCM token saved:', data);
    return data;
    
  } catch (error) {
    console.error('❌ Error saving FCM token:', error);
    throw error;
  }
}
```

---

## cURL Example (For Testing)

```bash
curl -X POST http://localhost:8000/api/staff/save-fcm-token/ \
  -H "Authorization: Token YOUR_AUTH_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"fcm_token": "YOUR_FCM_TOKEN_HERE"}'
```

**Example with real values**:
```bash
curl -X POST http://localhost:8000/api/staff/save-fcm-token/ \
  -H "Authorization: Token a1b2c3d4e5f6g7h8i9j0" \
  -H "Content-Type: application/json" \
  -d '{"fcm_token": "eJxVzE0KgzAQBeDrBG8QmEwSx3-MmKRgF0VQcKEgdtHa..."}'
```

---

## Testing the Token

After saving, verify it's stored in the database:

### Option 1: Django Admin
1. Go to Django Admin: `http://localhost:8000/admin/`
2. Navigate to: **Staff** → Click on your porter
3. Check the **fcm_token** field - should have a long string

### Option 2: Python Script
```python
from staff.models import Staff

porter = Staff.objects.get(id=36)  # Your porter ID
print(f"FCM Token: {porter.fcm_token}")
print(f"Has token: {bool(porter.fcm_token)}")
```

### Option 3: API Response
The save endpoint returns confirmation:
```json
{
  "message": "FCM token saved successfully",
  "staff_id": 36,
  "has_fcm_token": true  // ✅ This confirms it's saved
}
```

---

## Token Refresh

FCM tokens can expire or change. Handle token refresh:

```javascript
import { onTokenRefresh } from 'firebase/messaging';
import { messaging } from '../config/firebase';

// Listen for token refresh
onTokenRefresh(messaging, async (newToken) => {
  console.log('🔄 FCM token refreshed:', newToken);
  
  // Save new token to backend
  await saveFCMTokenToBackend(newToken);
  
  // Update local storage
  localStorage.setItem('fcm_token', newToken);
});
```

---

## Common Issues

### 1. "401 Unauthorized"
**Problem**: Auth token not included or invalid

**Solution**: 
```javascript
// Make sure you're sending the auth token
const authToken = localStorage.getItem('auth_token');
if (!authToken) {
  console.error('No auth token found!');
  return;
}
```

### 2. "404 Staff profile not found"
**Problem**: User is not linked to a Staff profile

**Solution**: User must be a staff member with a profile in the database

### 3. Token not saving
**Problem**: Request not reaching backend

**Solution**: Check CORS settings and API URL:
```javascript
// Make sure API_BASE_URL is correct
const API_BASE_URL = 'http://localhost:8000'; // Development
// or
const API_BASE_URL = 'https://your-api.com'; // Production
```

---

## Complete Example Component

```javascript
import React, { useEffect } from 'react';
import { getToken, onMessage } from 'firebase/messaging';
import { messaging } from './config/firebase';
import axios from 'axios';

const VAPID_KEY = process.env.REACT_APP_FIREBASE_VAPID_KEY;
const API_URL = process.env.REACT_APP_API_URL;

function App() {
  useEffect(() => {
    const setupPushNotifications = async () => {
      // Check if user is authenticated
      const authToken = localStorage.getItem('auth_token');
      if (!authToken) return;

      // Request permission
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') return;

      try {
        // Get FCM token
        const fcmToken = await getToken(messaging, {
          vapidKey: VAPID_KEY
        });

        if (fcmToken) {
          // Save to backend
          await axios.post(
            `${API_URL}/api/staff/save-fcm-token/`,
            { fcm_token: fcmToken },
            {
              headers: {
                'Authorization': `Token ${authToken}`,
                'Content-Type': 'application/json',
              }
            }
          );

          console.log('✅ Push notifications enabled');
          localStorage.setItem('fcm_token', fcmToken);
        }
      } catch (error) {
        console.error('Error setting up push notifications:', error);
      }
    };

    setupPushNotifications();
  }, []);

  return <div className="App">{/* Your app */}</div>;
}

export default App;
```

---

## Summary

1. **Get FCM token** from Firebase using `getToken(messaging, { vapidKey })`
2. **Send to backend** via `POST /api/staff/save-fcm-token/`
3. **Include auth token** in `Authorization: Token <token>` header
4. **Verify success** by checking response or database

That's it! Once the token is saved, porters will receive push notifications automatically when orders are created. 🎉
