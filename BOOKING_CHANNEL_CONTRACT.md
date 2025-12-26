# Booking Channel Contract

**Channel**: `{hotel_slug}.room-bookings`

## Event Names (Exact Match Required)

| Event Name | Purpose | Status |
|------------|---------|---------|
| `booking_created` | New booking initiated | PENDING_PAYMENT |
| `booking_confirmed` | Payment confirmed | CONFIRMED |
| `booking_updated` | Details modified | Various |
| `booking_party_updated` | Guest party changed | Various |
| `booking_cancelled` | Booking cancelled | CANCELLED |
| `booking_checked_in` | Guest checked in | CHECKED_IN |
| `booking_checked_out` | Guest checked out | COMPLETED |

## Event Schema

All events follow the normalized envelope pattern:

```json
{
  "category": "room_booking",
  "type": "booking_cancelled",
  "payload": {
    "booking_id": "BK-2025-0001",
    "status": "CANCELLED",
    "assigned_room_number": "101",
    "...": "domain-specific data"
  },
  "meta": {
    "hotel_slug": "hotel-killarney", 
    "event_id": "uuid-v4",
    "ts": "2025-12-26T10:30:00Z",
    "scope": {}
  }
}
```

## Minimum Payload Requirements

### All Events
- `booking_id` (string)
- `status` (UPPERCASE: CANCELLED, CONFIRMED, PENDING_PAYMENT, etc.)
- `check_in` (ISO date)
- `check_out` (ISO date)

### Staff UI Updates
- `assigned_room_number` (string|null) - for room assignment display
- `guest_name` (string) - for guest identification
- `confirmation_number` (string|null) - for booking lookup

### Cancellation Events
- `cancellation_reason` (string)
- `cancelled_at` (ISO timestamp)

## Frontend Integration

```javascript
const channel = pusher.subscribe(`${hotelSlug}.room-bookings`);

['booking_created', 'booking_confirmed', 'booking_updated', 
 'booking_party_updated', 'booking_cancelled', 'booking_checked_in', 
 'booking_checked_out'].forEach(eventName => {
  channel.bind(eventName, (eventData) => {
    eventBus.emit(`${eventData.category}.${eventData.type}`, eventData);
  });
});
```

## Critical Rules

1. **Status Values**: Always UPPERCASE canonical statuses (CANCELLED, not cancelled)
2. **Event Timing**: All events emit AFTER database commit via `transaction.on_commit()`
3. **Guest Notifications**: booking_confirmed sends FCM, NOT booking_created
4. **Deduplication**: Use `meta.event_id` for duplicate detection
5. **Event Ordering**: Use `meta.ts` for chronological sorting