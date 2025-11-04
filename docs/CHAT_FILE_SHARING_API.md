# Chat File Sharing & Message CRUD API Documentation

## Overview
This document describes the enhanced chat functionality including file sharing, message editing, deletion, and reply features for the HotelMate chat system.

## Table of Contents
1. [File Attachments](#file-attachments)
2. [Message CRUD Operations](#message-crud-operations)
3. [Message Reply Feature](#message-reply-feature)
4. [Real-time Updates](#real-time-updates)
5. [Frontend Integration Examples](#frontend-integration-examples)

---

## File Attachments

### Supported File Types

#### Images
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`
- Maximum size: 10MB per file
- Auto-detected as `image` type

#### PDFs
- `.pdf`
- Maximum size: 10MB
- Auto-detected as `pdf` type

#### Documents
- `.doc`, `.docx` (Word documents)
- `.xls`, `.xlsx` (Excel spreadsheets)
- `.txt` (Text files)
- `.csv` (CSV files)
- Maximum size: 10MB per file
- Auto-detected as `document` type

### Upload File Attachment

**Endpoint:** `POST /chat/<hotel_slug>/conversations/<conversation_id>/upload-attachment/`

**Authentication:** AllowAny (Both staff and guests can upload)

**Content-Type:** `multipart/form-data`

**Parameters:**
- `files` (required): One or more files to upload
- `message` (optional): Text message to accompany the files
- `message_id` (optional): Attach files to an existing message

**Request Example:**
```javascript
const formData = new FormData();
formData.append('files', file1);
formData.append('files', file2);
formData.append('message', 'Here are the documents you requested');

fetch('/chat/hotel-royal/conversations/123/upload-attachment/', {
  method: 'POST',
  body: formData,
  headers: {
    'Authorization': 'Token your-auth-token' // If staff
  }
})
```

**Response (Success):**
```json
{
  "success": true,
  "message": {
    "id": 456,
    "conversation": 123,
    "room": 101,
    "sender_type": "staff",
    "message": "Here are the documents you requested",
    "timestamp": "2025-11-04T14:30:00Z",
    "attachments": [
      {
        "id": 78,
        "file_url": "https://example.com/media/chat/hotel-royal/room_101/2025/11/04/invoice.pdf",
        "file_name": "invoice.pdf",
        "file_type": "pdf",
        "file_size": 245760,
        "file_size_display": "240.0 KB",
        "mime_type": "application/pdf",
        "uploaded_at": "2025-11-04T14:30:00Z"
      },
      {
        "id": 79,
        "file_url": "https://example.com/media/chat/hotel-royal/room_101/2025/11/04/receipt.jpg",
        "file_name": "receipt.jpg",
        "file_type": "image",
        "file_size": 156789,
        "file_size_display": "153.1 KB",
        "mime_type": "image/jpeg",
        "thumbnail_url": "https://example.com/media/chat/hotel-royal/room_101/2025/11/04/receipt_thumb.jpg",
        "uploaded_at": "2025-11-04T14:30:00Z"
      }
    ],
    "has_attachments": true,
    "is_edited": false,
    "is_deleted": false
  },
  "attachments": [...],
  "warnings": [] // Any files that were rejected
}
```

**Response (Error):**
```json
{
  "error": "No valid files uploaded",
  "details": [
    "document.exe: File type not allowed",
    "large_file.pdf: File too large (max 10MB)"
  ]
}
```

### Delete File Attachment

**Endpoint:** `DELETE /chat/attachments/<attachment_id>/delete/`

**Authentication:** AllowAny (Only message sender can delete)

**Response:**
```json
{
  "success": true,
  "attachment_id": 78,
  "message_id": 456
}
```

---

## Message CRUD Operations

### Update/Edit Message

**Endpoint:** `PATCH /chat/messages/<message_id>/update/`

**Authentication:** AllowAny (Only message sender can edit)

**Permissions:**
- Staff can only edit their own messages
- Guests can edit their own messages
- Cannot edit deleted messages

**Request:**
```json
{
  "message": "Updated message text here"
}
```

**Response:**
```json
{
  "success": true,
  "message": {
    "id": 456,
    "message": "Updated message text here",
    "is_edited": true,
    "edited_at": "2025-11-04T14:35:00Z",
    "timestamp": "2025-11-04T14:30:00Z",
    // ... other fields
  }
}
```

**Error Responses:**
```json
// Empty message
{
  "error": "Message cannot be empty"
}

// Editing someone else's message
{
  "error": "You can only edit your own messages"
}

// Editing deleted message
{
  "error": "Cannot edit a deleted message"
}
```

### Delete Message

**Endpoint:** `DELETE /chat/messages/<message_id>/delete/`

**Authentication:** AllowAny (Only message sender can delete)

**Query Parameters:**
- `hard_delete=true` (optional): Permanently delete message (managers/admins only)

**Permissions:**
- **Soft Delete:** Any user can soft-delete their own messages
  - Message text becomes "[Message deleted]"
  - Message still exists in database with `is_deleted=true`
  - Attachments are preserved but hidden
  
- **Hard Delete:** Only staff with manager/admin role
  - Permanently removes message from database
  - Deletes all associated attachments

**Request Examples:**
```javascript
// Soft delete (default)
fetch('/chat/messages/456/delete/', {
  method: 'DELETE'
})

// Hard delete (admin only)
fetch('/chat/messages/456/delete/?hard_delete=true', {
  method: 'DELETE',
  headers: {
    'Authorization': 'Token admin-token'
  }
})
```

**Response (Soft Delete):**
```json
{
  "success": true,
  "hard_delete": false,
  "message": {
    "id": 456,
    "message": "[Message deleted]",
    "is_deleted": true,
    "deleted_at": "2025-11-04T14:40:00Z",
    // ... other fields
  }
}
```

**Response (Hard Delete):**
```json
{
  "success": true,
  "hard_delete": true,
  "message_id": 456
}
```

---

## Message Reply Feature

### Reply to a Message

When sending a new message, include the `reply_to` field to create a reply thread.

**Endpoint:** `POST /chat/<hotel_slug>/conversations/<conversation_id>/messages/send/`

**Request:**
```json
{
  "message": "Yes, I can help with that!",
  "reply_to": 455  // ID of message being replied to
}
```

**Response:**
```json
{
  "conversation_id": 123,
  "message": {
    "id": 457,
    "message": "Yes, I can help with that!",
    "reply_to": 455,
    "reply_to_message": {
      "id": 455,
      "message": "Can someone help me with checkout?",
      "sender_type": "guest",
      "sender_name": "Guest",
      "timestamp": "2025-11-04T14:00:00Z"
    },
    // ... other fields
  }
}
```

### Frontend Display
Show replied message above the new message:
```
┌─────────────────────────────────────┐
│ ↩️ Replying to Guest:               │
│ "Can someone help me with checkout?"│
├─────────────────────────────────────┤
│ Yes, I can help with that!          │
└─────────────────────────────────────┘
```

---

## Real-time Updates

All message operations trigger Pusher events for real-time synchronization.

### Pusher Events

#### Message Updated
**Channel:** `{hotel_slug}-conversation-{conversation_id}-chat`
**Event:** `message-updated`

```javascript
pusher.subscribe(`hotel-royal-conversation-123-chat`)
  .bind('message-updated', (data) => {
    // data contains full updated message object
    updateMessageInUI(data);
  });
```

#### Message Deleted
**Channel:** `{hotel_slug}-conversation-{conversation_id}-chat`
**Event:** `message-deleted`

```javascript
.bind('message-deleted', (data) => {
  if (data.hard_delete) {
    removeMessageFromUI(data.message_id);
  } else {
    // Soft delete - show "[Message deleted]"
    updateMessageInUI(data.message);
  }
});
```

#### Attachment Deleted
**Channel:** `{hotel_slug}-conversation-{conversation_id}-chat`
**Event:** `attachment-deleted`

```javascript
.bind('attachment-deleted', (data) => {
  removeAttachmentFromUI(data.message_id, data.attachment_id);
});
```

#### New Message with Attachment
**Channel:** `{hotel_slug}-conversation-{conversation_id}-chat`
**Event:** `new-message`

```javascript
.bind('new-message', (data) => {
  if (data.has_attachments) {
    renderMessageWithAttachments(data);
  } else {
    renderTextMessage(data);
  }
});
```

---

## Frontend Integration Examples

### 1. File Upload Component (React)

```jsx
import React, { useState } from 'react';

function FileUploadButton({ conversationId, hotelSlug, onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    
    // Validate file types
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];
    
    const validFiles = files.filter(file => {
      if (file.size > 10 * 1024 * 1024) {
        alert(`${file.name} is too large (max 10MB)`);
        return false;
      }
      if (!allowedTypes.includes(file.type)) {
        alert(`${file.name} type not supported`);
        return false;
      }
      return true;
    });
    
    setSelectedFiles(validFiles);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    
    setUploading(true);
    const formData = new FormData();
    
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });
    
    formData.append('message', 'File shared');

    try {
      const response = await fetch(
        `/chat/${hotelSlug}/conversations/${conversationId}/upload-attachment/`,
        {
          method: 'POST',
          body: formData,
          headers: {
            'Authorization': `Token ${localStorage.getItem('authToken')}`
          }
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        onUploadComplete(data.message);
        setSelectedFiles([]);
      } else {
        alert(`Upload failed: ${data.error}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload files');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        multiple
        onChange={handleFileSelect}
        accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt"
        style={{ display: 'none' }}
        id="file-upload"
      />
      
      <label htmlFor="file-upload">
        <button type="button" onClick={() => document.getElementById('file-upload').click()}>
          📎 Attach Files
        </button>
      </label>
      
      {selectedFiles.length > 0 && (
        <div>
          <p>{selectedFiles.length} file(s) selected</p>
          <button onClick={handleUpload} disabled={uploading}>
            {uploading ? 'Uploading...' : 'Send Files'}
          </button>
        </div>
      )}
    </div>
  );
}

export default FileUploadButton;
```

### 2. Message Display Component

```jsx
function ChatMessage({ message, currentUser, onEdit, onDelete }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.message);
  
  const isOwnMessage = (
    (currentUser.type === 'staff' && message.sender_type === 'staff' && 
     message.staff === currentUser.id) ||
    (currentUser.type === 'guest' && message.sender_type === 'guest')
  );

  const handleEdit = async () => {
    await onEdit(message.id, editText);
    setIsEditing(false);
  };

  return (
    <div className={`message ${message.sender_type}`}>
      {/* Reply thread */}
      {message.reply_to_message && (
        <div className="reply-reference">
          <span>↩️ Reply to {message.reply_to_message.sender_name}:</span>
          <p>"{message.reply_to_message.message}"</p>
        </div>
      )}
      
      {/* Message content */}
      {isEditing ? (
        <div>
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
          />
          <button onClick={handleEdit}>Save</button>
          <button onClick={() => setIsEditing(false)}>Cancel</button>
        </div>
      ) : (
        <div>
          <p>{message.message}</p>
          {message.is_edited && <span className="edited-badge">✏️ Edited</span>}
          {message.is_deleted && <span className="deleted-badge">🗑️ Deleted</span>}
        </div>
      )}
      
      {/* Attachments */}
      {message.has_attachments && (
        <div className="attachments">
          {message.attachments.map(attachment => (
            <AttachmentDisplay
              key={attachment.id}
              attachment={attachment}
              canDelete={isOwnMessage}
              onDelete={() => onDelete(attachment.id)}
            />
          ))}
        </div>
      )}
      
      {/* Actions */}
      {isOwnMessage && !message.is_deleted && (
        <div className="message-actions">
          <button onClick={() => setIsEditing(true)}>Edit</button>
          <button onClick={() => onDelete(message.id)}>Delete</button>
        </div>
      )}
      
      <span className="timestamp">
        {new Date(message.timestamp).toLocaleTimeString()}
      </span>
    </div>
  );
}
```

### 3. Attachment Display Component

```jsx
function AttachmentDisplay({ attachment, canDelete, onDelete }) {
  const renderPreview = () => {
    switch (attachment.file_type) {
      case 'image':
        return (
          <img
            src={attachment.thumbnail_url || attachment.file_url}
            alt={attachment.file_name}
            onClick={() => window.open(attachment.file_url)}
            style={{ cursor: 'pointer', maxWidth: '200px' }}
          />
        );
      
      case 'pdf':
        return (
          <a href={attachment.file_url} target="_blank" rel="noopener noreferrer">
            📄 {attachment.file_name} ({attachment.file_size_display})
          </a>
        );
      
      case 'document':
        return (
          <a href={attachment.file_url} target="_blank" rel="noopener noreferrer">
            📝 {attachment.file_name} ({attachment.file_size_display})
          </a>
        );
      
      default:
        return (
          <a href={attachment.file_url} download>
            📎 {attachment.file_name} ({attachment.file_size_display})
          </a>
        );
    }
  };

  return (
    <div className="attachment-item">
      {renderPreview()}
      {canDelete && (
        <button onClick={() => onDelete(attachment.id)} className="delete-attachment">
          ✖️
        </button>
      )}
    </div>
  );
}
```

---

## Permission Matrix

| Action | Guest | Staff (Own) | Staff (Other) | Admin/Manager |
|--------|-------|-------------|---------------|---------------|
| Upload file | ✅ | ✅ | ✅ | ✅ |
| Edit own message | ✅ | ✅ | ❌ | ❌ |
| Soft delete own message | ✅ | ✅ | ❌ | ❌ |
| Hard delete any message | ❌ | ❌ | ❌ | ✅ |
| Delete own attachment | ✅ | ✅ | ❌ | ❌ |
| Reply to message | ✅ | ✅ | ✅ | ✅ |

---

## Database Schema Changes

### RoomMessage Model - New Fields
```python
is_edited = BooleanField(default=False)
edited_at = DateTimeField(null=True)
is_deleted = BooleanField(default=False)
deleted_at = DateTimeField(null=True)
reply_to = ForeignKey('self', null=True)
```

### New MessageAttachment Model
```python
message = ForeignKey(RoomMessage)
file = FileField(upload_to=message_attachment_path)
file_name = CharField(max_length=255)
file_type = CharField(choices=ATTACHMENT_TYPES)
file_size = PositiveIntegerField()
mime_type = CharField(max_length=100)
thumbnail = ImageField(null=True)  # For images
uploaded_at = DateTimeField(auto_now_add=True)
```

---

## Migration Required

Run these commands to apply the database changes:

```bash
python manage.py makemigrations chat
python manage.py migrate chat
```

---

## Testing Checklist

- [ ] Upload single image file
- [ ] Upload multiple files at once
- [ ] Upload PDF document
- [ ] Upload Word/Excel document
- [ ] Validate file size limit (10MB)
- [ ] Validate file type restrictions
- [ ] Edit own message
- [ ] Try to edit someone else's message (should fail)
- [ ] Soft delete own message
- [ ] Hard delete as admin
- [ ] Delete attachment
- [ ] Reply to a message
- [ ] Receive real-time Pusher updates for all operations
- [ ] Test as guest (no authentication)
- [ ] Test as staff (with authentication)

---

## Error Handling

### Common Error Codes

| Status | Error | Description |
|--------|-------|-------------|
| 400 | No files provided | No files in request |
| 400 | File too large | File exceeds 10MB |
| 400 | File type not allowed | Unsupported file extension |
| 400 | Message cannot be empty | Empty message text |
| 400 | Cannot edit a deleted message | Trying to edit deleted message |
| 403 | You can only edit your own messages | Permission denied |
| 403 | Only managers can hard delete | Not authorized for hard delete |
| 404 | Message not found | Invalid message ID |
| 404 | Attachment not found | Invalid attachment ID |

---

## Best Practices

1. **File Validation:** Always validate files on frontend before uploading
2. **Progress Indicators:** Show upload progress for better UX
3. **Image Optimization:** Consider compressing images before upload
4. **Error Display:** Show clear error messages to users
5. **Real-time Sync:** Subscribe to Pusher channels for instant updates
6. **Attachment Preview:** Show thumbnails for images, icons for documents
7. **Download Links:** Make files easily downloadable
8. **Edit History:** Consider storing edit history for audit purposes
9. **Soft Delete First:** Default to soft delete to allow recovery
10. **Permission Checks:** Always verify user permissions before operations

---

## Future Enhancements

- [ ] Auto-generate thumbnails for images
- [ ] Video file support
- [ ] Audio file support
- [ ] Drag-and-drop file upload
- [ ] Paste images from clipboard
- [ ] File upload progress bar
- [ ] Message reactions/emojis
- [ ] Message search including attachments
- [ ] Attachment gallery view
- [ ] Edit history tracking
- [ ] Message pinning
- [ ] Message forwarding
- [ ] Bulk operations (delete multiple messages)
