# Frontend Realtime Booking Integration Guide

## Overview

This guide explains how the frontend should integrate with the HotelMate realtime booking system, including the canonical data serializer and all realtime event handling for guest booking status pages.

## Core Serializer: PublicRoomBookingDetailSerializer

### Complete Data Structure

The `PublicRoomBookingDetailSerializer` is the **canonical serializer** used for both API responses and realtime event payloads. Here's the complete data structure the frontend will receive:

```json
{
  "booking_id": "BK-2025-0001",
  "confirmation_number": "HM123456",
  "status": "CONFIRMED",
  "created_at": "2025-12-28T10:30:00Z",
  "hotel": {
    "name": "Hotel Killarney",
    "slug": "hotel-killarney",
    "phone": "+353 64 663 1555",
    "email": "info@hotelkillarney.ie"
  },
  "room": {
    "type": "Deluxe Double Room",
    "code": "DDR",
    "photo": "https://example.com/room-photo.jpg"
  },
  "dates": {
    "check_in": "2025-12-30",
    "check_out": "2026-01-02",
    "nights": 3
  },
  "guests": {
    "adults": 2,
    "children": 0,
    "total": 2
  },
  "guest": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  },
  "special_requests": "Late check-in requested",
  "pricing": {
    "subtotal": "275.00",
    "taxes": "25.00", 
    "discount": "0.00",
    "total": "300.00",
    "currency": "EUR"
  },
  "promo_code": null,
  "payment_required": false,
  "payment_url": null,
  "can_cancel": true,
  "cancellation_preview": {
    "fee_amount": "30.00",
    "refund_amount": "270.00",
    "description": "Cancellation fee applies for bookings cancelled within 48 hours",
    "applied_rule": "48_hour_policy"
  },
  "checked_in_at": "2025-12-30T15:00:00Z",
  "checked_out_at": null,
  "assigned_room_number": "205"
}
```

### Key Field Explanations

#### Status Values
- `PENDING_PAYMENT` - Booking created, payment required
- `PENDING_APPROVAL` - Payment captured, awaiting staff approval
- `CONFIRMED` - Approved and ready for check-in
- `CHECKED_IN` - Guest has checked in
- `CHECKED_OUT` - Stay completed
- `CANCELLED` - Booking cancelled

#### Check-in/Room Assignment Fields
- `checked_in_at`: ISO datetime when guest checked in (null if not checked in)
- `checked_out_at`: ISO datetime when guest checked out (null if not checked out)
- `assigned_room_number`: Actual room number assigned (null if not assigned)

#### Payment Fields
- `payment_required`: Boolean - true if booking needs payment
- `payment_url`: Direct URL to payment session (only for PENDING_PAYMENT status)

#### Cancellation Fields
- `can_cancel`: Boolean - true if booking can be cancelled
- `cancellation_preview`: Object with fee breakdown (null if can't cancel)

## Realtime System Architecture

### Guest Token Authentication

Each booking automatically generates a secure guest token that provides:
- Access to booking-specific realtime events
- Authentication for the booking status page
- Secure channel subscription without exposing sensitive data

### Pusher Channel Structure

#### Guest Channels
- **Channel**: `private-guest-booking-{booking_id}`
- **Authentication**: Guest token (passed via URL parameter)
- **Events**: All booking-related updates for that specific booking

#### Staff Channels (for reference)
- **Channel**: `hotel-{hotel_slug}`
- **Authentication**: Staff session
- **Events**: Hotel-wide booking updates

### Realtime Events

The frontend should listen for these events on the guest channel:

#### 1. `guest-booking-confirmed`
**Triggered When**: Staff approves a PENDING_APPROVAL booking
```json
{
  "event": "guest-booking-confirmed",
  "booking": {
    // Complete PublicRoomBookingDetailSerializer data
    "status": "CONFIRMED",
    "payment_required": false,
    // ... all other fields
  }
}
```

#### 2. `guest-booking-checked-in`
**Triggered When**: Staff checks in the guest
```json
{
  "event": "guest-booking-checked-in", 
  "booking": {
    // Complete PublicRoomBookingDetailSerializer data
    "status": "CHECKED_IN",
    "checked_in_at": "2025-12-30T15:00:00Z",
    "assigned_room_number": "205",
    // ... all other fields
  }
}
```

#### 3. `guest-booking-cancelled`
**Triggered When**: Booking is cancelled by staff or guest
```json
{
  "event": "guest-booking-cancelled",
  "booking": {
    // Complete PublicRoomBookingDetailSerializer data
    "status": "CANCELLED",
    "can_cancel": false,
    // ... all other fields
  }
}
```

#### 4. `guest-booking-updated`
**Triggered When**: Any other booking updates (room changes, special requests, etc.)
```json
{
  "event": "guest-booking-updated",
  "booking": {
    // Complete PublicRoomBookingDetailSerializer data
    // ... all current field values
  }
}
```

## Frontend Implementation Guide

### 1. Initial Page Load

```javascript
// Extract parameters from URL
const { hotel_slug, booking_id, token } = getURLParameters();

// Load initial booking data
const bookingData = await fetch(`/api/public/hotel/${hotel_slug}/room-bookings/${booking_id}/`, {
  headers: {
    'Authorization': `GuestToken ${token}`
  }
});

// Initialize page with booking data
renderBookingStatus(bookingData);
```

### 2. Pusher Authentication

```javascript
// Configure Pusher with custom auth endpoint
const pusher = new Pusher('your-pusher-key', {
  cluster: 'your-cluster',
  authEndpoint: `/api/notifications/pusher/auth/?hotel_slug=${hotel_slug}`,
  auth: {
    headers: {
      'Authorization': `GuestToken ${token}`
    }
  }
});
```

### 3. Subscribe to Guest Channel

```javascript
// Subscribe to guest-specific channel
const guestChannel = pusher.subscribe(`private-guest-booking-${booking_id}`);

// Listen for all booking events
guestChannel.bind('guest-booking-confirmed', handleBookingUpdate);
guestChannel.bind('guest-booking-checked-in', handleBookingUpdate);
guestChannel.bind('guest-booking-cancelled', handleBookingUpdate);
guestChannel.bind('guest-booking-updated', handleBookingUpdate);
```

### 4. Handle Realtime Updates

```javascript
function handleBookingUpdate(data) {
  console.log('Booking update received:', data.event);
  
  // Update the entire booking state with fresh data
  const updatedBooking = data.booking;
  
  // Re-render the booking status page
  renderBookingStatus(updatedBooking);
  
  // Show appropriate notifications
  showUpdateNotification(data.event, updatedBooking);
}

function renderBookingStatus(booking) {
  // Update all UI elements based on current booking state
  updateBookingHeader(booking);
  updateStatusBadge(booking);
  updateCheckInInfo(booking);
  updateRoomAssignment(booking);
  updatePaymentSection(booking);
  updateCancellationOptions(booking);
}

function updateCheckInInfo(booking) {
  const checkInStatus = document.getElementById('check-in-status');
  
  if (booking.checked_in_at) {
    checkInStatus.innerHTML = `
      <div class="check-in-complete">
        ✅ Checked in: ${formatDateTime(booking.checked_in_at)}
        <br>Room: ${booking.assigned_room_number || 'Not assigned yet'}
      </div>
    `;
  } else if (booking.status === 'CONFIRMED') {
    checkInStatus.innerHTML = `
      <div class="check-in-pending">
        🕐 Ready for check-in from ${booking.dates.check_in}
      </div>
    `;
  } else {
    checkInStatus.innerHTML = `
      <div class="check-in-not-ready">
        ⏳ Check-in will be available once booking is confirmed
      </div>
    `;
  }
}
```

### 5. Status-Based UI Rendering

```javascript
function updateStatusBadge(booking) {
  const statusBadge = document.getElementById('status-badge');
  const statusClasses = {
    'PENDING_PAYMENT': 'status-pending-payment',
    'PENDING_APPROVAL': 'status-pending-approval', 
    'CONFIRMED': 'status-confirmed',
    'CHECKED_IN': 'status-checked-in',
    'CHECKED_OUT': 'status-completed',
    'CANCELLED': 'status-cancelled'
  };
  
  const statusMessages = {
    'PENDING_PAYMENT': 'Payment Required',
    'PENDING_APPROVAL': 'Awaiting Approval',
    'CONFIRMED': 'Confirmed - Ready for Check-in',
    'CHECKED_IN': 'Checked In',
    'CHECKED_OUT': 'Stay Completed', 
    'CANCELLED': 'Cancelled'
  };
  
  statusBadge.className = `status-badge ${statusClasses[booking.status]}`;
  statusBadge.textContent = statusMessages[booking.status];
}

function showUpdateNotification(event, booking) {
  const messages = {
    'guest-booking-confirmed': '🎉 Your booking has been confirmed!',
    'guest-booking-checked-in': `🏨 Welcome! You've been checked into room ${booking.assigned_room_number}`,
    'guest-booking-cancelled': '❌ Your booking has been cancelled',
    'guest-booking-updated': '📝 Your booking has been updated'
  };
  
  showToast(messages[event] || 'Booking updated');
}
```

### 6. Error Handling

```javascript
// Handle connection errors
pusher.connection.bind('error', function(err) {
  console.error('Pusher connection error:', err);
  showErrorMessage('Real-time updates temporarily unavailable');
});

// Handle authentication failures
guestChannel.bind('pusher:subscription_error', function(err) {
  console.error('Channel subscription failed:', err);
  showErrorMessage('Unable to connect to live updates');
});
```

## Complete Event Flow Example

### Scenario: Staff Checks In Guest

1. **Staff Action**: Staff member clicks "Check In" for booking BK-2025-0001 and assigns room 205

2. **Backend Processing**:
   - Updates booking: `status="CHECKED_IN"`, `checked_in_at=now()`, `assigned_room="205"`
   - Triggers realtime event with complete booking data

3. **Frontend Receives**:
   ```json
   {
     "event": "guest-booking-checked-in",
     "booking": {
       "booking_id": "BK-2025-0001",
       "status": "CHECKED_IN",
       "checked_in_at": "2025-12-30T15:00:00Z",
       "assigned_room_number": "205",
       // ... all other current booking data
     }
   }
   ```

4. **Frontend Updates**:
   - Status badge changes to "Checked In"
   - Check-in section shows completion time and room number
   - Payment section hides (if applicable)
   - Cancellation options disable
   - Shows welcome notification

## Testing Realtime Events

### Using Browser Developer Tools

```javascript
// Test connection in browser console
pusher.connection.bind('connected', () => {
  console.log('✅ Connected to Pusher');
});

// Monitor all channel events
guestChannel.bind_global((event, data) => {
  console.log('📡 Event received:', event, data);
});

// Test channel subscription
console.log('📻 Subscribed channels:', pusher.allChannels());
```

### Manual Event Testing

Staff can trigger events through the admin interface to test frontend updates:
1. Change booking status
2. Assign/change room
3. Check in guest
4. Update special requests

## Best Practices

### 1. Always Use Complete Data
- Never rely on partial updates
- Always re-render with the complete `booking` object from events
- This ensures UI consistency even if some events are missed

### 2. Graceful Fallback
- Implement periodic polling as fallback if realtime fails
- Cache last known state for offline scenarios
- Show connection status to users

### 3. Performance Optimization
- Debounce rapid successive updates
- Only re-render changed sections when possible
- Use virtual DOM or similar for efficient updates

### 4. User Experience
- Show loading states during updates
- Provide clear status messages
- Use animations for status transitions

## Security Considerations

- Guest tokens are SHA-256 hashed and time-limited
- Tokens only provide access to single booking data
- No sensitive payment information in realtime payloads
- Channel authentication prevents unauthorized access

## Troubleshooting

### Common Issues

1. **Events not received**: Check token validity and channel subscription
2. **Authentication failed**: Verify token format and expiry
3. **Partial data**: Always use complete booking object from events
4. **Connection drops**: Implement reconnection logic

### Debug Checklist

- [ ] Token included in URL and auth headers
- [ ] Pusher connection established
- [ ] Channel subscription successful 
- [ ] Event listeners bound correctly
- [ ] Error handlers implemented
- [ ] Fallback polling configured

---

This integration ensures that guests see real-time updates of their booking status, check-in progress, and room assignments as soon as staff make changes in the system.