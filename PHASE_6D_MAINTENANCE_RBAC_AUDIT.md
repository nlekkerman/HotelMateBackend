# Phase 6D — Maintenance RBAC Deep Audit

Source of truth: code only (`maintenance/`, `staff/permissions.py`,
`staff/capability_catalog.py`, `staff/module_policy.py`,
`staff/nav_catalog.py`, `staff_urls.py`, `notifications/`).
No frontend changes. No code modifications. Audit only.

---

## 0. Module Footprint (verified from code)

The Maintenance app is dramatically smaller than the prompt template implies.
None of the following exist on disk:

- `maintenance/services.py` — absent
- `maintenance/policy.py` — absent
- `maintenance/signals.py` — absent
- `maintenance/staff_urls.py` — absent (mounted via `STAFF_APPS` loop in
  [staff_urls.py](staff_urls.py#L48-L62) using `maintenance.urls`)
- `maintenance/business_rules.py` / state machine module — absent

Files actually present in [maintenance/](maintenance/):
`__init__.py`, `admin.py`, `apps.py`, `models.py`, `serializers.py`,
`urls.py`, `views.py`, `tests.py`, `migrations/`.

There is **no signal handler, no NotificationManager call, no Pusher
trigger, no service layer, and no Room mutation** anywhere in the
Maintenance app. The `notify_maintenance_staff` helper in
[notifications/pusher_utils.py](notifications/pusher_utils.py#L165-L177)
exists but is **not invoked from the Maintenance app**.

---

## 1. Endpoint Inventory

URL prefix (from [staff_urls.py](staff_urls.py#L260-L268) +
[maintenance/urls.py](maintenance/urls.py#L1-L12)):
`/api/staff/hotel/<hotel_slug>/maintenance/…`

All three viewsets are unrestricted `ModelViewSet`s — i.e. DRF auto-routes
list/retrieve/create/update/partial_update/destroy.

| URL | Method | View / action | Serializer | Service fn | Permission classes | Inline checks |
|-----|--------|---------------|------------|------------|--------------------|---------------|
| `requests/` | GET | `MaintenanceRequestViewSet.list` | `MaintenanceRequestSerializer` | — | `IsAuthenticated, HasMaintenanceNav, IsStaffMember, IsSameHotel` | — |
| `requests/` | POST | `MaintenanceRequestViewSet.create` → `perform_create` | `MaintenanceRequestSerializer` | inline (auto-stamp `reported_by`, `hotel`) | same | requires `staff_profile`, else `PermissionDenied` ([maintenance/views.py](maintenance/views.py#L22-L31)) |
| `requests/{pk}/` | GET | `retrieve` | same | — | same | — |
| `requests/{pk}/` | PUT | `update` → `perform_update` | same | inline (auto-stamp `accepted_by` when `status == "in_progress"` and `accepted_by is None`) | same | requires `staff_profile` only on the accept branch ([maintenance/views.py](maintenance/views.py#L33-L43)) |
| `requests/{pk}/` | PATCH | `partial_update` → `perform_update` | same | same | same | same |
| `requests/{pk}/` | DELETE | `destroy` | — | — | same | — |
| `comments/` | GET | `MaintenanceCommentViewSet.list` | `MaintenanceCommentSerializer` | — | same | queryset scoped to `request.user.staff_profile.hotel` ([maintenance/views.py](maintenance/views.py#L51-L55)) |
| `comments/` | POST | `create` → `perform_create` | same | — | same | requires `staff_profile`; auto-stamps `staff` ([maintenance/views.py](maintenance/views.py#L57-L61)) |
| `comments/{pk}/` | GET / PUT / PATCH / DELETE | `retrieve`/`update`/`partial_update`/`destroy` | same | — | same | none beyond hotel queryset filter |
| `photos/` | GET | `MaintenancePhotoViewSet.list` | `MaintenancePhotoSerializer` | — | same | queryset scoped to user’s hotel ([maintenance/views.py](maintenance/views.py#L70-L73)) |
| `photos/` | POST | `MaintenancePhotoViewSet.create` (overridden — bulk) | `BulkMaintenancePhotoSerializer` | inline create-many | same | requires `staff_profile` ([maintenance/views.py](maintenance/views.py#L75-L83)) |
| `photos/{pk}/` | GET / PUT / PATCH / DELETE | DRF defaults | `MaintenancePhotoSerializer` | — | same | hotel queryset filter only |

Every viewset is a `ModelViewSet` with **no `http_method_names`
restriction**, so PUT/PATCH/DELETE on requests, comments, and photos
are **all live**.

---

## 2. Real Action Map (extracted from code only)

The prompt’s template list (assign technician, set priority, mark room
out of order, clear room maintenance, cancel/close, completion timestamps,
bulk operations, etc.) is **not represented in the Maintenance code**.

What the code actually supports:

| Real action | Trigger endpoint | Mutation | Side effects | Realtime | Room/HK state |
|-------------|-----------------|----------|--------------|----------|---------------|
| List maintenance requests | `GET requests/` | — | — | none | — |
| Read single request | `GET requests/{pk}/` | — | — | none | — |
| Create request | `POST requests/` | new `MaintenanceRequest` row; auto `reported_by = staff_profile`, `hotel = staff_profile.hotel` | none | none | none |
| Edit request fields (title/description/room/location_note/status/accepted_by) | `PUT/PATCH requests/{pk}/` | mutates any writable field | if `status="in_progress"` and `accepted_by` is null, auto-stamps `accepted_by = staff_profile` | none | none |
| “Accept” a request | `PATCH requests/{pk}/ {status:"in_progress"}` | sets status + auto-stamps `accepted_by` | — | none | none |
| Resolve / close request | `PATCH requests/{pk}/ {status:"resolved" | "closed"}` | status change only | none | none | none |
| Reopen | `PATCH requests/{pk}/ {status:"open"}` | status change only | none | none | none |
| Delete request | `DELETE requests/{pk}/` | row delete (cascades to comments + photos) | — | none | none |
| List comments | `GET comments/` | — | hotel-scoped | none | — |
| Add comment | `POST comments/` | new `MaintenanceComment`; auto `staff = staff_profile` | — | none | none |
| Edit / delete comment | `PUT/PATCH/DELETE comments/{pk}/` | row mutation/delete | none | none | none |
| List photos | `GET photos/` | — | hotel-scoped | none | — |
| Bulk upload photos | `POST photos/` (Bulk serializer) | N×`MaintenancePhoto` rows; auto `uploaded_by = staff_profile` | Cloudinary upload | none | none |
| Edit / delete photo | `PUT/PATCH/DELETE photos/{pk}/` | row mutation/delete | none | none | none |

**Actions in the prompt that do NOT exist in code:**
- assign technician (no `assigned_to` field; `accepted_by` is self-claim only)
- set priority (no `priority` field)
- start work / complete work as discrete endpoints (only generic PATCH)
- cancel as a discrete action (only `status="closed"` via PATCH)
- mark room out of order / clear room maintenance — these belong to the
  `rooms`/`housekeeping` modules (`room.maintenance.flag` /
  `room.maintenance.clear`, see
  [staff/capability_catalog.py](staff/capability_catalog.py#L222-L226)),
  **not Maintenance**. Maintenance never touches `Room.maintenance_required`.
- bulk operations on requests (only photo upload is bulk)

---

## 3. Current Permission Model

For every endpoint listed above the gate set is **identical**:

```python
permission_classes = [IsAuthenticated, HasMaintenanceNav, IsStaffMember, IsSameHotel]
```

(Confirmed at [maintenance/views.py L18, L49, L67](maintenance/views.py#L18).)

| Layer | Present? | Notes |
|-------|----------|-------|
| Capability gates | **NONE** | No `HasCapability` subclass used anywhere in maintenance |
| Nav gates | `HasMaintenanceNav` (no `safe_methods_bypass`, gates reads + writes) | Defined at [staff/permissions.py L514-L516](staff/permissions.py#L514-L516); `HasNavPermission.has_permission` at [staff/permissions.py L268-L282](staff/permissions.py#L268-L282) does NOT skip writes — nav alone is currently the sole authorization for every mutation |
| Tier gates | **NONE applied** | `CanManageMaintenance` (tier-based, `staff_admin` floor, [staff/permissions.py L467-L478](staff/permissions.py#L467-L478)) is imported at [maintenance/views.py L10](maintenance/views.py#L10) but **never placed in any `permission_classes` list** — dead code |
| Role-string gates | None | No `request.user.staff_profile.role.slug == ...` checks |
| Object-level perms | None | No `has_object_permission` overrides |

### Flagged

- **Nav leak (CRITICAL):** `HasMaintenanceNav` is the only authority on
  every write. Per
  [staff/permissions.py L9-L13](staff/permissions.py#L9-L13) module
  visibility “MUST NEVER grant mutation authority” — Maintenance is the
  textbook violation. Anyone with the `maintenance` nav slug can
  create/update/delete requests, comments, and photos, including changing
  `status` and `accepted_by` for any request in their hotel.
- **Decorative tier gate:** `CanManageMaintenance` exists but is not
  wired. Even if it were wired, it would be a **tier leak** (it grants
  authority by tier alone — exactly the pattern Phase 6 is retiring).
- **Over-permissioned flows:** any nav-holder can DELETE a request,
  cascade-deleting all comments and photos, with no audit trail and no
  capability check.
- **Under-protected flows:** every status transition is unguarded; an
  ordinary staff member can resolve or close any ticket regardless of
  reporter, accepter, or department.
- **Inconsistent inline check:** `perform_create` raises
  `PermissionDenied` if `staff_profile` is missing, but
  `IsStaffMember` already enforces the same precondition — defensive
  duplicate, harmless.

---

## 4. State Machine Discovery

Status field is `MaintenanceRequest.status` ([maintenance/models.py L11-L16, L39](maintenance/models.py#L11-L16)).

Statuses: `open`, `in_progress`, `resolved`, `closed` (default `open`).

**There is no formal state machine** — no `business_rules.py`, no
service-layer guards, no `clean()` validation. The only transition
behavior is in `MaintenanceRequestViewSet.perform_update`
([maintenance/views.py L33-L43](maintenance/views.py#L33-L43)):

- If incoming `status == "in_progress"` AND `instance.accepted_by is None`,
  `accepted_by` is set to the requester’s `staff_profile`.
- Every other status change saves through unchanged.

| Transition | Allowed by code? | Who can trigger | Mutates room/HK? |
|------------|------------------|-----------------|------------------|
| `open → in_progress` | yes (PATCH) | any user with `HasMaintenanceNav` | no |
| `open → resolved` | yes (PATCH) | same | no |
| `open → closed` | yes (PATCH) | same | no |
| `in_progress → resolved` | yes | same | no |
| `in_progress → open` | yes (no guard) | same | no |
| `in_progress → closed` | yes | same | no |
| `resolved → *` (any) | yes (no guard) | same | no |
| `closed → *` (any reopen) | yes (no guard) | same | no |
| Reassign `accepted_by` (force a different staff) | yes (writable in serializer) | same | no |

**No transition mutates `Room.status`, `Room.maintenance_required`,
`Room.maintenance_priority`, or `Room.maintenance_notes`.** Those Room
fields are only manipulated through the `housekeeping` and `rooms`
modules — separate from this app.

---

## 5. Capability Proposal

Every proposed capability below maps to a real endpoint in code; nothing
decorative.

```python
# staff/capability_catalog.py (proposed, namespace: maintenance.*)

# Nav / read
MAINTENANCE_MODULE_VIEW       = 'maintenance.module.view'
MAINTENANCE_REQUEST_READ      = 'maintenance.request.read'

# Operate (line technician self-service)
MAINTENANCE_REQUEST_CREATE    = 'maintenance.request.create'
MAINTENANCE_REQUEST_ACCEPT    = 'maintenance.request.accept'      # status → in_progress (self-claim)
MAINTENANCE_REQUEST_RESOLVE   = 'maintenance.request.resolve'     # status → resolved
MAINTENANCE_COMMENT_CREATE    = 'maintenance.comment.create'
MAINTENANCE_PHOTO_UPLOAD      = 'maintenance.photo.upload'

# Supervise
MAINTENANCE_REQUEST_UPDATE    = 'maintenance.request.update'      # edit title/desc/room/location_note
MAINTENANCE_REQUEST_REASSIGN  = 'maintenance.request.reassign'    # change accepted_by
MAINTENANCE_REQUEST_REOPEN    = 'maintenance.request.reopen'      # resolved/closed → open/in_progress
MAINTENANCE_COMMENT_MODERATE  = 'maintenance.comment.moderate'    # edit/delete others' comments
MAINTENANCE_PHOTO_DELETE      = 'maintenance.photo.delete'

# Manage (destructive / lifecycle close-out)
MAINTENANCE_REQUEST_CLOSE     = 'maintenance.request.close'       # status → closed
MAINTENANCE_REQUEST_DELETE    = 'maintenance.request.delete'
```

Capabilities **explicitly NOT proposed** because no code supports them
(would be decorative):

- `maintenance.priority.set` — no `priority` field on `MaintenanceRequest`.
- `maintenance.issue.assign` (assign-to-technician) — no `assigned_to`
  field; only the self-claim flow exists. (Reassign cap above covers
  the only writable assignment surface, `accepted_by`.)
- `maintenance.room.out_of_order.set` / `maintenance.room.clear` — these
  already exist as `room.maintenance.flag` / `room.maintenance.clear`
  in the rooms namespace ([staff/capability_catalog.py L222-L226](staff/capability_catalog.py#L222-L226))
  and are enforced in the rooms/housekeeping module, not here.
- `maintenance.bulk.operate` — no bulk-mutation endpoint exists
  (bulk-photo upload would be `MAINTENANCE_PHOTO_UPLOAD`).
- `maintenance.dashboard.read` — no dashboard endpoint exists; collapse
  into `MAINTENANCE_REQUEST_READ`.

---

## 6. Enforcement Mapping (proposed)

| Capability | Endpoint | View / action | Service / policy enforcement |
|------------|----------|---------------|------------------------------|
| `maintenance.module.view` | every `maintenance/*` | viewset gate (replaces nav-only) | new `CanViewMaintenance(HasCapability)` with `safe_methods_bypass=False` |
| `maintenance.request.read` | `GET requests/`, `GET requests/{pk}/`, `GET comments/`, `GET photos/` | list / retrieve | `CanReadMaintenance` |
| `maintenance.request.create` | `POST requests/` | `perform_create` | `CanCreateMaintenanceRequest` |
| `maintenance.request.accept` | `PATCH requests/{pk}/` with `status="in_progress"` | `perform_update` accept branch | payload-aware permission (see §7) |
| `maintenance.request.resolve` | `PATCH requests/{pk}/` with `status="resolved"` | `perform_update` | payload-aware |
| `maintenance.request.update` | `PATCH/PUT requests/{pk}/` writable non-action fields | `update` | payload-aware |
| `maintenance.request.reassign` | `PATCH requests/{pk}/` with `accepted_by` change | `perform_update` | payload-aware (compare instance.accepted_by) |
| `maintenance.request.reopen` | `PATCH` from terminal state back to active | `perform_update` | payload-aware (read instance.status) |
| `maintenance.request.close` | `PATCH requests/{pk}/` with `status="closed"` | `perform_update` | payload-aware |
| `maintenance.request.delete` | `DELETE requests/{pk}/` | `destroy` | `CanDeleteMaintenanceRequest` |
| `maintenance.comment.create` | `POST comments/` | `perform_create` | `CanCommentMaintenance` |
| `maintenance.comment.moderate` | `PUT/PATCH/DELETE comments/{pk}/` not authored by self | `update`/`destroy` | object-level guard |
| `maintenance.photo.upload` | `POST photos/` (Bulk) | `create` override | `CanUploadMaintenancePhoto` |
| `maintenance.photo.delete` | `DELETE photos/{pk}/` | `destroy` | `CanModerateMaintenancePhoto` |

`MODULE_POLICY['maintenance']` is currently **absent** from
[staff/module_policy.py](staff/module_policy.py); add an entry shaped like
`bookings`/`rooms`/`housekeeping`.

---

## 7. PATCH / Serializer Drift Risks

[`MaintenanceRequestSerializer`](maintenance/serializers.py#L37-L51):

```python
fields = ['id','hotel','room','location_note','title','description',
          'reported_by','accepted_by','status','created_at','updated_at',
          'comments','photos']
read_only_fields = ['id','hotel','reported_by','created_at','updated_at']
```

Writable action-bearing fields exposed to a generic `PATCH /requests/{pk}/`:

| Field | Risk |
|-------|------|
| `status` | A holder of `maintenance.request.update` (proposed) could close, resolve, reopen any ticket. Today: any nav-holder can. **Must be split out behind action capabilities.** |
| `accepted_by` | Writable, despite being declared `StaffSerializer(read_only=True)` on the **viewset class body** (see [maintenance/views.py L20-L21](maintenance/views.py#L20-L21)) — that declaration is on the *viewset*, not the serializer, so it has **no effect**. Any nav-holder can set `accepted_by` to any Staff PK (including cross-hotel — see §8). |
| `room` | Writable. No validation that the room belongs to the same hotel (`PrimaryKeyRelatedField` defaults to global `Room.objects.all()` queryset). |
| `title` / `description` / `location_note` | Bare content edits — acceptable behind a single `update` cap. |

Other fields explicitly **not** present (and therefore not at risk via
PATCH): `priority`, `assigned_to`, completion timestamps,
cancellation_reason, out-of-order flags. The risk surface is narrower
than typical because the model is thin.

### Recommendation

Apply the same payload-aware split used in Rooms 6B.2 / Housekeeping 6C:

1. Mark `status` and `accepted_by` as `read_only` on
   `MaintenanceRequestSerializer`.
2. Expose discrete action endpoints (DRF `@action` methods on the
   viewset) for the verbs in §5: `accept`, `resolve`, `reopen`, `close`,
   `reassign`. Each enforces its own capability.
3. Generic `PUT/PATCH requests/{pk}/` becomes a metadata-only edit
   gated by `maintenance.request.update`.

---

## 8. Cross-Hotel / Tenant Isolation Risks

| Lookup | Where | Scoped? |
|--------|-------|---------|
| `MaintenanceRequest` queryset (viewset list/retrieve) | `HotelScopedQuerysetMixin.get_queryset` ([common/mixins.py L36-L38](common/mixins.py#L36-L38)) — filters by `request.user.staff_profile.hotel` | **YES** |
| `MaintenanceComment` queryset | viewset override filters by `staff_profile.hotel` ([maintenance/views.py L52-L55](maintenance/views.py#L52-L55)) | **YES** |
| `MaintenancePhoto` queryset | viewset override filters by `staff_profile.hotel` ([maintenance/views.py L70-L73](maintenance/views.py#L70-L73)) | **YES** |
| `MaintenancePhotoSerializer.request` (PrimaryKeyRelatedField) | default queryset = `MaintenancePhoto._meta.get_field('request').remote_field.model.objects.all()` → unscoped | **NO — cross-hotel leak** |
| `BulkMaintenancePhotoSerializer.request` | `PrimaryKeyRelatedField(queryset=MaintenanceRequest.objects.all())` ([maintenance/serializers.py L15](maintenance/serializers.py#L15)) | **NO — cross-hotel leak** |
| `MaintenanceCommentSerializer.request` | implicit `PrimaryKeyRelatedField` from `ModelSerializer` over `MaintenanceComment.request` → unscoped | **NO — cross-hotel leak** |
| `MaintenanceRequestSerializer.room` | implicit PRF over `Room.objects.all()` — unscoped | **NO — cross-hotel/cross-room leak** |
| `MaintenanceRequestSerializer.accepted_by` | implicit PRF over `Staff.objects.all()` — unscoped | **NO — cross-hotel staff assignment** |

**Concrete attack paths a present-day staff member with `HasMaintenanceNav` can execute:**

1. `POST comments/ {request: <PK in another hotel>, message: "..."}` — staff in
   hotel A can leave comments on a request belonging to hotel B; the
   `staff` field auto-stamps to the attacker. The `get_queryset` filter
   then hides the comment from the attacker’s list view, but the row
   exists in hotel B and shows up there.
2. `POST photos/` Bulk with foreign `request` PK — same cross-hotel write.
3. `PATCH requests/{pk}/ {accepted_by: <Staff PK in another hotel>}` —
   assigns a hotel-B staffer as the accepter of a hotel-A ticket.
4. `PATCH requests/{pk}/ {room: <Room PK in another hotel>}` — links a
   hotel-A ticket to a hotel-B room (`MaintenanceRequest.hotel` stays at
   hotel A; the `room` FK now crosses tenants).

The `HotelScopedQuerysetMixin.perform_create` ([common/mixins.py L40-L42](common/mixins.py#L40-L42))
is overridden by `MaintenanceRequestViewSet.perform_create`, so request
creation correctly stamps the attacker’s own hotel — **but the attacker
can still set the `room` FK to a foreign-hotel room in the same call.**

---

## 9. Gap Analysis

Blockers for a clean Phase 6D RBAC migration:

1. **No maintenance capabilities exist.** Catalog has zero
   `maintenance.*` slugs; only `room.maintenance.flag/clear` (which
   belong to the rooms module).
2. **No maintenance `MODULE_POLICY` entry.** Frontend cannot render
   action booleans for this module today.
3. **`HasMaintenanceNav` is the sole gate on every mutation** — nav
   leak in violation of `staff/permissions.py` contract preamble.
4. **`CanManageMaintenance` is decorative** — defined and imported but
   never wired; would also be a tier leak if wired.
5. **State transitions are unguarded.** Any nav-holder can flip a
   ticket through any status combination, including reopening closed
   tickets, with no audit.
6. **`status` and `accepted_by` are writable on the generic serializer**
   — must be removed in favor of payload-aware action endpoints.
7. **Cross-hotel writable surface** in three serializer fields
   (`MaintenanceCommentSerializer.request`,
   `MaintenancePhotoSerializer.request` /
   `BulkMaintenancePhotoSerializer.request`,
   `MaintenanceRequestSerializer.room` and `accepted_by`). Querysets must
   be hotel-scoped via `get_serializer_context()` + custom field, or via
   `validate_<field>`.
8. **No object-level permissions on comments/photos.** A nav-holder can
   edit/delete any other staff member’s comment or photo within their
   hotel.
9. **Dead `notify_maintenance_staff`** — the helper exists in
   `notifications/pusher_utils.py` but Maintenance never produces realtime
   events. Either wire it (after RBAC) or document the gap.
10. **Naming drift risk:** the rooms namespace already owns
    `room.maintenance.flag` / `room.maintenance.clear`. Any Phase 6D
    capabilities must stay in the `maintenance.*` namespace and never
    duplicate room-state authority.
11. **Module-tier preset coverage missing.** `maintenance_staff`,
    `maintenance_supervisor`, `maintenance_manager` roles exist in
    [staff/role_catalog.py L74-L84](staff/role_catalog.py#L74-L84) and
    role presets in
    [staff/capability_catalog.py L483-L488](staff/capability_catalog.py#L483-L488)
    only carry `room.maintenance.*` (Phase 6B.1) — they grant **zero**
    `maintenance.*` capabilities (because none exist). Departments and
    role presets must be extended once the catalog is added.

---

## 10. Final Verdict

**READY for RBAC implementation? NO.**

Maintenance is the most under-protected mutation surface in the codebase
audited so far. It has no capabilities, no policy entry, no payload-aware
gates, and three cross-hotel write vectors via unsafely-defaulted
`PrimaryKeyRelatedField`s.

### Blocking issues (must fix before / during 6D)

- B1. Add the `maintenance.*` capability slugs in §5 to
  `staff/capability_catalog.py` and register them in `CANONICAL_CAPABILITIES`.
- B2. Add `'maintenance'` entry to `MODULE_POLICY` in
  `staff/module_policy.py` matching the bookings/rooms/housekeeping shape.
- B3. Replace nav-only gates on every viewset with capability gates
  (`CanViewMaintenance`, `CanReadMaintenance` + per-action classes).
- B4. Remove (or repurpose) the dead `CanManageMaintenance` tier class —
  do **not** wire it; tier must not gate maintenance actions.
- B5. Make `status` and `accepted_by` `read_only` on
  `MaintenanceRequestSerializer`; add `@action` endpoints `accept`,
  `resolve`, `reopen`, `close`, `reassign` each enforcing its own cap.
- B6. Hotel-scope the four leaky serializer FK fields (`request` on
  comment, photo, bulk photo serializers; `room` and `accepted_by` on
  request serializer). Validate that the related row’s `hotel` matches
  `request.user.staff_profile.hotel`.
- B7. Add object-level permission for comment/photo edit & delete
  (author-or-`maintenance.comment.moderate` / `maintenance.photo.delete`).

### Recommended capability list (final)

```
maintenance.module.view
maintenance.request.read
maintenance.request.create
maintenance.request.accept
maintenance.request.resolve
maintenance.request.update
maintenance.request.reassign
maintenance.request.reopen
maintenance.request.close
maintenance.request.delete
maintenance.comment.create
maintenance.comment.moderate
maintenance.photo.upload
maintenance.photo.delete
```

### Recommended implementation order

1. Land catalog additions + `MODULE_POLICY['maintenance']` (no behavior
   change yet — frontend can begin reading the policy shape).
2. Map role/department presets:
   - `maintenance` department preset → read + create + accept + resolve
     + comment.create + photo.upload.
   - `maintenance_supervisor` role → + update + reassign + reopen +
     comment.moderate + photo.delete.
   - `maintenance_manager` role → + close + delete.
   - `regular_staff` (cross-department reporters): grant
     `maintenance.module.view`, `maintenance.request.read`,
     `maintenance.request.create` only (so reception/HK can file
     tickets but not action them).
3. Patch serializer drift (B5, B6) — independent change, no caps needed.
4. Wire payload-aware permission classes on the existing PATCH path
   AND add the new `@action` endpoints. Keep nav gate (`CanViewMaintenance`)
   as the read-side authority.
5. Remove dead `CanManageMaintenance` import + class (or convert to a
   thin shim alias for B3 caps and mark deprecated).
6. Backfill tests (`maintenance/tests.py` is currently a
   one-line stub) for: cross-hotel rejection, status-action capability
   gating, dead-end nav-only writes failing.
7. (Optional, separate from 6D) Wire `notify_maintenance_staff` to
   capture status transitions for realtime dashboards once the action
   endpoints exist.
