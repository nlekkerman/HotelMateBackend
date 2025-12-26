# Guest Token + Booking-Scoped Realtime Implementation Plan

## Overview

Implement secure guest-token authentication for booking-specific realtime updates using existing NotificationManager patterns, while maintaining staff channel isolation and preserving all payment/booking logic.

## Goals

- Guests can see live booking state changes (accepted / payment required / confirmed / cancelled) using a guest token
- Guests cannot access staff channels  
- No changes to Stripe logic — realtime only mirrors state transitions
- All events use canonical envelope `{category,type,payload,meta}` and emit after commit via `transaction.on_commit()`

## A) Payment Stage Classification

### Utility Function: `payment_stage(booking)`

**Location**: `hotel/utils.py` or `hotel/services.py`

**Purpose**: Classify payment stage from existing booking fields to determine correct Stripe actions during cancellation.

**Return Values**:
- `NONE` - No session/intent exists
- `SESSION_CREATED` - Checkout session exists  
- `AUTHORIZED` - Payment intent authorized but not captured
- `CAPTURED` - `paid_at` exists / payment status captured

**Exact Field Mappings** (prevents interpretation ambiguity):
- `NONE`: `payment_provider_reference` is empty AND `paid_at` is null
- `SESSION_CREATED`: `payment_provider_reference` startswith "cs_" (Stripe Checkout Session ID)
- `AUTHORIZED`: `payment_provider_reference` startswith "pi_" AND `paid_at` is null (only if PI is stored)
- `CAPTURED`: `paid_at` is not null (and optionally payment status == "CAPTURED")

**Usage**: Stripe actions depend on `payment_stage`, not staff approval status.

## B) GuestBookingToken Model

### Model Definition

**Location**: `hotel/models.py`

**Fields**:
- `token` - Secure random string, unique, indexed
- `booking` - FK to RoomBooking, indexed  
- `hotel` - FK to Hotel (optional; can be derived via `booking.hotel`)
- `created_at` - Auto timestamp
- `expires_at` - Nullable; recommended: `check_out + 30 days`
- `revoked_at` - Nullable for token revocation
- `last_used_at` - Optional for debugging/security
- `purpose` - Enum field (optional): `STATUS`, `PRECHECKIN` for future reuse

**Token Format & Security**:
- **Length**: 32+ bytes random (base64url/hex)
- **Storage**: Store hashed using constant-time comparison (MANDATORY for security)

**Constraints**:
- `UniqueConstraint(booking, revoked_at IS NULL)` - One active token per booking
- Token uniqueness across system

**Token Lifecycle Policy**:
- **Rotate on resend**: Optional (can generate new token if guest requests new link)
- **Revoke on cancellation**: Recommended (prevent access to cancelled booking updates)
- **New link requests**: Generate new token, revoke previous (enforce one active token rule)

### Token Generation Strategy

**When**: On booking creation in `BookingCreateAPIView`
**Expiry**: `check_out + 30 days` (best UX; avoids token expiry during stay)
**Storage**: Store expiry in DB; don't hardcode

## C) Guest Booking Realtime Channel

### Channel Naming Convention

**Format**: `private-guest-booking.{booking_id}`

**Rationale**: 
- `booking_id` is stable and used across the system
- Private channel requires authentication
- Scoped to specific booking for security

## D) Pusher Auth Endpoint Enhancement

### Dual-Mode Authentication

**Location**: `notifications/views.py` - Extend existing `/pusher/auth`

#### Mode 1: Staff Auth (Existing)
- Validate staff JWT/session
- Authorize channels:
  - `{hotelSlug}.room-bookings`
  - `{hotelSlug}.rooms`
  - Any other existing staff channels

#### Mode 2: Guest Token Auth (NEW)
- Guest provides `guest_token` (header or POST field)
- Authorize ONLY if:
  - Token exists, not expired, not revoked
  - Requested channel matches: `private-guest-booking.{token.booking.booking_id}`
  - Deny everything else

### Hard Deny Rules for Guest Tokens
- **CRITICAL**: Guest token auth must hard-reject any `{hotelSlug}.` channel, even if the token is valid
- Any channel starting with `{hotelSlug}.` must be rejected
- Any other private channel not matching booking must be rejected  
- Use standard Pusher private auth response

**Enforcement**: Do NOT subscribe guest to hotel channels under any circumstances

## E) NotificationManager: Guest-Scoped Methods

### New Methods

**Location**: `notifications/notification_manager.py`

#### Guest Event Methods
- `realtime_guest_booking_payment_required(booking, guest_token_or_scope)`
- `realtime_guest_booking_confirmed(booking, guest_token_or_scope)`  
- `realtime_guest_booking_cancelled(booking, reason, guest_token_or_scope)`

#### Implementation Requirements
- Use existing `_create_normalized_event()`
- Set `meta.scope = {type: "guest_booking", booking_id: "BK-..."}`
- Emit to: `private-guest-booking.{booking.booking_id}`
- Wrap in `transaction.on_commit()`

#### Canonical Meta.Scope Shape
**Guest Events**: `{type: "guest_booking", booking_id: "BK-..."}`
**Staff Events**: `{type: "hotel_staff", slug: "hotel-killarney"}` (maintain consistency)

### Guest-Safe Payload Design

**Include**:
- `booking_id`
- `status` (canonical uppercase)
- Relevant timestamps: `created_at`/`confirmed_at`/`cancelled_at`
- Payment fields: `payment_required: true`, `payment_deadline` (optional)
- Safe hotel info: `hotel_name`, `hotel_phone`

**Exclude**:
- Staff notes
- Internal IDs  
- Guest PII beyond what guest already has

**Deterministic Payload Per Event**:
- **`booking_payment_required`**: `booking_id`, `status`, `payment_required=true`
- **`booking_confirmed`**: `booking_id`, `status`, `confirmed_at`
- **`booking_cancelled`**: `booking_id`, `status`, `cancelled_at`, `cancellation_reason`

## F) Event Inventory & Trigger Points

### Guest Events (Initial Implementation)

1. **`booking_created`** (Optional - guest page often fetches initial state)
2. **`booking_payment_required`** - Hotel accepted and payment needed
3. **`booking_confirmed`** - Paid + confirmed OR confirmed by pay-at-hotel flow  
4. **`booking_cancelled`** - Any stage cancellation

### Trigger Point Integration

#### Booking Creation
**Location**: `BookingCreateAPIView` in `hotel/views.py`
- Create `GuestBookingToken`
- Return token in response  
- Optionally emit `booking_created` to guest channel

#### Staff Accept Flow  
**Location**: Staff booking acceptance logic
- If payment needed → emit `booking_payment_required`
- If pay-at-hotel → emit `booking_confirmed`

#### Stripe Webhook
**Location**: Payment webhook handlers in `hotel/views.py`
- When capture succeeds → emit `booking_confirmed`

#### Cancellation
**Location**: Cancel endpoints
- After cancellation commit → emit `booking_cancelled`

## G) Smart Cancellation Service

### Service Function: `cancel_booking(booking, reason, actor)`

**Purpose**: Payment-stage-aware cancellation with proper Stripe handling

#### Logic by Payment Stage
- **`NONE`**: Cancel DB only
- **`SESSION_CREATED`/`AUTHORIZED`**: Cancel DB + void/expire/cancel PI/session  
- **`CAPTURED`**: Cancel DB + refund flow (full/partial based on policy)

#### Event Emission
- Staff: `{hotelSlug}.room-bookings` → `booking_cancelled`
- Guest: `private-guest-booking.{booking_id}` → `booking_cancelled`

**Rule**: Never decide Stripe action using approval status alone

## H) Testing Requirements

### Critical Test Cases

1. **Auth Restrictions**:
   - Guest token cannot auth staff channels
   - Guest token can auth only its booking channel
   - Expired/revoked token denies auth

2. **Event Schema Validation**:
   - `{category,type,payload,meta}` structure
   - `meta.event_id` exists
   - Events emit only after commit (test via mocking `transaction.on_commit`)

3. **Business Logic**:
   - `payment_stage` classification accuracy
   - Token generation and expiry logic
   - Cancellation service Stripe decision logic

## I) Operations & Maintenance

### Management Command

**Command**: `create_guest_tokens_for_existing_bookings --since YYYY-MM-DD`

**Purpose**: Generate guest tokens for existing bookings

**Features**:
- Date filtering for selective backfill
- Option to rotate/revoke tokens for cancelled bookings
- Bulk processing with progress indication

## Implementation Order

### Phase 1: Foundation
1. Create `payment_stage()` utility function
2. Add `GuestBookingToken` model
3. Generate and apply database migration

### Phase 2: Authentication  
4. Extend Pusher auth endpoint for dual-mode
5. Add comprehensive auth tests

### Phase 3: Realtime Events
6. Extend NotificationManager with guest-scoped methods
7. Integrate token auto-generation on booking creation
8. Add booking state event triggers

### Phase 4: Business Logic
9. Implement smart cancellation service
10. Add comprehensive business logic tests

### Phase 5: Operations
11. Create backfill management command
12. Documentation and deployment

## Key Architectural Principles

- **Follow Existing Patterns**: Use UUID tokens like `GuestChatSession`
- **Leverage NotificationManager**: Use existing event schema and channel utilities
- **Maintain Hotel Scoping**: All channels remain hotel-scoped for security
- **Transaction Safety**: All realtime events wrapped in `transaction.on_commit()`
- **Preserve Payment Logic**: No changes to existing Stripe authorization/capture flow
- **Guest-Staff Isolation**: Strict channel access controls prevent guest access to staff data

## Reconnect Recovery

**WebSocket Reconnection**: If websocket reconnects, guest page may refetch booking by token once (safe), dedupe via `meta.event_id`.

## Success Criteria

- [x] Guests receive realtime booking status updates via secure tokens
- [x] Guest tokens cannot access any staff channels or data  
- [x] All existing payment flows work unchanged
- [x] Events follow canonical schema and emit safely after DB commits
- [x] Cancellation logic properly handles all payment stages
- [x] Comprehensive test coverage prevents regressions
- [x] Backfill capability for existing bookings
