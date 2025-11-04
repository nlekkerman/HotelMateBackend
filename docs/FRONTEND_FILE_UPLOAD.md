# 📎 File Upload - Frontend Implementation Guide

## 🎉 Backend is Ready!

The backend now supports file and image uploads in chat between guests and staff. Files are automatically stored in **Cloudinary cloud storage** and return full CDN URLs.

**✅ What's Configured:**
- File upload endpoint ready
- Cloudinary storage configured
- File size validation (10MB max)
- File type validation (images, PDF, documents)
- Real-time Pusher notifications
- Multiple file uploads supported

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
- **Max size**: 10MB per file (enforced on backend)
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
  const maxSize = 10 * 1024 * 1024; // 10MB
  const allowedTypes = [
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
    'application/pdf',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain', 'text/csv'
  ];
  
  if (file.size > maxSize) {
    return { valid: false, error: `File too large (${(file.size / (1024*1024)).toFixed(2)}MB, max 10MB)` };
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
      // Check file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        errors.push(`${file.name}: Too large (${(file.size / (1024*1024)).toFixed(2)}MB, max 10MB)`);
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
if (file.size > 10 * 1024 * 1024) {
  alert('File too large. Max 10MB.');
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
1. Check file size is under 10MB
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
**Max File Size**: 10MB per file  
**Supported Types**: Images, PDF, Documents
