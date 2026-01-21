# HotelMate Backend: OVERDUE and CRITICAL Booking Behavior Analysis

**Analysis Date**: January 21, 2026  
**Status**: Current Backend Behavior Documentation  
**Purpose**: Document existing behavior and identify decision points for OVERDUE/CRITICAL bookings

---

## 1. Approval Overdue Analysis (PENDING_APPROVAL Status)

### Current Timeline of States

**Initial State**: PAID → PENDING_APPROVAL  
- `approval_deadline_at` is computed from `paid_at` + hotel SLA minutes (default: 30 min)
- Risk level calculated by [`get_approval_risk_level()`](apps/booking/services/booking_deadlines.py#L88)

**Risk Level Progression**:
1. **OK**: More than 10 minutes until deadline
2. **DUE_SOON**: ≤ 10 minutes until deadline  
3. **OVERDUE**: Past deadline, ≤ 60 minutes overdue
4. **CRITICAL**: Past deadline, > 60 minutes overdue
5. **EXPIRED**: [`auto_expire_overdue_bookings`](hotel/management/commands/auto_expire_overdue_bookings.py) job runs

### What Currently Happens

#### Before Job Runs (Booking Still PENDING_APPROVAL)
- **Status remains**: `PENDING_APPROVAL` 
- **Staff can still approve**: YES - [`StaffBookingAcceptView`](hotel/staff_views.py#L3241) has NO expiry checks
- **UI shows warning**: YES - serializers expose `approval_risk_level: 'CRITICAL'`
- **No automatic action**: Backend takes no action until job runs

#### When Auto-Expire Job Runs
- **Trigger condition**: `approval_deadline_at < now()` AND `expired_at IS NULL`
- **Actions taken**:
  1. Status changed to `EXPIRED`
  2. `expired_at` timestamp set
  3. `auto_expire_reason_code = 'APPROVAL_TIMEOUT'`
  4. Stripe refund attempted (if applicable)
  5. Realtime notification sent to staff
  6. Guest email notification (TODO - not implemented)

#### After Expiry
- **Status**: `EXPIRED`
- **Staff can still approve**: YES - no guards prevent this in [`StaffBookingAcceptView`](hotel/staff_views.py#L3290-3387)
- **Risk of double-capture**: HIGH - expired booking with valid payment_intent_id could still be captured

### Decision Point Gaps
- **EXPIRED bookings can be approved by mistake** - no backend validation
- **No hard cutoff** - only soft UI warnings until job runs
- **Race condition window** - booking can be approved while job is expiring it

---

## 2. Overstay Analysis (IN_HOUSE Past Checkout)

### Current Timeline of States

**Initial State**: CONFIRMED → IN_HOUSE (checked in)  
- `checkout_deadline_at` computed from checkout date + hotel checkout time + grace minutes
- Risk level calculated by [`get_overstay_risk_level()`](apps/booking/services/stay_time_rules.py#L77)

**Risk Level Progression**:
1. **OK**: Before standard checkout time
2. **GRACE**: After standard checkout, within grace period
3. **OVERDUE**: Past grace deadline, ≤ 120 minutes over  
4. **CRITICAL**: Past grace deadline, > 120 minutes over

### What Currently Happens

#### Overstay Detection Process
- **Job**: [`flag_overstay_bookings`](hotel/management/commands/flag_overstay_bookings.py) runs periodically
- **Trigger condition**: `checked_in_at IS NOT NULL` AND `checked_out_at IS NULL` AND past checkout deadline
- **Actions taken**:
  1. `overstay_flagged_at` timestamp set
  2. Realtime booking update sent
  3. Specific overstay alert sent to hotel staff (reception/manager roles)
  4. No status change - remains `IN_HOUSE`

#### No Automatic Actions
- **Booking remains IN_HOUSE indefinitely** 
- **No forced checkout** - purely alerting mechanism
- **No backend restrictions** - guest can continue to use room/access
- **Manual resolution required** - staff must take action

### Decision Point Gaps
- **CRITICAL overstay has no enforcement** - only alerting
- **No auto-escalation** - stays CRITICAL forever until manual action
- **No backend controls** - booking functionality unaffected by overstay state

---

## 3. Realtime & Staff Visibility Analysis

### Events That Emit Realtime Updates
- **Booking expiry**: [`auto_expire_overdue_bookings`](hotel/management/commands/auto_expire_overdue_bookings.py#L132) calls `realtime_booking_updated()`
- **Overstay flagging**: [`flag_overstay_bookings`](hotel/management/commands/flag_overstay_bookings.py#L87) calls:
  - `realtime_booking_updated()` - general booking update
  - `send_staff_notification()` - targeted overstay alert

### Events That Are Silent
- **Risk level transitions** (OK → DUE_SOON → OVERDUE → CRITICAL) - no realtime events
- **Approval deadline passing** - silent until job runs
- **Checkout deadline passing** - silent until job runs

### Staff Visibility Issues
- **CRITICAL states only visible on page refresh** until flagging/expiry jobs run
- **Job frequency determines alert speed** - not instant transitions
- **Risk level changes are passive** - computed in serializers, not actively pushed

---

## 4. Undecided Product Rules & Decision Points

### Approval Flow Decisions

#### Decision A: Should CRITICAL approval still be approvable?
**Current Behavior**: YES - no backend restrictions on CRITICAL approval  
**Risk**: Staff might approve bookings that should have been expired  
**Options**:
1. **Soft Warning**: Keep current behavior, rely on UI warnings
2. **Hard Cutoff**: Block approval after X minutes overdue (backend validation)

#### Decision B: Should EXPIRED bookings be hard-locked?
**Current Behavior**: NO - expired bookings can still be approved by mistake  
**Risk**: Double-capture of payment, guest confusion  
**Options**:
1. **Backend Block**: Add status validation to approve endpoint
2. **Staff Override**: Allow with explicit "override expired" flag

#### Decision C: Should approval jobs run more frequently?
**Current Behavior**: Job frequency determines expiry speed  
**Risk**: Long delays between CRITICAL → EXPIRED transitions  
**Options**:
1. **Real-time Expiry**: Expire bookings immediately when deadline passes
2. **Frequent Jobs**: Run every 1-2 minutes instead of 5-15 minutes

### Overstay Flow Decisions  

#### Decision D: Should CRITICAL overstay trigger automatic actions?
**Current Behavior**: NO - purely alerting, no enforcement  
**Risk**: Indefinite overstays with no consequences  
**Options**:
1. **Soft Escalation**: Escalate alerts to management/security
2. **Access Control**: Disable room access after X hours overstay  
3. **Forced Checkout**: Auto-checkout with extension billing

#### Decision E: Should overstay states affect booking functionality?
**Current Behavior**: NO - overstay doesn't restrict any backend operations  
**Risk**: Guest continues using services while in violation  
**Options**:
1. **Service Restrictions**: Block certain features for overstay bookings
2. **Billing Integration**: Auto-charge extension fees for overstays

### Real-time Visibility Decisions

#### Decision F: Should risk transitions be instantly visible?
**Current Behavior**: NO - computed fields only update on API calls  
**Risk**: Staff unaware of time-sensitive situations  
**Options**:
1. **Live Risk Updates**: Push risk level changes to frontend
2. **Deadline Alerts**: Push notifications when deadlines pass

#### Decision G: Should CRITICAL states auto-sort to top?
**Current Behavior**: NO - sorting handled by frontend  
**Risk**: Critical situations buried in long lists  
**Options**:
1. **Backend Sorting**: Include risk-based sorting in API responses
2. **Frontend Priority**: Keep current behavior, sort in UI

---

## 5. Summary of Current Behavior Risks

### High-Risk Issues
1. **Expired bookings can be approved** - no backend validation prevents this
2. **CRITICAL overstays have no consequences** - indefinite room occupation possible  
3. **Silent risk transitions** - staff may miss critical deadlines
4. **Race conditions during expiry** - booking can be approved while being expired

### Medium-Risk Issues
1. **Job-dependent alerting** - delays based on cron frequency
2. **No escalation paths** - CRITICAL states remain CRITICAL forever
3. **Manual-only resolution** - no automated enforcement mechanisms

### Low-Risk Issues  
1. **UI-only warnings** - backend agnostic to risk levels
2. **No centralized monitoring** - difficult to audit overdue patterns
3. **Guest notification gaps** - expired bookings lack guest communication

---

## 6. Current Implementation Files Reference

### Core Service Files
- [`apps/booking/services/booking_deadlines.py`](apps/booking/services/booking_deadlines.py) - Approval deadline logic
- [`apps/booking/services/stay_time_rules.py`](apps/booking/services/stay_time_rules.py) - Overstay detection logic

### Management Commands  
- [`hotel/management/commands/auto_expire_overdue_bookings.py`](hotel/management/commands/auto_expire_overdue_bookings.py) - Expires overdue approvals
- [`hotel/management/commands/flag_overstay_bookings.py`](hotel/management/commands/flag_overstay_bookings.py) - Flags overstay situations

### Staff Endpoints
- [`hotel/staff_views.py#L3241`](hotel/staff_views.py#L3241) - `StaffBookingAcceptView` (approve endpoint)  
- [`hotel/staff_views.py#L3388`](hotel/staff_views.py#L3388) - `StaffBookingDeclineView` (decline endpoint)

### Serializers  
- [`hotel/canonical_serializers.py#L170`](hotel/canonical_serializers.py#L170) - `StaffRoomBookingListSerializer`
- [`hotel/canonical_serializers.py#L373`](hotel/canonical_serializers.py#L373) - `StaffRoomBookingDetailSerializer`

### Model Fields
- [`hotel/models.py#L746-756`](hotel/models.py#L746-756) - Approval deadline and expiry fields
- [`hotel/models.py#L867-872`](hotel/models.py#L867-872) - Overstay tracking fields

**Next Steps**: Product team must decide on enforcement policies before implementation of safeguards.