# Staff Chat Context - Pusher Fix

## Problem Identified ❌

Your `StaffChatContext.jsx` has several issues preventing Pusher updates:

1. **Wrong Channel Subscription**: You're listening for `new-message` on the **notification channel** (`{hotel}-staff-{id}-notifications`), but the backend **never sends that event there**
2. **Backend Only Broadcasts to Conversation Channel**: The backend only calls `broadcast_new_message()` which triggers on `{hotel}-staff-conversation-{id}` channel
3. **Race Condition**: You subscribe to conversation channels AFTER fetching conversations, causing missed events
4. **No Real-time Updates in Current View**: If you're viewing a conversation, new messages won't appear because the conversation channel handler only updates the list, not the current chat view

## What Backend Actually Does ✅

```python
# staff_chat/views_messages.py (Line ~259)
broadcast_new_message(
    hotel_slug,
    conversation.id,
    message_data
)

# staff_chat/pusher_utils.py (Line ~60)
def broadcast_new_message(hotel_slug, conversation_id, message_data):
    """Broadcast new message to all conversation participants"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "new-message",  # ← Event name
        message_data
    )

# This triggers on channel: {hotel_slug}-staff-conversation-{conversation_id}
```

**Backend does NOT send "new-message" to the notification channel!**

The notification channel is only used for:
- `message-mention` - when you're @mentioned
- `new-conversation` - when added to new conversation

## Fixed Code ✅

```jsx
// src/staff_chat/context/StaffChatContext.jsx
import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import Pusher from "pusher-js";
import { fetchConversations } from "../services/staffChatApi";
import { useAuth } from "@/context/AuthContext";

const StaffChatContext = createContext(undefined);

export const StaffChatProvider = ({ children }) => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const pusherRef = useRef(null);
  const channelsRef = useRef(new Map());

  // Get staff ID and hotel slug from user
  const staffId = user?.staff_id || user?.id;
  const hotelSlug = user?.hotel_slug;

  // Fetch staff conversations
  const fetchStaffConversations = useCallback(async () => {
    if (!hotelSlug) return;

    try {
      const res = await fetchConversations(hotelSlug);
      const convs = res?.results || res || [];
      setConversations(convs);
    } catch (err) {
      console.error("Failed to fetch staff conversations:", err);
    }
  }, [hotelSlug]);

  useEffect(() => {
    fetchStaffConversations();
  }, [fetchStaffConversations]);

  // Initialize Pusher for staff-to-staff chat
  useEffect(() => {
    if (!hotelSlug || !staffId) return;

    console.log('🔌 [STAFF CHAT] Initializing Pusher');
    console.log('🔌 Hotel:', hotelSlug, 'Staff ID:', staffId);

    const pusher = new Pusher(import.meta.env.VITE_PUSHER_KEY, {
      cluster: import.meta.env.VITE_PUSHER_CLUSTER,
      forceTLS: true,
    });
    pusherRef.current = pusher;

    pusher.connection.bind("connected", () => {
      console.log("✅ [STAFF CHAT] Pusher connected");
    });

    pusher.connection.bind("error", (err) => {
      console.error("❌ [STAFF CHAT] Pusher error:", err);
    });

    // Subscribe to personal staff notifications channel
    // This channel ONLY receives: message-mention, new-conversation
    // It does NOT receive "new-message" events!
    const staffNotificationsChannel = `${hotelSlug}-staff-${staffId}-notifications`;
    console.log('📡 [STAFF CHAT] Subscribing to notifications:', staffNotificationsChannel);
    
    const notifChannel = pusher.subscribe(staffNotificationsChannel);
    
    notifChannel.bind('pusher:subscription_succeeded', () => {
      console.log(`✅ [STAFF CHAT] Subscribed to: ${staffNotificationsChannel}`);
    });

    notifChannel.bind('pusher:subscription_error', (error) => {
      console.error(`❌ [STAFF CHAT] Subscription error:`, error);
    });
    
    // ⚠️ REMOVED: "new-message" listener here - backend doesn't send it!
    // Backend only sends: message-mention, new-conversation

    // Listen for mentions
    notifChannel.bind("message-mention", (data) => {
      console.log("🔔 [STAFF CHAT] MENTION received:", data);
      
      // Refresh conversations to update unread counts
      fetchStaffConversations();

      // Show notification
      if (
        "Notification" in window &&
        Notification.permission === "granted"
      ) {
        new Notification(`${data.sender_name} mentioned you`, {
          body: data.message || 'You were mentioned in a message',
          icon: data.sender_profile_image || "/favicon-32x32.png",
          tag: `staff-mention-${data.message_id}`,
        });
      }
    });

    // Listen for new conversation invites
    notifChannel.bind("new-conversation", (data) => {
      console.log("📬 [STAFF CHAT] NEW CONVERSATION:", data);
      
      // Refresh to show new conversation
      fetchStaffConversations();

      // Show notification
      if (
        "Notification" in window &&
        Notification.permission === "granted"
      ) {
        new Notification("Added to new conversation", {
          body: data.title || 'You were added to a conversation',
          icon: "/favicon-32x32.png",
          tag: `new-conv-${data.conversation_id}`,
        });
      }
    });

    return () => {
      notifChannel.unbind_all();
      pusher.unsubscribe(staffNotificationsChannel);
      
      channelsRef.current.forEach((ch) => {
        ch.unbind_all();
        pusher.unsubscribe(ch.name);
      });
      channelsRef.current.clear();
      pusher.disconnect();
      pusherRef.current = null;
    };
  }, [hotelSlug, staffId, fetchStaffConversations]);

  // Subscribe to individual conversation channels dynamically
  // ✅ THIS IS WHERE REAL MESSAGE UPDATES HAPPEN
  useEffect(() => {
    if (!pusherRef.current || !hotelSlug) return;

    conversations.forEach((conv) => {
      if (channelsRef.current.has(conv.id)) return;

      // THIS is where backend sends "new-message" events!
      const channelName = `${hotelSlug}-staff-conversation-${conv.id}`;
      console.log('📡 [STAFF CHAT] Subscribing to conversation:', channelName);
      
      const channel = pusherRef.current.subscribe(channelName);

      channel.bind('pusher:subscription_succeeded', () => {
        console.log(`✅ [STAFF CHAT] Subscribed to: ${channelName}`);
      });

      channel.bind('pusher:subscription_error', (error) => {
        console.error(`❌ [STAFF CHAT] Subscription error:`, error);
      });

      // ✅ THIS IS THE MAIN EVENT HANDLER FOR NEW MESSAGES
      channel.bind("new-message", (msg) => {
        console.log("📨 [STAFF CHAT] ==================== NEW MESSAGE ====================");
        console.log("📨 Channel:", channelName);
        console.log("📨 Conversation ID:", conv.id);
        console.log("📨 Message:", msg);
        console.log("📨 Current conversation:", currentConversationId);
        console.log("📨 Sender ID:", msg.sender?.id, "My ID:", staffId);
        console.log("=================================================================");
        
        // Update conversations list (for sidebar preview)
        setConversations((prev) =>
          prev.map((c) => {
            if (c.id === msg.conversation_id || c.id === conv.id) {
              return {
                ...c,
                last_message: {
                  message: msg.message || msg.content,
                  has_attachments: msg.attachments?.length > 0 || false,
                  attachments: msg.attachments || [],
                  timestamp: msg.timestamp
                },
                // Don't increment unread if this is the current conversation
                // or if I sent the message
                unread_count:
                  c.id === currentConversationId || msg.sender?.id === staffId
                    ? c.unread_count
                    : (c.unread_count || 0) + 1,
                updated_at: msg.timestamp
              };
            }
            return c;
          })
        );

        // Show desktop notification if:
        // 1. Not current conversation
        // 2. I didn't send it
        // 3. Notifications enabled
        if (
          msg.conversation_id !== currentConversationId &&
          msg.sender?.id !== staffId &&
          "Notification" in window &&
          Notification.permission === "granted"
        ) {
          const senderName = msg.sender?.full_name || msg.sender_name || 'Staff member';
          const conversationTitle = conv.title || senderName;
          
          new Notification(`${senderName} in ${conversationTitle}`, {
            body: msg.message || msg.content || 'New message',
            icon: msg.sender?.profile_image_url || "/favicon-32x32.png",
            tag: `staff-msg-${msg.id}`,
          });
        }
      });

      // ✅ Also listen for other conversation events
      channel.bind("message-edited", (data) => {
        console.log("✏️ [STAFF CHAT] Message edited:", data);
        // The StaffChatRoom component should handle this
        // But we can update last_message if it's the latest
      });

      channel.bind("message-deleted", (data) => {
        console.log("🗑️ [STAFF CHAT] Message deleted:", data);
        // The StaffChatRoom component should handle this
      });

      channel.bind("messages-read", (data) => {
        console.log("👀 [STAFF CHAT] Messages read:", data);
        // The StaffChatRoom component should handle this
      });

      channelsRef.current.set(conv.id, channel);
    });
  }, [conversations, hotelSlug, currentConversationId, staffId]);

  const markConversationRead = async (conversationId) => {
    try {
      // Update local state immediately
      setConversations((prev) =>
        prev.map((c) =>
          c.id === conversationId
            ? { ...c, unread_count: 0 }
            : c
        )
      );
      // API call will be handled by the component
    } catch (err) {
      console.error("Failed to mark conversation as read:", err);
    }
  };

  const totalUnread = conversations.reduce((sum, c) => sum + (c.unread_count || 0), 0);

  return (
    <StaffChatContext.Provider value={{
      conversations,
      fetchStaffConversations,
      markConversationRead,
      totalUnread,
      pusherInstance: pusherRef.current,
      currentConversationId,
      setCurrentConversationId
    }}>
      {children}
    </StaffChatContext.Provider>
  );
};

export const useStaffChat = () => {
  const context = useContext(StaffChatContext);
  if (context === undefined) {
    throw new Error('useStaffChat must be used within a StaffChatProvider');
  }
  return context;
};
```

## Additional Fix: StaffChatRoom Component

Your `StaffChatRoom` component also needs to listen to Pusher events to update the messages in the current view. Add this to your chat room component:

```jsx
// In your StaffChatRoom component
useEffect(() => {
  if (!pusherInstance || !hotelSlug || !conversationId) return;

  const channelName = `${hotelSlug}-staff-conversation-${conversationId}`;
  console.log('📡 [CHAT ROOM] Subscribing to:', channelName);
  
  const channel = pusherInstance.subscribe(channelName);

  channel.bind('new-message', (msg) => {
    console.log('📨 [CHAT ROOM] New message received:', msg);
    
    // Add message to chat if not already there
    setMessages((prev) => {
      // Prevent duplicates
      if (prev.some(m => m.id === msg.id)) return prev;
      return [...prev, msg];
    });
    
    // Scroll to bottom
    scrollToBottom();
  });

  channel.bind('message-edited', (data) => {
    console.log('✏️ [CHAT ROOM] Message edited:', data);
    setMessages((prev) =>
      prev.map(m => m.id === data.id ? { ...m, ...data } : m)
    );
  });

  channel.bind('message-deleted', (data) => {
    console.log('🗑️ [CHAT ROOM] Message deleted:', data);
    if (data.hard_delete) {
      setMessages((prev) => prev.filter(m => m.id !== data.message_id));
    } else {
      setMessages((prev) =>
        prev.map(m => m.id === data.message_id ? { ...m, ...data.message } : m)
      );
    }
  });

  channel.bind('messages-read', (data) => {
    console.log('👀 [CHAT ROOM] Messages read:', data);
    setMessages((prev) =>
      prev.map(m => {
        if (data.message_ids.includes(m.id)) {
          return { 
            ...m, 
            is_read: true,
            read_by: [...(m.read_by || []), data.staff_id]
          };
        }
        return m;
      })
    );
  });

  return () => {
    channel.unbind_all();
    pusherInstance.unsubscribe(channelName);
  };
}, [pusherInstance, hotelSlug, conversationId]);
```

## Summary of Changes ✅

1. **Removed "new-message" from notification channel** - Backend doesn't send it there
2. **Fixed conversation channel handler** - This is where ALL message events happen
3. **Added better logging** - Shows exactly what's happening
4. **Added message deduplication** - Prevents showing same message twice
5. **Added sender check** - Don't increment unread for your own messages
6. **Added other event handlers** - message-edited, message-deleted, messages-read
7. **StaffChatRoom needs separate subscription** - To update the actual chat view

## Testing Checklist ✅

Open browser console and verify:
- [ ] `✅ [STAFF CHAT] Subscribed to: {hotel}-staff-{id}-notifications`
- [ ] `✅ [STAFF CHAT] Subscribed to: {hotel}-staff-conversation-{id}` (for each conversation)
- [ ] When message sent: `📨 [STAFF CHAT] NEW MESSAGE` appears
- [ ] Message appears in sidebar preview
- [ ] Unread count increases
- [ ] Desktop notification shows (if not in conversation)
- [ ] In chat room: message appears in real-time

## Why It Wasn't Working Before ❌

1. You were listening for `new-message` on `{hotel}-staff-{id}-notifications` 
2. Backend NEVER sends that event there
3. Backend ONLY sends to `{hotel}-staff-conversation-{id}` channel
4. You subscribed to conversation channels AFTER fetching conversations (race condition)
5. Your chat room component wasn't listening to Pusher at all

Now it should work! 🚀
