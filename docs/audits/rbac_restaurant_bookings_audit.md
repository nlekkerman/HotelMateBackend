# RBAC Audit — Restaurant Bookings Module

Audit-only. No implementation. Scope is restricted to the restaurant-booking
domain (`bookings/` app). Room bookings (`room_bookings/`) and `room_services/`
are out of scope.

All claims below are derived from inspecting source files; nothing is inferred
from documentation, comments, or prior summaries.

---

## 1. Files inspected

- [bookings/urls.py](bookings/urls.py)
- [bookings/staff_urls.py](bookings/staff_urls.py)
- [bookings/views.py](bookings/views.py)
- [bookings/serializers.py](bookings/serializers.py)
- [bookings/models.py](bookings/models.py)
- [staff_urls.py](staff_urls.py)
- [HotelMateBackend/urls.py](HotelMateBackend/urls.py)
- [staff/permissions.py](staff/permissions.py)
- [staff/capability_catalog.py](staff/capability_catalog.py)
- [staff/module_policy.py](staff/module_policy.py)
- [staff/role_catalog.py](staff/role_catalog.py)
- [staff/department_catalog.py](staff/department_catalog.py)
- [staff/nav_catalog.py](staff/nav_catalog.py)

---

## 2. Route / endpoint inventory

### Mount points

| Prefix | Source | File |
|---|---|---|
| `/api/bookings/` | `path('api/bookings/', include('bookings.urls'))` | [HotelMateBackend/urls.py](HotelMateBackend/urls.py#L57) |
| `/<staff-prefix>/hotel/<hotel_slug>/service-bookings/` | `path('hotel/<str:hotel_slug>/service-bookings/', include('bookings.staff_urls'))` | [staff_urls.py](staff_urls.py#L171-L173) |

Both prefixes mount the same view classes (defined in [bookings/views.py](bookings/views.py)). The staff-mount uses [bookings/staff_urls.py](bookings/staff_urls.py) which re-uses the same viewsets via a fresh `DefaultRouter`.

### Public/guest mount (`/api/bookings/`) — [bookings/urls.py](bookings/urls.py)

| Method(s) | URL path (relative to `/api/bookings/`) | View | Action / method | `permission_classes` (effective) | Serializer | Model / service |
|---|---|---|---|---|---|---|
| GET | `restaurants/` (router) | `RestaurantViewSet` | `list` | `IsAuthenticated`, `HasNavPermission('restaurant_bookings')`, `IsStaffMember`, `IsSameHotel` | `RestaurantSerializer` | `Restaurant` |
| POST | `restaurants/` | `RestaurantViewSet` | `create` | + `CanManageRestaurantBookings` | `RestaurantSerializer` | `Restaurant` |
| GET / PUT / PATCH / DELETE | `restaurants/<slug>/` | `RestaurantViewSet` | `retrieve` / `update` / `partial_update` / `destroy` (soft via `is_active=False`) | base + (write → `CanManageRestaurantBookings`) | `RestaurantSerializer` | `Restaurant` |
| GET | `bookings/` (router) | `BookingViewSet` | `list` | `IsAuthenticated`, `HasNavPermission('restaurant_bookings')`, `IsStaffMember`, `IsSameHotel` | `BookingSerializer` | `Booking` |
| POST | `bookings/` | `BookingViewSet` | `create` | + `CanManageRestaurantBookings` | `BookingSerializer` | `Booking` |
| GET / PUT / PATCH / DELETE | `bookings/<pk>/` | `BookingViewSet` | `retrieve` / `update` / `partial_update` / `destroy` | base + (write → `CanManageRestaurantBookings`) | `BookingSerializer` | `Booking` |
| GET | `categories/` (router) | `BookingCategoryViewSet` | `list` | `IsAuthenticated`, `HasNavPermission('restaurant_bookings')`, `IsStaffMember`, `IsSameHotel` | `BookingCategorySerializer` | `BookingCategory` |
| POST / PUT / PATCH / DELETE | `categories/...` | `BookingCategoryViewSet` | CUD | + `CanManageRestaurantBookings` | `BookingCategorySerializer` | `BookingCategory` |
| GET | `blueprint-object-types/` (router) | `BlueprintObjectTypeViewSet` | `list` / `retrieve` | `AllowAny` | `BlueprintObjectTypeSerializer` | `BlueprintObjectType` |
| GET / POST | `<hotel_slug>/restaurants/` | `RestaurantViewSet` (alias view) | `list` / `create` | as per viewset (above) | `RestaurantSerializer` | `Restaurant` |
| GET / POST | `<hotel_slug>/<restaurant_slug>/blueprint/<blueprint_id>/objects/` | `BlueprintObjectViewSet` | `list` / `create` | list/retrieve → `IsAuthenticated`; CUD → `IsAuthenticated`, `HasNavPermission('restaurant_bookings')`, `IsStaffMember`, `IsSameHotel`, `CanManageRestaurantBookings` | `BlueprintObjectSerializer` | `BlueprintObject` |
| GET / PATCH / PUT / DELETE | `<hotel_slug>/<restaurant_slug>/blueprint/<blueprint_id>/objects/<pk>/` | `BlueprintObjectViewSet` | `retrieve` / `update` / `partial_update` / `destroy` | same as above | `BlueprintObjectSerializer` | `BlueprintObject` |
| GET / POST | `guest-booking/<hotel_slug>/restaurant/<restaurant_slug>/[room/<room_number>/]` | `GuestDinnerBookingView` | `get` / `post` | `AllowAny` | `BookingSerializer` (out), `BookingCreateSerializer` (in) | `Booking`, `Restaurant`, `BookingCategory`, `BookingSubcategory`, `Room`, `Hotel` |
| GET / POST | `<hotel_slug>/<restaurant_slug>/blueprint/` | `RestaurantBlueprintViewSet` | `list` / `create` | list/retrieve → `AllowAny`; CUD → `IsAuthenticated`, `HasNavPermission('restaurant_bookings')`, `IsStaffMember`, `IsSameHotel`, `CanManageRestaurantBookings` | `RestaurantBlueprintSerializer` | `RestaurantBlueprint` |
| GET / PUT / PATCH / DELETE | `<hotel_slug>/<restaurant_slug>/blueprint/<pk>/` | `RestaurantBlueprintViewSet` | `retrieve` / write | same as above | `RestaurantBlueprintSerializer` | `RestaurantBlueprint` |
| GET / POST | `<hotel_slug>/<restaurant_slug>/tables/` | `DiningTableViewSet` | `list` / `create` | list/retrieve → `AllowAny`; CUD → `IsAuthenticated`, `HasNavPermission('restaurant_bookings')`, `IsStaffMember`, `IsSameHotel`, `CanManageRestaurantBookings` | `DiningTableSerializer` | `DiningTable` |
| GET / PUT / PATCH / DELETE | `<hotel_slug>/<restaurant_slug>/tables/<id>/` | `DiningTableViewSet` | `retrieve` / write | same as above | `DiningTableSerializer` | `DiningTable` |
| GET | `available-tables/<hotel_slug>/<restaurant_slug>/` | `AvailableTablesView` | `get` | `AllowAny` | `DiningTableSerializer` | `DiningTable`, `Booking`, `Restaurant` |
| POST | `mark-seen/<hotel_slug>/` | `mark_bookings_seen` (FBV) | `POST` | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel` + inline `HasNavPermission('restaurant_bookings').has_permission(...)` | — | `Booking` |
| POST | `assign/<hotel_slug>/<restaurant_slug>/` | `AssignGuestToTableAPIView` | `post` | `IsAuthenticated`, `HasRestaurantBookingsNav`, `IsStaffMember`, `IsSameHotel`, `CanManageRestaurantBookings` | — | `Booking`, `DiningTable`, `BookingTable` |
| POST | `unseat/<hotel_slug>/<restaurant_slug>/` | `UnseatBookingAPIView` | `post` | same chain | `BookingSerializer` (out) | `Booking`, `BookingTable` |
| DELETE | `delete/<hotel_slug>/<restaurant_slug>/<booking_id>/` | `DeleteBookingAPIView` | `delete` | same chain | — | `Booking` |

### Staff mount (`/.../service-bookings/`) — [bookings/staff_urls.py](bookings/staff_urls.py)

This file re-routes the **same** view classes; permission behaviour is identical to the public mount (the views own `get_permissions`):

- Router: `bookings/`, `categories/`, `blueprint-object-types/`, `restaurants/`.
- `blueprint/<slug>/`, `blueprint/<slug>/<pk>/` → `RestaurantBlueprintViewSet`.
- `tables/<slug>/`, `tables/<slug>/<id>/` → `DiningTableViewSet`.
- `blueprint/<slug>/<blueprint_id>/objects/[...]` → `BlueprintObjectViewSet`.
- `available-tables/<slug>/` → `AvailableTablesView` (`AllowAny`).
- `mark-seen/` → `mark_bookings_seen` (note: the URL has no `<hotel_slug>` segment here, but the view signature in [bookings/views.py](bookings/views.py#L549) requires `hotel_slug` — UNKNOWN whether this route is currently reachable; reverse-resolved differently).
- `assign/<slug>/`, `unseat/<slug>/`, `delete/<slug>/<booking_id>/` → corresponding `APIView` classes.

`GuestDinnerBookingView` is **not** registered on the staff mount — guest-only.

---

## 3. Current authority checks (per endpoint group)

Legend: ✓ = present, ✗ = absent / not enforced, n/a = not applicable.

| Endpoint group | AuthN | Staff check | Same-hotel | Nav slug | Tier check | Role string | Inline custom | Notes |
|---|---|---|---|---|---|---|---|---|
| `BookingViewSet` (list/retrieve) | ✓ `IsAuthenticated` | ✓ `IsStaffMember` | ✓ `IsSameHotel` | ✓ `HasNavPermission('restaurant_bookings')` | ✗ | ✗ | ✗ | Reads gated by nav only. |
| `BookingViewSet` (CUD) | ✓ | ✓ | ✓ | ✓ | ✓ via `CanManageRestaurantBookings` (`tier ≥ staff_admin`) | ✗ | ✗ | Tier-only authority for CUD. |
| `BookingCategoryViewSet` | same as above | same | same | same | same | ✗ | ✗ | Mirrors `BookingViewSet`. |
| `RestaurantViewSet` | same | same | same | same | same | ✗ | ✗ | `destroy` is soft-delete (`is_active=False`); still tier-gated. |
| `RestaurantBlueprintViewSet` (list/retrieve) | ✗ `AllowAny` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | Public read of blueprint geometry. |
| `RestaurantBlueprintViewSet` (CUD) | ✓ | ✓ | ✓ | ✓ | ✓ tier ≥ staff_admin | ✗ | ✗ | |
| `DiningTableViewSet` (list/retrieve) | ✗ `AllowAny` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | Public read of table inventory. |
| `DiningTableViewSet` (CUD) | ✓ | ✓ | ✓ | ✓ | ✓ tier ≥ staff_admin | ✗ | ✗ | |
| `BlueprintObjectTypeViewSet` | ✗ `AllowAny` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | Read-only catalog. |
| `BlueprintObjectViewSet` (list/retrieve) | ✓ `IsAuthenticated` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | Any authenticated user (including guest tokens? — UNKNOWN, depends on token contract). |
| `BlueprintObjectViewSet` (CUD) | ✓ | ✓ | ✓ | ✓ | ✓ tier ≥ staff_admin | ✗ | ✗ | |
| `GuestDinnerBookingView.get` | ✗ `AllowAny` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | Lists dinner bookings for hotel — exposes guest bookings publicly. |
| `GuestDinnerBookingView.post` | ✗ `AllowAny` | ✗ | n/a | ✗ | ✗ | ✗ | ✓ business rules (capacity, group size, max-per-hour, dup-room/day) | Anonymous create; no token validation visible. |
| `AvailableTablesView.get` | ✗ `AllowAny` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | Public availability lookup. |
| `mark_bookings_seen` (FBV) | ✓ | ✓ | ✓ | ✓ inline (`HasNavPermission(...).has_permission`) | ✗ | ✗ | ✓ inline | Inline nav check instead of decorator class. |
| `AssignGuestToTableAPIView` | ✓ | ✓ | ✓ | ✓ `HasRestaurantBookingsNav` | ✓ tier ≥ staff_admin | ✗ | ✗ | |
| `UnseatBookingAPIView` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | |
| `DeleteBookingAPIView` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | Hard delete. |

### Missing checks worth flagging

- `GuestDinnerBookingView.post` — no guest-token validation (e.g. no `resolve_guest_access` equivalent as used in `room_services`); accepts any anonymous payload, only validated against business rules.
- `GuestDinnerBookingView.get` — anonymous read of all dinner bookings for a hotel (PII via `guest`/`room` related serializer fields — UNKNOWN exposure, depends on `BookingSerializer`).
- `RestaurantBlueprintViewSet`, `DiningTableViewSet` — `AllowAny` on read; same-hotel scope is enforced only by URL slugs in `get_queryset`, no authority check.
- `BlueprintObjectViewSet` (list/retrieve) — `IsAuthenticated` only; no `IsStaffMember`, no `IsSameHotel`, no nav. Cross-hotel staff (or any authenticated user with a token) can read another hotel's blueprint objects.
- All staff CUD endpoints — authority is strictly tier-based (`tier ≥ staff_admin` via `CanManageRestaurantBookings`); no per-action capability granularity, no role/department preset participation.
- No object-level (`has_object_permission`) checks anywhere — same-hotel scoping relies on `IsSameHotel` (request-level) plus URL slug filtering in `get_queryset` / `get_object`.

---

## 4. Action surface (derived from endpoints)

Real, enforced actions present in code today:

- Restaurant config
  - restaurant read (list/retrieve)
  - restaurant create
  - restaurant update / partial_update
  - restaurant soft-delete (`destroy` → `is_active=False`)
- Booking category config
  - category read
  - category create / update / delete
- Booking record
  - booking read (list/retrieve)
  - booking create (staff path; guest path via `GuestDinnerBookingView`)
  - booking update / partial_update
  - booking destroy (DRF default, gated by `CanManageRestaurantBookings`)
  - booking hard-delete via `DeleteBookingAPIView`
  - booking "mark seen" bulk update (`mark_bookings_seen`)
- Booking ↔ table assignment
  - assign booking to table (`AssignGuestToTableAPIView`)
  - unseat booking from table (`UnseatBookingAPIView`)
- Dining-room config
  - dining table read (currently `AllowAny`)
  - dining table create / update / delete
  - blueprint read (currently `AllowAny`)
  - blueprint create / update / delete
  - blueprint object read (`IsAuthenticated`)
  - blueprint object create / update / delete
  - blueprint object type read (`AllowAny`, catalog)
- Availability lookup
  - available-tables (`AllowAny`)
- Guest path
  - guest list dinner bookings (`AllowAny`)
  - guest create dinner booking (`AllowAny`)

No "approve / confirm" workflow exists in code. No status-transition state machine is enforced beyond the booking's `seen` flag.

---

## 5. RBAC gap table

| # | Endpoint | Current gate | Missing gate | Proposed capability | Risk |
|---|---|---|---|---|---|
| 1 | `BookingViewSet` list/retrieve | nav + staff + same-hotel | per-action capability | `restaurant_booking.record.read` | Medium — read open to any nav-enabled staff. |
| 2 | `BookingViewSet` create | nav + staff + same-hotel + tier ≥ staff_admin | granular cap; tier-only authority | `restaurant_booking.record.create` | Medium — non-admin floor staff cannot book; admins always can — coarse. |
| 3 | `BookingViewSet` update / partial_update | same | granular cap | `restaurant_booking.record.update` | Medium |
| 4 | `BookingViewSet` destroy | same | granular cap | `restaurant_booking.record.delete` | Medium |
| 5 | `BookingCategoryViewSet` reads | nav + staff + same-hotel | granular cap | `restaurant_booking.category.read` | Low |
| 6 | `BookingCategoryViewSet` CUD | + tier ≥ staff_admin | granular cap | `restaurant_booking.category.manage` | Low–Medium |
| 7 | `RestaurantViewSet` reads | nav + staff + same-hotel | granular cap | `restaurant_booking.restaurant.read` | Low |
| 8 | `RestaurantViewSet` CUD | + tier ≥ staff_admin | granular cap | `restaurant_booking.restaurant.manage` | Medium |
| 9 | `RestaurantBlueprintViewSet` list/retrieve | `AllowAny` | authN + staff + same-hotel + cap | `restaurant_booking.blueprint.read` (or keep guest-readable behind a token) | High — blueprint geometry exposed publicly. |
| 10 | `RestaurantBlueprintViewSet` CUD | nav + tier ≥ staff_admin | granular cap | `restaurant_booking.blueprint.manage` | Medium |
| 11 | `DiningTableViewSet` list/retrieve | `AllowAny` | authN + staff + same-hotel + cap (or token-gated guest read) | `restaurant_booking.table.read` | High — table inventory public. |
| 12 | `DiningTableViewSet` CUD | nav + tier ≥ staff_admin | granular cap | `restaurant_booking.table.manage` | Medium |
| 13 | `BlueprintObjectViewSet` list/retrieve | `IsAuthenticated` only | staff + same-hotel + cap | `restaurant_booking.blueprint.read` (shared) | High — any authenticated principal can read another hotel's blueprint objects. |
| 14 | `BlueprintObjectViewSet` CUD | nav + staff + same-hotel + tier ≥ staff_admin | granular cap | `restaurant_booking.blueprint.manage` | Medium |
| 15 | `BlueprintObjectTypeViewSet` | `AllowAny` | UNKNOWN whether intended public | `restaurant_booking.blueprint.read` (or keep public if static catalog) | Low |
| 16 | `GuestDinnerBookingView.get` | `AllowAny` | guest-token validation, restrict to non-PII fields, scope to hotel | n/a (guest path) | High — anonymous list of all dinner bookings for hotel; PII exposure depends on serializer. |
| 17 | `GuestDinnerBookingView.post` | `AllowAny` + business rules | guest-token validation (room/QR token) | n/a (guest path) | High — anonymous booking creation; abuse / spoofed-room risk. |
| 18 | `AvailableTablesView.get` | `AllowAny` | guest-token validation OR staff cap | n/a (guest path) — for staff use also add `restaurant_booking.table.read` | Medium |
| 19 | `mark_bookings_seen` | inline nav (function call) | promote to per-action cap, drop inline | `restaurant_booking.record.mark_seen` | Low — semantics OK, style inconsistent. |
| 20 | `AssignGuestToTableAPIView` | nav + staff + same-hotel + tier ≥ staff_admin | granular cap | `restaurant_booking.assignment.assign` | Medium — coarse tier gate. |
| 21 | `UnseatBookingAPIView` | same | granular cap | `restaurant_booking.assignment.unseat` | Medium |
| 22 | `DeleteBookingAPIView` | same | granular cap; consider soft-delete | `restaurant_booking.record.delete` | Medium — hard delete. |
| 23 | All viewsets | — | fail-closed `_DenyAll` for unmapped actions (pattern used in `room_services`) | n/a | Low — defence in depth. |

---

## 6. Capability / registry status

Verified by grep against [staff/capability_catalog.py](staff/capability_catalog.py), [staff/module_policy.py](staff/module_policy.py), [staff/role_catalog.py](staff/role_catalog.py), [staff/department_catalog.py](staff/department_catalog.py), [staff/nav_catalog.py](staff/nav_catalog.py), [staff/permissions.py](staff/permissions.py).

| Registry | Restaurant-booking presence | Evidence |
|---|---|---|
| `CANONICAL_CAPABILITIES` | **Absent.** No `restaurant_booking.*` slug exists. The `BOOKING_*` slugs (`booking.module.view`, `booking.record.read`, `booking.room.assign`, `booking.stay.checkin`, `booking.config.manage`, …) are **room-booking** capabilities, not restaurant. | grep `restaurant\|dining\|table` in catalog → only doc comments. |
| `MODULE_POLICY` | **Absent.** Only key `bookings` exists, and it maps to room-booking caps via `BOOKINGS_ACTIONS` (`BOOKING_RECORD_READ`, `BOOKING_ROOM_ASSIGN`, `BOOKING_STAY_CHECKIN`, etc.). No `restaurant_bookings` key. | [staff/module_policy.py](staff/module_policy.py#L260-L264) |
| Tier defaults (`TIER_DEFAULT_CAPABILITIES`) | No restaurant-booking bucket. Authority for restaurant-booking CUD is delivered via `CanManageRestaurantBookings` (`_tier_at_least(tier, 'staff_admin')`) outside the capability system. | [staff/permissions.py](staff/permissions.py#L375-L387) |
| `ROLE_PRESET_CAPABILITIES` | No restaurant-booking caps wired to any role. Roles `waiter`, `host`, `bartender`, `chef`, `fnb_manager` exist in [staff/role_catalog.py](staff/role_catalog.py) (Food & Beverage department), but they have no per-module restaurant-booking grants because no caps exist. | grep `waiter\|fnb\|food_beverage\|host` in catalog → only one doc comment line. |
| `DEPARTMENT_PRESET_CAPABILITIES` | `food_beverage` department exists in [staff/department_catalog.py](staff/department_catalog.py#L42-L46). UNKNOWN whether it carries any preset bundle — no `restaurant_booking.*` caps to bundle. | grep restaurant in catalog → none. |
| Permission classes (`staff/permissions.py`) | Only legacy: `HasRestaurantBookingsNav` (nav-only) and `CanManageRestaurantBookings` (tier-only). No `HasCapability`-derived class for any restaurant-booking action. | [staff/permissions.py](staff/permissions.py#L375), [staff/permissions.py](staff/permissions.py#L418-L420) |
| `nav_catalog.py` | `restaurant_bookings` slug is registered. Nav visibility intact. | [staff/nav_catalog.py](staff/nav_catalog.py#L49) |

Net: the restaurant-booking module is **pre-canonical** — it sits on the legacy `nav + tier` pattern, identical to the state of `room_services` before its refactor (see [docs/audits/rbac_room_services_refactor.md](docs/audits/rbac_room_services_refactor.md) for the destination shape).

---

## 7. Implementation recommendation (no code changes performed)

### 7.1 Module key

`restaurant_bookings` (matches existing nav slug — keeps nav identity stable).

### 7.2 Capability slugs to add to `CANONICAL_CAPABILITIES`

Visibility / module:
- `restaurant_booking.module.view`

Restaurant config (CRUD + soft-delete):
- `restaurant_booking.restaurant.read`
- `restaurant_booking.restaurant.create`
- `restaurant_booking.restaurant.update`
- `restaurant_booking.restaurant.delete`

Booking categories:
- `restaurant_booking.category.read`
- `restaurant_booking.category.manage`

Bookings:
- `restaurant_booking.record.read`
- `restaurant_booking.record.create`
- `restaurant_booking.record.update`
- `restaurant_booking.record.delete`
- `restaurant_booking.record.mark_seen`

Table / blueprint config:
- `restaurant_booking.table.read`
- `restaurant_booking.table.manage`
- `restaurant_booking.blueprint.read`
- `restaurant_booking.blueprint.manage`

Seating workflow:
- `restaurant_booking.assignment.assign`
- `restaurant_booking.assignment.unseat`

(No `approve` / `confirm` capability — no such workflow exists in code.)

### 7.3 `module_policy.py` — `MODULE_POLICY['restaurant_bookings']`

```text
view_capability: restaurant_booking.module.view
read_capability: restaurant_booking.record.read
actions:
  module_view              → restaurant_booking.module.view
  restaurant_read          → restaurant_booking.restaurant.read
  restaurant_create        → restaurant_booking.restaurant.create
  restaurant_update        → restaurant_booking.restaurant.update
  restaurant_delete        → restaurant_booking.restaurant.delete
  category_read            → restaurant_booking.category.read
  category_manage          → restaurant_booking.category.manage
  record_read              → restaurant_booking.record.read
  record_create            → restaurant_booking.record.create
  record_update            → restaurant_booking.record.update
  record_delete            → restaurant_booking.record.delete
  record_mark_seen         → restaurant_booking.record.mark_seen
  table_read               → restaurant_booking.table.read
  table_manage             → restaurant_booking.table.manage
  blueprint_read           → restaurant_booking.blueprint.read
  blueprint_manage         → restaurant_booking.blueprint.manage
  assignment_assign        → restaurant_booking.assignment.assign
  assignment_unseat        → restaurant_booking.assignment.unseat
```

### 7.4 Permission classes to add (in [staff/permissions.py](staff/permissions.py))

All `HasCapability` subclasses (mirrors `room_services` pattern):

- `CanViewRestaurantBookingsModule` (`safe_methods_bypass=False`)
- `CanReadRestaurant`
- `CanCreateRestaurant`, `CanUpdateRestaurant`, `CanDeleteRestaurant`
- `CanReadBookingCategory`, `CanManageBookingCategory`
- `CanReadRestaurantBooking`, `CanCreateRestaurantBooking`, `CanUpdateRestaurantBooking`, `CanDeleteRestaurantBooking`
- `CanMarkRestaurantBookingsSeen`
- `CanReadDiningTable`, `CanManageDiningTable`
- `CanReadRestaurantBlueprint`, `CanManageRestaurantBlueprint`
- `CanAssignRestaurantBooking`, `CanUnseatRestaurantBooking`

Retire (replace with fail-closed stubs, matching `room_services` migration of `CanManageRoomServices`):

- `HasRestaurantBookingsNav` — replaced by `CanViewRestaurantBookingsModule`.
- `CanManageRestaurantBookings` — body becomes a fail-closed deny stub; legacy import sites surface as runtime 403s rather than `ImportError`.

### 7.5 Endpoint mapping

Base chain for all staff endpoints (per `room_services` precedent):
`IsAuthenticated` + `IsStaffMember` + `IsSameHotel` + `CanViewRestaurantBookingsModule` + per-action capability. Unmapped actions → `_DenyAll`.

| Viewset / view | Action | Per-action class |
|---|---|---|
| `BookingViewSet` | list, retrieve | `CanReadRestaurantBooking` |
| | create | `CanCreateRestaurantBooking` |
| | update, partial_update | `CanUpdateRestaurantBooking` |
| | destroy | `CanDeleteRestaurantBooking` |
| `BookingCategoryViewSet` | list, retrieve | `CanReadBookingCategory` |
| | create, update, partial_update, destroy | `CanManageBookingCategory` |
| `RestaurantViewSet` | list, retrieve | `CanReadRestaurant` |
| | create | `CanCreateRestaurant` |
| | update, partial_update | `CanUpdateRestaurant` |
| | destroy | `CanDeleteRestaurant` |
| `RestaurantBlueprintViewSet` | list, retrieve | `CanReadRestaurantBlueprint` (drop `AllowAny`) |
| | create, update, partial_update, destroy | `CanManageRestaurantBlueprint` |
| `DiningTableViewSet` | list, retrieve | `CanReadDiningTable` (drop `AllowAny`) |
| | create, update, partial_update, destroy | `CanManageDiningTable` |
| `BlueprintObjectViewSet` | list, retrieve | `CanReadRestaurantBlueprint` |
| | create, update, partial_update, destroy | `CanManageRestaurantBlueprint` |
| `BlueprintObjectTypeViewSet` | list, retrieve | UNKNOWN — keep `AllowAny` if intended catalog; otherwise `CanReadRestaurantBlueprint`. |
| `mark_bookings_seen` (FBV) | POST | `CanMarkRestaurantBookingsSeen` (decorator-style; remove inline `HasNavPermission(...)` call) |
| `AssignGuestToTableAPIView` | post | `CanAssignRestaurantBooking` |
| `UnseatBookingAPIView` | post | `CanUnseatRestaurantBooking` |
| `DeleteBookingAPIView` | delete | `CanDeleteRestaurantBooking` |

Guest-flow endpoints (`GuestDinnerBookingView`, `AvailableTablesView`) need their own decision: keep `AllowAny` only if a guest-token validator (analogous to `resolve_guest_access` used by `room_services`) is added. Without one, they remain anonymous-writable. UNKNOWN whether such a token exists for restaurant flows.

### 7.6 Preset assignment (proposed bundles)

```text
_RESTAURANT_BOOKING_BASE     = module.view
                              + restaurant.read + category.read
                              + record.read + table.read + blueprint.read

_RESTAURANT_BOOKING_OPERATE  = BASE
                              + record.{create,update,mark_seen}
                              + assignment.{assign,unseat}

_RESTAURANT_BOOKING_MANAGE   = OPERATE
                              + record.delete
                              + restaurant.{create,update,delete}
                              + category.manage
                              + table.manage + blueprint.manage
```

Tier wiring (mirrors `room_services` precedent):

| Tier | Bundle |
|---|---|
| `super_staff_admin` | `_RESTAURANT_BOOKING_MANAGE` |
| `staff_admin` | `_RESTAURANT_BOOKING_MANAGE` |
| `regular_staff` | `_RESTAURANT_BOOKING_BASE` |

Department preset (`food_beverage`): `_RESTAURANT_BOOKING_OPERATE`.

Role presets (in [staff/role_catalog.py](staff/role_catalog.py)):

- `waiter`, `host`, `bartender` → `_RESTAURANT_BOOKING_OPERATE`.
- `fnb_manager` → `_RESTAURANT_BOOKING_MANAGE`.
- `chef` → `_RESTAURANT_BOOKING_BASE` (read-only insight).

These role/department mappings are recommendations derived from the role names; final assignment requires product confirmation.

### 7.7 Ownership / hotel-scope rules

- Keep `IsSameHotel` in the base chain.
- In each viewset's `get_queryset` / `get_object`, retain hotel-slug filtering. Add explicit same-hotel verification inside `perform_create` for any object created from URL kwargs (already present for `RestaurantViewSet`, `DiningTableViewSet`, `BlueprintObjectViewSet`).
- For staff branches that may execute under guest-public mounts (none currently exist for restaurant bookings; `GuestDinnerBookingView` is fully guest), apply the `room_services` `_staff_hotel_matches` pattern if any future endpoint mixes both.

### 7.8 Out-of-scope items not to touch in this refactor

- `frontend/`
- `tests`
- `room_bookings/` and the existing `'bookings'` module-policy entry (room-booking domain).
- `room_services/`.
- Guest path PII redaction in `BookingSerializer` — track separately if needed (not an RBAC concern per se).

---

## 8. Validation commands (post-implementation)

```powershell
python manage.py check
python manage.py shell -c "from staff.module_policy import validate_module_policy; print(validate_module_policy())"
python manage.py shell -c "from staff.capability_catalog import validate_preset_maps; print(validate_preset_maps())"
```

Optionally (alignment with `room_services` audit):

```powershell
python manage.py shell -c "from staff.capability_catalog import CANONICAL_CAPABILITIES; print([c for c in CANONICAL_CAPABILITIES if c.startswith('restaurant_booking.')])"
```

---

## 9. Items marked UNKNOWN (require code-level confirmation before implementation)

1. Whether `BlueprintObjectTypeViewSet` is intentionally `AllowAny` (static catalog) or an oversight.
2. Whether a guest token contract exists for `GuestDinnerBookingView` / `AvailableTablesView` (analogous to `resolve_guest_access` in `room_services`).
3. Whether `mark-seen/` on the staff mount (`bookings/staff_urls.py`) is reachable given the FBV's required `hotel_slug` URL kwarg is missing on that mount.
4. Whether `food_beverage` department currently has any preset capabilities wired (no restaurant-booking caps exist, but other-domain caps may — out of scope to verify here).
5. Whether `BookingSerializer` exposes guest PII fields publicly via `GuestDinnerBookingView.get` — orthogonal to RBAC but relevant to overall risk.

End of audit.
