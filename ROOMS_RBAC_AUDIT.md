# Rooms RBAC Audit & Design

**Scope:** Rooms module — inventory (`Room`), room types (`RoomType`), room
status/turnover, maintenance flags, out-of-order, inspection/readiness, room
media (`RoomImage`, room-type photo).
**Out of scope:** `room_bookings` lifecycle, `housekeeping` workflow (except
status touches that originate in the rooms app), `maintenance` requests app,
public page display.
**Source of truth:** `rooms/views.py`, `rooms/urls.py`, `rooms/staff_urls.py`,
`hotel/staff_views.py`, `hotel/urls.py`, `staff_urls.py`,
`staff/permissions.py`, `staff/capability_catalog.py`.
**Reference module:** `room_bookings` (Phase 6A) — capability-based,
`CanViewBookings + CanReadBookings + Can<Action>` chains, no tier authority.

---

## 1. Endpoint Inventory

All paths are reachable (router-mounted) unless marked **DEAD**. `{slug}` =
`hotel_slug`; `{rt}` = room_type_id; `{rn}` = room_number; `{id}` = pk.

| # | Endpoint | View | Method | Current Permissions | Classification |
|---|---|---|---|---|---|
| 1 | `/api/staff/hotel/{slug}/room-management/` | `rooms.views.StaffRoomViewSet` | GET/POST/PUT/PATCH/DELETE | `IsAuthenticated + HasNavPermission('rooms') + IsStaffMember + IsSameHotel` (+ `CanManageRooms` on writes) | inventory CRUD |
| 2 | `/api/staff/hotel/{slug}/room-management/{rn}/` | `StaffRoomViewSet` detail | GET/PUT/PATCH/DELETE | same | inventory CRUD |
| 3 | `/api/staff/hotel/{slug}/hotel/staff/rooms/` | `hotel.staff_views.StaffRoomViewSet` | GET/POST/PUT/PATCH/DELETE | `IsAuthenticated + HasNavPermission('rooms') + IsStaffMember + IsSameHotel` (+ `CanManageRooms` on writes) | inventory CRUD — **DUPLICATE** of #1 |
| 4 | `/api/staff/hotel/{slug}/hotel/staff/rooms/{id}/generate_pin/` | `StaffRoomViewSet.generate_pin` | POST | same | deprecated (returns 400) — **DEAD** |
| 5 | `/api/staff/hotel/{slug}/hotel/staff/rooms/{id}/generate_qr/` | `StaffRoomViewSet.generate_qr` | POST | same | QR generation (room_service/breakfast/chat_pin/restaurant) |
| 6 | `/api/staff/hotel/{slug}/room-types/` | `hotel.staff_views.StaffRoomTypeViewSet` | GET/POST/PUT/PATCH/DELETE | `IsAuthenticated + HasNavPermission('rooms') + IsStaffMember + IsSameHotel` (+ `CanManageRooms` on writes) | room-type CRUD |
| 7 | `/api/staff/hotel/{slug}/hotel/staff/room-types/` | same class | same | same | **DUPLICATE** of #6 |
| 8 | `/api/staff/hotel/{slug}/room-types/{id}/upload-image/` | `StaffRoomTypeViewSet.upload_image` | POST | same | room-type media |
| 9 | `/api/staff/hotel/{slug}/room-types/{rt}/rooms/bulk-create/` | `rooms.views.bulk_create_rooms` | POST | `IsAuthenticated + IsStaffMember + IsSameHotel` + inline `HasNavPermission('rooms')` + inline `CanManageRooms` | bulk inventory create |
| 10 | `/api/staff/hotel/{slug}/rooms/checkout/` | `rooms.views.checkout_rooms` | POST | `IsAuthenticated + IsStaffMember + IsSameHotel` + inline `HasNavPermission('rooms')` + inline `CanManageRooms` + inline `is_superuser` (if destructive) | bulk checkout (non-destructive + nuclear) |
| 11 | `/api/staff/hotel/{slug}/rooms/{rn}/start-cleaning/` | `start_cleaning` | POST | `IsAuthenticated + IsStaffMember + IsSameHotel` + inline `HasNavPermission('rooms')` | status transition |
| 12 | `/api/staff/hotel/{slug}/rooms/{rn}/mark-cleaned/` | `mark_cleaned` | POST | same | status transition |
| 13 | `/api/staff/hotel/{slug}/rooms/{rn}/inspect/` | `inspect_room` | POST | same | inspection / readiness |
| 14 | `/api/staff/hotel/{slug}/rooms/{rn}/mark-maintenance/` | `mark_maintenance` | POST | `IsAuthenticated + IsStaffMember + IsSameHotel` + inline `HasNavPermission('maintenance')` | maintenance flag set |
| 15 | `/api/staff/hotel/{slug}/rooms/{rn}/complete-maintenance/` | `complete_maintenance` | POST | same (maintenance nav) | maintenance flag clear |
| 16 | `/api/staff/hotel/{slug}/turnover/rooms/` | `turnover_rooms` | GET | `IsAuthenticated + IsStaffMember + IsSameHotel` + inline `HasNavPermission('rooms')` | dashboard read |
| 17 | `/api/staff/hotel/{slug}/turnover/stats/` | `turnover_stats` | GET | same | dashboard read |
| 18 | `/api/staff/hotel/{slug}/room-images/` | `rooms.views.RoomImageViewSet` | GET/POST/PUT/PATCH/DELETE | `IsAuthenticated + HasNavPermission('rooms') + IsStaffMember + IsSameHotel` (+ `CanManageRooms` on writes) | room media CRUD |
| 19 | `/api/staff/hotel/{slug}/room-images/bulk-upload/` | `RoomImageViewSet.bulk_upload` | POST | same | room media bulk |
| 20 | `/api/staff/hotel/{slug}/room-images/reorder/` | `RoomImageViewSet.reorder` | POST | same | room media ordering |
| 21 | `/api/staff/hotel/{slug}/room-images/{id}/set-cover/` | `RoomImageViewSet.set_cover` | POST | same | room media cover |
| D1 | `rooms/urls.py → router 'rooms'` | `rooms.views.RoomViewSet` (read-only) | GET | `IsAuthenticated + HasRoomsNav + IsStaffMember + IsSameHotel` | **DEAD** — `rooms/urls.py` is not `include()`-d anywhere |
| D2 | `rooms/urls.py → {slug}/rooms/{rn}/add-guest/` | `AddGuestToRoomView` | POST | `…+ CanManageRooms` | **DEAD** — same |
| D3 | `rooms/urls.py → {slug}/rooms/{rn}/` | `RoomByHotelAndNumberView` | GET | `IsAuthenticated + HasRoomsNav + IsStaffMember + IsSameHotel` | **DEAD** — same |
| D4 | `rooms/urls.py → {slug}/checkout/` | `checkout_rooms` | POST | same as #10 | **DEAD** — duplicate route definition (live one is in `rooms/staff_urls.py`) |
| D5 | `rooms/urls.py → {slug}/checkout-needed/` | `checkout_needed` | GET | `IsAuthenticated + IsStaffMember + IsSameHotel` + inline `HasNavPermission('rooms')` | **DEAD** — not mounted |
| D6 | legacy `RoomTypeViewSet` in `rooms/views.py` (read-only) | `rooms.views.RoomTypeViewSet` | GET | `IsAuthenticated + HasRoomsNav + IsStaffMember + IsSameHotel` | **DEAD** — no router registration |

Verified non-routing of `rooms/urls.py`: a workspace-wide grep for
`include('rooms.urls')` / `include("rooms.urls")` returns zero hits; only
`rooms.staff_urls` is ever included (by `staff_urls.py`).

---

## 2. Current Security Issues

### 2.1 No capability model exists for rooms
`staff/capability_catalog.py` defines no `room.*` slugs. Every write in the
rooms module is gated exclusively by:
- `HasNavPermission('rooms')` — nav-based visibility, not authority
- `CanManageRooms` — tier check `_tier_at_least(tier, 'super_staff_admin')`

There is literally nothing between "nav visible" and "tier is
super_staff_admin". No operate bucket, no supervise bucket, no
capability-class gate. This is the exact pre-Phase-6A pattern the bookings
module retired.

### 2.2 Tier leak — `CanManageRooms` is tier-based authority
`staff/permissions.py` line 361:
```
class CanManageRooms(BasePermission):
    def has_permission(self, request, view):
        if request.method in ('GET','HEAD','OPTIONS'): return True
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'super_staff_admin')
```
Tier is the sole authority. A regular_staff or staff_admin housekeeper has no
path to create/update a room, set maintenance flags (via the viewset path),
upload media, or bulk-create — even if their role preset would logically
cover some of these actions. This is bucket-via-tier.

### 2.3 Nav-based security used as the *only* gate on write endpoints
In `checkout_rooms`, `bulk_create_rooms`, `start_cleaning`, `mark_cleaned`,
`inspect_room`, `mark_maintenance`, `complete_maintenance`, `turnover_rooms`,
`turnover_stats`, the *only* per-action check beyond membership is an inline
`HasNavPermission(...)`. Turnover transitions (11–15) have zero authority
gate beyond nav — any authenticated staff member of the same hotel with the
`rooms` nav item can drive the full turnover state machine, and with the
`maintenance` nav item can flip `MAINTENANCE_REQUIRED`. Nav is not auth.

### 2.4 Cross-domain nav leakage
`mark_maintenance` / `complete_maintenance` live in the rooms module but
gate on `HasNavPermission('maintenance')`. This couples rooms-module write
authority to a foreign nav slug. A staff member with `maintenance` nav but
no `rooms` nav can transition room status to `MAINTENANCE_REQUIRED` and
back. Authority must come from a capability, not a sibling domain's nav.

### 2.5 `is_superuser` used as authority layer
`checkout_rooms` destructive branch uses `request.user.is_superuser` as the
authority ceiling. `is_superuser` is a Django admin flag, not a business
role; it leaks admin-plane authority into the staff plane and bypasses the
capability model entirely. Destructive bulk checkout is a manage-bucket
action and should require a dedicated cap, not a superuser flag.

### 2.6 Advertised-vs-enforced drift on `CanManageRooms` surface
`CanManageRooms` is attached to inventory CRUD (`StaffRoomViewSet`,
`StaffRoomTypeViewSet`, `RoomImageViewSet`, `bulk_create_rooms`,
`checkout_rooms`) but **not** to the turnover endpoints
(`start_cleaning`, `mark_cleaned`, `inspect_room`, `mark_maintenance`,
`complete_maintenance`). So the backend currently advertises "rooms manage
= super_staff_admin only" for inventory, while simultaneously letting any
nav-visible staff member drive maintenance flags and inspection passes.
Frontend will render these actions under the same "rooms" menu with no way
to know which subset is gated.

### 2.7 Route duplication / drift risk
- `StaffRoomViewSet` (inventory) is mounted at **both**
  `/api/staff/hotel/{slug}/room-management/` (via `staff_urls.py`) and
  `/api/staff/hotel/{slug}/hotel/staff/rooms/` (via `hotel/urls.py`
  included under the legacy `hotel` staff wrapper). There are also **two
  different `StaffRoomViewSet` classes** — one in `rooms/views.py` and one
  in `hotel/staff_views.py`. Same name, two bodies. Any future perm change
  applied to one will silently skip the other.
- `StaffRoomTypeViewSet` is mounted at `{slug}/room-types/`,
  `{slug}/hotel/staff/room-types/`. Same drift surface.

### 2.8 Unsafe writes
- `RoomImageViewSet.set_cover` (detail action, POST) — no `CanManageRooms`
  at method level; relies on `get_permissions()`'s `action not in
  ('list','retrieve')` branch, which *does* add `CanManageRooms`, so
  correct today but the pattern is fragile — a future nested-action
  addition that uses `@action(detail=True, methods=['get'])` that mutates
  state (antipattern but possible) would bypass.
- `RoomImageViewSet.perform_destroy` calls `cloudinary.uploader.destroy`
  on a public_id controlled by DB row — safe given `get_queryset()` scopes
  by `room__hotel=staff.hotel`, but destructive side-effect with only
  tier-based gating. Should be capability-gated (`room.media.delete` or
  `room.inventory.manage`).
- `bulk_create_rooms` creates `RoomStatusEvent` audit rows with
  `source='SYSTEM'` and `changed_by=staff` — mixes sources.

### 2.9 Dead endpoints / views that will re-enter production by mistake
See inventory rows D1–D6. They are not mounted today but importable
(`rooms.urls`, `rooms.views.RoomViewSet`, `AddGuestToRoomView`,
`RoomByHotelAndNumberView`, `checkout_needed`,
`rooms.views.RoomTypeViewSet`). `AddGuestToRoomView` in particular is a
write path that bypasses any booking lifecycle — re-mounting it would
fork the guest-onboarding surface.

### 2.10 Role-string / magic-value checks
None found in `rooms/` app itself — all authority is tier-based.
`checkout_rooms` destructive mode uses `request.user.is_superuser`
(magic flag, §2.5). No `role == '...'` string comparisons.

### 2.11 Routing order hazard
`staff_urls.py` mounts `rooms.staff_urls` **after** the top-level
`staff_hotel_router` (which owns `room-management`, `room-images`,
`room-types`). `rooms.staff_urls` owns `rooms/*` and `turnover/*`, so
prefixes don't collide today — but the legacy `STAFF_APPS` loop appends
`hotel/<slug>/<app>/` includes for every app in the list; `rooms` is
explicitly excluded there with a comment. That exclusion is the only
thing preventing a third mount point; regressing that comment would
create a third live `StaffRoomViewSet`.

---

## 3. Proposed Capability Model

Every capability below is backed by at least one currently live endpoint.
No floating caps.

| Capability | Backing endpoint(s) |
|---|---|
| `room.view` | nav presence + any GET below |
| `room.inventory.read` | #1/#3 GET, #2 detail GET, D1 if revived |
| `room.inventory.create` | #1/#3 POST, #9 `bulk_create_rooms` |
| `room.inventory.update` | #1/#3 PUT/PATCH |
| `room.inventory.delete` | #1/#3 DELETE |
| `room.type.read` | #6/#7 GET |
| `room.type.manage` | #6/#7 POST/PUT/PATCH/DELETE, #8 `upload-image` |
| `room.media.read` | #18 GET |
| `room.media.manage` | #18 POST/PUT/PATCH/DELETE, #19 `bulk-upload`, #20 `reorder`, #21 `set-cover` |
| `room.status.read` | #16 `turnover_rooms`, #17 `turnover_stats` |
| `room.status.transition` | #11 `start-cleaning`, #12 `mark-cleaned` (operate — housekeeping day-to-day) |
| `room.inspection.perform` | #13 `inspect_room` (supervise — inspection is an authority step over cleaning) |
| `room.maintenance.flag` | #14 `mark-maintenance` (operate — any qualified staff can flag) |
| `room.maintenance.clear` | #15 `complete-maintenance` (supervise — clearing is authority) |
| `room.out_of_order.set` | no dedicated endpoint today; today happens via `StaffRoomViewSet` PATCH on `is_out_of_order` field. Bind to `room.out_of_order.set` once extracted, or mandate via #1 PATCH body guard. Listed here because field exists and frontend does toggle it. |
| `room.checkout.bulk` | #10 `checkout_rooms` non-destructive branch |
| `room.checkout.destructive` | #10 `checkout_rooms` destructive branch (manage-only; replaces `is_superuser` check) |
| `room.qr.generate` | #5 `generate_qr` |

Explicitly NOT proposed (no live endpoint backing them — would be dead on arrival):
- `room.pin.generate` — #4 `generate_pin` is deprecated-by-response. Delete, do not model.
- `room.guest.add` — would back D2 `AddGuestToRoomView`; that path must be deleted, not capability-gated.
- `room.config.manage` — there is no room-wide config endpoint; `HotelSettings` and precheckin/survey are separate domains.

---

## 4. Capability Buckets

### read
Passive queries, no state change. Mapped to `CanReadRooms`
(safe-methods bypass = False, explicit read cap required so read is not a
free tier pass).
- `room.view`
- `room.inventory.read`
- `room.type.read`
- `room.media.read`
- `room.status.read`

### operate
Day-to-day line-staff actions. No authority over peers, no config, no
destructive side-effects.
- `room.status.transition` (start cleaning, mark cleaned)
- `room.maintenance.flag` (flag for maintenance)
- `room.qr.generate` (operational utility)

### supervise
Authority-over-work actions. Approves/overrides peer operate work.
- `room.inspection.perform` (inspection pass/fail decides release)
- `room.maintenance.clear` (clears a maintenance flag someone else set)
- `room.checkout.bulk` (bulk mutation across rooms — supervisory)

### manage
Inventory, configuration, destructive and money-adjacent actions.
Manager-only.
- `room.inventory.create`
- `room.inventory.update`
- `room.inventory.delete`
- `room.type.manage`
- `room.media.manage`
- `room.out_of_order.set`
- `room.checkout.destructive`

Bucket orthogonality rule: manage ⊃ nothing by implication; granting
`manage` does NOT auto-grant operate or supervise. Presets must union the
needed buckets explicitly (same rule Phase 6A validated).

---

## 5. Distribution Model

Strict rules enforced:
- **Tier grants no room capability.** Tier is identity only.
- **Manage caps are never in tier nor in department preset.** Role preset
  only (or super_staff_admin role preset, not tier).
- **No cross-department leakage.** F&B / kitchen / restaurant roles get
  zero room caps. Chat / attendance roles get zero room caps.
- **Read bucket is the only bucket a department preset may grant
  broadly.**

### Departments

| Department | Caps granted via department preset |
|---|---|
| `front_office` | `room.view`, `room.inventory.read`, `room.type.read`, `room.status.read`, `room.media.read`, `room.qr.generate` |
| `housekeeping` | `room.view`, `room.inventory.read`, `room.type.read`, `room.media.read`, `room.status.read`, `room.status.transition`, `room.maintenance.flag` |
| `maintenance` | `room.view`, `room.inventory.read`, `room.status.read`, `room.maintenance.flag` (they can also flag — confirms what they already see on the floor) |
| `food_and_beverage` / `kitchen` / `restaurant` | *empty* |
| `admin` / `management` | handled via role preset, not department |

### Roles (additive on top of department preset)

| Role | Additional caps |
|---|---|
| `housekeeper` | *(none beyond housekeeping dept)* |
| `housekeeping_supervisor` | `room.inspection.perform`, `room.maintenance.clear`, `room.checkout.bulk` |
| `front_desk_agent` | *(none beyond front_office dept)* |
| `front_office_manager` | `room.checkout.bulk`, `room.inspection.perform` (covers HK manager absence), `room.qr.generate` |
| `maintenance_technician` | *(none beyond maintenance dept)* |
| `maintenance_supervisor` | `room.maintenance.clear` |
| `operations_admin` | full `supervise` bucket + `room.out_of_order.set` + `room.checkout.destructive`. **Not** `room.inventory.*` / `room.type.manage` / `room.media.manage` (those are hotel_manager's office). |
| `hotel_manager` / `super_staff_admin` (role, not tier) | full `manage` bucket + full `supervise` bucket + `room.out_of_order.set` + `room.checkout.destructive` |

### Tiers

| Tier | Room caps |
|---|---|
| `regular_staff` | none (gets caps from dept+role) |
| `staff_admin` | none (same) |
| `super_staff_admin` | none as tier. If the user also holds the `super_staff_admin` / `hotel_manager` *role* preset, they get manage. Tier alone is identity. |

This mirrors the Phase-6A.1 correction that `super_staff_admin` tier must
not carry `_BOOKING_MANAGE`; same rule applies here on day one.

---

## 6. Endpoint → Capability Mapping

| # | Endpoint | Capability | Bucket | Permission Class |
|---|---|---|---|---|
| 1/3 GET list | `/room-management/` | `room.inventory.read` | read | `CanViewRooms + CanReadRoomInventory` |
| 1/3 GET detail | `/room-management/{rn}/` | `room.inventory.read` | read | same |
| 1/3 POST | `/room-management/` | `room.inventory.create` | manage | `CanViewRooms + CanCreateRoomInventory` |
| 1/3 PUT/PATCH | `/room-management/{rn}/` | `room.inventory.update` | manage | `CanViewRooms + CanUpdateRoomInventory` (with `is_out_of_order`-diff escalating to `CanSetRoomOutOfOrder`) |
| 1/3 DELETE | `/room-management/{rn}/` | `room.inventory.delete` | manage | `CanViewRooms + CanDeleteRoomInventory` |
| 5 | `/hotel/staff/rooms/{id}/generate_qr/` | `room.qr.generate` | operate | `CanViewRooms + CanGenerateRoomQR` |
| 6/7 GET | `/room-types/` | `room.type.read` | read | `CanViewRooms + CanReadRoomTypes` |
| 6/7 writes | `/room-types/` | `room.type.manage` | manage | `CanViewRooms + CanManageRoomTypes` |
| 8 | `/room-types/{id}/upload-image/` | `room.type.manage` | manage | same |
| 9 | `/room-types/{rt}/rooms/bulk-create/` | `room.inventory.create` | manage | `CanViewRooms + CanCreateRoomInventory` |
| 10 non-destructive | `/rooms/checkout/` | `room.checkout.bulk` | supervise | `CanViewRooms + CanBulkCheckoutRooms` |
| 10 destructive | `/rooms/checkout/` (`destructive=true`) | `room.checkout.destructive` | manage | `CanViewRooms + CanDestructiveCheckoutRooms` (replaces `is_superuser` check) |
| 11 | `/rooms/{rn}/start-cleaning/` | `room.status.transition` | operate | `CanViewRooms + CanTransitionRoomStatus` |
| 12 | `/rooms/{rn}/mark-cleaned/` | `room.status.transition` | operate | same |
| 13 | `/rooms/{rn}/inspect/` | `room.inspection.perform` | supervise | `CanViewRooms + CanInspectRoom` |
| 14 | `/rooms/{rn}/mark-maintenance/` | `room.maintenance.flag` | operate | `CanViewRooms + CanFlagRoomMaintenance` (**remove** `HasNavPermission('maintenance')` — cross-domain leak) |
| 15 | `/rooms/{rn}/complete-maintenance/` | `room.maintenance.clear` | supervise | `CanViewRooms + CanClearRoomMaintenance` |
| 16 | `/turnover/rooms/` | `room.status.read` | read | `CanViewRooms + CanReadRoomStatus` |
| 17 | `/turnover/stats/` | `room.status.read` | read | same |
| 18 GET | `/room-images/` | `room.media.read` | read | `CanViewRooms + CanReadRoomMedia` |
| 18 writes | `/room-images/` | `room.media.manage` | manage | `CanViewRooms + CanManageRoomMedia` |
| 19 | `/room-images/bulk-upload/` | `room.media.manage` | manage | same |
| 20 | `/room-images/reorder/` | `room.media.manage` | manage | same |
| 21 | `/room-images/{id}/set-cover/` | `room.media.manage` | manage | same |
| 4 | `/hotel/staff/rooms/{id}/generate_pin/` | — | — | **DELETE endpoint** (deprecated) |
| D1–D6 | `rooms/urls.py` entire file | — | — | **DELETE file + views** |

Note: `CanViewRooms` replaces standalone `HasNavPermission('rooms')` and
carries the same nav check plus `request.user.staff_profile.hotel ==
view.hotel` re-assertion, per the Phase-6A `CanViewBookings` pattern.
Safe-methods bypass = **False**.

---

## 7. Required Backend Changes

### 7.1 Capability registry
- Add `room.*` slugs to `staff/capability_catalog.py` per §3.
- Add `MODULE_POLICY` entry for `'rooms'` with bucket assignments
  matching §4.
- Add department/role presets per §5 in the same registry files Phase 6A
  extended (`PRESET_CAPABILITIES` — department map and role map).

### 7.2 New permission classes (in `staff/permissions.py`)
- `CanViewRooms` (nav + same-hotel re-check, mirrors `CanViewBookings`)
- `CanReadRoomInventory`, `CanCreateRoomInventory`,
  `CanUpdateRoomInventory`, `CanDeleteRoomInventory`
- `CanReadRoomTypes`, `CanManageRoomTypes`
- `CanReadRoomMedia`, `CanManageRoomMedia`
- `CanReadRoomStatus`, `CanTransitionRoomStatus`, `CanInspectRoom`
- `CanFlagRoomMaintenance`, `CanClearRoomMaintenance`
- `CanSetRoomOutOfOrder`
- `CanBulkCheckoutRooms`, `CanDestructiveCheckoutRooms`
- `CanGenerateRoomQR`

All delegate to the capability resolver, none call `resolve_tier()`.
Safe-methods bypass = False on the specific action classes; `CanViewRooms`
permits safe methods only after nav + hotel scope check.

### 7.3 Permissions to remove
- `CanManageRooms` (tier check) — **delete** from `staff/permissions.py`
  and every call site (§2.2). It is the tier leak.
- Inline `HasNavPermission(...)` calls inside function views
  (`bulk_create_rooms`, `checkout_rooms`, `checkout_needed`,
  `start_cleaning`, `mark_cleaned`, `inspect_room`, `mark_maintenance`,
  `complete_maintenance`, `turnover_rooms`, `turnover_stats`). Replace
  with `@permission_classes([…capability classes…])`.
- Inline `request.user.is_superuser` gate in `checkout_rooms` destructive
  branch — replace with `CanDestructiveCheckoutRooms`.
- `HasNavPermission('maintenance')` inside `mark_maintenance` /
  `complete_maintenance` — the rooms-module endpoint must not gate on a
  foreign nav slug.

### 7.4 View updates
- `StaffRoomViewSet` (`rooms/views.py`): replace `get_permissions()`
  with per-action capability classes per §6. Guard `is_out_of_order`
  field changes in `perform_update` (escalate to `CanSetRoomOutOfOrder`
  if that field is in `serializer.validated_data`).
- `StaffRoomTypeViewSet` (`hotel/staff_views.py`): same pattern.
- `RoomImageViewSet` (`rooms/views.py`): same pattern.
- All `@api_view` function views in `rooms/views.py`: replace
  `permission_classes=[IsAuthenticated, IsStaffMember, IsSameHotel]` +
  inline `HasNavPermission(...)` + inline `CanManageRooms()` with a
  single declarative class list per §6.

### 7.5 Dead code to delete
- `rooms/urls.py` — entire file (D1–D5, none routed).
- `rooms/views.py::RoomViewSet` (readonly, dead).
- `rooms/views.py::RoomByHotelAndNumberView` (dead).
- `rooms/views.py::AddGuestToRoomView` (dead AND unsafe — bypasses
  booking lifecycle).
- `rooms/views.py::checkout_needed` (dead).
- `rooms/views.py::RoomTypeViewSet` (dead, duplicates `StaffRoomTypeViewSet`).
- `StaffRoomViewSet.generate_pin` (deprecated, returns 400 always).
- **Resolve `StaffRoomViewSet` duplication**: keep exactly one class.
  Recommendation — keep `hotel/staff_views.py::StaffRoomViewSet` (it has
  `generate_qr`), delete `rooms/views.py::StaffRoomViewSet`, update
  `staff_urls.py` import line. Drop the `hotel/urls.py` staff_router
  registration of `r'rooms'` to eliminate the `/hotel/staff/rooms/`
  duplicate mount; keep only `/room-management/`.
- Same duplication resolution for `StaffRoomTypeViewSet` — keep the
  `hotel/staff_views.py` class, drop the `hotel/urls.py` staff_router
  registration of `r'room-types'`.

### 7.6 Audit-trail hygiene
- `bulk_create_rooms` writes `RoomStatusEvent.source='SYSTEM'` but passes
  `changed_by=staff`. Change to `source='STAFF_ACTION'` (or whichever
  enum value housekeeping uses for staff-originated events) when
  `changed_by` is non-null.

---

## 8. Tests Required

All tests live in `rooms/tests/test_rbac_*.py`. Each asserts the
capability contract, not tier behaviour.

### 8.1 Registry
- `test_rooms_module_policy_validates` — `validate_module_policy()` is
  clean for `'rooms'`.
- `test_rooms_bucket_orthogonality` — synthetic cap-set probes per
  Phase 6A's `rbac_phase6a_validation.py` pattern: operate-only set
  cannot access supervise endpoints; supervise-only set cannot access
  manage endpoints; read-only set cannot POST anywhere.
- `test_no_room_cap_in_any_tier_preset` — no `room.*` slug appears in
  `TIER_PRESET_CAPABILITIES` for any tier.
- `test_manage_room_caps_require_role_preset` — manage bucket caps never
  appear in department preset map.

### 8.2 Per-endpoint enforcement (one test per row of §6 table)
For each mapped endpoint:
- 403 without `room.view`.
- 403 with `room.view` but missing the specific action cap.
- 200/201/204 with exact required caps.
- 403 cross-hotel (staff_profile.hotel ≠ url slug) even with caps.

### 8.3 Cross-domain isolation
- `test_room_caps_do_not_grant_bookings` — a staff with full `room.*`
  manage bucket gets 403 on every `room_bookings` endpoint.
- `test_booking_caps_do_not_grant_rooms` — symmetric.
- `test_maintenance_nav_cannot_flip_room_status` — with only
  `HasNavPermission('maintenance')` and no `room.maintenance.flag`,
  `mark_maintenance` returns 403. (Closes §2.4.)

### 8.4 Regression / dead-code
- `test_rooms_urls_file_not_importable_as_urlconf` — assert
  `include('rooms.urls')` does not resolve in the URL tree.
- `test_generate_pin_returns_410_or_removed` — once removed.
- `test_add_guest_to_room_view_removed` — reverse lookup
  `'add-guest-to-room'` raises `NoReverseMatch`.

### 8.5 Destructive-checkout re-gating
- `test_destructive_checkout_requires_manage_cap` — user is_superuser=True
  but without `room.checkout.destructive` gets 403. (Closes §2.5.)
- `test_destructive_checkout_with_cap` — user has cap, is_superuser=False,
  succeeds.

### 8.6 `is_out_of_order` escalation
- `test_patch_room_sets_out_of_order_requires_ooo_cap` — PATCH with only
  `room.inventory.update` and payload `{is_out_of_order: true}` → 403.
- `test_patch_room_other_fields_allowed_without_ooo_cap` — PATCH without
  `is_out_of_order` in payload succeeds with just `room.inventory.update`.

### 8.7 Routing duplication gone
- `test_only_one_room_management_mount` — `reverse('staff-rooms-list')`
  resolves to `/room-management/` only; old
  `/hotel/staff/rooms/` returns 404.

---

## 9. Go / No-Go

**Is the module ready to implement? NO.**

### What blocks implementation

1. **No capability namespace exists.** `room.*` caps must be added to
   `staff/capability_catalog.py` before any view can be re-gated.
   (Blocker — §3, §7.1.)
2. **Routing duplication of `StaffRoomViewSet` and `StaffRoomTypeViewSet`
   under two class bodies in two apps.** Re-gating one class leaves the
   other silently unpatched and accessible. Must be consolidated first.
   (Blocker — §2.7, §7.5.)
3. **Dead-code surface is production-importable.** `rooms/urls.py` and
   `AddGuestToRoomView` could be mounted by anyone doing a routine
   "include all app urls" sweep, bypassing any new rules we write. Must
   be deleted before gating is tightened. (Blocker — §2.9, §7.5.)
4. **Turnover endpoints are today gated by nav-only** (`start_cleaning`,
   `mark_cleaned`, `inspect_room`, `mark_maintenance`,
   `complete_maintenance`). This is the exact advertised-vs-enforced drift
   Phase 6A retired. Any frontend menu that renders these as "rooms
   actions" is lying about authority today. Must be gated against real
   caps before we publish the new nav. (Blocker — §2.3, §2.6.)
5. **`CanManageRooms` tier leak is wired across five views and the
   hotel/staff_views module.** Deleting it is a coordinated change across
   `staff/permissions.py`, `rooms/views.py`, `hotel/staff_views.py`,
   `hotel/urls.py`, and every call site. (Blocker — §2.2, §7.3.)
6. **No test suite exists for rooms RBAC.** Phase 6A shipped with a
   validation harness (`rbac_phase6a_validation.py`); rooms has nothing
   equivalent. Without §8 in place first we cannot detect regressions at
   merge time. (Blocker — §8.)

### What must be done first (ordered)

1. Consolidate `StaffRoomViewSet` and `StaffRoomTypeViewSet` to one class
   each; drop duplicate router registrations in `hotel/urls.py`. Land
   as a no-behaviour-change refactor under the existing tier permissions.
2. Delete `rooms/urls.py`, `RoomViewSet` (read-only), `AddGuestToRoomView`,
   `RoomByHotelAndNumberView`, `checkout_needed`, `RoomTypeViewSet`
   legacy, `StaffRoomViewSet.generate_pin`. Verify import graph.
3. Add `room.*` capability catalog + `MODULE_POLICY['rooms']` +
   department/role presets per §5. Registry tests (§8.1) green.
4. Add new permission classes per §7.2; keep old `CanManageRooms` in
   parallel for one commit.
5. Swap every rooms-module view onto the new classes per §6. Remove
   inline `HasNavPermission(...)` calls and `is_superuser` gate. Remove
   `CanManageRooms`.
6. Ship full §8 test suite. Only then is the module ready.

Only when **all six** are complete is rooms ready to go capability-based.
Until then, any frontend change that assumes rooms works like
room-bookings will advertise actions the backend still tier-gates.
