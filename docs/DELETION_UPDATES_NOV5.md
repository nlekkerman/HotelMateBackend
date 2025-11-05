# Chat Deletion Updates - November 5, 2025

## What Changed

### 1. **Fixed Permission Bug for Guest Deletions** 🐛
**Problem:** Guests were getting "You do not have permission to delete this message" error when trying to delete their own messages.

**Solution:** Updated permission logic to explicitly allow anonymous guests to delete guest messages in their room.

### 2. **Enhanced Deletion Payloads with Context** ✨
Added contextual information to all deletion events so frontends can display appropriate messages.

---

## Updated Payload Structure

### `content-deleted` Event (Message Deletion)

```json
{
  "message_id": 123,
  "hard_delete": true,          // true = remove completely, false = soft delete
  "soft_delete": false,         // NEW: Inverse of hard_delete
  "attachment_ids": [456, 457], // IDs of attachments to remove from UI
  "deleted_by": "staff",        // NEW: "staff" or "guest"
  "original_sender": "guest",   // NEW: "staff" or "guest"
  "staff_id": 456,              // NEW: Staff ID (null if guest deleted)
  "staff_name": "John Smith",   // NEW: Staff name (null if guest deleted)
  "timestamp": "2025-11-05T10:30:00Z"  // NEW: When deletion occurred
}
```

### `attachment-deleted` Event (Attachment Deletion)

```json
{
  "message_id": 123,
  "attachment_id": 789,
  "deleted_by": "staff",        // NEW: "staff" or "guest"
  "original_sender": "guest",   // NEW: "staff" or "guest"
  "staff_id": 456,              // NEW: Staff ID (null if guest deleted)
  "staff_name": "John Smith",   // NEW: Staff name (null if guest deleted)
  "timestamp": "2025-11-05T10:30:00Z"  // NEW: When deletion occurred
}
```

---

## Channels Used (No Changes)

Deletions broadcast to:
1. **Conversation Channel:** `{hotel}-conversation-{id}-chat` (all participants)
2. **Room Channel:** `{hotel}-room-{number}-chat` (guest-specific)
3. **Deletion Channel:** `{hotel}-room-{number}-deletions` (dedicated)
4. **Staff Channels:** `{hotel}-staff-{id}-chat` (individual staff)

---

## Frontend Integration Guide

### Use the Context Fields for Better UX

```javascript
deletionChannel.bind('content-deleted', (data) => {
  const { 
    message_id, 
    soft_delete,      // Use this instead of hard_delete
    deleted_by,       // "staff" or "guest"
    original_sender,  // "staff" or "guest"
    staff_name        // Name of staff who deleted (if applicable)
  } = data;
  
  // Show contextual message based on who deleted what
  const deletedText = getContextualDeletionText(
    deleted_by, 
    original_sender, 
    staff_name, 
    isGuestView
  );
  
  // Update UI
  updateMessageAsDeleted(message_id, deletedText);
});
```

### Contextual Message Examples

| Scenario | deleted_by | original_sender | Guest View | Staff View |
|----------|------------|-----------------|------------|------------|
| Guest deletes own message | `"guest"` | `"guest"` | "You deleted this message" | "Message deleted by guest" |
| Staff deletes guest message | `"staff"` | `"guest"` | "Message removed by staff" | "You removed this message" |
| Staff deletes own message | `"staff"` | `"staff"` | "Message deleted" | "You deleted this message" |

### Helper Function

```javascript
function getContextualDeletionText(deleted_by, original_sender, staff_name, isGuestView) {
  if (isGuestView) {
    // Guest UI
    if (deleted_by === 'guest' && original_sender === 'guest') {
      return 'You deleted this message';
    }
    if (deleted_by === 'staff' && original_sender === 'guest') {
      return 'Message removed by staff';
    }
    if (deleted_by === 'staff' && original_sender === 'staff') {
      return 'Message deleted';
    }
  } else {
    // Staff UI
    if (deleted_by === 'guest' && original_sender === 'guest') {
      return 'Message deleted by guest';
    }
    if (deleted_by === 'staff') {
      return staff_name ? `Message deleted by ${staff_name}` : 'Message deleted';
    }
  }
  
  return 'Message deleted';
}
```

---

## Permission Rules (Updated)

### Staff (Authenticated Users)
- ✅ Can delete their own staff messages
- ✅ Can delete ANY guest messages (moderation)
- ✅ Can hard delete if they have manager/admin role

### Guest (Anonymous via QR/PIN)
- ✅ **Can delete ANY guest messages in their room** (FIXED)
- ❌ Cannot delete staff messages
- ❌ Cannot hard delete (only soft delete)

---

## Testing Checklist

- [ ] Guest can delete their own messages ✅ **NOW WORKS**
- [ ] Guest sees "You deleted this message"
- [ ] Staff sees "Message deleted by guest"
- [ ] Staff can delete guest messages (moderation)
- [ ] Guest sees "Message removed by staff"
- [ ] Staff can delete their own messages
- [ ] Both UIs update in real-time via deletion channel
- [ ] Attachments are removed from UI when message deleted

---

## Breaking Changes

**None!** All changes are additive:
- Existing `hard_delete` field still sent for backward compatibility
- Added `soft_delete` field (inverse of `hard_delete`) for clarity
- Added context fields that can be ignored by old clients
- No changes to channel names or existing events

---

## What Frontend Needs to Do

### Option 1: Minimal Update (Works Immediately)
Nothing! Existing deletion handling will continue to work.

### Option 2: Enhanced UX (Recommended)
1. Use `soft_delete` field instead of `hard_delete` (clearer naming)
2. Use `deleted_by` and `original_sender` to show contextual messages
3. Optionally show staff name who performed moderation

---

## Questions?

- Backend sends all deletion events to deletion channel: `{hotel}-room-{number}-deletions`
- Event name: `content-deleted` for messages, `attachment-deleted` for attachments
- All context fields are included in every deletion event
- Guest deletions now work correctly (permission bug fixed)

**Last Updated:** November 5, 2025
