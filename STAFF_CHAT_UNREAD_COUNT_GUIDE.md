# 📊 Staff Chat Unread Count - New Implementation Guide

**🔥 Using NEW NotificationManager Logic (NOT Legacy)**

This guide shows how to implement real-time staff chat unread count updates using the unified NotificationManager approach.

## 🚀 **Backend Implementation**

### **1. Fire Unread Count Updates**

```python
from notifications.notification_manager import notification_manager

# When a new message is created (increases unread for recipients)
def create_staff_message(sender, conversation, message_text):
    # Create the message
    message = StaffChatMessage.objects.create(
        conversation=conversation,
        sender=sender,
        text=message_text
    )
    
    # Fire message created event
    notification_manager.realtime_staff_chat_message_created(message)
    
    # Update unread count for each recipient (excluding sender)
    for recipient in conversation.participants.exclude(id=sender.id):
        notification_manager.realtime_staff_chat_unread_updated(
            staff=recipient,
            conversation=conversation
            # unread_count will be auto-calculated
        )
    
    return message

# When messages are marked as read (decreases unread)
def mark_conversation_as_read(staff, conversation, message_ids):
    # Mark messages as read in database
    messages = conversation.messages.filter(
        id__in=message_ids,
        sender__ne=staff  # Don't mark own messages as "read"
    )
    
    for message in messages:
        message.read_by.add(staff)
    
    # Fire read receipt event
    notification_manager.realtime_staff_chat_message_read(
        conversation, staff, message_ids
    )
    
    # Fire unread count update (now 0 for this conversation)
    notification_manager.realtime_staff_chat_unread_updated(
        staff=staff,
        conversation=conversation,
        unread_count=0  # Explicitly set to 0 after reading
    )

# Update total unread badge (across all conversations)
def refresh_total_unread_badge(staff):
    notification_manager.realtime_staff_chat_unread_updated(
        staff=staff
        # No conversation specified = calculates total across all
    )
```

### **2. Integration in Views**

```python
# In staff_chat/views_messages.py
from notifications.notification_manager import notification_manager

@api_view(['POST'])
def send_message(request, hotel_slug, conversation_id):
    # ... create message logic ...
    
    message = StaffChatMessage.objects.create(
        conversation=conversation,
        sender=staff,
        text=message_text
    )
    
    # Fire realtime events
    notification_manager.realtime_staff_chat_message_created(message)
    
    # Update unread for recipients
    for recipient in conversation.participants.exclude(id=staff.id):
        notification_manager.realtime_staff_chat_unread_updated(
            staff=recipient,
            conversation=conversation
        )
    
    return Response(serializer.data)

@api_view(['POST'])  
def mark_as_read(request, hotel_slug, conversation_id):
    # ... mark as read logic ...
    
    # Fire unread count update
    notification_manager.realtime_staff_chat_unread_updated(
        staff=request.user.staff,
        conversation=conversation,
        unread_count=0
    )
    
    return Response({'success': True})
```

## 📡 **Pusher Event Details**

### **Channel & Event**
- **Channel**: `hotel-{hotel_slug}.staff-{staff_id}-notifications`
- **Event**: `unread_updated`
- **Category**: `staff_chat`

### **Event Data Structure**

```json
{
  "category": "staff_chat",
  "type": "unread_updated", 
  "payload": {
    "staff_id": 123,
    "conversation_id": 456,       // null for total count
    "unread_count": 3,           // count for this conversation
    "total_unread": 15,          // null for specific conversation updates
    "updated_at": "2025-12-06T10:30:00Z"
  },
  "meta": {
    "hotel_slug": "hotel-killarney",
    "event_id": "uuid-here",
    "ts": "2025-12-06T10:30:00Z"
  }
}
```

## 🎯 **Frontend Implementation**

### **1. Subscribe to Events**

```javascript
// Initialize Pusher subscription
const hotelSlug = 'hotel-killarney';
const staffId = getCurrentStaff().id;

const channel = pusher.subscribe(`hotel-${hotelSlug}.staff-${staffId}-notifications`);

// Listen for unread count updates
channel.bind('unread_updated', function(eventData) {
    if (eventData.category === 'staff_chat') {
        handleUnreadCountUpdate(eventData.payload);
    }
});
```

### **2. Update UI Components**

```javascript
function handleUnreadCountUpdate(payload) {
    const { 
        conversation_id, 
        unread_count, 
        total_unread, 
        staff_id 
    } = payload;
    
    console.log('📊 Unread count update:', payload);
    
    // Update specific conversation badge
    if (conversation_id) {
        updateConversationBadge(conversation_id, unread_count);
    }
    
    // Update total unread badge in navbar
    if (total_unread !== null) {
        updateTotalUnreadBadge(total_unread);
    }
}

function updateConversationBadge(conversationId, unreadCount) {
    const conversationElement = document.querySelector(
        `[data-conversation-id="${conversationId}"]`
    );
    
    if (!conversationElement) return;
    
    const badge = conversationElement.querySelector('.unread-badge');
    const listItem = conversationElement.closest('.conversation-item');
    
    if (unreadCount > 0) {
        // Show badge with count
        badge.textContent = unreadCount;
        badge.style.display = 'inline-block';
        badge.classList.add('has-unread');
        
        // Add visual indicator to conversation
        listItem?.classList.add('has-unread-messages');
        
        // Move to top of list if sorting by recent activity
        moveConversationToTop(conversationElement);
    } else {
        // Hide badge
        badge.style.display = 'none';
        badge.classList.remove('has-unread');
        listItem?.classList.remove('has-unread-messages');
    }
}

function updateTotalUnreadBadge(totalUnread) {
    const navBadge = document.querySelector('#staff-chat-nav-badge');
    const headerBadge = document.querySelector('#staff-chat-header-badge');
    
    // Update navigation badge
    if (navBadge) {
        if (totalUnread > 0) {
            navBadge.textContent = totalUnread > 99 ? '99+' : totalUnread;
            navBadge.style.display = 'inline-block';
            navBadge.classList.add('badge-danger');
        } else {
            navBadge.style.display = 'none';
            navBadge.classList.remove('badge-danger');
        }
    }
    
    // Update header badge  
    if (headerBadge) {
        headerBadge.textContent = totalUnread;
        headerBadge.style.display = totalUnread > 0 ? 'inline-block' : 'none';
    }
    
    // Update document title with count
    updateDocumentTitle(totalUnread);
}

function updateDocumentTitle(unreadCount) {
    const baseTitle = 'HotelMate Staff';
    document.title = unreadCount > 0 
        ? `(${unreadCount}) ${baseTitle}` 
        : baseTitle;
}
```

### **3. Vue.js Component Example**

```vue
<template>
  <div class="staff-chat-container">
    <!-- Navigation with total badge -->
    <nav class="chat-nav">
      <span class="nav-title">
        Staff Chat
        <span 
          v-if="totalUnread > 0" 
          class="badge badge-danger"
          :class="{ 'pulse': recentUpdate }"
        >
          {{ totalUnread > 99 ? '99+' : totalUnread }}
        </span>
      </span>
    </nav>
    
    <!-- Conversation List -->
    <div class="conversations-list">
      <div 
        v-for="conversation in sortedConversations" 
        :key="conversation.id"
        :data-conversation-id="conversation.id"
        class="conversation-item"
        :class="{ 
          'has-unread': conversation.unread_count > 0,
          'recent-update': conversation.recentUpdate 
        }"
        @click="openConversation(conversation)"
      >
        <div class="conversation-info">
          <h4>{{ conversation.title }}</h4>
          <p>{{ conversation.last_message_preview }}</p>
        </div>
        
        <div class="conversation-meta">
          <span class="timestamp">{{ formatTime(conversation.updated_at) }}</span>
          <span 
            v-if="conversation.unread_count > 0"
            class="unread-badge"
            :class="{ 'bounce': conversation.recentUpdate }"
          >
            {{ conversation.unread_count }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StaffChatList',
  
  data() {
    return {
      conversations: [],
      totalUnread: 0,
      recentUpdate: false,
      pusherChannel: null
    }
  },
  
  computed: {
    sortedConversations() {
      return [...this.conversations].sort((a, b) => {
        // Sort by unread first, then by recent activity
        if (a.unread_count > 0 && b.unread_count === 0) return -1;
        if (b.unread_count > 0 && a.unread_count === 0) return 1;
        return new Date(b.updated_at) - new Date(a.updated_at);
      });
    }
  },
  
  mounted() {
    this.initializePusher();
    this.loadConversations();
  },
  
  beforeDestroy() {
    if (this.pusherChannel) {
      this.pusherChannel.unbind('unread_updated');
    }
  },
  
  methods: {
    initializePusher() {
      const channel = `hotel-${this.$store.state.hotel.slug}.staff-${this.$store.state.user.staff_id}-notifications`;
      
      this.pusherChannel = this.$pusher.subscribe(channel);
      this.pusherChannel.bind('unread_updated', this.handleUnreadUpdate);
    },
    
    handleUnreadUpdate(eventData) {
      if (eventData.category !== 'staff_chat') return;
      
      const { conversation_id, unread_count, total_unread } = eventData.payload;
      
      // Update specific conversation
      if (conversation_id) {
        const conversation = this.conversations.find(c => c.id === conversation_id);
        if (conversation) {
          conversation.unread_count = unread_count;
          conversation.recentUpdate = true;
          
          // Remove animation class after delay
          setTimeout(() => {
            conversation.recentUpdate = false;
          }, 2000);
        }
      }
      
      // Update total unread
      if (total_unread !== null) {
        this.totalUnread = total_unread;
        this.recentUpdate = true;
        
        setTimeout(() => {
          this.recentUpdate = false;
        }, 1500);
      }
      
      // Play notification sound for new unreads
      if (unread_count > 0) {
        this.playNotificationSound();
      }
    },
    
    async loadConversations() {
      try {
        const response = await this.$api.get(`/staff-chat/${this.$route.params.hotelSlug}/conversations/`);
        this.conversations = response.data.results;
        
        // Calculate initial total unread
        this.totalUnread = this.conversations.reduce((sum, conv) => sum + conv.unread_count, 0);
      } catch (error) {
        console.error('Failed to load conversations:', error);
      }
    },
    
    async openConversation(conversation) {
      // Navigate to conversation
      this.$router.push({
        name: 'StaffChatConversation',
        params: { conversationId: conversation.id }
      });
      
      // Mark as read if has unread messages
      if (conversation.unread_count > 0) {
        await this.markConversationAsRead(conversation.id);
      }
    },
    
    async markConversationAsRead(conversationId) {
      try {
        await this.$api.post(`/staff-chat/${this.$route.params.hotelSlug}/conversations/${conversationId}/mark-as-read/`);
        // Unread count will be updated via Pusher event
      } catch (error) {
        console.error('Failed to mark as read:', error);
      }
    },
    
    playNotificationSound() {
      // Play subtle notification sound
      const audio = new Audio('/sounds/message-notification.mp3');
      audio.volume = 0.3;
      audio.play().catch(e => console.log('Audio play failed:', e));
    }
  }
}
</script>

<style scoped>
.conversation-item.has-unread {
  background-color: #f8f9ff;
  border-left: 3px solid #007bff;
  font-weight: 600;
}

.unread-badge {
  background: #dc3545;
  color: white;
  border-radius: 50%;
  padding: 2px 6px;
  font-size: 0.75rem;
  font-weight: bold;
  min-width: 18px;
  text-align: center;
}

.unread-badge.bounce {
  animation: bounce 0.6s ease-in-out;
}

.badge.pulse {
  animation: pulse 1s infinite;
}

@keyframes bounce {
  0%, 60%, 100% { transform: scale(1); }
  30% { transform: scale(1.2); }
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}
</style>
```

### **4. React Component Example**

```jsx
import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { usePusher } from '../hooks/usePusher';

const StaffChatList = () => {
  const [conversations, setConversations] = useState([]);
  const [totalUnread, setTotalUnread] = useState(0);
  
  const { hotelSlug, staffId } = useSelector(state => ({
    hotelSlug: state.hotel.slug,
    staffId: state.user.staff_id
  }));
  
  // Subscribe to Pusher events
  usePusher(`hotel-${hotelSlug}.staff-${staffId}-notifications`, 'unread_updated', (eventData) => {
    if (eventData.category === 'staff_chat') {
      handleUnreadUpdate(eventData.payload);
    }
  });
  
  const handleUnreadUpdate = (payload) => {
    const { conversation_id, unread_count, total_unread } = payload;
    
    // Update specific conversation
    if (conversation_id) {
      setConversations(prev => 
        prev.map(conv => 
          conv.id === conversation_id 
            ? { ...conv, unread_count, recentUpdate: true }
            : conv
        )
      );
      
      // Remove animation after delay
      setTimeout(() => {
        setConversations(prev => 
          prev.map(conv => 
            conv.id === conversation_id 
              ? { ...conv, recentUpdate: false }
              : conv
          )
        );
      }, 2000);
    }
    
    // Update total unread
    if (total_unread !== null) {
      setTotalUnread(total_unread);
      
      // Update document title
      document.title = total_unread > 0 
        ? `(${total_unread}) HotelMate Staff`
        : 'HotelMate Staff';
    }
  };
  
  return (
    <div className="staff-chat-list">
      <header className="chat-header">
        <h2>
          Staff Chat
          {totalUnread > 0 && (
            <span className="badge badge-danger ml-2">
              {totalUnread > 99 ? '99+' : totalUnread}
            </span>
          )}
        </h2>
      </header>
      
      <div className="conversations">
        {conversations.map(conversation => (
          <div 
            key={conversation.id}
            className={`conversation-item ${conversation.unread_count > 0 ? 'has-unread' : ''}`}
            data-conversation-id={conversation.id}
          >
            <div className="conversation-content">
              <h4>{conversation.title}</h4>
              <p>{conversation.last_message_preview}</p>
            </div>
            
            {conversation.unread_count > 0 && (
              <span 
                className={`unread-badge ${conversation.recentUpdate ? 'animate-bounce' : ''}`}
              >
                {conversation.unread_count}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default StaffChatList;
```

## 🎨 **CSS Animations**

```css
/* Unread conversation styling */
.conversation-item.has-unread {
  background: linear-gradient(90deg, #e3f2fd 0%, #ffffff 100%);
  border-left: 4px solid #2196f3;
  box-shadow: 0 2px 4px rgba(33, 150, 243, 0.1);
}

/* Unread badge */
.unread-badge {
  background: linear-gradient(135deg, #ff4444, #cc0000);
  color: white;
  border-radius: 12px;
  padding: 4px 8px;
  font-size: 0.75rem;
  font-weight: 700;
  min-width: 20px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Animation for new unread messages */
@keyframes unread-bounce {
  0%, 60%, 100% { transform: scale(1); }
  30% { transform: scale(1.15); }
}

.unread-badge.animate-bounce {
  animation: unread-bounce 0.6s ease-in-out;
}

/* Pulse animation for total badge */
@keyframes unread-pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
  100% { opacity: 1; transform: scale(1); }
}

.badge.animate-pulse {
  animation: unread-pulse 1.5s infinite;
}

/* Gradient background for recent updates */
.conversation-item.recent-update {
  background: linear-gradient(90deg, #fff3cd 0%, #ffffff 100%);
  transition: background 2s ease-out;
}
```

## ✅ **Key Benefits of New Approach**

1. **✅ Unified Events**: Single NotificationManager for all Pusher events
2. **✅ Real-time Updates**: Instant UI updates without polling
3. **✅ Smart Calculation**: Auto-calculates total unread when needed
4. **✅ Flexible Targeting**: Update specific conversations or total count
5. **✅ No Legacy Code**: Clean, maintainable implementation
6. **✅ Normalized Structure**: Consistent event format across domains
7. **✅ Error Handling**: Built-in Pusher error handling
8. **✅ Performance**: Efficient targeted updates

## 🚨 **Migration from Legacy**

**DON'T USE:**
- ❌ `staff_chat/pusher_utils.py` functions
- ❌ Direct `pusher_client.trigger()` calls  
- ❌ Manual channel construction
- ❌ Old event names like `new-message`

**USE INSTEAD:**
- ✅ `notification_manager.realtime_staff_chat_unread_updated()`
- ✅ Normalized event structure
- ✅ Personal notification channels
- ✅ Auto-calculated unread counts

This new implementation provides real-time, efficient unread count management with a clean, maintainable architecture!