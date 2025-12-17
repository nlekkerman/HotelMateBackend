# Booking Serializer Audit - Source of Truth
**Generated**: December 17, 2025  
**Purpose**: Complete audit of all booking-related serializers, endpoints, and response shapes to eliminate duplicated/contradictory payloads and establish canonical contracts.

---

## A) Canonical Data Model

### Intended Truth Hierarchy
- **Pre-Check-in Truth**: `RoomBooking.party` (PRIMARY + companions)
- **Post-Check-in Truth**: `Guest` / `in_house` records  
- **Authentication Models**:
  - Token-based precheckin: "public" access but authenticated by token
  - Staff APIs: Full authentication + hotel scoping
- **Configuration Constraint**: "Required ⊆ Enabled" for precheckin fields

### Data Flow
```
Booking Creation → Party Management → Pre-checkin → Check-in → In-House
       ↓                ↓               ↓           ↓          ↓
  primary_* fields → party.PRIMARY → party → Guest records → in_house
```

---

## B) Endpoint → Serializer Mapping

| Endpoint | Method | View/ViewSet | Serializer(s) | Auth | Hotel Scope | Notes |
|----------|--------|--------------|---------------|------|-------------|--------|
| **PUBLIC BOOKING ENDPOINTS** |
| `/api/public/hotel/{slug}/room-bookings/{id}/` | GET | `PublicRoomBookingDetailView` | `RoomBookingDetailSerializer` | None | ✓ | Mock data Phase 1 |
| `/api/public/hotel/{slug}/pricing/quote/` | GET | `HotelPricingQuoteView` | `PricingQuoteSerializer` | None | ✓ | Availability + pricing |
| **PUBLIC PRECHECKIN ENDPOINTS** |
| `/api/public/hotel/{slug}/precheckin/` | GET | `ValidatePrecheckinTokenView` | Manual dict construction | Token | ✓ | Returns booking + party + config |
| `/api/public/hotel/{slug}/precheckin/submit/` | POST | `SubmitPrecheckinDataView` | `BookingGuestSerializer` | Token | ✓ | Party + precheckin data |
| **STAFF BOOKING ENDPOINTS** |
| `/api/staff/hotel/{slug}/room-bookings/` | GET | `StaffBookingsListView` | `StaffRoomBookingListSerializer` | Staff + Hotel | ✓ | List with filtering |
| `/api/staff/hotel/{slug}/room-bookings/{id}/` | GET | `StaffBookingDetailView` | `StaffRoomBookingDetailSerializer` | Staff + Hotel | ✓ | Complete booking data |
| `/api/staff/hotel/{slug}/room-bookings/{id}/confirm/` | PATCH | `StaffBookingConfirmView` | `StaffRoomBookingDetailSerializer` | Staff + Hotel | ✓ | Status update |
| `/api/staff/hotel/{slug}/room-bookings/{id}/cancel/` | PATCH | `StaffBookingCancelView` | `RoomBookingDetailSerializer` | Staff + Hotel | ✓ | Cancellation + response |
| `/api/staff/hotel/{slug}/room-bookings/{id}/assign-room/` | POST | `BookingAssignmentView` | `StaffRoomBookingDetailSerializer` | Staff + Hotel | ✓ | Check-in process |
| `/api/staff/hotel/{slug}/room-bookings/{id}/checkout/` | POST | `BookingAssignmentView` | `StaffRoomBookingDetailSerializer` | Staff + Hotel | ✓ | Check-out process |
| `/api/staff/hotel/{slug}/room-bookings/{id}/party/` | GET/POST | `BookingPartyManagementView` | `BookingPartyGroupedSerializer` | Staff + Hotel | ✓ | Party CRUD |
| `/api/staff/hotel/{slug}/room-bookings/{id}/send-precheckin-link/` | POST | `SendPrecheckinLinkView` | Success dict | Staff + Hotel | ✓ | Email precheckin link |
| **SAFE ROOM ASSIGNMENT** |
| `/api/staff/hotel/{slug}/room-bookings/{id}/available-rooms/` | GET | `AvailableRoomsView` | Room list | Staff + Hotel | ✓ | Available room list |
| `/api/staff/hotel/{slug}/room-bookings/{id}/safe-assign-room/` | POST | `SafeAssignRoomView` | `StaffRoomBookingDetailSerializer` | Staff + Hotel | ✓ | Atomic assignment |
| `/api/staff/hotel/{slug}/room-bookings/safe/` | GET | `SafeStaffBookingListView` | `RoomBookingListSerializer` | Staff + Hotel | ✓ | Enhanced list view |

---

## C) Serializer Inventory

### 1. BookingOptionsSerializer
**File**: `hotel/booking_serializers.py`  
**Model**: `BookingOptions`  
**Fields**: `['primary_cta_label', 'primary_cta_url', 'secondary_cta_label', 'secondary_cta_phone', 'terms_url', 'policies_url']`  
**Used**: Hotel public page configurations  
**Issues**: None identified

### 2. BookingGuestSerializer  
**File**: `hotel/booking_serializers.py`  
**Model**: `BookingGuest`  
**Fields**: `['id', 'role', 'first_name', 'last_name', 'full_name', 'email', 'phone', 'is_staying', 'created_at']`  
**Used**: Precheckin endpoints, party management  
**Issues**: None - this is correct party member representation

### 3. RoomTypeSerializer
**File**: `hotel/booking_serializers.py`  
**Model**: `RoomType`  
**Fields**: `['id', 'code', 'name', 'short_description', 'max_occupancy', 'bed_setup', 'photo_url', 'starting_price_from', 'currency', 'booking_code', 'booking_url', 'availability_message']`  
**Used**: Booking availability endpoints  
**Issues**: None identified

### 4. PricingQuoteSerializer
**File**: `hotel/booking_serializers.py`  
**Model**: `PricingQuote`  
**Fields**: `['quote_id', 'hotel', 'room_type', 'room_type_name', 'check_in', 'check_out', 'adults', 'children', 'base_price_per_night', 'number_of_nights', 'subtotal', 'taxes', 'fees', 'discount', 'total', 'currency', 'promo_code', 'created_at', 'valid_until']`  
**Used**: Pricing/availability endpoints  
**Issues**: None identified

### 5. RoomBookingListSerializer ⚠️ **PROBLEMATIC**
**File**: `hotel/booking_serializers.py`  
**Model**: `RoomBooking`  
**Fields**: `['id', 'booking_id', 'confirmation_number', 'hotel_name', 'room_type_name', 'guest_name', 'primary_email', 'primary_phone', 'booker_type', 'assigned_room_number', 'check_in', 'check_out', 'nights', 'adults', 'children', 'total_amount', 'currency', 'status', 'checked_in_at', 'checked_out_at', 'created_at', 'paid_at']`  
**Issues**:
- ❌ Exposes `adults`, `children` at root level (should use party.total_count)
- ❌ Uses `guest_name` method field that returns `primary_guest_name` (duplicates party data)

### 6. RoomBookingDetailSerializer ❌ **MAJOR ISSUES**
**File**: `hotel/booking_serializers.py`  
**Model**: `RoomBooking`  
**Fields**: `['id', 'booking_id', 'confirmation_number', 'hotel_name', 'hotel_preset', 'room_type_name', 'room_photo_url', 'guest_name', 'primary_first_name', 'primary_last_name', 'primary_email', 'primary_phone', 'booker_type', 'booker_first_name', 'booker_last_name', 'booker_email', 'booker_phone', 'booker_company', 'assigned_room', 'assigned_room_number', 'check_in', 'check_out', 'nights', 'adults', 'children', 'total_amount', 'currency', 'status', 'special_requests', 'promo_code', 'payment_reference', 'payment_provider', 'paid_at', 'checked_in_at', 'checked_out_at', 'created_at', 'updated_at', 'internal_notes', 'cancellation_details', 'booking_summary', 'party', 'party_complete', 'party_missing_count']`  
**Issues**:
- ❌ Exposes `primary_first_name`, `primary_last_name`, `primary_email`, `primary_phone` AND `party` (duplicate data)
- ❌ Exposes `adults`, `children` at root level (conflicts with party.total_count)  
- ❌ Custom `get_party()` method creates own structure instead of using canonical serializer
- ✅ Correctly includes `party_complete`, `party_missing_count` flags

### 7. BookingPartyGuestSerializer ✅ **CANONICAL**
**File**: `hotel/canonical_serializers.py`  
**Model**: `BookingGuest`  
**Fields**: `['id', 'role', 'first_name', 'last_name', 'full_name', 'email', 'phone', 'is_staying', 'created_at']`  
**Used**: Canonical party member representation  
**Issues**: None - this is the correct single member serializer

### 8. BookingPartyGroupedSerializer ✅ **CANONICAL**
**File**: `hotel/canonical_serializers.py`  
**Model**: Custom serializer for RoomBooking  
**Returns**: `{'primary': {...}, 'companions': [...], 'total_count': int}`  
**Used**: Staff endpoints via StaffRoomBookingDetailSerializer  
**Issues**: None - this is the canonical party structure

### 9. InHouseGuestSerializer
**File**: `hotel/canonical_serializers.py`  
**Model**: `Guest`  
**Fields**: `['id', 'first_name', 'last_name', 'full_name', 'guest_type', 'id_pin', 'room_number', 'check_in_date', 'check_out_date']`  
**Used**: Post-checkin guest display  
**Issues**: None identified

### 10. InHouseGuestsGroupedSerializer  
**File**: `hotel/canonical_serializers.py`  
**Model**: Custom serializer for RoomBooking  
**Returns**: Grouped in-house guest structure  
**Used**: Staff booking detail when checked_in_at != null  
**Issues**: ⚠️ Should only appear when `checked_in_at` is not null

### 11. StaffRoomBookingListSerializer ⚠️ **PARTIALLY PROBLEMATIC**
**File**: `hotel/canonical_serializers.py`  
**Model**: `RoomBooking`  
**Fields**: `['booking_id', 'confirmation_number', 'status', 'check_in', 'check_out', 'nights', 'assigned_room_number', 'booker_type', 'booker_summary', 'primary_guest_name', 'primary_email', 'booker_email', 'party_total_count', 'party_complete', 'party_missing_count', 'party_status_display', 'total_amount', 'currency', 'adults', 'children', 'created_at', 'updated_at']`  
**Issues**:
- ❌ Exposes both `party_total_count` AND `adults`, `children` (duplicate/conflicting data)
- ❌ Exposes `primary_guest_name` method field (duplicates party.primary data)
- ✅ Correctly includes party completion flags

### 12. StaffRoomBookingDetailSerializer ❌ **MAJOR ISSUES**
**File**: `hotel/canonical_serializers.py`  
**Model**: `RoomBooking`  
**Fields**: `['booking_id', 'confirmation_number', 'status', 'check_in', 'check_out', 'nights', 'adults', 'children', 'total_amount', 'currency', 'special_requests', 'promo_code', 'payment_reference', 'payment_provider', 'paid_at', 'checked_in_at', 'checked_out_at', 'created_at', 'updated_at', 'internal_notes', 'booker', 'primary_guest', 'party', 'in_house', 'room', 'flags']`  
**Nested Objects**: `booker`, `primary_guest`, `party`, `in_house`, `room`, `flags`  
**Issues**:
- ❌ Exposes `adults`, `children` at root level (conflicts with party structure)  
- ❌ Exposes both `primary_guest` object AND `party.primary` (duplicate data)
- ❌ Shows `in_house` even when not checked in
- ✅ Uses canonical `BookingPartyGroupedSerializer` for party

---

## D) Response Shape Examples

### Staff Booking Detail Response (Current - Problematic)
```json
{
  "booking_id": "BK-2025-001",
  "status": "CONFIRMED", 
  "adults": 2,           // ❌ DUPLICATE
  "children": 0,         // ❌ DUPLICATE
  "booker": {
    "type": "SELF",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  },
  "primary_guest": {     // ❌ DUPLICATE 
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  },
  "party": {             // ✅ CANONICAL
    "primary": {
      "id": 123,
      "role": "PRIMARY",
      "first_name": "John", 
      "last_name": "Doe",
      "email": "john@example.com"
    },
    "companions": [
      {
        "id": 124,
        "role": "COMPANION",
        "first_name": "Jane",
        "last_name": "Doe"
      }
    ],
    "total_count": 2
  },
  "in_house": {          // ❌ SHOWS BEFORE CHECK-IN
    "primary": null,
    "companions": [],
    "total_count": 0
  }
}
```

### Precheckin GET Response (Current)  
```json
{
  "booking_summary": {
    "booking_id": "BK-2025-001",
    "check_in": "2025-12-20",
    "check_out": "2025-12-22",
    "room_type_name": "Deluxe Room",
    "total_guests": 2,
    "hotel_name": "Hotel Example",
    "nights": 2,
    "adults": 2,           // ❌ DUPLICATE 
    "children": 0,         // ❌ DUPLICATE
    "special_requests": ""
  },
  "party": {               // ✅ CANONICAL
    "primary": {...},
    "companions": [...],
    "total_party_size": 2
  },
  "party_complete": false,
  "party_missing_count": 1,
  "precheckin_config": {...},
  "precheckin_field_registry": {...}
}
```

---

## E) Duplication/Contradiction Report

### Critical Conflicts

#### 1. **Multiple Primary Guest Representations**
- **Endpoints Affected**: Staff booking detail, Staff booking list
- **Serializers**: `StaffRoomBookingDetailSerializer`, `StaffRoomBookingListSerializer`
- **Issue**: Exposes `primary_guest` object AND `party.primary` with same data
- **Fix**: Remove `primary_guest`, use only `party.primary`

#### 2. **Duplicate Guest Count Fields**
- **Endpoints Affected**: All booking detail/list endpoints  
- **Serializers**: `RoomBookingDetailSerializer`, `RoomBookingListSerializer`, `StaffRoomBookingDetailSerializer`, `StaffRoomBookingListSerializer`
- **Issue**: Exposes `adults`/`children` at root AND `party.total_count`
- **Fix**: Remove root-level `adults`/`children`, use only `party.total_count`

#### 3. **in_house Data Before Check-in**
- **Endpoints Affected**: Staff booking detail
- **Serializers**: `StaffRoomBookingDetailSerializer`
- **Issue**: Returns `in_house` structure even when `checked_in_at` is null
- **Fix**: Only return `in_house` when `checked_in_at != null`

#### 4. **Inconsistent Party Structures**
- **Endpoints Affected**: Public precheckin vs Staff endpoints  
- **Serializers**: `RoomBookingDetailSerializer.get_party()` vs `BookingPartyGroupedSerializer`
- **Issue**: Different field names (`total_party_size` vs `total_count`)
- **Fix**: Use canonical `BookingPartyGroupedSerializer` everywhere

#### 5. **Redundant Primary Guest Name Fields**
- **Endpoints Affected**: Staff booking list
- **Serializers**: `StaffRoomBookingListSerializer`  
- **Issue**: `primary_guest_name` method field duplicates `party.primary` data
- **Fix**: Remove method field, derive from party if needed

### Minor Issues

#### 6. **Booker vs Primary Guest Confusion**  
- **Issue**: `primary_*` fields at booking level duplicate party data
- **Status**: Acceptable for now - needed for backwards compatibility
- **Future**: Consider deprecating direct booking `primary_*` fields

---

## F) Canonical Contract Proposal

### Staff Booking Detail (Final Shape)
```json
{
  "booking_id": "BK-2025-001",
  "confirmation_number": "CONF-001", 
  "status": "CONFIRMED",
  "check_in": "2025-12-20",
  "check_out": "2025-12-22",
  "nights": 2,
  "total_amount": "150.00",
  "currency": "EUR",
  "booker": {                    // ✅ KEEP - billing info
    "type": "SELF",
    "first_name": "John",
    "last_name": "Doe", 
    "email": "john@example.com"
  },
  "party": {                     // ✅ SINGLE SOURCE OF TRUTH
    "primary": {
      "id": 123,
      "role": "PRIMARY",
      "first_name": "John",
      "last_name": "Doe", 
      "email": "john@example.com"
    },
    "companions": [
      {
        "id": 124,
        "role": "COMPANION", 
        "first_name": "Jane",
        "last_name": "Doe"
      }
    ],
    "total_count": 2
  },
  "party_complete": true,        // ✅ EXPLICIT FLAGS
  "party_missing_count": 0,
  "in_house": {                  // ✅ ONLY IF checked_in_at != null
    "primary": {...},
    "companions": [...],
    "total_count": 2
  },
  "room": {
    "room_number": "101",
    "room_type_name": "Deluxe Room"
  },
  "flags": {
    "can_check_in": false,
    "can_check_out": true
  }
}
```

### Staff Booking List (Minimal Shape)
```json
{
  "booking_id": "BK-2025-001",
  "confirmation_number": "CONF-001",
  "status": "CONFIRMED",
  "check_in": "2025-12-20", 
  "check_out": "2025-12-22",
  "nights": 2,
  "total_amount": "150.00",
  "currency": "EUR",
  "booker_type": "SELF",
  "party_total_count": 2,        // ✅ DERIVED FROM PARTY
  "party_complete": true,
  "party_missing_count": 0,
  "party_status_display": "Complete (2/2 guests)"
}
```

### Precheckin GET Response (Clean Shape)
```json
{
  "booking_summary": {
    "booking_id": "BK-2025-001",
    "check_in": "2025-12-20",
    "check_out": "2025-12-22", 
    "room_type_name": "Deluxe Room",
    "hotel_name": "Hotel Example",
    "nights": 2,
    "special_requests": ""
  },
  "party": {                     // ✅ SINGLE SOURCE OF TRUTH
    "primary": {...},
    "companions": [...],
    "total_count": 2             // ✅ CONSISTENT NAMING
  },
  "party_complete": false,       // ✅ EXPLICIT FLAGS  
  "party_missing_count": 1,
  "precheckin_config": {...},
  "precheckin_field_registry": {...},
  "hotel_style": {
    "preset": 2
  }
}
```

---

## G) Implementation TODO List

### High Priority (Breaking Changes)

1. **Fix StaffRoomBookingDetailSerializer** (`hotel/canonical_serializers.py`)
   - Remove `adults`, `children` from fields list
   - Remove `get_primary_guest()` method  
   - Modify `get_in_house()` to return null when `checked_in_at` is null

2. **Fix RoomBookingDetailSerializer** (`hotel/booking_serializers.py`)  
   - Remove `primary_first_name`, `primary_last_name`, `primary_email`, `primary_phone` from fields
   - Remove `adults`, `children` from fields  
   - Replace custom `get_party()` with canonical `BookingPartyGroupedSerializer`

3. **Fix StaffRoomBookingListSerializer** (`hotel/canonical_serializers.py`)
   - Remove `adults`, `children` from fields
   - Remove `get_primary_guest_name()` method 
   - Keep only `party_total_count`, `party_complete`, `party_missing_count`

### Medium Priority

4. **Fix RoomBookingListSerializer** (`hotel/booking_serializers.py`)
   - Remove `adults`, `children` from fields
   - Modify `get_guest_name()` to derive from party if needed

5. **Standardize Precheckin Responses** (`hotel/public_views.py`)  
   - Use `total_count` instead of `total_party_size` in party structure
   - Remove `adults`, `children` from booking_summary

### Low Priority (Backwards Compatibility)

6. **Consider Deprecating Booking primary_* Fields**
   - Keep for now but add deprecation warnings
   - Plan migration path for v2 API

7. **Add Response Shape Tests**
   - Create comprehensive serializer tests
   - Validate canonical contracts
   - Prevent future regressions

### Validation Rules

8. **Enforce Party Constraints**
   - Exactly one PRIMARY per booking  
   - party.total_count matches staying guest expectation
   - party_complete/party_missing_count accuracy

---

## H) Success Criteria Checklist

- ✅ **"Which serializer produces primary_guest?"**  
  Answer: `StaffRoomBookingDetailSerializer.get_primary_guest()` - **SHOULD BE REMOVED**

- ✅ **"Where does in_house come from?"**  
  Answer: `InHouseGuestsGroupedSerializer` via `StaffRoomBookingDetailSerializer.get_in_house()`

- ✅ **"Which endpoints should only return party?"**  
  Answer: All booking endpoints should use `party` as single source, remove duplicate fields

- ✅ **"Which serializer is used for staff booking detail vs public booking detail?"**  
  Answer: Staff = `StaffRoomBookingDetailSerializer`, Public = `RoomBookingDetailSerializer`

**Status**: Audit complete. Critical duplications identified. Implementation plan established.