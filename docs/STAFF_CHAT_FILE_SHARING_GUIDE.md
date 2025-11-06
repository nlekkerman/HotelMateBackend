# Staff Chat - File & Image Sharing Guide

## 📋 Complete Guide to Uploading, Sharing, and Managing Files

This guide covers everything about file attachments in staff chat: uploading images and documents, sharing files with messages, replying with files, and managing attachments.

---

## 📸 What You Can Share

### Supported File Types

#### Images
- `.jpg` / `.jpeg` - JPEG images
- `.png` - PNG images
- `.gif` - Animated GIFs
- `.webp` - WebP images
- `.bmp` - Bitmap images

#### Documents
- `.pdf` - PDF documents
- `.doc` / `.docx` - Microsoft Word
- `.xls` / `.xlsx` - Microsoft Excel
- `.txt` - Text files
- `.csv` - CSV files

### File Limits
- **Max files per upload**: 10 files
- **Max file size**: 50MB per file
- **Storage**: All files stored in Cloudinary (cloud storage)
- **Automatic thumbnails**: Generated for images

---

## 🚀 Upload Methods

### Method 1: Upload Files with New Message

Send a message with files attached.

```javascript
// POST /api/staff_chat/{hotel_slug}/conversations/{conversation_id}/upload/

async function uploadFilesWithMessage(conversationId, files, messageText = '') {
  const formData = new FormData();
  
  // Add files
  files.forEach(file => {
    formData.append('files', file);
  });
  
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
        // Don't set Content-Type - browser sets it automatically with boundary
      },
      body: formData
    }
  );
  
  return await response.json();
}

// Example: Upload photos with message
const fileInput = document.getElementById('fileInput');
const files = Array.from(fileInput.files);
await uploadFilesWithMessage(45, files, "Here are today's inspection photos");
```

**Response:**
```json
{
  "success": true,
  "message": {
    "id": 235,
    "conversation": 45,
    "sender": {
      "id": 3,
      "first_name": "John",
      "last_name": "Doe",
      "profile_image": "https://..."
    },
    "message": "Here are today's inspection photos",
    "timestamp": "2025-11-05T14:30:00Z",
    "attachments": [
      {
        "id": 67,
        "file_name": "room_101.jpg",
        "file_type": "image",
        "file_size": 2048576,
        "mime_type": "image/jpeg",
        "file_url": "https://res.cloudinary.com/.../room_101.jpg",
        "thumbnail_url": "https://res.cloudinary.com/.../thumb_room_101.jpg",
        "uploaded_at": "2025-11-05T14:30:00Z"
      },
      {
        "id": 68,
        "file_name": "room_102.jpg",
        "file_type": "image",
        "file_size": 1876543,
        "mime_type": "image/jpeg",
        "file_url": "https://res.cloudinary.com/.../room_102.jpg",
        "thumbnail_url": "https://res.cloudinary.com/.../thumb_room_102.jpg",
        "uploaded_at": "2025-11-05T14:30:01Z"
      }
    ]
  },
  "attachments": [...]
}
```

---

### Method 2: Add Files to Existing Message

Attach files to a message you already sent.

```javascript
async function addFilesToExistingMessage(conversationId, messageId, files) {
  const formData = new FormData();
  
  // Add files
  files.forEach(file => {
    formData.append('files', file);
  });
  
  // Specify existing message ID
  formData.append('message_id', messageId);
  
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

// Example: Add files to message #234
await addFilesToExistingMessage(45, 234, files);
```

**Important**: Only the **message sender** can add files to their own messages.

---

### Method 3: Upload Files as Reply

Reply to a message with file attachments.

```javascript
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
  } else {
    formData.append('message', '[File shared]');
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

// Example: Reply to message #234 with photos
await replyWithFiles(45, 234, files, "Here's the requested document");
```

**Response includes reply information:**
```json
{
  "success": true,
  "message": {
    "id": 236,
    "message": "Here's the requested document",
    "reply_to_message": {
      "id": 234,
      "message": "Can you send me the report?",
      "sender": {
        "id": 5,
        "first_name": "Jane",
        "last_name": "Smith"
      }
    },
    "attachments": [
      {
        "id": 69,
        "file_name": "monthly_report.pdf",
        "file_type": "pdf",
        "file_url": "https://..."
      }
    ]
  }
}
```

---

## 🖼️ Display Files in UI

### Image Preview

```javascript
function ImageAttachment({ attachment }) {
  return (
    <div className="image-attachment">
      {/* Show thumbnail first, full image on click */}
      <a href={attachment.file_url} target="_blank" rel="noopener">
        <img 
          src={attachment.thumbnail_url || attachment.file_url}
          alt={attachment.file_name}
          className="thumbnail"
          loading="lazy"
        />
      </a>
      
      {/* File info */}
      <div className="file-info">
        <span className="file-name">{attachment.file_name}</span>
        <span className="file-size">{formatFileSize(attachment.file_size)}</span>
      </div>
    </div>
  );
}
```

### Document Attachment

```javascript
function DocumentAttachment({ attachment }) {
  // Get file icon based on type
  const getFileIcon = (fileType, fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();
    
    if (fileType === 'pdf') return '📄';
    if (['doc', 'docx'].includes(ext)) return '📝';
    if (['xls', 'xlsx'].includes(ext)) return '📊';
    if (ext === 'txt') return '📃';
    if (ext === 'csv') return '📈';
    return '📎';
  };
  
  return (
    <a 
      href={attachment.file_url} 
      target="_blank" 
      rel="noopener"
      className="document-attachment"
    >
      <span className="file-icon">
        {getFileIcon(attachment.file_type, attachment.file_name)}
      </span>
      
      <div className="file-details">
        <span className="file-name">{attachment.file_name}</span>
        <span className="file-meta">
          {attachment.file_type.toUpperCase()} · {formatFileSize(attachment.file_size)}
        </span>
      </div>
      
      <span className="download-icon">⬇️</span>
    </a>
  );
}
```

### Complete Message with Attachments

```javascript
function MessageWithAttachments({ message, currentUserId }) {
  const isMine = message.sender.id === currentUserId;
  
  return (
    <div className={`message ${isMine ? 'my-message' : 'their-message'}`}>
      {/* Sender info (for others' messages) */}
      {!isMine && (
        <div className="sender-info">
          <img src={message.sender.profile_image} alt="" className="avatar" />
          <span>{message.sender.first_name} {message.sender.last_name}</span>
        </div>
      )}
      
      {/* Reply preview (if replying) */}
      {message.reply_to_message && (
        <div className="reply-preview">
          <strong>{message.reply_to_message.sender.first_name}:</strong>
          <span>{message.reply_to_message.message}</span>
        </div>
      )}
      
      {/* Message text */}
      {message.message && message.message !== '[File shared]' && (
        <div className="message-text">
          {message.message}
        </div>
      )}
      
      {/* Attachments */}
      {message.attachments && message.attachments.length > 0 && (
        <div className="attachments-container">
          {message.attachments.map(attachment => (
            <div key={attachment.id}>
              {attachment.file_type === 'image' ? (
                <ImageAttachment attachment={attachment} />
              ) : (
                <DocumentAttachment attachment={attachment} />
              )}
            </div>
          ))}
        </div>
      )}
      
      {/* Timestamp */}
      <div className="timestamp">
        {formatTime(message.timestamp)}
      </div>
      
      {/* Delete button (only for your own attachments) */}
      {isMine && message.attachments?.length > 0 && (
        <div className="attachment-actions">
          {message.attachments.map(attachment => (
            <button 
              key={attachment.id}
              onClick={() => deleteAttachment(attachment.id)}
              className="delete-attachment-btn"
            >
              🗑️ Delete {attachment.file_name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Helper function to format file size
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
```

---

## 🗑️ Delete Attachments

### Delete a Single File

```javascript
// DELETE /api/staff_chat/{hotel_slug}/attachments/{attachment_id}/delete/

async function deleteAttachment(attachmentId) {
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/attachments/${attachmentId}/delete/`,
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
async function handleDeleteAttachment(attachmentId, fileName) {
  if (confirm(`Delete ${fileName}?`)) {
    try {
      const result = await deleteAttachment(attachmentId);
      console.log('File deleted:', result);
      // UI will update via Pusher event
    } catch (error) {
      console.error('Failed to delete file:', error);
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "attachment_id": 67,
  "message_id": 235
}
```

**Important Rules:**
- ✅ Only the **message sender** can delete their attachments
- ✅ **Managers/Admins** can delete any attachment
- ✅ File is deleted from cloud storage (Cloudinary)
- ✅ Real-time update sent to all participants via Pusher

---

## 🎨 UI Components

### File Upload Button

```javascript
function FileUploadButton({ conversationId, onUploadSuccess }) {
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  
  async function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    
    if (files.length === 0) return;
    
    // Validate file count
    if (files.length > 10) {
      alert('Maximum 10 files per upload');
      return;
    }
    
    // Validate file sizes
    const oversized = files.filter(f => f.size > 50 * 1024 * 1024);
    if (oversized.length > 0) {
      alert(`File too large: ${oversized[0].name} (max 50MB)`);
      return;
    }
    
    setUploading(true);
    try {
      const result = await uploadFilesWithMessage(conversationId, files);
      onUploadSuccess && onUploadSuccess(result);
      
      // Clear input
      e.target.value = '';
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  }
  
  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".jpg,.jpeg,.png,.gif,.webp,.bmp,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />
      
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading}
        className="file-upload-btn"
      >
        {uploading ? '📤 Uploading...' : '📎 Attach Files'}
      </button>
    </>
  );
}
```

### Drag & Drop Upload

```javascript
function DragDropUpload({ conversationId, onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  
  function handleDragOver(e) {
    e.preventDefault();
    setIsDragging(true);
  }
  
  function handleDragLeave(e) {
    e.preventDefault();
    setIsDragging(false);
  }
  
  async function handleDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    
    if (files.length > 10) {
      alert('Maximum 10 files per upload');
      return;
    }
    
    try {
      const result = await uploadFilesWithMessage(conversationId, files);
      onUploadSuccess && onUploadSuccess(result);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    }
  }
  
  return (
    <div
      className={`drop-zone ${isDragging ? 'dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="drop-zone-content">
        <span className="drop-icon">📎</span>
        <p>Drag & drop files here</p>
        <small>Images, PDFs, Documents (max 50MB, 10 files)</small>
      </div>
    </div>
  );
}
```

### Image Gallery (Multiple Images)

```javascript
function ImageGallery({ attachments }) {
  const [lightboxIndex, setLightboxIndex] = useState(null);
  
  const images = attachments.filter(att => att.file_type === 'image');
  
  if (images.length === 0) return null;
  
  return (
    <div className="image-gallery">
      <div className={`gallery-grid grid-${Math.min(images.length, 4)}`}>
        {images.map((image, index) => (
          <div 
            key={image.id} 
            className="gallery-item"
            onClick={() => setLightboxIndex(index)}
          >
            <img
              src={image.thumbnail_url || image.file_url}
              alt={image.file_name}
              loading="lazy"
            />
            
            {/* Show count on last item if more than 4 */}
            {index === 3 && images.length > 4 && (
              <div className="more-overlay">
                +{images.length - 4}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Lightbox modal */}
      {lightboxIndex !== null && (
        <ImageLightbox
          images={images}
          currentIndex={lightboxIndex}
          onClose={() => setLightboxIndex(null)}
        />
      )}
    </div>
  );
}
```

### File Preview Before Upload

```javascript
function FilePreview({ files, onRemove }) {
  return (
    <div className="file-preview-list">
      {files.map((file, index) => (
        <div key={index} className="file-preview-item">
          {/* Image preview */}
          {file.type.startsWith('image/') && (
            <img 
              src={URL.createObjectURL(file)} 
              alt={file.name}
              className="preview-thumbnail"
            />
          )}
          
          {/* File info */}
          <div className="file-info">
            <span className="file-name">{file.name}</span>
            <span className="file-size">
              {formatFileSize(file.size)}
            </span>
          </div>
          
          {/* Remove button */}
          <button
            onClick={() => onRemove(index)}
            className="remove-file-btn"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
```

---

## 🔄 Real-Time Updates (Pusher)

### Listen for Attachment Events

```javascript
// Subscribe to conversation channel
const channelName = `${hotelSlug}-staff-conversation-${conversationId}`;
const channel = pusher.subscribe(channelName);

// 1. New message with attachments
channel.bind('new-message', (data) => {
  console.log('📨 New message with files:', data);
  
  if (data.attachments && data.attachments.length > 0) {
    // Add message with attachments to UI
    addMessageToUI({
      id: data.message_id,
      message: data.message,
      sender: data.sender,
      timestamp: data.timestamp,
      attachments: data.attachments
    });
    
    // Show notification if not viewing chat
    if (!isConversationVisible()) {
      showNotification(
        `${data.sender.name} sent ${data.attachments.length} file(s)`
      );
    }
  }
});

// 2. Files added to existing message
channel.bind('attachment-uploaded', (data) => {
  console.log('📎 Files added to message:', data);
  
  // Update message with new attachments
  updateMessageAttachments(data.message_id, data.attachments);
});

// 3. Attachment deleted
channel.bind('attachment-deleted', (data) => {
  console.log('🗑️ File deleted:', data);
  
  // Remove attachment from message in UI
  removeAttachmentFromMessage(data.message_id, data.attachment_id);
});
```

---

## 📱 FCM Notifications

### File Upload Notifications

Users receive notifications when files are shared:

#### Image Notification
```json
{
  "notification": {
    "title": "📷 Jane Smith",
    "body": "Sent 3 image(s)"
  },
  "data": {
    "type": "staff_chat_file",
    "conversation_id": "45",
    "file_count": "3",
    "file_types": ["image", "image", "image"]
  }
}
```

#### Document Notification
```json
{
  "notification": {
    "title": "📄 Jane Smith",
    "body": "Sent monthly_report.pdf"
  },
  "data": {
    "type": "staff_chat_file",
    "conversation_id": "45",
    "file_count": "1",
    "file_types": ["pdf"]
  }
}
```

#### Mixed Files Notification
```json
{
  "notification": {
    "title": "📎 Jane Smith",
    "body": "Sent 5 file(s)"
  },
  "data": {
    "type": "staff_chat_file",
    "conversation_id": "45",
    "file_count": "5",
    "file_types": ["image", "image", "pdf", "document", "image"]
  }
}
```

**Important**: Only **recipients** receive notifications, never the sender!

---

## 💡 Best Practices

### 1. Validate Before Upload

```javascript
function validateFiles(files) {
  const errors = [];
  const maxFileSize = 50 * 1024 * 1024; // 50MB
  const allowedTypes = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'text/csv'
  ];
  
  // Check file count
  if (files.length > 10) {
    errors.push('Maximum 10 files allowed per upload');
  }
  
  // Check each file
  files.forEach(file => {
    // Check size
    if (file.size > maxFileSize) {
      errors.push(`${file.name}: File too large (max 50MB)`);
    }
    
    // Check type
    if (!allowedTypes.includes(file.type)) {
      errors.push(`${file.name}: File type not allowed`);
    }
  });
  
  return errors;
}

// Usage
const files = Array.from(fileInput.files);
const errors = validateFiles(files);

if (errors.length > 0) {
  alert(errors.join('\n'));
} else {
  await uploadFilesWithMessage(conversationId, files);
}
```

### 2. Show Upload Progress

```javascript
function uploadWithProgress(conversationId, files, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    
    files.forEach(file => formData.append('files', file));
    
    // Track upload progress
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const percentComplete = (e.loaded / e.total) * 100;
        onProgress(percentComplete);
      }
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status === 201) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error('Upload failed'));
      }
    });
    
    xhr.addEventListener('error', () => reject(new Error('Upload failed')));
    
    xhr.open('POST', `/api/staff_chat/${hotelSlug}/conversations/${conversationId}/upload/`);
    xhr.setRequestHeader('Authorization', `Bearer ${authToken}`);
    xhr.send(formData);
  });
}

// Usage with progress bar
async function handleUpload(files) {
  setUploading(true);
  setProgress(0);
  
  try {
    await uploadWithProgress(conversationId, files, (progress) => {
      setProgress(progress);
    });
    alert('Upload complete!');
  } catch (error) {
    alert('Upload failed');
  } finally {
    setUploading(false);
  }
}
```

### 3. Compress Images Before Upload

```javascript
async function compressImage(file, maxWidth = 1920, quality = 0.8) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;
        
        // Resize if larger than max
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }
        
        canvas.width = width;
        canvas.height = height;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        
        canvas.toBlob((blob) => {
          resolve(new File([blob], file.name, {
            type: 'image/jpeg',
            lastModified: Date.now()
          }));
        }, 'image/jpeg', quality);
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// Usage
const files = Array.from(fileInput.files);
const compressedFiles = await Promise.all(
  files.map(file => 
    file.type.startsWith('image/') ? compressImage(file) : file
  )
);
await uploadFilesWithMessage(conversationId, compressedFiles);
```

### 4. Lazy Load Images

```javascript
function LazyImage({ src, alt, thumbnail }) {
  const [loaded, setLoaded] = useState(false);
  const imgRef = useRef(null);
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setLoaded(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );
    
    if (imgRef.current) {
      observer.observe(imgRef.current);
    }
    
    return () => observer.disconnect();
  }, []);
  
  return (
    <img
      ref={imgRef}
      src={loaded ? src : thumbnail}
      alt={alt}
      className={loaded ? 'loaded' : 'loading'}
      loading="lazy"
    />
  );
}
```

---

## � Message Reactions with Files

### Add Reaction to Messages with Attachments

**⚠️ IMPORTANT**: Each user can have **only ONE reaction per message**. When you select a new emoji, your previous reaction is automatically replaced.

```javascript
// POST /api/staff_chat/{hotel_slug}/messages/{message_id}/react/

async function addReaction(messageId, emoji) {
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/messages/${messageId}/react/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ emoji })
    }
  );
  
  return await response.json();
}

// Example: React to a message with files
await addReaction(235, '👍');

// Example: Change reaction (removes 👍, adds ❤️)
await addReaction(235, '❤️');
```

**Available Emojis:**
- 👍 Thumbs Up
- ❤️ Heart
- 😊 Smile
- 😂 Laugh
- 😮 Wow
- 😢 Sad
- 🎉 Party
- 🔥 Fire
- ✅ Check
- 👏 Clap

### Remove Reaction

```javascript
// DELETE /api/staff_chat/{hotel_slug}/messages/{message_id}/react/{emoji}/

async function removeReaction(messageId, emoji) {
  const response = await fetch(
    `/api/staff_chat/${hotelSlug}/messages/${messageId}/react/${emoji}/`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    }
  );
  
  return response.ok;
}

// Example
await removeReaction(235, '❤️');
```

### Display Reactions on File Messages

```javascript
function FileMessageWithReactions({ message, currentUserId }) {
  // Get current user's reaction
  const myReaction = message.reactions?.find(
    r => r.staff.id === currentUserId
  );
  
  // Group reactions by emoji
  const groupedReactions = groupReactions(message.reactions || []);
  
  return (
    <div className="message-with-files">
      {/* Message text */}
      {message.message && (
        <div className="message-text">{message.message}</div>
      )}
      
      {/* File attachments */}
      <div className="attachments">
        {message.attachments.map(att => (
          <div key={att.id} className="attachment-item">
            {att.file_type === 'image' ? (
              <img src={att.file_url} alt={att.file_name} />
            ) : (
              <a href={att.file_url} target="_blank">
                📎 {att.file_name}
              </a>
            )}
          </div>
        ))}
      </div>
      
      {/* Reactions display */}
      {groupedReactions.length > 0 && (
        <div className="reactions-display">
          {groupedReactions.map(group => (
            <button
              key={group.emoji}
              className={`reaction-bubble ${
                myReaction?.emoji === group.emoji ? 'my-reaction' : ''
              }`}
              onClick={() => 
                myReaction?.emoji === group.emoji
                  ? removeReaction(message.id, group.emoji)
                  : addReaction(message.id, group.emoji)
              }
              title={group.staff.map(s => s.first_name).join(', ')}
            >
              <span className="emoji">{group.emoji}</span>
              <span className="count">{group.count}</span>
            </button>
          ))}
        </div>
      )}
      
      {/* Reaction picker */}
      <div className="reaction-picker">
        {['👍', '❤️', '😊', '😂', '😮', '😢', '🎉', '🔥', '✅', '👏'].map(emoji => (
          <button
            key={emoji}
            onClick={() => addReaction(message.id, emoji)}
            className={myReaction?.emoji === emoji ? 'active' : ''}
            title={myReaction?.emoji === emoji ? 'Your reaction' : `React with ${emoji}`}
          >
            {emoji}
          </button>
        ))}
      </div>
    </div>
  );
}

// Helper: Group reactions by emoji
function groupReactions(reactions) {
  const grouped = {};
  reactions.forEach(reaction => {
    if (!grouped[reaction.emoji]) {
      grouped[reaction.emoji] = {
        emoji: reaction.emoji,
        count: 0,
        staff: []
      };
    }
    grouped[reaction.emoji].count++;
    grouped[reaction.emoji].staff.push(reaction.staff);
  });
  return Object.values(grouped);
}
```

### Real-Time Reaction Updates

```javascript
// Listen for reaction changes on file messages
channel.bind('message-reaction', (data) => {
  console.log('👍 Reaction update:', data);
  
  if (data.action === 'add') {
    // Add reaction to message
    setMessages(prev => prev.map(msg => {
      if (msg.id === data.message_id) {
        return {
          ...msg,
          reactions: [...(msg.reactions || []), {
            emoji: data.emoji,
            staff: data.staff
          }]
        };
      }
      return msg;
    }));
  } else if (data.action === 'remove') {
    // Remove reaction from message
    setMessages(prev => prev.map(msg => {
      if (msg.id === data.message_id) {
        return {
          ...msg,
          reactions: (msg.reactions || []).filter(
            r => !(r.emoji === data.emoji && r.staff.id === data.staff.id)
          )
        };
      }
      return msg;
    }));
  }
});
```

### CSS for Reactions

```css
/* Reaction display bubbles */
.reactions-display {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.reaction-bubble {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
  background: #f5f5f5;
  cursor: pointer;
  transition: all 0.2s;
}

.reaction-bubble:hover {
  background: #e8e8e8;
  border-color: #d0d0d0;
}

.reaction-bubble.my-reaction {
  background: #e3f2fd;
  border-color: #2196f3;
  font-weight: 600;
}

.reaction-bubble .emoji {
  font-size: 14px;
}

.reaction-bubble .count {
  font-size: 12px;
  color: #666;
}

/* Reaction picker */
.reaction-picker {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  padding: 8px;
  background: #fafafa;
  border-radius: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-with-files:hover .reaction-picker {
  opacity: 1;
}

.reaction-picker button {
  padding: 6px;
  border: 1px solid transparent;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.2s;
}

.reaction-picker button:hover {
  background: #fff;
  border-color: #e0e0e0;
  transform: scale(1.2);
}

.reaction-picker button.active {
  background: #e3f2fd;
  border-color: #2196f3;
}
```

---

## �📝 Complete Example: Chat with File Sharing

```javascript
import React, { useState, useRef } from 'react';

function ChatWithFileSharing({ conversationId, hotelSlug, authToken }) {
  const [messages, setMessages] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  
  // Upload files
  async function handleSend(e) {
    e.preventDefault();
    
    if (selectedFiles.length > 0) {
      // Upload with files
      await uploadFiles();
    } else if (messageText.trim()) {
      // Send text only
      await sendTextMessage();
    }
  }
  
  async function uploadFiles() {
    setUploading(true);
    try {
      const formData = new FormData();
      
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });
      
      if (messageText.trim()) {
        formData.append('message', messageText);
      }
      
      const response = await fetch(
        `/api/staff_chat/${hotelSlug}/conversations/${conversationId}/upload/`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${authToken}` },
          body: formData
        }
      );
      
      const result = await response.json();
      
      // Clear inputs
      setSelectedFiles([]);
      setMessageText('');
      fileInputRef.current.value = '';
      
      console.log('Upload success:', result);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  }
  
  function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    
    // Validate
    if (files.length > 10) {
      alert('Maximum 10 files');
      return;
    }
    
    const oversized = files.filter(f => f.size > 50 * 1024 * 1024);
    if (oversized.length > 0) {
      alert(`File too large: ${oversized[0].name}`);
      return;
    }
    
    setSelectedFiles(files);
  }
  
  function removeFile(index) {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  }
  
  return (
    <div className="chat-container">
      {/* Messages */}
      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id} className="message">
            <div className="message-text">{msg.message}</div>
            
            {/* Attachments */}
            {msg.attachments?.map(att => (
              <div key={att.id} className="attachment">
                {att.file_type === 'image' ? (
                  <img src={att.file_url} alt={att.file_name} />
                ) : (
                  <a href={att.file_url} target="_blank">
                    📎 {att.file_name}
                  </a>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
      
      {/* Input area */}
      <form onSubmit={handleSend} className="message-input">
        {/* File preview */}
        {selectedFiles.length > 0 && (
          <div className="selected-files">
            {selectedFiles.map((file, index) => (
              <div key={index} className="file-preview">
                <span>{file.name}</span>
                <button type="button" onClick={() => removeFile(index)}>
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
        
        {/* Text input */}
        <input
          type="text"
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          placeholder="Type a message..."
          disabled={uploading}
        />
        
        {/* File input (hidden) */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.xls,.xlsx"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        
        {/* Buttons */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
        >
          📎
        </button>
        
        <button type="submit" disabled={uploading}>
          {uploading ? '⏳' : '➤'}
        </button>
      </form>
    </div>
  );
}
```

---

## ✅ Summary

### What You Can Do:
1. ✅ Upload images (JPG, PNG, GIF, WebP, BMP)
2. ✅ Upload documents (PDF, Word, Excel, TXT, CSV)
3. ✅ Send files with messages
4. ✅ Send files without text (shows "[File shared]")
5. ✅ Reply to messages with files
6. ✅ Add files to existing messages
7. ✅ Upload multiple files (max 10)
8. ✅ Delete your own attachments
9. ✅ React to file messages with emojis (ONE reaction per user)
10. ✅ Real-time file sharing updates via Pusher
11. ✅ Push notifications for file uploads

### File Limits:
- **Max files**: 10 per upload
- **Max size**: 50MB per file
- **Storage**: Cloudinary (cloud)
- **Thumbnails**: Auto-generated for images

### Reactions:
- ✅ **ONE reaction per user per message** (selecting new emoji replaces old one)
- ✅ 10 emoji options available
- ✅ React to messages with files
- ✅ Real-time reaction updates

### Real-Time:
- ✅ Files appear instantly via Pusher
- ✅ Recipients get notifications
- ✅ Deletion syncs across devices
- ✅ Reactions update in real-time

**Everything is production-ready!** 🚀
