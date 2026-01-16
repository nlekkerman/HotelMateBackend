# Backend Contract Check: Check-in / Check-out → Status + Realtime

**Generated**: January 16, 2026  
**Purpose**: Confirm canonical backend behavior for check-in and check-out operations before frontend integration

---

## Executive Summary

✅ **CHECK-IN AND CHECK-OUT ARE FULLY IMPLEMENTED** with proper database updates, realtime events, and transaction safety.

**Key Findings**:
- Check-in/out endpoints use centralized services with atomic transactions
- Room status properly transitions through housekeeping workflow states  
- Comprehensive realtime events are emitted to multiple channels
- All operations are deduplicated and idempotent
- Transaction safety ensures realtime events only fire after commit

---

## 1️⃣ CHECK-IN BEHAVIOR

### Endpoint
```
POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/check-in/
```

**Implementation**: [`hotel/staff_views.py:2476`](hotel/staff_views.py#L2476) - `BookingCheckInView`

### Database Changes

#### 🏨 **Room Model Updates**
| Field | Before | After | Service |
|-------|--------|-------|---------|
| `is_occupied` | `false` | `true` | Direct update |
| `room_status` | `READY_FOR_GUEST` | `OCCUPIED` | `housekeeping.services.set_room_status()` |

#### 📋 **Booking Model Updates**
| Field | Before | After | Notes |
|-------|--------|-------|-------|
| `checked_in_at` | `null` | `timezone.now()` | Timestamp set |
| `status` | `CONFIRMED` | No change | Status unchanged during check-in |

#### 👥 **Guest Records Created**
- Creates/updates `Guest` objects for all `BookingGuest` party members
- Sets primary guest relationships for companions
- Idempotent creation using `get_or_create()` with `booking_guest` FK

#### 🔑 **Token Generation**
- Generates fresh `GuestBookingToken` with `CHAT` purpose
- Scopes: `['STATUS_READ', 'CHAT', 'ROOM_SERVICE']`
- Returns raw token in API response for guest portal access

### Validation & Business Rules
- Validates check-in policy timing (hotel-specific rules)
- Ensures booking has assigned room
- Blocks if already checked in (idempotent)
- Validates party completion (all guests must be named)

---

## 2️⃣ CHECK-OUT BEHAVIOR

### Endpoint
```
POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/check-out/
```

**Implementation**: [`hotel/staff_views.py:2620`](hotel/staff_views.py#L2620) - `BookingCheckOutView`  
**Service**: [`room_bookings/services/checkout.py`](room_bookings/services/checkout.py) - `checkout_booking()`

### Database Changes

#### 🏨 **Room Model Updates**
| Field | Before | After | Service |
|-------|--------|-------|---------|
| `is_occupied` | `true` | `false` | Direct update |
| `room_status` | `OCCUPIED` | `CHECKOUT_DIRTY` | `housekeeping.services.set_room_status()` |
| `guest_fcm_token` | `<token>` | `null` | Direct update |

#### 📋 **Booking Model Updates**  
| Field | Before | After | Notes |
|-------|--------|-------|-------|
| `checked_out_at` | `null` | `timezone.now()` | Timestamp set |
| `status` | `CONFIRMED` | `COMPLETED` | Final status |

#### 👥 **Guest Records Cleanup**
- Detaches all `Guest.room` references (sets to `null`)
- Maintains `Guest.booking` links for historical records
- Handles corrupted guest-booking relationships
- Consistency check: ensures room has no remaining guests

#### 🔑 **Token Revocation**
- Revokes all active `GuestBookingToken` records
- Sets status to `REVOKED` with timestamp and reason
- Prevents continued guest portal access

#### 🧹 **Additional Cleanup**
- Deletes `Conversation` and `RoomMessage` records
- Clears `Order` and `BreakfastOrder` records
- Adds turnover notes for housekeeping tracking

---

## 3️⃣ REALTIME EVENTS EMISSIONS

### CHECK-IN Events

#### Staff Channel Events
| Event | Channel | Payload Shape |
|-------|---------|---------------|
| `booking_checked_in` | `staff-hotel-{hotel_id}` | Complete booking + room + guest data |
| `room_occupancy_updated` | `{hotel_slug}.rooms` | Room occupancy + current booking info |
| `room_updated` | `{hotel_slug}.rooms` | Full room state + change metadata |

#### Guest Channel Events
| Event | Channel | Payload Shape |
|-------|---------|---------------|
| `booking_checked_in` | `private-guest-booking.{booking_id}` | Status + room assignment + fresh token |

### CHECK-OUT Events

#### Staff Channel Events
| Event | Channel | Payload Shape |
|-------|---------|---------------|
| `booking_checked_out` | `staff-hotel-{hotel_id}` | Complete booking data + checkout timestamp |
| `room_occupancy_updated` | `{hotel_slug}.rooms` | Room occupancy cleared + booking removal |
| `room_updated` | `{hotel_slug}.rooms` | Room status → CHECKOUT_DIRTY + metadata |

#### Guest Channel Events  
| Event | Channel | Payload Shape |
|-------|---------|---------------|
| `booking_checked_out` | `private-guest-booking.{booking_id}` | Status COMPLETED + checkout confirmation |

### Event Payload Requirements

#### ✅ **Rooms Channel Payloads Include**:
- `room_number` (always present - required by frontend roomsStore)
- `room_id`, `room_status`, `is_occupied` 
- `maintenance_required`, `is_out_of_order`
- `guests_in_room` array with guest details
- `changed_fields` array for targeted updates
- `meta.event_id` for deduplication
- `category: "rooms"` and `event_type: "room_updated"`

#### 📋 **Booking Channel Payloads Include**:
- Complete booking serialization with canonical serializers
- Room assignment details when applicable
- Party member information
- Status transition metadata
- Timestamps in ISO format

---

## 4️⃣ ORDERING & ATOMICITY

### Transaction Safety ✅
- **Check-in**: Wrapped in `@transaction.atomic` with `select_for_update` locks
- **Check-out**: Service uses `@transaction.atomic` with room/booking locking
- **Idempotent Operations**: Both check-in and check-out handle duplicate calls gracefully

### Realtime Event Ordering ✅
- **Critical**: All realtime events use `transaction.on_commit()` lambdas
- Events only fire AFTER successful database commit
- No risk of stale data or phantom updates
- Multiple events emitted in sequence for complete frontend synchronization

### Error Handling ✅
- Room status changes via `housekeeping.services.set_room_status()` with validation
- Critical failures (room status update) abort entire operation
- Non-critical failures (survey email, token revocation) logged but don't block operation
- Comprehensive error responses with structured error codes

---

## 5️⃣ CHANNEL ARCHITECTURE

### Primary Channels

#### `{hotel_slug}.rooms` 
- **Purpose**: Real-time room state updates for Rooms UI
- **Events**: `room_updated`, `room_occupancy_updated` 
- **Consumers**: Staff dashboard, housekeeping interface
- **Payload**: Always includes `room_number` for roomsStore updates

#### `staff-hotel-{hotel_id}`
- **Purpose**: Staff-scoped booking management events  
- **Events**: `booking_checked_in`, `booking_checked_out`, `booking_updated`
- **Consumers**: Staff booking management UI
- **Payload**: Complete booking details with canonical serializers

#### `private-guest-booking.{booking_id}`
- **Purpose**: Guest-scoped booking status updates
- **Events**: `booking_checked_in`, `booking_checked_out`, `booking_room_assigned`
- **Consumers**: Guest mobile app and web portal
- **Payload**: Guest-appropriate data with privacy filtering

### No Missing Emissions ✅
All check-in/out operations properly emit to required channels. The implementation uses the centralized `NotificationManager` which handles:

- Staff notification consolidation
- Guest privacy-filtered events  
- Deduplication via event IDs
- Error handling with fallback logging

---

## 6️⃣ HOUSEKEEPING INTEGRATION

### Room Status Workflow
```
CHECK-IN:  READY_FOR_GUEST → OCCUPIED
CHECK-OUT: OCCUPIED → CHECKOUT_DIRTY
```

### Canonical Service Integration ✅
- Uses `housekeeping.services.set_room_status()` for all room status changes
- Creates audit trail in `RoomStatusEvent` table
- Enforces status transition validation and permissions
- Emits room-level realtime events automatically via `transaction.on_commit()`

### Turnover Workflow Ready ✅
- Check-out properly sets `CHECKOUT_DIRTY` status
- Rooms require housekeeping workflow completion to become `READY_FOR_GUEST`
- Integration with cleaning/inspection endpoints already implemented
- Maintenance flags and notes properly managed

---

## 7️⃣ VALIDATION SUMMARY

### ✅ **Confirmed Canonical Behaviors**

| Requirement | Implementation | Status |
|-------------|----------------|---------|
| Room status updates | `housekeeping.services.set_room_status()` | ✅ Complete |
| Booking lifecycle | Atomic transactions with proper status flow | ✅ Complete |
| Guest management | Idempotent creation/cleanup with relationship integrity | ✅ Complete |
| Realtime events | Multi-channel emission with payload consistency | ✅ Complete |
| Transaction safety | `on_commit()` pattern prevents stale reads | ✅ Complete |
| Error handling | Structured responses with rollback on critical failures | ✅ Complete |
| Token management | Fresh generation on check-in, revocation on check-out | ✅ Complete |

### 📱 **Frontend Integration Ready**

The backend contract is **fully ready** for frontend integration:

1. **Rooms UI**: Subscribe to `{hotel_slug}.rooms` channel for live updates
2. **Bookings UI**: Subscribe to `staff-hotel-{hotel_id}` for booking state changes  
3. **Guest App**: Subscribe to `private-guest-booking.{booking_id}` for status updates
4. **No Optimistic Updates**: Frontend can rely entirely on realtime events
5. **Consistent Payloads**: All events include required fields for UI updates

---

## 8️⃣ IMPLEMENTATION FILES

### Core Endpoints
- [`hotel/staff_views.py:2476-2620`](hotel/staff_views.py#L2476-L2620) - Check-in/out views
- [`room_bookings/staff_urls.py:113-120`](room_bookings/staff_urls.py#L113-L120) - URL routing
- [`room_bookings/services/checkout.py`](room_bookings/services/checkout.py) - Centralized checkout logic

### Supporting Services  
- [`housekeeping/services.py:18-175`](housekeeping/services.py#L18-L175) - Room status management
- [`notifications/notification_manager.py:1494-1631`](notifications/notification_manager.py#L1494-L1631) - Realtime events
- [`hotel/models.py`](hotel/models.py) - Token and booking models

### Database Models
- [`rooms/models.py:37-45`](rooms/models.py#L37-L45) - Room status choices
- [`hotel/models.py`](hotel/models.py) - Booking and token models
- [`guests/models.py`](guests/models.py) - Guest management

---

## ✅ CONCLUSION

**The check-in and check-out backend implementation is production-ready and fully supports the frontend requirements.**

- **Single Channel**: `${hotelSlug}.rooms` properly receives all room updates
- **No Optimistic UI**: All state changes are server-driven with realtime propagation
- **Atomic Operations**: Transaction safety prevents inconsistent states
- **Complete Payloads**: All required fields are included in realtime events
- **Error Resilience**: Proper validation and rollback handling

The frontend can proceed with confidence that the backend contract is stable and comprehensive.