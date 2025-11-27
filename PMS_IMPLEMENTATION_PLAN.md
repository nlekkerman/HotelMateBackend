# PMS Availability & Pricing Engine Implementation Plan

## Overview
Refactor the Phase 1 booking system from inline view logic to a professional PMS-style architecture with dedicated models for rate management, inventory control, and promotions. Introduce a service layer (`hotel/services/`) to centralize all business logic, making it reusable across views and testable independently of DRF. Maintain 100% backward compatibility with existing public API schemas.

## Implementation Steps

### Step 1: Create PMS Models in `rooms/models.py`
Add five new models to support advanced rate management and inventory control:

1. **RatePlan** - Rate plans per hotel (e.g., "Standard Rate", "Non-Refundable")
   - Fields: hotel, name, code, description, is_refundable, default_discount_percent, is_active
   - Unique constraint: (hotel, code)

2. **RoomTypeRatePlan** - Link room types to rate plans with optional base price override
   - Fields: room_type, rate_plan, base_price, is_active
   - Unique constraint: (room_type, rate_plan)

3. **DailyRate** - Per-day pricing for room type + rate plan combinations
   - Fields: room_type, rate_plan, date, price
   - Unique constraint: (room_type, rate_plan, date)

4. **Promotion** - Promotional codes with advanced rules
   - Fields: hotel, code, name, description, discount_percent, discount_fixed
   - Date range: valid_from, valid_until
   - Restrictions: room_types (M2M), rate_plans (M2M), min_nights, max_nights
   - Status: is_active

5. **RoomTypeInventory** - Daily inventory control per room type
   - Fields: room_type, date, total_rooms, stop_sell
   - Unique constraint: (room_type, date)
   - Purpose: Override physical room count or stop sales for specific dates

**Actions:**
- Add models to `rooms/models.py`
- Run `python manage.py makemigrations rooms`
- Run `python manage.py migrate`
- Register models in `rooms/admin.py` with list_display and list_filter

### Step 2: Build Availability Service (`hotel/services/availability.py`)

Create pure Python service functions for availability checking:

**Functions:**
1. `validate_dates(check_in_str, check_out_str)` → (check_in, check_out, nights)
   - Parse and validate date strings
   - Ensure check_out > check_in
   - Raise ValueError on invalid input

2. `_inventory_for_date(room_type, day)` → int
   - Check RoomTypeInventory for overrides:
     - If stop_sell=True → return 0
     - If total_rooms is set → return total_rooms
   - Fallback: Count physical Room instances where is_active=True

3. `_booked_for_date(room_type, day)` → int
   - Count RoomBooking overlaps for that date
   - Status filter: PENDING_PAYMENT or CONFIRMED
   - Overlap logic: check_in <= day < check_out

4. `is_room_type_available(room_type, check_in, check_out, required_units)` → bool
   - For each night in range:
     - available = _inventory_for_date() - _booked_for_date()
   - Return True only if available >= required_units for ALL nights

5. `get_room_type_availability(hotel, check_in, check_out, adults, children)` → List[Dict]
   - Iterate hotel's active room types
   - Calculate can_accommodate (max_occupancy check)
   - Calculate is_available (real inventory check)
   - Return list of dicts matching current API response format

### Step 3: Build Pricing Service (`hotel/services/pricing.py`)

Create pricing calculation engine with promotion support:

**Constants:**
- `VAT_RATE = Decimal('0.09')` (Ireland VAT)
- `DEFAULT_RATE_PLAN_CODE = "STD"`

**Functions:**
1. `get_or_create_default_rate_plan(hotel)` → RatePlan
   - Lazy creation of "Standard" rate plan per hotel
   - Code: "STD", is_refundable=True, is_active=True

2. `get_nightly_base_rates(room_type, check_in, check_out, rate_plan)` → List[(date, Decimal)]
   - For each night, prioritize:
     1. DailyRate for (room_type, rate_plan, date)
     2. RoomTypeRatePlan.base_price for (room_type, rate_plan)
     3. room_type.starting_price_from
   - Return list of (date, price) tuples

3. `apply_promotion(hotel, room_type, rate_plan, check_in, check_out, subtotal, promo_code)` → (new_subtotal, discount, Promotion|None)
   - Try Promotion model first:
     - Match: code (case-insensitive), hotel, date range, is_active
     - Validate: room_types, rate_plans, min_nights, max_nights restrictions
     - Apply: discount_percent and/or discount_fixed
   - Fallback to legacy codes if no Promotion found:
     - WINTER20 → 20% off
     - SAVE10 → 10% off
   - Single promotion per booking (no stacking)

4. `apply_taxes(subtotal)` → (total_with_taxes, taxes_amount)
   - Calculate 9% VAT on subtotal
   - Return (total, taxes)

5. `build_pricing_quote_data(hotel, room_type, check_in, check_out, adults, children, promo_code)` → Dict
   - Orchestrate full pricing flow:
     - Get/create default rate plan
     - Calculate nightly rates and subtotal
     - Apply promotion
     - Apply taxes
     - Create PricingQuote instance (valid_until = now + 30 minutes)
   - Return dict matching existing HotelPricingQuoteView response schema

### Step 4: Build Booking Service (`hotel/services/booking.py`)

Create booking creation helper:

**Function:**
- `create_room_booking_from_request(hotel, room_type, check_in, check_out, adults, children, guest_data, special_requests, promo_code)` → RoomBooking
  - Reuse pricing service logic for consistent calculations
  - Create RoomBooking with:
    - status='PENDING_PAYMENT'
    - Auto-generated booking_id and confirmation_number (existing logic)
    - Guest information from guest_data dict
    - Calculated total_amount and currency
  - Do NOT modify existing bookings (historical data preserved)

### Step 5: Refactor `HotelAvailabilityView`

**Changes:**
- Import: `from hotel.services.availability import validate_dates, get_room_type_availability`
- Replace date parsing with: `validate_dates(check_in_str, check_out_str)`
- Replace availability logic with: `get_room_type_availability(hotel, check_in, check_out, adults, children)`
- Handle ValueError from validate_dates → 400 response

**Preserved:**
- Query params: check_in, check_out, adults, children
- Response structure: hotel, hotel_name, check_in, check_out, nights, adults, children, total_guests, available_rooms
- Error handling: 400 for invalid dates, 404 for missing hotel
- Permission: AllowAny

### Step 6: Refactor `HotelPricingQuoteView`

**Changes:**
- Import: `from hotel.services.pricing import build_pricing_quote_data`
- Import: `from hotel.services.availability import validate_dates`
- Replace date parsing with: `validate_dates(check_in_str, check_out_str)`
- Replace pricing calculation with: `build_pricing_quote_data(...)`
- Return service function result directly

**Preserved:**
- POST schema: room_type_code, check_in, check_out, adults, children, promo_code
- Response structure: quote_id, valid_until, currency, room_type, dates, guests, breakdown, applied_promo
- Quote validity: 30 minutes
- Error handling: 400 for invalid dates, 404 for room type not found

### Step 7: Refactor `HotelBookingCreateView`

**Changes:**
- Import: `from hotel.services.booking import create_room_booking_from_request`
- Import: `from hotel.services.availability import validate_dates`
- Replace date parsing with: `validate_dates(check_in_str, check_out_str)`
- Replace booking creation with: `create_room_booking_from_request(...)`
- Build response from returned booking instance

**Preserved:**
- POST schema: quote_id, room_type_code, check_in, check_out, adults, children, guest, special_requests, promo_code
- Guest validation: all fields required (first_name, last_name, email, phone)
- Response structure: booking_id, confirmation_number, status, created_at, hotel, room, dates, guests, guest, special_requests, pricing, promo_code, quote_id, payment_required, payment_url
- Payment URL format: `/api/bookings/{booking.booking_id}/payment/session/`
- Status code: 201 CREATED

## Architecture Principles

### Service Layer Rules
1. **No DRF imports** - Services must not import Response, APIView, status, etc.
2. **Pure business logic** - All calculations and validations in services
3. **Model imports only** - Direct imports from hotel.models, rooms.models, bookings.models
4. **Reusability** - Functions callable from views, management commands, tests
5. **Cross-service imports allowed** - booking.py can import from pricing.py

### Model Placement
- **rooms app**: All PMS models (RatePlan, RoomTypeRatePlan, DailyRate, Promotion, RoomTypeInventory)
- **bookings app**: Guest-facing models (RoomBooking, PricingQuote) - DO NOT MOVE
- **hotel app**: Hotel and configuration models

### Backward Compatibility
- All public API endpoints unchanged (URLs, methods, schemas)
- Existing RoomBooking and PricingQuote records preserved
- New pricing engine only applies to new bookings
- Response JSON structures identical to Phase 1

## Key Design Decisions

### 1. Default Rate Plan Strategy
- **Decision**: Lazy creation on-demand
- **Rationale**: Avoid seeding test/demo hotels unnecessarily
- **Implementation**: `get_or_create_default_rate_plan()` in pricing service

### 2. Inventory Fallback
- **Decision**: Count only active Rooms (filter is_active=True)
- **Rationale**: Match real-world PMS behavior
- **Note**: Room model doesn't have is_out_of_order field, so only check is_active

### 3. Promotion Stacking
- **Decision**: Single promotion per booking (first match wins)
- **Rationale**: Simplify Phase 1, document extensibility for later
- **Implementation**: Return early after first valid Promotion found

### 4. Service Import Boundaries
- **Decision**: Services can import each other, use function-level imports if circular
- **Rationale**: Enable code reuse between pricing and booking services
- **Pattern**: `from hotel.services.pricing import get_nightly_base_rates`

### 5. Historical Data
- **Decision**: Never recalculate existing bookings
- **Rationale**: Maintain audit trail and pricing integrity
- **Implementation**: Only new bookings use new pricing engine

## Testing Considerations

After implementation, test:
1. **Availability**: Real inventory vs bookings overlap
2. **Pricing**: Promotion application (model + legacy codes)
3. **Booking**: End-to-end flow with promotions
4. **Backward compatibility**: Existing API responses unchanged
5. **Edge cases**: Stop-sell dates, inventory overrides, expired quotes

## Migration Strategy

1. Add models → migrate rooms app only
2. Create service layer → no DB changes
3. Refactor views one at a time → test each endpoint
4. Staff can configure rate plans, promotions via admin
5. Legacy hardcoded promo codes still work as fallback

## Future Enhancements (Out of Scope)

- Multi-promotion stacking rules
- Guest-specific rate plans (loyalty, corporate)
- Channel manager integration
- Dynamic pricing based on occupancy
- Overbooking rules and waitlists
- Rate shopping and competitor analysis
