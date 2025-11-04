# Guest PIN Validation - URL Fix

## Issue
Frontend getting 404 error:
```
POST https://hotelsmates.com/api/chat/hotel-killarney/room/101/validate-chat-pin/ 404 (Not Found)
```

## Problem
**Frontend is calling the wrong URL!**

❌ **Frontend URL**: `/api/chat/{hotel_slug}/room/{room_number}/validate-chat-pin/`

✅ **Correct URL**: `/api/chat/{hotel_slug}/messages/room/{room_number}/validate-chat-pin/`

**Missing `/messages/` in the path!**

## Two Options for Guest Session

### Option 1: Simple PIN Validation (Updated)
Use the enhanced `validate_chat_pin` endpoint I just updated.

**URL**: `POST /api/chat/{hotel_slug}/messages/room/{room_number}/validate-chat-pin/`

**Request**:
```json
{
  "pin": "1234",
  "fcm_token": "optional_token"
}
```

**Response**:
```json
{
  "valid": true,
  "fcm_token_saved": true,
  "session_data": {
    "session_id": "uuid",
    "room_number": "101",
    "hotel_slug": "hotel-killarney",
    "conversation_id": "uuid",
    "guest_name": "John Doe",
    "pusher_channel": "hotel-killarney-room-101-chat"
  }
}
```

### Option 2: Full Session Management (Recommended)
Use `initialize_guest_session` - this is more robust and includes session token management.

**URL**: `POST /api/chat/{hotel_slug}/guest-session/room/{room_number}/initialize/`

**Request**:
```json
{
  "pin": "1234",
  "session_token": "optional_existing_token"
}
```

**Response**:
```json
{
  "session_token": "uuid_token",
  "conversation_id": 123,
  "room_number": "101",
  "is_new_session": true,
  "pusher_channel": "hotel-killarney-room-101-chat",
  "current_staff_handler": null
}
```

## Frontend Fix Required

### Quick Fix (Option 1)
Just add `/messages/` to the URL:

```javascript
// ❌ WRONG - Missing /messages/
const response = await fetch(
  `/api/chat/${hotelSlug}/room/${roomNumber}/validate-chat-pin/`,
  { /* ... */ }
);

// ✅ CORRECT - Has /messages/
const response = await fetch(
  `/api/chat/${hotelSlug}/messages/room/${roomNumber}/validate-chat-pin/`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      pin: userPin,
      fcm_token: fcmToken // optional
    })
  }
);
```

### Better Implementation (Option 2 - Recommended)
Use the session management endpoint:

```javascript
const initializeGuestSession = async (pin, fcmToken) => {
  try {
    // Check if we have an existing session token
    const existingToken = localStorage.getItem('guestSessionToken');
    
    const response = await fetch(
      `/api/chat/${hotelSlug}/guest-session/room/${roomNumber}/initialize/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          pin,
          session_token: existingToken // Will reuse if valid
        })
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      
      // Store the session token
      localStorage.setItem('guestSessionToken', data.session_token);
      
      // Store session data
      const sessionData = {
        sessionToken: data.session_token,
        conversationId: data.conversation_id,
        roomNumber: data.room_number,
        pusherChannel: data.pusher_channel,
        hotelSlug: hotelSlug,
        isNewSession: data.is_new_session
      };
      
      localStorage.setItem('guestChatSession', JSON.stringify(sessionData));
      
      console.log('✅ Guest session initialized:', data);
      
      // Now save FCM token separately
      if (fcmToken) {
        await saveFCMTokenForGuest(data.room_number, fcmToken);
      }
      
      return sessionData;
    } else {
      const error = await response.json();
      console.error('❌ Session initialization failed:', error);
      throw new Error(error.error || 'Invalid PIN');
    }
  } catch (error) {
    console.error('❌ Error during guest session initialization:', error);
    throw error;
  }
};

// Separate function to save FCM token (after PIN validation)
const saveFCMTokenForGuest = async (roomNumber, fcmToken) => {
  try {
    const response = await fetch(
      `/api/chat/${hotelSlug}/messages/room/${roomNumber}/validate-chat-pin/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          pin: userPin, // You'll need to keep this
          fcm_token: fcmToken
        })
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ FCM token saved:', data.fcm_token_saved);
    }
  } catch (error) {
    console.error('⚠️ Failed to save FCM token:', error);
    // Don't throw - FCM is optional
  }
};
```

## Complete URL Reference

### Chat API URLs (all relative to `/api/chat/`)

| Endpoint | Method | URL Pattern |
|----------|--------|-------------|
| **Validate PIN (Simple)** | POST | `{hotel_slug}/messages/room/{room_number}/validate-chat-pin/` |
| **Initialize Session (Better)** | POST | `{hotel_slug}/guest-session/room/{room_number}/initialize/` |
| **Validate Session Token** | GET | `guest-session/{session_token}/validate/` |
| **Get/Create Conversation** | POST | `{hotel_slug}/conversations/from-room/{room_number}/` |
| **Get Messages** | GET | `{hotel_slug}/conversations/{conversation_id}/messages/` |
| **Send Message** | POST | `{hotel_slug}/conversations/{conversation_id}/messages/send/` |
| **Unread Count for Guest** | GET | `guest-session/{session_token}/unread-count/` |

## Testing the Correct URL

### Test with curl:
```bash
# Option 1: Simple validation (with /messages/)
curl -X POST https://hotelsmates.com/api/chat/hotel-killarney/messages/room/101/validate-chat-pin/ \
  -H "Content-Type: application/json" \
  -d '{"pin": "1234", "fcm_token": "test_token"}'

# Option 2: Session initialization (recommended)
curl -X POST https://hotelsmates.com/api/chat/hotel-killarney/guest-session/room/101/initialize/ \
  -H "Content-Type: application/json" \
  -d '{"pin": "1234"}'
```

### Test in browser console:
```javascript
// Test the correct URL
fetch('/api/chat/hotel-killarney/messages/room/101/validate-chat-pin/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ pin: '1234' })
})
.then(r => r.json())
.then(d => console.log('Response:', d))
.catch(e => console.error('Error:', e));
```

## Common Errors

### Error 1: 404 Not Found
**Cause**: Missing `/messages/` in the URL path
**Fix**: Add `/messages/` before `/room/`

### Error 2: "Unexpected token '<', "<!DOCTYPE "... is not valid JSON"
**Cause**: 404 error returns HTML, not JSON
**Fix**: Use the correct URL to get JSON response

### Error 3: 401 Invalid PIN
**Cause**: Wrong PIN provided
**Fix**: Ensure PIN matches `room.guest_id_pin` in database

## Summary

**Quick fix**: Add `/messages/` to your URL:
- Change: `/api/chat/{hotel}/room/{room}/validate-chat-pin/`
- To: `/api/chat/{hotel}/messages/room/{room}/validate-chat-pin/`

**Better solution**: Use the session management endpoint:
- URL: `/api/chat/{hotel}/guest-session/room/{room}/initialize/`
- Returns session token for persistence
- More robust session management

Both endpoints now return complete session data after my backend updates!
