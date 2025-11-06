# Staff Chat Message Forwarding Guide

## Overview

The message forwarding feature allows staff members to share messages from one conversation to multiple other conversations. The system supports forwarding to both **existing conversations** and **new participants** (which creates new conversations automatically).

## Key Concepts

### Forwarding Flow

1. **Select Message**: User selects a message to forward from any conversation
2. **Choose Recipients**: User can select:
   - Existing conversations (from their conversation list)
   - New people (staff members not yet in their conversations)
3. **Send**: Message is sent to all selected targets
   - For existing conversations: Message is added directly
   - For new people: New 1-on-1 conversation is created, then message is sent

### Important Notes

- Forwarded messages do NOT preserve the reply chain (reply_to is set to null)
- Forwarded messages appear as new messages from the forwarding user
- Cannot forward deleted messages
- Must be a participant in the original conversation to forward
- Must be a participant in target conversations (for existing conversations)
- Cannot forward to yourself

---

## Backend API Endpoints

### 1. Get Conversations for Forwarding

**Endpoint**: `GET /api/staff-chat/<hotel_slug>/conversations/for-forwarding/`

**Purpose**: Retrieve a simplified list of conversations optimized for the forwarding UI.

**Authentication**: Required (IsAuthenticated)

**Query Parameters**:
- `search` (optional): Filter conversations by title or participant names

**Response**:
```json
{
  "count": 10,
  "conversations": [
    {
      "id": 1,
      "title": "John Doe",
      "is_group": false,
      "participants": [
        {
          "id": 5,
          "name": "John Doe",
          "profile_image_url": "https://..."
        }
      ],
      "participant_count": 2,
      "last_message": {
        "message": "Hello there!",
        "timestamp": "2025-11-06T10:30:00Z",
        "sender_name": "John Doe"
      },
      "updated_at": "2025-11-06T10:30:00Z"
    },
    {
      "id": 2,
      "title": "Management Team",
      "is_group": true,
      "participants": [
        {
          "id": 3,
          "name": "Jane Smith",
          "profile_image_url": "https://..."
        },
        {
          "id": 7,
          "name": "Mike Johnson",
          "profile_image_url": null
        }
      ],
      "participant_count": 4,
      "last_message": {
        "message": "Meeting at 3 PM",
        "timestamp": "2025-11-06T09:15:00Z",
        "sender_name": "Jane Smith"
      },
      "updated_at": "2025-11-06T09:15:00Z"
    }
  ]
}
```

**Features**:
- Returns only conversations where the user is a participant
- Conversations ordered by most recent activity (`updated_at`)
- Includes conversation type (1-on-1 vs group)
- Shows last message preview
- Participant information for UI display
- Search functionality for finding specific conversations

---

### 2. Forward Message

**Endpoint**: `POST /api/staff-chat/<hotel_slug>/messages/<message_id>/forward/`

**Purpose**: Forward a message to multiple conversations (existing or new).

**Authentication**: Required (IsAuthenticated, IsStaffMember, IsSameHotel)

**Request Body**:
```json
{
  "conversation_ids": [1, 2, 5],        // Optional: IDs of existing conversations
  "new_participant_ids": [10, 15, 20]   // Optional: IDs of staff to create new conversations with
}
```

**Validation Rules**:
- At least one of `conversation_ids` or `new_participant_ids` must be provided
- IDs in each array must be unique
- Cannot forward to deleted messages
- Must be participant in original conversation
- Must be participant in target conversations (for existing conversations)
- Cannot forward to yourself (in new_participant_ids)

**Success Response** (200 OK):
```json
{
  "success": true,
  "forwarded_to_existing": 3,
  "forwarded_to_new": 2,
  "total_forwarded": 5,
  "results": [
    {
      "conversation_id": 1,
      "message_id": 123,
      "created_conversation": false,
      "success": true
    },
    {
      "conversation_id": 2,
      "message_id": 124,
      "created_conversation": false,
      "success": true
    },
    {
      "conversation_id": 8,
      "message_id": 125,
      "created_conversation": true,
      "participant_id": 10,
      "success": true
    },
    {
      "conversation_id": 5,
      "error": "You are not a participant in this conversation",
      "created_conversation": false,
      "success": false
    }
  ]
}
```

**Error Responses**:

**400 Bad Request** - Validation errors:
```json
{
  "error": "Must provide at least one conversation_id or new_participant_id"
}
```

**403 Forbidden** - Permission denied:
```json
{
  "error": "You must be a participant in the conversation to forward messages"
}
```

**404 Not Found** - Message or staff not found:
```json
{
  "error": "Staff profile not found"
}
```

---

## Frontend Implementation Guide

### Step 1: Display Forward Button

In your message component, add a forward option:

```jsx
// MessageItem.jsx
const MessageItem = ({ message, onForward }) => {
  return (
    <div className="message">
      <p>{message.message}</p>
      <div className="message-actions">
        <button onClick={() => onForward(message)}>
          Forward
        </button>
      </div>
    </div>
  );
};
```

### Step 2: Load Conversations for Forwarding

When user clicks forward, fetch the conversation list:

```javascript
// api/staffChat.js
export const getConversationsForForwarding = async (hotelSlug, searchQuery = '') => {
  const url = `/api/staff-chat/${hotelSlug}/conversations/for-forwarding/`;
  const params = searchQuery ? `?search=${encodeURIComponent(searchQuery)}` : '';
  
  const response = await fetch(url + params, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to load conversations');
  }
  
  return await response.json();
};
```

### Step 3: Show Forward Modal

Create a modal that shows:
1. **Existing Conversations List** (from for-forwarding endpoint)
2. **Option to Add New People** (from staff-list endpoint)

```jsx
// ForwardMessageModal.jsx
const ForwardMessageModal = ({ message, hotelSlug, onClose, onComplete }) => {
  const [conversations, setConversations] = useState([]);
  const [selectedConversations, setSelectedConversations] = useState([]);
  const [showAddPeople, setShowAddPeople] = useState(false);
  const [selectedNewPeople, setSelectedNewPeople] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  
  useEffect(() => {
    loadConversations();
  }, [searchQuery]);
  
  const loadConversations = async () => {
    try {
      const data = await getConversationsForForwarding(hotelSlug, searchQuery);
      setConversations(data.conversations);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };
  
  const handleToggleConversation = (convId) => {
    setSelectedConversations(prev => 
      prev.includes(convId)
        ? prev.filter(id => id !== convId)
        : [...prev, convId]
    );
  };
  
  const handleTogglePerson = (staffId) => {
    setSelectedNewPeople(prev =>
      prev.includes(staffId)
        ? prev.filter(id => id !== staffId)
        : [...prev, staffId]
    );
  };
  
  const handleForward = async () => {
    if (selectedConversations.length === 0 && selectedNewPeople.length === 0) {
      alert('Please select at least one recipient');
      return;
    }
    
    try {
      const response = await forwardMessage(
        hotelSlug,
        message.id,
        selectedConversations,
        selectedNewPeople
      );
      
      console.log('Forward results:', response);
      
      // Show success message
      alert(`Message forwarded to ${response.total_forwarded} recipients`);
      onComplete(response);
      onClose();
    } catch (error) {
      console.error('Error forwarding message:', error);
      alert('Failed to forward message');
    }
  };
  
  return (
    <div className="modal">
      <div className="modal-header">
        <h2>Forward Message</h2>
        <button onClick={onClose}>×</button>
      </div>
      
      <div className="modal-body">
        {/* Search */}
        <input
          type="text"
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        
        {/* Existing Conversations */}
        <section>
          <h3>Your Conversations</h3>
          <div className="conversation-list">
            {conversations.map(conv => (
              <div
                key={conv.id}
                className={`conversation-item ${
                  selectedConversations.includes(conv.id) ? 'selected' : ''
                }`}
                onClick={() => handleToggleConversation(conv.id)}
              >
                <div className="conversation-info">
                  <strong>{conv.title}</strong>
                  {conv.last_message && (
                    <p className="last-message">
                      {conv.last_message.message}
                    </p>
                  )}
                </div>
                <input
                  type="checkbox"
                  checked={selectedConversations.includes(conv.id)}
                  onChange={() => handleToggleConversation(conv.id)}
                />
              </div>
            ))}
          </div>
        </section>
        
        {/* Add New People */}
        <section>
          <button onClick={() => setShowAddPeople(!showAddPeople)}>
            {showAddPeople ? 'Hide' : 'Add'} New People
          </button>
          
          {showAddPeople && (
            <StaffSelector
              hotelSlug={hotelSlug}
              selectedStaffIds={selectedNewPeople}
              onToggleStaff={handleTogglePerson}
            />
          )}
        </section>
        
        {/* Selection Summary */}
        <div className="selection-summary">
          <p>
            Selected: {selectedConversations.length} conversation(s), 
            {selectedNewPeople.length} new person/people
          </p>
        </div>
      </div>
      
      <div className="modal-footer">
        <button onClick={onClose}>Cancel</button>
        <button
          onClick={handleForward}
          disabled={selectedConversations.length === 0 && selectedNewPeople.length === 0}
        >
          Forward
        </button>
      </div>
    </div>
  );
};
```

### Step 4: Forward API Call

```javascript
// api/staffChat.js
export const forwardMessage = async (
  hotelSlug,
  messageId,
  conversationIds = [],
  newParticipantIds = []
) => {
  const response = await fetch(
    `/api/staff-chat/${hotelSlug}/messages/${messageId}/forward/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        conversation_ids: conversationIds,
        new_participant_ids: newParticipantIds
      })
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to forward message');
  }
  
  return await response.json();
};
```

### Step 5: Handle Results

```javascript
const handleForwardComplete = (results) => {
  // Check for failures
  const failures = results.results.filter(r => !r.success);
  
  if (failures.length > 0) {
    console.warn('Some forwards failed:', failures);
    // Show warning to user
  }
  
  // Update UI - maybe navigate to one of the conversations
  const firstSuccess = results.results.find(r => r.success);
  if (firstSuccess) {
    // Navigate to conversation or refresh conversation list
    navigateToConversation(firstSuccess.conversation_id);
  }
};
```

---

## User Experience Flow

### Scenario 1: Forward to Existing Conversations

1. User opens a conversation with John
2. User long-presses a message and selects "Forward"
3. Modal opens showing all their conversations
4. User selects "Management Team" and "Kitchen Staff" conversations
5. User clicks "Forward"
6. Message is sent to both conversations
7. Success message: "Message forwarded to 2 recipients"

### Scenario 2: Forward to New Person

1. User opens a conversation
2. User selects "Forward" on a message
3. Modal opens
4. User clicks "Add New People"
5. Staff list appears (similar to creating new conversation)
6. User selects "Sarah (Housekeeping)"
7. User clicks "Forward"
8. New conversation with Sarah is created
9. Message is sent to the new conversation
10. Success message: "Message forwarded to 1 recipient"

### Scenario 3: Forward to Multiple Mixed Recipients

1. User selects "Forward" on a message
2. Modal opens
3. User selects 2 existing conversations
4. User clicks "Add New People"
5. User selects 3 new staff members
6. User clicks "Forward"
7. System:
   - Sends to 2 existing conversations
   - Creates 3 new conversations with selected staff
   - Sends message to all 3 new conversations
8. Success message: "Message forwarded to 5 recipients"

---

## Real-time Updates

When a message is forwarded:
1. **Pusher broadcasts** the new message to all participants in each target conversation
2. **FCM notifications** are sent to participants (except the sender)
3. Conversation's `updated_at` timestamp is updated
4. Conversation's `has_unread` flag is set to true

Recipients will see the forwarded message as a new message in their conversation.

---

## Testing Checklist

### Backend Tests
- [ ] Can forward to single existing conversation
- [ ] Can forward to multiple existing conversations
- [ ] Can forward to new participant (creates conversation)
- [ ] Can forward to multiple new participants
- [ ] Can forward to mixed (existing + new)
- [ ] Cannot forward deleted message
- [ ] Cannot forward if not participant in original conversation
- [ ] Cannot forward to conversation where not participant
- [ ] Cannot forward to self
- [ ] Validation errors returned correctly
- [ ] Pusher broadcasts work
- [ ] FCM notifications sent

### Frontend Tests
- [ ] Forward button appears on messages
- [ ] Modal loads conversations correctly
- [ ] Search filters conversations
- [ ] Can select/deselect conversations
- [ ] Can add new people
- [ ] Shows correct selection count
- [ ] Forward button disabled when nothing selected
- [ ] Success message displays
- [ ] Error handling works
- [ ] Real-time updates received

---

## Database Schema Impact

### StaffConversation
- No schema changes required
- Uses existing `get_or_create_conversation` method

### StaffChatMessage
- Forwarded messages have:
  - `sender`: The user who forwarded
  - `message`: Copy of original message text
  - `reply_to`: null (not preserved)
  - `conversation`: Target conversation ID

### No New Tables Required

---

## Security Considerations

1. **Authorization**: Only participants can forward from conversations
2. **Validation**: All conversation and staff IDs validated against hotel
3. **Active Staff Only**: Only active staff members can receive forwards
4. **Same Hotel**: All operations scoped to single hotel
5. **Deleted Messages**: Cannot forward deleted messages
6. **Self-Forwarding**: Prevented in new_participant_ids

---

## Performance Considerations

1. **Bulk Operations**: Forwards to multiple targets processed sequentially
2. **Transaction Safety**: Each forward wrapped in try-catch
3. **Partial Success**: Returns detailed results even if some forwards fail
4. **Conversation Lookup**: Uses `get_or_create_conversation` to avoid duplicates
5. **Real-time**: Pusher broadcasts happen per conversation (not batched)

---

## Error Handling

The API returns partial success - some forwards may succeed while others fail:

```json
{
  "success": true,
  "total_forwarded": 3,
  "results": [
    { "conversation_id": 1, "message_id": 123, "success": true },
    { "conversation_id": 5, "error": "Not a participant", "success": false },
    { "conversation_id": 9, "message_id": 124, "success": true }
  ]
}
```

Frontend should:
1. Show overall success count
2. Warn user about failures
3. Allow retry for failed forwards

---

## Future Enhancements

Potential improvements:
- Forward with comment/caption
- Preserve attachments when forwarding
- Forward multiple messages at once
- Forward to external channels (email, SMS)
- Forward history tracking
- Undo forwarding within time window
