# Frontend Implementation: Multi-Staff Conversation Handoff

## Overview
This document provides complete implementation instructions for supporting multiple staff members handling guest conversations, with seamless handoff between staff members.

---

## API Endpoints

### 1. Assign Staff to Conversation (New)
**Endpoint:** `POST /chat/{hotel_slug}/conversations/{conversation_id}/assign-staff/`

**Authentication:** Required (Staff only)

**When to Call:**
- When staff clicks/opens a conversation from the sidebar
- Before loading conversation messages
- When staff "claims" a conversation

**Request:**
```javascript
const response = await fetch(
  `${API_BASE_URL}/chat/${hotelSlug}/conversations/${conversationId}/assign-staff/`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${staffToken}`,
      'Content-Type': 'application/json'
    }
  }
);
```

**Response:** `200 OK`
```json
{
  "conversation_id": 123,
  "assigned_staff": {
    "name": "John Smith",
    "role": "Receptionist",
    "profile_image": "https://example.com/images/john.jpg"
  },
  "sessions_updated": 1,
  "room_number": 101
}
```

**Error Responses:**
- `403 Forbidden` - Not authenticated as staff
- `400 Bad Request` - Conversation doesn't belong to this hotel
- `404 Not Found` - Conversation not found

---

## Staff Dashboard Implementation

### Step 1: Update Conversation Click Handler

**Current Flow:**
```javascript
// OLD - Just open conversation
function handleConversationClick(conversationId) {
  loadConversationMessages(conversationId);
}
```

**New Flow:**
```javascript
// NEW - Assign staff first, then load
async function handleConversationClick(conversationId, hotelSlug) {
  try {
    // 1. Assign current staff as handler
    const assignResponse = await assignStaffToConversation(conversationId, hotelSlug);
    
    // 2. Update UI with assigned staff info
    console.log(`Assigned: ${assignResponse.assigned_staff.name}`);
    
    // 3. Load conversation messages
    await loadConversationMessages(conversationId);
    
    // 4. Update header or sidebar to show staff is handling this
    updateConversationHeader(assignResponse.assigned_staff);
    
  } catch (error) {
    console.error('Failed to assign staff:', error);
    // Fallback: still load messages even if assignment fails
    loadConversationMessages(conversationId);
  }
}

// Helper function
async function assignStaffToConversation(conversationId, hotelSlug) {
  const response = await fetch(
    `${API_BASE_URL}/chat/${hotelSlug}/conversations/${conversationId}/assign-staff/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getStaffToken()}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to assign staff: ${response.status}`);
  }
  
  return await response.json();
}
```

### Step 2: Display Staff Handler in Sidebar (Optional)

Add visual indicator showing which staff is handling each conversation:

```javascript
function renderConversationItem(conversation) {
  return `
    <div class="conversation-item" onclick="handleConversationClick(${conversation.conversation_id}, '${hotelSlug}')">
      <div class="room-info">
        <span class="room-number">Room ${conversation.room_number}</span>
        ${conversation.guest_name ? `<span class="guest-name">${conversation.guest_name}</span>` : ''}
      </div>
      
      ${conversation.has_unread ? '<span class="unread-badge"></span>' : ''}
      
      <!-- NEW: Show who's handling -->
      ${conversation.current_handler ? `
        <div class="handler-info">
          <small>Handled by: ${conversation.current_handler.name}</small>
        </div>
      ` : ''}
      
      <div class="last-message">
        <span class="timestamp">${formatTime(conversation.last_message_time)}</span>
        <p>${conversation.last_message}</p>
      </div>
    </div>
  `;
}
```

### Step 3: React to Staff Changes (Real-time)

If another staff member takes over a conversation you're viewing, show a notification:

```javascript
// Subscribe to conversation channel
const conversationChannel = pusher.subscribe(
  `${hotelSlug}-conversation-${conversationId}-chat`
);

// Listen for staff assignment changes
conversationChannel.bind('staff-assigned', (data) => {
  const currentStaffId = getCurrentStaffId();
  const assignedStaffName = data.staff_name;
  
  // Check if someone else took over
  if (!isCurrentStaffAssigned(data)) {
    showNotification(
      `${assignedStaffName} is now handling this conversation`,
      'info'
    );
    
    // Optional: Update UI to show it's no longer "yours"
    updateConversationOwnership(false);
  }
});

function isCurrentStaffAssigned(assignmentData) {
  const currentStaffName = localStorage.getItem('staff_name');
  return assignmentData.staff_name === currentStaffName;
}
```

---

## Guest Chat Implementation

### Step 1: Listen for Staff Assignment Events

Guests should know who they're chatting with:

```javascript
// In guest chat component initialization
function initializeGuestChat(hotelSlug, roomNumber, sessionToken) {
  // ... existing initialization ...
  
  const guestChannel = pusher.subscribe(
    `${hotelSlug}-room-${roomNumber}-chat`
  );
  
  // NEW: Listen for staff assignments
  guestChannel.bind('staff-assigned', (data) => {
    updateChatHeader(data.staff_name, data.staff_role);
    
    // Optional: Show message in chat
    addSystemMessage(
      `${data.staff_name} (${data.staff_role}) is now assisting you`
    );
  });
}
```

### Step 2: Update Chat Header

Display current staff handler in the chat window:

```javascript
function updateChatHeader(staffName, staffRole) {
  const headerElement = document.getElementById('chat-header');
  
  headerElement.innerHTML = `
    <div class="chat-header-content">
      <div class="staff-avatar">
        <i class="icon-person"></i>
      </div>
      <div class="staff-info">
        <h3>${staffName || 'Hotel Staff'}</h3>
        <span class="staff-role">${staffRole || 'Receptionist'}</span>
      </div>
      <div class="online-indicator">
        <span class="status-dot online"></span>
        <span>Online</span>
      </div>
    </div>
  `;
}
```

**React Example:**
```jsx
function GuestChatHeader({ staffName, staffRole }) {
  return (
    <div className="chat-header">
      <div className="staff-avatar">
        <PersonIcon />
      </div>
      <div className="staff-info">
        <h3>{staffName || 'Hotel Staff'}</h3>
        <span className="staff-role">{staffRole || 'Receptionist'}</span>
      </div>
      <div className="online-indicator">
        <span className="status-dot online" />
        <span>Online</span>
      </div>
    </div>
  );
}

// In parent component
const [currentStaff, setCurrentStaff] = useState({ 
  name: null, 
  role: null 
});

useEffect(() => {
  const channel = pusher.subscribe(`${hotelSlug}-room-${roomNumber}-chat`);
  
  channel.bind('staff-assigned', (data) => {
    setCurrentStaff({
      name: data.staff_name,
      role: data.staff_role
    });
  });
  
  return () => channel.unbind('staff-assigned');
}, [hotelSlug, roomNumber]);
```

### Step 3: Display Staff Info in Messages

Show which staff member sent each message:

```javascript
function renderStaffMessage(message) {
  const staffInfo = message.staff_info || {};
  
  return `
    <div class="message staff-message">
      <div class="message-header">
        <img 
          src="${staffInfo.profile_image || '/default-avatar.png'}" 
          alt="${staffInfo.name}"
          class="staff-avatar-small"
        />
        <span class="staff-name">${staffInfo.name || 'Hotel Staff'}</span>
        <span class="staff-role">${staffInfo.role || ''}</span>
      </div>
      <div class="message-content">
        ${message.message}
      </div>
      <div class="message-time">
        ${formatTime(message.timestamp)}
      </div>
    </div>
  `;
}
```

---

## Complete Example: Staff Conversation View

### Vanilla JavaScript Implementation

```javascript
class StaffConversationManager {
  constructor(hotelSlug, pusher) {
    this.hotelSlug = hotelSlug;
    this.pusher = pusher;
    this.currentConversationId = null;
    this.currentStaffInfo = this.getStaffInfo();
  }
  
  getStaffInfo() {
    return {
      id: localStorage.getItem('staff_id'),
      name: localStorage.getItem('staff_name'),
      token: localStorage.getItem('staff_token')
    };
  }
  
  async openConversation(conversationId) {
    try {
      // 1. Close current conversation if any
      if (this.currentConversationId) {
        this.closeConversation();
      }
      
      this.currentConversationId = conversationId;
      
      // 2. Assign current staff as handler
      const assignment = await this.assignStaffToConversation(conversationId);
      console.log('✅ Assigned to:', assignment.assigned_staff.name);
      
      // 3. Load messages
      const messages = await this.loadMessages(conversationId);
      
      // 4. Render conversation
      this.renderConversation(messages, assignment);
      
      // 5. Setup real-time listeners
      this.setupPusherListeners(conversationId);
      
      // 6. Mark as read
      await this.markConversationRead(conversationId);
      
    } catch (error) {
      console.error('Failed to open conversation:', error);
      this.showError('Unable to load conversation');
    }
  }
  
  async assignStaffToConversation(conversationId) {
    const response = await fetch(
      `${API_BASE_URL}/chat/${this.hotelSlug}/conversations/${conversationId}/assign-staff/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.currentStaffInfo.token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (!response.ok) {
      throw new Error('Assignment failed');
    }
    
    return await response.json();
  }
  
  async loadMessages(conversationId) {
    const response = await fetch(
      `${API_BASE_URL}/chat/${this.hotelSlug}/conversations/${conversationId}/messages/`,
      {
        headers: {
          'Authorization': `Bearer ${this.currentStaffInfo.token}`
        }
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to load messages');
    }
    
    return await response.json();
  }
  
  setupPusherListeners(conversationId) {
    const channel = this.pusher.subscribe(
      `${this.hotelSlug}-conversation-${conversationId}-chat`
    );
    
    // New messages
    channel.bind('new-message', (data) => {
      this.appendMessage(data);
    });
    
    // Staff changes
    channel.bind('staff-assigned', (data) => {
      if (data.staff_name !== this.currentStaffInfo.name) {
        this.showTakeoverNotification(data.staff_name);
      }
    });
    
    // Guest read receipts
    channel.bind('messages-read-by-guest', (data) => {
      this.updateReadReceipts(data.message_ids);
    });
  }
  
  showTakeoverNotification(staffName) {
    // Show subtle notification that another staff took over
    const notification = document.createElement('div');
    notification.className = 'takeover-notification';
    notification.innerHTML = `
      <i class="icon-info"></i>
      <span>${staffName} is now handling this conversation</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 5000);
  }
  
  async sendMessage(messageText) {
    const response = await fetch(
      `${API_BASE_URL}/chat/${this.hotelSlug}/conversations/${this.currentConversationId}/messages/send/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.currentStaffInfo.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: messageText })
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    
    const result = await response.json();
    
    // Auto-assignment happens on backend when staff sends message
    console.log('Message sent, still assigned to:', result.staff_info?.name);
    
    return result;
  }
  
  closeConversation() {
    if (this.currentConversationId) {
      const channel = this.pusher.channel(
        `${this.hotelSlug}-conversation-${this.currentConversationId}-chat`
      );
      
      if (channel) {
        channel.unbind_all();
        this.pusher.unsubscribe(channel.name);
      }
      
      this.currentConversationId = null;
    }
  }
}

// Usage
const staffManager = new StaffConversationManager(hotelSlug, pusher);

// When staff clicks on a conversation
document.querySelectorAll('.conversation-item').forEach(item => {
  item.addEventListener('click', () => {
    const conversationId = item.dataset.conversationId;
    staffManager.openConversation(conversationId);
  });
});
```

---

## React Implementation Example

```jsx
import { useState, useEffect, useCallback } from 'react';
import Pusher from 'pusher-js';

function StaffConversationView({ hotelSlug, conversationId, staffToken }) {
  const [messages, setMessages] = useState([]);
  const [assignedStaff, setAssignedStaff] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [handoffNotification, setHandoffNotification] = useState(null);
  
  // Assign staff on conversation open
  const assignStaffToConversation = useCallback(async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/chat/${hotelSlug}/conversations/${conversationId}/assign-staff/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${staffToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setAssignedStaff(data.assigned_staff);
        console.log('✅ Assigned:', data.assigned_staff.name);
      }
    } catch (error) {
      console.error('Failed to assign staff:', error);
    }
  }, [hotelSlug, conversationId, staffToken]);
  
  // Load messages
  const loadMessages = useCallback(async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/chat/${hotelSlug}/conversations/${conversationId}/messages/`,
        {
          headers: { 'Authorization': `Bearer ${staffToken}` }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setMessages(data);
      }
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setIsLoading(false);
    }
  }, [hotelSlug, conversationId, staffToken]);
  
  // Initialize conversation
  useEffect(() => {
    const initConversation = async () => {
      setIsLoading(true);
      await assignStaffToConversation();
      await loadMessages();
    };
    
    initConversation();
  }, [assignStaffToConversation, loadMessages]);
  
  // Setup Pusher listeners
  useEffect(() => {
    const pusher = new Pusher(process.env.REACT_APP_PUSHER_KEY, {
      cluster: process.env.REACT_APP_PUSHER_CLUSTER
    });
    
    const channel = pusher.subscribe(
      `${hotelSlug}-conversation-${conversationId}-chat`
    );
    
    // New messages
    channel.bind('new-message', (data) => {
      setMessages(prev => [...prev, data]);
    });
    
    // Staff handoff
    channel.bind('staff-assigned', (data) => {
      const currentStaffName = localStorage.getItem('staff_name');
      
      if (data.staff_name !== currentStaffName) {
        setHandoffNotification({
          staffName: data.staff_name,
          staffRole: data.staff_role
        });
        
        // Clear notification after 5 seconds
        setTimeout(() => setHandoffNotification(null), 5000);
      }
      
      setAssignedStaff({
        name: data.staff_name,
        role: data.staff_role
      });
    });
    
    // Cleanup
    return () => {
      channel.unbind_all();
      pusher.unsubscribe(`${hotelSlug}-conversation-${conversationId}-chat`);
      pusher.disconnect();
    };
  }, [hotelSlug, conversationId]);
  
  const sendMessage = async (messageText) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL}/chat/${hotelSlug}/conversations/${conversationId}/messages/send/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${staffToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ message: messageText })
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        // Message will appear via Pusher event
        console.log('Message sent');
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };
  
  if (isLoading) {
    return <div>Loading conversation...</div>;
  }
  
  return (
    <div className="conversation-view">
      {/* Handoff notification */}
      {handoffNotification && (
        <div className="handoff-notification">
          <span>
            {handoffNotification.staffName} ({handoffNotification.staffRole}) 
            is now handling this conversation
          </span>
        </div>
      )}
      
      {/* Header showing assigned staff */}
      <div className="conversation-header">
        <h3>Room Conversation</h3>
        {assignedStaff && (
          <div className="assigned-staff-badge">
            Handled by: {assignedStaff.name}
          </div>
        )}
      </div>
      
      {/* Messages */}
      <div className="messages-container">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </div>
      
      {/* Input */}
      <MessageInput onSend={sendMessage} />
    </div>
  );
}

export default StaffConversationView;
```

---

## Testing Checklist

### Staff Side Testing

- [ ] **Single Staff Assignment**
  - Click on conversation → Staff is assigned
  - Send message → Still assigned
  - Refresh page → Assignment persists

- [ ] **Multi-Staff Handoff**
  - Staff A opens conversation → Staff A assigned
  - Staff B opens same conversation → Staff B now assigned
  - Staff A sees notification about handoff
  - Guest sees updated staff name

- [ ] **Message Send Assignment**
  - Staff A assigned to Conversation 1
  - Staff B sends message to Conversation 1
  - Staff B is now assigned automatically

### Guest Side Testing

- [ ] **Initial Connection**
  - Guest enters chat → No staff assigned yet
  - Shows "Hotel Staff" or generic name

- [ ] **Staff Assignment Display**
  - Staff member replies → Guest sees staff name
  - Staff name appears in chat header
  - Staff name shows with each message

- [ ] **Staff Handoff**
  - Staff A handling guest
  - Staff B takes over
  - Guest sees system message: "Staff B is now assisting you"
  - Header updates with new staff name

---

## CSS Styling Examples

```css
/* Handoff notification */
.handoff-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #2196F3;
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  animation: slideIn 0.3s ease;
  z-index: 1000;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Assigned staff badge */
.assigned-staff-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: #E3F2FD;
  color: #1976D2;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* Staff info in message */
.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.staff-avatar-small {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}

.staff-name {
  font-weight: 600;
  color: #1976D2;
}

.staff-role {
  font-size: 12px;
  color: #666;
}
```

---

## Error Handling

```javascript
async function assignStaffToConversation(conversationId, hotelSlug) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/chat/${hotelSlug}/conversations/${conversationId}/assign-staff/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getStaffToken()}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 403:
          console.error('Not authenticated as staff');
          redirectToLogin();
          break;
          
        case 400:
          console.error('Invalid conversation:', error.error);
          showError('Cannot access this conversation');
          break;
          
        case 404:
          console.error('Conversation not found');
          showError('Conversation no longer exists');
          break;
          
        default:
          throw new Error(`Unexpected error: ${response.status}`);
      }
      
      return null;
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('Network error:', error);
    showError('Connection failed. Please try again.');
    return null;
  }
}
```

---

## Summary

### Key Points for Frontend:

1. **Always call `/assign-staff/` when staff opens a conversation**
2. **Listen to `staff-assigned` Pusher event on guest side**
3. **Display staff name dynamically in chat UI**
4. **Show handoff notifications when staff changes**
5. **Auto-assignment also happens when staff sends messages**

### API Calls Sequence:

```
Staff Opens Conversation:
1. POST /assign-staff/ → Assigns staff
2. GET /messages/ → Load messages
3. POST /mark-read/ → Mark as read
4. [Pusher] Listen for new messages

Staff Sends Message:
1. POST /messages/send/ → Send message (auto-assigns sender)
2. [Pusher] Message delivered to guest
3. [Pusher] staff-assigned event to guest

Guest Receives:
1. [Pusher] new-staff-message event
2. [Pusher] staff-assigned event
3. Update UI with staff info
```

This implementation ensures smooth conversation handoff between multiple reception staff members! 🎯
