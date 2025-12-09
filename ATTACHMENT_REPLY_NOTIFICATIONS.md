# Attachment Reply Notifications Enhancement

## Overview

Enhanced the `NotificationManager` to provide specialized handling for staff chat messages that reply to messages containing attachments (images, documents, etc.). This provides richer notifications and better user experience when replying to images or files.

## What Was Added

### 1. Enhanced Reply-to-Attachment Detection

The `realtime_staff_chat_message_created()` method now:
- Automatically detects when a message is replying to a message with attachments
- Builds attachment preview data for the original message
- Includes attachment metadata in the notification payload

### 2. Specialized FCM Notifications

New `_send_attachment_reply_fcm()` method provides:
- **Smart notification titles** based on attachment type:
  - `"💬 John replied to your photo"` (single image)
  - `"💬 John replied to your photos"` (multiple images) 
  - `"💬 John replied to your file"` (documents)
  - `"💬 John replied to your files"` (multiple files)
- **Enhanced FCM data payload** with attachment context
- **Rich notification support** with original attachment URLs for preview

### 3. Enhanced Pusher Payload Structure

Reply notifications now include:
```json
{
  "category": "staff_chat",
  "type": "realtime_staff_chat_message_created",
  "payload": {
    "id": 535,
    "conversation_id": 100,
    "message": "This looks great! Can we update room 205?",
    "sender_id": 67,
    "sender_name": "Jane Smith",
    "timestamp": "2025-12-09T16:35:00Z",
    "attachments": [],
    "is_system_message": false,
    "reply_to": {
      "id": 534,
      "message": "Here's the updated floor plan",
      "sender_id": 45,
      "sender_name": "John Doe",
      "timestamp": "2025-12-09T16:30:00Z",
      "has_attachments": true,
      "attachments_preview": [
        {
          "id": 789,
          "file_name": "floor_plan.jpg",
          "file_type": "image",
          "mime_type": "image/jpeg",
          "file_url": "https://cloudinary.com/files/floor_plan.jpg",
          "thumbnail_url": "https://cloudinary.com/thumbnails/floor_plan_thumb.jpg"
        }
      ],
      "attachment_count": 1
    },
    "is_reply_to_attachment": true
  }
}
```

## How to Use

### Automatic Operation

The enhancement works **automatically** - no code changes needed in your views or serializers. When staff members reply to messages with attachments:

1. **Backend Detection**: The notification manager automatically detects the reply-to-attachment scenario
2. **Enhanced Notifications**: Participants receive specialized FCM notifications with context
3. **Rich Pusher Events**: Frontend receives attachment preview data in the event payload

### Frontend Integration

#### 1. **FCM Notification Handling**
```dart
// Flutter FCM handler can now detect attachment replies
if (data['is_reply_to_attachment'] == 'true') {
  String attachmentType = data['original_attachment_type'];
  String thumbnailUrl = data['original_thumbnail_url'];
  
  // Show rich notification with thumbnail
  showRichNotification(
    title: title, // e.g., "John replied to your photo"
    body: body,
    thumbnail: thumbnailUrl,
    attachmentType: attachmentType
  );
}
```

#### 2. **Pusher Event Handling**
```javascript
// JavaScript frontend can render reply bubbles with attachment previews
pusher.bind('realtime_staff_chat_message_created', (data) => {
  const message = data.payload;
  
  if (message.is_reply_to_attachment && message.reply_to) {
    // Render reply bubble with attachment previews
    renderReplyBubble(message.reply_to, {
      showAttachmentPreviews: true,
      attachments: message.reply_to.attachments_preview
    });
  }
  
  // Render the actual reply message
  renderMessage(message);
});
```

#### 3. **React/Vue Component Example**
```jsx
// React component for reply bubble with attachment preview
function ReplyBubble({ replyTo }) {
  if (!replyTo || !replyTo.has_attachments) return null;
  
  return (
    <div className="reply-bubble">
      <div className="reply-header">
        <span className="sender">{replyTo.sender_name}</span>
        <span className="timestamp">{formatTime(replyTo.timestamp)}</span>
      </div>
      
      <div className="reply-content">
        <p>{replyTo.message}</p>
        
        {/* Attachment previews */}
        <div className="attachment-previews">
          {replyTo.attachments_preview?.map(att => (
            <div key={att.id} className="attachment-preview">
              {att.file_type === 'image' ? (
                <img 
                  src={att.thumbnail_url || att.file_url} 
                  alt={att.file_name}
                  className="thumbnail"
                />
              ) : (
                <div className="file-icon">
                  📄 {att.file_name}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

## Configuration

No additional configuration required. The enhancement uses existing:
- FCM service configuration
- Pusher client setup  
- Staff chat message models
- Attachment serializers

## Event Flow

```
1. Staff A sends message with image attachment
   ↓
2. Staff B replies to that message
   ↓ 
3. NotificationManager.realtime_staff_chat_message_created() called
   ↓
4. System detects reply_to message has attachments
   ↓
5. Builds attachment preview data (first 3 attachments)
   ↓
6. Sends specialized FCM: "Staff B replied to your photo"
   ↓
7. Sends enhanced Pusher event with attachment previews
   ↓
8. Frontend renders reply bubble with image thumbnails
```

## Payload Structure Reference

### Standard Message (No Reply)
```json
{
  "id": 534,
  "message": "Hello everyone",
  "attachments": [],
  "reply_to": null,
  "is_reply_to_attachment": false
}
```

### Reply to Text Message
```json
{
  "id": 535,
  "message": "Thanks for the update",
  "reply_to": {
    "id": 534,
    "message": "Meeting at 3pm",
    "has_attachments": false,
    "attachments_preview": []
  },
  "is_reply_to_attachment": false
}
```

### Reply to Message with Attachments
```json
{
  "id": 536,
  "message": "Looks good!",
  "reply_to": {
    "id": 534,
    "message": "Here are the floor plans",
    "has_attachments": true,
    "attachment_count": 2,
    "attachments_preview": [
      {
        "id": 789,
        "file_name": "floor_plan_1.jpg",
        "file_type": "image", 
        "mime_type": "image/jpeg",
        "file_url": "https://cloudinary.com/files/floor_plan_1.jpg",
        "thumbnail_url": "https://cloudinary.com/thumbnails/floor_plan_1_thumb.jpg"
      },
      {
        "id": 790,
        "file_name": "floor_plan_2.pdf",
        "file_type": "document",
        "mime_type": "application/pdf", 
        "file_url": "https://cloudinary.com/files/floor_plan_2.pdf"
      }
    ]
  },
  "is_reply_to_attachment": true
}
```

## FCM Data Structure

When replying to attachments, FCM notifications include:
```json
{
  "type": "staff_chat_message",
  "message_id": "536",
  "conversation_id": "100",
  "is_reply": "true",
  "is_reply_to_attachment": "true",
  "reply_to_message_id": "534",
  "attachment_count": "2",
  "original_attachment_id": "789",
  "original_attachment_name": "floor_plan_1.jpg",
  "original_attachment_type": "image",
  "original_attachment_url": "https://cloudinary.com/files/floor_plan_1.jpg",
  "original_thumbnail_url": "https://cloudinary.com/thumbnails/floor_plan_1_thumb.jpg",
  "click_action": "FLUTTER_NOTIFICATION_CLICK",
  "route": "/staff-chat/conversation",
  "hotel_slug": "hotel-killarney"
}
```

## Benefits

1. **Better UX**: Staff see context of what they're replying to with visual previews
2. **Clearer Notifications**: FCM titles indicate reply context ("replied to your photo")
3. **Rich UI**: Frontend can render attachment previews in reply bubbles
4. **Performance**: Only first 3 attachments included in previews
5. **Backward Compatible**: Existing code continues to work unchanged

## Troubleshooting

### Debug Logging
The notification manager includes extensive logging:
```
💬 Realtime staff chat: message 536 created by staff 67
🔗 Processing reply to message 534
📎 Reply targets message with 2 attachments
🔗 Built reply_to_data with 2 attachment previews
📱 Sending attachment-aware FCM to staff 45: 💬 Jane replied to your photo
```

### Common Issues

1. **Missing attachment previews**: Check that original message `attachments` relationship is properly loaded
2. **FCM not specialized**: Verify `fcm_token` exists for recipient staff
3. **Thumbnail URLs missing**: Check Cloudinary configuration for thumbnail generation
4. **Large payload**: Attachment previews limited to first 3 items automatically

## Future Enhancements

Potential additions:
- Audio/video attachment special handling
- Attachment reaction notifications ("❤️ loved your photo") 
- Multiple attachment type mixing logic
- Attachment download progress notifications
- File sharing notifications for large documents