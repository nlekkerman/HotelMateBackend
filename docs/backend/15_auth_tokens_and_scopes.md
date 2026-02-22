# Auth, Tokens & Scopes

> Documents all authentication mechanisms, permission classes, token types, and authorization flows.

---

## 1. Global Authentication Defaults

**Source:** `HotelMateBackend/settings.py`

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}
```

Every endpoint defaults to **DRF TokenAuthentication** + **IsAuthenticated** unless explicitly overridden.

---

## 2. Authentication Mechanisms

### 2.1 Staff Authentication — DRF Token

| Aspect | Detail |
|--------|--------|
| **Type** | `rest_framework.authtoken.Token` (one per user, no expiry) |
| **Header** | `Authorization: Token <key>` |
| **Issued at** | Login via `StaffLoginView` (`staff/views.py`) |
| **Auto-created** | Signal in `staff/signals.py` creates token on `User` post_save |
| **Login response** | Token + staff profile + canonical permissions (`nav_permissions` list) |

### 2.2 Guest Token Authentication — Custom

| Aspect | Detail |
|--------|--------|
| **Model** | `hotel.GuestBookingToken` (`hotel/models.py`) |
| **Storage** | SHA-256 hash in DB; raw token sent to guest (never stored) |
| **Header** | `Authorization: Bearer <token>` or `Authorization: GuestToken <token>` |
| **Fallback** | `?token=<token>` query parameter |
| **Extraction** | `GuestTokenMixin` in `hotel/guest_portal_views.py` (not a DRF `BaseAuthentication`) |
| **Validation** | Hash lookup → status check (ACTIVE) → expiry check → optional hotel match → update `last_used_at` |

**Not a DRF auth backend** — views manually extract and validate tokens in their method bodies. These views set `permission_classes = [AllowAny]` and handle auth internally.

### 2.3 Subdomain Authentication Backend — Custom Django Auth Backend

| Aspect | Detail |
|--------|--------|
| **Class** | `SubdomainAuthBackend` (`hotel/authentication.py`) |
| **Type** | Django `ModelBackend` subclass |
| **Behavior** | Reads `request.hotel` (set by middleware). Superusers bypass hotel check. Normal users must have `Staff.hotel == request.hotel` |
| **⚠️ Status** | Defined but **NOT registered** in `settings.AUTHENTICATION_BACKENDS` — only `ModelBackend` is active |

---

## 3. Custom Permission Classes

### Staff Permissions

| Class | File | Logic |
|-------|------|-------|
| **`IsStaffOfHotel`** | `hotel/permissions.py` | User authenticated + has `Staff` profile + `is_active=True` + staff's `hotel.slug` matches URL `hotel_slug` |
| **`HasNavPermission`** | `staff/permissions.py` | Superuser bypass → else checks if `nav_slug` (from view attribute) exists in user's canonical `nav_permissions` (resolved via `get_canonical_permissions()`) |
| **`IsStaffAdmin`** | `staff/permissions.py` | User authenticated + `access_level == 'staff_admin'` or `'super_staff_admin'` |

### Housekeeping Permissions

| Class | File | Logic |
|-------|------|-------|
| **`IsStaffOfHotel`** | `housekeeping/permissions.py` | Duplicate of hotel version: staff's `hotel.slug` matches URL `hotel_slug`. Object-level: compares hotel IDs on `HousekeepingTask` or `RoomStatusLog` |

### Staff Chat Permissions

| Class | File | Logic |
|-------|------|-------|
| **`IsStaffOfHotel`** | `staff_chat/permissions.py` | Same pattern |
| **`IsConversationParticipant`** | `staff_chat/permissions.py` | Object-level: user's staff is in `conversation.participants` |
| **`IsMessageSender`** | `staff_chat/permissions.py` | Object-level: `message.sender == request.user.staff_profile` |
| **`CanDeleteConversation`** | `staff_chat/permissions.py` | Creator OR `role.slug` in `['manager', 'admin']` |
| **`CanDeleteMessage`** | `staff_chat/permissions.py` | Own messages for soft-delete; manager/admin for hard-delete |

### Housekeeping RBAC Policy Functions

| Function | File | Logic |
|----------|------|-------|
| `is_manager(staff)` | `housekeeping/permissions.py` | `is_superuser` OR `access_level` in `[staff_admin, super_staff_admin]` |
| `is_housekeeping_staff(staff)` | `housekeeping/permissions.py` | `is_superuser` OR `department.slug == 'housekeeping'` |
| `can_transition(staff, from_status, to_status)` | `housekeeping/permissions.py` | Managers: any valid. Housekeeping: workflow only. Front desk: limited |
| `can_assign_tasks(staff)` | `housekeeping/permissions.py` | Only managers |
| `can_perform_housekeeping(staff)` | `housekeeping/permissions.py` | Managers OR housekeeping staff |

### Navigation Permission Helpers

| Function | File | Purpose |
|----------|------|---------|
| `get_canonical_permissions(user)` | `staff/permissions.py` | Returns dict with `access_level`, `hotel_id`, `hotel_slug`, `is_superuser`, `nav_slugs` (list), `nav_items` (full menu) |
| `nav_permission_required(nav_slug)` | `staff/permissions.py` | View decorator |
| `make_nav_permission(nav_slug)` | `staff/permissions.py` | Factory for `HasNavPermission` instances |

---

## 4. Token Types & Scopes

### 4.1 GuestBookingToken Scopes

| Scope | Grants Access To |
|-------|-----------------|
| `STATUS_READ` | View booking status, basic booking context |
| `CHAT` | Guest ↔ staff chat messaging |
| `ROOM_SERVICE` | Place room service / breakfast orders |

**Scope derivation from legacy `scope` field:**
- `FULL_ACCESS` → `['STATUS_READ', 'CHAT', 'ROOM_SERVICE']`
- `CHAT` → `['STATUS_READ', 'CHAT']`
- Default → `['STATUS_READ']`

**Constraints:**
- One active token per booking (DB unique constraint)
- New token generation revokes any existing active token
- Expires at: `check_out_date + 30 days`
- Revoked on: checkout, cancellation, new token generation

### 4.2 PrecheckinToken

| Aspect | Detail |
|--------|--------|
| **Model** | `hotel.PrecheckinToken` |
| **Purpose** | Pre-check-in form access (name, ID, preferences) |
| **Issued** | Staff sends pre-checkin email link |
| **Validated** | `hotel/public_views.py:ValidatePrecheckinTokenView` |
| **Expires** | Time-based |
| **Config** | Snapshots hotel's precheckin config at creation |

### 4.3 BookingManagementToken

| Aspect | Detail |
|--------|--------|
| **Model** | `hotel.BookingManagementToken` |
| **Purpose** | Guest booking management (view status, cancel) |
| **Validated** | `hotel/public_views.py:ValidateBookingManagementTokenView` |
| **Validity** | Status-based (not time-based) — valid while booking is in cancellable state |
| **Scopes** | `allowed_actions` JSONField |

### 4.4 SurveyToken

| Aspect | Detail |
|--------|--------|
| **Model** | `hotel.SurveyToken` |
| **Purpose** | Post-checkout survey access |
| **Issued** | Automatically on checkout (if AUTO_IMMEDIATE/DELAYED) or manually by staff |
| **Expires** | Time-based |
| **Config** | Snapshots hotel's survey config at creation |

---

## 5. Unprotected Endpoints (AllowAny)

### Public Zone (`/api/public/`)
All endpoints use `AllowAny` — by design for public hotel discovery and booking flow:
- Hotel listing, filtering, public page
- Room availability, pricing quotes
- Booking creation, payment sessions
- Pre-checkin form submission
- Survey form submission
- Booking status check, cancellation
- Stripe webhook

### Staff Auth Endpoints
- `POST /api/staff/login/` — `AllowAny`
- `POST /api/staff/<hotel_slug>/register/` — `AllowAny`
- `POST /api/staff/password-reset/` — `AllowAny`
- `POST /api/staff/password-reset-confirm/` — `AllowAny`

### Guest Portal (`/api/guest/`)
Views use `AllowAny` but enforce token auth internally via `GuestTokenMixin`.

### Other AllowAny Endpoints
- All entertainment/game endpoints (guest-facing)
- Room service guest ordering endpoints
- Some hotel_info read endpoints
- `GET /api/hotels/<hotel_slug>/face-config/` — face recognition config
- Maintenance comments (`MaintenanceCommentViewSet`)
- Pusher auth (`/api/notifications/pusher/auth/`) — custom auth logic inside

### ⚠️ Potentially Unprotected
- `AddGuestToRoomView` (`rooms/views.py`) — no `permission_classes` set explicitly; relies on DRF global default (`IsAuthenticated`)
- `RoomByHotelAndNumberView` (`rooms/views.py`) — same concern

---

## 6. Hotel Scoping Mechanisms

### Middleware — `SubdomainMiddleware` (`hotel/middleware.py`)
Runs on every request:
1. Extract subdomain from `Host` header (e.g., `killarney.hotelsmates.com` → `killarney`)
2. Look up `Hotel.objects.get(slug=subdomain)`
3. Set `request.hotel` (or `None` for localhost/IP)

### URL Path — `<hotel_slug>` parameter
Most staff views capture `hotel_slug` in URL kwargs. Permission classes like `IsStaffOfHotel` validate staff's hotel matches the URL parameter.

### Custom Headers
| Header | Purpose | File |
|--------|---------|------|
| `X-Hotel-Slug` | Used by `GuestViewSet` to scope guests | `guests/views.py` |
| `X-Hotel-Id` | CORS allowed header | `settings.py` |
| `X-Hotel-Identifier` | CORS allowed header | `settings.py` |
| `Idempotency-Key` | Payment idempotency | `settings.py` CORS config |

### Token-Implicit
Guest portal views derive hotel context from the token's booking → hotel FK chain. No URL-level hotel slug needed.

---

## 7. Pusher Channel Authentication

**Endpoint:** `POST /api/notifications/pusher/auth/`  
**View:** `PusherAuthView` (`notifications/views.py`)

**Dual-mode authentication:**

| Mode | Detection | Validation |
|------|-----------|-----------|
| **Staff** | DRF TokenAuth header present | Validate staff belongs to hotel in channel name |
| **Guest** | `Authorization: GuestToken <token>` or `?token=` | Validate token active, not expired, scopes include `CHAT`, hotel matches channel |

**Channel naming:** Channels contain hotel_slug for scoping (e.g., `private-hotel-killarney-room-101`).  
**Signing:** HMAC-SHA256 via Pusher SDK.
