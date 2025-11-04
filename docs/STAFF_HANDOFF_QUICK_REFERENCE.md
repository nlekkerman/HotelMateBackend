# Staff Conversation Handoff - Quick Reference

## Backend Endpoints Summary

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/chat/{hotel_slug}/conversations/{conversation_id}/assign-staff/` | POST | Staff | Assign staff to conversation when they click/open it |
| `/chat/{hotel_slug}/conversations/{conversation_id}/messages/send/` | POST | Any | Send message (auto-assigns staff if sender is staff) |

---

## Frontend Integration - Quick Steps

### 1️⃣ Staff Opens Conversation
```javascript
// When staff clicks conversation in sidebar
async function openConversation(conversationId) {
  // Step 1: Assign current staff as handler
  await fetch(`/chat/${hotelSlug}/conversations/${conversationId}/assign-staff/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${staffToken}` }
  });
  
  // Step 2: Load and display messages
  loadMessages(conversationId);
}
```

### 2️⃣ Guest Listens for Staff Changes
```javascript
// In guest chat initialization
pusher.subscribe(`${hotelSlug}-room-${roomNumber}-chat`)
  .bind('staff-assigned', (data) => {
    // Update header: "Chatting with John Smith - Receptionist"
    updateChatHeader(data.staff_name, data.staff_role);
  });
```

### 3️⃣ Display Staff Info in Messages
```javascript
// Each staff message includes staff_info
{
  "id": 123,
  "message": "Hello! How can I help?",
  "sender_type": "staff",
  "staff_info": {
    "name": "John Smith",
    "role": "Receptionist",
    "profile_image": "https://..."
  }
}
```

---

## Pusher Events Reference

### Event: `staff-assigned`
**Channel:** `{hotel_slug}-room-{room_number}-chat` (Guest channel)

**Triggered When:**
- Staff clicks/opens conversation
- Staff sends a message

**Payload:**
```json
{
  "staff_name": "John Smith",
  "staff_role": "Receptionist",
  "conversation_id": 123
}
```

**Frontend Action:**
- Update chat header with staff name
- Show "Staff X is now assisting you" message
- Update message sender display

---

## Real-World Scenarios

### Scenario 1: Shift Change
```
8:00 AM - Sarah (Day Shift) opens conversation → Assigned to Sarah
3:00 PM - Mike (Night Shift) opens same conversation → Assigned to Mike
Guest sees: "Mike - Night Receptionist is now assisting you"
```

### Scenario 2: Coverage During Lunch
```
John handling Room 101
John goes to lunch → Marks conversation unread
Emma clicks Room 101 → Emma now assigned
Guest sees: "Emma - Receptionist is now assisting you"
```

### Scenario 3: Multiple Receptionists
```
3 receptionists on duty:
- Guest sends message → All 3 see notification
- Sarah clicks first → Sarah assigned
- Sarah's name appears in guest's chat
- John/Mike can still view but know Sarah is handling it
```

---

## UI/UX Recommendations

### Staff Dashboard
```
┌─────────────────────────────────────┐
│ Room 101 - John Doe                 │
│ ├─ Last: "Thank you!"               │
│ ├─ 2 min ago                        │
│ └─ 🔵 Handled by: Sarah Jones      │ ← Show handler
└─────────────────────────────────────┘
```

### Guest Chat Header
```
┌─────────────────────────────────────┐
│  👤 Sarah Jones                     │
│     Receptionist                    │
│     🟢 Online                       │
└─────────────────────────────────────┘
```

### Handoff Notification (Staff)
```
ℹ️ Mike Thompson is now handling this conversation
```

---

## API Response Examples

### Assign Staff Response
```json
{
  "conversation_id": 123,
  "assigned_staff": {
    "name": "John Smith",
    "role": "Receptionist",
    "profile_image": "https://example.com/john.jpg"
  },
  "sessions_updated": 1,
  "room_number": 101
}
```

### Message with Staff Info
```json
{
  "id": 456,
  "conversation": 123,
  "room": 101,
  "room_number": 101,
  "sender_type": "staff",
  "staff": 5,
  "staff_name": "John Smith",
  "staff_display_name": "John Smith",
  "staff_role_name": "Receptionist",
  "staff_info": {
    "name": "John Smith",
    "role": "Receptionist",
    "profile_image": "https://example.com/john.jpg"
  },
  "message": "Hello! How can I help you today?",
  "timestamp": "2025-11-04T14:30:00Z",
  "status": "delivered"
}
```

---

## Testing Commands

### Test Staff Assignment
```bash
# As Staff User
curl -X POST \
  "http://localhost:8000/chat/hotel-abc/conversations/123/assign-staff/" \
  -H "Authorization: Bearer YOUR_STAFF_TOKEN"
```

### Test Message Send (Auto-Assignment)
```bash
# As Staff User
curl -X POST \
  "http://localhost:8000/chat/hotel-abc/conversations/123/messages/send/" \
  -H "Authorization: Bearer YOUR_STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from staff"}'
```

---

## Common Issues & Solutions

### Issue: Guest doesn't see staff name
**Solution:** Ensure frontend is listening to `staff-assigned` Pusher event

### Issue: Multiple staff seeing same unread badge
**Solution:** This is correct! All staff can see guest messages. Badge clears when ANY staff reads it.

### Issue: Staff name shows as "Hotel Staff"
**Solution:** Check that staff profile has `first_name` and `last_name` filled

### Issue: Old staff name persists after handoff
**Solution:** Verify Pusher connection and `staff-assigned` event handler

---

## State Management Tips

### React State Structure
```javascript
const [conversationState, setConversationState] = useState({
  conversationId: null,
  messages: [],
  assignedStaff: null,    // Current handler
  isLoading: false
});

// Update on staff-assigned event
useEffect(() => {
  channel.bind('staff-assigned', (data) => {
    setConversationState(prev => ({
      ...prev,
      assignedStaff: {
        name: data.staff_name,
        role: data.staff_role
      }
    }));
  });
}, []);
```

### Vue.js State Structure
```javascript
data() {
  return {
    conversation: {
      id: null,
      messages: [],
      currentStaff: null
    }
  }
},
mounted() {
  this.channel.bind('staff-assigned', (data) => {
    this.conversation.currentStaff = {
      name: data.staff_name,
      role: data.staff_role
    };
  });
}
```

---

## Performance Considerations

1. **Debounce Assignment Calls**: Only call when user actually opens/focuses conversation
2. **Cache Staff Info**: Store staff profile images locally
3. **Lazy Load Messages**: Load messages after staff assignment completes
4. **Batch Updates**: Group multiple state updates together

---

## Security Notes

- ✅ Only authenticated staff can assign themselves
- ✅ Staff can only assign to conversations in their hotel
- ✅ Guests cannot trigger staff assignment
- ✅ Assignment endpoint validates hotel ownership

---

## Migration Notes

If you have existing conversations without staff handlers:

1. Old conversations will work normally
2. First staff to open/reply gets assigned automatically
3. No database migration needed
4. `current_staff_handler` defaults to `null`

---

## Support Matrix

| Feature | Supported | Notes |
|---------|-----------|-------|
| Multiple staff assignments | ✅ | Last one wins |
| Guest sees staff name | ✅ | Via Pusher event |
| Staff sees who's handling | ✅ | Via API response |
| Handoff during active chat | ✅ | Real-time update |
| Assignment persistence | ✅ | Stored in database |
| Mobile support | ✅ | Same API/events |

---

## Next Steps

1. ✅ Backend implementation complete
2. 📱 Implement frontend staff assignment call
3. 📱 Add Pusher listener for `staff-assigned`
4. 🎨 Design handoff UI/notifications
5. 🧪 Test multi-staff scenarios
6. 📊 Monitor assignment patterns
