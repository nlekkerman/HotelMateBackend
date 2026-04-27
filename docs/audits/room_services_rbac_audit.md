# Backend RBAC Audit — `room_services` module

Audit only. No code changes. All claims below are derived from the current
source code referenced inline. Anything not verified in code is marked
`UNKNOWN`.

---

## 1. Files inspected

Real files inspected (room_services + relevant cross-module files):

- [room_services/urls.py](room_services/urls.py)
- [room_services/views.py](room_services/views.py)
- [room_services/staff_views.py](room_services/staff_views.py)
- [room_services/serializers.py](room_services/serializers.py)
- [room_services/models.py](room_services/models.py)
- [room_services/apps.py](room_services/apps.py)
- [staff_urls.py](staff_urls.py)
- [guest_urls.py](guest_urls.py)
- [HotelMateBackend/urls.py](HotelMateBackend/urls.py)
- [staff/permissions.py](staff/permissions.py)
- [staff/capability_catalog.py](staff/capability_catalog.py)
- [staff/module_policy.py](staff/module_policy.py)
- [staff/nav_catalog.py](staff/nav_catalog.py)

Files asked for but **not present** in the module:

- `room_services/staff_urls.py` — does not exist
- `room_services/services.py` — does not exist
- `room_services/permissions.py` — does not exist
- `room_services/policy.py` — does not exist

The module has `signals.py`, `admin.py`, `tests.py`, and a `migrations/`
folder, but no internal services / permissions / policy layer.

---

## 2. Route / endpoint inventory

### 2.1 Mount points (verified from code)

- `HotelMateBackend/urls.py` line 55 mounts the module guest/legacy router:
  - `path('api/room_services/', include('room_services.urls'))`
- `staff_urls.py` registers the **staff CRUD** router on the staff hotel
  router (mounted under `/api/staff/hotel/<hotel_slug>/...`):
  - `r'room-service-items'` → `StaffRoomServiceItemViewSet`
  - `r'breakfast-items'` → `StaffBreakfastItemViewSet`
  - The string `'room_services'` also appears in the `STAFF_APPS` list at
    [staff_urls.py](staff_urls.py#L57) but the project's wrapping pattern
    for that list is not re-confirmed here (the explicit registrations
    above are the verified live mounts).
- `guest_urls.py` re-exposes guest endpoints under `/api/guest/...`:
  - `hotels/<hotel_slug>/room-services/orders/` →
    `OrderViewSet.as_view({'get': 'room_order_history', 'post': 'create'})`
  - `hotels/<hotel_slug>/room/<room_number>/menu/` →
    `RoomServiceItemViewSet.as_view({'get': 'menu'})`

### 2.2 Endpoints from `room_services/urls.py` (mounted at `/api/room_services/`)

| HTTP | URL path | View | Action | permission_classes (effective) | Serializer | Model/touched |
|------|----------|------|--------|--------------------------------|------------|---------------|
| GET | `<hotel_slug>/room/<room_number>/menu/` | `RoomServiceItemViewSet` | `menu` | `[AllowAny]` (class-level) | `RoomServiceItemSerializer` | `RoomServiceItem` |
| GET | `<hotel_slug>/room/<room_number>/breakfast/` | `BreakfastItemViewSet` | `menu` | `[AllowAny]` (class-level) | `BreakfastItemSerializer` | `BreakfastItem` |
| POST | `<hotel_slug>/room/<room_number>/save-fcm-token/` | `save_guest_fcm_token` (FBV) | n/a | `@permission_classes([AllowAny])`; guest token validated in body via `resolve_guest_access` | n/a | `Room.guest_fcm_token` |
| GET | `<hotel_slug>/orders/` | `OrderViewSet` | `list` | `IsAuthenticated + HasNavPermission('room_services') + IsStaffMember + IsSameHotel` | `OrderSerializer` | `Order` |
| POST | `<hotel_slug>/orders/` | `OrderViewSet` | `create` | `[AllowAny]` (per-action override; guest token validated in `perform_create`; staff bypass via `_is_staff_request`) | `OrderSerializer` | `Order`, `OrderItem` |
| GET | `<hotel_slug>/orders/<pk>/` | `OrderViewSet` | `retrieve` | staff read gate (see above) | `OrderSerializer` | `Order` |
| PUT | `<hotel_slug>/orders/<pk>/` | `OrderViewSet` | `update` | staff mutation gate: read gate + `CanManageRoomServices` | `OrderSerializer` | `Order` |
| PATCH | `<hotel_slug>/orders/<pk>/` | `OrderViewSet` | `partial_update` | staff mutation gate: read gate + `CanManageRoomServices` (custom status-transition validator in body) | `OrderSerializer` | `Order` |
| DELETE | `<hotel_slug>/orders/<pk>/` | `OrderViewSet` | `destroy` | staff mutation gate: read gate + `CanManageRoomServices` | `OrderSerializer` | `Order` |
| GET | `<hotel_slug>/orders/all-orders-summary/` | `OrderViewSet` | `all_orders_summary` | staff read gate | `OrderSerializer` | `Order` |
| GET | `<hotel_slug>/orders/order-history/` | `OrderViewSet` | `order_history` | staff read gate | `OrderSerializer` | `Order` |
| GET | `<hotel_slug>/orders/pending-count/` | `OrderViewSet` | `pending_count` | staff read gate | n/a (count) | `Order` |
| GET | `<hotel_slug>/orders/pending-count.<format>/` | `OrderViewSet` | `pending_count` | staff read gate | n/a | `Order` |
| GET | `<hotel_slug>/breakfast-orders/` | `BreakfastOrderViewSet` | `list` | staff read gate (same shape as `OrderViewSet`) | `BreakfastOrderSerializer` | `BreakfastOrder` |
| POST | `<hotel_slug>/breakfast-orders/` | `BreakfastOrderViewSet` | `create` | `[AllowAny]` (guest token in `perform_create`; staff bypass) | `BreakfastOrderSerializer` | `BreakfastOrder`, `BreakfastOrderItem` |
| GET | `<hotel_slug>/breakfast-orders/<pk>/` | `BreakfastOrderViewSet` | `retrieve` | staff read gate | `BreakfastOrderSerializer` | `BreakfastOrder` |
| PUT | `<hotel_slug>/breakfast-orders/<pk>/` | `BreakfastOrderViewSet` | `update` | staff mutation gate + `CanManageRoomServices` | `BreakfastOrderSerializer` | `BreakfastOrder` |
| PATCH | `<hotel_slug>/breakfast-orders/<pk>/` | `BreakfastOrderViewSet` | `partial_update` | staff mutation gate + `CanManageRoomServices` (custom transition validator) | `BreakfastOrderSerializer` | `BreakfastOrder` |
| DELETE | `<hotel_slug>/breakfast-orders/<pk>/` | `BreakfastOrderViewSet` | `destroy` | staff mutation gate + `CanManageRoomServices` | `BreakfastOrderSerializer` | `BreakfastOrder` |
| GET | `<hotel_slug>/breakfast-orders/breakfast-pending-count/` | `BreakfastOrderViewSet` | `pending_count` | staff read gate | n/a | `BreakfastOrder` |

Additionally, the file registers `router = DefaultRouter()` with
`router.register(r'orders', OrderViewSet, basename='order')` and
`path('', include(router.urls))`. This exposes a **second** non-hotel-scoped
`/api/room_services/orders/...` route family. Because `OrderViewSet`
mutation/read paths derive the hotel from `hotel_slug` via
`get_hotel_from_request` — which raises `Http404("Hotel slug not provided")`
when the URL kwarg is missing — these routes appear non-functional for any
action that needs the hotel. They are still **routable** and must be
accounted for (see §5).

The `room_order_history` action exists on `OrderViewSet` (`url_path="room-history"`)
but is **not routed in `room_services/urls.py`**. It is exposed only via
`guest_urls.py` at `/api/guest/hotels/<hotel_slug>/room-services/orders/`
(GET dispatch).

### 2.3 Endpoints from `staff_urls.py` (mounted under `/api/staff/hotel/<hotel_slug>/`)

`StaffRoomServiceItemViewSet` registered at `room-service-items`:

| HTTP | URL path | Action | permission_classes | Serializer | Model |
|------|----------|--------|--------------------|------------|-------|
| GET | `room-service-items/` | `list` | `[IsAuthenticated, HasRoomServicesNav, IsStaffMember, IsSameHotel]` | `RoomServiceItemStaffSerializer` | `RoomServiceItem` |
| POST | `room-service-items/` | `create` | same as above | same | `RoomServiceItem` |
| GET | `room-service-items/<pk>/` | `retrieve` | same | same | `RoomServiceItem` |
| PUT | `room-service-items/<pk>/` | `update` | same | same | `RoomServiceItem` |
| PATCH | `room-service-items/<pk>/` | `partial_update` | same | same | `RoomServiceItem` |
| DELETE | `room-service-items/<pk>/` | `destroy` | same | same | `RoomServiceItem` |
| POST | `room-service-items/<pk>/upload-image/` | `upload_image` | same | same | `RoomServiceItem.image` |

`StaffBreakfastItemViewSet` registered at `breakfast-items` — identical
shape, with `BreakfastItem` and `BreakfastItemStaffSerializer`.

### 2.4 Effective `OrderViewSet` / `BreakfastOrderViewSet` permission dispatch

From `room_services/views.py`:

- `_GUEST_ACTIONS = {'create', 'room_order_history'}` for `OrderViewSet`
  and `{'create'}` for `BreakfastOrderViewSet`.
- `get_permissions()`:
  - if action in `_GUEST_ACTIONS` → `[AllowAny]`
  - else if `request.method` not in `('GET', 'HEAD', 'OPTIONS')` →
    `[IsAuthenticated, HasNavPermission('room_services'), IsStaffMember, IsSameHotel, CanManageRoomServices]`
  - else → `[IsAuthenticated, HasNavPermission('room_services'), IsStaffMember, IsSameHotel]`

---

## 3. Current authority checks

| Endpoint group | Auth | Staff check | Same-hotel | Nav slug | Role string | Tier / access_level | Inline custom | Missing |
|----------------|------|-------------|------------|----------|-------------|---------------------|---------------|---------|
| Guest menu (`RoomServiceItemViewSet.menu`, `BreakfastItemViewSet.menu`) | `AllowAny` | — | hotel resolved by slug only; no per-room scope | — | — | — | — | No guest-token check; intentional — guest browsing |
| `save_guest_fcm_token` | `AllowAny` | — | yes (URL room must equal token-derived room) | — | — | — | `resolve_guest_access(token, scopes=['ROOM_SERVICE'], require_in_house=True)`; URL room_number equality check | None at this endpoint |
| `OrderViewSet.create` (guest path) | `AllowAny` | — | hotel from URL slug | — | — | — | `resolve_guest_access(...)`; client-supplied `room_number` overridden by token-derived room | none for guest path |
| `OrderViewSet.create` (staff bypass) | `_is_staff_request` only (truthy `staff_profile`) | implicit via `staff_profile` | **no `IsSameHotel`/hotel match** at the staff-bypass branch | — | — | — | hotel set from URL slug, not from `staff.hotel` | **Cross-hotel staff write possible**: any authenticated staff with a `staff_profile` can POST an order to any hotel slug |
| `OrderViewSet.list/retrieve/summary/history/pending_count` | `IsAuthenticated` | `IsStaffMember` | `IsSameHotel` | `HasNavPermission('room_services')` | — | — | — | None for read gate |
| `OrderViewSet.partial_update` (status transitions) | `IsAuthenticated` | `IsStaffMember` | `IsSameHotel` | `HasNavPermission('room_services')` | — | tier ≥ `staff_admin` via `CanManageRoomServices` | inline `valid_transitions` dict (`pending → accepted → completed`) | **`regular_staff` (e.g. porter, kitchen) cannot accept/complete orders**; tier-only gate; no per-transition or fulfill-role capability |
| `OrderViewSet.update / destroy` | as above | as above | as above | as above | — | tier ≥ `staff_admin` | — | None inside the gate; but DELETE has no business rule |
| `BreakfastOrderViewSet.*` | mirror of `OrderViewSet` | — | `IsSameHotel` | `HasNavPermission('room_services')` | — | tier ≥ `staff_admin` for mutations | inline transition validator | Same `regular_staff` gap as orders |
| `room_order_history` (via guest_urls) | `AllowAny` | n/a (staff bypass possible via query params) | hotel from query / URL | — | — | — | guest token resolver, OR staff path requires `room_number` query param | **Staff path** has no `IsSameHotel` / nav / staff check; any authenticated user with `staff_profile` may read any hotel's room history (and the action treats them as staff) |
| `StaffRoomServiceItemViewSet.*`, `StaffBreakfastItemViewSet.*` (incl. `upload_image`) | `IsAuthenticated` | `IsStaffMember` | `IsSameHotel` | `HasRoomServicesNav` (= `HasNavPermission('room_services')`) | — | — | `perform_create` forces `hotel = staff.hotel` | **No `CanManageRoomServices`**: any nav-visible staff (e.g. `regular_staff` whose role/overrides include `room_services`) can create / update / delete menu items and upload images |

`HasNavPermission` is module visibility only — it never grants mutation
authority (per its own docstring). `CanManageRoomServices.has_permission`
short-circuits to `True` for `GET/HEAD/OPTIONS` and otherwise requires
`tier ≥ staff_admin` from `resolve_tier(request.user)`.

---

## 4. Action surface

Derived strictly from live endpoints / actions in code:

**Module visibility**

- See / navigate the room-services module (nav slug `room_services`)

**Menu — read (guest)**

- Read room-service item menu for a hotel/room
- Read breakfast item menu for a hotel/room

**Menu — manage (staff)**

- List room-service items (staff scope)
- Create room-service item
- Update room-service item
- Delete room-service item
- Upload / set room-service item image
- List breakfast items (staff scope)
- Create breakfast item
- Update breakfast item
- Delete breakfast item
- Upload / set breakfast item image

**Orders — guest**

- Create room-service order (guest token, `ROOM_SERVICE` scope)
- Read own room's order history (guest token)
- Save guest FCM token for the token-derived room

**Orders — staff (room-service)**

- List orders for hotel (excludes `completed`)
- Retrieve order detail
- Read all-orders summary (paginated, with status breakdown)
- Read order history (`completed` orders, paginated)
- Read pending-count
- Create order on behalf of guest (staff bypass)
- Update order (full PUT)
- Update order status (`pending → accepted`, `accepted → completed`)
- Delete order

**Orders — staff (breakfast)**

- List breakfast orders (`pending` + `accepted`)
- Retrieve breakfast order detail
- Read breakfast pending-count
- Create breakfast order on behalf of guest (staff bypass)
- Update breakfast order (full PUT)
- Update breakfast order status (`pending → accepted → completed`)
- Delete breakfast order

**Notification routing (already capability-modeled, no endpoint)**

- Receive porter-routed room-service order pings
  (`room_service.order.fulfill_porter`, defined in capability catalog,
  not enforced at any room_services endpoint)
- Receive kitchen-routed room-service order pings
  (`room_service.order.fulfill_kitchen`, same status)

---

## 5. RBAC gap table

| Endpoint | Current gate | Missing gate | Proposed capability | Risk |
|---|---|---|---|---|
| `RoomServiceItemViewSet.menu`, `BreakfastItemViewSet.menu` | `AllowAny` | (intentional public read) — but no rate limiting at view level beyond DRF defaults | n/a (keep public) | Low; menu data is public |
| `save_guest_fcm_token` | `AllowAny` + token resolver | None functional; no capability needed (guest path) | n/a | Low |
| `OrderViewSet.create` (staff bypass branch) | `_is_staff_request` only — no `IsSameHotel`, no nav, no manage capability | hotel-scope check; capability gate | `room_service.order.create` + `IsSameHotel` | **High**: cross-hotel write by any authenticated staff |
| `OrderViewSet.list/retrieve` | `Authenticated + nav + staff + same-hotel` | capability gate | `room_service.order.read` | Medium: any staff with nav can read orders, regardless of department |
| `OrderViewSet.all_orders_summary`, `order_history`, `pending_count` | as above | capability gate | `room_service.order.read` (or dedicated `room_service.order.history.read`) | Medium |
| `OrderViewSet.update / destroy` | nav + staff + same-hotel + `tier ≥ staff_admin` | capability gate; destroy hard-gate | `room_service.order.update`, `room_service.order.delete` | Medium |
| `OrderViewSet.partial_update` (status transition) | nav + staff + same-hotel + `tier ≥ staff_admin` + inline FSM | capability gate; per-transition (accept vs. complete) | `room_service.order.accept`, `room_service.order.complete` (or single `room_service.order.transition`) | **High**: front-desk / porter / kitchen `regular_staff` cannot operate orders today; tier wall blocks operational staff |
| `BreakfastOrderViewSet.*` (mirror) | mirror of order gates | mirror of capability gates | `room_service.breakfast_order.read`, `.create`, `.update`, `.delete`, `.accept`, `.complete` (or shared with orders) | Medium / High (same operate gap) |
| `OrderViewSet.room_order_history` (staff query-param branch via guest_urls) | `AllowAny` + `_is_staff_request` truthy + `room_number` query param | `IsAuthenticated`, `IsSameHotel`, capability gate | `room_service.order.read` | **High**: any authenticated user with `staff_profile` can read any hotel's room order history |
| `OrderViewSet.partial_update` inline FSM | hardcoded transitions; no capability per transition | refactor to capability-checked transitions OR keep inline but capability-gate the call | `room_service.order.accept`, `room_service.order.complete` | Medium |
| `StaffRoomServiceItemViewSet` / `StaffBreakfastItemViewSet` CRUD + `upload_image` | nav + staff + same-hotel — **no `CanManageRoomServices`** | manage-capability gate | `room_service.menu.item.read`, `.create`, `.update`, `.delete`, `.image_manage` (or single `room_service.menu.manage`) | **High**: nav-visible operational staff can mutate menu / prices / stock |
| Default-router `OrderViewSet` mounted at `/api/room_services/orders/...` | inherits `OrderViewSet` permissions; guest `create` is `AllowAny` and uses `get_hotel_from_request` which 404s without `hotel_slug` | confirm or remove; surface duplication is a footgun | n/a (route hygiene) | Low–Medium: redundant route surface |

Note: the existing capabilities `ROOM_SERVICE_ORDER_FULFILL_PORTER` /
`ROOM_SERVICE_ORDER_FULFILL_KITCHEN` (in `staff/capability_catalog.py`)
are **routing/eligibility flags** for notifications, not authority — per
their own docstrings. They do not gate any endpoint and should not be
proposed as the authority gate.

---

## 6. Capability / registry status

Verified against current code:

- `staff/capability_catalog.py`:
  - **No** `room_service.module.view`
  - **No** `room_service.menu.*` capabilities
  - **No** `room_service.order.*` capabilities for read / create / update /
    accept / complete / cancel / delete
  - Only `ROOM_SERVICE_ORDER_FULFILL_PORTER` and
    `ROOM_SERVICE_ORDER_FULFILL_KITCHEN` exist (defined ~line 167–175,
    listed in `CANONICAL_CAPABILITIES` and granted by the
    `front_desk_agent` role preset and `kitchen` department preset
    respectively).
- `staff/module_policy.py`:
  - `MODULE_POLICY` contains: `attendance`, `bookings`, `chat`, `guests`,
    `hotel_info`, `rooms`, `staff_chat`, `housekeeping`, `maintenance`,
    `staff_management`. **`room_services` is absent.** The header comment
    explicitly lists `room_services` as a future pass.
- `staff/permissions.py`:
  - `HasRoomServicesNav` (nav-only) and `CanManageRoomServices`
    (tier ≥ `staff_admin`) exist; both are **non-capability** gates.
  - `'room_services'` appears in `TIER_DEFAULT_NAVS['super_staff_admin']`
    only (not `staff_admin` or `regular_staff`).
- `staff/nav_catalog.py`:
  - `'room_services'` is a canonical nav slug and is registered as a nav
    item (line 84).
- Preset bundles:
  - No role / department preset grants any `room_service.menu.*` or
    `room_service.order.*` capability beyond the two notification-routing
    flags.

Conclusion: room_services has **zero** authority capabilities. It is gated
by tier (`CanManageRoomServices`) plus nav visibility, plus an ad-hoc
`_is_staff_request` truthy check inside `perform_create` and inside
`room_order_history`.

---

## 7. Implementation recommendation (no implementation performed)

### 7.1 Module name

`room_services` (matches app label, nav slug, `staff_urls.py` `STAFF_APPS`
entry, and the existing `HasNavPermission('room_services')` callsite).

### 7.2 Capabilities to add to `staff/capability_catalog.py`

Following the `domain.resource.action` convention used elsewhere
(`booking.record.read`, `housekeeping.task.execute`, etc.):

Module + menu:

- `room_service.module.view`
- `room_service.menu.read`
- `room_service.menu.item.create`
- `room_service.menu.item.update`
- `room_service.menu.item.delete`
- `room_service.menu.item.image_manage`

Orders (room-service):

- `room_service.order.read`
- `room_service.order.create`            (staff-on-behalf-of-guest)
- `room_service.order.update`            (full PUT — destructive edit)
- `room_service.order.delete`
- `room_service.order.accept`            (`pending → accepted`)
- `room_service.order.complete`          (`accepted → completed`)

Breakfast orders (decision point: share with `order.*` or split):

- Recommended: split, mirroring orders, since the model is distinct:
  - `room_service.breakfast_order.read`
  - `room_service.breakfast_order.create`
  - `room_service.breakfast_order.update`
  - `room_service.breakfast_order.delete`
  - `room_service.breakfast_order.accept`
  - `room_service.breakfast_order.complete`

Keep existing routing capabilities as-is:

- `room_service.order.fulfill_porter` (already present)
- `room_service.order.fulfill_kitchen` (already present)

All new capabilities must be added to `CANONICAL_CAPABILITIES` and granted
by at least one preset (otherwise `validate_module_policy` /
`validate_preset_maps` will reject them).

### 7.3 Preset bundle wiring (recommended starting allocation, code-derived)

- Tier `super_staff_admin`: full `room_service.*` manage bundle
  (matches `TIER_DEFAULT_NAVS` already including `room_services` only at
  this tier).
- Role `hotel_manager`: full `room_service.*` manage bundle (mirrors
  existing pattern where `hotel_manager` aggregates manage bundles for
  bookings, rooms, housekeeping, maintenance, staff_management,
  hotel_info, attendance).
- Role `front_desk_agent` / department `front_office`:
  `room_service.module.view`, `room_service.menu.read`,
  `room_service.order.read`, `room_service.order.create`,
  `room_service.order.accept`, `room_service.order.complete`
  (front-desk takes orders on behalf of guests and accepts/completes).
- Department `kitchen`: `room_service.module.view`,
  `room_service.order.read`, `room_service.order.accept`,
  `room_service.order.complete`, plus `room_service.breakfast_order.*`
  operate set. (Already carries `room_service.order.fulfill_kitchen`
  for routing.)
- Porter role (verify exact slug from `staff/role_catalog.py` —
  `UNKNOWN` from current read): operate bundle (`order.read`, `accept`,
  `complete`); already carries `room_service.order.fulfill_porter` as a
  routing flag.

`regular_staff` tier should **not** receive any `room_service.*`
capability by tier; authority must come exclusively from role/department
presets, mirroring Phase 6A pattern.

### 7.4 Permission classes needed

- `CanReadRoomServices(HasCapability)` → `room_service.order.read`
  (or compose per-action zero-arg subclasses, as bookings/maintenance do).
- `CanManageRoomServiceMenu(HasCapability)` → resource-specific
  capability (different per action via `get_permissions`).
- `CanCreateRoomServiceOrder`, `CanAcceptRoomServiceOrder`,
  `CanCompleteRoomServiceOrder`, `CanUpdateRoomServiceOrder`,
  `CanDeleteRoomServiceOrder` → analogous per-action gates.
- Mirror set for `breakfast_order.*`.
- Retire `CanManageRoomServices` (tier-based) once endpoints migrate.

`HasCapability` already exists in `staff/permissions.py` — follow the
booking / housekeeping migration pattern.

### 7.5 Endpoint mapping (proposed)

| Endpoint | New permissions |
|---|---|
| `RoomServiceItemViewSet.menu`, `BreakfastItemViewSet.menu` | unchanged (`AllowAny`) |
| `save_guest_fcm_token` | unchanged (`AllowAny` + token resolver) |
| `OrderViewSet.list/retrieve/all_orders_summary/order_history/pending_count` | `IsAuthenticated, IsStaffMember, IsSameHotel, HasCapability('room_service.order.read')` |
| `OrderViewSet.create` (staff bypass) | branch keeps `AllowAny` for guest token path; **add** `IsSameHotel` + `HasCapability('room_service.order.create')` for the staff branch (e.g. via explicit check inside `perform_create`, or split into a staff-only endpoint) |
| `OrderViewSet.partial_update` | route to `room_service.order.accept` for `pending → accepted`, `room_service.order.complete` for `accepted → completed`; reject otherwise |
| `OrderViewSet.update` | `HasCapability('room_service.order.update')` |
| `OrderViewSet.destroy` | `HasCapability('room_service.order.delete')` |
| `OrderViewSet.room_order_history` (staff branch via guest_urls) | require `IsAuthenticated + IsStaffMember + IsSameHotel + HasCapability('room_service.order.read')`; do **not** trust `_is_staff_request` alone |
| `BreakfastOrderViewSet.*` | mirror, using `room_service.breakfast_order.*` |
| `StaffRoomServiceItemViewSet.list/retrieve` | `... + HasCapability('room_service.menu.read')` |
| `StaffRoomServiceItemViewSet.create` | `... + HasCapability('room_service.menu.item.create')` |
| `StaffRoomServiceItemViewSet.update/partial_update` | `... + HasCapability('room_service.menu.item.update')` |
| `StaffRoomServiceItemViewSet.destroy` | `... + HasCapability('room_service.menu.item.delete')` |
| `StaffRoomServiceItemViewSet.upload_image` | `... + HasCapability('room_service.menu.item.image_manage')` |
| `StaffBreakfastItemViewSet.*` | identical, same capabilities (menu items share the bundle) |

### 7.6 Ownership / hotel-scope rules

Code-derived rules to preserve:

- All staff endpoints must enforce `IsSameHotel` against the URL
  `hotel_slug`. The `OrderViewSet.create` staff-bypass currently uses
  `get_hotel_from_request(self.request)` (URL slug) without
  cross-checking `staff.hotel`; this must be tightened.
- `StaffRoomServiceItemViewSet.perform_create` / `StaffBreakfastItemViewSet.perform_create`
  already force `hotel = staff.hotel`. Keep that.
- Guest path: `resolve_guest_access(token, hotel_slug=hotel.slug, required_scopes=['ROOM_SERVICE'], require_in_house=True)`
  is the canonical guest gate — keep verbatim. The room is always
  derived from the token, never trusted from the URL/body
  (already enforced in `OrderViewSet.perform_create`).
- `save_guest_fcm_token` keeps the token-vs-URL `room_number`
  equality check.
- Module policy entry must register `room_services` in
  `MODULE_POLICY` (currently absent — see §6).

### 7.7 `MODULE_POLICY` entry (proposed, for the frontend contract)

```python
'room_services': {
    'view_capability': ROOM_SERVICE_MODULE_VIEW,
    'read_capability': ROOM_SERVICE_ORDER_READ,
    'actions': {
        'menu_read': ROOM_SERVICE_MENU_READ,
        'menu_item_create': ROOM_SERVICE_MENU_ITEM_CREATE,
        'menu_item_update': ROOM_SERVICE_MENU_ITEM_UPDATE,
        'menu_item_delete': ROOM_SERVICE_MENU_ITEM_DELETE,
        'menu_item_image_manage': ROOM_SERVICE_MENU_ITEM_IMAGE_MANAGE,
        'order_read': ROOM_SERVICE_ORDER_READ,
        'order_create': ROOM_SERVICE_ORDER_CREATE,
        'order_update': ROOM_SERVICE_ORDER_UPDATE,
        'order_delete': ROOM_SERVICE_ORDER_DELETE,
        'order_accept': ROOM_SERVICE_ORDER_ACCEPT,
        'order_complete': ROOM_SERVICE_ORDER_COMPLETE,
        'breakfast_order_read': ROOM_SERVICE_BREAKFAST_ORDER_READ,
        'breakfast_order_create': ROOM_SERVICE_BREAKFAST_ORDER_CREATE,
        'breakfast_order_update': ROOM_SERVICE_BREAKFAST_ORDER_UPDATE,
        'breakfast_order_delete': ROOM_SERVICE_BREAKFAST_ORDER_DELETE,
        'breakfast_order_accept': ROOM_SERVICE_BREAKFAST_ORDER_ACCEPT,
        'breakfast_order_complete': ROOM_SERVICE_BREAKFAST_ORDER_COMPLETE,
        # Routing flags — surface for frontend filtering, not authority:
        'fulfill_porter': ROOM_SERVICE_ORDER_FULFILL_PORTER,
        'fulfill_kitchen': ROOM_SERVICE_ORDER_FULFILL_KITCHEN,
    },
},
```

### 7.8 Migration order (no implementation here)

1. Add capability slugs to `staff/capability_catalog.py` and grow
   `CANONICAL_CAPABILITIES`.
2. Add `room_services` entry to `MODULE_POLICY`.
3. Allocate to `ROLE_PRESET_CAPABILITIES` /
   `DEPARTMENT_PRESET_CAPABILITIES`.
4. Introduce zero-arg `HasCapability` subclasses (or use `HasCapability('slug')`).
5. Migrate `OrderViewSet.get_permissions`, `BreakfastOrderViewSet.get_permissions`,
   `StaffRoomServiceItemViewSet`, `StaffBreakfastItemViewSet`.
6. Tighten `OrderViewSet.create` staff bypass (hotel-scope) and
   `OrderViewSet.room_order_history` staff branch.
7. Decide on `room_services/urls.py` default-router duplicate route surface.
8. Retire `CanManageRoomServices` once no callsite remains.

---

## 8. Validation commands

To run after implementation (not now — audit only):

```bash
python manage.py check
python manage.py shell -c "from staff.module_policy import validate_module_policy; print(validate_module_policy())"
python manage.py shell -c "from staff.capability_catalog import validate_preset_maps; print(validate_preset_maps())"
```

Suggested additional sanity checks consistent with prior phases:

```bash
python manage.py test room_services
python manage.py shell -c "from staff.permissions import resolve_effective_access; from django.contrib.auth import get_user_model; U=get_user_model(); print(resolve_effective_access(U.objects.first()))"
```
