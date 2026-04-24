# Phase 6C — Housekeeping RBAC Deep Audit (Code-Verified)

Source of truth used for this audit:

- `housekeeping/views.py`
- `housekeeping/staff_urls.py`
- `housekeeping/services.py`
- `housekeeping/policy.py`
- `housekeeping/serializers.py`
- `housekeeping/models.py`
- `staff/permissions.py`
- `staff/capability_catalog.py`
- `staff/module_policy.py`

No comments, naming heuristics, or documentation were trusted — every claim
below traces to a function definition or class body in the files above.

---

## 1. Endpoint Inventory

All housekeeping URLs are mounted under
`/api/staff/hotel/{hotel_slug}/housekeeping/` via `housekeeping/staff_urls.py`.

### 1.1 `GET /housekeeping/dashboard/`

- View: `HousekeepingDashboardViewSet.list`
- Serializer: returns dict; references `HousekeepingTaskSerializer` for tasks
- Service: `get_room_dashboard_data(hotel)`
- Permissions: `IsAuthenticated, HasHousekeepingNav, IsStaffMember, IsSameHotel`
- Notes: Branches on `staff.access_level in ['staff_admin','super_staff_admin']`
  to additionally include `open_tasks` (tier leak — see §7).

### 1.2 `GET /housekeeping/tasks/`  (list)

- View: `HousekeepingTaskViewSet.list`
- Serializer: `HousekeepingTaskSerializer`
- Service: queryset filtered by `staff.hotel`
- Permissions: `IsAuthenticated, HasNavPermission('housekeeping'), IsStaffMember, IsSameHotel`

### 1.3 `GET /housekeeping/tasks/{id}/`  (retrieve)

- View: `HousekeepingTaskViewSet.retrieve`
- Serializer: `HousekeepingTaskSerializer`
- Permissions: same as list (no extra gate).

### 1.4 `POST /housekeeping/tasks/`  (create)

- View: `HousekeepingTaskViewSet.create` (DRF default)
- Serializer: `HousekeepingTaskSerializer`
- Service: `perform_create` injects `hotel` and `created_by` from `staff_profile`
- Permissions: nav chain + `CanManageHousekeeping`

### 1.5 `PUT /housekeeping/tasks/{id}/` and `PATCH /housekeeping/tasks/{id}/`

- View: `HousekeepingTaskViewSet.update` / `partial_update`
- Serializer: `HousekeepingTaskSerializer`
- Permissions: nav chain + `CanManageHousekeeping`

### 1.6 `DELETE /housekeeping/tasks/{id}/`

- View: `HousekeepingTaskViewSet.destroy`
- Permissions: nav chain + `CanManageHousekeeping`

### 1.7 `POST /housekeeping/tasks/{id}/assign/`

- View: `HousekeepingTaskViewSet.assign` (`@action(detail=True, methods=['post'])`)
- Serializer: `HousekeepingTaskAssignSerializer` (calls `policy.can_assign_task`)
- Permissions: nav chain + `CanManageHousekeeping`

### 1.8 `POST /housekeeping/tasks/{id}/start/`

- View: `HousekeepingTaskViewSet.start`
- Serializer: none (raw `request.data`)
- Permissions: nav chain only (action NOT in `management_actions` set;
  `CanManageHousekeeping` not appended)
- Inline check: `task.assigned_to and task.assigned_to != staff` → 403;
  `task.status != 'OPEN'` → 400.

### 1.9 `POST /housekeeping/tasks/{id}/complete/`

- View: `HousekeepingTaskViewSet.complete`
- Serializer: none
- Permissions: nav chain only
- Inline check: `task.assigned_to != staff` → 403;
  `task.status != 'IN_PROGRESS'` → 400.

### 1.10 `POST /housekeeping/rooms/{room_id}/status/`

- View: `RoomStatusViewSet.update_status` (mapped via
  `RoomStatusViewSet.as_view({'post': 'update_status'})`)
- Serializer: `RoomStatusUpdateSerializer` (calls `can_change_room_status`)
- Service: `set_room_status(room=…, to_status=…, staff=…, source=…, note=…)`
- Permissions: `IsAuthenticated, HasHousekeepingNav, IsStaffMember, IsSameHotel`
  (no action-level class — gate is the capability check inside `policy.py`).

### 1.11 `POST /housekeeping/rooms/{room_id}/manager_override/`

- View: `RoomStatusViewSet.manager_override`
- Serializer: none (reads `to_status`, `note` from `request.data`)
- Service: `set_room_status(..., source="MANAGER_OVERRIDE", note=note)`
- Permissions: nav chain + `CanManageHousekeeping`
- Authority gate inside service: `housekeeping.room_status.override` capability.

### 1.12 `GET /housekeeping/rooms/{room_id}/status-history/`

- View: `RoomStatusViewSet.status_history`
- Serializer: `RoomStatusEventSerializer`
- Permissions: nav chain only.

---

## 2. Action Map (real system behaviour)

Every action below is grounded in a function in `housekeeping/views.py`,
`housekeeping/services.py`, or `housekeeping/policy.py`.

### Action: `view_dashboard`
- Triggered by: `GET /housekeeping/dashboard/`
- Code: `HousekeepingDashboardViewSet.list`
- Mutation: none
- Side effects: tier-conditional payload (`open_tasks` only for `staff_admin+`).

### Action: `list_tasks` / `retrieve_task`
- Triggered by: `GET /housekeeping/tasks/[/{id}]`
- Code: `HousekeepingTaskViewSet.list/retrieve`
- Mutation: none

### Action: `create_task`
- Triggered by: `POST /housekeeping/tasks/`
- Code: `HousekeepingTaskViewSet.create` + `perform_create`
- Mutation: insert `HousekeepingTask`

### Action: `update_task` / `partial_update_task`
- Triggered by: `PUT|PATCH /housekeeping/tasks/{id}/`
- Code: `HousekeepingTaskViewSet.update/partial_update`
- Mutation: any writable field on `HousekeepingTaskSerializer`
  (`hotel` is read-only; mutable: `room, booking, task_type, status,
  priority, assigned_to, note, created_by, started_at, completed_at`).

### Action: `delete_task`
- Triggered by: `DELETE /housekeeping/tasks/{id}/`
- Mutation: row delete

### Action: `assign_task`
- Triggered by: `POST /housekeeping/tasks/{id}/assign/`
- Code: `HousekeepingTaskViewSet.assign` → `HousekeepingTaskAssignSerializer`
  → `policy.can_assign_task`
- Mutation: `task.assigned_to = …; save(update_fields=['assigned_to'])`
- Capability checked in serializer: `housekeeping.task.assign`

### Action: `start_task`
- Triggered by: `POST /housekeeping/tasks/{id}/start/`
- Mutation: `task.status = 'IN_PROGRESS'`, `started_at = now`,
  `assigned_to = staff` if previously null.

### Action: `complete_task`
- Triggered by: `POST /housekeeping/tasks/{id}/complete/`
- Mutation: `task.status = 'DONE'`, `completed_at = now`.

### Action: `transition_room_status`
- Triggered by: `POST /housekeeping/rooms/{room_id}/status/`
- Code: `RoomStatusViewSet.update_status` → `set_room_status`
- Mutation: `room.room_status` and side-effect fields:
  - to `CLEANED_UNINSPECTED`: `last_cleaned_at`, `cleaned_by_staff`
  - to `READY_FOR_GUEST`: `last_inspected_at`, `inspected_by_staff`,
    clears `maintenance_required`, `maintenance_priority`,
    `maintenance_notes`, sets `is_active=True`, `is_out_of_order=False`,
    conditionally clears `is_occupied`.
  - to `MAINTENANCE_REQUIRED`: `maintenance_required=True`, appends
    `maintenance_notes`.
- Side effects: writes a `RoomStatusEvent` audit row; emits
  `notification_manager.realtime_room_updated` on commit.
- Capability gate (inside `policy.can_change_room_status`):
  one of `housekeeping.room_status.override`,
  `housekeeping.room_status.transition`,
  `housekeeping.room_status.front_desk`.

### Action: `manager_override_room_status`
- Triggered by: `POST /housekeeping/rooms/{room_id}/manager_override/`
- Code: `RoomStatusViewSet.manager_override` → `set_room_status(..., source='MANAGER_OVERRIDE')`
- Mutation: same as `transition_room_status`.
- Capability gate: `housekeeping.room_status.override` (note required).

### Action: `view_room_status_history`
- Triggered by: `GET /housekeeping/rooms/{room_id}/status-history/`
- Mutation: none.

---

## 3. Current Permission Model (real, not intended)

| Endpoint | DRF `permission_classes` | Inline / service gates | Tier / nav / role leaks |
| --- | --- | --- | --- |
| `dashboard` GET | `IsAuthenticated, HasHousekeepingNav, IsStaffMember, IsSameHotel` | branches on `staff.access_level in ['staff_admin','super_staff_admin']` for `open_tasks` | ❌ tier leak (access_level) |
| `tasks` GET | `IsAuthenticated, HasNavPermission('housekeeping'), IsStaffMember, IsSameHotel` | none | nav-only on read (acceptable) |
| `tasks` POST/PUT/PATCH/DELETE | nav chain + `CanManageHousekeeping` | none | ❌ `CanManageHousekeeping` is a **tier check** (`_tier_at_least(tier,'staff_admin')`) — no capability used |
| `tasks/{id}/assign` POST | nav chain + `CanManageHousekeeping` | `can_assign_task` (capability `housekeeping.task.assign`) | ❌ double gate: tier *and* capability; serializer-level cap is correct, the class-level tier check is unjustified |
| `tasks/{id}/start` POST | nav chain only | `task.assigned_to == request.staff` or `assigned_to is None` | ❌ no capability check — any staff with the `housekeeping` nav can start any unassigned task |
| `tasks/{id}/complete` POST | nav chain only | same as start | ❌ no capability check |
| `rooms/{id}/status` POST | nav chain only | `policy.can_change_room_status` (3 capabilities) | ✅ capability-driven |
| `rooms/{id}/manager_override` POST | nav chain + `CanManageHousekeeping` | `policy.can_change_room_status` (override capability + note required) | ❌ class-level **tier** check duplicates and shadows capability; tier authority is not the contract truth |
| `rooms/{id}/status-history` GET | nav chain only | none | nav-only on read (acceptable) |

### Concrete violations (literal lines)

- `housekeeping/views.py` `HousekeepingDashboardViewSet.list`:
  `if staff.access_level in ['staff_admin', 'super_staff_admin']:` — **tier
  string check**.
- `staff/permissions.py::CanManageHousekeeping.has_permission`:
  `tier = resolve_tier(request.user); return _tier_at_least(tier, 'staff_admin')`
  — **tier-only gate**, no capability. Used on:
  - task `create / update / partial_update / destroy / assign`
  - `RoomStatusViewSet.manager_override`
- `HousekeepingTaskViewSet.start` and `.complete`: no action-level
  permission class beyond the nav chain. Inline check is *self-service
  consistency* (cannot grab someone else's task) but does **not** enforce
  any housekeeping capability — a staff member with the `housekeeping`
  nav slug but zero housekeeping capabilities can start/complete an
  unassigned task.

---

## 4. State Machine Discovery

### 4.1 `Room.room_status` (housekeeping flow)

Reconstructed from `housekeeping/policy.py::_can_housekeeping_change_status`
and `_can_front_desk_change_status`. The actual gate
`room.can_transition_to(to_status)` lives on `rooms.models.Room` (out of
this audit's scope, but referenced).

States observed in code:

- `CHECKOUT_DIRTY`
- `CLEANING_IN_PROGRESS`
- `CLEANED_UNINSPECTED`
- `READY_FOR_GUEST`
- `OCCUPIED`
- `MAINTENANCE_REQUIRED`

#### Housekeeping workflow matrix (`housekeeping.room_status.transition`)

| From | Allowed To | Triggered via |
| --- | --- | --- |
| `CHECKOUT_DIRTY` | `CLEANING_IN_PROGRESS`, `MAINTENANCE_REQUIRED` | `update_status` |
| `CLEANING_IN_PROGRESS` | `CLEANED_UNINSPECTED`, `CHECKOUT_DIRTY` (rollback), `MAINTENANCE_REQUIRED` | `update_status` |
| `CLEANED_UNINSPECTED` | `READY_FOR_GUEST`, `MAINTENANCE_REQUIRED` | `update_status` |
| `READY_FOR_GUEST` | `MAINTENANCE_REQUIRED` | `update_status` |
| `OCCUPIED` | `MAINTENANCE_REQUIRED` | `update_status` |
| Any | `MAINTENANCE_REQUIRED` (fall-through) | `update_status` |

#### Front desk matrix (`housekeeping.room_status.front_desk`)

Hard-forbidden targets: `READY_FOR_GUEST`, `CLEANED_UNINSPECTED`,
`CLEANING_IN_PROGRESS`.

| From | Allowed To |
| --- | --- |
| `OCCUPIED` | `CHECKOUT_DIRTY`, `MAINTENANCE_REQUIRED` |
| `READY_FOR_GUEST` | `MAINTENANCE_REQUIRED` |

#### Override (`housekeeping.room_status.override`)

Any transition `room.can_transition_to(to_status)` allows. When
`source == 'MANAGER_OVERRIDE'`, a non-empty `note` is required (gate is
duplicated in `policy.can_change_room_status` and
`RoomStatusUpdateSerializer.validate`).

### 4.2 `HousekeepingTask.status`

- States: `OPEN, IN_PROGRESS, DONE, CANCELLED` (`HousekeepingTask.STATUS_CHOICES`).
- Transitions enforced in code:
  - `OPEN → IN_PROGRESS` via `start` (only if assignee matches or unassigned).
  - `IN_PROGRESS → DONE` via `complete` (only if assignee matches).
- `CANCELLED` is declared in choices but **no endpoint or service ever
  transitions to it**. Settable only via the generic
  `update/partial_update` (gated by `CanManageHousekeeping` tier).

### 4.3 Who can trigger today

| Transition | Real gate as implemented |
| --- | --- |
| Room: any housekeeping flow transition | one of three housekeeping caps via `policy.can_change_room_status` |
| Room: manager override | `housekeeping.room_status.override` capability **AND** `staff_admin+` tier |
| Task create/update/delete | `staff_admin+` tier (no capability) |
| Task assign | `housekeeping.task.assign` capability **AND** `staff_admin+` tier |
| Task start/complete | nav `housekeeping` only + assignee match |

---

## 5. Proposed Capabilities (canonical, atomic)

Removes duplication, removes tier shadowing, replaces three "who"
capabilities with one verb-per-action set.

```
housekeeping.module.view             — see the module (nav replacement)
housekeeping.dashboard.read          — read dashboard payload (incl. open_tasks)

housekeeping.task.read               — list / retrieve tasks
housekeeping.task.create             — create a task
housekeeping.task.update             — edit task fields (note, priority, type, room, booking)
housekeeping.task.delete             — delete a task
housekeeping.task.assign             — set assigned_to on a task
housekeeping.task.cancel             — transition to CANCELLED (currently dead)
housekeeping.task.execute            — start / complete a task assigned to self

housekeeping.room_status.transition  — perform the housekeeping workflow matrix
housekeeping.room_status.front_desk  — perform the front-desk matrix
housekeeping.room_status.override    — bypass the matrix (any valid transition)
                                       (still requires note when source = MANAGER_OVERRIDE)

housekeeping.room_status.history.read — read RoomStatusEvent log for a room
```

Notes on the proposal:

- `housekeeping.dashboard.read` exists separately so the `staff_admin`
  branch on `open_tasks` becomes a clean capability flag instead of a
  tier-string check. Alternatively fold it into `housekeeping.task.read`
  if the hotel-wide `open_tasks` payload is acceptable to anyone with
  task read.
- `housekeeping.task.execute` replaces the implicit "if you have the
  nav, you can start/complete anything assigned to you" rule. Self-
  ownership is still enforced inline, but a capability is now the floor.
- `housekeeping.task.cancel` exposes the dead `CANCELLED` state behind
  one explicit gate; remove from the catalog if the state stays unused.

---

## 6. Enforcement Mapping

| Capability | Endpoint | Enforcement Point |
| --- | --- | --- |
| `housekeeping.module.view` | nav chain on every endpoint | `HasHousekeepingNav` (replace) → `HasCapability('housekeeping.module.view', safe_methods_bypass=False)` |
| `housekeeping.dashboard.read` | `GET /housekeeping/dashboard/` | `HousekeepingDashboardViewSet.list` (replace `access_level` branch) |
| `housekeeping.task.read` | `GET /housekeeping/tasks/[/{id}]` | `HousekeepingTaskViewSet.list/retrieve` |
| `housekeeping.task.create` | `POST /housekeeping/tasks/` | `HousekeepingTaskViewSet.create` |
| `housekeeping.task.update` | `PUT|PATCH /housekeeping/tasks/{id}/` | `HousekeepingTaskViewSet.update/partial_update` |
| `housekeeping.task.delete` | `DELETE /housekeeping/tasks/{id}/` | `HousekeepingTaskViewSet.destroy` |
| `housekeeping.task.assign` | `POST /housekeeping/tasks/{id}/assign/` | `HousekeepingTaskViewSet.assign` (already partly via `policy.can_assign_task`) |
| `housekeeping.task.execute` | `POST /housekeeping/tasks/{id}/start/` and `/complete/` | `HousekeepingTaskViewSet.start`, `.complete` |
| `housekeeping.task.cancel` | `PATCH /housekeeping/tasks/{id}/` with `{status: CANCELLED}` | requires payload-discriminating gate in `get_permissions` (mirrors Phase 6B.2 PATCH split) |
| `housekeeping.room_status.transition` | `POST /housekeeping/rooms/{id}/status/` | `policy.can_change_room_status` (already enforced) |
| `housekeeping.room_status.front_desk` | `POST /housekeeping/rooms/{id}/status/` | `policy.can_change_room_status` (already enforced) |
| `housekeeping.room_status.override` | `POST /housekeeping/rooms/{id}/manager_override/` and `…/status/` (when matrix denies) | `RoomStatusViewSet.manager_override`, `policy.can_change_room_status` |
| `housekeeping.room_status.history.read` | `GET /housekeeping/rooms/{id}/status-history/` | `RoomStatusViewSet.status_history` |

`MODULE_POLICY['housekeeping']` block to add to `staff/module_policy.py`:

```python
'housekeeping': {
    'view_capability': HOUSEKEEPING_MODULE_VIEW,
    'read_capability': HOUSEKEEPING_TASK_READ,
    'actions': {
        'dashboard_read':       HOUSEKEEPING_DASHBOARD_READ,
        'task_create':          HOUSEKEEPING_TASK_CREATE,
        'task_update':          HOUSEKEEPING_TASK_UPDATE,
        'task_delete':          HOUSEKEEPING_TASK_DELETE,
        'task_assign':          HOUSEKEEPING_TASK_ASSIGN,        # already canonical
        'task_execute':         HOUSEKEEPING_TASK_EXECUTE,
        'task_cancel':          HOUSEKEEPING_TASK_CANCEL,
        'status_transition':    HOUSEKEEPING_ROOM_STATUS_TRANSITION,  # already canonical
        'status_front_desk':    HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,  # already canonical
        'status_override':      HOUSEKEEPING_ROOM_STATUS_OVERRIDE,    # already canonical
        'status_history_read':  HOUSEKEEPING_ROOM_STATUS_HISTORY_READ,
    },
},
```

---

## 7. Gap Analysis

### 7.1 Missing capabilities (action exists, no capability gate)

- **`task.start` / `task.complete`** — no capability check at all. Only
  the nav slug + self-ownership.
- **`task.create / update / delete / assign`** — gated by **tier**
  (`CanManageHousekeeping`), not by capability. Capability `task.assign`
  exists but is shadowed by the tier check above it.
- **`status-history` read** — no capability; nav-only.
- **`dashboard` `open_tasks` payload** — gated by literal access_level
  string list, not a capability.
- **`task.cancel` state transition** — no dedicated gate; only reachable
  via the broad `update` path which is tier-gated.

### 7.2 Over-permissioned endpoints

- `RoomStatusViewSet.manager_override`: requires both `staff_admin+` tier
  AND the `housekeeping.room_status.override` capability. The capability
  is the contract authority; the tier check is dead weight that risks
  blocking a legitimately-capable role assigned at `regular_staff` tier.
- `HousekeepingTaskViewSet.assign`: same double gate (tier +
  `housekeeping.task.assign`). Per `DEPARTMENT_PRESET_CAPABILITIES`, no
  department currently grants `housekeeping.task.assign`; only role
  presets `housekeeping_supervisor` and `housekeeping_manager` and the
  supervisor tier bundle do — and those staff are on `staff_admin+` tier
  anyway. So today the double gate is *coincidentally* equivalent. It
  becomes wrong the moment a `regular_staff`-tier role is given
  `housekeeping.task.assign` (e.g. `housekeeping_supervisor` deployed
  at `regular_staff` tier).

### 7.3 Under-protected flows

- `task.start`, `task.complete`: any staff with the `housekeeping` nav
  can act on any **unassigned** task (the inline check only blocks
  acting on someone else's already-assigned task).
- `tasks` list / detail: any staff with the `housekeeping` nav can read
  every task in the hotel (no capability, no scoping beyond hotel).
  Likely fine, but should be a `housekeeping.task.read` capability for
  contract conformance, not nav.
- `status-history` GET: same — nav-only.

### 7.4 Tier leaks

- `HousekeepingDashboardViewSet.list`:
  `staff.access_level in ['staff_admin','super_staff_admin']`.
- `CanManageHousekeeping`: pure `_tier_at_least(tier, 'staff_admin')`.
  Used on tasks CUD + assign + manager_override. **This is the core
  Phase 6C drift** — tier is being used as the action authority for the
  housekeeping module.

### 7.5 Nav leaks

- The entire module is fronted by `HasHousekeepingNav` /
  `HasNavPermission('housekeeping')`. Per `staff/permissions.py` docstring:
  *"HasNavPermission controls ONLY module/route visibility — never
  mutation authority."* Today, **for `task.start`, `task.complete`, and
  `status-history`, nav is the only gate on a non-safe / sensitive
  endpoint** — i.e. nav is being used as the mutation authority. This
  is the documented anti-pattern.

### 7.6 Role-string checks

None grep-detectable in `housekeeping/`. The role-slug checks were
already migrated; the leaks here are tier and nav.

---

## 8. Drift Risks

Patterns matching prior failures (Rooms PATCH drift, Phase 6B.2):

1. **Mixed-action endpoint (`PATCH /tasks/{id}/`)**: the generic
   `partial_update` lets a holder of `housekeeping.task.update` mutate
   `assigned_to` (the `task.assign` action) and `status` (the `start /
   complete / cancel` actions) without ever passing through the
   action-specific endpoints. Same shape as the rooms `is_out_of_order`
   bug. Either:
   - lock the serializer's writable fields to a non-action subset
     (i.e. drop `assigned_to`, `status`, `started_at`, `completed_at`
     from `HousekeepingTaskSerializer.Meta.fields` writable surface), or
   - add a payload-content-driven branch in
     `HousekeepingTaskViewSet.get_permissions` that demands the
     corresponding capability (assign / execute / cancel) when those
     fields are present.
2. **`CanManageHousekeeping` shadowing capabilities**: `task.assign` and
   `room_status.override` capabilities exist but are advertised
   "decorative" while the tier check actually decides. Any
   `regular_staff`-tier role bundle that grants those capabilities will
   be silently denied — exactly the Phase 6B.1 Risk #2 ("ops_admin
   advertised but unusable") pattern.
3. **`housekeeping.task.assign` registry gap**: the capability is
   declared canonical and used by `policy.can_assign_task`, but
   `MODULE_POLICY` does not export a housekeeping module entry at all,
   so the frontend has no boolean for it and cannot render the assign
   button conditionally on capability.
4. **`HOUSEKEEPING_ROOM_STATUS_FRONT_DESK` advertised, never gated by
   any module-policy action**: same drift class — capability is granted
   to `front_office` department but not surfaced as a `rbac.housekeeping`
   action. Front-end has no way to test for it.
5. **`HOUSEKEEPING_TASK_ASSIGN` is nominally hotel-scoped**, but
   `HousekeepingTaskAssignSerializer.validate_assigned_to_id` looks up
   `Staff.objects.get(id=value)` **before** the hotel check, leaking
   existence of staff IDs across hotels via the
   `serializers.ValidationError("Staff member not found.")` vs.
   `"Can only assign tasks to staff members in your hotel."` differential
   error messages. Not RBAC per se; flag as a related drift.
6. **`get_object()` permissions on `start` / `complete`**: DRF runs the
   queryset filter (`get_queryset` scopes by hotel) and then the
   permission classes' `has_object_permission` (none defined here). The
   self-ownership check is in the action body; there is no
   `IsSameHotel.has_object_permission` enforcement on the task object
   beyond the queryset filter. Today safe (queryset filter prevents
   cross-hotel `pk` resolution), but the chain doesn't fail closed if
   the queryset is ever loosened.

---

## 9. Final Verdict

**READY for RBAC implementation? — NO.**

Blocking issues that must be resolved before Phase 6C implementation can
be deterministic:

1. **`CanManageHousekeeping` is tier-based**, not capability-based, and
   is the gate on every CUD + assign + manager_override endpoint.
   Replace with `HasCapability` subclasses bound to the new
   `housekeeping.task.*` and `housekeeping.room_status.override`
   capabilities. Until this is replaced, every `task.*` capability is
   "advertised but unusable" for any role outside `staff_admin+` tier.
2. **`task.start` and `task.complete` have no capability gate.**
   Introduce `housekeeping.task.execute` and enforce it; keep the
   self-ownership check as a secondary business rule.
3. **`housekeeping` is missing from `MODULE_POLICY`** in
   `staff/module_policy.py`. The frontend has no `rbac.housekeeping`
   block, so it cannot drive button visibility from capabilities and
   will fall back to nav (= the very anti-pattern this audit is closing).
   Add the module block per §6 once the new capability slugs land.
4. **`HousekeepingDashboardViewSet.list` branches on
   `staff.access_level`** to include `open_tasks`. Replace with a
   capability check (`housekeeping.dashboard.read` or a fold into
   `housekeeping.task.read`).
5. **`HousekeepingTaskSerializer` writable surface includes action
   fields (`assigned_to`, `status`, `started_at`, `completed_at`)**.
   Decide which the canonical surface is (action endpoints vs. generic
   PATCH) and remove them from the writable set, or add a
   payload-content gate in `get_permissions` à la Phase 6B.2.
6. **`status-history` GET has no capability** — add
   `housekeeping.room_status.history.read` and enforce it; nav alone is
   not contract-conformant for a non-safe-by-default audit endpoint
   even on GET.
7. **`HousekeepingTaskAssignSerializer.validate_assigned_to_id`**
   leaks cross-hotel staff existence. Reorder so the hotel check runs
   before the existence message (housekeeping change, but adjacent to
   the assign capability work).

Non-blocking but recommended in the same pass:

- Decide whether `HousekeepingTask.STATUS_CHOICES.CANCELLED` is a real
  state. If yes, add `housekeeping.task.cancel` and an endpoint /
  serializer-action for it. If no, drop it from the choice set so
  generic PATCH cannot reach it.
- Replace `HasHousekeepingNav` chain with
  `HasCapability('housekeeping.module.view', safe_methods_bypass=False)`
  to remove the last nav-as-authority surface.

When the seven blockers above are addressed, `MODULE_POLICY['housekeeping']`,
the new capability slugs, the role / department preset additions, and the
endpoint rewires can be implemented as a single Phase 6C patch with the
same shape as Phase 6B.1.
