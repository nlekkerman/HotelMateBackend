# Staff Chat Forwarding - Quick Reference

## API Endpoints

### 1. Get Conversations for Forwarding
```
GET /api/staff-chat/<hotel_slug>/conversations/for-forwarding/
```
Optional query param: `?search=query`

Returns simplified list of user's conversations for selection UI.

### 2. Forward Message
```
POST /api/staff-chat/<hotel_slug>/messages/<message_id>/forward/
```

**Body:**
```json
{
  "conversation_ids": [1, 2, 3],      // Optional
  "new_participant_ids": [10, 15]     // Optional
}
```

**Response:**
```json
{
  "success": true,
  "forwarded_to_existing": 3,
  "forwarded_to_new": 2,
  "total_forwarded": 5,
  "results": [...]
}
```

## Frontend Flow

1. **Show Forward Button** on message
2. **Click Forward** → Open modal
3. **Load Conversations** from `/for-forwarding/` endpoint
4. **Select Recipients**:
   - Check existing conversations
   - OR click "Add New People" to select staff
5. **Click Forward** → POST to `/forward/` endpoint
6. **Handle Response** → Show success/errors

## Key Features

✅ Forward to multiple conversations at once
✅ Forward to new people (auto-creates conversation)
✅ Search/filter conversations
✅ Shows last message preview
✅ Partial success handling (some may fail)
✅ Real-time updates via Pusher
✅ FCM notifications sent

## Validation Rules

- ❌ Cannot forward deleted messages
- ❌ Must be participant in original conversation
- ❌ Must be participant in target conversations
- ❌ Cannot forward to yourself
- ✅ At least one recipient required
- ✅ Duplicate IDs automatically filtered

## Code Snippets

### Load Conversations
```javascript
const conversations = await fetch(
  `/api/staff-chat/${hotelSlug}/conversations/for-forwarding/`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);
```

### Forward Message
```javascript
const result = await fetch(
  `/api/staff-chat/${hotelSlug}/messages/${messageId}/forward/`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      conversation_ids: [1, 2],
      new_participant_ids: [5]
    })
  }
);
```

## Database Changes

**None required** - Uses existing models and methods.

## Testing URLs

```bash
# Get conversations for forwarding
GET http://localhost:8000/api/staff-chat/my-hotel/conversations/for-forwarding/

# Forward message ID 123
POST http://localhost:8000/api/staff-chat/my-hotel/messages/123/forward/
Body: {"conversation_ids": [1, 2], "new_participant_ids": [5]}
```

## See Full Documentation

For detailed implementation guide, see:
`docs/STAFF_CHAT_FORWARD_MESSAGE_GUIDE.md`
