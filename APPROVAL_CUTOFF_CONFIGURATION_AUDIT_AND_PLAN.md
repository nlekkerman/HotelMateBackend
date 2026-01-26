# APPROVAL_CUTOFF_CONFIGURATION_AUDIT_AND_PLAN

## Audit: Existing Hotel Configuration Patterns

### Hotel Configuration Infrastructure ✅ 

**Model**: [HotelAccessConfig](hotel/models.py#L313-375) - One-to-one relationship with Hotel
- **Current Time Fields**: 
  - `standard_checkout_time = TimeField(default="11:00")` ✅ REUSABLE PATTERN
  - `late_checkout_grace_minutes = PositiveIntegerField(default=30)` ✅ REUSABLE PATTERN  
  - `approval_sla_minutes = PositiveIntegerField(default=30)` ✅ REUSABLE PATTERN
- **Status**: Time configuration infrastructure already exists

**Timezone System**: [Hotel.timezone_obj](hotel/models.py#L257-259) property
- **Source**: `Hotel.timezone` field (IANA string, default='Europe/Dublin')
- **Implementation**: Returns `pytz.timezone(self.timezone)` object
- **Status**: Timezone handling already implemented ✅

### Staff API Infrastructure ✅

**Serializer**: [HotelAccessConfigStaffSerializer](hotel/staff_serializers.py#L20-33)
- **Current Exposed Fields**: Portal toggles, PIN settings, session limits
- **Missing Fields**: Time control fields (`standard_checkout_time`, `late_checkout_grace_minutes`, `approval_sla_minutes`)
- **Pattern**: Uses `ModelSerializer` with explicit field list

**ViewSet**: [StaffAccessConfigViewSet](hotel/staff_views.py#L327-351)
- **Methods**: GET/PUT/PATCH only (auto-creates config if missing)
- **Permissions**: IsAuthenticated, IsStaffMember, IsSameHotel
- **Pattern**: OneToOne relationship, `get_or_create` in `get_object()`

**API Endpoint**: `/api/staff/hotel/<hotel_slug>/access-config/`
- **Status**: Live endpoint ready for field expansion ✅

### Current Approval Cutoff Logic ❌

**Hardcoded Implementation**: [compute_approval_cutoff](apps/booking/services/booking_deadlines.py#L37-63)
```python
# CURRENT - HARDCODED 22:00
cutoff_local = hotel_tz.localize(
    timezone.datetime.combine(booking.check_in, time(22, 0))  # ← HARDCODED
)
```

**Usage Points**:
- [auto_expire_overdue_bookings.py](hotel/management/commands/auto_expire_overdue_bookings.py#L57) - Auto-expiry job
- Background processes that enforce expiry deadlines

**Business Rule**: All bookings must be approved by 22:00 on check-in day (hotel timezone)
- **Day Offset**: Currently 0 (same day only)
- **Time**: Fixed at 22:00
- **Status**: REQUIRES CONFIGURATION ❌

---

## Implementation Plan: Hotel-Controlled Approval Cutoff

### Phase 1: Configuration Storage

**Add to HotelAccessConfig model**:
```python
# NEW FIELDS
approval_cutoff_time = models.TimeField(
    default="22:00",
    help_text="Daily cutoff time for booking approval (e.g., 22:00)"
)
approval_cutoff_day_offset = models.PositiveSmallIntegerField(
    default=0,
    choices=[(0, "Same day"), (1, "Next day")],
    help_text="Day offset: 0=check-in day, 1=day after check-in"
)
```

**Migration**: Add fields with sane defaults (22:00, offset=0) - no business logic embedded

### Phase 2: Update Approval Logic

**Replace hardcoded logic in** [compute_approval_cutoff](apps/booking/services/booking_deadlines.py#L37-63):
```python
def compute_approval_cutoff(booking) -> timezone.datetime:
    """Compute approval cutoff using hotel-configured rule."""
    hotel_config = booking.hotel.access_config
    
    # Use hotel configuration
    cutoff_time = hotel_config.approval_cutoff_time  # e.g., 22:00
    day_offset = hotel_config.approval_cutoff_day_offset  # 0 or 1
    
    # Compute cutoff date (check-in + offset)
    cutoff_date = booking.check_in + timedelta(days=day_offset)
    
    # Create timezone-aware datetime
    hotel_tz = booking.hotel.timezone_obj
    cutoff_local = hotel_tz.localize(
        timezone.datetime.combine(cutoff_date, cutoff_time)
    )
    
    return cutoff_local.astimezone(timezone.utc)
```

### Phase 3: Staff API Exposure

**Expand HotelAccessConfigStaffSerializer fields**:
```python
fields = [
    # Existing fields...
    'guest_portal_enabled',
    'staff_portal_enabled',
    # ADD TIME CONTROL FIELDS
    'standard_checkout_time',
    'late_checkout_grace_minutes', 
    'approval_sla_minutes',
    'approval_cutoff_time',        # NEW
    'approval_cutoff_day_offset',  # NEW
]
```

**API Usage**: Existing `/api/staff/hotel/<hotel_slug>/access-config/` endpoint ready ✅

### Phase 4: Optional Booking Payload Enhancement

**Add computed cutoff to booking serializers** (for frontend clarity):
```python
approval_cutoff_at = serializers.SerializerMethodField()

def get_approval_cutoff_at(self, obj):
    if obj.status == 'PENDING_APPROVAL':
        return compute_approval_cutoff(obj)
    return None
```

---

## Implementation Constraints

### Day Offset Restrictions
- **Supported**: `{0, 1}` only (same-day or next-day)
- **Not Supported**: Negative offsets (-1) - adds validation complexity without clear use case
- **Rationale**: Keep simple initially, extend if hotels request

### Timezone Source
- **Source**: `Hotel.timezone_obj` property (existing system)
- **Fallback**: `pytz.timezone(hotel.timezone)` with Europe/Dublin default
- **Status**: No guessing required - infrastructure exists ✅

### SLA vs Expiry Separation
- **SLA Warnings**: Keep `approval_sla_minutes` unchanged (warnings only)
- **Hard Expiry**: Use new cutoff configuration (enforcement)
- **Jobs Affected**: Only auto-expiry job, not SLA deadline warnings

---

## Default Configuration Strategy

### Sane Defaults (No Business Logic)
- **approval_cutoff_time**: `"22:00"` (maintains current behavior)
- **approval_cutoff_day_offset**: `0` (same day as check-in)
- **Rationale**: Preserves existing 22:00 same-day rule as default, but configurable

### Migration Strategy
- **Existing Hotels**: Get defaults automatically (no behavior change)
- **New Hotels**: Use defaults unless explicitly configured
- **Staff Control**: Can modify via existing API endpoint immediately after migration

---

## Files Requiring Changes

### Database Layer
1. [hotel/models.py](hotel/models.py#L313-375) - Add cutoff fields to HotelAccessConfig
2. **Migration**: `python manage.py makemigrations hotel`

### Business Logic 
3. [apps/booking/services/booking_deadlines.py](apps/booking/services/booking_deadlines.py#L37-63) - Replace hardcoded logic
4. [hotel/management/commands/auto_expire_overdue_bookings.py](hotel/management/commands/auto_expire_overdue_bookings.py) - Verify uses new logic

### API Layer
5. [hotel/staff_serializers.py](hotel/staff_serializers.py#L20-33) - Add time fields to serializer

### Optional Enhancement
6. Booking serializers - Add computed `approval_cutoff_at` field for frontend

---

## Success Criteria

- ✅ **Configuration**: Staff can set cutoff time (hour) and day offset (0/1) per hotel
- ✅ **Enforcement**: Auto-expiry job uses hotel-specific cutoff, not hardcoded 22:00  
- ✅ **Defaults**: Existing behavior preserved (22:00 same-day) until staff changes
- ✅ **API**: Existing staff endpoint exposes new time controls
- ✅ **Timezone**: Uses existing hotel timezone system (no guessing)
- ✅ **Separation**: SLA warnings unaffected, only expiry logic changes

---

## BACKEND IMPLEMENTATION PROMPT (FINAL - SOURCE OF TRUTH)

**Implement hotel-configurable approval cutoff using existing infrastructure.**

### Context / Existing Infrastructure (Verified):
- `HotelAccessConfig` exists and already stores time-related fields (`standard_checkout_time`, `late_checkout_grace_minutes`, `approval_sla_minutes`)
- `Hotel.timezone_obj` exists and returns the hotel timezone (pytz)  
- Staff endpoint already exists: `StaffAccessConfigViewSet` at `/api/staff/hotel/<hotel_slug>/access-config/` with GET/PUT/PATCH and get_or_create behavior
- Current `compute_approval_cutoff()` is hardcoded to 22:00 same-day and is used by `auto_expire_overdue_bookings.py`

### Requirements:

**1. Add config fields to HotelAccessConfig:**
- `approval_cutoff_time` (TimeField) 
- `approval_cutoff_day_offset` (int, choices restricted to {0,1} only: same day / next day)
- Provide defaults to preserve current behavior, but do not embed business logic beyond defaults

**2. Replace hardcoded 22:00 in `apps/booking/services/booking_deadlines.py::compute_approval_cutoff()`:**
- Compute cutoff as: `cutoff_date = booking.check_in + day_offset`, `cutoff_time = config.approval_cutoff_time`
- Build timezone-aware datetime using `booking.hotel.timezone_obj`
- Return UTC-aware datetime
- No guessing, no frontend math; backend is single source of truth

**3. Auto-expiry enforcement must use cutoff, not SLA:**
- Update `hotel/management/commands/auto_expire_overdue_bookings.py` so the expiry condition is based on `now > compute_approval_cutoff(booking)`
- Keep SLA warnings/risk levels unchanged (SLA remains "warnings only")
- **Invariant**: SLA (approval_sla_minutes) affects warnings only and must never trigger expiry/refunds. Only compute_approval_cutoff() can cause expiry.

**4. Expose time controls to staff UI via existing endpoint:**
- Expand `HotelAccessConfigStaffSerializer` to include: `standard_checkout_time`, `late_checkout_grace_minutes`, `approval_sla_minutes`, `approval_cutoff_time`, `approval_cutoff_day_offset`
- Ensure PATCH works and validates day_offset is only 0 or 1
- **Validation Rule**: Validate approval_cutoff_day_offset ∈ {0,1} and validate approval_cutoff_time is a valid time. Reject anything else with 400.

**5. Optional but recommended:** add computed `approval_cutoff_at` to staff booking serializers (list + detail) for frontend clarity/debugging (read-only field computed from config)

### Deliverables:
- Migration(s)
- Updated `compute_approval_cutoff()`
- Updated auto-expire job to cutoff-based enforcement  
- Updated staff serializer exposure
- Tests covering: same-day vs next-day offsets, timezone correctness, SLA warnings unchanged while expiry uses cutoff

### Non-goals / Do NOT implement:
- No new config system
- No negative offsets  
- Do not change risk-level computation logic
- Do not implement checkout grace / late arrival changes in this PR

---

## Next Steps

Ready for implementation. All required infrastructure (models, API, timezone) already exists.
Hotel staff will be able to configure approval cutoffs immediately via existing staff API.