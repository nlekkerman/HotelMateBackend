# Staff Chat - Share, Reply & Delete Guide

## 📋 Complete Frontend Guide for Message & File Operations

This guide covers how to **share messages**, **reply to messages and files**, **delete messages**, and handle **real-time updates** in staff chat. Users can delete their own messages while still being able to share and reply to both their own and others' messages.

---

## 🎯 Core Principles

### ✅ What Users Can Do:
1. ✅ **Share** any message or file (yours or others')
2. ✅ **Reply** to any message or file (yours or others')
3. ✅ **Delete** only your own messages
4. ✅ **Reply to deleted messages** (shows "[Message deleted]")
5. ✅ **Share deleted messages** (forwards the deleted state)

### ⚠️ Important Rules:
- Users can **only delete their own messages**
- **Managers/Admins** can delete any message
- Deleted messages show **"[Message deleted]"** or **"[Message and file(s) deleted]"**
- You **can reply** to deleted messages
- Real-time updates via **Pusher**
- Push notifications via **FCM** (recipients only)

---

## 💬 Send Text Messages

### Basic Text Message

```javascript
// POST /api/staff_chat/{hotel_slug}/conversations/{conversation_id}/send-message/

async function sendMessage(conversationId, messageText) {
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/conversations/${conversationId}/send-message/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: messageText
      })
    }
  );
  
  return await response.json();
}

// Example
await sendMessage(45, "Hello team! Ready for the shift?");
```

**Response:**
```json
{
  "id": 234,
  "conversation": 45,
  "sender": {
    "id": 3,
    "first_name": "John",
    "last_name": "Doe",
    "profile_image": "https://..."
  },
  "message": "Hello team! Ready for the shift?",
  "timestamp": "2025-11-05T14:30:00Z",
  "status": "delivered",
  "is_read": false,
  "is_edited": false,
  "is_deleted": false,
  "reply_to_message": null,
  "reactions": [],
  "attachments": [],
  "mentions": [],
  "read_by": []
}
```

---

## ↩️ Reply to Messages

### Reply to Text Message

```javascript
// POST /api/staff_chat/{hotel_slug}/conversations/{conversation_id}/send-message/

async function replyToMessage(conversationId, replyToMessageId, messageText) {
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/conversations/${conversationId}/send-message/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: messageText,
        reply_to: replyToMessageId
      })
    }
  );
  
  return await response.json();
}

// Example: Reply to message #234
await replyToMessage(45, 234, "Yes, I'm ready!");
```

**Response includes reply information:**
```json
{
  "id": 236,
  "message": "Yes, I'm ready!",
  "reply_to_message": {
    "id": 234,
    "message": "Hello team! Ready for the shift?",
    "sender": {
      "id": 3,
      "first_name": "John",
      "last_name": "Doe"
    },
    "attachments": []
  }
}
```

### Reply to Your Own Message

**✅ You CAN reply to your own messages!**

```javascript
// Reply to your own message
await replyToMessage(45, 234, "Actually, let me add to that...");
```

### Reply to Deleted Message

**✅ You CAN reply to deleted messages!** The reply will show "[Message deleted]" as the original message.

```javascript
// Reply to a deleted message
await replyToMessage(45, 234, "I saw your previous message");
```

**Response shows deleted state:**
```json
{
  "id": 237,
  "message": "I saw your previous message",
  "reply_to_message": {
    "id": 234,
    "message": "[Message deleted]",
    "is_deleted": true,
    "sender": {
      "id": 3,
      "first_name": "John",
      "last_name": "Doe"
    }
  }
}
```

---

## 📎 Reply with Files

### Upload Files as Reply

```javascript
// POST /api/staff_chat/{hotel_slug}/conversations/{conversation_id}/upload/

async function replyWithFiles(conversationId, replyToMessageId, files, messageText = '') {
  const formData = new FormData();
  
  // Add files
  files.forEach(file => {
    formData.append('files', file);
  });
  
  // Specify which message you're replying to
  formData.append('reply_to', replyToMessageId);
  
  // Add optional message text
  if (messageText) {
    formData.append('message', messageText);
  }
  
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/conversations/${conversationId}/upload/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      body: formData
    }
  );
  
  return await response.json();
}

// Example: Reply with photo
const fileInput = document.getElementById('fileInput');
const files = Array.from(fileInput.files);
await replyWithFiles(45, 234, files, "Here's the inspection photo you requested");
```

### Reply to Message with Files

**✅ You CAN reply to messages that have attachments!**

```javascript
// Reply to a message that has files attached
await replyToMessage(45, 235, "Thanks for sharing those photos!");
```

---

## 📤 Share Messages

### Get or Create Conversation with Staff

**Important**: When sharing, you select **staff members**, not conversations. The system will automatically get or create the conversation.

```javascript
// POST /api/staff_chat/{hotel_slug}/conversations/

async function getOrCreateConversation(participantIds, title = '') {
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/conversations/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        participant_ids: participantIds,  // Array of staff IDs
        title: title  // Optional
      })
    }
  );
  
  const data = await response.json();
  
  // Returns existing conversation if one exists, or creates new one
  // Response status: 200 (existing) or 201 (created)
  return data;
}

// Example: Get or create 1-on-1 conversation
const conversation = await getOrCreateConversation([5]);  // Staff ID 5

// Example: Get or create group conversation
const groupConv = await getOrCreateConversation([5, 8, 12], "Team Leaders");
```

**Response:**
```json
{
  "id": 46,
  "title": "Team Leaders",
  "hotel": 1,
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
  "created_at": "2025-11-06T10:00:00Z",
  "updated_at": "2025-11-06T10:00:00Z",
  "last_message": null,
  "unread_count": 0
}
```

### Share Message to Staff Members

```javascript
async function shareMessageToStaff(originalMessage, staffIds, additionalText = '') {
  // Step 1: Get or create conversation with selected staff
  const conversation = await getOrCreateConversation(staffIds);
  
  // Step 2: Format shared message
  let messageText = `📤 Shared message from ${originalMessage.sender.first_name}:\n\n"${originalMessage.message}"`;
  
  if (additionalText) {
    messageText += `\n\n${additionalText}`;
  }
  
  // Step 3: Send message to conversation
  return await sendMessage(conversation.id, messageText);
}

// Example: Share to one staff member
await shareMessageToStaff(originalMessage, [5], "FYI - important update");

// Example: Share to multiple staff members
await shareMessageToStaff(originalMessage, [5, 8, 12], "Team, please review this");
```

### Share/Forward Message to Existing Conversation

If you already have a conversation ID:

```javascript
async function shareMessage(originalMessageId, targetConversationId, additionalText = '') {
  // Get the original message first
  const originalMessage = await getMessageDetails(originalMessageId);
  
  // Create new message with shared content
  let messageText = `📤 Shared message from ${originalMessage.sender.first_name}:\n\n"${originalMessage.message}"`;
  
  if (additionalText) {
    messageText += `\n\n${additionalText}`;
  }
  
  return await sendMessage(targetConversationId, messageText);
}

// Example: Share message to another conversation
await shareMessage(234, 46, "Check out this important update");
```

### Share Message with Files (Images & Documents)

**Important**: When sharing a message with files (images, PDFs, etc.), you want the **actual files to appear** in the new conversation, not just text describing them.

#### Method 1: Re-upload Files to New Conversation (Recommended)

This creates new file attachments in the target conversation so recipients see the actual images/documents:

```javascript
async function shareMessageWithFiles(originalMessage, targetConversationId, additionalText = '') {
  // Format message text with context
  let messageText = `📤 Shared from ${originalMessage.sender.first_name}:\n\n"${originalMessage.message}"`;
  
  if (additionalText) {
    messageText += `\n\n${additionalText}`;
  }
  
  // If message has attachments, download and re-upload them
  if (originalMessage.attachments && originalMessage.attachments.length > 0) {
    // Download files from Cloudinary URLs
    const filePromises = originalMessage.attachments.map(async (att) => {
      const response = await fetch(att.file_url);
      const blob = await response.blob();
      
      // Create File object with original name and type
      return new File([blob], att.file_name, { type: att.mime_type });
    });
    
    const files = await Promise.all(filePromises);
    
    // Upload files to new conversation
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    formData.append('message', messageText);
    
    const uploadResponse = await fetch(
      `/api/staff_chat/${hotelSlug}/conversations/${targetConversationId}/upload/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        body: formData
      }
    );
    
    return await uploadResponse.json();
  } else {
    // No files, just send text message
    return await sendMessage(targetConversationId, messageText);
  }
}

// Example: Share message with images
await shareMessageWithFiles(messageWithPhotos, 46, "Check out these inspection photos");
```

**Result**: Recipients will see:
- ✅ Your shared message text
- ✅ The actual images displayed (not just text)
- ✅ Documents as clickable attachments
- ✅ All files stored in Cloudinary

**✅ IMPORTANT**: You can share the **same image/file multiple times** to different conversations!

```javascript
// Share same message with photos to multiple staff members
const messageWithPhotos = { 
  id: 234, 
  message: "Inspection complete",
  sender: { first_name: "John" },
  attachments: [
    { file_url: "https://...", file_name: "room_101.jpg", mime_type: "image/jpeg" }
  ]
};

// Share to Maintenance team
await shareMessageWithFiles(messageWithPhotos, maintenanceConvId, "For your review");

// Share same photos to Manager
await shareMessageWithFiles(messageWithPhotos, managerConvId, "FYI");

// Share to another colleague
await shareMessageWithFiles(messageWithPhotos, colleagueConvId, "Look at this");

// ✅ Share to SAME conversation multiple times (allowed!)
await shareMessageWithFiles(messageWithPhotos, maintenanceConvId, "Updated version");
await shareMessageWithFiles(messageWithPhotos, maintenanceConvId, "Final review needed");

// ✅ Each share creates a NEW message with NEW attachments
// ✅ Each conversation gets its own copy of the image
// ✅ Images are re-uploaded to Cloudinary (new URLs created)
// ✅ No limit on how many times you can share
// ✅ Can share to same conversation multiple times
```

#### Method 2: Share File URLs (Text Only - Not Recommended)

Only shares text mentioning the files (files won't display):

```javascript
async function shareMessageFileInfo(originalMessage, targetConversationId, additionalText = '') {
  let messageText = `📤 Shared from ${originalMessage.sender.first_name}:\n\n"${originalMessage.message}"`;
  
  if (additionalText) {
    messageText += `\n\n${additionalText}`;
  }
  
  // Add file links as text
  if (originalMessage.attachments && originalMessage.attachments.length > 0) {
    messageText += `\n\n📎 Files:\n`;
    originalMessage.attachments.forEach(att => {
      messageText += `${att.file_name}: ${att.file_url}\n`;
    });
  }
  
  return await sendMessage(targetConversationId, messageText);
}
```

**Result**: Recipients will see:
- ⚠️ Text with file URLs (must click links)
- ⚠️ No image previews
- ⚠️ No inline display

### Share Your Own Message

**✅ You CAN share your own messages!**

```javascript
// Share your own message to another conversation
await shareMessage(234, 46, "Forwarding my previous message");
```

---

## 🗑️ Delete Messages

### Delete Your Own Message (Soft Delete)

**⚠️ Important**: You can **only delete your own messages**. Managers/Admins can delete any message.

```javascript
// DELETE /api/staff_chat/{hotel_slug}/messages/{message_id}/delete/

async function deleteMessage(messageId) {
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/messages/${messageId}/delete/`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    }
  );
  
  return await response.json();
}

// Example with confirmation
async function handleDeleteMessage(messageId, messageText) {
  if (confirm(`Delete message: "${messageText}"?`)) {
    try {
      const result = await deleteMessage(messageId);
      console.log('Message deleted:', result);
      // UI will update via Pusher event
    } catch (error) {
      console.error('Failed to delete message:', error);
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "hard_delete": false,
  "message": {
    "id": 234,
    "message": "[Message deleted]",
    "is_deleted": true,
    "deleted_at": "2025-11-05T14:45:00Z"
  }
}
```

### Hard Delete (Permanent Removal)

**Only for Managers/Admins**: Permanently removes message from database.

```javascript
// DELETE /api/staff_chat/{hotel_slug}/messages/{message_id}/delete/?hard_delete=true

async function hardDeleteMessage(messageId) {
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/messages/${messageId}/delete/?hard_delete=true`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    }
  );
  
  return await response.json();
}

// Example (managers only)
await hardDeleteMessage(234);
```

**Response:**
```json
{
  "success": true,
  "hard_delete": true,
  "message_id": 234
}
```

### Delete Message with Attachments

When you delete a message with files:

```javascript
// If message has only files (no text):
// Shows: "[File deleted]"

// If message has text and files:
// Shows: "[Message and file(s) deleted]"

// If message has only text:
// Shows: "[Message deleted]"
```

---

## 🎨 Deleted Message Placeholders

### Display Deleted Messages

When a message is deleted (soft delete), it should show a placeholder instead of the original content:

```javascript
function DeletedMessagePlaceholder({ message, showTimestamp = true }) {
  // Determine placeholder text based on content type
  const getPlaceholderText = () => {
    if (message.attachments && message.attachments.length > 0) {
      // Had files
      if (message.message && message.message !== '[File shared]') {
        return '🗑️ [Message and file(s) deleted]';
      }
      return '🗑️ [File deleted]';
    }
    // Text only
    return '🗑️ [Message deleted]';
  };
  
  return (
    <div className="message deleted-message">
      <div className="deleted-placeholder">
        <span className="deleted-icon">🗑️</span>
        <span className="deleted-text">{getPlaceholderText()}</span>
      </div>
      
      {showTimestamp && (
        <div className="timestamp">
          Deleted {formatTimeAgo(message.deleted_at)}
        </div>
      )}
    </div>
  );
}
```

### CSS for Deleted Messages

```css
/* Deleted message styling */
.message.deleted-message {
  opacity: 0.6;
}

.deleted-placeholder {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f5f5f5;
  border: 1px dashed #ccc;
  border-radius: 8px;
  font-style: italic;
  color: #666;
}

.deleted-icon {
  font-size: 16px;
}

.deleted-text {
  font-size: 14px;
  color: #999;
}

/* When deleted message is in reply preview */
.reply-preview .deleted {
  color: #999;
  font-style: italic;
  text-decoration: line-through;
}
```

### Complete Message Component with Deleted State

```javascript
function MessageComponent({ message, currentUserId }) {
  const isMine = message.sender.id === currentUserId;
  
  // If message is deleted, show placeholder
  if (message.is_deleted) {
    return (
      <div className={`message deleted-message ${isMine ? 'my-message' : 'their-message'}`}>
        {/* Still show sender for context */}
        {!isMine && (
          <div className="sender-info">
            <img src={message.sender.profile_image} alt="" />
            <span>{message.sender.first_name} {message.sender.last_name}</span>
          </div>
        )}
        
        {/* Deleted placeholder */}
        <div className="deleted-placeholder">
          <span className="deleted-icon">🗑️</span>
          <span className="deleted-text">{message.message}</span>
        </div>
        
        {/* Timestamp */}
        <div className="timestamp">
          {formatTime(message.timestamp)} · Deleted {formatTimeAgo(message.deleted_at)}
        </div>
        
        {/* Note: Can still reply to deleted messages */}
        <div className="deleted-hint">
          <small>💡 You can still reply to this message</small>
        </div>
      </div>
    );
  }
  
  // Normal message display
  return (
    <div className={`message ${isMine ? 'my-message' : 'their-message'}`}>
      {/* ... normal message content ... */}
    </div>
  );
}
```

### Reply Preview with Deleted Message

```javascript
function ReplyPreview({ replyToMessage, onClick }) {
  return (
    <div className="reply-preview" onClick={onClick}>
      <div className="reply-icon">↩️</div>
      <div className="reply-content">
        <strong>{replyToMessage.sender.first_name}:</strong>
        
        {/* Show deleted state in reply preview */}
        {replyToMessage.is_deleted ? (
          <span className="deleted">
            🗑️ {replyToMessage.message}
          </span>
        ) : (
          <span>{replyToMessage.message}</span>
        )}
        
        {/* Show attachment indicator if had files */}
        {replyToMessage.attachments?.length > 0 && !replyToMessage.is_deleted && (
          <span className="attachment-indicator">
            📎 {replyToMessage.attachments.length}
          </span>
        )}
      </div>
    </div>
  );
}
```

### Placeholder Text Examples

```javascript
// Backend sends these exact placeholder texts:

// 1. Text-only message deleted
{
  "message": "[Message deleted]",
  "is_deleted": true
}

// 2. Image/file-only message deleted
{
  "message": "[File deleted]",
  "is_deleted": true
}

// 3. Message with text and files deleted
{
  "message": "[Message and file(s) deleted]",
  "is_deleted": true
}
```

### Handle Deleted Messages in Chat List

```javascript
function ChatMessageList({ messages, currentUserId }) {
  return (
    <div className="messages-container">
      {messages.map(msg => (
        <div key={msg.id}>
          {msg.is_deleted ? (
            <DeletedMessagePlaceholder message={msg} />
          ) : (
            <MessageComponent message={msg} currentUserId={currentUserId} />
          )}
        </div>
      ))}
    </div>
  );
}
```

### Important Notes:
- ✅ **Always show sender info** even for deleted messages (for context)
- ✅ **Keep timestamp visible** so users know when it was sent/deleted
- ✅ **Visual styling** should be muted (gray, italic, dashed border)
- ✅ **Still allow replies** - show hint that users can reply
- ✅ **Reply preview** should clearly show deleted state
- ✅ **No attachments shown** after deletion (they're removed from cloud)

---

## 🎨 UI Components

### Message with Reply & Delete Actions

```javascript
function MessageWithActions({ message, currentUserId, conversationId }) {
  const isMine = message.sender.id === currentUserId;
  const [showActions, setShowActions] = useState(false);
  const [replyTo, setReplyTo] = useState(null);
  
  // Check if user can delete this message
  const canDelete = isMine || isManager(currentUserId);
  
  return (
    <div className={`message ${isMine ? 'my-message' : 'their-message'}`}>
      {/* Sender info */}
      {!isMine && (
        <div className="sender-info">
          <img src={message.sender.profile_image} alt="" />
          <span>{message.sender.first_name} {message.sender.last_name}</span>
        </div>
      )}
      
      {/* Reply preview (if this message is a reply) */}
      {message.reply_to_message && (
        <div className="reply-preview" onClick={() => scrollToMessage(message.reply_to_message.id)}>
          <div className="reply-icon">↩️</div>
          <div className="reply-content">
            <strong>{message.reply_to_message.sender.first_name}:</strong>
            <span className={message.reply_to_message.is_deleted ? 'deleted' : ''}>
              {message.reply_to_message.message}
            </span>
          </div>
        </div>
      )}
      
      {/* Message content */}
      <div className={`message-content ${message.is_deleted ? 'deleted' : ''}`}>
        {message.message}
        {message.is_edited && !message.is_deleted && (
          <span className="edited-badge">edited</span>
        )}
      </div>
      
      {/* Attachments */}
      {message.attachments?.length > 0 && !message.is_deleted && (
        <div className="attachments">
          {message.attachments.map(att => (
            <AttachmentPreview key={att.id} attachment={att} />
          ))}
        </div>
      )}
      
      {/* Timestamp */}
      <div className="timestamp">
        {formatTime(message.timestamp)}
      </div>
      
      {/* Action buttons (show on hover) */}
      {!message.is_deleted && (
        <div className="message-actions" onMouseEnter={() => setShowActions(true)} onMouseLeave={() => setShowActions(false)}>
          {showActions && (
            <>
              {/* Reply button (available for ALL messages) */}
              <button onClick={() => setReplyTo(message)} title="Reply">
                ↩️ Reply
              </button>
              
              {/* Share button (available for ALL messages) */}
              <button onClick={() => shareMessage(message)} title="Share">
                📤 Share
              </button>
              
              {/* Delete button (only for your own messages) */}
              {canDelete && (
                <button onClick={() => handleDeleteMessage(message.id, message.message)} title="Delete" className="delete-btn">
                  🗑️ Delete
                </button>
              )}
            </>
          )}
        </div>
      )}
      
      {/* Reply interface */}
      {replyTo && (
        <ReplyInput
          conversationId={conversationId}
          replyTo={replyTo}
          onCancel={() => setReplyTo(null)}
          onSent={() => setReplyTo(null)}
        />
      )}
    </div>
  );
}
```

### Reply Input Component

```javascript
function ReplyInput({ conversationId, replyTo, onCancel, onSent }) {
  const [messageText, setMessageText] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const fileInputRef = useRef(null);
  
  async function handleSend(e) {
    e.preventDefault();
    
    if (selectedFiles.length > 0) {
      // Reply with files
      await replyWithFiles(conversationId, replyTo.id, selectedFiles, messageText);
    } else if (messageText.trim()) {
      // Reply with text
      await replyToMessage(conversationId, replyTo.id, messageText);
    }
    
    setMessageText('');
    setSelectedFiles([]);
    onSent && onSent();
  }
  
  return (
    <div className="reply-input-container">
      {/* Show what we're replying to */}
      <div className="replying-to">
        <div className="reply-preview">
          <span>Replying to {replyTo.sender.first_name}:</span>
          <p>{replyTo.message}</p>
        </div>
        <button onClick={onCancel} className="cancel-reply">✕</button>
      </div>
      
      {/* File preview */}
      {selectedFiles.length > 0 && (
        <div className="selected-files">
          {selectedFiles.map((file, index) => (
            <div key={index} className="file-preview">
              <span>{file.name}</span>
              <button onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== index))}>
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
      
      {/* Input form */}
      <form onSubmit={handleSend} className="reply-form">
        <input
          type="text"
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          placeholder="Type your reply..."
          autoFocus
        />
        
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx"
          onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
          style={{ display: 'none' }}
        />
        
        <button type="button" onClick={() => fileInputRef.current?.click()}>
          📎
        </button>
        
        <button type="submit" disabled={!messageText.trim() && selectedFiles.length === 0}>
          Send Reply
        </button>
      </form>
    </div>
  );
}
```

### Share Message Modal (Staff Selection)

**Best Practice**: Select staff members instead of conversations. This creates the conversation if it doesn't exist.

```javascript
function ShareMessageModal({ message, onClose, currentUserId }) {
  const [staffList, setStaffList] = useState([]);
  const [selectedStaff, setSelectedStaff] = useState([]);
  const [additionalText, setAdditionalText] = useState('');
  const [sharing, setSharing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  useEffect(() => {
    loadStaff();
  }, []);
  
  async function loadStaff() {
    // Load all staff in hotel (excluding current user)
    const response = await fetch(
      `/api/staff_chat/${hotelSlug}/staff/`,
      { headers: { 'Authorization': `Bearer ${authToken}` } }
    );
    const data = await response.json();
    
    // Filter out current user
    setStaffList(data.filter(staff => staff.id !== currentUserId));
  }
  
  function toggleStaff(staffId) {
    setSelectedStaff(prev => 
      prev.includes(staffId)
        ? prev.filter(id => id !== staffId)
        : [...prev, staffId]
    );
  }
  
  async function handleShare() {
    if (selectedStaff.length === 0) {
      alert('Please select at least one staff member');
      return;
    }
    
    setSharing(true);
    try {
      // ✅ Get or create conversation with selected staff
      // Returns existing conversation OR creates new one (no duplicates!)
      const conversation = await getOrCreateConversation(selectedStaff);
      
      // Format shared message text
      let messageText = `📤 Shared message from ${message.sender.first_name}:\n\n"${message.message}"`;
      
      if (additionalText) {
        messageText += `\n\n${additionalText}`;
      }
      
      // ✅ If message has files, download and re-upload them
      // This ensures actual images/documents appear in the new conversation
      if (message.attachments && message.attachments.length > 0) {
        // Download files from Cloudinary URLs
        const filePromises = message.attachments.map(async (att) => {
          const response = await fetch(att.file_url);
          const blob = await response.blob();
          return new File([blob], att.file_name, { type: att.mime_type });
        });
        
        const files = await Promise.all(filePromises);
        
        // Upload files with message to conversation
        const formData = new FormData();
        files.forEach(file => {
          formData.append('files', file);
        });
        formData.append('message', messageText);
        
        await fetch(
          `/api/staff_chat/${hotelSlug}/conversations/${conversation.id}/upload/`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${authToken}`
            },
            body: formData
          }
        );
      } else {
        // No files, just send text message
        await sendMessage(conversation.id, messageText);
      }
      
      alert('Message shared successfully!');
      onClose();
    } catch (error) {
      console.error('Failed to share message:', error);
      alert('Failed to share message');
    } finally {
      setSharing(false);
    }
  }
  
  // Filter staff by search term
  const filteredStaff = staffList.filter(staff =>
    `${staff.first_name} ${staff.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
    staff.role?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  return (
    <div className="share-modal">
      <div className="modal-content">
        <h3>Share Message</h3>
        
        {/* Preview of message being shared */}
        <div className="message-preview">
          <strong>{message.sender.first_name}:</strong>
          <p>{message.message}</p>
          {message.attachments?.length > 0 && (
            <div className="attachments-info">
              📎 {message.attachments.length} file(s) attached
            </div>
          )}
        </div>
        
        {/* Search staff */}
        <div className="staff-search">
          <input
            type="text"
            placeholder="🔍 Search staff by name or role..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        {/* Select staff members */}
        <div className="staff-selector">
          <label>Share with:</label>
          <div className="staff-list">
            {filteredStaff.map(staff => (
              <div
                key={staff.id}
                className={`staff-item ${selectedStaff.includes(staff.id) ? 'selected' : ''}`}
                onClick={() => toggleStaff(staff.id)}
              >
                <img src={staff.profile_image} alt="" className="staff-avatar" />
                <div className="staff-info">
                  <span className="staff-name">
                    {staff.first_name} {staff.last_name}
                  </span>
                  <span className="staff-role">{staff.role}</span>
                </div>
                {selectedStaff.includes(staff.id) && (
                  <span className="selected-icon">✓</span>
                )}
              </div>
            ))}
          </div>
          
          {/* Selected count */}
          {selectedStaff.length > 0 && (
            <div className="selected-count">
              {selectedStaff.length} staff member(s) selected
            </div>
          )}
        </div>
        
        {/* Additional message */}
        <div className="additional-text">
          <label>Add a message (optional):</label>
          <textarea
            value={additionalText}
            onChange={(e) => setAdditionalText(e.target.value)}
            placeholder="Add your own message..."
          />
        </div>
        
        {/* Actions */}
        <div className="modal-actions">
          <button onClick={onClose} disabled={sharing}>
            Cancel
          </button>
          <button onClick={handleShare} disabled={sharing || selectedStaff.length === 0}>
            {sharing ? 'Sharing...' : `Share with ${selectedStaff.length || '...'}`}
          </button>
        </div>
      </div>
    </div>
  );
}
```

### CSS for Staff Selection

```css
/* Share modal */
.share-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

/* Staff search */
.staff-search input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin: 16px 0;
  font-size: 14px;
}

/* Staff list */
.staff-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-top: 8px;
}

.staff-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.staff-item:hover {
  background: #f5f5f5;
}

.staff-item.selected {
  background: #e3f2fd;
  border-left: 3px solid #2196f3;
}

.staff-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.staff-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.staff-name {
  font-weight: 500;
  font-size: 14px;
}

.staff-role {
  font-size: 12px;
  color: #666;
}

.selected-icon {
  color: #2196f3;
  font-weight: bold;
  font-size: 18px;
}

.selected-count {
  margin-top: 8px;
  font-size: 12px;
  color: #2196f3;
  font-weight: 500;
}
```

### Alternative: Share to Existing Conversation

If you want to allow sharing to existing conversations as well:

```javascript
function ShareMessageModal({ message, onClose, currentUserId }) {
  const [mode, setMode] = useState('staff'); // 'staff' or 'conversation'
  const [staffList, setStaffList] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [selectedStaff, setSelectedStaff] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  
  // ... rest of component
  
  return (
    <div className="share-modal">
      <div className="modal-content">
        <h3>Share Message</h3>
        
        {/* Toggle between staff and conversation selection */}
        <div className="share-mode-toggle">
          <button
            className={mode === 'staff' ? 'active' : ''}
            onClick={() => setMode('staff')}
          >
            👥 Select Staff
          </button>
          <button
            className={mode === 'conversation' ? 'active' : ''}
            onClick={() => setMode('conversation')}
          >
            💬 Existing Conversation
          </button>
        </div>
        
        {mode === 'staff' ? (
          // Staff selection UI
          <div>...</div>
        ) : (
          // Conversation selection UI
          <div className="conversation-selector">
            <label>Select conversation:</label>
            <select onChange={(e) => setSelectedConversation(e.target.value)}>
              <option value="">Choose...</option>
              {conversations.map(conv => (
                <option key={conv.id} value={conv.id}>
                  {conv.title || conv.participants.map(p => p.first_name).join(', ')}
                </option>
              ))}
            </select>
          </div>
        )}
        
        {/* ... rest of modal */}
      </div>
    </div>
  );
}
```

---

## 🔄 Real-Time Updates (Pusher)

### Setup Pusher Connection

```javascript
import Pusher from 'pusher-js';

// Initialize Pusher
const pusher = new Pusher('YOUR_PUSHER_KEY', {
  cluster: 'YOUR_CLUSTER',
  encrypted: true
});

// Subscribe to conversation channel
const conversationId = 45;
const channelName = `${hotelSlug}-staff-conversation-${conversationId}`;
const channel = pusher.subscribe(channelName);
```

### Listen for Message Events

```javascript
// 1. New message
channel.bind('new-message', (data) => {
  console.log('📨 New message:', data);
  
  addMessageToUI({
    id: data.message_id,
    message: data.message,
    sender: data.sender,
    timestamp: data.timestamp,
    reply_to_message: data.reply_to || null,
    attachments: data.attachments || [],
    is_deleted: false
  });
  
  // Play notification sound if not viewing conversation
  if (!isConversationVisible()) {
    playNotificationSound();
    showBadge(conversationId);
  }
});

// 2. Message edited
channel.bind('message-edited', (data) => {
  console.log('✏️ Message edited:', data);
  
  updateMessageInUI(data.message_id, {
    message: data.new_message,
    is_edited: true,
    edited_at: data.edited_at
  });
});

// 3. Message deleted
channel.bind('message-deleted', (data) => {
  console.log('🗑️ Message deleted:', data);
  
  if (data.hard_delete) {
    // Hard delete - remove from UI completely
    removeMessageFromUI(data.message_id);
  } else {
    // Soft delete - update to show "[Message deleted]"
    updateMessageInUI(data.message_id, {
      message: data.message.message,
      is_deleted: true,
      deleted_at: data.timestamp
    });
  }
});

// 4. Attachment uploaded
channel.bind('attachment-uploaded', (data) => {
  console.log('📎 Files uploaded:', data);
  
  updateMessageAttachments(data.message_id, data.attachments);
});

// 5. Attachment deleted
channel.bind('attachment-deleted', (data) => {
  console.log('🗑️ File deleted:', data);
  
  removeAttachmentFromMessage(data.message_id, data.attachment_id);
});

// 6. Message reaction
channel.bind('message-reaction', (data) => {
  console.log('👍 Reaction:', data);
  
  if (data.action === 'add') {
    addReactionToMessage(data.message_id, {
      emoji: data.emoji,
      staff: data.staff
    });
  } else if (data.action === 'remove') {
    removeReactionFromMessage(data.message_id, data.emoji, data.staff.id);
  }
});
```

### Helper Functions for UI Updates

```javascript
function addMessageToUI(message) {
  setMessages(prev => [...prev, message]);
  scrollToBottom();
}

function updateMessageInUI(messageId, updates) {
  setMessages(prev => prev.map(msg =>
    msg.id === messageId ? { ...msg, ...updates } : msg
  ));
}

function removeMessageFromUI(messageId) {
  setMessages(prev => prev.filter(msg => msg.id !== messageId));
}

function updateMessageAttachments(messageId, attachments) {
  setMessages(prev => prev.map(msg =>
    msg.id === messageId ? { ...msg, attachments: [...(msg.attachments || []), ...attachments] } : msg
  ));
}

function removeAttachmentFromMessage(messageId, attachmentId) {
  setMessages(prev => prev.map(msg =>
    msg.id === messageId
      ? { ...msg, attachments: (msg.attachments || []).filter(att => att.id !== attachmentId) }
      : msg
  ));
}
```

---

## 📱 FCM Push Notifications

### Setup FCM (Firebase Cloud Messaging)

```javascript
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

// Initialize Firebase
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  projectId: "YOUR_PROJECT_ID",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// Request permission and get token
async function requestNotificationPermission() {
  try {
    const permission = await Notification.requestPermission();
    
    if (permission === 'granted') {
      const token = await getToken(messaging, {
        vapidKey: 'YOUR_VAPID_KEY'
      });
      
      // Send token to your backend
      await saveTokenToBackend(token);
      
      console.log('FCM token:', token);
    }
  } catch (error) {
    console.error('Failed to get FCM token:', error);
  }
}

// Handle incoming messages
onMessage(messaging, (payload) => {
  console.log('📱 FCM notification received:', payload);
  
  const { title, body } = payload.notification;
  const { type, conversation_id, message_id } = payload.data;
  
  // Show browser notification
  if ('Notification' in window && Notification.permission === 'granted') {
    const notification = new Notification(title, {
      body: body,
      icon: '/icon.png',
      badge: '/badge.png',
      data: { conversation_id, message_id }
    });
    
    notification.onclick = () => {
      window.focus();
      // Navigate to conversation
      navigateToConversation(conversation_id);
    };
  }
});
```

### Notification Types

#### 1. New Text Message
```json
{
  "notification": {
    "title": "💬 Jane Smith",
    "body": "Hello team! Ready for the shift?"
  },
  "data": {
    "type": "staff_chat_message",
    "conversation_id": "45",
    "message_id": "234",
    "sender_id": "5",
    "hotel_slug": "hotel-killarney",
    "click_action": "/staff-chat/hotel-killarney/conversation/45"
  }
}
```

#### 2. Reply to Your Message
```json
{
  "notification": {
    "title": "💬 Jane Smith replied",
    "body": "Yes, I'm ready!"
  },
  "data": {
    "type": "staff_chat_reply",
    "conversation_id": "45",
    "message_id": "236",
    "reply_to_message_id": "234",
    "priority": "high"
  }
}
```

#### 3. @Mention Notification
```json
{
  "notification": {
    "title": "@️⃣ Jane Smith mentioned you",
    "body": "Hey @John can you check this?"
  },
  "data": {
    "type": "staff_chat_mention",
    "conversation_id": "45",
    "message_id": "235",
    "priority": "high"
  }
}
```

#### 4. File Shared
```json
{
  "notification": {
    "title": "📷 Jane Smith",
    "body": "Sent 3 image(s)"
  },
  "data": {
    "type": "staff_chat_file",
    "conversation_id": "45",
    "message_id": "235",
    "file_count": "3",
    "file_types": ["image", "image", "image"]
  }
}
```

#### 5. Message Deleted (if you were mentioned)
```json
{
  "notification": {
    "title": "🗑️ Message deleted",
    "body": "A message you were mentioned in was deleted"
  },
  "data": {
    "type": "staff_chat_deleted",
    "conversation_id": "45",
    "message_id": "234"
  }
}
```

### Handle Notification Click

```javascript
// Handle notification click (when app is in background)
navigator.serviceWorker.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'notification-click') {
    const { conversation_id, message_id } = event.data;
    
    // Navigate to the conversation
    window.location.href = `/staff-chat/conversation/${conversation_id}`;
    
    // Optionally scroll to specific message
    if (message_id) {
      setTimeout(() => {
        scrollToMessage(message_id);
      }, 500);
    }
  }
});
```

### Important FCM Rules:
- ✅ **Only recipients** receive notifications (never the sender)
- ✅ High priority for **@mentions** and **replies to your messages**
- ✅ Normal priority for **general messages**
- ✅ Notifications include **click actions** to navigate to conversation

---

## 📝 Complete Example: Chat Component

```javascript
import React, { useState, useEffect, useRef } from 'react';
import Pusher from 'pusher-js';

function StaffChatWindow({ conversationId, hotelSlug, authToken, currentUserId }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [replyTo, setReplyTo] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const channelRef = useRef(null);
  const pusherRef = useRef(null);
  
  useEffect(() => {
    loadMessages();
    setupPusher();
    
    return () => {
      if (channelRef.current) {
        pusherRef.current.unsubscribe(channelRef.current.name);
      }
    };
  }, [conversationId]);
  
  function setupPusher() {
    pusherRef.current = new Pusher('YOUR_KEY', { cluster: 'YOUR_CLUSTER' });
    const channelName = `${hotelSlug}-staff-conversation-${conversationId}`;
    channelRef.current = pusherRef.current.subscribe(channelName);
    
    // Listen for new messages
    channelRef.current.bind('new-message', (data) => {
      setMessages(prev => [...prev, {
        id: data.message_id,
        message: data.message,
        sender: data.sender,
        timestamp: data.timestamp,
        reply_to_message: data.reply_to || null,
        attachments: data.attachments || [],
        reactions: [],
        is_deleted: false
      }]);
    });
    
    // Listen for deleted messages
    channelRef.current.bind('message-deleted', (data) => {
      if (data.hard_delete) {
        setMessages(prev => prev.filter(msg => msg.id !== data.message_id));
      } else {
        setMessages(prev => prev.map(msg =>
          msg.id === data.message_id
            ? { ...msg, message: data.message.message, is_deleted: true }
            : msg
        ));
      }
    });
  }
  
  async function loadMessages() {
    const response = await fetch(
      `/api/staff_chat/${hotelSlug}/conversations/${conversationId}/messages/`,
      { headers: { 'Authorization': `Bearer ${authToken}` } }
    );
    const data = await response.json();
    setMessages(data.messages || []);
  }
  
  async function handleSend(e) {
    e.preventDefault();
    
    if (selectedFiles.length > 0) {
      // Send with files
      if (replyTo) {
        await replyWithFiles(conversationId, replyTo.id, selectedFiles, newMessage);
      } else {
        await uploadFilesWithMessage(conversationId, selectedFiles, newMessage);
      }
    } else if (newMessage.trim()) {
      // Send text only
      if (replyTo) {
        await replyToMessage(conversationId, replyTo.id, newMessage);
      } else {
        await sendMessage(conversationId, newMessage);
      }
    }
    
    // Clear inputs
    setNewMessage('');
    setReplyTo(null);
    setSelectedFiles([]);
  }
  
  async function handleDelete(messageId, messageText) {
    if (confirm(`Delete message: "${messageText}"?`)) {
      await deleteMessage(messageId);
    }
  }
  
  return (
    <div className="chat-window">
      {/* Messages */}
      <div className="messages-container">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.sender.id === currentUserId ? 'my-message' : 'their-message'}`}>
            {/* Sender info */}
            {msg.sender.id !== currentUserId && (
              <div className="sender-info">
                <img src={msg.sender.profile_image} alt="" />
                <span>{msg.sender.first_name}</span>
              </div>
            )}
            
            {/* Reply preview */}
            {msg.reply_to_message && (
              <div className="reply-preview">
                <strong>{msg.reply_to_message.sender.first_name}:</strong>
                <span>{msg.reply_to_message.message}</span>
              </div>
            )}
            
            {/* Message content */}
            <div className={`message-content ${msg.is_deleted ? 'deleted' : ''}`}>
              {msg.message}
              {msg.is_edited && !msg.is_deleted && <span className="edited">(edited)</span>}
            </div>
            
            {/* Attachments */}
            {msg.attachments?.map(att => (
              <div key={att.id} className="attachment">
                {att.file_type === 'image' ? (
                  <img src={att.file_url} alt={att.file_name} />
                ) : (
                  <a href={att.file_url} target="_blank">📎 {att.file_name}</a>
                )}
              </div>
            ))}
            
            {/* Actions */}
            {!msg.is_deleted && (
              <div className="message-actions">
                <button onClick={() => setReplyTo(msg)}>↩️ Reply</button>
                {msg.sender.id === currentUserId && (
                  <button onClick={() => handleDelete(msg.id, msg.message)}>🗑️ Delete</button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Input area */}
      <form onSubmit={handleSend} className="message-input">
        {/* Replying to indicator */}
        {replyTo && (
          <div className="replying-to">
            <span>Replying to {replyTo.sender.first_name}: {replyTo.message}</span>
            <button type="button" onClick={() => setReplyTo(null)}>✕</button>
          </div>
        )}
        
        {/* File preview */}
        {selectedFiles.length > 0 && (
          <div className="selected-files">
            {selectedFiles.map((file, i) => (
              <div key={i}>{file.name}</div>
            ))}
          </div>
        )}
        
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder={replyTo ? "Type your reply..." : "Type a message..."}
        />
        
        <input
          type="file"
          multiple
          onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
          style={{ display: 'none' }}
          id="fileInput"
        />
        
        <label htmlFor="fileInput">📎</label>
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
```

---

## ✅ Summary

### What Users Can Do:
1. ✅ **Send** text messages
2. ✅ **Send** messages with files
3. ✅ **Reply** to any message (yours or others')
4. ✅ **Reply** with files
5. ✅ **Reply** to deleted messages
6. ✅ **Reply** to your own messages
7. ✅ **Share** any message to other conversations
8. ✅ **Delete** only your own messages (soft delete)
9. ✅ **Managers/Admins** can hard delete any message
10. ✅ **Real-time updates** via Pusher
11. ✅ **Push notifications** via FCM (recipients only)

### Delete Behavior:
- **Soft delete**: Shows "[Message deleted]" - can still be replied to
- **Hard delete**: Permanently removed from database (managers only)
- **With files**: Shows "[File deleted]" or "[Message and file(s) deleted]"
- **Only your messages**: Regular users can only delete their own
- **Real-time sync**: All participants see deletion instantly

### Real-Time (Pusher):
- ✅ New messages appear instantly
- ✅ Deletions sync across devices
- ✅ File uploads notify participants
- ✅ Reactions update in real-time

### Push Notifications (FCM):
- ✅ New message notifications
- ✅ Reply notifications (high priority)
- ✅ @Mention notifications (high priority)
- ✅ File share notifications
- ✅ Only recipients notified (never sender)

**Everything is production-ready!** 🚀
