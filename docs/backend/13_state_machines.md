# 13. State Machines and Business Logic Workflows

This document describes the key state machines and business logic workflows in the HotelMate backend.

## 1. Room Booking State Machine

The room booking lifecycle follows a strict state machine with the following states and transitions:

### Booking States

**States Definition:** `hotel/models.py` lines 625-636

```python
STATUS_CHOICES = [
    ('PENDING_PAYMENT', 'Pending Payment'),
    ('PENDING_APPROVAL', 'Pending Staff Approval'),  # NEW: Authorization pending
    ('CONFIRMED', 'Confirmed'),
    ('IN_HOUSE', 'In House'),  # NEW: Guest checked in
    ('DECLINED', 'Declined'),  # NEW: Authorization cancelled
    ('CANCELLED', 'Cancelled'),
    ('CANCELLED_DRAFT', 'Cancelled Draft'),  # NEW: Expired unpaid bookings
    ('EXPIRED', 'Expired'),  # NEW: Auto-expired due to timeout
    ('COMPLETED', 'Completed'),
    ('NO_SHOW', 'No Show'),
]
```

### State Transitions

**Initial State:** `PENDING_PAYMENT` (default)

**Valid Transitions:**

1. **PENDING_PAYMENT → PENDING_APPROVAL**
   - Trigger: Payment authorization successful
   - Action: Payment hold created, awaiting staff approval
   - Fields: `payment_intent_id`, `payment_authorized_at`, `approval_deadline_at`

2. **PENDING_PAYMENT → CANCELLED_DRAFT**
   - Trigger: Booking expiry timeout (15 minutes)
   - Action: Auto-cleanup of unpaid bookings
   - Fields: `expires_at`, `expired_at`

3. **PENDING_APPROVAL → CONFIRMED**
   - Trigger: Staff approval within SLA
   - Action: Payment capture, booking confirmed
   - Fields: `decision_by`, `decision_at`, `paid_at`

4. **PENDING_APPROVAL → DECLINED**
   - Trigger: Staff rejection
   - Action: Payment authorization voided
   - Fields: `decision_by`, `decision_at`, `decline_reason_code`

5. **PENDING_APPROVAL → EXPIRED**
   - Trigger: Approval timeout (configurable SLA)
   - Action: Auto-decline and void payment
   - Fields: `approval_deadline_at`, `auto_expire_reason_code`

6. **CONFIRMED → IN_HOUSE**
   - Trigger: Guest check-in process
   - Action: Room assignment and access granted

7. **CONFIRMED → CANCELLED**
   - Trigger: Guest or staff cancellation
   - Action: Refund processing (policy-dependent)

8. **CONFIRMED → NO_SHOW**
   - Trigger: No check-in by cutoff time
   - Action: No-show penalty processing

9. **IN_HOUSE → COMPLETED**
   - Trigger: Successful check-out
   - Action: Final billing and room release

### Timing Controls

**Configuration:** `HotelAccessConfig` model (`hotel/models.py` lines 369-388)

```python
# Checkout timing
standard_checkout_time = models.TimeField(default="11:00")
late_checkout_grace_minutes = models.PositiveIntegerField(default=30)

# Approval timing
approval_sla_minutes = models.PositiveIntegerField(default=30)
approval_cutoff_time = models.TimeField(default="22:00")
approval_cutoff_day_offset = models.PositiveSmallIntegerField(default=0)
```

**Evidence:** `hotel/models.py` lines 369-388

## 2. Room Status State Machine

Rooms follow a turnover workflow state machine for housekeeping operations:

### Room States

**States Definition:** `rooms/models.py` lines 36-44

```python
ROOM_STATUS_CHOICES = [
    ('OCCUPIED', 'Occupied'),
    ('CHECKOUT_DIRTY', 'Checkout Dirty'),
    ('CLEANING_IN_PROGRESS', 'Cleaning in Progress'),
    ('CLEANED_UNINSPECTED', 'Cleaned Uninspected'), 
    ('MAINTENANCE_REQUIRED', 'Maintenance Required'),
    ('OUT_OF_ORDER', 'Out of Order'),
    ('READY_FOR_GUEST', 'Ready for Guest'),
]
```

### State Transitions

**State Validation:** `rooms/models.py` lines 103-115

```python
def can_transition_to(self, new_status):
    """Validate state machine transitions"""
    valid_transitions = {
        'OCCUPIED': ['CHECKOUT_DIRTY'],
        'CHECKOUT_DIRTY': ['CLEANING_IN_PROGRESS', 'CLEANED_UNINSPECTED', 'MAINTENANCE_REQUIRED', 'READY_FOR_GUEST'],
        'CLEANING_IN_PROGRESS': ['CLEANED_UNINSPECTED', 'CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED', 'READY_FOR_GUEST'],
        'CLEANED_UNINSPECTED': ['READY_FOR_GUEST', 'CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED', 'READY_FOR_GUEST'],
        'MAINTENANCE_REQUIRED': ['CHECKOUT_DIRTY', 'OUT_OF_ORDER', 'READY_FOR_GUEST'],
        'OUT_OF_ORDER': ['CHECKOUT_DIRTY', 'READY_FOR_GUEST'],
        'READY_FOR_GUEST': ['OCCUPIED', 'MAINTENANCE_REQUIRED', 'OUT_OF_ORDER'],
    }
    return new_status in valid_transitions.get(self.room_status, [])
```

### Business Rules

**Room Availability:** `rooms/models.py` lines 94-102

```python
def is_bookable(self):
    """Single source of truth for room availability"""
    if self.is_out_of_order:
        return False
        
    return (
        self.room_status == 'READY_FOR_GUEST' and
        self.is_active and
        not self.maintenance_required
    )
```

**State Tracking Fields:**
- `last_cleaned_at` / `cleaned_by_staff` - Cleaning history
- `last_inspected_at` / `inspected_by_staff` - Inspection history
- `turnover_notes` - Timestamped workflow notes
- `maintenance_required` / `maintenance_priority` - Maintenance status

**Evidence:** `rooms/models.py` lines 50-90

## 3. Staff Attendance State Machine

**Background Job:** Auto clock-out system via Heroku Scheduler
- Command: `python manage.py auto_clock_out_excessive`
- Frequency: Every 30 minutes
- Purpose: Automatic clock-out for excessive hours
- Evidence: `setup_heroku_scheduler.sh` lines 19-20

UNCLEAR IN CODE: Specific attendance state transitions need analysis of `attendance/models.py`

## 4. Payment Authorization Workflow

### Two-Phase Payment Process

**Phase 1: Authorization (Hold)**
- Stripe PaymentIntent created with `capture_method='manual'`
- Payment authorized but not captured
- Booking status: `PENDING_APPROVAL`
- Field: `payment_intent_id`, `payment_authorized_at`

**Phase 2: Capture (on Approval) or Void (on Decline)**
- Staff approves → Payment captured, status `CONFIRMED`
- Staff declines → Payment voided, status `DECLINED`
- Timeout → Payment voided, status `EXPIRED`

**Evidence:** Payment authorization fields in `RoomBooking` model (lines 741-756)

## 5. Overstay Detection System

UNCLEAR IN CODE: Overstay state machine implementation needs analysis of overstay-related models and management commands. References found in:
- `hotel/management/commands/flag_overstay_bookings.py`
- Various overstay audit documents in repository

## 6. Token-Based Access Control

### Guest Booking Tokens

**Purpose Types:**
```python
PURPOSE_CHOICES = [
    ('STATUS', 'Booking Status'),
    ('MANAGEMENT', 'Booking Management'), 
    ('PRECHECKIN', 'Precheckin Access'),
    ('ROOM_ACCESS', 'Room Access'),
    ('SURVEY', 'Post-Stay Survey'),
]
```

**Scoped Permissions:**
```python
DEFAULT_SCOPES = {
    'STATUS': ['read_booking', 'read_room_services'],
    'MANAGEMENT': ['read_booking', 'cancel_booking', 'modify_booking'],
    'PRECHECKIN': ['read_booking', 'write_precheckin'],
    'ROOM_ACCESS': ['read_booking', 'read_room_services', 'write_room_services'],
    'SURVEY': ['read_booking', 'write_survey'],
}
```

**Token Generation:** Secure token generation with expiration
- Evidence: `GuestBookingToken` model structure analysis needed

## 7. Survey Workflow

**Send Modes:**
```python
SEND_MODE_CHOICES = [
    ('AUTO_IMMEDIATE', 'Send immediately after checkout'),
    ('AUTO_DELAYED', 'Send after delay'),
    ('MANUAL_ONLY', 'Manual sending only')
]
```

**Configuration:** `HotelSurveyConfig` model
- `delay_hours` - Delay before sending survey
- `token_expiry_hours` - Survey token validity period
- Evidence: `hotel/models.py` lines 489-502

## 8. Cancellation Policy Engine

**Policy Types:**
```python
TEMPLATE_TYPE_CHOICES = [
    ('FLEXIBLE', 'Flexible (free until check-in)'),
    ('MODERATE', 'Moderate (free until X hours)'), 
    ('STRICT', 'Strict (non-refundable)'),
    ('SUPER_STRICT', 'Super Strict (partial refund only)'),
    ('CUSTOM', 'Custom Policy'),
]
```

**Penalty Processing:**
```python
PENALTY_TYPE_CHOICES = [
    ('NONE', 'No penalty'),
    ('FIXED_AMOUNT', 'Fixed amount'),
    ('PERCENTAGE', 'Percentage of booking'),
    ('FIRST_NIGHT', 'First night charge'),
    ('FULL_STAY', 'Full stay charge'),
]
```

UNCLEAR IN CODE: Detailed cancellation policy execution logic needs analysis of policy models and services.

## 9. Business Rule Invariants

### Booking Validation Rules

1. **Check-out must be after check-in**
2. **Primary guest information required** (`primary_first_name`, `primary_last_name`)
3. **Adults must be ≥ 1**
4. **Room must be bookable** (`room.is_bookable()`)
5. **Hotel timezone considerations** for date calculations

**Evidence:** `RoomBooking.clean()` method and validation logic

### Room Assignment Rules

1. **One booking per room at a time** (occupancy constraint)
2. **Room status must be READY_FOR_GUEST** for new bookings
3. **Active rooms only** (`is_active=True`)
4. **Not out of order** (`is_out_of_order=False`)

### Approval Timing Rules

1. **Approval deadline calculated** from hotel configuration
2. **Auto-expiry after SLA timeout**
3. **Approval cutoff time** prevents late-day bookings
4. **Grace periods** for checkout overstays

**Evidence:** Hotel access configuration timing fields

### Multi-tenancy Rules

1. **All operations scoped to hotel** via foreign keys
2. **Staff permissions limited to their hotel**
3. **Guest tokens contain hotel context**
4. **URL routing includes hotel slug** for isolation

This state machine documentation covers the core business logic workflows. Additional state machines may exist in other domains requiring further analysis.