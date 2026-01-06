# Staff Room Conversations API Guide

**Date**: January 6, 2026  
**Purpose**: Guide for retrieving all conversations between rooms and front office staff  

## Overview

This guide explains how to access all guest-to-staff conversations from the staff side using the existing chat system APIs. The system tracks conversations between hotel guests in rooms and front office staff.

## Main API Endpoints

### 1. Get All Active Conversations (Primary)

```http
GET /api/staff/hotels/{hotel_slug}/chat/conversations/
```

**Description**: Retrieves all conversations (rooms with messages) for a hotel

**Authentication**: Staff authentication required

**Response**: List of conversations ordered by most recent activity

**Features**:
- Returns conversations that include guest-to-staff messages from rooms
- Includes staff responses to guests  
- Provides room information and message counts
- Shows conversation metadata and read status

**Example**:
```http
GET /api/staff/hotels/hotel-killarney/chat/conversations/
```

### 2. Get Messages in Specific Conversation

```http
GET /api/staff/hotels/{hotel_slug}/chat/conversations/{conversation_id}/messages/
```

**Description**: Retrieves all messages in a specific room conversation

**Query Parameters**:
- `limit`: Number of messages to load (default: 10)
- `before_id`: Load messages older than this ID (for pagination)

**Example**:
```http
GET /api/staff/hotels/hotel-killarney/chat/conversations/55/messages/?limit=50
GET /api/staff/hotels/hotel-killarney/chat/conversations/55/messages/?before_id=120&limit=20
```

## Data Models

### Conversation Model
- **room**: Links to a specific Room
- **participants_staff**: Staff members involved in conversation
- **has_unread**: Boolean indicating unread messages
- **messages**: Related RoomMessage records
- **created_at/updated_at**: Timestamps

### RoomMessage Model
- **conversation**: Links to parent Conversation
- **room**: Room where message originated
- **booking**: Associated booking (for guest messages)
- **sender_type**: `"guest"`, `"staff"`, or `"system"`
- **staff**: Staff member (for staff messages)
- **message**: Message content
- **timestamp**: When message was sent
- **read_by_staff/read_by_guest**: Read status tracking

## Implementation Examples

### Python Service Example

```python
from chat.models import Conversation, RoomMessage
from hotel.models import Hotel

def get_all_room_conversations(hotel_slug, staff_user):
    """
    Get all conversations between rooms and front office for a hotel
    """
    hotel = Hotel.objects.get(slug=hotel_slug)
    
    # Get all conversations for rooms in this hotel
    # Note: Remove 'room__guests' as it doesn't exist - guests are linked differently
    conversations = Conversation.objects.filter(
        room__hotel=hotel
    ).select_related('room').prefetch_related('messages').order_by('-updated_at')
    
    return conversations

def get_conversation_with_messages(conversation_id):
    """
    Get a specific conversation with all its messages
    """
    conversation = Conversation.objects.get(id=conversation_id)
    messages = conversation.messages.select_related(
        'staff', 'booking'
    ).order_by('timestamp')
    
    return conversation, messages
```

### Frontend API Call Example

```javascript
// Get all conversations
const response = await fetch('/api/staff/hotels/hotel-killarney/chat/conversations/', {
    headers: {
        'Authorization': `Bearer ${staffToken}`,
        'Content-Type': 'application/json'
    }
});
const conversations = await response.json();

// Get messages for a specific conversation
const messagesResponse = await fetch('/api/staff/hotels/hotel-killarney/chat/conversations/55/messages/?limit=50', {
    headers: {
        'Authorization': `Bearer ${staffToken}`,
        'Content-Type': 'application/json'
    }
});
const messages = await messagesResponse.json();
```

## Related Systems

### Staff-to-Staff Chat (Separate System)
There's a separate staff chat system for internal staff communications:

```http
GET /api/staff/hotels/{hotel_slug}/staff-chat/conversations/
```

**Note**: This is for staff-to-staff internal chat, NOT guest-to-staff room communications.

## File Locations

- **Main Chat Views**: `chat/views.py`
- **Chat Models**: `chat/models.py`
- **Chat URLs**: `chat/urls.py`
- **Staff Chat Views**: `staff_chat/views.py` (separate system)

## Key Functions in Codebase

### chat/views.py
- `get_active_conversations()`: Main endpoint for retrieving all conversations
- `get_conversation_messages()`: Get messages in specific conversation
- `send_conversation_message()`: Send staff replies

### Models
- `Conversation`: Links rooms to message threads
- `RoomMessage`: Individual messages in conversations
- `GuestConversationParticipant`: Tracks staff participation

## Authentication & Permissions

- **Staff Authentication Required**: All endpoints require valid staff token
- **Hotel Scope**: Conversations are scoped to specific hotel via `hotel_slug`
- **Room Access**: Staff can access conversations for rooms in their hotel

## Usage Notes

1. **Primary Endpoint**: Use `/api/staff/hotels/{hotel_slug}/chat/conversations/` to get all room conversations
2. **Not Staff Chat**: Don't confuse with `/api/staff/hotels/{hotel_slug}/staff-chat/` endpoints (internal staff communications)
3. **Pagination**: Use `limit` and `before_id` for message pagination
4. **Real-time**: System supports Pusher for real-time message updates
5. **Read Status**: Track read/unread status for both staff and guests

## Correct URL Structure

**✅Troubleshooting

### Common Issues

#### 1. AttributeError: Cannot find 'guests' on Room object
**Problem**: The Room model doesn't have a direct `guests` relationship.

**Solution**: Remove `'room__guests'` from prefetch_related() calls. Guests are related through bookings:
```python
# ✅ Correct
conversations = Conversation.objects.filter(room__hotel=hotel).prefetch_related('messages')

# ❌ Incorrect  
conversations = Conversation.objects.filter(room__hotel=hotel).prefetch_related('room__guests', 'messages')
```

#### 2. Duplicate Hotel Slug in URL
**Problem**: URL contains hotel slug twice: `/api/staff/hotel/hotel-killarney/chat/hotel-killarney/conversations/`

**Solution**: Use the correct URL format: `/api/staff/hotels/{hotel_slug}/chat/conversations/`

#### 3. 404 Not Found
**Problem**: Using incorrect URL structure without staff wrapper.

**Solution**: Ensure you're using the staff API endpoints with proper authentication.

##  Correct**: `/api/staff/hotels/{hotel_slug}/chat/conversations/`  
**❌ Incorrect**: `/api/chat/{hotel_slug}/conversations/`  

All chat endpoints are wrapped under the staff API structure and require staff authentication.