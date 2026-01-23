# BACKEND OVERSTAY & TIME RULES AUDIT — Complete System Inventory

**Goal**: Definitive audit of all existing overstay/checkout/deadline/expiry logic in the current backend codebase to reconcile with the new OverstayIncident noon-based system without conflicts or duplication.

## 1️⃣ Inventory Existing "Overstay" Concepts

### 1.1 Database Fields (Canonical State)

#### RoomBooking Model (`hotel/models.py`)
| Field | Type | Purpose | Writes DB? | Source of Truth? |
|-------|------|---------|------------|------------------|
| `overstay_flagged_at` | DateTimeField | Timestamp when overstay detected | ✅ YES | ❌ Legacy - flagging only |
| `overstay_acknowledged_at` | DateTimeField | Staff acknowledgment timestamp | ✅ YES | ❌ UI workflow state |
| `approval_deadline_at` | DateTimeField | PENDING_APPROVAL SLA deadline | ✅ YES | ✅ Approval flow canonical |
| `expired_at` | DateTimeField | Auto-expired due to timeout | ✅ YES | ✅ Expiry canonical |
| `auto_expire_reason_code` | CharField | Reason for auto-expiry | ✅ YES | ❌ Metadata only |
| `expires_at` | DateTimeField | Unpaid booking expiry | ✅ YES | ✅ Payment timeout canonical |
| `checked_in_at` / `checked_out_at` | DateTimeField | Physical stay timestamps | ✅ YES | ✅ Stay state canonical |

**File**: [hotel/models.py](hotel/models.py#L875-L885)

#### OverstayIncident Model (`hotel/models.py`)
| Field | Type | Purpose | Writes DB? | Source of Truth? |
|-------|------|---------|------------|------------------|
| `expected_checkout_date` | DateField | Original checkout date | ✅ YES | ✅ Incident canonical |
| `detected_at` | DateTimeField | Noon detection timestamp | ✅ YES | ✅ Incident canonical |
| `status` | CharField | OPEN/ACKED/RESOLVED/DISMISSED | ✅ YES | ✅ Workflow canonical |
| `severity` | CharField | LOW/MEDIUM/HIGH | ✅ YES | ✅ Incident canonical |
| `acknowledged_at` | DateTimeField | Staff acknowledgment | ✅ YES | ✅ Workflow canonical |
| `resolved_at` | DateTimeField | Resolution timestamp | ✅ YES | ✅ Workflow canonical |

**File**: [hotel/models.py](hotel/models.py#L2907-L2975)

#### BookingExtension Model (`hotel/models.py`)
| Field | Type | Purpose | Writes DB? | Source of Truth? |
|-------|------|---------|------------|------------------|
| `old_checkout_date` | DateField | Pre-extension checkout | ✅ YES | ✅ Audit trail canonical |
| `new_checkout_date` | DateField | Post-extension checkout | ✅ YES | ✅ Audit trail canonical |
| `payment_intent_id` | CharField | Extension payment tracking | ✅ YES | ✅ Payment canonical |

**File**: [hotel/models.py](hotel/models.py#L2977-L3024)

### 1.2 Computed Logic Functions (Derived State)

#### Checkout Deadline Computation
**File**: [apps/booking/services/stay_time_rules.py](apps/booking/services/stay_time_rules.py#L13-L35)
```python
def compute_checkout_deadline(booking, check_out_date=None) -> timezone.datetime:
    """Hotel checkout time + grace minutes = deadline"""
    # Default: 11:00 AM + 30 min grace = 11:30 AM deadline
```
- **Trigger**: Hotel config + checkout date
- **Writes DB**: ❌ Pure computation
- **Used by**: Overstay detection, risk level calculation

#### Overstay Detection Logic
**File**: [apps/booking/services/stay_time_rules.py](apps/booking/services/stay_time_rules.py#L45-L66)
```python
def is_overstay(booking, now=None) -> bool:
    """Past checkout deadline + still checked in = overstay"""
    return now > compute_checkout_deadline(booking) and booking.checked_in_at and not booking.checked_out_at
```

#### Risk Level Classification
**File**: [apps/booking/services/stay_time_rules.py](apps/booking/services/stay_time_rules.py#L90-L130)
```python
def get_overstay_risk_level(booking, now=None) -> str:
    """Returns: 'OK', 'GRACE', 'OVERDUE', 'CRITICAL'"""
    # OVERDUE: Past deadline ≤ 120 minutes
    # CRITICAL: Past deadline > 120 minutes
```

#### Approval Deadline Computation
**File**: [apps/booking/services/booking_deadlines.py](apps/booking/services/booking_deadlines.py#L13-L30)
```python
def compute_approval_deadline(booking, base_dt=None) -> timezone.datetime:
    """paid_at + hotel SLA minutes (default: 30min)"""
```

#### Approval Risk Classification
**File**: [apps/booking/services/booking_deadlines.py](apps/booking/services/booking_deadlines.py#L88-L116)
```python
def get_approval_risk_level(booking) -> str:
    """Returns: 'OK', 'DUE_SOON', 'OVERDUE', 'CRITICAL'"""
    # DUE_SOON: ≤ 10 minutes until deadline
    # OVERDUE: Past deadline ≤ 60 minutes
    # CRITICAL: Past deadline > 60 minutes
```

### 1.3 New Noon-Based System Functions

#### Noon Rule Detection
**File**: [room_bookings/services/overstay.py](room_bookings/services/overstay.py#L58-L105)
```python
def detect_overstays(hotel: Hotel, now_utc: datetime) -> int:
    """Detect and create OverstayIncident at noon hotel time"""
    # Creates OverstayIncident records
    # Replaces simple overstay_flagged_at logic
```

#### Extension with Resolution
**File**: [room_bookings/services/overstay.py](room_bookings/services/overstay.py#L194-L283)
```python
def extend_overstay(hotel, booking, staff_user, new_checkout_date=None, add_nights=None):
    """Extend booking and smart-resolve overstay incident"""
    # Updates booking.check_out
    # Creates BookingExtension record
    # Resolves OverstayIncident if applicable
```

## 2️⃣ Scheduler & Background Jobs Audit

### 2.1 Approval Expiry Scheduler
**File**: [hotel/management/commands/auto_expire_overdue_bookings.py](hotel/management/commands/auto_expire_overdue_bookings.py)

**Trigger Condition**: 
```python
status='PENDING_APPROVAL' AND approval_deadline_at < now() AND expired_at IS NULL
```

**Actions Taken**:
1. Sets `status = 'EXPIRED'`
2. Sets `expired_at = now()`
3. Sets `auto_expire_reason_code = 'APPROVAL_TIMEOUT'`
4. Processes Stripe refund if paid
5. Sets `refunded_at` and `refund_reference`
6. Emits `realtime_booking_updated` event
7. TODO: Send guest email notification

**Scheduler Frequency**: Every 5-15 minutes (recommended)

### 2.2 Legacy Overstay Flagging Scheduler
**File**: [hotel/management/commands/flag_overstay_bookings.py](hotel/management/commands/flag_overstay_bookings.py)

**Trigger Condition**:
```python
checked_in_at IS NOT NULL AND 
checked_out_at IS NULL AND 
check_out <= now.date() AND 
overstay_flagged_at IS NULL AND
should_flag_overstay(booking)  # Uses old deadline logic
```

**Actions Taken**:
1. Sets `overstay_flagged_at = now()`
2. Calls `notification_manager.realtime_booking_updated(booking)`
3. Sends targeted overstay alert to reception/manager staff
4. No status change - remains `CHECKED_IN`

**Scheduler Frequency**: Every 15-30 minutes (recommended)

**⚠️ CONFLICT RISK**: This uses the OLD deadline logic, not the new noon rule!

### 2.3 Other Scheduled Tasks
**File**: [hotel/management/commands/send_scheduled_surveys.py](hotel/management/commands/send_scheduled_surveys.py)
- **Purpose**: Guest survey emails
- **Relevance**: None - unrelated to overstay

**File**: [hotel/management/commands/cleanup_survey_tokens.py](hotel/management/commands/cleanup_survey_tokens.py)
- **Purpose**: Token cleanup
- **Relevance**: None - unrelated to overstay

## 3️⃣ Canonical vs Derived State Classification

| Concept | Source | Writes DB? | Used by UI? | Safe to Remove? |
|---------|--------|------------|-------------|-----------------|
| **CANONICAL (Keep as Source of Truth)** |
| `OverstayIncident.detected_at` | Noon rule | ✅ YES | ✅ YES | ❌ NEW CANONICAL |
| `OverstayIncident.status` | Workflow | ✅ YES | ✅ YES | ❌ NEW CANONICAL |
| `approval_deadline_at` | SLA rules | ✅ YES | ✅ YES | ❌ KEEP - different domain |
| `expired_at` | Auto-expiry | ✅ YES | ✅ YES | ❌ KEEP - different domain |
| `checked_in_at`/`checked_out_at` | Physical state | ✅ YES | ✅ YES | ❌ KEEP - fundamental |
| **TRANSITIONAL (Deprecate After Migration)** |
| `overstay_flagged_at` | Legacy flagging | ✅ YES | ✅ YES | ✅ REPLACE with OverstayIncident |
| `overstay_acknowledged_at` | Legacy workflow | ✅ YES | ❌ NO | ✅ REPLACE with OverstayIncident.acknowledged_at |
| **DERIVED/COMPUTED (UI-Only)** |
| `is_overstay()` | Computation | ❌ NO | ✅ YES | ❌ KEEP for backward compat |
| `get_overstay_risk_level()` | Computation | ❌ NO | ✅ YES | ❌ KEEP for UI warnings |
| `compute_checkout_deadline()` | Computation | ❌ NO | ✅ YES | ❌ KEEP for UI display |
| **AUDIT TRAIL (Keep Forever)** |
| `BookingExtension` records | Extension history | ✅ YES | ✅ YES | ❌ KEEP - immutable audit |

## 4️⃣ Realtime Events Audit

### 4.1 Booking Update Events
**Location**: [hotel/management/commands/flag_overstay_bookings.py](hotel/management/commands/flag_overstay_bookings.py#L109)
```python
notification_manager.realtime_booking_updated(booking)
```
**Payload**: Standard booking serialization
**Frontend Listens**: ✅ YES - Updates booking cards in real-time

**Location**: [hotel/management/commands/auto_expire_overdue_bookings.py](hotel/management/commands/auto_expire_overdue_bookings.py#L142)
```python
notification_manager.realtime_booking_updated(booking)
```

### 4.2 New Overstay-Specific Events
**Location**: [room_bookings/services/overstay.py](room_bookings/services/overstay.py#L482-L575)

**Events Defined**:
1. `_emit_overstay_flagged()` - When incident created
2. `_emit_overstay_acknowledged()` - When staff acknowledges  
3. `_emit_overstay_extended()` - When extension processed
4. `_emit_booking_updated()` - Standard booking change

**Frontend Status**: ❓ Implementation exists but frontend integration unknown

### 4.3 Staff Alert Events
**Location**: [hotel/management/commands/flag_overstay_bookings.py](hotel/management/commands/flag_overstay_bookings.py#L111-L130)
```python
alert_data = {
    'type': 'overstay_alert',
    'booking_id': booking.booking_id,
    'room_number': booking.assigned_room.room_number,
    'guest_name': f"{booking.primary_first_name} {booking.primary_last_name}",
    'checkout_deadline': checkout_deadline.isoformat(),
    'overstay_minutes': overstay_minutes
}
notification_manager.send_staff_notification(
    hotel=booking.hotel,
    roles=['reception', 'manager'],
    message=f"🚨 Guest overstaying in Room {booking.assigned_room.room_number}",
    data=alert_data
)
```

## 5️⃣ Conflict Risk Analysis

### 5.1 HIGH RISK CONFLICTS

#### ❌ Dual Overstay Detection Systems
**Problem**: Two systems detecting and flagging overstays:
1. **Legacy**: `flag_overstay_bookings.py` → sets `overstay_flagged_at`
2. **New**: `detect_overstays()` → creates `OverstayIncident`

**Exact Code Paths**:
- Legacy: [hotel/management/commands/flag_overstay_bookings.py](hotel/management/commands/flag_overstay_bookings.py#L87-L102)
- New: [room_bookings/services/overstay.py](room_bookings/services/overstay.py#L87-L105)

**Risk**: Duplicate alerts, inconsistent state, confused staff workflow

#### ❌ Different Time Rules
**Problem**: Different deadline calculations:
1. **Legacy**: Hotel checkout time + grace minutes
2. **New**: Noon hotel time (no grace period)

**Exact Code Paths**:
- Legacy: [apps/booking/services/stay_time_rules.py](apps/booking/services/stay_time_rules.py#L13-L35)
- New: [room_bookings/services/overstay.py](room_bookings/services/overstay.py#L80-L85)

**Risk**: Different bookings flagged at different times, inconsistent UX

#### ❌ Duplicate Realtime Events
**Problem**: Multiple event emissions for same overstay:
1. Legacy flagging emits `booking_updated`
2. New system emits `overstay_flagged` + `booking_updated`

**Risk**: Frontend receiving duplicate/conflicting events

### 5.2 MEDIUM RISK CONFLICTS

#### ⚠️ Overstay Resolution Logic
**Current**: `overstay_flagged_at` cleared manually or by extension
**New**: `OverstayIncident.status` managed by smart resolution

**Risk**: Partial migrations leave inconsistent state

#### ⚠️ UI State Dependencies  
**Risk**: Frontend code expecting `overstay_flagged_at` field but receiving `OverstayIncident` data

### 5.3 LOW RISK (Safe Coexistence)

#### ✅ Approval Expiry System
**Domain**: PENDING_APPROVAL bookings only
**New System**: IN_HOUSE (CHECKED_IN) bookings only
**Analysis**: Completely different booking states - no overlap

#### ✅ Extension Audit Trail
**Current**: Manual extension process
**New**: `BookingExtension` records with payment tracking
**Analysis**: Additive - enhances existing functionality

## 6️⃣ Final Recommendation

### Single Canonical Overstay Source of Truth
**RECOMMENDATION**: `OverstayIncident` model with noon-based detection

**Rationale**:
- Clear workflow states (OPEN/ACKED/RESOLVED)
- Proper audit trail with timestamps
- Consistent noon rule across all hotels
- Supports extension with smart resolution
- Eliminates ambiguity of simple flagged_at timestamp

### Schedulers to Keep
✅ **Keep**: `auto_expire_overdue_bookings.py`
- **Domain**: PENDING_APPROVAL bookings
- **No conflict** with IN_HOUSE overstay system

### Schedulers to Refactor
🔄 **Refactor**: `flag_overstay_bookings.py`
- **Change**: Use `detect_overstays()` instead of direct flagging
- **Migration path**:
  ```python
  # OLD CODE
  booking.overstay_flagged_at = now
  booking.save(update_fields=['overstay_flagged_at'])
  
  # NEW CODE  
  detect_overstays(booking.hotel, now)
  ```

### Fields to Stop Writing
❌ **Stop Writing**: 
- `overstay_flagged_at` - Replace with OverstayIncident creation
- `overstay_acknowledged_at` - Replace with OverstayIncident.acknowledged_at

### Fields to Keep as Computed-Only
✅ **Computed-Only** (UI warnings, no DB writes):
- `is_overstay(booking)` - Backward compatibility
- `get_overstay_risk_level(booking)` - UI risk indicators  
- `compute_checkout_deadline(booking)` - UI display

### Fields to Keep as Canonical
✅ **Keep Writing**:
- All approval-related fields (`approval_deadline_at`, `expired_at`)
- All payment-related fields (`paid_at`, `refunded_at`)
- All physical state fields (`checked_in_at`, `checked_out_at`)
- `OverstayIncident` model - NEW canonical source

### Migration Strategy
1. **Phase 1**: Deploy OverstayIncident system alongside legacy
2. **Phase 2**: Update `flag_overstay_bookings.py` to use `detect_overstays()`
3. **Phase 3**: Stop writing to legacy fields (`overstay_flagged_at`)
4. **Phase 4**: Frontend migration to use OverstayIncident API
5. **Phase 5**: Remove legacy fields (breaking change)

### Exact Schedulers Configuration
```bash
# Heroku Scheduler Jobs
Every 15 minutes: python manage.py auto_expire_overdue_bookings
Every 30 minutes: python manage.py flag_overstay_bookings  # Until Phase 2
Every 30 minutes: python manage.py detect_overstays_all_hotels  # After Phase 2
```

**CRITICAL**: Ensure only ONE overstay detection system runs at a time during migration.