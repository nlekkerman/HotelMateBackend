# RBAC Operational Visibility Audit

> Code-derived audit of the live RBAC stack.
> Sources analysed: [staff/capability_catalog.py](staff/capability_catalog.py), [staff/module_policy.py](staff/module_policy.py), [staff/permissions.py](staff/permissions.py), [staff/role_catalog.py](staff/role_catalog.py), [staff/department_catalog.py](staff/department_catalog.py), [staff/nav_catalog.py](staff/nav_catalog.py).
> Resolution model: `allowed_capabilities = TIER_DEFAULT_CAPABILITIES[tier] ∪ ROLE_PRESET_CAPABILITIES[role.slug] ∪ DEPARTMENT_PRESET_CAPABILITIES[department.slug]` (see [staff/capability_catalog.py](staff/capability_catalog.py#L1898) `resolve_capabilities`). Module visibility / read / actions are then projected via [staff/module_policy.py](staff/module_policy.py#L487) `resolve_module_policy`.
> Comments/docstrings were intentionally ignored — only the literal preset bundles were used.

---

## 1. Executive Summary

**Verdict: the current RBAC model is operationally TOO STRICT for a working hotel.**

The capability split is technically clean (granular, well-namespaced, every endpoint has a slug). But the *preset distribution* leaves large categories of canonical roles with **zero capability contributions** beyond what their tier already gives them. The result is a system where:

1. **Nine of the twenty canonical role slugs have NO entry in `ROLE_PRESET_CAPABILITIES`.** Their staff inherit only tier + department capabilities. For some of them (duty manager, kitchen manager, FO supervisor, guest relations \*, fb\_supervisor) this collapses to either "no useful module access at all" or "exactly what a junior co-worker has".
2. **Three of the eight canonical departments have NO entry in `DEPARTMENT_PRESET_CAPABILITIES`** (`management`, `administration`, `guest_relations`). Anybody whose department is `management` or `guest_relations` gets *no* department-derived capabilities, even though those are precisely the cross-cutting "see everything" departments.
3. **Tier defaults stripped almost everything cross-cutting.** Outside guest-chat/staff-chat/attendance-self-service/room-services-read, tier carries nothing. That was a deliberate Phase 6 move ("tier is not the permission engine"), but role + department presets did not absorb the operational defaults that tier dropped — they only absorbed *some* of them.
4. **Several modules are visible-but-unreadable, or readable-but-invisible**, because `view_capability` and `read_capability` come from different bundles (e.g. housekeeping module visibility on the front-office department but no `housekeeping.task.read`).
5. **Attendance is the worst offender.** Outside `hotel_manager`, *no* role or department preset grants any roster, shift, daily-plan, analytics or hotel-wide log capability. Front Office Manager, Housekeeping Manager, Maintenance Manager, F&B Manager, FO Supervisor, Duty Manager all see only their *own* attendance.

Departments that became unrealistic: **management** (empty preset), **guest\_relations** (empty preset), **administration** (empty preset), **kitchen** (no chat / no maintenance reporter / no hotel\_info), **food\_beverage** (no chat / no maintenance / no hotel\_info / no guests).

Modules that are over-tightened: **attendance** (no supervisory tier between self and full hotel\_manager bundle), **staff\_management** (department-head-view bundle grants `staff.read` but not `module.view` — hidden navbar), **maintenance** (no role preset for line `maintenance_staff`), **hotel\_info** (read denied to most non-front-office staff), **chat / guest chat** (front-office-only by design — frustrates duty managers, hotel managers' subordinates, GR agents).

---

## 2. Visibility Matrix

Notation:
- ✅ = capability present in resolved bundle.
- ❌ = capability absent.
- ⚠️ = mismatch (visible+unread, or read+invisible, or nav+invisible, etc.).
- "self" = self-service only (own logs / own roster / own face).

Tier abbreviations:
- `RS` = `regular_staff`
- `SA` = `staff_admin` (tier)
- `SSA` = `super_staff_admin` (tier)

Tier baselines re-used across personas (from [staff/capability_catalog.py](staff/capability_catalog.py#L1444)):
- `RS` = `_STAFF_CHAT_BASE` ∪ `_ATTENDANCE_SELF_SERVICE` ∪ `_ROOM_SERVICE_BASE`
- `SA` = `RS` ∪ `_SUPERVISOR_AUTHORITY` (chat moderate, chat conv assign, staff\_chat moderate, staff\_chat conv delete)
- `SSA` = `SA` ∪ `_BOOKING_SUPERVISE`

### 2.1 Front Office Manager (role=`front_office_manager`, dept=`front_office`, tier=`SSA`)

| Module              | Visible | Read    | Major actions                                                                                                                |
| ------------------- | ------- | ------- | ---------------------------------------------------------------------------------------------------------------------------- |
| bookings            | ✅      | ✅      | update ✅, cancel ✅, assign\_room ✅, checkin ✅, checkout ✅, communicate ✅, override\_\* ✅, manage\_rules ✅                |
| rooms               | ✅      | ✅      | status\_transition ✅, maintenance\_flag ✅, inspect ✅, maintenance\_clear ✅, checkout\_bulk ✅, inventory CUD ❌, type/media ❌, out\_of\_order ❌, checkout\_destructive ❌ |
| housekeeping        | ✅      | ✅      | dashboard ✅, task create/update/assign/execute/cancel ✅, status\_transition/front\_desk/override/history ✅, task\_delete ❌ |
| maintenance         | ✅      | ✅      | request\_create ✅, accept/resolve/update/reassign/reopen/close/delete ❌, comment\_create ❌, photo\_upload ❌ ⚠️             |
| attendance          | ✅      | self    | clock ✅, break ✅, log\_read\_self ✅, **shift\_read ❌**, period\_\* ❌, daily\_plan\_\* ❌, analytics\_read ❌, log\_read\_all ❌ ⚠️ |
| staff\_management   | ❌ ⚠️   | ✅ ⚠️   | every action ❌. Nav slug `staff_management` is in `TIER_DEFAULT_NAVS['super_staff_admin']` so the link is rendered but `rbac.staff_management.visible=false`. |
| chat (guest)        | ✅      | ✅      | message\_send ✅, message\_moderate ✅ (tier), conv\_assign ✅, guest\_respond ✅ (dept), attachment up/del ✅                  |
| staff\_chat         | ✅      | ✅      | conv\_create ✅, conv\_delete ✅ (tier), msg\_send ✅, msg\_moderate ✅ (tier), reaction ✅                                     |
| guests              | ✅      | ✅      | update ✅                                                                                                                    |
| hotel\_info         | ✅      | ✅      | entry\_read ✅, all CUD ❌, qr\_generate ❌                                                                                    |
| room\_services      | ✅      | ✅      | menu\_read ✅; **order\_accept ❌, order\_complete ❌, order\_update ❌, order\_create ❌**, order\_delete ❌, menu\_item\_\* ❌; breakfast same ⚠️ |
| restaurant\_bookings| ❌      | ❌      | every action ❌                                                                                                              |

### 2.2 Front Desk Agent (role=`front_desk_agent`, dept=`front_office`, tier=`RS`)

| Module              | Visible | Read    | Major actions                                                                          |
| ------------------- | ------- | ------- | -------------------------------------------------------------------------------------- |
| bookings            | ✅      | ✅      | update/cancel/assign\_room/checkin/checkout/communicate ✅, override/manage\_rules ❌  |
| rooms               | ✅      | ✅      | status\_transition ❌, maintenance\_flag ❌, inspect ❌, maintenance\_clear ❌, all CUD ❌ |
| housekeeping        | ✅      | ❌ ⚠️   | dashboard\_read ❌, task\_read ❌, status\_history\_read ✅, status\_front\_desk ✅; everything else ❌ — module visible without baseline read. |
| maintenance         | ✅      | ✅      | request\_create ✅; accept/resolve/update/photo/comment ❌                              |
| attendance          | ✅      | self    | clock/break/log\_read\_self/roster\_read\_self ✅; everything else ❌                   |
| staff\_management   | ❌      | ❌      | —                                                                                      |
| chat (guest)        | ✅      | ✅      | message\_send ✅, attachment up/del ✅, conv\_assign ✅, guest\_respond ✅; moderate ❌ |
| staff\_chat         | ✅      | ✅      | conv\_create ✅, msg\_send ✅, attach ✅, reaction ✅; conv\_delete ❌, moderate ❌      |
| guests              | ✅      | ✅      | update ✅                                                                              |
| hotel\_info         | ✅      | ✅      | every CUD ❌                                                                           |
| room\_services      | ✅      | ✅      | order\_create/update/accept/complete ✅; order\_delete ❌, menu\_item\_\* ❌            |
| restaurant\_bookings| ❌      | ❌      | —                                                                                      |

### 2.3 Waiter (role=`waiter`, dept=`food_beverage`, tier=`RS`)

| Module              | Visible | Read | Major actions |
| ------------------- | ------- | ---- | ------------- |
| bookings            | ❌      | ❌   | — |
| rooms               | ❌      | ❌   | — |
| housekeeping        | ❌      | ❌   | — |
| maintenance         | ❌ ⚠️   | ❌   | cannot file a ticket about a broken table / bar |
| attendance          | ✅      | self | self only |
| staff\_management   | ❌      | ❌   | — |
| chat (guest)        | ❌ ⚠️   | ❌   | — (no `_CHAT_BASE` because dept ≠ `front_office`) |
| staff\_chat         | ✅      | ✅   | base + reaction ✅; conv\_delete/moderate ❌ |
| guests              | ❌ ⚠️   | ❌   | no `guest.record.read` — cannot match a walk-in guest |
| hotel\_info         | ❌ ⚠️   | ❌   | cannot answer guest questions about the hotel |
| room\_services      | ✅      | ✅   | menu\_read ✅; order\_accept/complete/create/update ❌ — only base read |
| restaurant\_bookings| ✅      | ✅   | record\_create/update/mark\_seen ✅, assignment\_assign/unseat ✅; record\_delete ❌, restaurant\_\* ❌, table\_manage ❌, blueprint\_manage ❌, category\_manage ❌ |

### 2.4 Housekeeper (role=`housekeeper`, dept=`housekeeping`, tier=`RS`)

> `housekeeper` has **no entry in `ROLE_PRESET_CAPABILITIES`**. All authority comes from tier + department.

| Module              | Visible | Read | Major actions |
| ------------------- | ------- | ---- | ------------- |
| bookings            | ❌      | ❌   | — |
| rooms               | ✅      | ✅   | status\_transition ✅, maintenance\_flag ✅; inspect/clear ❌, all CUD ❌ |
| housekeeping        | ✅      | ✅   | dashboard ✅, task\_execute ✅, status\_transition ✅, status\_history\_read ✅; task\_create/update/assign/cancel/delete ❌, status\_override ❌, status\_front\_desk ❌ |
| maintenance         | ✅      | ✅   | request\_create ✅; rest ❌ (reporter only) |
| attendance          | ✅      | self | self only |
| chat (guest)        | ❌      | ❌   | cannot coordinate "room has issue, message guest" |
| staff\_chat         | ✅      | ✅   | base |
| guests              | ❌      | ❌   | — |
| hotel\_info         | ❌      | ❌   | — |
| room\_services      | ✅      | ✅   | base read only |
| restaurant\_bookings| ❌      | ❌   | — |

### 2.5 Maintenance Staff (role=`maintenance_staff`, dept=`maintenance`, tier=`RS`)

> `maintenance_staff` has **no entry in `ROLE_PRESET_CAPABILITIES`**. All authority from tier + department.

| Module              | Visible | Read | Major actions |
| ------------------- | ------- | ---- | ------------- |
| bookings            | ❌      | ❌   | — |
| rooms               | ✅      | ✅   | maintenance\_flag ✅; status\_transition ❌ (only `housekeeping.room_status.transition` is granted, in housekeeping module), inspect/clear ❌, all CUD ❌ |
| housekeeping        | ❌ ⚠️   | ❌   | `HOUSEKEEPING_ROOM_STATUS_TRANSITION` is granted by dept but `HOUSEKEEPING_MODULE_VIEW` is **not** → cap exists but module is invisible. |
| maintenance         | ✅      | ✅   | request\_create/accept/resolve ✅, comment\_create ✅, photo\_upload ✅; reassign/reopen/close/delete/comment\_moderate/photo\_delete ❌ |
| attendance          | ✅      | self | self only |
| chat (guest)        | ❌      | ❌   | — |
| staff\_chat         | ✅      | ✅   | base |
| guests              | ❌      | ❌   | — |
| hotel\_info         | ❌      | ❌   | — |
| room\_services      | ✅      | ✅   | base read only |
| restaurant\_bookings| ❌      | ❌   | — |

### 2.6 Hotel Manager (role=`hotel_manager`, dept=`management`, tier=`SSA`)

> `management` department has **no preset entry**. All authority from tier + role.

| Module              | Visible | Read | Major actions |
| ------------------- | ------- | ---- | ------------- |
| bookings            | ✅      | ✅   | full manage (including `manage_rules`) ✅ |
| rooms               | ✅      | ✅   | full manage ✅ |
| housekeeping        | ✅      | ✅   | full manage ✅ |
| maintenance         | ✅      | ✅   | full manage ✅ |
| attendance          | ✅      | ✅   | full manage (period/shift/daily\_plan/analytics/face) ✅ |
| staff\_management   | ✅      | ✅   | full manager bundle (incl. `authority.supervise`) ✅ |
| chat (guest)        | ✅      | ✅   | message\_send/moderate/conv\_assign/upload/delete ✅; **`guest_respond` ❌** (not in `_CHAT_BASE`, granted only via dept `front_office`). Routing eligibility, not authority — Hotel Manager will not be auto-routed inbound guest pings. |
| staff\_chat         | ✅      | ✅   | full ✅ |
| guests              | ✅      | ✅   | update ✅ |
| hotel\_info         | ✅      | ✅   | entry CUD + qr\_generate ✅; `category_manage` ❌ (intentionally superuser-only) |
| room\_services      | ✅      | ✅   | full manage ✅ |
| restaurant\_bookings| ✅      | ✅   | full manage ✅ |

This is the ONE persona the system actually behaves correctly for.

### 2.7 Kitchen Staff (role=`kitchen_staff`, dept=`kitchen`, tier=`RS`)

> `kitchen_staff` has **no entry in `ROLE_PRESET_CAPABILITIES`**.

| Module              | Visible | Read | Major actions |
| ------------------- | ------- | ---- | ------------- |
| room\_services      | ✅      | ✅   | order\_create/update/accept/complete ✅, breakfast same; order\_delete ❌, menu\_item\_\* ❌ |
| attendance          | ✅      | self | self only |
| staff\_chat         | ✅      | ✅   | base |
| chat (guest)        | ❌      | ❌   | — |
| maintenance         | ❌ ⚠️   | ❌   | a kitchen porter cannot file a ticket about a broken oven |
| hotel\_info         | ❌      | ❌   | — |
| guests              | ❌      | ❌   | — |
| bookings / rooms / housekeeping / restaurant\_bookings / staff\_management | ❌ | ❌ | — |

### 2.8 F&B Supervisor (role=`fb_supervisor`, dept=`food_beverage`, tier=`SA`)

> `fb_supervisor` has **no entry in `ROLE_PRESET_CAPABILITIES`**. Effective access = tier `staff_admin` + dept `food_beverage` only.

| Module              | Visible | Read | Major actions |
| ------------------- | ------- | ---- | ------------- |
| bookings            | ❌      | ❌   | — (a shift lead cannot see who's checking in tonight) |
| rooms               | ❌      | ❌   | — |
| housekeeping        | ❌      | ❌   | — |
| maintenance         | ❌      | ❌   | — |
| attendance          | ✅      | self | **shift\_read ❌** — supervisor cannot see their own team's roster |
| staff\_management   | ❌      | ❌   | — |
| chat (guest)        | ❌      | ❌   | — |
| staff\_chat         | ✅      | ✅   | conv\_delete ✅, moderate ✅, base ✅ |
| guests              | ❌      | ❌   | — |
| hotel\_info         | ❌      | ❌   | — |
| room\_services      | ✅      | ✅   | base read only |
| restaurant\_bookings| ✅      | ✅   | operate (record CRUD + assignment) ✅; manage ❌ |

Operationally identical to a waiter except for staff-chat moderation. **Not a real supervisor.**

### 2.9 Duty Manager (role=`duty_manager`, dept=`management`, tier=`SSA`)

> `duty_manager` has **no entry in `ROLE_PRESET_CAPABILITIES`** AND `management` has **no department preset**. Effective access = pure tier `super_staff_admin`.

| Module              | Visible | Read | Major actions |
| ------------------- | ------- | ---- | ------------- |
| bookings            | ✅      | ✅   | update/cancel/assign\_room/checkin/checkout/communicate/override\_\* ✅; manage\_rules ❌ |
| rooms               | ❌ ⚠️   | ❌   | the manager on duty cannot see the room board |
| housekeeping        | ❌ ⚠️   | ❌   | cannot see turnover state |
| maintenance         | ❌ ⚠️   | ❌   | cannot see open tickets |
| attendance          | ✅      | self | self only — manager on duty cannot see who is on shift right now |
| staff\_management   | ❌      | ❌   | — |
| chat (guest)        | ❌ ⚠️   | ❌   | manager on duty cannot see escalated guest chats |
| staff\_chat         | ✅      | ✅   | conv\_delete ✅, moderate ✅ |
| guests              | ❌ ⚠️   | ❌   | — |
| hotel\_info         | ❌      | ❌   | — |
| room\_services      | ✅      | ✅   | base read only |
| restaurant\_bookings| ❌      | ❌   | — |

**The Duty Manager is effectively blind.** This is the single most operationally broken persona produced by the current presets.

### 2.10 Compact cross-role overview

Only "module visible" is shown; "✅" means `rbac.<module>.visible == true`, blank means false.

| Module \ Role            | hotel\_mgr | front\_office\_mgr | front\_office\_supv | front\_desk\_agent | duty\_mgr | hk\_mgr | hk\_supv | housekeeper | maint\_mgr | maint\_supv | maint\_staff | fnb\_mgr | fb\_supv | waiter | kitchen\_mgr/supv/staff | gr\_mgr/supv/agent |
| ------------------------ | :--------: | :----------------: | :-----------------: | :----------------: | :-------: | :-----: | :------: | :---------: | :--------: | :---------: | :----------: | :------: | :------: | :----: | :--------------------: | :----------------: |
| bookings                 |     ✅     |         ✅         |         ✅          |         ✅         |     ✅    |         |          |             |            |             |              |          |          |        |                        |                    |
| rooms                    |     ✅     |         ✅         |         ✅          |         ✅         |           |    ✅   |    ✅    |      ✅     |     ✅     |     ✅      |      ✅      |          |          |        |                        |                    |
| housekeeping             |     ✅     |         ✅         |         ✅          |         ✅         |           |    ✅   |    ✅    |      ✅     |            |             |              |          |          |        |                        |                    |
| maintenance              |     ✅     |         ✅         |         ✅          |         ✅         |           |    ✅   |    ✅    |      ✅     |     ✅     |     ✅      |      ✅      |          |          |        |                        |                    |
| attendance               |     ✅     |         ✅         |         ✅          |         ✅         |     ✅    |    ✅   |    ✅    |      ✅     |     ✅     |     ✅      |      ✅      |    ✅    |    ✅    |   ✅   |           ✅           |         ✅         |
| staff\_management        |     ✅     |          ⚠️\*       |                     |                    |           |  ⚠️\*    |          |             |     ⚠️\*    |             |              |    ⚠️\*   |          |        |                        |                    |
| chat (guest)             |     ✅     |         ✅         |         ✅          |         ✅         |           |         |          |             |            |             |              |          |          |        |                        |                    |
| staff\_chat              |     ✅     |         ✅         |         ✅          |         ✅         |     ✅    |    ✅   |    ✅    |      ✅     |     ✅     |     ✅      |      ✅      |    ✅    |    ✅    |   ✅   |           ✅           |         ✅         |
| guests                   |     ✅     |         ✅         |         ✅          |         ✅         |           |         |          |             |            |             |              |          |          |        |                        |                    |
| hotel\_info              |     ✅     |         ✅         |         ✅          |         ✅         |           |         |          |             |            |             |              |          |          |        |                        |                    |
| room\_services           |     ✅     |         ✅         |         ✅          |         ✅         |     ✅    |    ✅   |    ✅    |      ✅     |     ✅     |     ✅      |      ✅      |    ✅    |    ✅    |   ✅   |           ✅           |         ✅         |
| restaurant\_bookings     |     ✅     |                    |                     |                    |           |         |          |             |            |             |              |    ✅    |    ✅    |   ✅   |                        |                    |

\* `*_DEPARTMENT_HEAD_VIEW` grants `staff_management.staff.read` but **not** `STAFF_MANAGEMENT_MODULE_VIEW`. So `rbac.staff_management.read=true` but `rbac.staff_management.visible=false`. See §3.1.

`gr_*` (guest relations roles) and `kitchen_*` non-staff roles inherit nothing beyond tier + their department's preset. `kitchen` department gives only room\_services. `guest_relations` department has **no preset at all** → guest relations agents/supervisors/managers see only `staff_chat`, `attendance` (self), `room_services` (base read). They cannot see guest records, guest chat, bookings, rooms, hotel info — the literal core of guest relations.

---

## 3. Operational Contradictions

### 3.1 `staff_management.read=true` but `staff_management.visible=false` (department-head roles)

Affected roles: `front_office_manager`, `housekeeping_manager`, `maintenance_manager`, `fnb_manager`.

The `_STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW` preset ([staff/capability_catalog.py](staff/capability_catalog.py#L1156)):

```python
_STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW: frozenset[str] = frozenset({
    STAFF_MANAGEMENT_STAFF_READ,
})
```

It deliberately omits `STAFF_MANAGEMENT_MODULE_VIEW`. The module policy ([staff/module_policy.py](staff/module_policy.py#L429)) reads:

```python
'staff_management': {
    'view_capability': STAFF_MANAGEMENT_MODULE_VIEW,
    'read_capability': STAFF_MANAGEMENT_STAFF_READ,
    ...
},
```

Result: `rbac.staff_management.visible=false`, `rbac.staff_management.read=true`. Frontend will hide the module entirely while every staff-read endpoint accepts these managers. The intent ("module.view comes from `allowed_navigation_items`") is documented in the comment at [capability_catalog.py L1149-L1155](staff/capability_catalog.py#L1149-L1155) but the docstring lies: nav and module visibility are *not* the same channel — the frontend now strictly consumes `user.rbac.<module>.visible`.

### 3.2 `housekeeping.module.view=true` but `housekeeping.task.read=false` (front\_office department)

Front Office department preset ([staff/capability_catalog.py](staff/capability_catalog.py#L1572)):

```python
'front_office': frozenset({
    CHAT_GUEST_RESPOND,
    CHAT_CONVERSATION_ASSIGN,
    HOUSEKEEPING_MODULE_VIEW,
    HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
    HOUSEKEEPING_ROOM_STATUS_HISTORY_READ,
}) | _CHAT_BASE | _BOOKING_READ | _BOOKING_OPERATE | _ROOM_READ | _MAINTENANCE_REPORTER,
```

It grants `HOUSEKEEPING_MODULE_VIEW` but never `HOUSEKEEPING_TASK_READ`. Module policy uses `HOUSEKEEPING_TASK_READ` as `read_capability`. Result for *any* front-office role without role-preset coverage (e.g. `front_office_supervisor`, `front_desk_agent`): the module is visible but the task list returns 403 / the dashboard is empty.

For `front_office_manager` this is masked because `_HOUSEKEEPING_SUPERVISE` ⊃ `_HOUSEKEEPING_BASE` ⊃ `HOUSEKEEPING_TASK_READ`.

### 3.3 `housekeeping.room_status.transition` without `housekeeping.module.view` (maintenance department)

Maintenance department preset ([staff/capability_catalog.py](staff/capability_catalog.py#L1599)):

```python
'maintenance': _ROOM_READ | frozenset({
    ROOM_MAINTENANCE_FLAG,
    HOUSEKEEPING_ROOM_STATUS_TRANSITION,
}) | _MAINTENANCE_OPERATE,
```

`HOUSEKEEPING_ROOM_STATUS_TRANSITION` is granted (so the canonical housekeeping service accepts the call when maintenance flips a room to `MAINTENANCE_REQUIRED` and back). But `HOUSEKEEPING_MODULE_VIEW` is **not** granted → `rbac.housekeeping.visible=false`. The capability silently exists with no UI surface to invoke it from. Same pattern for `HOUSEKEEPING_ROOM_STATUS_HISTORY_READ` for maintenance.

### 3.4 `chat` is invisible to almost everyone except front office

`_CHAT_BASE` is only mixed into:
- `front_office` department preset
- `hotel_manager` role preset

Tier deliberately dropped it (commit-comment evidence at [capability_catalog.py L1059-L1067](staff/capability_catalog.py#L1059-L1067)). Result:
- Waiters, housekeepers, kitchen staff, maintenance staff, GR staff, duty managers — **none** of them see the guest-chat module.
- A front-office supervisor (no role preset) gets it through the department, fine.
- A duty manager (dept `management`) does **not**.
- A guest-relations agent (dept `guest_relations` — empty preset) does **not**, even though answering guests is the literal job description.

This is the precise contradiction the user reported as "Front Office Manager could NOT see roster/staff/chat" being symptomatic of broader over-restriction.

### 3.5 Front Office Manager has booking *override* but not room-service *operate*

Tier `super_staff_admin` grants `_BOOKING_SUPERVISE` (i.e. override authority) but only `_ROOM_SERVICE_BASE` (read-only). The FOM role does not add `_ROOM_SERVICE_OPERATE`. Net result: a Front Office Manager can force-checkout a guest but cannot accept the room-service order on that guest's room — they have to bounce it to a Front Desk Agent or Hotel Manager. Same applies to `front_office_supervisor` and `duty_manager`.

### 3.6 Attendance: every department-head sees only their own clock

`_ATTENDANCE_MANAGE` is granted **only** by `hotel_manager`. None of `front_office_manager`, `housekeeping_manager`, `maintenance_manager`, `fnb_manager` (or any supervisor role) carry any of:
- `ATTENDANCE_LOG_READ_ALL`
- `ATTENDANCE_SHIFT_READ`
- `ATTENDANCE_PERIOD_READ`
- `ATTENDANCE_DAILY_PLAN_READ`
- `ATTENDANCE_ANALYTICS_READ`
- `ATTENDANCE_LOG_APPROVE` / `REJECT` / `RELINK`

→ A department head cannot supervise their own department's attendance. The user's reported case ("Front Office Manager could NOT see roster") is not an accident — there is no preset on the entire planet that gives FOM `attendance.shift.read`.

### 3.7 `duty_manager` has nothing department-specific

Code paths:
- Role preset: `duty_manager` not in `ROLE_PRESET_CAPABILITIES` (see [capability_catalog.py L1505-L1561](staff/capability_catalog.py#L1505-L1561)).
- Department preset: `'management'` not in `DEPARTMENT_PRESET_CAPABILITIES` (see [capability_catalog.py L1571-L1605](staff/capability_catalog.py#L1571-L1605)).
- Tier: `super_staff_admin` carries supervisor authority + booking supervise + chat-tier-dropped.

The Duty Manager therefore lands with no `rooms`, no `housekeeping`, no `maintenance`, no `chat`, no `guests`, no `hotel_info`, no `staff_management`, no `restaurant_bookings`, no `attendance` (beyond self) — but full booking override. **Any management-department persona is in the same hole.**

### 3.8 Nine canonical role slugs have no preset at all

The complete list of canonical role slugs that are NOT keys of `ROLE_PRESET_CAPABILITIES`:

| Role slug                  | Department          | Tier expectation | Effective access      |
| -------------------------- | ------------------- | ---------------- | --------------------- |
| `front_office_supervisor`  | `front_office`      | `staff_admin`    | tier + FO dept        |
| `housekeeper`              | `housekeeping`      | `regular_staff`  | tier + HK dept        |
| `fb_supervisor`            | `food_beverage`     | `staff_admin`    | tier + F&B dept       |
| `kitchen_staff`            | `kitchen`           | `regular_staff`  | tier + kitchen dept   |
| `kitchen_supervisor`       | `kitchen`           | `staff_admin`    | tier + kitchen dept   |
| `kitchen_manager`          | `kitchen`           | `super_staff_admin` | tier + kitchen dept |
| `maintenance_staff`        | `maintenance`       | `regular_staff`  | tier + maint dept     |
| `guest_relations_agent`    | `guest_relations`   | `regular_staff`  | tier ONLY (no dept preset) |
| `guest_relations_supervisor` | `guest_relations` | `staff_admin`    | tier ONLY             |
| `guest_relations_manager`  | `guest_relations`   | `super_staff_admin` | tier ONLY          |
| `duty_manager`             | `management`        | `super_staff_admin` | tier ONLY          |

(11 slugs — the 9-figure in the summary referred to non-tier roles; counting depends on whether the `staff_admin` / `super_staff_admin` "role" personas are excluded. They are listed in `ROLE_PRESET_CAPABILITIES`.)

For supervisor / manager rows in this list, the supervisor/manager is **operationally indistinguishable from a junior in the same department**, except for staff-chat moderation and (for managers on `super_staff_admin`) booking override.

### 3.9 `kitchen_manager` is no different from `kitchen_staff`

Both rely entirely on `kitchen` department preset (`_ROOM_SERVICE_OPERATE | {ROOM_SERVICE_ORDER_FULFILL_KITCHEN}`). The only delta is tier-derived staff-chat moderation and (for `super_staff_admin`) booking override. The role title is decorative.

### 3.10 `category.manage` is a dead capability for hotel\_info (intentional, but worth flagging)

`HOTEL_INFO_CATEGORY_MANAGE` is in `CANONICAL_CAPABILITIES` and in `MODULE_POLICY['hotel_info'].actions['category_manage']` but is never granted by any preset (not even `_HOTEL_INFO_MANAGE`). It is reserved for `is_superuser=True` only. The frontend will always render `actions.category_manage=false` for every non-superuser including the Hotel Manager. Document the intent — otherwise it looks like an oversight.

---

## 4. Workflow Blockers

### 4.1 Reception ↔ Housekeeping coordination

Affected roles: `front_desk_agent`, `front_office_supervisor`.
Capability gap: `housekeeping.task.read` is missing from the `front_office` department preset.
Evidence: §3.2.
Operational consequence: a front desk agent who needs to know which rooms are still being cleaned (the most common front-desk question on earth) sees a visible Housekeeping module that returns no task data. They can only flip room status front-desk style and read history; they cannot read the live task board.

### 4.2 F&B ↔ Front Office (split-stay arrivals)

Affected roles: every F&B role.
Capability gap: F&B department preset has zero `booking.*` and zero `guest.record.read`.
Operational consequence: a waiter cannot look up the room number of a charge-to-room walk-in, cannot see whether tonight's restaurant booking is a hotel guest, cannot identify "Mrs. Smith from 412" without leaving the F&B UI.

### 4.3 Anybody-but-front-office to guest

Affected roles: `housekeeper`, `housekeeping_supervisor`, `housekeeping_manager`, every `kitchen_*` role, every `maintenance_*` role, every `guest_relations_*` role, `duty_manager`, `fb_supervisor`, `waiter`, `fnb_manager`.
Capability gap: `chat.module.view` not granted.
Operational consequence: there is no channel for a housekeeper to escalate a found-item to the guest, for a guest-relations agent to chat with a complaining guest, for a duty manager to read an in-progress chat. The chat module is currently a front-office-only product.

### 4.4 Maintenance reporter from the kitchen / restaurant floor

Affected roles: every kitchen role, every F&B role, every guest-relations role.
Capability gap: `_MAINTENANCE_REPORTER` is on `front_office`, `housekeeping` department presets and on `front_office_manager` / `front_desk_agent` / `housekeeping_*` / `maintenance_*` role presets only. F&B, kitchen, GR cannot file a maintenance ticket.
Operational consequence: a kitchen porter who finds a leaking dishwasher cannot file the request from their own UI. A waiter who sees a broken dining-room AC cannot file. A guest-relations agent escalating a guest complaint about no hot water cannot file.

### 4.5 Department-head supervising attendance

Affected roles: `front_office_manager`, `housekeeping_manager`, `maintenance_manager`, `fnb_manager`, every `_supervisor` role.
Capability gap: no preset between `_ATTENDANCE_SELF_SERVICE` and `_ATTENDANCE_MANAGE`.
Operational consequence: a department head cannot read their own department's roster, cannot see who is currently clocked in, cannot approve an unrostered clock-in. All shift-management goes through `hotel_manager`.

### 4.6 Front office cannot operate room services

Affected roles: `front_office_manager`, `front_office_supervisor`, `duty_manager`.
Capability gap: `_ROOM_SERVICE_OPERATE` not granted.
Operational consequence: front office cannot accept / complete a room-service order even though they are usually the ones picking up the call. Currently only `front_desk_agent` (via role preset) and kitchen + hotel\_manager can.

### 4.7 Maintenance staff cannot see room context

Affected roles: every `maintenance_*` role.
Capability gap: `housekeeping` module not visible (§3.3); `guest.record.read` absent; `booking` module absent.
Operational consequence: a technician investigating "guest in 412 reports broken kettle" sees a maintenance ticket with a room number and nothing else — no current occupant, no reservation context, no whether the room is occupied right now.

### 4.8 Guest Relations is functionally non-existent

Affected roles: every `guest_relations_*` role.
Capability gap: `guest_relations` department has **no entry** in `DEPARTMENT_PRESET_CAPABILITIES`. None of the GR roles are in `ROLE_PRESET_CAPABILITIES`.
Operational consequence: a GR agent has tier-default access only — staff\_chat, attendance-self, room-services-read. They cannot access guests, guest chat, bookings, rooms, hotel info, maintenance, housekeeping, restaurant bookings.

### 4.9 Duty Manager dashboard is empty

Affected roles: `duty_manager`.
Capability gap: see §3.7.
Operational consequence: covered above. The most senior on-duty role sees no operational data.

---

## 5. Over-Granular Areas

### 5.1 Attendance (extreme)

37 capability slugs (every `period_*`, `shift_*`, `daily_plan_*`, `face_*`, `log_*` is its own slug). Distribution into bundles: only two bundles exist — `_ATTENDANCE_SELF_SERVICE` (self) and `_ATTENDANCE_MANAGE` (everything else). There is no intermediate "supervise my department's roster" bundle. Suggested grouping (conceptual only):
- `_ATTENDANCE_DEPARTMENT_HEAD` = self-service + `shift_read` + `period_read` + `daily_plan_read` + `log_read_all` + `analytics_read` + `roster_read` + `shift_location_read`.
- `_ATTENDANCE_SUPERVISE` = department-head + `log_approve` + `log_reject` + `log_relink` + `shift_create/update/bulk_write/copy/export_pdf`.

### 5.2 Face registration

Five slugs (`face_register_self`, `face_register_other`, `face_revoke`, `face_audit_read`, `face_read`) granted nowhere except the `_ATTENDANCE_MANAGE` mega-bundle. A "kiosk operator" or "shift lead can re-register a teammate after a haircut" persona is not modelled.

### 5.3 Chat moderation vs assignment vs send vs respond

Five chat capabilities, three different routing concepts:
- `CHAT_MESSAGE_SEND` — authoring authority.
- `CHAT_CONVERSATION_ASSIGN` — handoff authority (granted by tier `staff_admin`/`super_staff_admin` AND by dept `front_office`).
- `CHAT_GUEST_RESPOND` — *routing eligibility*, not authority (only `front_office` dept).
- `CHAT_MESSAGE_MODERATE` — hard-delete other staff's messages (only tier `staff_admin`/`super_staff_admin`).
- `CHAT_CONVERSATION_READ` / `CHAT_MODULE_VIEW` — visibility.

`CHAT_CONVERSATION_ASSIGN` shows up in two places (tier supervisor authority **and** front\_office dept). That is probably correct but worth flagging — `front_office_supervisor` (dept-only) gets it from dept; `duty_manager` (tier-only) gets it from tier; both go through different code paths but resolve to the same boolean.

### 5.4 Maintenance lifecycle

Twelve capability slugs for one resource (request) — `read / create / accept / resolve / update / reassign / reopen / close / delete / comment.create / comment.moderate / photo.upload / photo.delete`. This is fine for enforcement, but the *preset* shape is: `_MAINTENANCE_REPORTER` (3 slugs) → `_MAINTENANCE_OPERATE` (5) → `_MAINTENANCE_SUPERVISE` (10) → `_MAINTENANCE_MANAGE` (12). Reasonable. The pain is that `_MAINTENANCE_REPORTER` is granted to surprisingly few personas (see §4.4).

### 5.5 Rooms vs housekeeping namespace duplication

Two capabilities can transition room status:
- `ROOM_STATUS_TRANSITION` (rooms module action `status_transition`)
- `HOUSEKEEPING_ROOM_STATUS_TRANSITION` (housekeeping module action `status_transition`)

Both gate the same room-state mutation but live in different namespaces and different module-policy buckets. Maintenance department only gets the housekeeping one; housekeeping department gets the room one (`_ROOM_OPERATE`) plus the housekeeping one. That is two ways to express "I can move a room into cleaning". Frontend rbac payload reflects this as two booleans on two different modules — confusing.

### 5.6 Staff Management department-head split

The `_STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW` bundle is *one* capability (`staff.read`). Its very existence as a named bundle, plus the deliberate omission of `module.view`, makes §3.1 inevitable. Either grant `module.view` or remove the bundle entirely.

---

## 6. Nav vs RBAC Mismatches

### 6.1 `TIER_DEFAULT_NAVS['super_staff_admin']` includes `staff_management`, but rbac visibility requires a role preset

Source: [staff/permissions.py L40-L54](staff/permissions.py#L40-L54).

```python
TIER_DEFAULT_NAVS = {
    'super_staff_admin': {
        'home', 'rooms', 'room_bookings', 'restaurant_bookings', 'chat',
        'housekeeping', 'attendance', 'staff_management',
        'room_services', 'maintenance', 'hotel_info',
        'admin_settings',
    },
    ...
}
```

Effect: any `super_staff_admin` tier user without a role preset (e.g. `duty_manager`) gets the nav slugs `rooms`, `housekeeping`, `staff_management`, `room_services` (full), `maintenance`, `hotel_info`, `admin_settings` listed in `allowed_navs`, but `rbac.<module>.visible=false` for all of them. The frontend sees nav = `["staff_management"]` plus `rbac.staff_management.visible=false`. Behaviour depends on whether the navbar uses `allowed_navs` (legacy) or `rbac.<module>.visible` (new contract).

The same holds for `staff_admin` tier and `housekeeping`, `maintenance`, `hotel_info` nav slugs.

### 6.2 `TIER_DEFAULT_NAVS['super_staff_admin']` includes `chat`, but `_CHAT_BASE` is not on the SSA tier preset

Tier `super_staff_admin` carries `_SUPERVISOR_AUTHORITY | _BOOKING_SUPERVISE | _STAFF_CHAT_BASE | _ATTENDANCE_SELF_SERVICE | _ROOM_SERVICE_BASE`. There is no `_CHAT_BASE`. So `chat` nav is auto-listed, but `rbac.chat.visible=false` for any SSA staff who lacks role/dept that contributes `_CHAT_BASE` (i.e. `duty_manager`).

### 6.3 `Role.default_navigation_items` (DB-driven) is independent of capabilities

`resolve_effective_access` ([staff/permissions.py L207-L215](staff/permissions.py#L207-L215)) unions `role.default_navigation_items` into `allowed_navs`. Whatever the seeders/admin assigned to a role's nav M2M is included regardless of whether that role's *capability* preset gives module visibility. Drift between a role's nav M2M and its capability bundle is invisible to the RBAC validators (only `validate_preset_maps` and `validate_module_policy` exist; no validator checks "every nav slug a role grants has a corresponding `module.view` capability").

### 6.4 Module visible without read, or read without module visible

| Persona / dept            | Module          | visible | read | Why                                   |
| ------------------------- | --------------- | :-----: | :--: | ------------------------------------- |
| any front\_office without role preset | housekeeping | ✅ | ❌ | dept gives `MODULE_VIEW` but not `TASK_READ` (§3.2) |
| `front_office_manager` and other dept-head roles | staff\_management | ❌ | ✅ | `_DEPARTMENT_HEAD_VIEW` grants `STAFF_READ` only (§3.1) |
| any maintenance dept | housekeeping | ❌ | ❌ but `STATUS_TRANSITION` granted | cap exists with no module surface (§3.3) |

---

## 7. Recommended Direction (high-level only — not an implementation plan)

1. **Fill in the empty role and department presets.** All canonical roles and all canonical departments should have *some* entry, even if minimal. Specifically:
   - `management` department → at least booking-read, room-read, housekeeping-read, maintenance-read, chat-base, guest-record-read, attendance-read-all, hotel-info-read. This is what a duty manager's job actually requires.
   - `guest_relations` department → chat-base, chat-guest-respond, guests-operate, hotel-info-read, booking-read.
   - `administration` department → staff-management-basic at minimum (it is the dept the staff-management role personas live in).
   - `kitchen` department → add `_MAINTENANCE_REPORTER` and `_HOTEL_INFO_READ`. Kitchen porters file maintenance tickets.
   - `food_beverage` department → add `_CHAT_BASE` (probably without `guest_respond` routing), `_MAINTENANCE_REPORTER`, `_HOTEL_INFO_READ`, `GUEST_RECORD_READ`, `_BOOKING_READ`.

2. **Add a `_*_DEPARTMENT_HEAD` middle bundle for attendance.** Self-service ↔ full-manage is too steep. Department heads need read across logs/shifts/periods/daily-plans/analytics within their hotel. Likely one shared bundle granted to every `*_manager` role (front\_office\_manager, housekeeping\_manager, maintenance\_manager, fnb\_manager, kitchen\_manager once it has a preset).

3. **Give every `*_supervisor` and `*_manager` role an explicit preset.** The current pattern of "manager-tier already covers it" only holds for `hotel_manager`, because `hotel_manager` is the only role that adds *role* capabilities on top of an `super_staff_admin` tier. All other manager / supervisor roles silently inherit nothing.

4. **Resolve the `staff_management.module.view` mismatch.** Either: (a) add `STAFF_MANAGEMENT_MODULE_VIEW` to `_STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW`, or (b) drop the bundle and grant nothing — the frontend already hides the module so endpoint-level `staff.read` access is moot.

5. **Add `HOUSEKEEPING_TASK_READ` to the `front_office` department preset** (or replace `HOUSEKEEPING_MODULE_VIEW` there with `_HOUSEKEEPING_BASE`). Pick whichever doesn't drift the comment about front desk being read-only on housekeeping.

6. **Add `_CHAT_BASE` to a wider set of dept/role presets**: `food_beverage`, `kitchen`, `maintenance`, `guest_relations`, `management`. Hotel-wide guest-chat *visibility* (read + module.view + maybe message\_send) is a normal expectation.

7. **Add `_ROOM_SERVICE_OPERATE` to `front_office_manager` / `front_office_supervisor`.** Front office is the most common channel for room-service order intake.

8. **Add a `room` read fallback to maintenance role presets** (or just `BOOKING_RECORD_READ` + `GUEST_RECORD_READ` for context lookups). Maintenance currently sees rooms but not who is in them.

9. **Decide whether `category_manage` for hotel\_info should remain superuser-only.** If yes, document it clearly. If no, add it to `_HOTEL_INFO_MANAGE`.

10. **Add a validator that asserts `view_capability ⊆ read_capability ∪ {view_capability}` is consistently assigned across presets**, i.e. no preset grants module view without granting module read (or vice versa). The current `validate_module_policy` only checks slug-existence, not preset-distribution coherence.

---

## 8. Final Verdict

- **Is the current RBAC too strict?** Yes, in two distinct ways:
  1. *Distribution* — large categories of canonical roles and departments have empty preset entries, so every staff member inheriting from those slugs is effectively limited to tier defaults.
  2. *Modularity* — module `view` and module `read` capabilities live in different bundles and presets do not always grant both, producing visible-but-unreadable / read-but-invisible modules.

- **Areas that are healthy:**
  - The capability *catalog* itself (every endpoint has a slug, the namespacing is consistent).
  - The `hotel_manager` role preset (full coverage).
  - The `front_desk_agent` + `front_office` department combo (covers booking operate, room read, housekeeping front-desk, maintenance reporter, chat, guests, hotel-info, room services).
  - The `housekeeper` + `housekeeping` department combo (covers room operate, housekeeping operate, maintenance reporter).
  - The `staff_admin` / `super_staff_admin` *role* personas (clean staff-management-only bundles).
  - The `fnb_manager` + `food_beverage` combo *for restaurant booking specifically* (everything else is a hole).

- **Areas that became unrealistic:**
  - **`duty_manager`** and the entire `management` department: empty.
  - **All three `guest_relations_*` roles** + the `guest_relations` department: empty.
  - **All three `kitchen_*` roles**: indistinguishable from each other, with no chat / maintenance / hotel\_info / guests visibility.
  - **All `*_supervisor` roles**: same access as their juniors except for staff-chat moderation.
  - **Attendance for any department head**: self-service only.
  - **Front office room-service operation**: cannot accept / complete orders.
  - **Cross-department guest chat**: front-office-only.

- **Modules safest to loosen first** (highest operational gain, lowest risk):
  1. `chat` (guest chat) — add `_CHAT_BASE` to F&B / kitchen / maintenance / guest\_relations / management.
  2. `hotel_info` — extend read to every department; it is read-only catalog data.
  3. `maintenance` — extend reporter bundle to F&B / kitchen / guest\_relations / management.
  4. `attendance` (department-head read bundle) — add a middle tier for `*_manager` roles.
  5. `guest_relations` department preset — fill in.
  6. `management` department preset — fill in (covers `duty_manager`, `hotel_manager` is already covered by its role).
  7. `staff_management` module-view fix for department heads.

These are the seven changes that would convert the current "technically correct" RBAC into an operationally realistic one without re-opening any sensitive surface (write-on-bookings, write-on-rooms, write-on-staff-management, destructive checkout, face-revoke, period-finalize, etc. all stay role-gated as they are).
