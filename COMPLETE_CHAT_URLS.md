# Complete Chat System URLs

## Guest Chat URLs (Token-Based Authentication)

### Get Guest Chat Context
```
GET /api/public/chat/{hotel_slug}/guest/chat/context/?token={guest_token}
```

**Example**:
```
GET /api/public/chat/hotel-killarney/guest/chat/context/?token=abc123def456
```

### Send Guest Message
```
POST /api/public/chat/{hotel_slug}/guest/chat/messages/?token={guest_token}
```

**Example**:
```
POST /api/public/chat/hotel-killarney/guest/chat/messages/?token=abc123def456
```

**Body**:
```json
{
  "message": "Hello staff, I need help with my room",
  "reply_to": 123
}
```

## Staff Chat URLs (Staff Authentication Required)

### Get All Conversations
```
GET /api/chat/{hotel_slug}/conversations/
```

**Example**:
```
GET /api/chat/hotel-killarney/conversations/
```

### Get Messages in Conversation
```
GET /api/chat/{hotel_slug}/conversations/{conversation_id}/messages/
```

**Query Parameters**: `limit`, `before_id` (for pagination)

**Example**:
```
GET /api/chat/hotel-killarney/conversations/55/messages/?limit=50
GET /api/chat/hotel-killarney/conversations/55/messages/?before_id=120&limit=20
```

### Send Staff Message
```
POST /api/chat/{hotel_slug}/conversations/{conversation_id}/messages/send/
```

**Example**:
```
POST /api/chat/hotel-killarney/conversations/55/messages/send/
```

**Body**:
```json
{
  "message": "Hello guest, how can I help you?",
  "reply_to": 124
}
```

## Complete URL Structure

### Development URLs
```
# Guest endpoints (public API)
http://localhost:8000/api/public/chat/{hotel_slug}/guest/chat/context/?token={token}
http://localhost:8000/api/public/chat/{hotel_slug}/guest/chat/messages/?token={token}

# Staff endpoints (authenticated API)
http://localhost:8000/api/chat/{hotel_slug}/conversations/
http://localhost:8000/api/chat/{hotel_slug}/conversations/{id}/messages/
http://localhost:8000/api/chat/{hotel_slug}/conversations/{id}/messages/send/
```

### Production URLs
```
# Guest endpoints (public API)
https://yourdomain.com/api/public/chat/{hotel_slug}/guest/chat/context/?token={token}
https://yourdomain.com/api/public/chat/{hotel_slug}/guest/chat/messages/?token={token}

# Staff endpoints (authenticated API)  
https://yourdomain.com/api/chat/{hotel_slug}/conversations/
https://yourdomain.com/api/chat/{hotel_slug}/conversations/{id}/messages/
https://yourdomain.com/api/chat/{hotel_slug}/conversations/{id}/messages/send/
```

## Copy-Paste URL Templates

### For Guest Chat Frontend
```javascript
// Base URLs for guest chat
const GUEST_CHAT_BASE = `/api/public/chat/${hotelSlug}/guest/chat`;
const CONTEXT_URL = `${GUEST_CHAT_BASE}/context/?token=${guestToken}`;
const SEND_MESSAGE_URL = `${GUEST_CHAT_BASE}/messages/?token=${guestToken}`;
```

### For Staff Chat Frontend
```javascript
// Base URLs for staff chat
const STAFF_CHAT_BASE = `/api/chat/${hotelSlug}`;
const CONVERSATIONS_URL = `${STAFF_CHAT_BASE}/conversations/`;
const MESSAGES_URL = `${STAFF_CHAT_BASE}/conversations/${conversationId}/messages/`;
const SEND_MESSAGE_URL = `${STAFF_CHAT_BASE}/conversations/${conversationId}/messages/send/`;
```

## Pusher Channel Names

### Guest Chat Channels (Booking-Scoped)
```
private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}
```

**Examples**:
```
private-hotel-hotel-killarney-guest-chat-booking-BK-2025-0123
private-hotel-dublin-central-guest-chat-booking-BK-2025-0456
```

### Real-time Event Name
```
realtime_event
```

## HTTP Methods & Headers

### Guest Requests
```
GET  /api/public/chat/{hotel_slug}/guest/chat/context/?token={token}
POST /api/public/chat/{hotel_slug}/guest/chat/messages/?token={token}

Headers:
Content-Type: application/json
```

### Staff Requests
```
GET  /api/chat/{hotel_slug}/conversations/
GET  /api/chat/{hotel_slug}/conversations/{id}/messages/
POST /api/chat/{hotel_slug}/conversations/{id}/messages/send/

Headers:
Content-Type: application/json
Authorization: Bearer {staff_token}
```

## Complete Chat Flow URLs

### Guest Initiates Chat
1. **Get Context**: `GET /api/public/chat/{hotel_slug}/guest/chat/context/?token={token}`
2. **Subscribe to Pusher**: Use channel from context response
3. **Send Messages**: `POST /api/public/chat/{hotel_slug}/guest/chat/messages/?token={token}`

### Staff Responds to Guest
1. **Get Conversations**: `GET /api/chat/{hotel_slug}/conversations/`
2. **Get Messages**: `GET /api/chat/{hotel_slug}/conversations/{id}/messages/`
3. **Send Reply**: `POST /api/chat/{hotel_slug}/conversations/{id}/messages/send/`

## Error Response URLs

All endpoints return standard HTTP status codes:
- `200` - Success
- `201` - Created (for new messages)
- `400` - Bad Request (invalid data)
- `401` - Unauthorized (missing/invalid auth)
- `403` - Forbidden (not checked in)
- `404` - Not Found (invalid token/hotel)
- `409` - Conflict (no room assigned)

## Quick Reference

| Action | Method | URL Pattern |
|--------|--------|-------------|
| Guest get context | GET | `/api/public/chat/{hotel}/guest/chat/context/?token={}` |
| Guest send message | POST | `/api/public/chat/{hotel}/guest/chat/messages/?token={}` |
| Staff get conversations | GET | `/api/chat/{hotel}/conversations/` |
| Staff get messages | GET | `/api/chat/{hotel}/conversations/{id}/messages/` |
| Staff send message | POST | `/api/chat/{hotel}/conversations/{id}/messages/send/` |

**Note**: Guest endpoints are in `/api/public/` (no staff auth required), Staff endpoints are in `/api/` (staff auth required).