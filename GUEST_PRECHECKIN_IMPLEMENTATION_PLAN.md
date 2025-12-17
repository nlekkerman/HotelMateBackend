# Guest Pre-Check-In Implementation Plan

Implementation of a secure guest pre-check-in system allowing guests to complete party names via email links, with mandatory party completion enforced server-side for room assignment.

## Implementation Phases

### Phase A: Fix Existing Serializer Bug (CRITICAL FIRST)
- **Location**: [hotel/booking_serializers.py](hotel/booking_serializers.py)
- **Issue**: Crash after confirm due to serializer using `party_members` instead of `party`
- **Fix**: Replace `booking.party_members` usage with `booking.party.all()`
- **Acceptance**: POST `/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/confirm/` returns JSON 200 without AttributeError

### Phase B: Add Party Completion Computation
- **Location**: [hotel/models.py](hotel/models.py) - Add property to `RoomBooking` model
- **Rule**: 
  - `expected = adults + children`
  - `actual = booking.party.filter(is_staying=True).count()`
  - `party_complete = (actual == expected)`
  - `party_missing_count = max(0, expected - actual)`
- **Expose**: Add `party_complete` and `party_missing_count` to staff detail serializer
- **Acceptance**: Staff detail endpoint includes party completion fields

### Phase C: Create Secure Token Model
- **Location**: [hotel/models.py](hotel/models.py) - Same app as `RoomBooking`
- **Model**: `BookingPrecheckinToken`
- **Token Generation**: `secrets.token_urlsafe(32)` with SHA256 hashing
- **Expiry**: 72 hours
- **Usage**: One-time (valid until successful submit, then `used_at` set)
- **Acceptance**: Migration created and applied

### Phase D: Build Staff Send-Link Endpoint
- **Route**: `POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/send-precheckin-link/`
- **Location**: [room_bookings/staff_urls.py](room_bookings/staff_urls.py), [hotel/staff_views.py](hotel/staff_views.py)
- **Behavior**: Generate token, revoke previous tokens, send email to `primary_email` (fallback `booker_email`)
- **Response**: `{"success": true, "sent_to": "email", "expires_at": "ISO", "booking_id": "BK-..."}`
- **Acceptance**: Endpoint sends email and returns 200, token stored hashed

### Phase E: Implement Public Guest Endpoints
- **Validate**: `GET /api/public/hotel/{hotel_slug}/precheckin/?token=...`
- **Submit**: `POST /api/public/hotel/{hotel_slug}/precheckin/submit/`
- **Location**: [hotel/public_urls.py](hotel/public_urls.py), [hotel/public_views.py](hotel/public_views.py) (keep logic centralized in hotel app)
- **Security**: Token-only access, no booking_id bypass, unified 404 responses for invalid tokens
- **Acceptance**: Both endpoints validate tokens and handle party data securely

### Phase F: Enforce Party Completion Rule
- **Location**: `SafeAssignRoomView` in `/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/safe-assign-room/`
- **Rule**: Block assignment when `party_complete = false`
- **Error**: `{"code":"PARTY_INCOMPLETE","message":"Please provide all staying guest names before room assignment."}`
- **Acceptance**: `safe-assign-room` endpoint fails with `PARTY_INCOMPLETE` when party missing, succeeds when complete

## Detailed Specifications

### 1. Model Fields (Exact)

```python
class BookingPrecheckinToken(models.Model):
    booking = models.ForeignKey(RoomBooking, on_delete=models.CASCADE, related_name='precheckin_tokens')
    token_hash = models.CharField(max_length=64)  # SHA256 hash
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_email = models.EmailField(blank=True)  # Optional audit trail
```

### 2. Public Submit Payload (Exact)

```json
{
  "token": "RAW_TOKEN_STRING",
  "party": [
    {
      "first_name": "John",
      "last_name": "Doe", 
      "email": "john@example.com",
      "phone": "+1234567890",
      "is_staying": true,
      "role": "PRIMARY"
    }
  ],
  "eta": "14:30",
  "special_requests": "Late checkout requested",
  "accept_terms": true
}
```

### 3. Response Shapes (Minimal)

**Validate GET Response:**
```json
{
  "booking_summary": {"booking_id": "BK-2025-0001", "dates": "...", "adults": 2, "children": 0},
  "party": [{"id": 123, "first_name": "John", "role": "PRIMARY"}],
  "party_complete": false,
  "party_missing_count": 1
}
```

**Submit POST Response:**
```json
{
  "success": true,
  "party": [{"id": 123, "first_name": "John", "role": "PRIMARY"}],
  "party_complete": true
}
```

### 4. Error Codes (Standardized)

**Token Failures (Security):**
All invalid token states return:
- **HTTP 404**
- **JSON**: `{"message":"Link invalid or expired."}`
- **Internal logging**: `TOKEN_INVALID`, `TOKEN_EXPIRED`, `TOKEN_USED` (for debugging only)

**Other Errors:**
- `PARTY_INCOMPLETE` - Staying count doesn't match adults+children
- `VALIDATION_ERROR` - Field validation failures

### 5. Token Lifecycle Rule

Tokens are valid from creation until successful party submission. Once a guest successfully submits complete party information, the token's `used_at` field is set to the current timestamp and the token becomes permanently invalid for further use. This ensures each pre-check-in link can only be used once to complete the party information, preventing replay attacks and accidental duplicate submissions.

### 6. Security Guardrails

All token hash comparisons must use constant-time comparison functions to prevent timing attacks. Implement basic rate limiting on both validate and submit endpoints (e.g., 10 requests per minute per IP) to prevent enumeration attacks. The system must never reveal booking existence or details without a valid token - invalid tokens should return generic "not found" errors rather than distinguishing between non-existent bookings and invalid tokens.

## Implementation Notes

- **Email Target**: Send to `primary_email`, fallback to `booker_email` if primary not available
- **Party Validation**: Enforce total staying guest count equals `adults + children` without requiring exact adult vs child role distinction  
- **Token Storage**: Store SHA256 hash only, never raw token
- **Concurrent Access**: Handle multiple token generation requests gracefully by revoking previous active tokens

## Architecture Clarification

**room_bookings is not a Django app** - it's a service layer containing business logic, constants, and URL routing. All models and migrations live in the **hotel app**.

- **Models/Migrations**: `hotel/models.py` (where `RoomBooking` already exists)
- **Staff Routes**: `room_bookings/staff_urls.py` (routing layer pointing to `hotel.staff_views`)  
- **Enforcement**: Party completion enforced inside `safe-assign-room` flow using `RoomAssignmentService`

## Applied Tweaks

**TWEAK 1 — Hotel App Structure:**
- Public endpoints live in `hotel/public_urls.py` and `hotel/public_views.py` 
- Keep all booking logic centralized in hotel app
- Include hotel public URLs in project-level `public_urls.py` using existing convention

**TWEAK 2 — Token Security Response:**
- All invalid/expired/used/revoked tokens return HTTP 404
- Unified response: `{"message":"Link invalid or expired."}`
- Internal reason codes logged for debugging only
- Never leak booking existence

**TWEAK 3 — Minimum Enforcement Scope:**
- Enforce party completion on canonical `safe-assign-room` endpoint (minimum requirement)
- Additional assignment paths may also enforce but `SafeAssignRoomView` is mandatory
- Return `{"code":"PARTY_INCOMPLETE","message":"Please provide all staying guest names before room assignment."}`