# 🔥 Staff Chat Unread Count: Pusher Consistency Fix

## Problem Identified

Frontend logs showed **conflicting unread counts**:
```javascript
🔄 [MessengerWidget] Conversations/unread state changed: 
{totalUnreadFromContext: 0, calculatedUnread: 1}

🚨🚨 [MessengerWidget] UNREAD COUNT CHANGED - FORCING UPDATE: 
{from: 1, to: 0}
```

**Root Cause**: Pusher payload structure was ambiguous, causing frontend to receive inconsistent counts from:
1. **Pusher real-time events** - one count
2. **API responses** - different count  
3. **Component calculations** - yet another count

## Solution: Enhanced Pusher Payload

### 🔧 **Before (Ambiguous)**
```json
{
  "category": "staff_chat",
  "type": "realtime_staff_chat_unread_updated",
  "payload": {
    "staff_id": 35,
    "conversation_id": 100,
    "unread_count": 1,           // ❌ Ambiguous - could be conversation OR total
    "total_unread": null,        // ❌ Sometimes null, sometimes populated
    "updated_at": "2025-12-09T19:15:09.603Z"
  }
}
```

### ✅ **After (Explicit)**
```json
{
  "category": "staff_chat", 
  "type": "realtime_staff_chat_unread_updated",
  "payload": {
    "staff_id": 35,
    "conversation_id": 100,
    "unread_count": 1,                    // The primary count (conversation OR total based on context)
    "conversation_unread": 1,             // ✅ ALWAYS the conversation-specific count
    "total_unread": 5,                    // ✅ ALWAYS the total across all conversations
    "is_total_update": false,             // ✅ Flag indicating if this is a total count update
    "updated_at": "2025-12-09T19:15:09.603Z",
    "debug_info": {
      "conversation_provided": true,
      "unread_count_provided": false,
      "calculation_source": "conversation"
    }
  }
}
```

## Frontend Integration

### 🎯 **Updated Event Handler**
```javascript
// Handle Pusher unread count updates
pusher.bind('realtime_staff_chat_unread_updated', (eventData) => {
  const payload = eventData.payload;
  
  console.log('📊 Unread count update:', {
    conversationId: payload.conversation_id,
    conversationUnread: payload.conversation_unread,
    totalUnread: payload.total_unread,
    isTotal: payload.is_total_update
  });
  
  if (payload.is_total_update) {
    // This is a total unread count update across all conversations
    updateTotalUnreadBadge(payload.total_unread);
    
  } else {
    // This is a conversation-specific unread count update
    updateConversationBadge(payload.conversation_id, payload.conversation_unread);
    
    // Also update total badge with the accurate total
    updateTotalUnreadBadge(payload.total_unread);
  }
  
  // Force context/store update with consistent data
  dispatch({
    type: 'UPDATE_UNREAD_COUNTS',
    payload: {
      conversationId: payload.conversation_id,
      conversationUnread: payload.conversation_unread,
      totalUnread: payload.total_unread,
      timestamp: payload.updated_at
    }
  });
});
```

### 🔄 **React Context Update**
```jsx
// StaffChatContext.jsx
const handleUnreadUpdate = (eventData) => {
  const { conversation_unread, total_unread, conversation_id, is_total_update } = eventData.payload;
  
  if (is_total_update) {
    // Update total unread count only
    setTotalUnread(total_unread);
  } else {
    // Update specific conversation AND total
    setConversations(prev => prev.map(conv => 
      conv.id === conversation_id 
        ? { ...conv, unread_count: conversation_unread }
        : conv
    ));
    setTotalUnread(total_unread);
  }
  
  // No more calculation discrepancies!
  console.log('✅ Consistent unread counts:', { 
    conversationUnread: conversation_unread, 
    totalUnread: total_unread 
  });
};
```

## Backend Changes Made

### 🔧 **Enhanced Notification Manager**
1. **Always calculates both counts**: conversation-specific AND total unread
2. **Explicit payload structure**: No more ambiguous fields
3. **Debug logging**: Track count calculations for troubleshooting
4. **Atomic operations**: Ensures counts are calculated from fresh DB data

### 🔧 **Enhanced Model Methods**
1. **Atomic read operations**: Prevents race conditions in `mark_as_read_by()`
2. **Fresh DB queries**: Forces refresh to get accurate counts
3. **Debug logging**: Identifies which messages are counted as unread
4. **Sync method**: `sync_unread_counts_for_all_participants()` for manual fixes

### 🔧 **New Debug Endpoint**
```
POST /api/staff-chat/{hotel_slug}/conversations/sync-unread-counts/
```
Manually synchronizes unread counts when discrepancies are detected.

## Event Flow (Fixed)

```
1. Staff A sends message
   ↓
2. Post-save signal fires for all recipients
   ↓
3. Notification manager calculates:
   - conversation_unread = conversation.get_unread_count_for_staff(recipient)
   - total_unread = sum(all conversations for recipient)
   ↓
4. Pusher event sent with BOTH counts explicitly
   ↓
5. Frontend receives consistent data:
   - conversation_unread: 1 (for this conversation)
   - total_unread: 5 (across all conversations)
   ↓
6. No more count discrepancies! ✅
```

## Testing

### 🧪 **Test Scenarios**
1. **Send message**: Check both conversation and total counts update correctly
2. **Mark as read**: Verify counts decrease accurately  
3. **Multiple conversations**: Ensure total count is sum of all conversation counts
4. **Race conditions**: Send/read messages quickly to test atomic operations

### 🐛 **Debug Commands**
```bash
# Test Pusher event payload
curl -X POST http://localhost:8000/api/staff-chat/hotel-killarney/conversations/sync-unread-counts/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check backend logs
tail -f logs/django.log | grep "📊 Unread count"
tail -f logs/django.log | grep "🔢 Pusher unread payload"
```

### 🔍 **Frontend Debug**
```javascript
// Add to StaffChatContext.jsx
console.log('🔍 Context state:', {
  totalUnreadFromContext: totalUnread,
  conversationsWithUnread: conversations.filter(c => c.unread_count > 0),
  calculatedTotal: conversations.reduce((sum, c) => sum + c.unread_count, 0)
});
```

## Benefits

1. **✅ Eliminates count discrepancies**: Frontend receives consistent data
2. **✅ Better debugging**: Detailed logging and debug info in payloads
3. **✅ Atomic operations**: Prevents race conditions
4. **✅ Manual sync**: Debug endpoint for fixing inconsistencies
5. **✅ Future-proof**: Explicit payload structure prevents confusion

## Migration Notes

- **No breaking changes** - existing frontend code will continue working
- **Enhanced data** - frontend can now use the explicit count fields for better accuracy
- **Backward compatible** - old `unread_count` field still present
- **Opt-in debugging** - debug_info only used for troubleshooting