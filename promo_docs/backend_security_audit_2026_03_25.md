# Backend Security Audit — 2026-03-25

Focused audit of current backend auth, scoping, and endpoint security.  
No refactoring proposed. Read-only analysis with actionable findings.

---

## ✅ Verified Correct

- **GuestBookingToken model** is well-designed: SHA-256 hashed storage, one-active-per-booking constraint, expiration, scopes, revocation with reason tracking.
- **`generate_token()`** atomically revokes previous active token before creating a new one — prevents token accumulation.
- **`resolve_guest_token()` in `common/guest_auth.py`** properly validates: hash lookup → expiration → hotel slug match (anti-enumeration) → booking status → scope check → optional in-house check → touches `last_used_at`.
- **`resolve_guest_chat_context()` in `bookings/services.py`** mirrors the same validation chain with structured exception classes (`InvalidTokenError`, `NotInHouseError`, `MissingScopeError`).
- **`TokenAuthenticationMixin`** centralizes token extraction from `Bearer` / `GuestToken` headers and `?token=` query param.
- **`PublicRoomBookingDetailView`** requires email match against `booking.primary_email` — hardened against enumeration.
- **Room service `OrderViewSet` / `BreakfastOrderViewSet`** guest actions (`create`, `room_order_history`) use `AllowAny` externally but validate `GuestBookingToken` with `required_scopes=['ROOM_SERVICE']` internally.
- **`save_guest_fcm_token` in `room_services/views.py`** validates guest token with `required_scopes=['ROOM_SERVICE']` and `require_checked_in=True`, plus verifies URL `room_number` matches token-derived room.
- **Canonical guest chat views** (`GuestChatContextView`, `GuestChatSendMessageView`, `GuestChatPusherAuthView`) all use `TokenAuthenticationMixin` → `resolve_guest_chat_context()` chain consistently.
- **Token revocation on checkout** (`room_bookings/services/checkout.py`) bulk-revokes all active tokens for the booking.
- **Staff endpoints** correctly use `[IsAuthenticated, IsStaffMember, IsSameHotel]` permission stack across room service staff actions, maintenance, housekeeping, and attendance.
- **`HotelScopedQuerysetMixin` / `HotelScopedViewSetMixin`** in `common/mixins.py` provide centralized tenant scoping via `request.user.staff_profile.hotel`.
- **Global DRF default** is `IsAuthenticated` with `TokenAuthentication` — views without explicit `permission_classes` require staff auth.
- **Rate limiting** applied to public endpoints via `PublicBurstThrottle` / `PublicSustainedThrottle` and guest endpoints via `GuestTokenBurstThrottle` / `GuestTokenSustainedThrottle`.
- **Stripe webhook** correctly verifies Stripe signature before processing.
- **PIN-based auth flows removed from active auth paths** — no PIN gating on any protected endpoint.

---

## ⚠️ Remaining Risks

### HIGH — Unauthenticated Mutation Endpoints

| Endpoint | File | Issue |
|----------|------|-------|
| `chat/save_fcm_token` | `chat/views.py:1555` | **`AllowAny`, no guest token validation.** Accepts `room_number` + `fcm_token` from body and writes to `room.guest_fcm_token`. Any anonymous user can overwrite a guest's FCM token, hijacking push notifications. Compare with the properly secured `room_services/save_guest_fcm_token` which validates guest token. |
| `mark_bookings_seen` | `bookings/views.py:489` | **`AllowAny`, mutates data.** Any anonymous user can mark all unseen dinner bookings as seen for any hotel slug. Should require staff auth. |
| `GuestDinnerBookingView.post` | `bookings/views.py:68` | **`AllowAny` on POST.** Creates dinner bookings with no guest or staff authentication. GET also lists all dinner bookings for any hotel. |

### HIGH — Cross-Tenant Data Access (Authenticated but Unscoped)

| Endpoint | File | Issue |
|----------|------|-------|
| `BookingViewSet` | `bookings/views.py:40` | No explicit `permission_classes`, no hotel scoping. `queryset = Booking.objects.all()`. Any authenticated staff from any hotel can list/modify all bookings across all hotels. |
| `AssignGuestToTableAPIView` | `bookings/views.py:510` | `IsAuthenticated` but `booking_id` and `table_id` from request body with `get_object_or_404(Booking, pk=booking_id)` — no hotel scoping. Staff from Hotel A can assign bookings from Hotel B. |
| `UnseatBookingAPIView` | `bookings/views.py:548` | No explicit `permission_classes` (falls to global `IsAuthenticated`). `booking_id` from body with `Booking.objects.get(id=booking_id)` — no hotel scoping. |

### MEDIUM — Weakly Scoped Staff Endpoints

| Endpoint | File | Issue |
|----------|------|-------|
| `BookingCategoryViewSet` | `bookings/views.py:47` | Hotel filter is optional via `?hotel_slug=`. Without it, returns all hotels' categories. Should enforce hotel from `request.user.staff_profile.hotel`. |
| `DiningTableViewSet` | `bookings/views.py:362` | Falls back to `DiningTable.objects.all()` if no hotel/restaurant slug provided. |
| `CreatePaymentSessionView` | `hotel/payment_views.py:176` | `AllowAny`, accepts `booking_id` from URL with no requester verification. Anyone who guesses a booking_id UUID can initiate a payment session. |
| `HotelBySlugView` | `hotel/base_views.py:48` | `AllowAny`, returns full `HotelSerializer` which may include internal fields not intended for public consumption. |

### MEDIUM — Inconsistent Guest Token Validation

| Pattern | Location | Issue |
|---------|----------|-------|
| Two parallel resolver functions | `common/guest_auth.py:resolve_guest_token()` vs `bookings/services.py:resolve_guest_chat_context()` | Both implement GuestBookingToken validation with slightly different signatures, exception types, and return shapes. Canonical chat views use `bookings/services.py`; room service uses `common/guest_auth.py`. Not a bug today, but divergence risk. |
| Legacy chat FBVs in `chat/views.py` | `guest_chat_context` (L340), `guest_send_message` (L420) | Use `request.GET.get('token')` + `bookings.services.resolve_guest_chat_context()` directly, bypassing `TokenAuthenticationMixin`. Functionally OK but inconsistent with canonical views. |
| `PusherAuthView` in `notifications/views.py` | L17 | Manual token extraction from 3 sources (query, body, header) with its own parsing logic, not using `TokenAuthenticationMixin`. |

### LOW — PIN Field Remnants

| Location | Detail |
|----------|--------|
| `guests/models.py` | `id_pin` field still on `Guest` model |
| `guests/serializers.py`, `hotel/canonical_serializers.py` | `id_pin` exposed in API responses |
| `notifications/notification_manager.py` (L1605, L1825) | `id_pin` included in notification payloads |
| `hotel/models.py` | `requires_room_pin`, `room_pin_length` config fields still on `Hotel` model |
| `hotel/staff_views.py:305` | `chat_pin` QR code generation still handled |

These aren't security exploits (PIN doesn't gate access) but they leak defunct identifiers in API responses.

### LOW — Entertainment Endpoints

| Endpoint | File | Issue |
|----------|------|-------|
| `MemoryGameSessionViewSet` | `entertainment/views.py:179` | `AllowAny` with create/update. No auth or hotel scoping on mutations. |
| `GameHighScoreViewSet` | `entertainment/views.py:51` | `AllowAny` create with no validation. |
| `QuizSessionViewSet` | `entertainment/views.py:880` | `AllowAny` create/update. |

These are designed for room tablets but have no token verification to prevent abuse.

---

## 🎯 Next Backend Tasks (MAX 5)

1. **Secure `chat/save_fcm_token`** — Add `GuestBookingToken` validation matching the pattern in `room_services/save_guest_fcm_token`. This is the highest-impact fix: unauthenticated FCM token overwrite.

2. **Add hotel scoping to `bookings` app staff endpoints** — `BookingViewSet`, `AssignGuestToTableAPIView`, `UnseatBookingAPIView` need `request.user.staff_profile.hotel` filtering. Use existing `HotelScopedViewSetMixin` or add `hotel=hotel` to queryset lookups.

3. **Require staff auth on `mark_bookings_seen`** — Change from `AllowAny` to `[IsAuthenticated, IsStaffMember, IsSameHotel]` and scope the update query to `hotel=request.user.staff_profile.hotel`.

4. **Add guest token validation to `GuestDinnerBookingView.post`** — Either require `GuestBookingToken` (like room service) or staff auth for creating dinner bookings. GET should also be scoped.

5. **Remove `id_pin` from serializer `fields` and notification payloads** — Stop exposing the defunct PIN in API responses and push notification data. Model field can stay for migration compatibility.
