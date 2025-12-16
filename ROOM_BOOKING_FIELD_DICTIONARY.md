# RoomBooking Field Dictionary

**Status**: Source of Truth  
**Last Updated**: December 16, 2025  
**Version**: 1.0

## Primary Identifiers

### `booking_id`
**Type**: `string`  
**Format**: `BK-YYYY-####` (e.g., `BK-2025-0001`)  
**Purpose**: System-generated unique identifier for internal use  
**Mutability**: Immutable after creation  
**Visibility**:
- ✅ Public API
- ✅ Staff API  
- ✅ Realtime payloads
- ✅ Database primary business key

**Usage**: Use as primary key for frontend stores, API calls, and event tracking.

### `confirmation_number`
**Type**: `string`  
**Format**: `{hotel_code}-YYYY-####` (e.g., `HTL-2025-0001`)  
**Purpose**: Guest-facing reference number for customer service  
**Mutability**: Immutable after creation  
**Visibility**:
- ✅ Public API
- ✅ Staff API
- ✅ Realtime payloads
- ✅ Guest communications

**Usage**: Display to guests, use for guest lookup, include in confirmations.

## Status and Lifecycle

### `status`
**Type**: `string (enum)`  
**Values**: 
- `PENDING_PAYMENT` - Booking created, payment required
- `CONFIRMED` - Payment received, booking active
- `CANCELLED` - Booking cancelled  
- `COMPLETED` - Guest checked out, booking finished
- `NO_SHOW` - Guest failed to arrive

**Mutability**: Changes through lifecycle progression  
**Visibility**:
- ✅ Public API (limited context)
- ✅ Staff API (full context)
- ✅ Realtime payloads

**Business Rules**:
- Only `PENDING_PAYMENT` → `CONFIRMED` via payment
- Only `CONFIRMED` → `CHECKED_IN` via staff action  
- Only `CHECKED_IN` → `COMPLETED` via checkout
- `CANCELLED` and `NO_SHOW` are terminal states

### `checked_in_at`
**Type**: `datetime (ISO 8601)`  
**Example**: `2025-01-15T14:30:00Z`  
**Purpose**: Timestamp when guest checked into room  
**Mutability**: Set once during check-in process  
**Visibility**:
- ❌ Public API
- ✅ Staff API
- ✅ Realtime payloads (staff events)

**Business Rules**:
- Only set when booking transitions to checked-in state
- Requires `assigned_room` to be set first
- Cannot be modified after checkout

### `checked_out_at`  
**Type**: `datetime (ISO 8601)`  
**Example**: `2025-01-17T11:00:00Z`  
**Purpose**: Timestamp when guest checked out of room  
**Mutability**: Set once during checkout process  
**Visibility**:
- ❌ Public API
- ✅ Staff API
- ✅ Realtime payloads (staff events)

**Business Rules**:
- Only set during checkout process
- Automatically sets `status` to `COMPLETED`
- Immutable after being set

## Dates and Duration

### `check_in`
**Type**: `date (YYYY-MM-DD)`  
**Example**: `2025-01-15`  
**Purpose**: Planned arrival date (not actual check-in time)  
**Mutability**: Immutable after payment  
**Visibility**:
- ✅ Public API
- ✅ Staff API
- ✅ Realtime payloads

**Business Rules**:
- Must be present or future date at booking creation
- Cannot be after `check_out` date
- Used for room availability calculations

### `check_out`
**Type**: `date (YYYY-MM-DD)`  
**Example**: `2025-01-17`  
**Purpose**: Planned departure date  
**Mutability**: Immutable after payment  
**Visibility**:
- ✅ Public API
- ✅ Staff API
- ✅ Realtime payloads

**Business Rules**:  
- Must be after `check_in` date
- Used for room availability calculations
- Determines booking duration

### `nights`
**Type**: `integer (computed)`  
**Example**: `2`  
**Purpose**: Number of nights (check_out - check_in)  
**Mutability**: Computed field, changes with date changes  
**Visibility**:
- ✅ Public API
- ✅ Staff API
- ✅ Realtime payloads

**Computation**: `(check_out - check_in).days`

## Room Information

### `room_type`
**Type**: `object (RoomType)`  
**Structure**:
```json
{
  "id": 123,
  "name": "Standard Double",
  "description": "Comfortable room with city view", 
  "max_occupancy": 2,
  "amenities": ["WiFi", "AC", "TV"]
}
```
**Purpose**: Category of room booked (not specific room)  
**Mutability**: Immutable after booking creation  
**Visibility**:
- ✅ Public API (name only)
- ✅ Staff API (full object)
- ✅ Realtime payloads (full object)

**Usage**: Room category selection, availability checking, pricing basis.

### `assigned_room`
**Type**: `object (Room) | null`  
**Structure**:
```json
{
  "id": 456,
  "room_number": 201,
  "floor": 2,
  "room_type": { "name": "Standard Double" }
}
```
**Purpose**: Specific room assigned for stay  
**Mutability**: Set by staff during assignment process  
**Visibility**:
- ❌ Public API (security - no room numbers exposed)
- ✅ Staff API (full object)
- ✅ Realtime payloads (full object)

**Business Rules**:
- `null` until staff assigns specific room
- Must match booked `room_type` category
- Required before check-in process

## Guest Information

### Booker Fields (`booker_*`)
**Fields**: `booker_first_name`, `booker_last_name`, `booker_email`, `booker_phone`, `booker_company`  
**Purpose**: Person/entity making the payment  
**Mutability**: Modifiable by staff, limited guest updates  
**Visibility**:
- ❌ Public API (privacy - only when booker_type != SELF)
- ✅ Staff API (always visible)
- ✅ Realtime payloads (full details)

**Business Rules**:
- Required when `booker_type` != `SELF`
- Can be empty when `booker_type` == `SELF`  
- Used for payment processing and invoicing

### Primary Guest Fields (`primary_*`)
**Fields**: `primary_first_name`, `primary_last_name`, `primary_email`, `primary_phone`  
**Purpose**: Person who will stay in the room  
**Mutability**: Required at creation, modifiable by staff  
**Visibility**:
- ✅ Public API (limited - name only)
- ✅ Staff API (full details)
- ✅ Realtime payloads (full details)

**Business Rules**:
- Always required (person staying in room)
- Automatically syncs with PRIMARY party member
- Used for guest communications and check-in

### `booker_type`
**Type**: `string (enum)`  
**Values**:
- `SELF` - Booker is staying in room
- `THIRD_PARTY` - Third-party booking (gift, agent)
- `COMPANY` - Corporate booking

**Purpose**: Relationship between payer and guest  
**Mutability**: Set at creation, rarely changed  
**Visibility**:
- ❌ Public API  
- ✅ Staff API
- ✅ Realtime payloads

## Occupancy

### `adults`
**Type**: `integer`  
**Range**: `1` to room type max occupancy  
**Purpose**: Number of adult guests  
**Mutability**: Limited modification (staff only)  
**Visibility**:
- ✅ Public API
- ✅ Staff API
- ✅ Realtime payloads

### `children`  
**Type**: `integer`  
**Range**: `0` to (room type max occupancy - adults)  
**Purpose**: Number of child guests  
**Mutability**: Limited modification (staff only)  
**Visibility**:
- ✅ Public API
- ✅ Staff API  
- ✅ Realtime payloads

**Business Rules**:
- `adults + children` cannot exceed room type max occupancy
- Used for pricing calculations and room assignment

## Pricing

### `total_amount`
**Type**: `decimal (2 decimal places)`  
**Example**: `254.00`  
**Purpose**: Final amount charged to guest  
**Mutability**: Immutable after payment  
**Visibility**:
- ✅ Public API (own bookings only)
- ✅ Staff API (full access)
- ✅ Realtime payloads (staff events)

### `currency`
**Type**: `string (ISO 4217)`  
**Example**: `EUR`, `USD`, `GBP`  
**Purpose**: Currency code for pricing  
**Mutability**: Set at creation, immutable  
**Visibility**:
- ✅ Public API
- ✅ Staff API
- ✅ Realtime payloads

## Payment Information

### `payment_reference`
**Type**: `string`  
**Example**: `pi_1234567890abcdef`  
**Purpose**: Payment processor transaction ID  
**Mutability**: Set by payment processor  
**Visibility**:
- ❌ Public API (security)
- ✅ Staff API (financial access required)
- ✅ Realtime payloads (staff events only)

### `payment_provider`
**Type**: `string`  
**Example**: `stripe`, `paypal`, `square`  
**Purpose**: Which payment processor was used  
**Mutability**: Set by payment processor  
**Visibility**:
- ❌ Public API
- ✅ Staff API (financial access required)
- ✅ Realtime payloads (staff events only)

### `paid_at`
**Type**: `datetime (ISO 8601)`  
**Example**: `2025-12-16T16:00:00Z`  
**Purpose**: When payment was successfully processed  
**Mutability**: Set by payment processor  
**Visibility**:
- ❌ Public API
- ✅ Staff API (financial access required)
- ✅ Realtime payloads (staff events only)

## Party Management

### `party` (Computed Field)
**Type**: `object`  
**Structure**:
```json
{
  "primary": {
    "id": 789,
    "first_name": "John",
    "last_name": "Doe", 
    "email": "john@example.com",
    "role": "PRIMARY"
  },
  "companions": [
    {
      "id": 790,
      "first_name": "Jane", 
      "last_name": "Doe",
      "email": "jane@example.com",
      "role": "COMPANION"
    }
  ]
}
```
**Purpose**: All guests who will stay in the room  
**Mutability**: Staff can add/remove companions, update info  
**Visibility**:
- ❌ Public API (privacy)
- ✅ Staff API (full party details)
- ✅ Realtime payloads (party update events)

**Business Rules**:
- Always exactly 1 PRIMARY member
- PRIMARY member syncs with booking `primary_*` fields  
- Companions can be added/removed freely
- All party members have `is_staying: true`

## Audit and Notes

### `created_at`
**Type**: `datetime (ISO 8601)`  
**Example**: `2025-12-16T15:30:00Z`  
**Purpose**: When booking was first created  
**Mutability**: Immutable  
**Visibility**:
- ❌ Public API  
- ✅ Staff API
- ✅ Realtime payloads

### `updated_at`
**Type**: `datetime (ISO 8601)`  
**Example**: `2025-12-16T16:45:00Z`  
**Purpose**: When booking was last modified  
**Mutability**: Auto-updated on changes  
**Visibility**:
- ❌ Public API
- ✅ Staff API
- ✅ Realtime payloads

### `internal_notes`
**Type**: `text`  
**Purpose**: Staff annotations not visible to guest  
**Mutability**: Staff can add/edit freely  
**Visibility**:
- ❌ Public API (never exposed to guests)
- ✅ Staff API (full access)
- ✅ Realtime payloads (staff events only)

### `special_requests`
**Type**: `text`  
**Purpose**: Guest requests and preferences  
**Mutability**: Set by guest, viewable by staff  
**Visibility**:
- ✅ Public API (own booking only)
- ✅ Staff API (full access)
- ✅ Realtime payloads

## Computed Display Fields

### `primary_guest_name`
**Type**: `string (computed)`  
**Format**: `"John Doe"`  
**Computation**: `f"{primary_first_name} {primary_last_name}"`  
**Purpose**: Display-ready guest name  
**Visibility**: All APIs and payloads where guest name is shown

### `booker_name` 
**Type**: `string (computed)`  
**Format**: `"Jane Smith"` or `""` (empty if same as primary)  
**Computation**: `f"{booker_first_name} {booker_last_name}"` if present  
**Purpose**: Display booker name when different from guest  
**Visibility**: Staff API and realtime payloads only

## Field Validation Rules

### Required at Creation
- `primary_first_name`, `primary_last_name` (always)
- `check_in`, `check_out`, `room_type` (always)  
- `adults` (minimum 1)
- `total_amount`, `currency` (from quote)

### Optional at Creation  
- `booker_*` fields (depends on `booker_type`)
- `children` (defaults to 0)
- `special_requests` (guest input)
- `promo_code` (if applicable)

### Staff-Only Fields
- `internal_notes`
- `assigned_room` 
- `checked_in_at`, `checked_out_at`
- Payment details (`payment_reference`, etc.)

### System-Generated Fields
- `booking_id`, `confirmation_number`
- `created_at`, `updated_at`
- Computed fields (`nights`, display names)

## API Response Visibility Matrix

| Field | Public API | Staff API | Realtime |
|-------|------------|-----------|----------|  
| `booking_id` | ✅ | ✅ | ✅ |
| `confirmation_number` | ✅ | ✅ | ✅ |
| `status` | ✅ | ✅ | ✅ |
| `primary_first_name` | ✅ | ✅ | ✅ |
| `primary_last_name` | ✅ | ✅ | ✅ |
| `primary_email` | ❌ | ✅ | ✅ |
| `booker_*` fields | ❌ | ✅ | ✅ |
| `check_in`, `check_out` | ✅ | ✅ | ✅ |
| `room_type` | ✅ (name) | ✅ (full) | ✅ (full) |
| `assigned_room` | ❌ | ✅ | ✅ |
| `total_amount` | ✅ | ✅ | ✅ |
| `payment_*` fields | ❌ | ✅* | ✅* |
| `internal_notes` | ❌ | ✅ | ✅ |
| `party` details | ❌ | ✅ | ✅ |
| `checked_*_at` | ❌ | ✅ | ✅ |

*Staff with financial permissions only