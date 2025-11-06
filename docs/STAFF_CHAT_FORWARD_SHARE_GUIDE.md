# Staff Chat - Forward & Share Messages Guide

## 📤 Complete Guide to Forwarding Messages & Files

This guide covers how to **forward/share messages and files** to other staff members. The system uses **get-or-create** to prevent duplicate conversations.

---

## 🎯 Key Principles

### ✅ How Sharing Works:
1. ✅ **Select staff members** (not conversations)
2. ✅ **Get or create conversation** with selected staff
3. ✅ **Share actual files** (images display, not just text)
4. ✅ **No duplicate conversations** created (FIXED ✅)
5. ✅ Can share **same message multiple times** (same or different conversations)

### 🔄 Get-or-Create Behavior:
- If conversation with selected staff **exists** → Use existing ✅
- If conversation **doesn't exist** → Create new one ✅
- **1-on-1 conversations**: Always unique per staff pair ✅
- **Group conversations**: Unique by participant set ✅
- **Participant order doesn't matter**: [A, B, C] = [C, A, B] ✅

### 🐛 Fixed Issue (Nov 6, 2025):
**Problem**: Sharing to same people created duplicate conversations
- ❌ Groups (3+ people) always created new conversations
- ❌ 1-on-1 query counted participants incorrectly

**Solution**: Updated `get_or_create_conversation` in `staff_chat/models.py`
- ✅ Groups now check for existing conversations with same participants
- ✅ 1-on-1 query fixed: annotate count before filtering participants
- ✅ All tests passing - no more duplicates!

---

## 🔧 Backend API: Get or Create Conversation

### Endpoint

```
POST /api/staff_chat/{hotel_slug}/conversations/
```

### Request Body

```json
{
  "participant_ids": [5, 8, 12],  // Array of staff IDs (excluding yourself)
  "title": "Team Leaders"         // Optional: Only for groups
}
```

### Response

```json
{
  "id": 46,
  "title": "Team Leaders",
  "hotel": 1,
  "participants": [
    {
      "id": 3,
      "first_name": "John",
      "last_name": "Doe",
      "profile_image": "https://..."
    },
    {
      "id": 5,
      "first_name": "Jane",
      "last_name": "Smith",
      "profile_image": "https://..."
    }
  ],
  "created_at": "2025-11-06T10:00:00Z",
  "updated_at": "2025-11-06T10:00:00Z",
  "last_message": null,
  "unread_count": 0
}
```

### HTTP Status Codes

- **201 Created**: New conversation was created
- **200 OK**: Existing conversation was returned
- **400 Bad Request**: Invalid participants or empty list
- **403 Forbidden**: Not authorized
- **404 Not Found**: Staff profile not found

---

## 💬 Forward Text Messages

### Get or Create Conversation

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
        title: title  // Optional group title
      })
    }
  );
  
  const data = await response.json();
  
  // Check if created or existing
  if (response.status === 201) {
    console.log('✨ New conversation created');
  } else if (response.status === 200) {
    console.log('♻️ Using existing conversation');
  }
  
  return data;
}
```

### Forward Text Message to Staff

```javascript
async function forwardMessageToStaff(originalMessage, staffIds, additionalText = '') {
  // Step 1: Get or create conversation with selected staff
  const conversation = await getOrCreateConversation(staffIds);
  
  // Step 2: Format forwarded message
  let messageText = `📤 Forwarded from ${originalMessage.sender.first_name}:\n\n"${originalMessage.message}"`;
  
  if (additionalText) {
    messageText += `\n\n${additionalText}`;
  }
  
  // Step 3: Send message to conversation
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/conversations/${conversation.id}/send-message/`,
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

// Example: Forward to one staff member
const originalMsg = {
  id: 234,
  message: "Room 101 needs attention",
  sender: { first_name: "John" }
};

await forwardMessageToStaff(originalMsg, [5], "FYI - please handle this");

// Example: Forward to multiple staff (group)
await forwardMessageToStaff(originalMsg, [5, 8, 12], "Team, please review");
```

---

## 📸 Forward Messages with Files (Images & Documents)

**IMPORTANT**: When forwarding files, you must **download and re-upload** them so the actual images/documents appear in the target conversation.

### Forward Message with Files

```javascript
async function forwardMessageWithFiles(originalMessage, staffIds, additionalText = '') {
  // Step 1: Get or create conversation (NO DUPLICATES!)
  const conversation = await getOrCreateConversation(staffIds);
  
  // Step 2: Format message text
  let messageText = `📤 Forwarded from ${originalMessage.sender.first_name}:\n\n"${originalMessage.message}"`;
  
  if (additionalText) {
    messageText += `\n\n${additionalText}`;
  }
  
  // Step 3: If message has files, download and re-upload them
  if (originalMessage.attachments && originalMessage.attachments.length > 0) {
    // Download files from Cloudinary URLs
    const filePromises = originalMessage.attachments.map(async (att) => {
      const response = await fetch(att.file_url);
      const blob = await response.blob();
      
      // Create File object with original name and type
      return new File([blob], att.file_name, { type: att.mime_type });
    });
    
    const files = await Promise.all(filePromises);
    
    // Upload files to target conversation
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    formData.append('message', messageText);
    
    const uploadResponse = await fetch(
      `/api/staff_chat/${hotelSlug}/conversations/${conversation.id}/upload/`,
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
    return await sendMessage(conversation.id, messageText);
  }
}

// Helper: Send text message
async function sendMessage(conversationId, messageText) {
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/conversations/${conversationId}/send-message/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: messageText })
    }
  );
  
  return await response.json();
}
```

### Example: Forward Image to Staff

```javascript
const messageWithPhoto = {
  id: 235,
  message: "Room inspection photo",
  sender: { first_name: "John" },
  attachments: [
    {
      id: 67,
      file_name: "room_101.jpg",
      file_url: "https://res.cloudinary.com/.../room_101.jpg",
      mime_type: "image/jpeg",
      file_type: "image"
    }
  ]
};

// Forward to maintenance staff
await forwardMessageWithFiles(messageWithPhoto, [5], "Please check this issue");

// Recipients will see:
// ✅ Your forwarded message text
// ✅ The actual image (displayed inline)
// ✅ Original context from John
```

---

## ♻️ Share Same Message Multiple Times

**✅ You can forward the same message multiple times!**

### Share to Different Staff Members

```javascript
const inspectionPhoto = {
  message: "Daily inspection complete",
  sender: { first_name: "John" },
  attachments: [{ file_url: "https://...", file_name: "room_101.jpg", mime_type: "image/jpeg" }]
};

// Forward to Manager
await forwardMessageWithFiles(inspectionPhoto, [5], "For your review");

// Forward to Maintenance
await forwardMessageWithFiles(inspectionPhoto, [8], "Action needed");

// Forward to another colleague
await forwardMessageWithFiles(inspectionPhoto, [12], "FYI");

// ✅ Each staff member gets the actual image
// ✅ Each gets their own conversation (or existing one is used)
// ✅ No duplicate conversations created
```

### Share to Same Staff Multiple Times

**✅ You can forward to the SAME staff member multiple times!**

```javascript
// First forward
await forwardMessageWithFiles(inspectionPhoto, [5], "Initial inspection");

// Second forward (SAME STAFF, SAME CONVERSATION)
await forwardMessageWithFiles(inspectionPhoto, [5], "Updated status");

// Third forward (SAME CONVERSATION AGAIN)
await forwardMessageWithFiles(inspectionPhoto, [5], "Final review");

// ✅ All forwards go to the SAME conversation
// ✅ Each forward creates a NEW message
// ✅ Image is uploaded each time (new attachment)
// ✅ No conversation duplication
```

---

## 🎨 Forward Message Modal (Complete UI)

### Full React Component

```javascript
import React, { useState, useEffect } from 'react';

function ForwardMessageModal({ message, onClose, currentUserId, hotelSlug, authToken }) {
  const [staffList, setStaffList] = useState([]);
  const [selectedStaff, setSelectedStaff] = useState([]);
  const [additionalText, setAdditionalText] = useState('');
  const [forwarding, setForwarding] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  useEffect(() => {
    loadStaff();
  }, []);
  
  async function loadStaff() {
    // Load all active staff in hotel
    const response = await fetch(
      `/api/staff_chat/${hotelSlug}/staff/`,
      { headers: { 'Authorization': `Bearer ${authToken}` } }
    );
    const data = await response.json();
    
    // Filter out current user
    setStaffList(data.filter(staff => staff.id !== currentUserId && staff.is_active));
  }
  
  function toggleStaff(staffId) {
    setSelectedStaff(prev => 
      prev.includes(staffId)
        ? prev.filter(id => id !== staffId)
        : [...prev, staffId]
    );
  }
  
  async function handleForward() {
    if (selectedStaff.length === 0) {
      alert('Please select at least one staff member');
      return;
    }
    
    setForwarding(true);
    try {
      // Forward message (with or without files)
      if (message.attachments && message.attachments.length > 0) {
        await forwardMessageWithFiles(message, selectedStaff, additionalText);
      } else {
        await forwardMessageToStaff(message, selectedStaff, additionalText);
      }
      
      alert('Message forwarded successfully!');
      onClose();
    } catch (error) {
      console.error('Failed to forward message:', error);
      alert('Failed to forward message. Please try again.');
    } finally {
      setForwarding(false);
    }
  }
  
  // Filter staff by search
  const filteredStaff = staffList.filter(staff =>
    `${staff.first_name} ${staff.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
    staff.role?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  return (
    <div className="forward-modal-overlay" onClick={onClose}>
      <div className="forward-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>📤 Forward Message</h3>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>
        
        {/* Preview of message being forwarded */}
        <div className="message-preview">
          <div className="preview-label">Forwarding:</div>
          <div className="preview-content">
            <strong>{message.sender.first_name}:</strong>
            <p>{message.message}</p>
            {message.attachments?.length > 0 && (
              <div className="attachments-info">
                📎 {message.attachments.length} file(s) attached
                {message.attachments.map(att => (
                  <div key={att.id} className="file-badge">
                    {att.file_type === 'image' ? '🖼️' : '📄'} {att.file_name}
                  </div>
                ))}
              </div>
            )}
          </div>
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
          <label>Forward to:</label>
          <div className="staff-list">
            {filteredStaff.length === 0 ? (
              <div className="no-results">No staff members found</div>
            ) : (
              filteredStaff.map(staff => (
                <div
                  key={staff.id}
                  className={`staff-item ${selectedStaff.includes(staff.id) ? 'selected' : ''}`}
                  onClick={() => toggleStaff(staff.id)}
                >
                  <img 
                    src={staff.profile_image || '/default-avatar.png'} 
                    alt="" 
                    className="staff-avatar" 
                  />
                  <div className="staff-info">
                    <span className="staff-name">
                      {staff.first_name} {staff.last_name}
                    </span>
                    <span className="staff-role">{staff.role || 'Staff'}</span>
                  </div>
                  {selectedStaff.includes(staff.id) && (
                    <span className="selected-icon">✓</span>
                  )}
                </div>
              ))
            )}
          </div>
          
          {/* Selected count */}
          {selectedStaff.length > 0 && (
            <div className="selected-count">
              ✓ {selectedStaff.length} staff member{selectedStaff.length !== 1 ? 's' : ''} selected
            </div>
          )}
        </div>
        
        {/* Additional message */}
        <div className="additional-message">
          <label>Add your message (optional):</label>
          <textarea
            value={additionalText}
            onChange={(e) => setAdditionalText(e.target.value)}
            placeholder="Add context or instructions..."
            rows="3"
          />
        </div>
        
        {/* Actions */}
        <div className="modal-actions">
          <button onClick={onClose} disabled={forwarding} className="cancel-btn">
            Cancel
          </button>
          <button 
            onClick={handleForward} 
            disabled={forwarding || selectedStaff.length === 0}
            className="forward-btn"
          >
            {forwarding ? (
              <>⏳ Forwarding...</>
            ) : (
              <>📤 Forward {selectedStaff.length > 0 ? `to ${selectedStaff.length}` : ''}</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ForwardMessageModal;
```

### CSS Styling

```css
/* Modal overlay */
.forward-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Modal content */
.forward-modal-content {
  background: white;
  border-radius: 16px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Modal header */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}

.close-btn:hover {
  background: #f0f0f0;
}

/* Message preview */
.message-preview {
  padding: 16px 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.preview-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
  text-transform: uppercase;
}

.preview-content {
  background: white;
  padding: 12px;
  border-radius: 8px;
  border-left: 3px solid #2196f3;
}

.preview-content strong {
  color: #2196f3;
  font-size: 14px;
}

.preview-content p {
  margin: 4px 0;
  font-size: 14px;
  color: #333;
}

.attachments-info {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  font-size: 12px;
  color: #666;
}

.file-badge {
  display: inline-block;
  background: #e3f2fd;
  padding: 4px 8px;
  border-radius: 4px;
  margin: 4px 4px 0 0;
  font-size: 11px;
}

/* Search staff */
.staff-search {
  padding: 16px 24px;
}

.staff-search input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.staff-search input:focus {
  outline: none;
  border-color: #2196f3;
}

/* Staff selector */
.staff-selector {
  padding: 0 24px;
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.staff-selector label {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.staff-list {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  max-height: 250px;
}

.staff-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.staff-item:last-child {
  border-bottom: none;
}

.staff-item:hover {
  background: #f5f5f5;
}

.staff-item.selected {
  background: #e3f2fd;
  border-left: 4px solid #2196f3;
}

.staff-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e0e0e0;
}

.staff-item.selected .staff-avatar {
  border-color: #2196f3;
}

.staff-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.staff-name {
  font-weight: 500;
  font-size: 14px;
  color: #333;
}

.staff-role {
  font-size: 12px;
  color: #666;
}

.selected-icon {
  color: #2196f3;
  font-weight: bold;
  font-size: 20px;
}

.selected-count {
  margin-top: 12px;
  font-size: 13px;
  color: #2196f3;
  font-weight: 500;
  padding: 8px 12px;
  background: #e3f2fd;
  border-radius: 6px;
  text-align: center;
}

.no-results {
  padding: 24px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

/* Additional message */
.additional-message {
  padding: 16px 24px;
  border-top: 1px solid #e0e0e0;
}

.additional-message label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.additional-message textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s;
}

.additional-message textarea:focus {
  outline: none;
  border-color: #2196f3;
}

/* Modal actions */
.modal-actions {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
}

.modal-actions button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: white;
  color: #666;
  border: 1px solid #ddd;
}

.cancel-btn:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #ccc;
}

.forward-btn {
  background: #2196f3;
  color: white;
}

.forward-btn:hover:not(:disabled) {
  background: #1976d2;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

.modal-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

## 📱 Usage in Chat Component

### Add Forward Button to Messages

```javascript
function MessageComponent({ message, currentUserId }) {
  const [showForwardModal, setShowForwardModal] = useState(false);
  
  return (
    <>
      <div className="message">
        {/* ... message content ... */}
        
        {/* Forward button */}
        {!message.is_deleted && (
          <button 
            onClick={() => setShowForwardModal(true)}
            className="forward-btn"
            title="Forward message"
          >
            📤 Forward
          </button>
        )}
      </div>
      
      {/* Forward modal */}
      {showForwardModal && (
        <ForwardMessageModal
          message={message}
          onClose={() => setShowForwardModal(false)}
          currentUserId={currentUserId}
          hotelSlug={hotelSlug}
          authToken={authToken}
        />
      )}
    </>
  );
}
```

---

## ✅ Summary

### What This Guide Covers:
1. ✅ **Get-or-create conversation** (no duplicates) - **FIXED ✅**
2. ✅ **Forward text messages** to staff members
3. ✅ **Forward messages with files** (actual images/documents)
4. ✅ **Forward same message multiple times** (allowed)
5. ✅ **Complete UI component** with staff selection
6. ✅ **Real file uploads** (not just text links)

### Key Benefits:
- ✅ **No duplicate conversations** - properly fixed in backend
- ✅ **Actual files display** - images show inline, documents are attachments
- ✅ **Unlimited forwarding** - same message to same/different staff
- ✅ **Clean UX** - select people, not conversations
- ✅ **Search functionality** - find staff easily
- ✅ **Tested and verified** - all scenarios passing

### Flow:
1. User clicks "Forward" on a message
2. Modal opens with staff list
3. User selects one or more staff members
4. System **gets or creates** conversation (no duplicates!)
5. Files are downloaded and re-uploaded (if any)
6. Message appears in target conversation
7. Recipients see actual images/documents

### Technical Details (Backend):
**File**: `staff_chat/models.py` → `get_or_create_conversation()`

**Fix Applied (Nov 6, 2025)**:
- **1-on-1 conversations**: Query fixed to annotate participant count before filtering
- **Group conversations**: Added check for existing conversations with same participant set
- **Participant order**: Uses set comparison, so order doesn't matter

**Test Results**: ✅ All pass
- ✅ 1-on-1: No duplicates when sharing to same person
- ✅ Group (3+): No duplicates when sharing to same group
- ✅ Different order: Finds same conversation regardless of participant order

**Everything production-ready!** 🚀
