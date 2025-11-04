# Guest Chat Session Fix - PIN Validation Returns Complete Session Data

## Issue
Guest chat window showed:
```
❌ Cannot send message: No userId or guestSession
roomNumber: undefined
guestPusherChannel: null
willSubscribe: false
```

## Root Cause
After PIN validation, the frontend wasn't storing or using the session data properly. The backend was only returning `{valid: true}`, which didn't give the frontend enough information to:
1. Identify the guest
2. Know which room they're in
3. Subscribe to the correct Pusher channel
4. Send messages

## Backend Fix Applied

### Enhanced PIN Validation Response
The `validate_chat_pin` endpoint now returns complete session data:

**Endpoint**: `POST /api/chat/{hotel_slug}/room/{room_number}/validate-chat-pin/`

**Request Body**:
```json
{
  "pin": "1234",
  "fcm_token": "optional_firebase_device_token"
}
```

**Response (Success)**:
```json
{
  "valid": true,
  "fcm_token_saved": true,
  "session_data": {
    "session_id": "uuid-here",
    "room_number": "205",
    "hotel_slug": "hotel-killarney",
    "conversation_id": "conversation-uuid",
    "guest_name": "John Doe",
    "pusher_channel": "hotel-killarney-room-205-chat"
  }
}
```

**Response (Invalid PIN)**:
```json
{
  "valid": false
}
```

### Backend Changes
File: `chat/views.py` - `validate_chat_pin` function

Now automatically:
1. ✅ Gets or creates a `Conversation` for the room
2. ✅ Gets or creates a `GuestChatSession` 
3. ✅ Activates the session if it was inactive
4. ✅ Returns all necessary session data
5. ✅ Saves FCM token if provided
6. ✅ Logs session creation with emoji marker

## Frontend Fix Required

### 1. Store Session Data After PIN Validation

When PIN validation succeeds, **save the `session_data` object**:

```javascript
// In your PIN validation handler
const validatePin = async (pin, fcmToken) => {
  try {
    const response = await fetch(
      `/api/chat/${hotelSlug}/room/${roomNumber}/validate-chat-pin/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          pin, 
          fcm_token: fcmToken // Optional
        })
      }
    );
    
    const data = await response.json();
    
    if (data.valid) {
      // ✅ IMPORTANT: Store the session_data
      const sessionData = data.session_data;
      
      // Store in localStorage for persistence
      localStorage.setItem('guestChatSession', JSON.stringify(sessionData));
      
      // Store in state/context for immediate use
      setGuestSession(sessionData);
      
      // Navigate to chat
      navigate(`/chat/${sessionData.hotel_slug}/conversation/${sessionData.conversation_id}`);
      
      console.log('✅ Guest session established:', sessionData);
    } else {
      alert('Invalid PIN');
    }
  } catch (error) {
    console.error('PIN validation error:', error);
  }
};
```

### 2. Load Session Data in ChatWindow

When the ChatWindow component loads, retrieve the session:

```javascript
// In ChatWindow component
const [guestSession, setGuestSession] = useState(null);
const isGuest = !userId; // If no authenticated userId, they're a guest

useEffect(() => {
  if (isGuest) {
    // Load from localStorage
    const storedSession = localStorage.getItem('guestChatSession');
    if (storedSession) {
      const session = JSON.parse(storedSession);
      setGuestSession(session);
      console.log('🔍 Guest session loaded:', session);
    } else {
      console.error('❌ No guest session found - redirect to PIN entry');
      // Redirect back to PIN validation page
    }
  }
}, [isGuest]);
```

### 3. Use Session Data for Pusher

```javascript
// In your Pusher subscription logic
const setupPusher = () => {
  if (isGuest && guestSession) {
    const channelName = guestSession.pusher_channel;
    // Or construct it: `${guestSession.hotel_slug}-room-${guestSession.room_number}-chat`
    
    const channel = pusher.subscribe(channelName);
    
    channel.bind('new-message', (data) => {
      console.log('📩 New message received:', data);
      setMessages(prev => [...prev, data.message]);
    });
    
    console.log('✅ Pusher subscribed to:', channelName);
  }
};
```

### 4. Use Session Data for Sending Messages

```javascript
const sendMessage = async (messageText) => {
  if (!isGuest && !userId) {
    console.error('❌ Not authenticated');
    return;
  }
  
  if (isGuest && !guestSession) {
    console.error('❌ No guest session - cannot send message');
    return;
  }
  
  const payload = isGuest ? {
    message_text: messageText,
    sender_type: 'guest',
    guest_session_id: guestSession.session_id, // ✅ From session data
    room_number: guestSession.room_number        // ✅ From session data
  } : {
    message_text: messageText,
    sender_type: 'staff',
    staff_id: userId
  };
  
  try {
    const response = await fetch(
      `/api/chat/${hotelSlug}/conversation/${conversationId}/messages/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    );
    
    if (response.ok) {
      console.log('✅ Message sent');
    }
  } catch (error) {
    console.error('❌ Failed to send message:', error);
  }
};
```

## Complete Flow

### Guest Chat Flow with Session Data

1. **Guest enters PIN** → 
2. **Frontend calls** `POST /validate-chat-pin/` with `{pin, fcm_token}` →
3. **Backend validates** and returns `session_data` →
4. **Frontend stores** session data in localStorage + state →
5. **Frontend navigates** to chat using `conversation_id` from session →
6. **ChatWindow loads** session from localStorage →
7. **Pusher subscribes** to channel from session data →
8. **Guest can send messages** using `session_id` and `room_number` →
9. **Guest receives messages** via Pusher on correct channel

## Debug Checklist

When debugging guest chat issues, verify:

- [ ] PIN validation returns `session_data` object
- [ ] `session_data` contains all required fields:
  - [ ] `session_id`
  - [ ] `room_number`
  - [ ] `hotel_slug`
  - [ ] `conversation_id`
  - [ ] `pusher_channel`
- [ ] Frontend stores session data after validation
- [ ] ChatWindow loads session data on mount
- [ ] Pusher channel name matches `session_data.pusher_channel`
- [ ] Message sending includes `guest_session_id` and `room_number`
- [ ] No console errors about missing `userId` or `guestSession`

## Console Output

### Backend (after PIN validation)
```
✅ Guest PIN validated for room 205, session ID: abc-123-def-456
```

### Frontend (after PIN validation)
```javascript
✅ Guest session established: {
  session_id: "abc-123-def-456",
  room_number: "205",
  hotel_slug: "hotel-killarney",
  conversation_id: "conv-uuid",
  guest_name: "John Doe",
  pusher_channel: "hotel-killarney-room-205-chat"
}
```

### Frontend (ChatWindow mount)
```javascript
🔍 Guest session loaded: {session_id: "...", room_number: "205", ...}
✅ Pusher subscribed to: hotel-killarney-room-205-chat
```

### Frontend (send message)
```javascript
✅ Message sent with session_id: abc-123-def-456, room: 205
```

## Error Messages You Should NOT See Anymore

- ❌ `Cannot send message: No userId or guestSession`
- ❌ `roomNumber: undefined`
- ❌ `guestPusherChannel: null`
- ❌ `willSubscribe: false`

## Testing

### Test PIN Validation Returns Session Data
```bash
curl -X POST http://localhost:8000/api/chat/hotel-killarney/room/205/validate-chat-pin/ \
  -H "Content-Type: application/json" \
  -d '{"pin": "1234", "fcm_token": "test_token_here"}'
```

Expected response:
```json
{
  "valid": true,
  "fcm_token_saved": true,
  "session_data": {
    "session_id": "...",
    "room_number": "205",
    ...
  }
}
```

## Related Files
- `chat/views.py` - Enhanced `validate_chat_pin` function (lines ~321-377)
- `chat/models.py` - `GuestChatSession` model
- Frontend: PIN validation component (needs update)
- Frontend: ChatWindow component (needs update)

## Summary
The backend now provides everything the frontend needs in a single PIN validation response. The frontend must store and use this `session_data` object for all guest chat operations.
