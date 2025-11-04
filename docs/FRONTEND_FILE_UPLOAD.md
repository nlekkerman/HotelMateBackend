# 📎 File Upload - Frontend Implementation Guide

## 🎉 Backend is Ready!

The backend now supports file and image uploads in chat between guests and staff. Files are automatically stored in **Cloudinary cloud storage** and return full CDN URLs.

**✅ What's Configured:**
- File upload endpoint ready
- Cloudinary storage configured
- File size validation (50MB max per file)
- File type validation (images, PDF, documents)
- Real-time Pusher notifications
- Multiple file uploads supported (no total limit)

---

## 🚀 Quick Implementation (3 Steps)

### Step 1: Add File Input to Chat

```jsx
<input
  type="file"
  multiple
  accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv"
  onChange={handleFileSelect}
  style={{ display: 'none' }}
  ref={fileInputRef}
/>

<button onClick={() => fileInputRef.current?.click()}>
  📎 Attach Files
</button>
```

### Step 2: Upload Files to Backend

```javascript
const uploadFiles = async (conversationId, files, messageText = "") => {
  const formData = new FormData();
  
  // Add files (required) - MUST use key "files" (plural)
  Array.from(files).forEach(file => {
    formData.append('files', file);  // ✅ "files" not "file"
  });
  
  // Optional: add message text
  if (messageText.trim()) {
    formData.append('message', messageText);
  }
  
  try {
    const response = await fetch(
      `${API_URL}/api/chat/${hotelSlug}/conversations/${conversationId}/upload-attachment/`,
      {
        method: 'POST',
        headers: {
          'Authorization': authToken ? `Token ${authToken}` : '',
          // ⚠️ IMPORTANT: DON'T set Content-Type header!
          // Browser automatically sets it with multipart boundary
        },
        body: formData
      }
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Upload failed');
    }
    
    const data = await response.json();
    console.log('✅ Upload successful:', data);
    return data;
    
  } catch (error) {
    console.error('❌ Upload error:', error);
    throw error;
  }
};
```

### Step 3: Display Attachments in Messages

```jsx
const MessageBubble = ({ message }) => {
  return (
    <div className="message">
      {/* Message text */}
      {message.message && <p>{message.message}</p>}
      
      {/* Attachments */}
      {message.attachments?.map(att => (
        <div key={att.id} className="attachment">
          {att.file_type === 'image' ? (
            // Show images inline
            <img 
              src={att.file_url} 
              alt={att.file_name}
              style={{ maxWidth: '300px', borderRadius: '8px' }}
              onClick={() => window.open(att.file_url, '_blank')}
            />
          ) : (
            // Show document with download button
            <div className="document">
              <span>📄 {att.file_name}</span>
              <span className="size">{att.file_size_display}</span>
              <a href={att.file_url} download={att.file_name}>
                ⬇️ Download
              </a>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
```

---

## 📡 API Endpoint

```
POST /api/chat/<hotel_slug>/conversations/<conversation_id>/upload-attachment/
```

### Request Format

**Content-Type**: `multipart/form-data` (automatic)

**Body Parameters**:
- `files`: Array of File objects (required)
- `message`: String - optional message text

### Response Format

**Success Response:**
```json
{
  "success": true,
  "message": {
    "id": 456,
    "conversation": 123,
    "room": 101,
    "sender_type": "staff",
    "message": "Here's the invoice",
    "timestamp": "2025-11-04T10:30:00Z",
    "attachments": [
      {
        "id": 789,
        "file_name": "invoice.pdf",
        "file_url": "https://res.cloudinary.com/your-cloud/image/upload/v123/chat/hotel-killarney/room_101/2025/11/04/invoice.pdf",
        "file_type": "pdf",
        "file_size": 245678,
        "file_size_display": "239.9 KB",
        "mime_type": "application/pdf",
        "thumbnail_url": null,
        "uploaded_at": "2025-11-04T10:30:00Z"
      }
    ],
    "has_attachments": true,
    "status": "delivered"
  },
  "attachments": [
    // Same as above
  ]
}
```

**Error Response:**
```json
{
  "error": "File too large (max 10MB)",
  "details": [
    "large-file.pdf: File too large (15.50MB, max 10MB)",
    "document.exe: File type '.exe' not allowed. Allowed: images, PDF, documents"
  ]
}
```

---

## 📋 File Constraints & Validation

### Backend Validation
- **Max size**: 50MB per file (enforced on backend)
- **Allowed types**: 
  - 📷 **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`
  - 📄 **PDF**: `.pdf`
  - 📝 **Documents**: `.doc`, `.docx`, `.xls`, `.xlsx`, `.txt`, `.csv`
- **Multiple files**: ✅ Yes, upload multiple files in one request
- **Security**: Filenames are sanitized, extensions validated

### Frontend Validation (Recommended)
Add client-side validation for better UX:

```javascript
const validateFile = (file) => {
  const maxSize = 50 * 1024 * 1024; // 50MB
  const allowedTypes = [
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
    'application/pdf',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain', 'text/csv'
  ];
  
  if (file.size > maxSize) {
    return { valid: false, error: `File too large (${(file.size / (1024*1024)).toFixed(2)}MB, max 50MB)` };
  }
  
  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: `File type not allowed: ${file.type}` };
  }
  
  return { valid: true };
};
```

---

## 🎨 Complete Chat Input Component

```jsx
import React, { useState, useRef } from 'react';

const ChatInput = ({ conversationId, hotelSlug, onMessageSent }) => {
  const [message, setMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const errors = [];
    
    // Validate each file
    const validFiles = files.filter(file => {
      // Check file size (50MB max per file)
      if (file.size > 50 * 1024 * 1024) {
        errors.push(`${file.name}: Too large (${(file.size / (1024*1024)).toFixed(2)}MB, max 50MB)`);
        return false;
      }
      
      // Check file type
      const allowedTypes = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
        'application/pdf',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain', 'text/csv'
      ];
      
      if (!allowedTypes.includes(file.type)) {
        errors.push(`${file.name}: File type not allowed`);
        return false;
      }
      
      return true;
    });
    
    if (errors.length > 0) {
      alert(errors.join('\n'));
    }
    
    setSelectedFiles([...selectedFiles, ...validFiles]);
    e.target.value = ''; // Reset input
  };

  const removeFile = (index) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index));
  };

  const handleSend = async () => {
    if (!message.trim() && selectedFiles.length === 0) return;

    setUploading(true);

    try {
      const formData = new FormData();
      
      // Add files
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });
      
      // Add message text
      if (message.trim()) {
        formData.append('message', message.trim());
      }

      const response = await fetch(
        `${API_URL}/api/chat/${hotelSlug}/conversations/${conversationId}/upload-attachment/`,
        {
          method: 'POST',
          headers: {
            'Authorization': localStorage.getItem('authToken') 
              ? `Token ${localStorage.getItem('authToken')}` 
              : '',
          },
          body: formData
        }
      );

      if (!response.ok) throw new Error('Upload failed');
      
      const data = await response.json();
      
      // Clear inputs
      setMessage('');
      setSelectedFiles([]);
      
      // Notify parent
      if (onMessageSent) onMessageSent(data.message);
      
    } catch (error) {
      console.error('Send error:', error);
      alert('Failed to send. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="chat-input-container">
      {/* File previews */}
      {selectedFiles.length > 0 && (
        <div className="file-previews">
          {selectedFiles.map((file, index) => (
            <div key={index} className="file-preview">
              {file.type.startsWith('image/') ? (
                <img 
                  src={URL.createObjectURL(file)} 
                  alt={file.name}
                  style={{ width: '60px', height: '60px', objectFit: 'cover' }}
                />
              ) : (
                <div className="file-icon">📄</div>
              )}
              <span className="file-name">{file.name}</span>
              <button onClick={() => removeFile(index)}>❌</button>
            </div>
          ))}
        </div>
      )}
      
      {/* Input row */}
      <div className="input-row">
        <input
          type="file"
          multiple
          accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv"
          onChange={handleFileSelect}
          ref={fileInputRef}
          style={{ display: 'none' }}
        />
        
        <button 
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="attach-btn"
        >
          📎
        </button>
        
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && !uploading && handleSend()}
          placeholder="Type a message..."
          disabled={uploading}
          className="message-input"
        />
        
        <button 
          onClick={handleSend} 
          disabled={uploading || (!message.trim() && selectedFiles.length === 0)}
          className="send-btn"
        >
          {uploading ? '⏳' : '📤'} Send
        </button>
      </div>
    </div>
  );
};

export default ChatInput;
```

---

## � Real-time Notifications (Pusher & FCM)

### Pusher Real-time Updates ✅

Messages with attachments come through the same Pusher events:

```javascript
// Listen for new messages (includes attachments)
pusher.subscribe(conversationChannel).bind('new-message', (data) => {
  console.log('New message:', data);
  
  // Check for attachments
  if (data.attachments && data.attachments.length > 0) {
    console.log('Message has attachments:', data.attachments);
    
    // Display notification: "User sent 3 files"
    data.attachments.forEach(att => {
      console.log(`- ${att.file_name} (${att.file_size_display})`);
    });
  }
  
  setMessages(prev => [...prev, data]);
});

// For staff listening to guest messages
pusher.subscribe(staffChannel).bind('new-guest-message', (data) => {
  if (data.has_attachments) {
    showNotification(`Guest sent ${data.attachments.length} file(s)`);
  }
});
```

### FCM Push Notifications ✅

File uploads trigger FCM notifications with special formatting:

**For Staff (when guest sends files):**
- 📷 "Guest sent 2 image(s) - Room 101"
- 📄 "Guest sent document(s) - Room 101"
- 📎 "Guest sent 3 file(s) - Room 101"

**For Guests (when staff sends files):**
- 📷 "John Smith sent 2 image(s)"
- 📄 "John Smith sent document(s)"
- 📎 "John Smith sent 3 file(s)"

**FCM Data Payload:**
```json
{
  "type": "new_chat_message_with_files",
  "conversation_id": "123",
  "room_number": "101",
  "message_id": "456",
  "sender_type": "staff",
  "staff_name": "John Smith",
  "has_attachments": "true",
  "attachment_count": "2",
  "hotel_slug": "hotel-killarney",
  "click_action": "/chat/hotel-killarney/conversation/123",
  "url": "https://hotelsmates.com/chat/hotel-killarney/conversation/123"
}
```

**Handle FCM in your app:**
```javascript
// When FCM notification is received
messaging.onMessage((payload) => {
  const { data } = payload;
  
  if (data.has_attachments === 'true') {
    const count = data.attachment_count;
    showNotification(`${data.sender_type === 'staff' ? data.staff_name : 'Guest'} sent ${count} file(s)`);
    
    // Navigate to chat on click
    if (data.click_action) {
      window.location.href = data.click_action;
    }
  }
});
```

---

## 🎨 Basic CSS Styling

```css
.chat-input-container {
  border-top: 1px solid #ddd;
  padding: 10px;
  background: white;
}

.file-previews {
  display: flex;
  gap: 10px;
  padding: 10px;
  overflow-x: auto;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 10px;
}

.file-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 10px;
  background: white;
  border-radius: 8px;
  position: relative;
}

.file-preview img {
  border-radius: 4px;
}

.file-icon {
  font-size: 40px;
}

.file-name {
  font-size: 11px;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-preview button {
  position: absolute;
  top: 5px;
  right: 5px;
  background: rgba(255, 0, 0, 0.8);
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 10px;
  cursor: pointer;
}

.input-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.attach-btn {
  padding: 10px 15px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 18px;
}

.message-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.send-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Message attachments */
.attachment {
  margin-top: 10px;
}

.attachment img {
  cursor: pointer;
  transition: transform 0.2s;
}

.attachment img:hover {
  transform: scale(1.02);
}

.document {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
}

.document .size {
  font-size: 12px;
  color: #666;
}

.document a {
  margin-left: auto;
  padding: 5px 10px;
  background: #4CAF50;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 12px;
}
```

---

## 🧪 Testing Checklist

### Basic Tests
- [ ] Upload single image
- [ ] Upload multiple images
- [ ] Upload PDF document
- [ ] Upload Office document
- [ ] View uploaded image inline
- [ ] Download uploaded document
- [ ] Send message with text + files
- [ ] Send message with only files (no text)

### Validation Tests
- [ ] Try uploading 11MB file (should fail with error)
- [ ] Try uploading .exe file (should fail)
- [ ] Upload file with special characters in name
- [ ] Upload same file multiple times

### Real-time Tests
- [ ] Guest uploads → Staff receives instantly
- [ ] Staff uploads → Guest receives instantly
- [ ] Multiple files appear correctly
- [ ] File URLs work and download properly

---

## ❌ Common Mistakes to Avoid

### ❌ MISTAKE #1: Setting Content-Type manually
```javascript
// WRONG ❌
headers: {
  'Content-Type': 'multipart/form-data'  // Browser needs to add boundary automatically
}

// RIGHT ✅
headers: {
  'Authorization': `Token ${token}`
  // Content-Type NOT set - browser adds it with correct boundary
}
```

### ❌ MISTAKE #2: Using 'file' instead of 'files'
```javascript
// WRONG ❌
formData.append('file', fileObject);  // Backend expects "files" (plural)

// RIGHT ✅
formData.append('files', fileObject);  // Must be "files" (plural)
```

### ❌ MISTAKE #3: Sending file path instead of File object
```javascript
// WRONG ❌
formData.append('files', '/path/to/file.pdf');  // String path won't work
formData.append('files', 'file.pdf');           // String won't work

// RIGHT ✅
formData.append('files', fileInputElement.files[0]);  // Actual File object from input
```

### ❌ DON'T forget to validate file size
```javascript
// Add validation before upload
if (file.size > 50 * 1024 * 1024) {
  alert('File too large. Max 50MB per file.');
  return;
}
```

### ❌ DON'T use input value for preview
```javascript
// WRONG ❌
<img src={file.path} />

// RIGHT ✅
<img src={URL.createObjectURL(file)} />
```

---

## 🐛 Troubleshooting

### Issue: Files not uploading
**Symptoms**: Upload fails, no error message or generic error

**Solutions**: 
1. Check file size is under 50MB per file
2. Verify file extension is in allowed list
3. Check browser console for detailed errors
4. Verify API endpoint URL includes correct `hotel_slug` and `conversation_id`
5. Check authentication token is valid

**Debug:**
```javascript
console.log('File size:', file.size, 'bytes');
console.log('File type:', file.type);
console.log('File name:', file.name);
console.log('API URL:', apiUrl);
```

### Issue: "No files provided" error
**Symptoms**: Backend returns error even though files are selected

**Solutions**: 
- ✅ Use `formData.append('files', file)` not `formData.append('file', file)`
- ✅ Don't set `Content-Type` header manually
- ✅ Make sure `file` is a File object, not a string

**Correct:**
```javascript
files.forEach(file => formData.append('files', file)); // ✅
```

**Wrong:**
```javascript
formData.append('file', file); // ❌ Wrong key
formData.append('files', file.path); // ❌ String not File
```

### Issue: Files upload but show local paths instead of Cloudinary URLs
**Symptoms**: URLs like `/chat/hotel-name/room_101/file.png` instead of `https://res.cloudinary.com/...`

**Solutions**: 
- ✅ Backend serializers have been fixed to return full Cloudinary URLs
- ✅ Check that `CLOUDINARY_URL` is set in backend `.env` file
- ✅ Verify `cloudinary` and `cloudinary_storage` are in `INSTALLED_APPS`

**Expected URL format:**
```
https://res.cloudinary.com/your-cloud-name/image/upload/v1234567890/chat/hotel-slug/room_number/2025/11/04/filename.png
```

### Issue: Files upload but don't display in messages
**Symptoms**: Message appears but no attachments shown

**Solutions**: 
- Check that response has `attachments` array
- Verify `file_url` in response is accessible (open in new tab)
- Check if message component renders `message.attachments`
- Verify CORS settings allow Cloudinary domain

### Issue: Large images load slowly
**Solutions**:
- Use `thumbnail_url` for previews if available
- Add loading spinner while image loads
- Consider compressing images on client before upload:

```javascript
const compressImage = async (file) => {
  // Use browser Image API or a library like browser-image-compression
  const options = {
    maxSizeMB: 1,
    maxWidthOrHeight: 1920,
    useWebWorker: true
  };
  return await imageCompression(file, options);
};
```

---

## 📞 Need Help?

- **Backend Issues**: Check with backend team
- **Frontend Issues**: Check browser console
- **API Errors**: Check Network tab in DevTools
- **File Access**: Verify Cloudinary URLs are accessible

---

## ✅ Summary

### Implementation Steps:
1. ✅ Add file input button to chat UI
2. ✅ Create FormData with selected files
3. ✅ POST to upload endpoint (don't set Content-Type header)
4. ✅ Display attachments in messages (use `file_url` from response)
5. ✅ Handle Pusher events for real-time updates
6. ✅ Add client-side file validation for better UX

### Backend Features:
- ✅ File upload endpoint: `/api/chat/{hotel_slug}/conversations/{conversation_id}/upload-attachment/`
- ✅ Cloudinary storage (files stored in cloud, not local server)
- ✅ File size validation (10MB max)
- ✅ File type validation (images, PDF, documents)
- ✅ Multiple file uploads supported
- ✅ Real-time Pusher notifications (guest ↔ staff)
- ✅ FCM push notifications (with file type indicators 📷📄📎)
- ✅ Full CDN URLs returned (https://res.cloudinary.com/...)
- ✅ Automatic thumbnail generation for images
- ✅ Secure filename sanitization

### What You Need:
- `hotel_slug` - Your hotel identifier
- `conversation_id` - The chat conversation ID
- `authToken` - User authentication token (optional for guests)
- Files to upload (max 10MB each)

**The backend is ready! Just implement the UI and you're done!** 🚀

---

**Last Updated**: November 4, 2025  
**Backend Status**: ✅ Complete & Tested  
**Storage**: Cloudinary Cloud Storage  
**Max File Size**: 50MB per file (unlimited total when sending multiple files)  
**Supported Types**: Images, PDF, Documents

---

# 🗑️ Message Deletion - Frontend Implementation Guide

## 🎉 Backend is Ready!

The backend now supports **soft delete** (hide message) and **hard delete** (permanently remove with all attachments from Cloudinary).

**✅ What's Configured:**
- Soft delete with smart text:
  - Text-only message → "[Message deleted]"
  - File-only message → "[File deleted]"
  - Text + Files → "[Message and file(s) deleted]"
- Hard delete (permanent removal + Cloudinary cleanup)
- Permission checks (users can delete own messages, admins can delete any)
- Real-time Pusher notifications for deletions
- Automatic Cloudinary file cleanup on hard delete

---

## 🚀 Delete Message API

### Endpoint
```
DELETE /api/chat/messages/<message_id>/delete/
```

### Authentication
- **Staff**: Must include `Authorization: Token <staff_token>`
- **Guest**: Can delete own messages (identified by session)

### Request Parameters
Query parameter (optional):
- `hard_delete=true` - Permanently delete (admin only)
- No parameter or `hard_delete=false` - Soft delete (default)

### Permissions
- **Regular users**: Can soft delete own messages only
- **Admins**: Can soft delete OR hard delete any message

---

## 💻 Frontend Implementation

### Basic Delete Function

```javascript
const deleteMessage = async (messageId, hardDelete = false) => {
  try {
    const authToken = localStorage.getItem('authToken');
    const url = hardDelete 
      ? `/api/chat/messages/${messageId}/delete/?hard_delete=true`
      : `/api/chat/messages/${messageId}/delete/`;
    
    const response = await fetch(`${API_URL}${url}`, {
      method: 'DELETE',
      headers: {
        'Authorization': authToken ? `Token ${authToken}` : '',
      },
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete message');
    }
    
    const data = await response.json();
    console.log('✅ Message deleted:', data);
    return data;
    
  } catch (error) {
    console.error('❌ Delete error:', error);
    throw error;
  }
};
```

### Complete Message Component with Delete

```jsx
import React, { useState } from 'react';

const MessageBubble = ({ message, currentUser, isAdmin }) => {
  const [isDeleted, setIsDeleted] = useState(message.is_deleted);
  const [showActions, setShowActions] = useState(false);
  
  const canDelete = message.sender_type === currentUser.type && 
                    message.staff?.id === currentUser.id;
  
  const handleSoftDelete = async () => {
    if (!confirm('Delete this message?')) return;
    
    try {
      await deleteMessage(message.id, false);
      setIsDeleted(true);
    } catch (error) {
      alert('Failed to delete message');
    }
  };
  
  const handleHardDelete = async () => {
    if (!isAdmin) {
      alert('Only admins can permanently delete messages');
      return;
    }
    
    if (!confirm('Permanently delete this message? This cannot be undone and will remove all attachments from cloud storage.')) {
      return;
    }
    
    try {
      await deleteMessage(message.id, true);
      // Message will be removed by Pusher event
    } catch (error) {
      alert('Failed to permanently delete message');
    }
  };
  
  if (isDeleted && !isAdmin) {
    return (
      <div className="message deleted">
        <span className="deleted-text">🗑️ {message.message}</span>
        <span className="timestamp">{formatTime(message.deleted_at)}</span>
      </div>
    );
  }
  
  return (
    <div className={`message ${message.sender_type}`}>
      <div className="message-header">
        <span className="sender">
          {message.sender_type === 'staff' 
            ? message.staff_info?.name 
            : 'Guest'}
        </span>
        
        {(canDelete || isAdmin) && (
          <button 
            className="actions-btn"
            onClick={() => setShowActions(!showActions)}
          >
            ⋮
          </button>
        )}
      </div>
      
      {showActions && (
        <div className="message-actions">
          {canDelete && (
            <button onClick={handleSoftDelete}>
              🗑️ Delete
            </button>
          )}
          {isAdmin && (
            <button onClick={handleHardDelete} className="danger">
              ⚠️ Delete Permanently
            </button>
          )}
        </div>
      )}
      
      <div className="message-content">
        {message.message && <p>{message.message}</p>}
        
        {/* Attachments */}
        {message.attachments?.map(att => (
          <div key={att.id} className="attachment">
            {att.file_type === 'image' ? (
              <img src={att.file_url} alt={att.file_name} />
            ) : (
              <a href={att.file_url} download={att.file_name}>
                📄 {att.file_name}
              </a>
            )}
          </div>
        ))}
      </div>
      
      <span className="timestamp">{formatTime(message.timestamp)}</span>
      
      {isDeleted && isAdmin && (
        <span className="admin-info">🗑️ Deleted</span>
      )}
    </div>
  );
};
```

---

## 📡 Real-time Delete Events (Pusher)

### Pusher Channels for Deletions

The backend sends `message-deleted` events to **3 channels simultaneously** to ensure all participants see the deletion in real-time:

1. **Conversation Channel**: `{hotelSlug}-conversation-{conversationId}-chat`
2. **Guest Channel**: `{hotelSlug}-room-{roomNumber}-chat`
3. **Staff Individual Channels**: `{hotelSlug}-staff-{staffId}-chat` (for each staff in conversation)

### Listen for Deletions

**For Guests:**
```javascript
// Guest subscribes to their room channel
const guestChannel = pusher.subscribe(`${hotelSlug}-room-${roomNumber}-chat`);

guestChannel.bind('message-deleted', (data) => {
  console.log('Message deleted:', data);
  
  if (data.hard_delete) {
    // Permanently remove message from UI
    setMessages(prev => prev.filter(msg => msg.id !== data.message_id));
    console.log('💥 Message permanently deleted (hard delete)');
  } else {
    // Soft delete - update message to show as deleted
    // Backend automatically sets text: "[Message deleted]", "[File deleted]", or "[Message and file(s) deleted]"
    setMessages(prev => prev.map(msg => 
      msg.id === data.message_id 
        ? { ...data.message, is_deleted: true, deleted_at: new Date() }
        : msg
    ));
    console.log('🗑️ Message soft deleted');
  }
});
```

**For Staff:**
```javascript
// Staff subscribes to their individual channel
const staffChannel = pusher.subscribe(`${hotelSlug}-staff-${staffId}-chat`);

staffChannel.bind('message-deleted', (data) => {
  console.log('Message deleted:', data);
  
  if (data.hard_delete) {
    // Permanently remove message from UI
    setMessages(prev => prev.filter(msg => msg.id !== data.message_id));
    console.log('💥 Message permanently deleted (hard delete)');
  } else {
    // Soft delete - update message to show as deleted
    setMessages(prev => prev.map(msg => 
      msg.id === data.message_id 
        ? { ...data.message, is_deleted: true, deleted_at: new Date() }
        : msg
    ));
    console.log('🗑️ Message soft deleted');
  }
});
```

**Or Subscribe to Conversation Channel (works for both):**
```javascript
// Both guests and staff can also subscribe to conversation channel
const conversationChannel = pusher.subscribe(`${hotelSlug}-conversation-${conversationId}-chat`);

conversationChannel.bind('message-deleted', (data) => {
  console.log('Message deleted:', data);
  
  if (data.hard_delete) {
    setMessages(prev => prev.filter(msg => msg.id !== data.message_id));
  } else {
    setMessages(prev => prev.map(msg => 
      msg.id === data.message_id 
        ? { ...data.message, is_deleted: true, deleted_at: new Date() }
        : msg
    ));
  }
});
```

### Pusher Event Data Structure

**Soft Delete (Text Message):**
```json
{
  "message_id": 456,
  "hard_delete": false,
  "message": {
    "id": 456,
    "message": "[Message deleted]",
    "is_deleted": true,
    "deleted_at": "2025-11-04T10:30:00Z",
    "sender_type": "staff",
    "attachments": [],
    ...
  }
}
```

**Soft Delete (File Only):**
```json
{
  "message_id": 457,
  "hard_delete": false,
  "message": {
    "id": 457,
    "message": "[File deleted]",
    "is_deleted": true,
    "deleted_at": "2025-11-04T10:30:00Z",
    "sender_type": "guest",
    "attachments": [],
    ...
  }
}
```

**Soft Delete (Text + Files):**
```json
{
  "message_id": 458,
  "hard_delete": false,
  "message": {
    "id": 458,
    "message": "[Message and file(s) deleted]",
    "is_deleted": true,
    "deleted_at": "2025-11-04T10:30:00Z",
    "sender_type": "staff",
    "attachments": [],
    ...
  }
}
```

**Hard Delete:**
```json
{
  "message_id": 456,
  "hard_delete": true
}
```

---

### 🔔 Real-time Update Guarantee

When any user deletes a message, the backend sends the `message-deleted` event to **ALL** relevant channels:

| Deletion By | Channels Notified |
|-------------|-------------------|
| Guest deletes | ✅ Guest's room channel<br>✅ All staff individual channels<br>✅ Conversation channel |
| Staff deletes | ✅ Guest's room channel<br>✅ All staff individual channels<br>✅ Conversation channel |

**Result**: Everyone sees the deletion **instantly**, regardless of which channel they're subscribed to!

---

## 🧪 Testing Checklist - Deletion

- [ ] Soft delete text-only message (should show "[Message deleted]")
- [ ] Soft delete file-only message (should show "[File deleted]")
- [ ] Soft delete message with text + files (should show "[Message and file(s) deleted]")
- [ ] Try to delete other user's message (should fail)
- [ ] Admin hard delete message (should disappear completely)
- [ ] Hard delete message with attachments (files removed from Cloudinary)
- [ ] **Guest deletes → Staff sees update instantly** ⭐
- [ ] **Staff deletes → Guest sees update instantly** ⭐
- [ ] **Multiple staff members all see deletion in real-time** ⭐
- [ ] Soft deleted message can still be seen by admins
- [ ] Hard deleted message disappears for everyone

---

# 💬 Reply to Messages - Frontend Implementation Guide

## 🎉 Backend is Ready!

The backend supports replying to any message (with or without attachments).

**✅ What's Configured:**
- `reply_to` field in message model
- Reply info included in message serialization
- Works for both text messages and messages with attachments

---

## 🚀 Reply to Message API

### Sending a Reply

Include `reply_to` parameter when sending a message:

```javascript
const sendReplyMessage = async (conversationId, messageText, replyToMessageId) => {
  try {
    const authToken = localStorage.getItem('authToken');
    
    const response = await fetch(
      `${API_URL}/api/chat/${hotelSlug}/conversations/${conversationId}/messages/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authToken ? `Token ${authToken}` : '',
        },
        body: JSON.stringify({
          message: messageText,
          reply_to: replyToMessageId  // ✅ This creates the reply link
        })
      }
    );
    
    if (!response.ok) throw new Error('Failed to send reply');
    
    const data = await response.json();
    return data;
    
  } catch (error) {
    console.error('Reply error:', error);
    throw error;
  }
};
```

### Replying with Files

```javascript
const sendReplyWithFiles = async (conversationId, files, messageText, replyToMessageId) => {
  const formData = new FormData();
  
  // Add files
  files.forEach(file => formData.append('files', file));
  
  // Add message text
  if (messageText.trim()) {
    formData.append('message', messageText);
  }
  
  // Add reply reference
  if (replyToMessageId) {
    formData.append('reply_to', replyToMessageId);  // ✅ Reply with files
  }
  
  const response = await fetch(
    `${API_URL}/api/chat/${hotelSlug}/conversations/${conversationId}/upload-attachment/`,
    {
      method: 'POST',
      headers: {
        'Authorization': authToken ? `Token ${authToken}` : '',
      },
      body: formData
    }
  );
  
  return await response.json();
};
```

---

## 💻 Complete Reply Component

```jsx
import React, { useState } from 'react';

const ChatInput = ({ conversationId, hotelSlug }) => {
  const [message, setMessage] = useState('');
  const [replyingTo, setReplyingTo] = useState(null);
  
  const handleReply = (messageToReplyTo) => {
    setReplyingTo(messageToReplyTo);
  };
  
  const cancelReply = () => {
    setReplyingTo(null);
  };
  
  const handleSend = async () => {
    if (!message.trim()) return;
    
    try {
      const authToken = localStorage.getItem('authToken');
      
      const payload = {
        message: message.trim()
      };
      
      // Add reply reference if replying
      if (replyingTo) {
        payload.reply_to = replyingTo.id;
      }
      
      const response = await fetch(
        `${API_URL}/api/chat/${hotelSlug}/conversations/${conversationId}/messages/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': authToken ? `Token ${authToken}` : '',
          },
          body: JSON.stringify(payload)
        }
      );
      
      if (!response.ok) throw new Error('Failed to send');
      
      // Clear inputs
      setMessage('');
      setReplyingTo(null);
      
    } catch (error) {
      console.error('Send error:', error);
      alert('Failed to send message');
    }
  };
  
  return (
    <div className="chat-input-container">
      {/* Reply preview */}
      {replyingTo && (
        <div className="reply-preview">
          <div className="reply-header">
            <span>↩️ Replying to {replyingTo.sender_type === 'staff' ? replyingTo.staff_info?.name : 'Guest'}</span>
            <button onClick={cancelReply}>❌</button>
          </div>
          <div className="reply-content">
            {replyingTo.message.substring(0, 50)}...
          </div>
        </div>
      )}
      
      {/* Input */}
      <div className="input-row">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder={replyingTo ? "Type your reply..." : "Type a message..."}
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
};

const MessageBubble = ({ message, onReply }) => {
  return (
    <div className="message">
      {/* Show replied-to message */}
      {message.reply_to_message && (
        <div className="replied-message">
          <span className="reply-icon">↩️</span>
          <div className="reply-info">
            <strong>{message.reply_to_message.sender_name}</strong>
            <p>{message.reply_to_message.message}</p>
          </div>
        </div>
      )}
      
      {/* Message content */}
      <p>{message.message}</p>
      
      {/* Attachments */}
      {message.attachments?.map(att => (
        <img key={att.id} src={att.file_url} alt={att.file_name} />
      ))}
      
      {/* Reply button */}
      <button 
        className="reply-btn"
        onClick={() => onReply(message)}
      >
        ↩️ Reply
      </button>
    </div>
  );
};
```

---

## 📊 Reply Response Format

When a message has a reply, it includes `reply_to_message` in the response:

```json
{
  "id": 789,
  "message": "Yes, I'll be there at 3pm",
  "sender_type": "guest",
  "timestamp": "2025-11-04T14:30:00Z",
  "reply_to_message": {
    "id": 456,
    "message": "Can you meet me at the lobby?",
    "sender_type": "staff",
    "sender_name": "John Smith",
    "timestamp": "2025-11-04T14:25:00Z"
  },
  "attachments": [],
  "has_attachments": false
}
```

---

## 🎨 CSS for Deletion & Reply UI

```css
/* Message Actions Menu */
.message-actions {
  position: absolute;
  top: 30px;
  right: 10px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 10;
}

.message-actions button {
  display: block;
  width: 100%;
  padding: 8px 16px;
  text-align: left;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 13px;
}

.message-actions button:hover {
  background: #f5f5f5;
}

.message-actions button.danger {
  color: #dc3545;
}

.message-actions button.danger:hover {
  background: #fff0f0;
}

/* Deleted Message */
.message.deleted {
  opacity: 0.6;
  font-style: italic;
}

.deleted-text {
  color: #999;
}

/* Reply Preview (when composing) */
.reply-preview {
  background: #f0f8ff;
  padding: 10px;
  margin-bottom: 10px;
  border-left: 3px solid #007bff;
  border-radius: 4px;
}

.reply-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12px;
  font-weight: 600;
  color: #007bff;
}

.reply-header button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.reply-content {
  font-size: 13px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Replied Message (in bubble) */
.replied-message {
  display: flex;
  gap: 8px;
  padding: 8px;
  margin-bottom: 8px;
  background: rgba(0, 0, 0, 0.03);
  border-left: 3px solid #007bff;
  border-radius: 4px;
  font-size: 13px;
}

.reply-icon {
  font-size: 16px;
  color: #007bff;
}

.reply-info strong {
  display: block;
  color: #007bff;
  margin-bottom: 2px;
}

.reply-info p {
  margin: 0;
  color: #666;
  font-size: 12px;
}

.reply-btn {
  margin-top: 5px;
  padding: 4px 8px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 3px;
  font-size: 11px;
  cursor: pointer;
  color: #666;
}

.reply-btn:hover {
  background: #e0e0e0;
}
```

---

## 🧪 Testing Checklist - Reply

- [ ] Reply to text message
- [ ] Reply to message with attachments
- [ ] Reply with text only
- [ ] Reply with text + files
- [ ] Reply preview shows correct original message
- [ ] Cancel reply removes preview
- [ ] Replied message displays with link to original
- [ ] Multiple levels of replies work correctly

---

## 📞 Summary - All Chat Features

### ✅ File Sharing
- Upload images, PDFs, documents (max 50MB per file)
- Multiple file uploads in one message
- Files stored in Cloudinary cloud storage
- Real-time notifications with file type indicators (📷📄📎)
- Automatic Cloudinary cleanup on hard delete

### ✅ Message Deletion
- **Soft delete**: Hides message with smart text:
  - Text-only → "[Message deleted]"
  - File-only → "[File deleted]"
  - Text + Files → "[Message and file(s) deleted]"
- **Hard delete**: Permanently removes message + all attachments from Cloudinary (admin only)
- Users can delete own messages
- Admins can delete any message
- Real-time Pusher updates

### ✅ Reply Functionality
- Reply to any message (with or without attachments)
- Visual reply preview when composing
- Replied messages show link to original
- Works with text, files, or both

### 🔑 Key Points
1. **File uploads** automatically cleaned from Cloudinary when hard deleted
2. **Soft delete** preserves message in database but marks as deleted
3. **Hard delete** removes everything (database + cloud files) - admin only
4. **Reply** works for all message types
5. All features have **real-time Pusher updates**

---

**Features Status**: ✅ File Sharing | ✅ Deletion | ✅ Reply  
**Last Updated**: November 4, 2025
