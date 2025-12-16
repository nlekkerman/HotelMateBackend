# Frontend RoomBooking Implementation Guide

**Status**: Implementation Guide  
**Last Updated**: December 16, 2025  
**Version**: 1.0

## Required Frontend Stores

### roomBookingStore

**Purpose**: Dedicated state management for RoomBooking domain

**State Shape**:
```javascript
const roomBookingStore = {
  // Booking list management
  bookings: {
    items: [], // Array of booking objects
    loading: false,
    error: null,
    filters: {
      status: null,
      checkInDate: null, 
      search: ''
    },
    pagination: {
      page: 1,
      hasMore: false,
      total: 0
    }
  },
  
  // Current booking detail
  currentBooking: {
    data: null, // Full booking object
    loading: false,
    error: null
  },
  
  // Booking creation flow
  createBooking: {
    quote: null, // Active pricing quote
    formData: {}, // Booking form data
    loading: false,
    error: null
  },
  
  // Room assignment
  roomAssignment: {
    availableRooms: [], // Rooms available for assignment
    loading: false,
    error: null
  },
  
  // Party management  
  partyManagement: {
    members: [], // Party members for current booking
    loading: false,
    error: null
  }
};
```

**Key Management Rules**:
- Use `booking_id` as primary key (NOT database ID)
- Index bookings by `booking_id` for O(1) lookups
- Separate loading states for each operation
- Clear error states on new operations

### Store Actions Required

```javascript
// Booking list management
const fetchBookings = (hotelSlug, filters = {}) => { /* HTTP fetch */ };
const searchBookings = (hotelSlug, query) => { /* HTTP search */ };
const refreshBookings = (hotelSlug) => { /* Force refresh */ };

// Booking detail
const fetchBookingDetail = (hotelSlug, bookingId) => { /* HTTP fetch */ };
const updateBookingDetail = (hotelSlug, bookingId, updates) => { /* HTTP update */ };

// Booking lifecycle  
const confirmBooking = (hotelSlug, bookingId) => { /* HTTP confirm */ };
const cancelBooking = (hotelSlug, bookingId, reason) => { /* HTTP cancel */ };
const checkInBooking = (hotelSlug, bookingId) => { /* HTTP check-in */ };
const checkOutBooking = (hotelSlug, bookingId) => { /* HTTP check-out */ };

// Room assignment
const assignRoom = (hotelSlug, bookingId, roomId) => { /* HTTP assign */ };
const fetchAvailableRooms = (hotelSlug, roomType, date) => { /* HTTP fetch */ };

// Party management
const addPartyMember = (hotelSlug, bookingId, memberData) => { /* HTTP add */ };
const updatePartyMember = (hotelSlug, bookingId, guestId, updates) => { /* HTTP update */ };
const removePartyMember = (hotelSlug, bookingId, guestId) => { /* HTTP remove */ };

// Realtime updates (called by eventBus)
const handleRealtimeBookingUpdate = (event) => { /* Update store from realtime */ };
```

## Required Realtime Wiring

### channelRegistry Changes

**File**: `src/realtime/channelRegistry.js`

**Before**:
```javascript
// OLD: Generic booking channel
const bookingChannel = `${hotelSlug}.booking`;
pusher.subscribe(bookingChannel);
```

**After**:  
```javascript
// NEW: Separate room booking channel
const roomBookingChannel = `${hotelSlug}.room-bookings`;
pusher.subscribe(roomBookingChannel);

// Keep existing for other booking types (restaurant, spa, events)
const genericBookingChannel = `${hotelSlug}.booking`;  
pusher.subscribe(genericBookingChannel);
```

**Channel Subscription Logic**:
```javascript
// Staff dashboard needs room booking realtime
if (userRole === 'staff' && currentPage.includes('room-bookings')) {
  const roomBookingChannel = `${hotelSlug}.room-bookings`;
  subscribeToChannel(roomBookingChannel, handleRoomBookingEvents);
}

// Public booking pages NO realtime (HTTP only)
if (currentPage.includes('public/booking')) {
  // NO realtime subscription
  // Use HTTP polling if needed
}
```

### eventBus Routing

**File**: `src/realtime/eventBus.js`

**Add Room Booking Routing**:
```javascript
// Event routing by category
const eventRouter = {
  // NEW: Room booking events
  'room_booking': {
    handler: roomBookingActions.handleRealtimeEvent,
    events: [
      'booking_created',
      'booking_updated', 
      'booking_party_updated',
      'booking_cancelled',
      'booking_checked_in',
      'booking_checked_out',
      'integrity_healed',
      'party_healed', 
      'guests_healed'
    ]
  },
  
  // EXISTING: Other booking types (keep unchanged)
  'booking': {
    handler: genericBookingActions.handleRealtimeEvent,
    events: [
      'restaurant_booking_created',
      'spa_booking_updated',
      // ... other non-room bookings
    ]
  }
};

// Route events by category
function routeEvent(event) {
  const router = eventRouter[event.category];
  if (router && router.events.includes(event.type)) {
    router.handler(event);
  }
}
```

### Event Binding Pattern

```javascript
// Bind to specific events on room booking channel
const roomBookingChannel = pusher.subscribe(`${hotelSlug}.room-bookings`);

roomBookingChannel.bind('booking_created', (event) => {
  eventBus.emit('room_booking_event', event);
});

roomBookingChannel.bind('booking_updated', (event) => {
  eventBus.emit('room_booking_event', event);
});

// ... repeat for all room booking event types
```

## UI Component Realtime Rules

### Staff Dashboards (✅ Use Realtime)

**BookingListPage**:
```javascript  
// Subscribe to realtime updates
useEffect(() => {
  const unsubscribe = roomBookingStore.subscribeToRealtime(hotelSlug);
  return unsubscribe;
}, [hotelSlug]);

// Handle realtime booking updates  
const handleBookingUpdate = useCallback((event) => {
  const { booking_id } = event.meta.scope;
  
  // Update booking in list if currently displayed
  if (currentBookingIds.includes(booking_id)) {
    roomBookingStore.updateBookingFromRealtime(event.payload);
  }
}, [currentBookingIds]);
```

**BookingDetailPage**:
```javascript
// Auto-refresh on realtime events for current booking
useEffect(() => {
  const handleUpdate = (event) => {
    if (event.meta.scope?.booking_id === currentBookingId) {
      roomBookingStore.setCurrentBooking(event.payload);
    }
  };
  
  eventBus.on('room_booking_event', handleUpdate);
  return () => eventBus.off('room_booking_event', handleUpdate);
}, [currentBookingId]);
```

**CheckInDashboard**:
```javascript
// React to check-in events for room status updates
const handleCheckInEvent = useCallback((event) => {
  if (event.type === 'booking_checked_in') {
    const roomNumber = event.meta.scope?.room_number;
    updateRoomStatus(roomNumber, 'OCCUPIED');
  }
}, []);
```

### Public Booking Pages (❌ NO Realtime)

**BookingPage**: 
```javascript
// HTTP-only booking creation
const createBooking = async (bookingData) => {
  const response = await api.post(`/api/public/hotel/${hotelSlug}/bookings/`, bookingData);
  // NO realtime subscription
  // NO event listening
  return response.data;
};
```

**PaymentPage**:
```javascript
// HTTP-only payment processing
const processPayment = async (paymentData) => {
  const response = await api.post(`/api/public/hotel/${hotelSlug}/bookings/${bookingId}/payment/`, paymentData);
  // Payment confirmation via webhook + HTTP polling
  return response.data;
};
```

## Guest Journey Tracking

### Booking Creation → Payment → Confirmation

**Flow**: Public API → HTTP only → Payment webhook → Staff realtime

```javascript
// 1. Public booking creation (HTTP)
const newBooking = await createBooking(bookingData);
// Result: booking with status "PENDING_PAYMENT"

// 2. Payment processing (HTTP + webhook)
const paymentResult = await processPayment(paymentData);
// Result: payment processor handles async confirmation

// 3. Staff sees realtime update (if watching)
// Event: booking_updated with status "CONFIRMED"
// Triggered by: payment webhook updating booking
```

### Confirmation → Check-in → Check-out

**Flow**: Staff actions → Realtime updates

```javascript
// 1. Room assignment (Staff HTTP + realtime)
await assignRoom(hotelSlug, bookingId, roomId);
// Triggers: booking_updated event with assigned_room

// 2. Check-in process (Staff HTTP + realtime)  
await checkInBooking(hotelSlug, bookingId);
// Triggers: booking_checked_in event with timestamps

// 3. Check-out process (Staff HTTP + realtime)
await checkOutBooking(hotelSlug, bookingId);
// Triggers: booking_checked_out event with completion
```

### Multi-Screen Coordination

```javascript
// Staff dashboard shows live updates across multiple screens
const BookingManagerDashboard = () => {
  // List view updates automatically
  const { bookings } = useRoomBookingStore();
  
  // Detail view updates automatically  
  const currentBooking = useCurrentBooking(bookingId);
  
  // Room status updates automatically
  const roomStatuses = useRoomStatuses();
  
  // All coordinated via realtime events
  return (
    <Dashboard>
      <BookingList bookings={bookings} />
      <BookingDetail booking={currentBooking} />
      <RoomStatus rooms={roomStatuses} />
    </Dashboard>
  );
};
```

## Anti-Patterns to Avoid

### ❌ DO NOT: Mix Booking Domains
```javascript
// WRONG: Using generic booking store for room bookings
const { bookings } = useGenericBookingStore(); // ❌
// RIGHT: Use dedicated room booking store  
const { bookings } = useRoomBookingStore(); // ✅
```

### ❌ DO NOT: Trust Payload Database IDs
```javascript
// WRONG: Using database ID as key
const bookingKey = event.payload.id; // ❌ Database ID can change
// RIGHT: Use business ID as key
const bookingKey = event.payload.booking_id; // ✅ Stable business ID
```

### ❌ DO NOT: Use Realtime for Public Pages
```javascript  
// WRONG: Realtime on public booking page
useEffect(() => {
  if (isPublicPage) {
    subscribeToRealtime(hotelSlug); // ❌ Public pages are HTTP-only
  }
}, []);

// RIGHT: HTTP-only for public pages
useEffect(() => {
  if (isStaffPage) {
    subscribeToRealtime(hotelSlug); // ✅ Only staff gets realtime
  }
}, []);
```

### ❌ DO NOT: Subscribe to Wrong Channel
```javascript
// WRONG: Old generic booking channel  
pusher.subscribe(`${hotelSlug}.booking`); // ❌ Won't receive room booking events
// RIGHT: Room booking specific channel
pusher.subscribe(`${hotelSlug}.room-bookings`); // ✅ Correct channel
```

### ❌ DO NOT: Ignore Event Deduplication
```javascript
// WRONG: Processing duplicate events
const handleEvent = (event) => {
  updateBooking(event.payload); // ❌ May process same event twice
};

// RIGHT: Deduplicate by event ID
const processedEvents = new Set();
const handleEvent = (event) => {
  if (processedEvents.has(event.meta.event_id)) return; // ✅
  processedEvents.add(event.meta.event_id);
  updateBooking(event.payload);
};
```

### ❌ DO NOT: Block UI on Realtime Failures  
```javascript
// WRONG: Failing when realtime is down
if (!realtimeConnected) {
  return <ErrorMessage>Live updates unavailable</ErrorMessage>; // ❌
}

// RIGHT: Graceful degradation
return (
  <div>
    {!realtimeConnected && <Warning>Live updates paused</Warning>}
    <BookingList bookings={bookings} /> {/* ✅ Still functional */}
  </div>
);
```

## Implementation Checklist

### Phase 1: Store Setup
- [ ] Create roomBookingStore with required state shape
- [ ] Implement all required actions (fetch, update, create, etc.)
- [ ] Add proper error handling and loading states
- [ ] Set up proper key management (booking_id as primary key)

### Phase 2: Realtime Wiring  
- [ ] Update channelRegistry to subscribe to room-bookings channel
- [ ] Add room_booking category routing to eventBus
- [ ] Bind all room booking event types to handlers
- [ ] Implement event deduplication logic

### Phase 3: UI Integration
- [ ] Update staff dashboard components to use roomBookingStore
- [ ] Add realtime subscriptions to staff pages only
- [ ] Remove realtime from public booking pages
- [ ] Implement proper loading/error states

### Phase 4: Testing & Validation
- [ ] Test all booking lifecycle events (create → check-in → check-out)
- [ ] Verify multi-screen coordination works
- [ ] Test graceful degradation when realtime is down
- [ ] Validate no public pages use realtime
- [ ] Confirm proper channel separation (no crosstalk)

## Performance Optimization

### Lazy Loading
```javascript
// Only load room booking store when needed
const roomBookingStore = lazy(() => import('./stores/roomBookingStore'));

// Only subscribe to realtime on staff pages
const shouldUseRealtime = userRole === 'staff' && isRoomBookingPage;
```

### Event Batching
```javascript
// Batch multiple rapid events
const eventQueue = [];
const processEventQueue = debounce(() => {
  const events = eventQueue.splice(0);
  roomBookingStore.batchUpdateFromEvents(events);
}, 300);
```

### Memory Management
```javascript
// Clean up old processed event IDs
const MAX_PROCESSED_EVENTS = 1000;
if (processedEvents.size > MAX_PROCESSED_EVENTS) {
  const oldEvents = Array.from(processedEvents).slice(0, 500);
  oldEvents.forEach(id => processedEvents.delete(id));
}
```