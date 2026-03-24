# Audit Remediation — Completed Fixes

**Date:** March 24, 2026  
**Based on:** [BACKEND_AUDIT.md](BACKEND_AUDIT.md) findings cross-referenced against codebase changes  
**Status:** ~18 of ~49 audit findings resolved

---

## Section 4 — Multi-Tenant Isolation

### FIX: `guests/views.py` — Replaced Header-Based Hotel Trust With URL Slug

**Audit finding:** `GuestViewSet` relied on the `x-hotel-slug` HTTP header, which is client-controlled. An authenticated user from Hotel A could pass `x-hotel-slug: hotel-b` to access Hotel B's guest data.

**What changed:**
- `get_queryset()`: `self.request.headers.get('x-hotel-slug')` → `self.kwargs.get('hotel_slug')`
- `get_object()`: Same replacement

Hotel is now resolved from the URL path (`/api/staff/hotel/<hotel_slug>/guests/`), which is the standard trusted pattern used across the project.

---

### FIX: `maintenance/views.py` — `MaintenanceCommentViewSet` No Longer `AllowAny`

**Audit finding:** `MaintenanceCommentViewSet` had `AllowAny` + `objects.all()` — anyone could read maintenance comments from any hotel.

**What changed:**
- `permission_classes` changed from `[AllowAny]` to `[IsAuthenticated]`

Note: `MaintenanceRequestViewSet` still needs hotel-scoped filtering (tracked in next steps).

---

### FIX: `stock_tracker/report_views.py` — Financial Reports No Longer Public

**Audit finding:** `StockValueReportView` and `SalesReportView` had `AllowAny` — anyone could view financial data for any hotel.

**What changed:**
- Both views changed from `permission_classes = [AllowAny]` to `permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]`
- Added import for `IsSuperStaffAdminForHotel` from `hotel.permissions`

Now only authenticated super staff admins for the specific hotel can access stock/sales reports.

---

### FIX: `hotel_info/views.py` — Info Pages Protected + Hotel Scoping on QR Generation

**Audit finding:** `HotelInfoViewSet` and `HotelInfoCategoryViewSet` had `AllowAny`, allowing mutations (create/update/delete) without authentication.

**What changed:**
- Both ViewSets changed from `AllowAny` to `IsAuthenticatedOrReadOnly` — guests can read, only staff can mutate
- `HotelInfoCategoryViewSet.create()`: Replaced `request.data.get("hotel_slug")` (client-controlled) with `request.user.staff_profile.hotel` (server-validated) for QR code generation
- `CategoryQRView.post()`: Replaced `request.data.get("hotel_slug")` with `request.user.staff_profile.hotel`, added 403 if caller has no staff profile

This eliminates the cross-hotel QR generation attack vector.

---

## Section 5 — Booking & Room Allocation Flow

### FIX: Checkout Deadline Uses Hotel Timezone

**Audit finding:** Overstay detection used hardcoded noon. No timezone awareness for hotels in different regions.

**What changed:**
- Implemented `compute_checkout_deadline_at()` in `room_bookings/services/overstay.py`
- Uses `HotelAccessConfig.standard_checkout_time` (configurable per hotel)
- Uses `hotel.timezone_obj` with `pytz.localize()` for proper DST handling
- Converts to UTC for consistent comparison
- All overstay/checkout logic routes through this single function (enforced by code comment as an invariant)

**Commits:** `c72c337`, `8f2b103`, `942ca78`, `6451df0`, `c6885c5`

---

### FIX: Booking Approval Cutoff Is Hotel-Configurable

**Audit finding:** No configurable approval deadlines for bookings.

**What changed:**
- Implemented hotel-configurable approval cutoff via `HotelAccessConfig`
- Management command `auto_expire_overdue_bookings` expires `PENDING_APPROVAL` bookings past their deadline with automatic Stripe refund

**Commits:** `b83c986`, `defecf1`

---

### FIX: Overstay Detection and Management System

**Audit finding:** Overstay handling existed but had gaps.

**What changed:**
- Full overstay lifecycle: `detect_overstays()` scans IN_HOUSE bookings past checkout deadline
- `OverstayIncident` model with states: OPEN → ACKED → RESOLVED
- `OverstayAcknowledgeView`, `OverstayExtendView`, `OverstayStatusView` API endpoints
- Extension creates `BookingExtension` with Stripe `PaymentIntent`
- Room conflict checking during extension
- Comprehensive test coverage for incident handling

**Commits:** `b3a8d6a` through `47ef9d5` (12+ commits)

---

## Section 6 — Guest Lifecycle & Token System

### FIX: Token Cleanup Management Command Now Exists

**Audit finding:** "Referenced in docs but doesn't exist; expired tokens accumulate."

**What changed:**
- Created `hotel/management/commands/cleanup_survey_tokens.py`
- Supports `--dry-run` flag to preview deletions
- Supports `--days-old` parameter (default: 30)
- Cleans up expired, used, and old survey tokens while preserving survey responses

---

## Section 8 — RBAC

### FIX: Superuser Escalation Vulnerability Eliminated

**Audit finding:** Any staff member creating another staff profile could set `is_superuser=True` via the POST body, granting full Django admin access.

```python
# BEFORE (vulnerable)
user.is_superuser = False
if "is_superuser" in request.data:
    user.is_superuser = request.data["is_superuser"]  # Anyone can escalate!
```

**What changed in `staff/views.py`:**
- Removed the `if "is_superuser" in request.data` block entirely
- Removed the `if "is_staff" in request.data` block
- Hardcoded `user.is_superuser = False` with comment: *"SECURITY: is_superuser is NEVER set via API — only via Django admin / CLI"*
- Replaced `print()` debug statement with `logger.info()`

This was the single most severe RBAC vulnerability in the audit.

---

### FIX: Access Level Check on Staff Creation

**Audit finding:** `CreateStaffFromUserAPIView` had no `access_level` restriction. A `regular_staff` could create `super_staff_admin` users.

**What changed in `staff/views.py`:**
- Added guard: if `requested_access_level == "super_staff_admin"` and the requesting staff isn't `super_staff_admin`, returns 403
- Only `super_staff_admin` can now create other `super_staff_admin` accounts

---

### FIX: `bookings/views.py` — `BlueprintObjectViewSet` No Longer `AllowAny`

**Audit finding:** `BlueprintObjectViewSet` had `permission_classes = [AllowAny]`.

**What changed:**
- Changed to `permission_classes = [IsAuthenticated]`

---

### FIX: `bookings/views.py` — `AssignGuestToTableAPIView` No Longer Unprotected

**Audit finding:** `AssignGuestToTableAPIView` had `permission_classes = []`.

**What changed:**
- Changed to `permission_classes = [IsAuthenticated]`

---

### FIX: Staff Booking Views — Proper Permission Declaration

**Audit finding:** `StaffBookingsListView`, `StaffBookingConfirmView`, `StaffBookingCancelView`, and `StaffBookingDetailView` all had `permission_classes = []` with a `get_permissions()` override returning instantiated permission objects.

**What changed in `hotel/staff_views.py`:**
- All four views changed from the indirect pattern to direct declaration:
```python
# BEFORE (fragile — permission_classes=[] bypasses DRF schema/introspection)
permission_classes = []
def get_permissions(self):
    return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

# AFTER (standard DRF pattern)
permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
```

---

### FIX: `entertainment/views.py` — QR Code Generation Requires Auth

**Audit finding:** All entertainment endpoints including `generate_qr_code` were `AllowAny`.

**What changed:**
- `MemoryGameTournamentViewSet.generate_qr_code` action changed from `AllowAny` to `IsAuthenticated`
- All remaining `AllowAny` viewsets annotated with comments explaining guest-facing intent (room tablet use case)

---

## Section 9 — Communication & Realtime

### FIX: Test Endpoint Removed From Production

**Audit finding:** `test_deletion_broadcast` was `AllowAny` and let anyone trigger arbitrary Pusher events.

**What changed:**
- Entire `test_deletion_broadcast` function (~107 lines) deleted from `chat/views.py`
- URL pattern removed from `chat/urls.py`
- No test endpoints remain in production code

---

### FIX: Staff-Only Chat Endpoints Now Require Authentication

**Audit finding:** 15+ chat endpoints used `AllowAny`, including staff-facing ones.

**What changed in `chat/views.py`:**

| Endpoint | Before | After |
|----------|--------|-------|
| `get_active_rooms` | `AllowAny` | `IsAuthenticated` |
| `get_unread_count` | `AllowAny` | `IsAuthenticated` |
| `get_unread_conversation_count` | `AllowAny` | `IsAuthenticated` |

Endpoints that must remain `AllowAny` for guest chat (guests are not Django-authenticated) were annotated with explicit comments explaining why:
- `send_conversation_message` — guests send messages
- `mark_conversation_read` — guests mark messages read
- `update_message` / `delete_message` — guests edit/delete own messages
- `upload_message_attachment` / `delete_attachment` — guests upload files
- `get_or_create_conversation_from_room` — guests initiate conversations

---

### FIX: Debug `print()` Statements Removed From Chat

**Audit finding:** `delete_message` had a 10-line `print()` debug block exposing user/message details.

**What changed:**
- Removed emoji-laden `print()` block (10 lines)
- Replaced with single structured `logger.info()` call logging only message_id, auth status, staff status, and sender_type

---

### FIX: Channel Naming Standardized to Dashes

**Audit finding:** Channel naming used inconsistent separators (dots vs dashes).

**What changed:**
- Commit `5deba36` updated channel naming conventions to use dashes for consistency
- Guest booking channels use `private-` prefix: `private-hotel-{slug}-guest-chat-booking-{booking_id}`

Note: One remaining inconsistency at line ~1476 in `notification_manager.py` still uses dot format (tracked in next steps).

---

### FIX: Security Gate Helper Added for Chat

**What changed:**
- Added `_require_staff_or_guest()` function at top of `chat/views.py`
- Verifies caller is either authenticated staff or valid guest context
- Provides consistent identity resolution for all chat endpoints

---

## Section 11 — Automation & Scheduler

### FIX: Auto-Creation of Hotel-Related Objects via Signals

**Audit finding:** Missing related objects could cause errors when accessing hotel features.

**What changed in `hotel/signals.py`:**
- New `create_hotel_related_objects` signal handler on `Hotel.post_save`
- Auto-creates: `HotelPublicPage`, `BookingOptions`, `AttendanceSettings`, `ThemePreference`, `HotelPrecheckinConfig`, `HotelSurveyConfig`
- Also backfills missing objects for existing hotels on save

**Backfill command:** `hotel/management/commands/backfill_hotel_related_objects.py` for one-time migration of existing hotels.

---

### FIX: `hotel/permissions.py` — Flexible Hotel Slug Resolution

**What changed:**
- `IsSuperStaffAdminForHotel` now checks both `hotel_slug` and `hotel_identifier` kwargs
- Supports URL patterns that use either naming convention

---

### FIX: `hotel/public_views.py` — Robust Public Page Handling

**What changed:**
- `HotelPublicPageView` no longer crashes when `public_page` doesn't exist
- Bare `except:` replaced with specific `Hotel.public_page.RelatedObjectDoesNotExist`
- Auto-creates `HotelPublicPage` if missing

---

## Summary

| Category | Fixes Applied |
|----------|---------------|
| Multi-Tenant Isolation | 4 fixes (guests header→URL, maintenance comments auth, stock reports auth, hotel_info scoping) |
| Booking Flow | 3 fixes (timezone-aware checkout, configurable approval cutoff, full overstay system) |
| Token System | 1 fix (cleanup command) |
| RBAC | 6 fixes (superuser escalation, access level guard, 4 endpoint permission fixes) |
| Realtime/Comms | 4 fixes (test endpoint removed, staff chat auth, debug prints removed, channel naming) |
| Scheduler/Infra | 3 fixes (auto-creation signals, backfill command, flexible permissions) |
| **Total** | **~18 fixes** |
