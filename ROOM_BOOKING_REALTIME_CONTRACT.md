# RoomBooking Realtime Contract

**Status**: Source of Truth  
**Last Updated**: December 16, 2025  
**Version**: 1.0

## Channel Naming

### Channel Pattern
```
${hotel_slug}.room-bookings
```

**Examples**:
- `hotel-killarney.room-bookings`
- `grand-plaza.room-bookings`  
- `seaside-resort.room-bookings`

### Channel Rules
- One channel per hotel for all room booking events
- Hotel slug derived from `booking.hotel.slug`
- NO generic `.booking` channel for RoomBookings
- NO mixing with restaurant/spa/event booking channels

## Event Envelope Schema

### Standard Envelope
```json
{
  "category": "room_booking",
  "type": "booking_created",
  "payload": { /* Staff serializer data */ },
  "meta": {
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "hotel_slug": "hotel-killarney",
    "ts": "2025-12-16T15:30:00.000Z",
    "scope": {
      "booking_id": "BK-2025-0001",
      "primary_email": "john@example.com"
    }
  }
}
```

### Envelope Field Definitions
- **category**: Always `"room_booking"` (NOT `"booking"`)
- **type**: Event type string (see Event Types section)
- **payload**: Complete booking data using staff serializer
- **meta.event_id**: UUID for deduplication
- **meta.hotel_slug**: Hotel identifier for routing
- **meta.ts**: ISO 8601 timestamp when event was created
- **meta.scope**: Event-specific metadata for filtering/routing

## Event Types

### Core Booking Events

#### `booking_created`
**Triggers**: New room booking created via public API or staff interface
**Payload Source**: Staff booking detail serializer
**Scope Fields**:
```json
{
  "booking_id": "BK-2025-0001", 
  "primary_email": "john@example.com"
}
```

#### `booking_updated`  
**Triggers**: Booking details modified (status change, contact info, etc.)
**Payload Source**: Staff booking detail serializer
**Scope Fields**:
```json
{
  "booking_id": "BK-2025-0001",
  "status": "CONFIRMED"
}
```

#### `booking_party_updated`
**Triggers**: Party members added, removed, or modified
**Payload Source**: Booking party grouped serializer  
**Scope Fields**:
```json
{
  "booking_id": "BK-2025-0001"
}
```

#### `booking_cancelled`
**Triggers**: Booking cancelled by guest or staff
**Payload Source**: Staff booking detail serializer + cancellation reason
**Scope Fields**:
```json
{
  "booking_id": "BK-2025-0001",
  "reason": "Guest requested"
}
```

### Check-in/Check-out Events

#### `booking_checked_in`
**Triggers**: Guest successfully checked into assigned room
**Payload Source**: Staff booking detail serializer with room assignment
**Scope Fields**:
```json
{
  "booking_id": "BK-2025-0001", 
  "room_number": 201
}
```

#### `booking_checked_out`
**Triggers**: Guest checked out, booking completed
**Payload Source**: Staff booking detail serializer with checkout timestamp
**Scope Fields**:
```json
{
  "booking_id": "BK-2025-0001",
  "room_number": 201
}
```

### System Healing Events  

#### `integrity_healed`
**Triggers**: Auto-heal service fixes booking data integrity issues
**Payload Source**: Healing report summary
**Scope Fields**:
```json
{
  "healing_type": "auto_heal",
  "changes_count": 3
}
```

#### `party_healed`
**Triggers**: Booking party integrity issues resolved  
**Payload Source**: Updated party structure after healing
**Scope Fields**:
```json
{
  "booking_id": "BK-2025-0001",
  "party_size": 2
}
```

#### `guests_healed`
**Triggers**: In-house guest data reconciled with booking  
**Payload Source**: Updated guest assignments after healing
**Scope Fields**:
```json
{
  "booking_id": "BK-2025-0001", 
  "room_number": 201
}
```

## Payload Data Source

### Staff Serializer Authority
All realtime payloads use **staff-level serializers** as the source of truth:

- `StaffRoomBookingDetailSerializer` - Full booking data
- `BookingPartyGroupedSerializer` - Party member data  
- Healing serializers - System maintenance data

### Payload Consistency Rules
- Payload always reflects post-operation state
- All staff-visible fields included (no public API filtering)
- Sensitive fields (payment details) included for authorized staff
- Computed fields (nights, guest names) included for convenience

## Event Deduplication

### Event ID Usage
```javascript
// Client-side deduplication
const processedEvents = new Set();

if (processedEvents.has(event.meta.event_id)) {
  return; // Skip duplicate event
}
processedEvents.add(event.meta.event_id);
```

### Deduplication Rules
- Each event has unique `meta.event_id` (UUID)
- Frontend MUST track processed event IDs  
- Event IDs are globally unique across all event types
- Safe to process same event multiple times (idempotent operations)

## Scope-Based Filtering

### Staff Dashboard Filtering
Staff dashboards should react to events based on scope:

```javascript
// Example: Only react to events for bookings currently displayed
function shouldProcessEvent(event, currentBookingIds) {
  const bookingId = event.meta.scope?.booking_id;
  return bookingId && currentBookingIds.includes(bookingId);
}
```

### Room-Based Filtering  
```javascript
// Example: Room status dashboard filtering by room number
function shouldProcessRoomEvent(event, monitoredRooms) {
  const roomNumber = event.meta.scope?.room_number;
  return roomNumber && monitoredRooms.includes(roomNumber);
}
```

### Scope Field Guarantee
- `booking_id` present in all booking-specific events
- `room_number` present when room is assigned
- Additional scope fields provide event-specific context
- Scope fields never contain sensitive data

## Realtime Usage Rules

### ✅ MUST Use Realtime For:
- Staff dashboard live updates
- Booking status changes in staff UI
- Room occupancy status updates
- Party member management
- Check-in/check-out status tracking
- Multi-staff coordination (prevent conflicts)

### ❌ MUST NOT Use Realtime For:
- Public booking creation flow (HTTP only)
- Payment processing (webhook + HTTP only)
- Guest-facing booking confirmations
- Initial page load data (always fetch via HTTP)
- Authentication or authorization decisions

### Frontend Responsibilities  
- Subscribe to hotel-specific channel: `${hotelSlug}.room-bookings`
- Filter events by `category: "room_booking"` 
- Validate event structure before processing
- Handle network reconnection gracefully
- Fallback to HTTP refresh on connection issues

## WebSocket Connection Management

### Subscription Pattern
```javascript
// Subscribe to hotel's room booking channel
const channel = `${hotelSlug}.room-bookings`;
pusher.subscribe(channel);

// Bind to all room booking events
pusher.bind('booking_created', handleRoomBookingEvent);
pusher.bind('booking_updated', handleRoomBookingEvent);
pusher.bind('booking_party_updated', handleRoomBookingEvent);
// ... etc for all event types
```

### Error Handling
- Connection failures: Show "Live updates disconnected" indicator
- Invalid events: Log error, continue processing other events  
- Parse errors: Skip malformed events, don't crash UI
- Authentication errors: Redirect to login

## Event Ordering

### Timestamp Authority
- `meta.ts` indicates when event was created on server
- Events may arrive out of order due to network latency
- Frontend should handle out-of-order events gracefully
- Use HTTP refresh for critical ordering requirements

### Conflict Resolution
- Later `meta.ts` wins for conflicting updates
- Check-in/check-out events always take precedence
- Status changes follow lifecycle rules (see domain doc)
- When in doubt, refresh from HTTP API

## Security Considerations  

### Authorization
- WebSocket connection requires valid JWT token
- Events only sent to authenticated staff with hotel access
- No guest-sensitive data in realtime (use direct notifications)
- Payment data only in events for authorized financial staff

### Data Exposure
- All events contain full staff-level data
- Assume realtime events are logged/monitored  
- No PCI data in realtime payloads
- Guest personal data limited to business necessity

## Performance Characteristics

### Event Volume Expectations
- Peak: ~10 events/minute per hotel (busy check-in)
- Average: ~2 events/minute per hotel
- Healing events: Infrequent bursts (~1/day per hotel)

### Client Resource Usage
- Keep processed event IDs in memory (max 1000 recent)
- Debounce rapid successive events (300ms)
- Batch UI updates for performance
- Clean up old event tracking data periodically

## Migration and Compatibility  

### Channel Migration Complete
- OLD: `${hotelSlug}.booking` (deprecated, RoomBookings removed)
- NEW: `${hotelSlug}.room-bookings` (active for RoomBookings)

### Category Migration Complete
- OLD: `category: "booking"` (deprecated for RoomBookings)  
- NEW: `category: "room_booking"` (active for RoomBookings)

### No Legacy Support
- No dual-channel publishing
- No category compatibility layer
- Frontend MUST update to new patterns
- Old subscriptions will not receive RoomBooking events