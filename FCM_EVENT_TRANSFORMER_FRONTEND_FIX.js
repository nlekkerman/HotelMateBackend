// FCM EVENT TRANSFORMER - Add this to your frontend eventBus handling

// Transform FCM events to match eventBus structure
function transformFCMEvent(fcmEvent) {
  const { payload } = fcmEvent;
  
  // Extract data from FCM payload
  const fcmData = payload.data || {};
  const notification = payload.notification || {};
  
  // Determine event type from FCM data
  const eventType = fcmData.type || 'unknown';
  
  // Map FCM types to your event structure
  const eventMapping = {
    // Guest Chat FCM
    'new_chat_message': {
      category: 'guest_chat',
      type: 'staff_message_created',
      channel: `hotel-${fcmData.hotel_slug}.guest-chat.${fcmData.room_number}`
    },
    'guest_message': {
      category: 'guest_chat', 
      type: 'guest_message_created',
      channel: `hotel-${fcmData.hotel_slug}.guest-chat.${fcmData.conversation_id}`
    },
    
    // Staff Chat FCM
    'staff_chat_message': {
      category: 'staff_chat',
      type: 'message_created', 
      channel: `hotel-${fcmData.hotel_slug}.staff-chat.${fcmData.conversation_id}`
    },
    'staff_chat_mention': {
      category: 'staff_chat',
      type: 'staff_mentioned',
      channel: `hotel-${fcmData.hotel_slug}.staff-${fcmData.mentioned_staff_id}-notifications`
    },
    
    // Room Service FCM  
    'room_service_order': {
      category: 'room_service',
      type: 'order_created',
      channel: `hotel-${fcmData.hotel_slug}.room-service`
    },
    
    // Booking FCM
    'booking_confirmation': {
      category: 'booking', 
      type: 'booking_confirmed',
      channel: `hotel-${fcmData.hotel_slug}.booking`
    },
    'booking_cancellation': {
      category: 'booking',
      type: 'booking_cancelled', 
      channel: `hotel-${fcmData.hotel_slug}.booking`
    }
  };
  
  const mapping = eventMapping[eventType] || {
    category: 'system',
    type: 'fcm_message', 
    channel: `hotel-${fcmData.hotel_slug || 'unknown'}.system`
  };
  
  // Create normalized event structure
  return {
    source: 'fcm',
    channel: mapping.channel,
    eventName: mapping.type,
    payload: {
      category: mapping.category,
      type: mapping.type,
      payload: {
        // Include FCM notification data
        title: notification.title,
        body: notification.body,
        // Include all custom data
        ...fcmData,
        // Add FCM-specific metadata
        fcm_message_id: payload.messageId,
        received_at: new Date().toISOString()
      },
      meta: {
        hotel_slug: fcmData.hotel_slug || 'unknown',
        event_id: payload.messageId || Date.now().toString(),
        ts: new Date().toISOString(),
        scope: {
          fcm_source: true,
          from: payload.from
        }
      }
    }
  };
}

// Update your eventBus handler
eventBus.on('incoming_realtime_event', (event) => {
  console.log('🚏 Incoming realtime event:', event);
  
  if (event.source === 'fcm') {
    // Transform FCM event
    const transformedEvent = transformFCMEvent(event);
    console.log('🔄 Transformed FCM event:', transformedEvent);
    
    // Route through normal eventBus flow
    eventBus.emit('pusher:message', transformedEvent.payload);
    return;
  }
  
  // Handle regular Pusher events normally
  if (event.channel && event.eventName) {
    eventBus.emit('pusher:message', event.payload);
  } else {
    console.warn('⚠️ Event missing channel/eventName:', event);
  }
});

// Or update your existing routing logic:
eventBus.on('pusher:message', (data) => {
  const { category, type, payload } = data;
  
  console.log(`📨 Routing ${category}:${type} event`);
  
  switch(category) {
    case 'attendance':
      attendanceStore.handleRealtimeEvent(type, payload);
      break;
    case 'staff_chat':
      chatStore.handleRealtimeEvent(type, payload);
      break;
    case 'guest_chat':
      guestChatStore.handleRealtimeEvent(type, payload);
      break;
    case 'room_service':
      roomServiceStore.handleRealtimeEvent(type, payload);
      break;
    case 'booking':
      bookingStore.handleRealtimeEvent(type, payload);
      break;
    case 'system':
      // Handle system/FCM fallback messages
      console.log('📱 FCM system message:', payload);
      break;
    default:
      console.warn(`⚠️ Unknown event category: ${category}`, data);
  }
});