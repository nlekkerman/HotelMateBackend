# Staff Chat - Conversation Management API

## Create a New Conversation

### Endpoint
```
POST /api/staff_chat/{hotel_slug}/conversations/
```

### Headers
```
Authorization: Bearer <your_token>
Content-Type: application/json
```

### Request Body

**For 1-on-1 Chat:**
```json
{
  "participant_ids": [5]
}
```

**For Group Chat:**
```json
{
  "participant_ids": [5, 8, 12],
  "title": "Housekeeping Team"
}
```

### Response (201 Created)
```json
{
  "id": 1,
  "hotel": {
    "id": 2,
    "name": "Grand Hotel",
    "slug": "hotel-killarney"
  },
  "title": "Housekeeping Team",
  "is_group": true,
  "participants": [
    {
      "id": 3,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@hotel.com",
      "department": "Housekeeping",
      "role": "Manager"
    },
    {
      "id": 5,
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane@hotel.com",
      "department": "Housekeeping",
      "role": "Staff"
    }
  ],
  "last_message": null,
  "unread_count": 0,
  "created_at": "2025-11-05T13:45:00Z",
  "updated_at": "2025-11-05T13:45:00Z"
}
```

### Notes:
- **participant_ids**: Array of staff member IDs to include in the conversation
- **title**: Optional for group chats (3+ participants), leave empty for 1-on-1
- The current user (you) is automatically added as a participant
- For 1-on-1 chats: If a conversation already exists between you and the other person, it returns the existing conversation (200 OK) instead of creating a duplicate

---

## List All Conversations

### Endpoint
```
GET /api/staff_chat/{hotel_slug}/conversations/
```

### Headers
```
Authorization: Bearer <your_token>
```

### Response (200 OK)
```json
[
  {
    "id": 1,
    "hotel": {
      "id": 2,
      "name": "Grand Hotel",
      "slug": "hotel-killarney"
    },
    "title": "",
    "is_group": false,
    "participants": [
      {
        "id": 3,
        "first_name": "John",
        "last_name": "Doe"
      },
      {
        "id": 5,
        "first_name": "Jane",
        "last_name": "Smith"
      }
    ],
    "last_message": {
      "id": 42,
      "message": "See you tomorrow!",
      "sender": {
        "id": 5,
        "first_name": "Jane",
        "last_name": "Smith"
      },
      "timestamp": "2025-11-05T12:30:00Z"
    },
    "unread_count": 2,
    "created_at": "2025-11-04T10:00:00Z",
    "updated_at": "2025-11-05T12:30:00Z"
  }
]
```

---

## Get Conversation Details

### Endpoint
```
GET /api/staff_chat/{hotel_slug}/conversations/{conversation_id}/
```

### Headers
```
Authorization: Bearer <your_token>
```

### Response (200 OK)
```json
{
  "id": 1,
  "hotel": {
    "id": 2,
    "name": "Grand Hotel",
    "slug": "hotel-killarney"
  },
  "title": "Housekeeping Team",
  "is_group": true,
  "participants": [
    {
      "id": 3,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@hotel.com",
      "profile_image": "https://...",
      "department": "Housekeeping",
      "role": "Manager"
    }
  ],
  "messages": [
    {
      "id": 42,
      "sender": {
        "id": 3,
        "first_name": "John",
        "last_name": "Doe"
      },
      "message": "Hello team!",
      "timestamp": "2025-11-05T13:45:00Z",
      "is_read": false,
      "is_edited": false,
      "is_deleted": false,
      "reactions": []
    }
  ],
  "created_at": "2025-11-05T13:45:00Z",
  "updated_at": "2025-11-05T13:45:00Z"
}
```

---

## Get Staff List (for selecting participants)

### Endpoint
```
GET /api/staff_chat/{hotel_slug}/staff-list/
```

### Headers
```
Authorization: Bearer <your_token>
```

### Query Parameters
- `search` - Search by name, email, department, role
- `ordering` - Sort by `first_name`, `last_name`, `department__name`

### Example
```
GET /api/staff_chat/hotel-killarney/staff-list/?search=house
```

### Response (200 OK)
```json
[
  {
    "id": 5,
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@hotel.com",
    "profile_image": "https://...",
    "department": {
      "id": 2,
      "name": "Housekeeping"
    },
    "role": {
      "id": 3,
      "name": "Staff"
    },
    "is_active": true
  }
]
```

---

## Quick Start Example

### 1. Get Staff List
```javascript
fetch('/api/staff_chat/hotel-killarney/staff-list/', {
  headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
})
.then(res => res.json())
.then(staff => console.log(staff));
```

### 2. Create 1-on-1 Conversation
```javascript
fetch('/api/staff_chat/hotel-killarney/conversations/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    participant_ids: [5]  // Jane's ID
  })
})
.then(res => res.json())
.then(conversation => {
  console.log('Conversation created:', conversation.id);
  // Now you can send messages!
});
```

### 3. Create Group Conversation
```javascript
fetch('/api/staff_chat/hotel-killarney/conversations/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    participant_ids: [5, 8, 12],
    title: "Morning Shift Team"
  })
})
.then(res => res.json())
.then(conversation => {
  console.log('Group created:', conversation.id);
});
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "At least one participant is required"
}
```
```json
{
  "error": "Some participants are invalid or inactive"
}
```

### 403 Forbidden
```json
{
  "error": "You can only create conversations in your hotel"
}
```

### 404 Not Found
```json
{
  "error": "Staff profile not found"
}
```

---

## Next Steps

Once you have a conversation:
1. **Send messages** - See `STAFF_CHAT_MESSAGING_GUIDE.md`
2. **Upload files** - See attachment endpoints
3. **Add reactions** - React to messages with emojis
4. **Listen to Pusher** - Get real-time updates

**Related Documentation:**
- Full messaging guide: `/docs/STAFF_CHAT_MESSAGING_GUIDE.md`
- Implementation summary: `/docs/STAFF_CHAT_IMPLEMENTATION_SUMMARY.md`
