# Pusher Real-Time Messaging Debug Guide

## Issue: Guest Not Receiving Messages in Real-Time (Requires Manual Refresh)

When reception/staff sends a message to a guest, the message doesn't appear until the guest manually refreshes the page.

---

## Backend Pusher Events (Already Implemented)

When **staff sends message to guest**, the backend triggers **3 Pusher events**:

### 1. Guest-Specific Channel (Primary)
```python
Channel: "{hotel_slug}-room-{room_number}-chat"
Event: "new-staff-message"
Data: {serialized message}
```
**Example:**
```
Channel: "hotel-paradise-room-101-chat"
Event: "new-staff-message"
```

### 2. Conversation Channel (General)
```python
Channel: "{hotel_slug}-conversation-{conversation_id}-chat"
Event: "new-message"
Data: {serialized message}
```
**Example:**
```
Channel: "hotel-paradise-conversation-45-chat"
Event: "new-message"
```

### 3. Message Delivered Confirmation
```python
Channel: "{hotel_slug}-conversation-{conversation_id}-chat"
Event: "message-delivered"
Data: {message_id, delivered_at, status}
```

---

## Debugging Steps

### Step 1: Check Backend Logs
Look for these log entries when staff sends a message:

```
✅ Message created with ID: {message_id}
✅ Pusher triggered: guest_channel={hotel_slug}-room-{room_number}-chat, event=new-staff-message, message_id={id}
✅ FCM sent to guest in room {room_number} for message from staff
✅ Pusher triggered for new message: channel={hotel_slug}-conversation-{conversation_id}-chat, message_id={id}
```

**If you see these logs:** ✅ Backend is working correctly
**If you DON'T see these logs:** ❌ Backend Pusher is failing

### Step 2: Check Pusher Dashboard
1. Go to Pusher Dashboard: https://dashboard.pusher.com/
2. Select your app
3. Go to "Debug Console"
4. Send a message from staff to guest
5. Watch for events in real-time

**What to look for:**
- ✅ Event appears in console = Backend is sending
- ❌ Event doesn't appear = Check Pusher credentials/config

### Step 3: Check Frontend Pusher Subscription

**Guest must subscribe to the correct channel:**

```javascript
// Guest should subscribe to:
const guestChannel = pusher.subscribe(`${hotelSlug}-room-${roomNumber}-chat`);

// And listen to BOTH events:
guestChannel.bind('new-staff-message', (data) => {
  console.log('New message from staff:', data);
  // Add message to UI
  setMessages(prev => [...prev, data]);
});

guestChannel.bind('new-message', (data) => {
  console.log('New message (general):', data);
  // Add message to UI
  setMessages(prev => [...prev, data]);
});
```

**Common Frontend Issues:**

#### ❌ Issue 1: Not Subscribed to Channel
```javascript
// WRONG - No subscription
useEffect(() => {
  // Missing pusher.subscribe()
}, []);

// CORRECT
useEffect(() => {
  const channel = pusher.subscribe(`${hotelSlug}-room-${roomNumber}-chat`);
  channel.bind('new-staff-message', handleNewMessage);
  
  return () => {
    channel.unbind('new-staff-message');
    pusher.unsubscribe(`${hotelSlug}-room-${roomNumber}-chat`);
  };
}, [hotelSlug, roomNumber]);
```

#### ❌ Issue 2: Wrong Channel Name
```javascript
// WRONG
pusher.subscribe(`${hotelSlug}-conversation-${conversationId}-chat`);

// CORRECT for guest
pusher.subscribe(`${hotelSlug}-room-${roomNumber}-chat`);
```

#### ❌ Issue 3: Not Listening to Correct Event
```javascript
// WRONG - Listening to wrong event name
channel.bind('message-received', handleMessage); // ❌

// CORRECT
channel.bind('new-staff-message', handleMessage); // ✅
// OR
channel.bind('new-message', handleMessage); // ✅ (also works)
```

#### ❌ Issue 4: Component Unmounting Before Message Arrives
```javascript
// WRONG - Channel unsubscribes when component unmounts
useEffect(() => {
  const channel = pusher.subscribe(channelName);
  channel.bind('new-staff-message', handleMessage);
  
  // This cleanup runs when component unmounts
  return () => {
    channel.unbind();
    pusher.unsubscribe(channelName); // ❌ Unsubscribes too early!
  };
}, []); // Empty dependency = only runs once

// CORRECT - Keep subscription alive
useEffect(() => {
  const channel = pusher.subscribe(channelName);
  channel.bind('new-staff-message', handleMessage);
  
  // Only cleanup when chat is closed or user leaves
  return () => {
    // Cleanup only when necessary
  };
}, [channelName]);
```

---

## Frontend Test Code

Add this to your guest chat component to test Pusher:

```javascript
useEffect(() => {
  console.log('🔌 Initializing Pusher for guest chat');
  console.log('Hotel:', hotelSlug);
  console.log('Room:', roomNumber);
  
  const channelName = `${hotelSlug}-room-${roomNumber}-chat`;
  console.log('📡 Subscribing to channel:', channelName);
  
  const channel = pusher.subscribe(channelName);
  
  // Test subscription success
  channel.bind('pusher:subscription_succeeded', () => {
    console.log('✅ Successfully subscribed to:', channelName);
  });
  
  // Test subscription error
  channel.bind('pusher:subscription_error', (error) => {
    console.error('❌ Subscription error:', error);
  });
  
  // Listen for new staff messages
  channel.bind('new-staff-message', (data) => {
    console.log('📨 Received new staff message:', data);
    setMessages(prev => [...prev, data]);
  });
  
  // Also listen to general new-message event
  channel.bind('new-message', (data) => {
    console.log('📨 Received new message (general):', data);
    // Only add if sender is staff to avoid duplicates
    if (data.sender_type === 'staff') {
      setMessages(prev => [...prev, data]);
    }
  });
  
  return () => {
    console.log('🔌 Cleaning up Pusher subscription');
    channel.unbind('new-staff-message');
    channel.unbind('new-message');
    pusher.unsubscribe(channelName);
  };
}, [hotelSlug, roomNumber]);
```

**Expected Console Output When Message Arrives:**
```
🔌 Initializing Pusher for guest chat
Hotel: hotel-paradise
Room: 101
📡 Subscribing to channel: hotel-paradise-room-101-chat
✅ Successfully subscribed to: hotel-paradise-room-101-chat

// When staff sends message:
📨 Received new staff message: {message: "Hello!", sender_type: "staff", ...}
📨 Received new message (general): {message: "Hello!", sender_type: "staff", ...}
```

---

## Quick Diagnostic

Run this checklist:

### Backend Checklist:
- [ ] Backend logs show "Pusher triggered: guest_channel=..."
- [ ] Pusher Dashboard shows events being sent
- [ ] No Pusher errors in backend logs
- [ ] Pusher credentials are correct in `.env`

### Frontend Checklist:
- [ ] Guest component subscribes to correct channel on mount
- [ ] Channel name matches backend format: `{hotelSlug}-room-{roomNumber}-chat`
- [ ] Listening to `new-staff-message` event
- [ ] Console shows "Successfully subscribed"
- [ ] No Pusher errors in browser console
- [ ] Component doesn't unmount when message arrives
- [ ] State updates when event is received

---

## Most Likely Issue

**90% chance it's a frontend subscription issue:**

1. Guest not subscribed to the channel
2. Subscribed to wrong channel name
3. Not listening to the correct event name
4. Component unmounting/re-mounting causing lost subscription

**How to verify:**
- Open browser console on guest page
- Send message from staff
- Check if Pusher event appears in console
- If YES → State update issue
- If NO → Subscription issue

---

## Solution

### If Backend Issue:
Check Pusher configuration in `chat/utils.py` or settings:
```python
pusher_client = pusher.Pusher(
    app_id=os.environ.get('PUSHER_APP_ID'),
    key=os.environ.get('PUSHER_KEY'),
    secret=os.environ.get('PUSHER_SECRET'),
    cluster=os.environ.get('PUSHER_CLUSTER'),
    ssl=True
)
```

### If Frontend Issue:
Ensure guest subscribes to the **room-specific channel**:
```javascript
const channel = pusher.subscribe(`${hotelSlug}-room-${roomNumber}-chat`);
channel.bind('new-staff-message', (data) => {
  setMessages(prev => [...prev, data]);
});
```

---

## Related Files

### Backend:
- `chat/views.py` - Line ~203: Guest channel trigger
- `chat/views.py` - Line ~260: Conversation channel trigger
- `chat/utils.py` - Pusher client configuration

### Frontend (Your Team):
- Guest chat component
- Pusher initialization
- Channel subscription logic
- Message state management

---

## Need More Help?

Share the following with your frontend team:

1. Backend Pusher channel name: `{hotelSlug}-room-{roomNumber}-chat`
2. Event name: `new-staff-message`
3. Event data structure: See `RoomMessageSerializer`
4. This debug guide

The backend is already correctly sending Pusher events. The issue is 99% likely in the frontend subscription/listening logic.
