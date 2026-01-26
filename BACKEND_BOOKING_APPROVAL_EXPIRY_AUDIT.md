# Backend Booking Approval + Expiry Semantics Audit

**Focus**: Same-day bookings and approval/expiry/no-show separation  
**Date**: January 26, 2026  
**Status**: Complete system audit with recommendations

## 1️⃣ Current Approval Logic

### Booking Statuses Requiring Staff Approval

**Target Status**: `PENDING_APPROVAL`

**Trigger Conditions**:
- Payment has been authorized (`paid_at` is set)
- Booking transitions from `PENDING_PAYMENT` → `PENDING_APPROVAL`
- Staff must explicitly approve to reach `CONFIRMED` status

**Code Location**: [hotel/models.py#L617-627](hotel/models.py#L617-627)
```python
STATUS_CHOICES = [
    ('PENDING_PAYMENT', 'Pending Payment'),
    ('PENDING_APPROVAL', 'Pending Staff Approval'),  # <-- Requires approval
    ('CONFIRMED', 'Confirmed'),                      # <-- After approval
    ('IN_HOUSE', 'In House'), 
    ('DECLINED', 'Declined'),                        # <-- Rejected approval
    ('CANCELLED', 'Cancelled'),
    ('CANCELLED_DRAFT', 'Cancelled Draft'),
    ('EXPIRED', 'Expired'),                          # <-- Auto-expired
    ('COMPLETED', 'Completed'),
    ('NO_SHOW', 'No Show'),
]
```

### Approval Timing Control Fields

**Primary Fields** (in `RoomBooking`):
1. **`paid_at`** - Payment authorization timestamp (baseline)
2. **`approval_deadline_at`** - Staff SLA deadline (computed)
3. **`expired_at`** - When booking was auto-expired
4. **`auto_expire_reason_code`** - Reason for expiry (e.g., 'APPROVAL_TIMEOUT')
5. **`decision_at`** - When staff made decision
6. **`decision_by`** - Staff member who approved/declined

**Configuration Fields** (in `HotelAccessConfig`):
- **`approval_sla_minutes`** - Hotel's approval SLA (default: 30 minutes)

**Code Location**: [hotel/models.py#L756-778](hotel/models.py#L756-778)

### Approval Expiry Implementation

**Implementation Location**: [hotel/management/commands/auto_expire_overdue_bookings.py](hotel/management/commands/auto_expire_overdue_bookings.py)

**Exact Trigger Condition**:
```python
overdue_qs = RoomBooking.objects.filter(
    status='PENDING_APPROVAL',
    approval_deadline_at__isnull=False,
    approval_deadline_at__lt=now(),
    expired_at__isnull=True  # Not already expired
)
```

**Actions Taken When Expired**:
1. Set `status = 'EXPIRED'`
2. Set `expired_at = now()`
3. Set `auto_expire_reason_code = 'APPROVAL_TIMEOUT'`
4. Process Stripe refund (if paid)
5. Set `refunded_at` and `refund_reference`
6. Emit realtime notification to staff
7. TODO: Guest email notification (not implemented)

**Scheduler**: Runs every 5-15 minutes (recommended)

### Exact Expiry Condition

**EXPIRED Status Triggered When**:
```
(status = 'PENDING_APPROVAL') AND 
(approval_deadline_at < current_time) AND 
(expired_at IS NULL) AND
(auto_expire_job runs)
```

**Deadline Calculation**: [apps/booking/services/booking_deadlines.py#L12-30](apps/booking/services/booking_deadlines.py#L12-30)
```python
base_dt = booking.paid_at if booking.paid_at else booking.created_at
deadline = base_dt + timedelta(minutes=hotel.access_config.approval_sla_minutes)
```

## 2️⃣ Same-Day Booking Handling

### Same-Day Approval Window

**Current Logic**: 
- Approval deadline is based on `paid_at` + SLA minutes
- **NO special logic for same-day bookings**
- **NO arrival cutoff consideration in approval logic**

### Key Question: At 14:45 on check-in day, can staff approve a PENDING_APPROVAL booking?

**Answer**: **YES** - if the approval deadline hasn't passed

**Example Timeline** (same-day booking at 14:00):
- 14:00 - Guest pays, booking becomes `PENDING_APPROVAL`
- 14:00 - `approval_deadline_at` = 14:30 (30min SLA)
- 14:30 - Risk level becomes `OVERDUE`
- 15:30 - Risk level becomes `CRITICAL` 
- Eventually - Auto-expire job sets status to `EXPIRED`

**No Check-in Time Awareness**: 
- Approval logic ignores hotel check-in times (15:00)
- No integration with arrival window validation
- Same-day bookings follow identical rules as future bookings

**Code Evidence**: [apps/booking/services/booking_deadlines.py](apps/booking/services/booking_deadlines.py) has no date-aware logic

### Current Risk Level Classification

**Risk Levels** ([apps/booking/services/booking_deadlines.py#L88-113](apps/booking/services/booking_deadlines.py#L88-113)):
- **`OK`**: More than 10 minutes until deadline
- **`DUE_SOON`**: ≤ 10 minutes until deadline  
- **`OVERDUE`**: Past deadline, ≤ 60 minutes overdue
- **`CRITICAL`**: Past deadline, > 60 minutes overdue
- **`EXPIRED`**: Auto-expire job has run

## 3️⃣ Meaning of EXPIRED

### Backend Definition of EXPIRED

**EXPIRED Status Means**:
1. **Approval timeout** - Staff failed to approve within SLA
2. **Auto-refunded** - Stripe payment refunded automatically  
3. **Irreversible** - Cannot be approved (hard-blocked by backend)
4. **Reason logged** - `auto_expire_reason_code = 'APPROVAL_TIMEOUT'`

**Code Evidence**: [hotel/staff_views.py#L3282-3291](hotel/staff_views.py#L3282-3291)
```python
# HARD BLOCK: Cannot approve expired bookings
if booking.status == 'EXPIRED' or booking.expired_at is not None:
    return Response({
        'error': 'Booking expired due to approval timeout and cannot be approved.',
        'expired_at': booking.expired_at.isoformat(),
        'auto_expire_reason_code': booking.auto_expire_reason_code
    }, status=status.HTTP_409_CONFLICT)
```

### Current Distinction Between Expiry Types

**Currently NO separation between**:
- Approval expiry (staff timeout)
- Payment expiry (unpaid bookings) 
- No-show situations

**All use same EXPIRED status** with different reason codes:
- `'APPROVAL_TIMEOUT'` - Staff didn't approve in time
- Potentially others for payment expiry (not audited)

## 4️⃣ No-Show vs Approval Expiry

### Current NO_SHOW Status

**Status Exists**: `NO_SHOW` is in `STATUS_CHOICES`

**Current Usage**: 
- Status exists in schema
- Used in test data generation
- **NO automatic detection logic found**
- **NO automatic transition from CONFIRMED → NO_SHOW**

**Manual Only**: Staff must manually set booking to `NO_SHOW`

### Arrival Window Logic (Separate System)

**Check-in Validation** exists but is **NOT integrated** with booking status:

**Arrival Cutoff Rules** ([hotelmate/utils/checkin_validation.py](hotelmate/utils/checkin_validation.py)):
- Same day: 12:00 - 02:00 next day
- Late arrival cutoff: 02:00 next day
- Beyond cutoff: Check-in blocked

**Key Gap**: Arrival window validation doesn't trigger status changes

### Missing No-Show Detection

**What Should Happen** (not implemented):
- CONFIRMED bookings that pass late arrival cutoff (02:00) → NO_SHOW
- Automatic status transition based on hotel timezone
- No-show detection job (doesn't exist)

## 5️⃣ Recommended Canonical Rules

### Approval Deadline Rules

**Current State**: ✅ Working as designed
- Approval overdue warning: `DUE_SOON` at -10min, `OVERDUE` at deadline
- Approval hard cutoff: Auto-expire job based on hotel SLA
- Same-day approval window: No special handling (follows SLA)

### Recommended Enhancements

#### A) Same-Day Booking Approval Rules
```
CURRENT: approval_deadline = paid_at + 30min (always)

RECOMMENDED: 
- Same-day bookings: MIN(paid_at + 30min, check_in_date 22:00 local)
- Future bookings: paid_at + 30min (unchanged)
```

**Rationale**: Approval should complete before evening of arrival day

#### B) Status Transition Separation

**Current Single EXPIRED** → **Recommended Multiple Statuses**:

```python
# Current
('EXPIRED', 'Expired')  # Used for everything

# Recommended  
('APPROVAL_EXPIRED', 'Approval Expired')  # Staff timeout
('PAYMENT_EXPIRED', 'Payment Expired')    # Unpaid timeout  
('NO_SHOW', 'No Show')                   # Arrival timeout
```

#### C) No-Show Detection Rules

**Recommended Implementation**:
```python
# New job: auto_flag_no_shows.py
# Trigger: CONFIRMED bookings past late arrival cutoff

transition_condition = (
    status='CONFIRMED' AND
    check_in_date < today AND
    last_arrival_time < (check_in_date + 1 day, 02:00 hotel_time) AND
    current_time > (check_in_date + 1 day, 02:00 hotel_time)
)
```

### Proposed Status Flow

```
PENDING_PAYMENT 
    ↓ (payment authorized)
PENDING_APPROVAL
    ↓ (staff approves before deadline)
CONFIRMED
    ↓ (guest checks in)
IN_HOUSE 
    ↓ (guest checks out)
COMPLETED

# Expiry/Failure Paths
PENDING_APPROVAL → APPROVAL_EXPIRED (approval timeout)
CONFIRMED → NO_SHOW (arrival timeout)
```

## 6️⃣ Code Locations Summary

### Current Implementation Files

**Approval Logic**:
- [hotel/models.py#L756-778](hotel/models.py#L756-778) - Deadline/expiry fields
- [apps/booking/services/booking_deadlines.py](apps/booking/services/booking_deadlines.py) - Deadline computation
- [hotel/management/commands/auto_expire_overdue_bookings.py](hotel/management/commands/auto_expire_overdue_bookings.py) - Auto-expiry job
- [hotel/staff_views.py#L3282-3291](hotel/staff_views.py#L3282-3291) - Approval endpoint with expiry blocking

**Configuration**:
- [hotel/models.py#L371-375](hotel/models.py#L371-375) - `HotelAccessConfig.approval_sla_minutes`

**Arrival Validation (Not Integrated)**:
- [hotelmate/utils/checkin_validation.py](hotelmate/utils/checkin_validation.py) - Arrival window validation
- [hotelmate/utils/checkin_policy.py](hotelmate/utils/checkin_policy.py) - Default arrival cutoff (02:00)

**Tests**:
- [booking_approval_expiry_tests.py](booking_approval_expiry_tests.py) - Comprehensive approval/expiry testing

### Recommended New Files

**No-Show Detection** (missing):
- `hotel/management/commands/auto_flag_no_shows.py` - No-show detection job
- Integration with existing arrival window validation

## 7️⃣ Summary & Next Steps

### Current Backend State ✅

**Working Correctly**:
1. ✅ Approval expiry with SLA enforcement
2. ✅ Hard-blocked EXPIRED booking approval 
3. ✅ Real-time risk level warnings (DUE_SOON/OVERDUE/CRITICAL)
4. ✅ Auto-refund on approval timeout
5. ✅ Race condition protection in approval/expiry

### Same-Day Booking Behavior ⚠️

**Current**: Same-day bookings follow identical approval rules (30min SLA from payment)

**Recommendation**: Consider evening cutoff for same-day bookings to ensure approval completes before guest arrival window

### Key Gaps 🔍

1. **No automatic no-show detection** - CONFIRMED bookings don't auto-transition to NO_SHOW
2. **Single EXPIRED status** - No distinction between approval timeout vs no-show
3. **Arrival window not integrated** - Check-in validation doesn't affect booking status

### Recommendation Priority

**High Priority**: 
- Implement automatic no-show detection for CONFIRMED bookings past arrival cutoff

**Medium Priority**: 
- Consider same-day approval deadline modifications
- Separate EXPIRED into APPROVAL_EXPIRED vs NO_SHOW statuses

**Low Priority**:
- Enhanced expiry reason codes for different timeout scenarios

---

**Backend Opinion**: Current approval expiry system is robust and working correctly. Main enhancement should be automated no-show detection to complete the booking lifecycle automation.