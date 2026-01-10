# Booking Validity, Checkout, and Guest Access Control - Current Backend Inventory

**Analysis Date**: January 10, 2026  
**Purpose**: Factual inventory of existing backend systems related to booking lifecycle, checkout, and guest access control.

---

## 1. BOOKING / STAY LIFECYCLE

### 📊 **Fields on RoomBooking Model** 
**Location**: `hotel/models.py` - `RoomBooking` class

**Lifecycle Tracking Fields**:
- `check_in` - DateField (required) - planned arrival date
- `check_out` - DateField (required) - planned departure date  
- `checked_in_at` - DateTimeField (null=True) - actual check-in timestamp
- `checked_out_at` - DateTimeField (null=True) - actual checkout timestamp
- `status` - CharField with STATUS_CHOICES
- `expires_at` - DateTimeField (null=True) - for unpaid booking cleanup

**Payment Tracking Fields**:
- `paid_at` - DateTimeField (null=True) - successful payment timestamp
- `payment_authorized_at` - DateTimeField (null=True) - authorization timestamp
- `payment_intent_id` - CharField - Stripe PaymentIntent ID

**Assignment Fields**:
- `assigned_room` - ForeignKey to Room (null=True)
- `room_assigned_at` - DateTimeField (null=True)
- `room_assigned_by` - ForeignKey to Staff (null=True)

### 📈 **Booking Status Choices**
**Location**: `hotel/models.py` - `RoomBooking.STATUS_CHOICES`

```python
STATUS_CHOICES = [
    ('PENDING_PAYMENT', 'Pending Payment'),
    ('PENDING_APPROVAL', 'Pending Staff Approval'),
    ('CONFIRMED', 'Confirmed'), 
    ('DECLINED', 'Declined'),
    ('CANCELLED', 'Cancelled'),
    ('CANCELLED_DRAFT', 'Cancelled Draft'),
    ('COMPLETED', 'Completed'),
    ('NO_SHOW', 'No Show'),
]
```

**Status Meanings**:
- `PENDING_PAYMENT` - Booking created, payment required
- `PENDING_APPROVAL` - Payment authorized, awaiting staff approval  
- `CONFIRMED` - Staff approved booking, ready for check-in
- `DECLINED` - Staff rejected booking, authorization cancelled
- `CANCELLED` - Booking cancelled by guest/staff
- `CANCELLED_DRAFT` - Expired unpaid booking (automated cleanup)
- `COMPLETED` - Guest has checked out
- `NO_SHOW` - Guest failed to arrive

### ✅ **Checked Out vs Expired Concept**
**EXISTS**: Clear distinction between checkout and expiration

- **Checked Out**: `checked_out_at != null` AND `status = 'COMPLETED'`
- **Expired by Date**: No built-in concept - would need to be determined by business logic
- **Payment Expiration**: `expires_at` field for unpaid bookings only

---

## 2. TIME HANDLING

### 🕐 **Checkout Date Treatment**  
**Current Implementation**: **EXCLUSIVE** checkout date

**Evidence**:
- Date range logic: `check_in <= day < check_out` (overnight hotel logic)
- Check-in eligibility: `check_in <= today < check_out`
- Availability overlap: `check_in__lte=day, check_out__gt=day`

### 🕒 **Checkout Cutoff Time**
**Location**: `hotelmate/utils/checkin_policy.py`

**Default Hotel Policy**:
```python
DEFAULT_CHECKIN_POLICY = {
    'timezone': 'Europe/Dublin',
    'check_in_time': '15:00',
    'early_checkin_from': '08:00', 
    'late_arrival_cutoff': '02:00'
}
```

**Checkout Time**: **NOT CURRENTLY DEFINED** - only check-in times are configured
**Available**: `get_checkin_policy(hotel)` function returns hotel-specific or default policy

### 🌍 **Timezone Handling**
**Default Timezone**: `Europe/Dublin`  
**Hotel-Specific**: Configurable via `get_checkin_policy(hotel)`  
**Current Time**: `get_hotel_now(hotel)` converts UTC to hotel timezone
**Date Evaluation**: Check-in validation uses hotel local time via `now_local` parameter

---

## 3. ACCESS CONTROL FOR GUEST ACTIONS

### 🔐 **Existing Token-Based Access Control**  
**Location**: `bookings/services.py`, `hotel/models.py`

**Core Function**: `resolve_guest_chat_context(hotel_slug, token_str, required_scopes, action_required)`

**Access Control Logic**:
```python
# Token must be ACTIVE and not expired
if guest_token.expires_at and timezone.now() > guest_token.expires_at:
    raise InvalidTokenError("Token has expired")

# For action endpoints: Must be checked in
if action_required and not booking.checked_in_at:
    raise NotInHouseError("Guest not checked in")
    
if action_required and booking.checked_out_at:
    raise NotInHouseError("Guest already checked out")
```

### 🛎️ **Guest Action Enforcement**

#### **Guest Chat Access**
**EXISTS**: Token-based validation enforced server-side
- **Endpoint**: `POST /api/public/chat/{hotel_slug}/guest/message/`
- **Validation**: Calls `resolve_guest_chat_context()` with `action_required=True`
- **Requirement**: `checked_in_at != null` AND `checked_out_at == null`

#### **Room Service Orders**  
**PARTIALLY EXISTS**: Structure in place, enforcement incomplete
- **Endpoint**: `/api/public/hotel/{hotel_slug}/room-services/orders/`
- **Current State**: Endpoint exists, token integration planned but not fully implemented
- **Token Logic**: Skeleton exists in `hotel/guest_portal_views.py`

#### **Breakfast Orders**
**PARTIALLY EXISTS**: Model structure exists, token enforcement incomplete  
- **Models**: `BreakfastOrder`, `BreakfastOrderItem` exist in `room_services/models.py`
- **Endpoints**: Basic CRUD exists, guest token integration incomplete
- **Current**: Staff-facing endpoints functional

### 🚫 **What Does NOT Exist**
- **Unified guest action validation** - each service implements separately
- **Server-side breakfast order validation** for guest tokens
- **Server-side room service validation** for guest tokens  
- **Automatic action blocking** based on checkout status
- **Checkout cutoff time enforcement** for guest actions

---

## 4. EXISTING CONTEXT/HELPER LOGIC

### ✅ **Helper Functions That EXIST**

#### **Token Context Resolution**
**Function**: `resolve_token_context(raw_token)` in `hotel/services/booking.py`
**Returns**:
```python
{
    'booking_id': str,
    'hotel_slug': str, 
    'assigned_room': {...} or None,
    'is_checked_in': bool,
    'is_checked_out': bool,
    'allowed_actions': list[str]  # Contains actions like 'chat'
}
```

#### **In-House Status Check**  
**Function**: `resolve_in_house_context(raw_token)` in `hotel/services/booking.py`
**Logic**:
```python
is_in_house = (
    booking.status == 'CHECKED_IN' and  # NOTE: This looks wrong - should be checking checked_in_at
    booking.assigned_room is not None and
    booking.check_in <= current_date <= booking.check_out
)
```
⚠️ **POTENTIAL BUG**: Checks `status == 'CHECKED_IN'` but `CHECKED_IN` is not in STATUS_CHOICES

#### **Guest Chat Context Resolution**
**Function**: `resolve_guest_chat_context()` in `bookings/services.py`
**Purpose**: Single source of truth for guest chat authentication
**Validates**: Token, hotel match, in-house status, room assignment

#### **Booking Expiration Logic**
**Function**: `_booked_for_date()` in `hotel/services/availability.py`
**Logic**: Excludes expired PENDING_PAYMENT bookings from availability
```python
Q(status='CONFIRMED') |  # CONFIRMED always blocks
(Q(status='PENDING_PAYMENT') & 
 (Q(expires_at__isnull=True) | Q(expires_at__gt=now)))  # Not expired
```

### ❌ **Helper Functions That DO NOT Exist**
- **`is_booking_expired(booking)`** - no centralized expiration check
- **`is_stay_active(booking)`** - no unified stay status check  
- **`should_block_guest_actions(booking)`** - no centralized action gating
- **Checkout time validation** - no helper for "past checkout time" logic

---

## 5. ENFORCEMENT

### 🔒 **Current Server-Side Enforcement**

#### **Guest Chat Messages**  
✅ **ENFORCED**: `guest_send_message()` in `chat/views.py`
- Validates token via `resolve_guest_chat_context()`
- Requires `checked_in_at != null` AND `checked_out_at == null`
- Returns 403 if not in-house

#### **Booking Management**
✅ **ENFORCED**: Cancellation endpoints validate booking status
- Only allows cancellation for `PENDING_PAYMENT` or `CONFIRMED` bookings
- Uses `BookingManagementToken` for secure access

#### **Check-in Process**
✅ **ENFORCED**: Comprehensive validation in `validate_checkin()` 
- Status must be `CONFIRMED` 
- `paid_at` must not be null
- Date/time window validation via hotel policy

### ⚠️ **Incomplete/Missing Enforcement**

#### **Room Service Orders**
**Current State**: Basic endpoint exists, **NO TOKEN VALIDATION**
- Endpoint: `room_services/views.py` - `OrderViewSet`
- Missing: Guest token validation
- Missing: In-house status checking

#### **Breakfast Orders**
**Current State**: Staff-facing endpoints only  
- Models exist with hotel/room_number fields
- **Missing**: Guest-facing endpoints with token validation
- **Missing**: Date range validation (can't order for past dates)

#### **Expired Booking Response**
**Current State**: Varies by endpoint
- **Availability**: Expired bookings excluded from blocking
- **Guest Actions**: Token expiration returns 404 (anti-enumeration)
- **Staff Views**: Expired bookings filtered out of operational lists

---

## 6. EXISTING ASSUMPTIONS

### 🏨 **Business Logic Assumptions**

1. **Check-out Date is Exclusive**: `check_out` date means "checkout BY this date"
2. **Hotel Timezone**: Default to Europe/Dublin, configurable per hotel  
3. **Token Security**: Use SHA-256 hashed tokens with anti-enumeration (404 for invalid)
4. **In-House Definition**: `checked_in_at != null AND checked_out_at == null`
5. **Guest Records Preserved**: Guest records are NOT deleted on checkout (for audit)
6. **Single Active Token**: Only one ACTIVE GuestBookingToken per booking
7. **Payment-Status Coupling**: `paid_at != null` determines payment completion

### 🔧 **Technical Assumptions**

1. **Atomic Operations**: All check-in/checkout use `transaction.atomic()`
2. **Token Expiration**: Computed dynamically (`expires_at <= now()`)
3. **Room Assignment**: `assigned_room` field is source of truth for room location  
4. **Status Progression**: Linear progression through STATUS_CHOICES
5. **Date Range Logic**: Overnight logic (`check_in <= date < check_out`)

---

## 7. SUMMARY

### ✅ **What EXISTS**
- Complete booking lifecycle tracking with timestamps
- Comprehensive status system with 8 distinct states
- Token-based guest authentication system  
- Hotel timezone configuration system
- Guest chat access control (fully implemented)
- Booking expiration handling for unpaid bookings
- Check-in/checkout business rule validation

### ❌ **What does NOT exist**  
- Unified guest action validation framework
- Server-side breakfast order enforcement 
- Server-side room service token validation
- Checkout time cutoff enforcement
- Centralized "booking validity" helper functions
- Automatic action blocking based on checkout status

### 🔧 **Current Frontend Assumptions**
- Room service ordering: **Frontend decides access** (no server validation)
- Breakfast ordering: **Staff-only** (no guest-facing implementation)
- Action availability: **Partially enforced** (chat enforced, orders not enforced)
