# Phase 6D.1 — Maintenance RBAC Implementation Report

**Status:** ✅ **GO**
**Scope:** `maintenance` module (`/api/staff/hotel/<slug>/maintenance/...`) — capability-first RBAC, tenant isolation, action endpoints, object-level comment/photo rules.
**Non-scope:** `rooms.maintenance.*` capabilities (kept strictly disjoint).

---

## 1. Files Changed

| File | Nature |
|------|--------|
| [staff/capability_catalog.py](staff/capability_catalog.py) | 14 new `maintenance.*` capabilities + 5 preset bundles + role/dept wiring |
| [staff/module_policy.py](staff/module_policy.py) | New `maintenance` module entry + imports |
| [staff/permissions.py](staff/permissions.py) | 14 new capability permission classes appended |
| [maintenance/serializers.py](maintenance/serializers.py) | Full rewrite — hotel-scoped request field, read-only `status`/`accepted_by`, generic cross-hotel errors |
| [maintenance/views.py](maintenance/views.py) | Full rewrite — capability-routed `get_permissions`, `@action` endpoints, object-level comment rules |
| [hotel/tests/test_rbac_maintenance.py](hotel/tests/test_rbac_maintenance.py) | New — 57 tests |

Legacy `HasMaintenanceNav` / `CanManageMaintenance` classes remain in `staff/permissions.py` but are no longer imported by `maintenance/views.py`.

---

## 2. Capabilities Added

All added to `CANONICAL_CAPABILITIES`:

| Capability | Purpose |
|------------|---------|
| `maintenance.module.view` | Module visible in navigation |
| `maintenance.request.read` | List / retrieve requests, comments, photos |
| `maintenance.request.create` | `POST requests/` |
| `maintenance.request.accept` | `POST requests/{id}/accept/` |
| `maintenance.request.resolve` | `POST requests/{id}/resolve/` |
| `maintenance.request.update` | `PATCH requests/{id}/` (metadata only) |
| `maintenance.request.reassign` | `POST requests/{id}/reassign/` |
| `maintenance.request.reopen` | `POST requests/{id}/reopen/` |
| `maintenance.request.close` | `POST requests/{id}/close/` |
| `maintenance.request.delete` | `DELETE requests/{id}/` |
| `maintenance.comment.create` | Create + edit/delete one's own comments |
| `maintenance.comment.moderate` | Edit/delete comments authored by other staff |
| `maintenance.photo.upload` | Upload photos |
| `maintenance.photo.delete` | Delete photos regardless of uploader |

Namespace is strictly disjoint from `room.maintenance.*` (enforced by test `test_maintenance_namespace_disjoint_from_room_maintenance`).

---

## 3. Module Policy Block

`MODULE_POLICY['maintenance']`:

```python
{
    'view_capability': MAINTENANCE_MODULE_VIEW,
    'read_capability': MAINTENANCE_REQUEST_READ,
    'actions': {
        'request_create':   MAINTENANCE_REQUEST_CREATE,
        'request_accept':   MAINTENANCE_REQUEST_ACCEPT,
        'request_resolve':  MAINTENANCE_REQUEST_RESOLVE,
        'request_update':   MAINTENANCE_REQUEST_UPDATE,
        'request_reassign': MAINTENANCE_REQUEST_REASSIGN,
        'request_reopen':   MAINTENANCE_REQUEST_REOPEN,
        'request_close':    MAINTENANCE_REQUEST_CLOSE,
        'request_delete':   MAINTENANCE_REQUEST_DELETE,
        'comment_create':   MAINTENANCE_COMMENT_CREATE,
        'comment_moderate': MAINTENANCE_COMMENT_MODERATE,
        'photo_upload':     MAINTENANCE_PHOTO_UPLOAD,
        'photo_delete':     MAINTENANCE_PHOTO_DELETE,
    },
}
```

`validate_module_policy()` returns `[]`.

---

## 4. Preset Distribution

Five escalating bundles:

- **`_MAINTENANCE_REPORTER`** = view + read + `request.create`
- **`_MAINTENANCE_READ`** = view + read
- **`_MAINTENANCE_OPERATE`** = READ + accept + resolve + comment.create + photo.upload
- **`_MAINTENANCE_SUPERVISE`** = OPERATE + update + reassign + reopen + comment.moderate + photo.delete
- **`_MAINTENANCE_MANAGE`** = SUPERVISE + close + delete

| Persona | Bundle |
|---|---|
| Role: `operations_admin` | MANAGE |
| Role: `hotel_manager` | MANAGE |
| Role: `maintenance_manager` | MANAGE |
| Role: `maintenance_supervisor` | SUPERVISE |
| Role: `front_office_manager` | REPORTER |
| Role: `front_desk_agent` | REPORTER |
| Dept: `maintenance` | OPERATE |
| Dept: `front_office` | REPORTER |
| Dept: `housekeeping` | REPORTER |
| **Any tier** (`regular_staff` / `staff_admin` / `super_staff_admin`) | **None** |

`validate_preset_maps()` returns `[]`. No `maintenance.*` capability leaks into any tier preset (enforced by test `test_no_maintenance_capability_in_any_tier_preset`).

---

## 5. Serializer Hardening

**`MaintenanceRequestSerializer`** — `read_only_fields = ['id', 'hotel', 'reported_by', 'accepted_by', 'status', 'created_at', 'updated_at']`. `status` and `accepted_by` can only be mutated by the action endpoints; `hotel` and `reported_by` are auto-stamped in `perform_create`.

**`_HotelScopedRequestField`** — `PrimaryKeyRelatedField` for `MaintenanceRequest` with `get_queryset()` filtered to the acting staff's hotel. `required`, `does_not_exist`, and `incorrect_type` all emit the identical generic error `"Maintenance request not found."` so cross-hotel existence cannot be probed.

**`MaintenanceRequestSerializer.validate_room`** — rejects foreign rooms with the generic `"Room not found."`.

**`MaintenanceRequestReassignSerializer`** — `accepted_by` is an integer id; the serializer queries `Staff.objects.get(pk=value, hotel_id=user_hotel)` and raises the generic `"Staff member not found."` for both missing and foreign-hotel staff (verified equal in `test_reassign_foreign_hotel_returns_same_error_as_missing`).

**`BulkMaintenancePhotoSerializer`** — stamps `uploaded_by` from the context; `request` FK uses the hotel-scoped field.

---

## 6. New `@action` Endpoints

All gated by base chain `(IsAuthenticated, IsStaffMember, IsSameHotel, CanViewMaintenanceModule, CanReadMaintenanceRequests)` + their own capability.

| Endpoint | Capability | Source → Target status |
|---|---|---|
| `POST requests/{id}/accept/` | `maintenance.request.accept` | `open`/`in_progress` → `in_progress` (stamps `accepted_by`); `closed` → 400 |
| `POST requests/{id}/resolve/` | `maintenance.request.resolve` | `in_progress` → `resolved`; else 400 |
| `POST requests/{id}/reopen/` | `maintenance.request.reopen` | `resolved`/`closed` → `open` (clears `accepted_by`); else 400 |
| `POST requests/{id}/close/` | `maintenance.request.close` | `resolved`/`in_progress` → `closed`; else 400 |
| `POST requests/{id}/reassign/` | `maintenance.request.reassign` | sets `accepted_by` via reassign serializer |

---

## 7. Endpoint Enforcement Table

| Endpoint | Base chain | + Capability |
|---|---|---|
| `GET requests/` | ✓ | `request.read` |
| `POST requests/` | ✓ | `request.create` |
| `GET requests/{id}/` | ✓ | `request.read` |
| `PATCH/PUT requests/{id}/` | ✓ | `request.read` + `request.update` |
| `DELETE requests/{id}/` | ✓ | `request.delete` |
| `POST requests/{id}/accept/` | ✓ | `request.read` + `request.accept` |
| `POST requests/{id}/resolve/` | ✓ | `request.read` + `request.resolve` |
| `POST requests/{id}/reopen/` | ✓ | `request.read` + `request.reopen` |
| `POST requests/{id}/close/` | ✓ | `request.read` + `request.close` |
| `POST requests/{id}/reassign/` | ✓ | `request.read` + `request.reassign` |
| `GET/POST comments/` | ✓ | `request.read` (+ `comment.create` for POST) |
| `PATCH/DELETE comments/{id}/` | ✓ | `request.read` + `comment.create` (+ object-level check) |
| `GET/POST photos/` | ✓ | `request.read` (+ `photo.upload` for POST) |
| `PATCH/DELETE photos/{id}/` | ✓ | `request.read` + `photo.delete` |

---

## 8. Tenant Isolation

- `MaintenanceRequestViewSet` inherits `HotelScopedQuerysetMixin` — list/retrieve auto-filters by `hotel`.
- `MaintenanceCommentViewSet.get_queryset()` filters by `request__hotel=staff.hotel`.
- `MaintenancePhotoViewSet.get_queryset()` filters by `request__hotel=staff.hotel`.
- `perform_create` on requests stamps `hotel` from `request.user.staff_profile.hotel`; user-supplied `hotel` is read-only.
- Cross-hotel FK rejection is parity-identical to "missing" for: `request` (comment create, photo create), `room` (request create/patch), `accepted_by` (reassign) — all verified.
- `check_object_permissions` on comment/photo viewsets skips `IsSameHotel.has_object_permission` (which can't introspect these models for `.hotel`) and relies on the queryset + view-level `IsSameHotel.has_permission` for isolation.

---

## 9. Comment & Photo Object Rules

**Comments — `update`/`partial_update`/`destroy`:**

```
author (comment.staff_id == request.user.staff_profile.id)  → allowed if user has `comment.create`
non-author                                                  → requires `comment.moderate`
```

**Photos — `update`/`partial_update`/`destroy`:**

```
any user with `photo.delete` (uploader does not matter)
```

Uploading is author-agnostic — gated solely by `photo.upload`.

---

## 10. Tests Added — `hotel/tests/test_rbac_maintenance.py`

**57 tests, 3 classes:**

1. **`MaintenancePolicyRegistryTest`** (5 tests) — registry self-consistency, canonical membership, namespace disjointness with `room.maintenance.*`, no tier leaks.
2. **`MaintenancePolicyPersonaTest`** (9 tests) — persona → module policy matrix across `operations_admin`, `hotel_manager`, `maintenance_manager`, `maintenance_supervisor`, maintenance dept, front_office dept, kitchen dept, staff_admin/super_staff_admin (no maintenance authority).
3. **`MaintenanceEndpointEnforcementTest`** (43 tests) — full matrix across every endpoint × every persona; PATCH read-only of `status`/`accepted_by`; all 5 action endpoints including state-machine guards; comment author-vs-moderator object rules; photo upload/delete split; cross-hotel room/staff/request/photo rejection with error-parity to missing.

---

## 11. Validation Results

```
>>> from staff.capability_catalog import validate_preset_maps
>>> validate_preset_maps()
[]
>>> from staff.module_policy import validate_module_policy
>>> validate_module_policy()
[]
```

Regression suite (spec-mandated):

```
$ python manage.py test hotel.tests.test_rbac_maintenance hotel.tests.test_rbac_housekeeping \
                        hotel.tests.test_rbac_rooms    hotel.tests.test_rbac_bookings \
                        --verbosity=1 --keepdb
----------------------------------------------------------------------
Ran 185 tests in 19.010s

OK
```

- `test_rbac_maintenance` — 57/57 ✅
- `test_rbac_housekeeping` — pass ✅ (no regression)
- `test_rbac_rooms` — pass ✅ (no regression)
- `test_rbac_bookings` — pass ✅ (no regression)

---

## 12. Remaining Risks

- **Legacy permission classes still in module**: `HasMaintenanceNav` and `CanManageMaintenance` live in `staff/permissions.py` but are unused by the rewritten `maintenance/views.py`. A follow-up may delete them once we're confident no external code imports them.
- **Cloudinary in production**: Photo upload tests mock `cloudinary.uploader.upload`. Production behaviour depends on actual Cloudinary credentials; capability enforcement is independent of the image backend.
- **No listing-level hotel filter on the photo FK lookup inside `_HotelScopedRequestField` during `create`**: scope is enforced by `get_queryset()` of the field, which is sufficient for serializer-level rejection, but a defense-in-depth `perform_create` re-check is present on comments but omitted on photos (bulk create rejects foreign `request` at serializer level — verified by test).
- **Pre-existing lint noise**: `E501`/continuation warnings in `permissions.py` and `module_policy.py` match the prevailing style of the repo; not addressed in this phase.

---

## 13. Final Verdict

**✅ GO**

- Canonical registry validators both return `[]`.
- All 57 new tests pass.
- Regression suite of 185 tests across maintenance + housekeeping + rooms + bookings: **0 failures, 0 errors**.
- Every endpoint is capability-gated; `status` and `accepted_by` are action-only; tenant isolation is parity-tested; comment/photo object rules are verified.
