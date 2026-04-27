# RBAC Refactor — room_services Module

Capability-based RBAC migration. Replaces all legacy authority
(`HasNavPermission('room_services')`, `HasRoomServicesNav`,
`CanManageRoomServices`, tier ≥ staff_admin checks, `_is_staff_request`-only
checks) with canonical capability gates.

---

## 1. Files modified

| File | Change |
|------|--------|
| [staff/capability_catalog.py](staff/capability_catalog.py) | Added 17 new room-service capabilities; added `CANONICAL_CAPABILITIES` entries; added `_ROOM_SERVICE_BASE` / `_ROOM_SERVICE_OPERATE` / `_ROOM_SERVICE_MANAGE` preset bundles; wired into `TIER_DEFAULT_CAPABILITIES`. |
| [staff/module_policy.py](staff/module_policy.py) | Added `MODULE_POLICY['room_services']` (view/read + 17 actions). |
| [staff/permissions.py](staff/permissions.py) | Added 17 `HasCapability` subclasses. Removed `HasRoomServicesNav`. Replaced `CanManageRoomServices` body with a fail-closed deprecation stub (any stale import is now denied at runtime). |
| [room_services/views.py](room_services/views.py) | `OrderViewSet` / `BreakfastOrderViewSet` rebuilt around per-action capability dispatch + `_DenyAll` fallback. Staff branches inside `perform_create` / `room_order_history` now enforce same-hotel + capability explicitly. `partial_update` enforces per-transition capabilities. |
| [room_services/staff_views.py](room_services/staff_views.py) | `StaffRoomServiceItemViewSet` / `StaffBreakfastItemViewSet` rebuilt around per-action capability dispatch + `_DenyAll` fallback (mixin-based). |

---

## 2. Capabilities added

All registered in `CANONICAL_CAPABILITIES`.

| Slug | Bucket |
|------|--------|
| `room_service.module.view` | view |
| `room_service.menu.read` | menu |
| `room_service.menu.item.create` | menu |
| `room_service.menu.item.update` | menu |
| `room_service.menu.item.delete` | menu |
| `room_service.menu.item.image_manage` | menu |
| `room_service.order.read` | order |
| `room_service.order.create` | order |
| `room_service.order.update` | order |
| `room_service.order.delete` | order |
| `room_service.order.accept` | order |
| `room_service.order.complete` | order |
| `room_service.breakfast_order.read` | breakfast |
| `room_service.breakfast_order.create` | breakfast |
| `room_service.breakfast_order.update` | breakfast |
| `room_service.breakfast_order.delete` | breakfast |
| `room_service.breakfast_order.accept` | breakfast |
| `room_service.breakfast_order.complete` | breakfast |

Retained (unchanged): `room_service.order.fulfill_porter`,
`room_service.order.fulfill_kitchen` — routing/eligibility caps used by
notifications, not authority gates.

### Preset bundles

```text
_ROOM_SERVICE_BASE     = module.view + menu.read + order.read + breakfast_order.read
_ROOM_SERVICE_OPERATE  = BASE + order.{create,update,accept,complete}
                              + breakfast_order.{create,update,accept,complete}
_ROOM_SERVICE_MANAGE   = OPERATE + order.delete + breakfast_order.delete
                                 + menu.item.{create,update,delete,image_manage}
```

### Tier wiring (`TIER_DEFAULT_CAPABILITIES`)

| Tier | Bundle |
|------|--------|
| `super_staff_admin` | `_ROOM_SERVICE_MANAGE` (in addition to existing tier bundle) |
| `staff_admin` | `_ROOM_SERVICE_MANAGE` |
| `regular_staff` | `_ROOM_SERVICE_BASE` (view + reads only) |

This is the canonical replacement for the old `tier ≥ staff_admin` rule:
mutating capabilities are granted via the manage bundle; reads/visibility
are broad.

---

## 3. Module policy

`MODULE_POLICY['room_services']` (in [staff/module_policy.py](staff/module_policy.py)):

| Key | Capability |
|-----|------------|
| `view_capability` | `room_service.module.view` |
| `read_capability` | `room_service.order.read` |
| `actions.menu_read` | `room_service.menu.read` |
| `actions.menu_item_create` | `room_service.menu.item.create` |
| `actions.menu_item_update` | `room_service.menu.item.update` |
| `actions.menu_item_delete` | `room_service.menu.item.delete` |
| `actions.menu_item_image_manage` | `room_service.menu.item.image_manage` |
| `actions.order_read` | `room_service.order.read` |
| `actions.order_create` | `room_service.order.create` |
| `actions.order_update` | `room_service.order.update` |
| `actions.order_delete` | `room_service.order.delete` |
| `actions.order_accept` | `room_service.order.accept` |
| `actions.order_complete` | `room_service.order.complete` |
| `actions.breakfast_order_read` | `room_service.breakfast_order.read` |
| `actions.breakfast_order_create` | `room_service.breakfast_order.create` |
| `actions.breakfast_order_update` | `room_service.breakfast_order.update` |
| `actions.breakfast_order_delete` | `room_service.breakfast_order.delete` |
| `actions.breakfast_order_accept` | `room_service.breakfast_order.accept` |
| `actions.breakfast_order_complete` | `room_service.breakfast_order.complete` |

---

## 4. Permission classes

Added in [staff/permissions.py](staff/permissions.py) (all `HasCapability` subclasses):

- `CanViewRoomServicesModule` (safe_methods_bypass=False)
- `CanReadRoomServiceMenu` (safe_methods_bypass=False)
- `CanCreateRoomServiceMenuItem`
- `CanUpdateRoomServiceMenuItem`
- `CanDeleteRoomServiceMenuItem`
- `CanManageRoomServiceMenuItemImage`
- `CanReadRoomServiceOrder` (safe_methods_bypass=False)
- `CanCreateRoomServiceOrder`
- `CanUpdateRoomServiceOrder`
- `CanDeleteRoomServiceOrder`
- `CanAcceptRoomServiceOrder`
- `CanCompleteRoomServiceOrder`
- `CanReadBreakfastOrder` (safe_methods_bypass=False)
- `CanCreateBreakfastOrder`
- `CanUpdateBreakfastOrder`
- `CanDeleteBreakfastOrder`
- `CanAcceptBreakfastOrder`
- `CanCompleteBreakfastOrder`

Removed:
- `HasRoomServicesNav` — deleted (legacy nav-only gate; replaced by `CanViewRoomServicesModule`).
- `CanManageRoomServices` — body replaced with a fail-closed stub. Kept as a class so any stale import surfaces at runtime as a denied request, not as an `ImportError` time-bomb. Marked deprecated in its docstring.

---

## 5. Endpoints fixed

### Staff order endpoints (`OrderViewSet`)

Chain (base): `IsAuthenticated` + `IsStaffMember` + `IsSameHotel` + `CanViewRoomServicesModule` + per-action class. Unmapped action → `_DenyAll` (fail-closed).

| Action | Per-action capability |
|--------|-----------------------|
| `list`, `retrieve`, `pending_count`, `all_orders_summary`, `order_history` | `CanReadRoomServiceOrder` |
| `update`, `partial_update` | `CanUpdateRoomServiceOrder` (transitions further gated below) |
| `destroy` | `CanDeleteRoomServiceOrder` |
| `create`, `room_order_history` | `AllowAny` (guest-token path); staff branch enforces same-hotel + capability inside body |

`partial_update` status transition gating (replaces `tier ≥ staff_admin`):

| From → To | Required capability |
|-----------|---------------------|
| `pending → accepted` | `room_service.order.accept` |
| `accepted → completed` | `room_service.order.complete` |

### Staff breakfast-order endpoints (`BreakfastOrderViewSet`)

Same chain shape.

| Action | Per-action capability |
|--------|-----------------------|
| `list`, `retrieve`, `pending_count` | `CanReadBreakfastOrder` |
| `update`, `partial_update` | `CanUpdateBreakfastOrder` (transitions further gated below) |
| `destroy` | `CanDeleteBreakfastOrder` |
| `create` | `AllowAny` (guest-token path); staff branch enforces same-hotel + capability inside body |

| From → To | Required capability |
|-----------|---------------------|
| `pending → accepted` | `room_service.breakfast_order.accept` |
| `accepted → completed` | `room_service.breakfast_order.complete` |

### Staff menu endpoints

`StaffRoomServiceItemViewSet` and `StaffBreakfastItemViewSet` share `_StaffMenuPermissionMixin`. Chain (base): `IsAuthenticated` + `IsStaffMember` + `IsSameHotel` + `CanViewRoomServicesModule`.

| Action | Per-action capability |
|--------|-----------------------|
| `list`, `retrieve` | `CanReadRoomServiceMenu` |
| `create` | `CanCreateRoomServiceMenuItem` |
| `update`, `partial_update` | `CanUpdateRoomServiceMenuItem` |
| `destroy` | `CanDeleteRoomServiceMenuItem` |
| `upload_image` | `CanManageRoomServiceMenuItemImage` |
| (any unmapped) | `_DenyAll` |

### Guest endpoints (unchanged)

Kept on `AllowAny` + `resolve_guest_access` token validation:
- `RoomServiceItemViewSet.menu` (room tablet)
- `BreakfastItemViewSet.menu` (room tablet)
- `OrderViewSet.create` (guest path branch)
- `OrderViewSet.room_order_history` (guest path branch)
- `BreakfastOrderViewSet.create` (guest path branch)
- `save_guest_fcm_token`

Guest flow not broken.

---

## 6. Security fixes applied

### Fix 1 — staff create order
**Before:** `OrderViewSet.create` ran under `AllowAny`; the `_is_staff_request` branch in `perform_create` accepted any authenticated staff with no same-hotel check and no capability check. Cross-hotel staff with `staff_profile` could create orders against any hotel.

**After:** `perform_create` staff branch raises `PermissionDenied` if (a) `_staff_hotel_matches(request, hotel)` is false, or (b) the user lacks `room_service.order.create`. Guest path unchanged.

### Fix 2 — `room_order_history`
**Before:** Staff branch only checked `_is_staff_request` (no same-hotel, no capability).

**After:** Staff branch returns 403 unless same-hotel **and** `room_service.order.read` is held. Guest path unchanged.

### Fix 3 — staff breakfast create order
**Before:** Same hole as Fix 1, applied to `BreakfastOrderViewSet.perform_create`.

**After:** Mirrors Fix 1 with `room_service.breakfast_order.create`.

### Fix 4 — menu mutation
**Before:** `StaffRoomServiceItemViewSet` / `StaffBreakfastItemViewSet` were gated only by `HasRoomServicesNav` + `IsStaffMember` + `IsSameHotel` — **no manage gate at all**. Any nav-visible staff could CRUD menu items and upload images.

**After:** Each action carries its canonical capability. By default, only `staff_admin` / `super_staff_admin` tier (carrying `_ROOM_SERVICE_MANAGE`) can mutate menu items.

### Fix 5 — tier-only mutation gate retired
**Before:** Order status transitions (`pending → accepted`, `accepted → completed`) and CUD on orders were gated by `CanManageRoomServices` (`tier ≥ staff_admin`).

**After:** Each transition has its own capability (`...accept` / `...complete`); the legacy `CanManageRoomServices` is a fail-closed stub.

### Fix 6 — fail-closed for unmapped actions
Any new action added to either viewset that is not registered in `_STAFF_ACTION_PERMISSIONS` / `_MENU_ACTION_PERMISSIONS` resolves to `_DenyAll` — no accidental open surfaces.

---

## 7. Validation results

| Check | Result |
|-------|--------|
| `python manage.py check` | `System check identified no issues (0 silenced).` |
| `validate_module_policy()` | `[]` |
| `validate_preset_maps()` | `[]` |

---

## 8. Legacy pattern scan inside `room_services/`

| Pattern | Hits |
|---------|------|
| `HasNavPermission` | 0 |
| `HasRoomServicesNav` | 0 |
| `CanManageRoomServices` (live use) | 0 (only one comment reference inside [room_services/views.py](room_services/views.py) explaining the migration) |
| `tier` / `access_level` gating | 0 |

`_is_staff_request` is retained (3 callsites) — it is the staff/guest dispatch helper, not an authority check, and now sits **above** explicit capability + same-hotel enforcement.

---

## 9. Out of scope (not touched)

- frontend
- tests
- unrelated modules

Done.
