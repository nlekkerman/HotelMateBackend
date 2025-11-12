# 🔧 Fix Pusher Real-time Updates in Frontend

## ✅ Backend Status: WORKING PERFECTLY
- Pusher broadcasts: ✅ Working
- FCM notifications: ✅ Working
- Channel: `hotel-killarney-staff-conversation-92`
- Event: `new-message`

## ❌ Problem: Frontend UI Not Updating

---

## 🎯 Solution: Add Pusher Listener in Your Frontend

### Step 1: Install Pusher (if not installed)
```bash
npm install pusher-js
```

### Step 2: Create Pusher Instance
```javascript
// In your main app file or pusher config file
import Pusher from 'pusher-js';

const pusher = new Pusher('6744ef8e4ff09af2a849', {
  cluster: 'eu',
  encrypted: true
});

export default pusher;
```

### Step 3: Subscribe to Conversation Channel
**In your chat message component or conversation view:**

```javascript
import { useEffect, useState } from 'react';
import pusher from './pusherConfig'; // your pusher instance

function ConversationView({ conversationId, hotelSlug }) {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    // 1. Subscribe to the conversation channel
    const channelName = `${hotelSlug}-staff-conversation-${conversationId}`;
    const channel = pusher.subscribe(channelName);
    
    console.log('📡 Subscribed to:', channelName); // Debug log
    
    // 2. Listen for new messages
    channel.bind('new-message', (newMessage) => {
      console.log('📨 New message received:', newMessage); // Debug log
      
      // 3. Update UI - add new message to list
      setMessages(prevMessages => [...prevMessages, newMessage]);
    });
    
    // 4. Listen for read receipts
    channel.bind('messages-read', (data) => {
      console.log('✅ Messages marked as read:', data);
      
      // Update read status in UI
      setMessages(prevMessages => 
        prevMessages.map(msg => 
          data.message_ids.includes(msg.id)
            ? { ...msg, read_by: [...msg.read_by, data.staff_id] }
            : msg
        )
      );
    });
    
    // 5. Listen for message edits
    channel.bind('message-edited', (editedMessage) => {
      console.log('✏️ Message edited:', editedMessage);
      
      setMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === editedMessage.id ? editedMessage : msg
        )
      );
    });
    
    // 6. Listen for message deletes
    channel.bind('message-deleted', (data) => {
      console.log('🗑️ Message deleted:', data.message_id);
      
      setMessages(prevMessages =>
        prevMessages.filter(msg => msg.id !== data.message_id)
      );
    });
    
    // 7. Cleanup - unsubscribe when component unmounts
    return () => {
      channel.unbind_all();
      channel.unsubscribe();
      console.log('👋 Unsubscribed from:', channelName);
    };
  }, [conversationId, hotelSlug]);

  return (
    <div>
      {messages.map(msg => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
    </div>
  );
}
```

---

## 🔍 Debug: Check if Pusher is Connected

Add this to see connection status:

```javascript
useEffect(() => {
  // Check connection state
  pusher.connection.bind('connected', () => {
    console.log('✅ Pusher CONNECTED');
  });

  pusher.connection.bind('disconnected', () => {
    console.warn('⚠️ Pusher DISCONNECTED');
  });

  pusher.connection.bind('error', (err) => {
    console.error('❌ Pusher ERROR:', err);
  });

  // Log current state
  console.log('Pusher State:', pusher.connection.state);
}, []);
```

---

## 🎯 Quick Test

**Open Browser Console (F12) and paste this:**

```javascript
// Test Pusher connection
const testPusher = new Pusher('6744ef8e4ff09af2a849', {
  cluster: 'eu',
  encrypted: true
});

testPusher.connection.bind('connected', () => {
  console.log('✅ Pusher connected!');
});

const channel = testPusher.subscribe('hotel-killarney-staff-conversation-92');

channel.bind('new-message', (data) => {
  console.log('📨 MESSAGE RECEIVED:', data);
  alert('New message: ' + data.message);
});

console.log('Listening for messages on conversation 92...');
```

Now send a message from another device/browser. You should see the alert!

---

## 📱 React Native Setup

If you're using React Native:

```bash
npm install pusher-js @react-native-community/netinfo
```

```javascript
import Pusher from 'pusher-js/react-native';

const pusher = new Pusher('6744ef8e4ff09af2a849', {
  cluster: 'eu',
  encrypted: true
});

// Rest is the same as React Web
```

---

## 🚨 Common Mistakes

### ❌ Wrong Channel Name
```javascript
// WRONG
pusher.subscribe('conversation-92'); 

// CORRECT
pusher.subscribe('hotel-killarney-staff-conversation-92');
//                ^^^^^^^^^^^^^^^^^ Must include hotel slug!
```

### ❌ Not Binding Events
```javascript
// WRONG - just subscribing doesn't update UI
const channel = pusher.subscribe(channelName);
// Nothing happens!

// CORRECT - bind to events
const channel = pusher.subscribe(channelName);
channel.bind('new-message', (data) => {
  setMessages(prev => [...prev, data]); // ← This updates UI
});
```

### ❌ Subscribing Multiple Times
```javascript
// WRONG - subscribes on every render
function Component() {
  pusher.subscribe('channel'); // ← Creates duplicate subscriptions
  return <div>...</div>;
}

// CORRECT - use useEffect
function Component() {
  useEffect(() => {
    const channel = pusher.subscribe('channel');
    return () => channel.unsubscribe(); // ← Cleanup
  }, []);
  return <div>...</div>;
}
```

---

## ✅ Checklist

- [ ] Installed `pusher-js`
- [ ] Created Pusher instance with key `6744ef8e4ff09af2a849` and cluster `eu`
- [ ] Subscribed to channel: `${hotelSlug}-staff-conversation-${conversationId}`
- [ ] Bound to `new-message` event
- [ ] Update state/UI when event received
- [ ] Added cleanup to unsubscribe
- [ ] Tested in browser console
- [ ] Checked for connection errors in console

---

## 🎉 When It Works

You should see in console:
```
✅ Pusher CONNECTED
📡 Subscribed to: hotel-killarney-staff-conversation-92
📨 New message received: { id: 133, message: "Hello", ... }
```

And your UI should update automatically without refresh!

---

## 💡 Need More Help?

1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for errors
4. Share the console output

The backend is working perfectly - just need to connect the frontend listener! 🚀
