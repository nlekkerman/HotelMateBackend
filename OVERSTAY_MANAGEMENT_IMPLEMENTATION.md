# HotelMate Backend: Overstay Management Implementation

## Overview
This document defines the canonical backend implementation for two staff actions:
1. **ACKNOWLEDGE OVERSTAY** - Staff acknowledges awareness of guest overstaying
2. **EXTEND OVERSTAY** - Staff approves and processes additional nights

## Locked Decisions

### Grace Period / Detection
- **Flag Time**: 12:00 local hotel time on the scheduled checkout date (no grace period)
- **Scope**: Only flag bookings that are `IN_HOUSE` (checked-in guests only)
- **Simplicity**: Clear, explainable rule - no complex time windows
- **Timezone**: Hotels must have `timezone` field (IANA string like "Europe/Dublin")

### Conflict Resolution
- **Method**: Deny extension with HTTP 409 if room conflict exists
- **Response**: Return suggested available rooms for manual staff room-move decision
- **No Auto-moves**: Staff handles room logistics manually

### Pricing & Payment
- **Rate Plan**: Extension nights use original booking's rate plan for consistency
- **Payment Flow**: Create PaymentIntent that requires frontend confirmation (not immediate capture)
- **Frontend Integration**: Return `payment_required=true` for frontend payment collection
- **No Saved Cards**: Assumes no saved payment method - requires frontend card collection
- **Extension Timing**: Booking is extended immediately, payment intent created for later collection (Option A approach)

### Data Strategy
- **Extension Method**: Update original `booking.checkout_date` directly
- **Acknowledge Effect**: Track acknowledgment only, no booking status change
- **New Models**: Create `OverstayIncident` and `BookingExtension` from scratch

## Data Models

### OverstayIncident

**Purpose**: Audit trail and workflow state for overstay detection/acknowledgment/resolution.

```python
class OverstayIncident(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    hotel = models.ForeignKey('hotels.Hotel', on_delete=models.CASCADE)
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE)
    
    # Detection
    expected_checkout_date = models.DateField()
    detected_at = models.DateTimeField()
    
    # Status
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('ACKED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='MEDIUM')
    
    # Acknowledgment
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, 
                                       related_name='acknowledged_overstays', on_delete=models.SET_NULL)
    acknowledged_note = models.TextField(blank=True)
    
    # Resolution
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   related_name='resolved_overstays', on_delete=models.SET_NULL)
    resolution_note = models.TextField(blank=True)
    
    # Dismissal
    dismissed_at = models.DateTimeField(null=True, blank=True)
    dismissed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    related_name='dismissed_overstays', on_delete=models.SET_NULL)
    dismissed_reason = models.TextField(blank=True)
    
    # Metadata
    meta = models.JSONField(default=dict, blank=True)  # room_id, guest_name, etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['booking'],
                condition=models.Q(status__in=['OPEN', 'ACKED']),
                name='unique_active_overstay_per_booking'
            )
        ]
        indexes = [
            models.Index(fields=['hotel', 'status']),
            models.Index(fields=['detected_at']),
        ]
```

### BookingExtension

**Purpose**: Audit trail for booking extensions with pricing and payment tracking.

```python
class BookingExtension(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    hotel = models.ForeignKey('hotels.Hotel', on_delete=models.CASCADE)
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE)
    
    # Staff tracking
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Date changes
    old_checkout_date = models.DateField()
    new_checkout_date = models.DateField()
    added_nights = models.PositiveSmallIntegerField()
    
    # Pricing
    pricing_snapshot = models.JSONField()  # nightly breakdown
    amount_delta = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    
    # Payment & Idempotency
    payment_intent_id = models.CharField(max_length=200, blank=True)
    idempotency_key = models.CharField(max_length=80, null=True, blank=True)
    
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),
        ('FAILED', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['booking', 'idempotency_key'],
                condition=models.Q(idempotency_key__isnull=False) & ~models.Q(idempotency_key=''),
                name='unique_idempotency_per_booking'
            )
        ]
        indexes = [
            models.Index(fields=['hotel', 'created_at']),
            models.Index(fields=['booking']),
        ]
```

## API Endpoints

Base path: `/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/overstay/`

**Note**: `booking_id` path param is the booking reference string (e.g. "BK-2025-0004"), not the database pk.

### 1. POST `acknowledge/`

**Purpose**: Staff acknowledges awareness of overstay

**Request Body**:
```json
{
  "note": "Guest requested late checkout, waiting on payment.",
  "dismiss": false
}
```

**Success Response (200)**:
```json
{
  "booking_id": "BK-2025-0004",
  "overstay": {
    "status": "ACKED",
    "detected_at": "2026-01-23T12:00:00Z",
    "acknowledged_at": "2026-01-23T12:05:10Z",
    "acknowledged_note": "Guest requested late checkout, waiting on payment."
  },
  "allowed_actions": ["EXTEND_OVERSTAY", "DISMISS_OVERSTAY"]
}
```

**Error Responses**:
- `404`: Booking not found in hotel
- `409`: Booking not in valid state (not checked-in)

### 2. POST `extend/`

**Purpose**: Staff approves additional nights for overstaying guest

**Request Body (Option A - New Date)**:
```json
{
  "new_checkout_date": "2026-01-25"
}
```

**Request Body (Option B - Add Nights)**:
```json
{
  "add_nights": 2
}
```

**Validation**: Exactly one of `new_checkout_date` or `add_nights` must be provided (400 otherwise).

**Request Headers** (Optional for idempotency):
```
Idempotency-Key: ext_BK-2025-0004_20260123_001
```

**Success Response (200)**:
```json
{
  "booking_id": "BK-2025-0004",
  "old_checkout_date": "2026-01-23",
  "new_checkout_date": "2026-01-25",
  "pricing": {
    "currency": "EUR",
    "added_nights": 2,
    "nightly": [
      {"date": "2026-01-23", "amount": "120.00"},
      {"date": "2026-01-24", "amount": "120.00"}
    ],
    "amount_delta": "240.00"
  },
  "payment": {
    "payment_required": true,
    "payment_intent_id": "pi_1234567890"
  },
  "overstay": {
    "status": "RESOLVED",
    "resolved_at": "2026-01-23T12:15:30Z"
  }
}
```

**Conflict Error Response (409)**:
```json
{
  "detail": "Extension conflicts with an incoming reservation for this room.",
  "conflicts": [
    {
      "room_id": 112,
      "conflicting_booking_id": "BK-2025-0009",
      "starts": "2026-01-24",
      "ends": "2026-01-26"
    }
  ],
  "suggested_rooms": [
    {
      "room_id": 245,
      "room_number": "245",
      "room_type": "Executive Suite"
    }
  ]
}
```

### 3. GET `status/` (Optional)

**Purpose**: Retrieve current overstay status for booking

**Response (200)**:
```json
{
  "booking_id": "BK-2025-0004",
  "is_overstay": true,
  "overstay": {
    "status": "OPEN",
    "detected_at": "2026-01-23T12:00:00Z",
    "expected_checkout_date": "2026-01-23",
    "hours_overdue": 8
  }
}
```

**Note**: `hours_overdue` is computed from noon local on expected_checkout_date: `max(0, (now_utc - hotel_noon_utc).total_seconds()/3600)`

## Validation & Conflict Rules

### Core Validations
1. **Hotel Scoping**: Booking must belong to specified hotel
2. **Booking Status**: Must be `IN_HOUSE` (checked-in guests only)
3. **Extension Dates**: 
   - `new_checkout_date` must be > current `checkout_date`
   - `add_nights` must be >= 1
4. **Stay Limits**: Must not exceed hotel max stay (if configured)

### Conflict Detection
1. **Room Availability**: Check if current assigned room has overlapping bookings for extension period
2. **Source of Truth**: Use canonical room assignment (booking.room OR RoomAssignment current record)
3. **Query**: Find bookings in same room overlapping `[old_checkout_date, new_checkout_date)` excluding current booking
4. **Precise Range**: Conflict exists if another booking overlaps any night from `old_checkout_date` to `new_checkout_date` (exclusive). A booking starting exactly on `new_checkout_date` is NOT a conflict.
5. **Conflict Response**: HTTP 409 with conflict details and room suggestions

### Room Suggestions Algorithm
1. **Same Type First**: Find available rooms of same `room_type` for extended period
2. **Any Available**: If no same-type rooms, suggest any available rooms
3. **Response Format**: Include `room_id`, `room_number`, and `room_type`

### Idempotency Controls
1. **Header Support**: Accept `Idempotency-Key` header on POST extend/
2. **Storage**: Store key in `BookingExtension.idempotency_key` with unique constraint
3. **Normalization**: If header missing or blank → store None (never empty string)
   ```python
   idempotency_key = request.headers.get("Idempotency-Key") or None
   if idempotency_key:
       idempotency_key = idempotency_key.strip() or None
   ```
4. **Duplicate Handling**: Return previous successful result without creating new PaymentIntent
5. **Key Format**: Suggested format: `ext_{booking_id}_{date}_{sequence}`

### Concurrency Controls
```python
with transaction.atomic():
    booking = Booking.objects.select_for_update().get(id=booking_id)
    # Re-run conflict detection inside transaction
    # Check for existing incident to avoid duplicates
    # Process extension
```

### Timezone Handling
```python
def get_hotel_noon_utc(hotel, date):
    """Convert noon local hotel time to UTC for given date"""
    # Handle DST transitions properly
    # Return timezone-aware UTC datetime
```

### Incident Resolution Logic
- **Resolve Rule**: Only resolve overstay if `new_checkout_date > today` AND it's before noon on the new checkout date
- **Edge Case**: Extension to today but after noon = still overstay
- **Deterministic**: Use same noon logic for both detection and resolution

## State Transitions

### OverstayIncident Status Flow
```
OPEN → ACKED     (on acknowledge)
OPEN → RESOLVED  (on successful extension)
ACKED → RESOLVED (on successful extension)
OPEN → DISMISSED (on dismiss)
ACKED → DISMISSED (on dismiss)
```

### Booking Changes
- **Status**: Remains `IN_HOUSE` (no status change)
- **Checkout Date**: Updated to new extended date
- **Totals**: Updated if stored at booking level

### Room Status
- **Status**: Remains `OCCUPIED` (no housekeeping status changes)
- **Assignment**: No automatic room reassignment

## Realtime Events

All events are emitted to hotel-scoped channels with booking-specific routing.

### Event Types

#### 1. booking_overstay_flagged
```json
{
  "type": "booking_overstay_flagged",
  "payload": {
    "hotel_slug": "hotel-killarney",
    "booking_id": "BK-2025-0004",
    "expected_checkout_date": "2026-01-23",
    "detected_at": "2026-01-23T12:00:00Z",
    "severity": "MEDIUM"
  },
  "meta": {
    "event_id": "evt_abc123",
    "ts": "2026-01-23T12:00:00Z"
  }
}
```

#### 2. booking_overstay_acknowledged
```json
{
  "type": "booking_overstay_acknowledged",
  "payload": {
    "hotel_slug": "hotel-killarney",
    "booking_id": "BK-2025-0004",
    "acknowledged_by": "staff_user_123",
    "acknowledged_note": "Guest requested late checkout"
  },
  "meta": {
    "event_id": "evt_def456",
    "ts": "2026-01-23T12:05:10Z"
  }
}
```

#### 3. booking_overstay_extended
```json
{
  "type": "booking_overstay_extended",
  "payload": {
    "hotel_slug": "hotel-killarney",
    "booking_id": "BK-2025-0004",
    "old_checkout_date": "2026-01-23",
    "new_checkout_date": "2026-01-25",
    "added_nights": 2,
    "amount_delta": "240.00",
    "currency": "EUR"
  },
  "meta": {
    "event_id": "evt_ghi789",
    "ts": "2026-01-23T12:15:30Z"
  }
}
```

#### 4. booking_updated
```json
{
  "type": "booking_updated",
  "payload": {
    "hotel_slug": "hotel-killarney",
    "booking_id": "BK-2025-0004",
    "changes": ["checkout_date"],
    "new_checkout_date": "2026-01-25"
  },
  "meta": {
    "event_id": "evt_jkl012",
    "ts": "2026-01-23T12:15:30Z"
  }
}
```

## Test Matrix

### Acknowledge Tests
| Test Case | Expected Result |
|-----------|----------------|
| Acknowledge new overstay | Creates incident, sets ACKED status |
| Acknowledge existing overstay | Updates existing incident |
| Acknowledge non-IN_HOUSE booking | HTTP 409 error |
| Cross-hotel access attempt | HTTP 404 error |
| Dismiss overstay | Sets DISMISSED status |

### Extend Tests
| Test Case | Expected Result |
|-----------|----------------|
| Extend with add_nights | Success, updates booking |
| Extend with new_checkout_date | Success, updates booking |
| Extend with room conflict | HTTP 409 with suggestions |
| Concurrent extension attempts | One succeeds, other gets conflict |
| Idempotent requests (same key) | Same result, no duplicate charges |
| Idempotent requests (no key) | New extension each time |
| Invalid dates (past/same day) | HTTP 400 validation error |

### Permission Tests
| Test Case | Expected Result |
|-----------|----------------|
| Staff user with correct permissions | Success |
| Staff user without overstay permissions | HTTP 403 error |
| Guest user access attempt | HTTP 403 error |
| Cross-hotel booking access | HTTP 404 error |

## Implementation Plan

### File Structure
```
room_bookings/
├── models/
│   └── overstay.py              # OverstayIncident, BookingExtension models
├── services/
│   └── overstay.py              # Business logic services
├── api/
│   └── staff/
│       ├── overstay_views.py    # API views
│       └── urls.py              # URL routing
├── migrations/
│   └── XXXX_add_overstay_models.py
└── management/
    └── commands/
        └── flag_overstay_bookings.py  # Updated command
```

### Implementation Steps

#### 1. Models & Migrations
- Create `room_bookings/models/overstay.py`
- Generate and run Django migrations
- Add model admin interfaces for debugging

#### 2. Service Layer (`room_bookings/services/overstay.py`)
```python
def get_hotel_noon_utc(hotel, date):
    """Convert noon local hotel time to UTC (DST-safe)"""
    
def detect_overstays(hotel, current_utc_datetime):
    """Detect and flag new overstays at noon hotel-local time"""
    
def acknowledge_overstay(hotel, booking, staff_user, note, dismiss=False):
    """Acknowledge overstay incident"""
    
def extend_overstay(hotel, booking, staff_user, new_checkout_date=None, add_nights=None, idempotency_key=None):
    """Extend booking and resolve overstay with idempotency support"""
    
def get_room_suggestions(hotel, start_date, end_date, current_room_type=None):
    """Find available rooms for conflict resolution"""
```

#### 3. API Views (`room_bookings/api/staff/overstay_views.py`)
```python
class OverstayAcknowledgeView(APIView):
    permission_classes = [IsStaffUser, HasOverstayPermissions]
    
class OverstayExtendView(APIView):
    permission_classes = [IsStaffUser, HasOverstayPermissions]
    
class OverstayStatusView(APIView):
    permission_classes = [IsStaffUser, HasOverstayPermissions]
```

#### 4. URL Configuration
Add to `room_bookings/api/staff/urls.py`:
```python
path('hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/overstay/', include([
    path('acknowledge/', OverstayAcknowledgeView.as_view(), name='overstay-acknowledge'),
    path('extend/', OverstayExtendView.as_view(), name='overstay-extend'),
    path('status/', OverstayStatusView.as_view(), name='overstay-status'),
]))
```

#### 5. Management Command Integration
Update `flag_overstay_bookings.py`:
```python
def handle(self, *args, **options):
    now_utc = timezone.now()
    for hotel in Hotel.objects.all():
        # Detection runs when now >= noon_local and not already flagged
        detect_overstays(hotel, now_utc)
```

**Note**: Detection job can run any time; it flags incidents when `now >= noon_local` and not already flagged. Run hourly and it will catch up automatically.

#### 6. Realtime Events Integration
- Add event emission to service functions
- Configure Pusher channels for hotel-scoped events
- Test event delivery in frontend

#### 7. Testing
- Unit tests for service functions
- Integration tests for API endpoints
- Concurrency tests for race conditions
- Permission boundary tests

### Database Indexes
```sql
-- OverstayIncident (actual table name will be room_bookings_overstayincident)
CREATE INDEX idx_overstay_hotel_status ON overstay_incident(hotel_id, status);
CREATE INDEX idx_overstay_detected_at ON overstay_incident(detected_at);

-- BookingExtension (actual table name will be room_bookings_bookingextension)
CREATE INDEX idx_extension_hotel_created ON booking_extension(hotel_id, created_at);
CREATE INDEX idx_extension_booking ON booking_extension(booking_id);
```

**Note**: SQL examples use simplified table names for readability. Django will generate actual table names like `room_bookings_overstayincident`.

## Security Considerations

### Permission Requirements
- Staff users must have `overstay_management` permission
- Hotel-scoped access control enforced at API layer
- Booking ownership validation (booking belongs to specified hotel)

### Audit Trail
- All actions logged with staff user attribution
- Immutable incident history (no deletion, only status changes)
- Extension attempts tracked regardless of success/failure

### Concurrency Safety
- Database-level unique constraints prevent duplicate incidents
- Select-for-update locking prevents race conditions
- Atomic transactions ensure consistency

## Monitoring & Alerting

### Key Metrics
- Daily overstay detection count per hotel
- Average resolution time (flagged → resolved)
- Extension success rate vs. conflict rate
- Payment completion rate for extensions

### Alerts
- High overstay count (> threshold per hotel)
- Failed payment intents for extensions
- Repeated conflicts for same room/dates
- Long-unacknowledged overstays (> 4 hours)

## Future Enhancements

### Phase 2 Features
- **Auto-room-move**: Suggest and execute room changes during extension
- **Dynamic Pricing**: Apply current rates instead of original booking rates
- **Guest Communication**: Automated notifications for overstay charges
- **Reporting Dashboard**: Overstay trends and staff performance metrics

### Integration Points
- **PMS Systems**: Sync overstay status with external property management
- **Revenue Management**: Feed extension data to pricing optimization
- **Housekeeping**: Adjust cleaning schedules based on extensions
- **Guest App**: Allow guests to request extensions self-service

---

## IMPLEMENTATION PROMPT FOR BACKEND COPILOT

**Implement the Overstay Management spec exactly as in the document above, with the following REQUIRED fixes and assumptions.**

### Required fixes (must implement)

1) **Use correct user FK**:
   - Replace any `staff.StaffUser` references with `settings.AUTH_USER_MODEL` OR the existing canonical staff user model used elsewhere in staff endpoints.

2) **Timezone-safe noon logic**:
   - Assume Hotel has `timezone` field (IANA string). If it doesn't exist, create it with default "Europe/Dublin".
   - Implement helper `get_hotel_noon_utc(hotel, date)` that converts noon local to UTC (DST-safe) and use it in detection and in computing hours_overdue.

3) **Booking identifier consistency**:
   - Booking lookup MUST match our routing. If `booking_id` in URL is a reference string like "BK-2025-0004", query by `Booking.booking_id` field (or correct field name). If pk is used, query by pk. Pick the correct approach based on existing codebase patterns.

4) **Room source-of-truth**:
   - Conflict detection MUST use the actual current assigned room (`booking.room` OR `RoomAssignment` current record). Determine which exists in our code and use that consistently.

5) **Idempotency support**:
   - Support header `Idempotency-Key` on POST extend/
   - Add `idempotency_key` field to BookingExtension with unique constraint (booking, idempotency_key) when not blank
   - Normalize: `idempotency_key = request.headers.get("Idempotency-Key") or None; if idempotency_key: idempotency_key = idempotency_key.strip() or None`
   - If same key is repeated, return the previous successful response without creating new PaymentIntent

6) **Input validation**:
   - Extend endpoint: exactly one of `new_checkout_date` or `add_nights` must be provided (400 otherwise)

7) **Payment intent semantics**:
   - Create PaymentIntent that requires frontend confirmation (return `payment_required=true` and `payment_intent_id`)
   - Do NOT assume immediate capture without a saved payment method

8) **Incident resolution rule**:
   - On extension, resolve overstay only if the booking is no longer an overstay under the noon rule for the updated checkout date
   - Use: `resolve if new_checkout_date > today OR (new_checkout_date == today AND now < noon_local)`

### Deliverables (code to generate)

- **Models**: `room_bookings/models/overstay.py`
  - OverstayIncident (with settings.AUTH_USER_MODEL FKs)
  - BookingExtension (with idempotency_key and constraints)
- **Migration**: Django migration for both models
- **Services**: `room_bookings/services/overstay.py`
  - `get_hotel_noon_utc(hotel, date)`
  - `detect_overstays(hotel, now_utc)`
  - `acknowledge_overstay(hotel, booking, staff_user, note, dismiss=False)`
  - `extend_overstay(hotel, booking, staff_user, new_checkout_date=None, add_nights=None, idempotency_key=None)`
  - `get_room_suggestions(hotel, start_date, end_date, room_type=None)`
- **API**: `room_bookings/api/staff/overstay_views.py`
  - `OverstayAcknowledgeView` (POST acknowledge/)
  - `OverstayExtendView` (POST extend/)  
  - `OverstayStatusView` (GET status/)
- **URLs**: Wire into `room_bookings/api/staff/urls.py` under:
  ```
  /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/overstay/...
  ```

### Behavior rules (from spec)

- **Detection**: At noon hotel-local on checkout date, only IN_HOUSE bookings
- **Acknowledge**: create/update incident, set ACKED, no booking status change
- **Extend**: validate dates, conflict check, suggest rooms on 409, update booking.checkout_date, create BookingExtension audit record, create payment intent, emit realtime events
- **Concurrency**: select_for_update + atomic transaction
- **Events**: Emit `booking_overstay_flagged`, `booking_overstay_acknowledged`, `booking_overstay_extended`, `booking_updated` using our existing realtime emitter wrapper

### Tests to write

Write tests covering:
- acknowledge creates incident for new overstay
- acknowledge updates existing incident
- extend success with add_nights
- extend success with new_checkout_date  
- extend conflict returns 409 + suggested_rooms
- idempotency with same key returns same result without duplicates
- idempotency without key creates new extension each time
- hotel scoping blocks cross-hotel access (404)
- non-IN_HOUSE booking returns 409
- timezone handling works correctly across DST boundaries

**Now implement all the above components with proper error handling, validation, and the exact API contracts specified in the document.**

---

*This implementation provides a solid foundation for overstay management while maintaining data integrity, audit trails, and staff workflow efficiency.*