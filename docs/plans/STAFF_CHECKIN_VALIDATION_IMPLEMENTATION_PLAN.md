# Staff Check-in Validation Implementation Plan

## Overview
Implement comprehensive backend validation for staff check-in with timezone-aware rules, room readiness checks, and structured error handling. This plan enforces clean architecture with no hardcoded values, single validation source, and stable API contracts.

## Core Principles

### 1. One Source of Truth: HotelSettings JSON
- **No hardcoded times in views** - All policy configuration lives in HotelSettings JSON
- **Consistent defaults** - Every hotel gets reliable fallback values without migrations
- **Future-proof schema** - Settings structure supports expansion without breaking changes

### 2. One Validation Function (Gatekeeper Pattern)
- **Single responsibility** - All check-in business rules live in one place
- **Prevents rule sprawl** - No "random rules in random views" anti-pattern
- **Testable isolation** - Pure function with clear inputs/outputs

### 3. Error Codes as API Contract
- **Stable messaging** - Frontend can rely on consistent error codes
- **No legacy mismatches** - Error responses become part of API specification
- **Clear UX mapping** - Each code maps to specific user experience

## Implementation Steps

### Step 1: Policy Schema + Defaults Resolver
**File:** `hotelmate/utils/checkin_policy.py`

```python
def get_checkin_policy(hotel):
    """
    Returns complete check-in policy with defaults for missing values
    
    If keys are missing in settings JSON, resolver injects defaults 
    and returns a complete policy object (but doesn't persist it yet).
    
    Schema:
    - timezone: Europe/Dublin
    - check_in_time: 15:00  
    - early_checkin_from: 12:00
    - late_arrival_cutoff: 02:00
    """
```

**Benefits:**
- No migrations required - works with existing HotelSettings
- Backwards compatible - empty settings JSON gets full defaults
- Format validation - ensures HH:MM time format, valid timezone strings
- Single point of policy configuration

### Step 2: Single Validation Function
**File:** `hotelmate/utils/checkin_validation.py`

```python
def validate_checkin(booking, room, policy, now_local):
    """
    Single gatekeeper for all check-in business rules
    Returns: (ok: bool, code: str, detail: str)
    
    Validates:
    - Booking status (CONFIRMED/APPROVED only)
    - Room assignment and readiness (READY_FOR_GUEST required)
    - Arrival window + early/late policy (exact window rules below)
    - Already checked-in → returns ok=True (idempotent success)
    """
```

**Validation Chain:**
1. Booking eligibility (status, assigned room, not already checked in)
2. Room readiness (READY_FOR_GUEST, not OUT_OF_ORDER/MAINTENANCE_REQUIRED)
3. **Arrival window + early/late policy** (exact rules):
   - `local_date == check_in_date AND local_time >= check_in_time`
   - **OR** `local_date == check_in_date + 1 AND local_time <= late_arrival_cutoff`

### Step 3: Enhanced BookingCheckInView
**File:** `staff/views/booking_views.py`

Updates to existing `BookingCheckInView`:
- Call `get_checkin_policy(hotel)` for configuration
- Call `validate_checkin()` for business rule validation
- Perform atomic state updates only after validation passes
- Return structured error responses with stable codes

### Step 4: Stable Error Codes
**API Contract:** These codes become permanent API behavior

```python
CHECKIN_ERROR_CODES = {
    'CHECKIN_TOO_EARLY': 'Check-in not allowed before {time}',
    'CHECKIN_WRONG_DATE': 'Check-in only allowed on arrival date {date}',
    'CHECKIN_TOO_LATE': 'Late arrival cutoff exceeded at {cutoff}',
    'ROOM_NOT_READY': 'Room {room} not ready for guest occupancy',
    'BOOKING_NOT_ELIGIBLE': 'Booking not eligible for check-in: {reason}'
}
```

**Response Format:** Uses existing DRF pattern - simple `error` field with code, `detail` field with message

### Step 5: Room Readiness Checks
Enhanced room status validation:
- Require `room.room_status = READY_FOR_GUEST`
- Reject `OUT_OF_ORDER` rooms with clear messaging
- Reject `MAINTENANCE_REQUIRED` rooms
- Validate `assigned_room` is not null

### Step 6: Comprehensive Test Coverage
**Test Categories:**
- **Time Restrictions:** Too early (before 12:00), too late (after 02:00), outside check-in hours
- **Date Validation:** Wrong arrival date, future dates, past dates
- **Room States:** Not assigned, out of order, maintenance required, already occupied
- **Booking States:** Not confirmed, already checked in, cancelled
- **Happy Path:** Valid check-in with proper state transitions
- **Edge Cases:** Timezone boundaries, midnight crossover, early check-in permission

## Technical Specifications

### Default Policy Values
```json
{
  "timezone": "Europe/Dublin",
  "check_in_time": "15:00",
  "early_checkin_from": "12:00", 
  "late_arrival_cutoff": "02:00"
}
```

### API Response Format (Error)
```json
{
  "error": "CHECKIN_TOO_EARLY",
  "detail": "Check-in not allowed before 15:00"
}
```

### API Response Format (Success)
```json
{
  "booking": {
    "id": "BK-2025-0001",
    "status": "CHECKED_IN",
    "checked_in_at": "2025-12-29T15:30:00Z",
    "assigned_room": {
      "number": "101",
      "room_status": "OCCUPIED",
      "is_occupied": true
    }
  }
}
```

## File Structure
```
hotelmate/utils/
├── checkin_policy.py      # Policy schema + defaults
├── checkin_validation.py  # Single validation function
└── timezone_helpers.py    # Hotel timezone utilities

staff/views/
└── booking_views.py       # Enhanced BookingCheckInView

tests/
├── test_checkin_policy.py
├── test_checkin_validation.py
└── test_staff_checkin_view.py
```

## Success Criteria
1. ✅ No hardcoded times in any view - all configuration from HotelSettings
2. ✅ Single validation function handles all check-in business rules
3. ✅ Stable error codes provide consistent API behavior
4. ✅ Room readiness properly enforced (READY_FOR_GUEST required)
5. ✅ Timezone-aware date/time validation works correctly
6. ✅ Backwards compatibility with existing hotels (defaults work)
7. ✅ Comprehensive test coverage for all edge cases

## Future Enhancements (Phase 2)
- Manager override permissions (`force=true` parameter)
- Role-based time restriction bypasses
- Hotel-specific early check-in policies
- Dynamic late arrival extensions
- Audit logging for policy violations