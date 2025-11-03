# FCM Token Endpoint Migration

## ⚠️ IMPORTANT: Endpoint Has Changed

The FCM token save endpoint has been **moved** from the notifications app to the staff app.

---

## What Changed

### ❌ OLD ENDPOINT (Deprecated)
```
POST /api/notifications/save-fcm-token/
```
**Status**: Returns `410 Gone` with migration message

### ✅ NEW ENDPOINT (Use This)
```
POST /api/staff/save-fcm-token/
```
**Status**: Active and working

---

## Frontend Code Update Required

### Old Code (REMOVE)
```javascript
const response = await axios.post(
  `${API_URL}/api/notifications/save-fcm-token/`,
  { fcm_token: fcmToken },
  {
    headers: {
      'Authorization': `Token ${authToken}`,
      'Content-Type': 'application/json'
    }
  }
);
```

### New Code (USE THIS)
```javascript
const response = await axios.post(
  `${API_URL}/api/staff/save-fcm-token/`,
  { fcm_token: fcmToken },
  {
    headers: {
      'Authorization': `Token ${authToken}`,
      'Content-Type': 'application/json'
    }
  }
);
```

**Only change**: `/api/notifications/save-fcm-token/` → `/api/staff/save-fcm-token/`

---

## Request & Response (No Change)

### Request
```json
{
  "fcm_token": "eJxVzE0KgzAQBeDrBG8QmEwSx3-MmKRgF0VQcKEgdtHa..."
}
```

### Success Response (200 OK)
```json
{
  "message": "FCM token saved successfully",
  "staff_id": 36,
  "has_fcm_token": true
}
```

### Error Responses
```json
// Missing token
{
  "error": "FCM token is required"
}

// No staff profile
{
  "error": "Staff profile not found for this user"
}
```

---

## Why the Change?

- FCM tokens are **staff-specific** (only porters need push notifications)
- The functionality logically belongs in the **staff module**
- Keeps notifications module focused on notification management

---

## Action Required

1. Find all references to `/api/notifications/save-fcm-token/` in your frontend
2. Replace with `/api/staff/save-fcm-token/`
3. Test the token saving flow
4. Deploy updated frontend

---

## Questions?

See full documentation in `HOW_TO_SAVE_FCM_TOKEN.md`
