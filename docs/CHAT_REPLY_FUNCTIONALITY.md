# Chat Reply Functionality - Frontend Implementation Guide

## Overview

This guide explains how to implement message reply functionality in the chat system. The backend already supports replying to messages through the `reply_to` field in the `RoomMessage` model.

**✅ Works for both:**
- **Staff replying to guest messages**
- **Guests replying to staff messages**

The implementation is identical for both user types - the backend automatically handles sender identification.

---

## 🚨 Quick Debug: Seeing `reply_to: null` for all messages?

**This is normal if:**
- ✅ You haven't sent any replies yet (existing messages won't have replies)
- ✅ The feature is new and old messages don't have reply data

**⚠️ IMPORTANT - Backend Fix Applied:**
The backend has been updated to properly handle the `reply_to` field. If you sent test replies **before this fix**, they won't have reply data. You need to send **new** replies after this update.

**To test the functionality:**
1. Click "Reply" button on any message
2. Type a response and send it
3. The **new message** should have `reply_to: <message_id>` and show the reply preview
4. Check browser Network tab → POST request should include `"reply_to": 624` in payload

**If new replies still show `null`**, see [Troubleshooting section](#-troubleshooting) below.

---

## � What to Look For in Browser DevTools

Open **Network tab** and look for the POST request when sending a reply:

**Without Reply (Regular Message):**
```
POST /api/chat/hotel-killarney/conversation/48/send/
Request Payload:
{
  "message": "Hello"
}

Response:
{
  "message": {
    "id": 644,
    "reply_to": null,          ← No reply
    "reply_to_message": null   ← No reply
  }
}
```

**With Reply:**
```
POST /api/chat/hotel-killarney/conversation/48/send/
Request Payload:
{
  "message": "Thank you!",
  "reply_to": 643              ← Reply to message 643
}

Response:
{
  "message": {
    "id": 645,
    "reply_to": 643,            ← Has reply!
    "reply_to_message": {       ← Has reply data!
      "id": 643,
      "message": "Can I help you?",
      "sender_type": "staff"
    }
  }
}
```

---

## �📤 Sending a Reply to Backend

### API Endpoint

**POST** `/api/chat/<hotel_slug>/conversation/<conversation_id>/send/`

### Request Payload

```json
{
  "message": "This is my reply text",
  "reply_to": 123  // ID of the message being replied to (optional)
}
```

### Example JavaScript/TypeScript

```javascript
const sendReply = async (originalMessageId, replyText, conversationId, hotelSlug) => {
  try {
    const response = await fetch(
      `/api/chat/${hotelSlug}/conversation/${conversationId}/send/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: replyText,
          reply_to: originalMessageId  // Link to original message
        })
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to send reply');
    }
    
    const data = await response.json();
    console.log('Reply sent successfully:', data.message);
    return data;
    
  } catch (error) {
    console.error('Error sending reply:', error);
    throw error;
  }
};
```

### Example with Axios

```javascript
import axios from 'axios';

const sendReply = async (originalMessageId, replyText, conversationId, hotelSlug) => {
  try {
    const response = await axios.post(
      `/api/chat/${hotelSlug}/conversation/${conversationId}/send/`,
      {
        message: replyText,
        reply_to: originalMessageId
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Error sending reply:', error);
    throw error;
  }
};
```

---

## � Usage Examples for Both User Types

### Guest Replying to Staff Message

```javascript
// Guest clicks reply on a staff message
const originalStaffMessage = {
  id: 100,
  message: "We'll send extra towels to your room right away!",
  sender_type: "staff",
  staff_info: {
    name: "John Smith",
    role: "Receptionist"
  }
};

// Guest sends reply
await sendReply(100, "Thank you so much!", conversationId, hotelSlug);
```

### Staff Replying to Guest Message

```javascript
// Staff clicks reply on a guest message
const originalGuestMessage = {
  id: 99,
  message: "Can I get extra towels?",
  sender_type: "guest"
};

// Staff sends reply
await sendReply(99, "We'll send extra towels to your room right away!", conversationId, hotelSlug);
```

**Both use the same API endpoint and same payload format!**

### Visual Flow

```
📱 Guest Side                           💼 Staff Side
─────────────                           ─────────────

[Guest Message #99]                     [Guest Message #99]
"Can I get extra towels?"      ←────→   "Can I get extra towels?"
                                                ↓
                                        [Staff clicks Reply]
                                                ↓
                                        [Reply Bar appears]
                                        Replying to: "Can I get..."
                                                ↓
[Staff Message #100]            ←────→  [Staff types & sends]
  ↳ Reply to #99                        reply_to: 99
  "We'll send them right away!"

        ↓
[Guest clicks Reply]
        ↓
[Reply Bar appears]
Replying to: "We'll send..."
        ↓
[Guest Message #101]            ────→   [Guest Message #101]
  ↳ Reply to #100                         ↳ Reply to #100
  "Thank you!"                            "Thank you!"
```

---

## � Message Structure from Backend

When you fetch messages, each message with a reply will include `reply_to_message` data:

```json
{
  "id": 456,
  "message": "Yes, I can help you with that!",
  "sender_type": "staff",
  "staff_info": {
    "name": "John Smith",
    "role": "Receptionist",
    "profile_image": "https://..."
  },
  "timestamp": "2025-11-04T14:30:00Z",
  "reply_to": 123,
  "reply_to_message": {
    "id": 123,
    "message": "Can you send me extra towels?",
    "sender_type": "guest",
    "sender_name": "Guest",
    "timestamp": "2025-11-04T14:25:00Z"
  },
  "attachments": [],
  "has_attachments": false,
  "is_edited": false,
  "is_deleted": false,
  "read_by_staff": true,
  "read_by_guest": false
}
```

### Key Fields

- **`reply_to`**: ID of the original message (null if not a reply)
- **`reply_to_message`**: Object containing preview data of the original message
  - Only included if the original message still exists and is not deleted
  - Contains: `id`, `message` (truncated to 100 chars), `sender_type`, `sender_name`, `timestamp`

### Example: Staff Reply to Guest Message

```json
{
  "id": 456,
  "message": "Yes, I'll send them right away!",
  "sender_type": "staff",
  "staff_info": {
    "name": "John Smith",
    "role": "Receptionist"
  },
  "reply_to": 123,
  "reply_to_message": {
    "id": 123,
    "message": "Can you send me extra towels?",
    "sender_type": "guest",
    "sender_name": "Guest"
  }
}
```

### Example: Guest Reply to Staff Message

```json
{
  "id": 789,
  "message": "Thank you so much!",
  "sender_type": "guest",
  "reply_to": 456,
  "reply_to_message": {
    "id": 456,
    "message": "Yes, I'll send them right away!",
    "sender_type": "staff",
    "sender_name": "John Smith"
  }
}
```

---

## 💬 Displaying Replies in Chat UI

### React Component Example

```jsx
import React, { useState } from 'react';
import './ChatMessage.css';

const ChatMessage = ({ message, onReply, scrollToMessage }) => {
  const isStaff = message.sender_type === 'staff';
  const isGuest = message.sender_type === 'guest';
  
  return (
    <div 
      id={`message-${message.id}`}
      className={`chat-message ${isStaff ? 'staff-message' : 'guest-message'}`}
    >
      {/* Reply Preview - Show if this message is replying to another */}
      {message.reply_to_message && (
        <div 
          className="reply-preview"
          onClick={() => scrollToMessage(message.reply_to)}
        >
          <div className="reply-border"></div>
          <div className="reply-content">
            <span className="reply-sender">
              {message.reply_to_message.sender_name}
            </span>
            <p className="reply-text">
              {message.reply_to_message.message}
            </p>
          </div>
        </div>
      )}
      
      {/* Message Content */}
      <div className="message-body">
        {/* Staff name (if staff sent the message) */}
        {message.staff_info && (
          <div className="staff-header">
            <strong>{message.staff_info.name}</strong>
            <span className="staff-role">{message.staff_info.role}</span>
          </div>
        )}
        
        {/* Message text */}
        <p className="message-text">{message.message}</p>
        
        {/* Attachments (if any) */}
        {message.has_attachments && (
          <div className="attachments">
            {message.attachments.map(attachment => (
              <AttachmentPreview key={attachment.id} attachment={attachment} />
            ))}
          </div>
        )}
        
        {/* Timestamp and status */}
        <div className="message-footer">
          <span className="timestamp">
            {formatTime(message.timestamp)}
          </span>
          {message.is_edited && (
            <span className="edited-badge">Edited</span>
          )}
          {message.is_read_by_recipient && (
            <span className="read-indicator">✓✓</span>
          )}
        </div>
      </div>
      
      {/* Action buttons */}
      <div className="message-actions">
        <button 
          className="reply-btn"
          onClick={() => onReply(message)}
          title="Reply to this message"
        >
          ↩️ Reply
        </button>
      </div>
    </div>
  );
};

export default ChatMessage;
```

### Complete Chat Window with Reply Functionality

```jsx
import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import './ChatWindow.css';

const ChatWindow = ({ conversationId, hotelSlug }) => {
  const [messages, setMessages] = useState([]);
  const [replyingTo, setReplyingTo] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  // Fetch messages on mount
  useEffect(() => {
    fetchMessages();
  }, [conversationId]);

  const fetchMessages = async () => {
    try {
      const response = await fetch(
        `/api/chat/${hotelSlug}/conversation/${conversationId}/messages/`
      );
      const data = await response.json();
      setMessages(data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    try {
      const payload = {
        message: inputValue.trim(),
        ...(replyingTo && { reply_to: replyingTo.id })
      };

      const response = await fetch(
        `/api/chat/${hotelSlug}/conversation/${conversationId}/send/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }
      );

      const data = await response.json();
      
      // Add new message to list
      setMessages(prev => [...prev, data.message]);
      
      // Clear input and reply mode
      setInputValue('');
      setReplyingTo(null);
      
      // Scroll to bottom
      scrollToBottom();
      
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const scrollToMessage = (messageId) => {
    const element = document.getElementById(`message-${messageId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      
      // Add highlight effect
      element.classList.add('highlight');
      setTimeout(() => {
        element.classList.remove('highlight');
      }, 2000);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-window">
      {/* Messages Container */}
      <div className="messages-container">
        {messages.map(message => (
          <ChatMessage
            key={message.id}
            message={message}
            onReply={setReplyingTo}
            scrollToMessage={scrollToMessage}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Reply Bar (shown when replying) */}
      {replyingTo && (
        <div className="reply-bar">
          <div className="reply-indicator"></div>
          <div className="reply-info">
            <strong>Replying to {replyingTo.sender_type === 'staff' ? replyingTo.staff_info.name : 'Guest'}:</strong>
            <p>{replyingTo.message.substring(0, 60)}{replyingTo.message.length > 60 ? '...' : ''}</p>
          </div>
          <button 
            className="cancel-reply-btn"
            onClick={() => setReplyingTo(null)}
            title="Cancel reply"
          >
            ✕
          </button>
        </div>
      )}

      {/* Input Container */}
      <div className="input-container">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={replyingTo ? "Type your reply..." : "Type a message..."}
          rows={1}
        />
        <button 
          onClick={sendMessage}
          disabled={!inputValue.trim()}
          className="send-btn"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
```

---

## 🎨 CSS Styling

```css
/* ChatMessage.css */

.chat-message {
  margin-bottom: 16px;
  max-width: 70%;
  animation: fadeIn 0.3s ease-in;
}

.guest-message {
  margin-right: auto;
}

.staff-message {
  margin-left: auto;
}

/* Reply Preview Styling */
.reply-preview {
  display: flex;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px 8px 0 0;
  padding: 8px 12px;
  margin-bottom: 4px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.reply-preview:hover {
  background: rgba(0, 0, 0, 0.1);
}

.reply-border {
  width: 3px;
  background: #007bff;
  border-radius: 2px;
  margin-right: 8px;
  flex-shrink: 0;
}

.reply-content {
  flex: 1;
  min-width: 0;
}

.reply-sender {
  font-weight: 600;
  color: #007bff;
  font-size: 12px;
  display: block;
  margin-bottom: 2px;
}

.reply-text {
  margin: 0;
  color: #666;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Message Body */
.message-body {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.staff-message .message-body {
  background: #007bff;
  color: white;
}

.staff-header {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.staff-role {
  margin-left: 8px;
  font-size: 12px;
  opacity: 0.8;
}

.message-text {
  margin: 0;
  line-height: 1.4;
  word-wrap: break-word;
}

.message-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 11px;
  opacity: 0.7;
}

.edited-badge {
  font-style: italic;
}

.read-indicator {
  color: #4CAF50;
}

/* Message Actions */
.message-actions {
  display: none;
  margin-top: 4px;
}

.chat-message:hover .message-actions {
  display: block;
}

.reply-btn {
  background: none;
  border: 1px solid #ddd;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.reply-btn:hover {
  background: #f5f5f5;
  border-color: #007bff;
  color: #007bff;
}

/* Highlight effect when scrolling to a message */
.chat-message.highlight {
  animation: highlightPulse 2s ease;
}

@keyframes highlightPulse {
  0%, 100% { background: transparent; }
  50% { background: rgba(255, 235, 59, 0.3); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

```css
/* ChatWindow.css */

.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Reply Bar */
.reply-bar {
  display: flex;
  align-items: center;
  background: #e3f2fd;
  padding: 12px 16px;
  border-top: 2px solid #007bff;
  gap: 12px;
}

.reply-indicator {
  width: 4px;
  height: 40px;
  background: #007bff;
  border-radius: 2px;
}

.reply-info {
  flex: 1;
}

.reply-info strong {
  display: block;
  color: #007bff;
  font-size: 13px;
  margin-bottom: 4px;
}

.reply-info p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.cancel-reply-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  padding: 4px 8px;
  transition: color 0.2s;
}

.cancel-reply-btn:hover {
  color: #333;
}

/* Input Container */
.input-container {
  display: flex;
  gap: 8px;
  padding: 16px;
  background: white;
  border-top: 1px solid #ddd;
}

.input-container textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  max-height: 100px;
}

.input-container textarea:focus {
  outline: none;
  border-color: #007bff;
}

.send-btn {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #0056b3;
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
```

---

## 🔔 Real-time Updates with Pusher

When a reply is sent, the backend automatically triggers Pusher events. Listen for these events:

```javascript
// Subscribe to conversation channel
const channel = pusher.subscribe(`${hotelSlug}-conversation-${conversationId}-chat`);

// Listen for new messages (including replies)
channel.bind('new-message', (data) => {
  setMessages(prev => [...prev, data]);
  
  // If this message is a reply, you might want to highlight it
  if (data.reply_to) {
    console.log('Received a reply to message:', data.reply_to);
  }
});
```

---

## 🧪 Testing Checklist

### Basic Reply Functionality
- [ ] Send a regular message (without reply)
- [ ] Click reply button on a message
- [ ] Verify reply bar appears with correct preview
- [ ] Send a reply and verify it includes `reply_to` field
- [ ] Verify reply preview appears above the new message
- [ ] Click on reply preview and verify it scrolls to original message
- [ ] Test canceling reply mode (X button)

### Guest User Tests
- [ ] **Guest replies to staff message** - Verify guest can reply to receptionist
- [ ] **Guest sees staff reply preview** - Verify staff info (name, role) displays correctly
- [ ] Guest reply shows "Guest" as sender_name in preview
- [ ] Guest receives Pusher notification when staff replies to their message

### Staff User Tests
- [ ] **Staff replies to guest message** - Verify staff can reply to guest request
- [ ] **Staff sees guest reply preview** - Verify "Guest" shows as sender
- [ ] Staff reply shows staff name and role in preview
- [ ] Staff receives Pusher notification when guest replies to their message

### Advanced Scenarios
- [ ] Test reply with attachments (images, PDFs)
- [ ] Test editing a message that has replies (should maintain reply chain)
- [ ] Verify deleted original message doesn't break reply display (should show null)
- [ ] Test multiple nested replies (A→B→C→D)
- [ ] Test reply in busy conversation (20+ messages)
- [ ] Test Pusher real-time reply updates for both staff and guest

### Edge Cases
- [ ] Long message text in reply preview (should truncate properly)
- [ ] Reply to very old message (should scroll correctly)
- [ ] Reply when original message is off-screen
- [ ] Multiple staff members replying to same guest message
- [ ] Guest replying to different staff members in same conversation

---

## ⚠️ Important Notes

1. **`reply_to` is optional** - If not provided, message is sent normally
2. **Deleted messages** - If the original message is deleted, `reply_to_message` will be `null`
3. **Scroll to message** - Clicking the reply preview should scroll to the original message
4. **Visual feedback** - Add highlight animation when scrolling to referenced message
5. **Mobile responsive** - Adjust reply preview width for mobile devices
6. **Keyboard shortcuts** - Consider adding Ctrl+Click or right-click to reply

---

## 🚀 Advanced Features (Optional)

### Thread View
For heavily nested replies, consider implementing a thread view that groups replies together.

### Quote Formatting
You could format the reply text to include a quote:
```
> Original message text
> from sender

Your reply here
```

### Reply Count Badge
Show how many replies a message has received:
```jsx
{message.replies?.length > 0 && (
  <span className="reply-count">
    {message.replies.length} {message.replies.length === 1 ? 'reply' : 'replies'}
  </span>
)}
```

---

## � Troubleshooting

### Issue: All messages show `reply_to: null` and `reply_to_message: null`

**Console output:**
```
🔍 [MSG RENDER] 624 reply_to: null reply_to_message: null
🔍 [MSG RENDER] 625 reply_to: null reply_to_message: null
```

**Possible Causes:**

1. **No replies have been sent yet** - The field exists but no messages are actually replying to other messages
   - **Solution:** Test by sending a reply using the reply functionality

2. **Backend not receiving `reply_to` field** - Check network request payload
   - **Debug:** Open browser DevTools → Network tab
   - Look for POST request to `/send/` endpoint
   - Check Request Payload - should include `reply_to` field if replying
   
   ```json
   // Correct payload when replying
   {
     "message": "Thank you!",
     "reply_to": 624  // ← This should be present
   }
   
   // Regular message (no reply)
   {
     "message": "Hello"
     // reply_to is omitted
   }
   ```

3. **Frontend not sending `reply_to` in request**
   - **Check your send message function:**
   ```javascript
   // ❌ Wrong - not including reply_to
   const sendMessage = () => {
     fetch('/api/chat/.../send/', {
       body: JSON.stringify({
         message: inputValue
         // Missing reply_to!
       })
     });
   };
   
   // ✅ Correct - including reply_to when replying
   const sendMessage = () => {
     const payload = {
       message: inputValue,
       ...(replyingTo && { reply_to: replyingTo.id })
     };
     
     fetch('/api/chat/.../send/', {
       body: JSON.stringify(payload)
     });
   };
   ```

4. **Database has old messages without replies**
   - Existing messages won't have `reply_to` until you actually send a reply
   - Create a new reply to test the functionality

### How to Test if Reply Functionality is Working

**Step-by-step test:**

1. **Open browser console** and filter for your debug logs

2. **Send a regular message** - Should show `reply_to: null`
   ```
   POST /api/chat/hotel-slug/conversation/48/send/
   Payload: { "message": "Test message" }
   ```

3. **Click "Reply" button** on that message
   - Verify reply bar appears
   - Verify `replyingTo` state is set

4. **Send the reply** - Should show `reply_to: <message_id>`
   ```
   POST /api/chat/hotel-slug/conversation/48/send/
   Payload: { "message": "This is a reply", "reply_to": 644 }
   ```

5. **Check the response** - Backend should return:
   ```json
   {
     "message": {
       "id": 645,
       "message": "This is a reply",
       "reply_to": 644,  // ← Should have value
       "reply_to_message": {  // ← Should have data
         "id": 644,
         "message": "Test message",
         "sender_type": "staff",
         "sender_name": "John Smith"
       }
     }
   }
   ```

6. **Verify in UI** - The new message should display reply preview

### Backend Verification

If frontend is sending `reply_to` but backend isn't saving it, check Django admin or database:

#### Django Shell Commands

```python
# Django shell
python manage.py shell

# Check if any messages have replies
from chat.models import RoomMessage

messages_with_replies = RoomMessage.objects.exclude(reply_to=None)
print(f"Messages with replies: {messages_with_replies.count()}")

# Check specific message
msg = RoomMessage.objects.get(id=645)
print(f"Reply to: {msg.reply_to}")
print(f"Reply to message: {msg.reply_to.message if msg.reply_to else 'None'}")

# Get the last 5 messages to see reply_to values
last_messages = RoomMessage.objects.order_by('-id')[:5]
for msg in last_messages:
    print(f"ID: {msg.id} | reply_to: {msg.reply_to_id} | message: {msg.message[:30]}")
```

#### Check Backend Logs

When a reply is sent, you should see logs like:
```
🔵 NEW MESSAGE | Type: staff | Hotel: hotel-killarney | Room: 101 | Conversation: 48
Message created with ID: 645
✅ MESSAGE COMPLETE | ID: 645 | Type: staff
```

#### Test Backend Directly (curl/Postman)

```bash
# Send a test reply
curl -X POST http://localhost:8000/api/chat/hotel-slug/conversation/48/send/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test reply from curl",
    "reply_to": 643
  }'

# Response should include:
# {
#   "message": {
#     "id": 646,
#     "reply_to": 643,
#     "reply_to_message": { ... }
#   }
# }
```

### Common Frontend Issues

**Issue: Reply button doesn't set `replyingTo` state**
```javascript
// Make sure onClick handler is correct
<button onClick={() => setReplyingTo(message)}>
  Reply
</button>
```

**Issue: `replyingTo` state not included in payload**
```javascript
// Verify your send function checks for replyingTo
const payload = {
  message: inputValue,
  ...(replyingTo && { reply_to: replyingTo.id })  // ← Check this line
};

console.log('Sending payload:', payload);  // ← Add debug log
```

**Issue: State cleared before sending**
```javascript
// Wrong order - clears state before sending!
setReplyingTo(null);  // ❌
await sendMessage();

// Correct order
await sendMessage();  // ✅
setReplyingTo(null);
```

---

## �📞 Support

For backend-related questions or issues, contact the backend team or refer to:
- Chat Models: `chat/models.py`
- Chat Views: `chat/views.py`
- Chat Serializers: `chat/serializers.py`
