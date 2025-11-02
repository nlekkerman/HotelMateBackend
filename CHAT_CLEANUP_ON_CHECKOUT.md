# 🧹 Chat Cleanup on Room Checkout

## Overview
When a room is checked out, all chat-related data is automatically cleaned up to ensure guest privacy and prevent data leakage between different guest stays.

---

## ✅ What Gets Deleted on Checkout

### 1. **Guest Chat Sessions** 🆕
- All `GuestChatSession` records for the room
- Invalidates any session tokens stored in guest's browser
- Removes staff handler assignments
- Clears session metadata (IP, user agent, etc.)

### 2. **Conversations**
- All `Conversation` records linked to the room
- Removes participant associations

### 3. **Messages**
- All `RoomMessage` records (cascade deleted with Conversation)
- Includes message text, timestamps, read receipts
- Removes staff display names and role information

### 4. **Guest Information**
- All `Guest` records linked to the room
- Clears many-to-many relationships

### 5. **Room Service Data**
- All pending `Order` records for that room
- All `BreakfastOrder` records for that room

### 6. **Room Status**
- Sets `is_occupied = False`
- Generates new `guest_id_pin` (invalidates old QR codes)

---

## 🔒 Privacy & Security

### Session Token Invalidation
When checkout happens:
1. ✅ `GuestChatSession` records are **deleted** from database
2. ✅ Guest's localStorage still has token, but it becomes **invalid**
3. ✅ Next time guest tries to access chat, backend returns `404` or `expired`
4. ✅ Frontend should handle this by showing PIN entry again
5. ✅ New guest gets **new PIN** and **new session token**

### Pusher Channels
- Old Pusher channel: `{hotel-slug}-room-{room-number}-chat` still exists
- But new guest won't know the old messages (deleted from DB)
- New conversation will have **new conversation_id**
- New Pusher events go to same channel name but **different conversation**

---

## 🔧 Implementation Details

### Backend Code (rooms/views.py)

```python
with transaction.atomic():
    for room in rooms:
        # 1. Remove guest associations
        room.guests.clear()
        Guest.objects.filter(room=room).delete()

        # 2. Delete guest chat sessions (NEW)
        from chat.models import GuestChatSession
        GuestChatSession.objects.filter(room=room).delete()

        # 3. Delete conversations and messages
        Conversation.objects.filter(room=room).delete()
        RoomMessage.objects.filter(room=room).delete()

        # 4. Reset room
        room.is_occupied = False
        room.generate_guest_pin()  # New PIN generated

        # 5. Delete orders
        Order.objects.filter(hotel=room.hotel, room_number=room.room_number).delete()
        BreakfastOrder.objects.filter(hotel=room.hotel, room_number=room.room_number).delete()

        room.save()
```

---

## 📱 Frontend Handling

### What Frontend Should Do

1. **On Session Validation Failure**:
```javascript
async function validateSession() {
  try {
    const response = await fetch(`/api/chat/guest-session/${token}/validate/`);
    
    if (!response.ok) {
      // Session invalid (room checked out)
      localStorage.removeItem('hotelmate_guest_chat_session');
      showPinEntry(); // Ask for PIN again
      return;
    }
    
    // Session valid, continue
  } catch (error) {
    // Handle error
  }
}
```

2. **Show Appropriate Message**:
```javascript
if (validationError.reason === 'not_found') {
  alert('This session has expired. The room may have been checked out.');
} else if (validationError.reason === 'expired') {
  alert('Session expired after 7 days.');
}
```

---

## 🧪 Testing Checkout Cleanup

### Test Steps:

1. **Setup**:
   - Check in guest to Room 102
   - Create chat session via QR code
   - Send messages between guest and staff

2. **Verify Data Exists**:
```python
from chat.models import GuestChatSession, Conversation, RoomMessage
from rooms.models import Room

room = Room.objects.get(room_number=102)
sessions = GuestChatSession.objects.filter(room=room)
conversations = Conversation.objects.filter(room=room)
messages = RoomMessage.objects.filter(room=room)

print(f"Sessions: {sessions.count()}")
print(f"Conversations: {conversations.count()}")
print(f"Messages: {messages.count()}")
```

3. **Checkout Room**:
```bash
POST /api/rooms/{hotel-slug}/checkout/
{
  "room_ids": [102]
}
```

4. **Verify Data Deleted**:
```python
# Should all return 0
sessions = GuestChatSession.objects.filter(room=room)
conversations = Conversation.objects.filter(room=room)
messages = RoomMessage.objects.filter(room=room)

print(f"Sessions after checkout: {sessions.count()}")  # 0
print(f"Conversations after checkout: {conversations.count()}")  # 0
print(f"Messages after checkout: {messages.count()}")  # 0
```

5. **Verify Room Reset**:
```python
room.refresh_from_db()
print(f"Is occupied: {room.is_occupied}")  # False
print(f"New PIN: {room.guest_id_pin}")  # Different from before
```

---

## ⚠️ Important Notes

### Database Cascade
- `RoomMessage` has FK to `Conversation` with `on_delete=CASCADE`
- When `Conversation` is deleted, all its messages auto-delete
- Explicit delete of `RoomMessage` ensures cleanup even if FK changes

### Session Expiration
Sessions can become invalid in 2 ways:
1. **Checkout**: Session deleted immediately
2. **Time**: Session expires after 7 days (natural expiration)

### Multi-Device Sessions
- One guest can have **multiple sessions** from different devices
- **All sessions deleted** on checkout
- All devices will fail validation after checkout

---

## 🎯 Summary

✅ **Checkout automatically deletes**:
- Guest chat sessions
- Conversations
- Messages
- Guest records
- Orders
- Regenerates PIN

✅ **Frontend handles gracefully**:
- Validates session on load
- Shows PIN entry if invalid
- Clears localStorage on error

✅ **Privacy protected**:
- No data leakage between guests
- Old tokens become invalid
- New PIN for new guest

This ensures **complete privacy** and **clean state** for each new guest! 🔒
