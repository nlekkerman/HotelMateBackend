# RBAC Operational Rebalance Audit

> Companion to [RBAC_OPERATIONAL_VISIBILITY_AUDIT.md](RBAC_OPERATIONAL_VISIBILITY_AUDIT.md). This document focuses on the **rebalance plan**: which preset bundles to introduce, which presets to expand, and in what phased order — without changing the RBAC architecture, capability slugs, module policy shape, or enforcement primitives.
>
> **Scope:** preset distribution only.
> **Out of scope:** capability namespace, `module_policy.py`, `resolve_module_policy`, `HasCapability`, frontend `can()` / `useCan()`, fail-closed semantics, role-slug / tier / nav-based authority (none of those are reintroduced).
>
> **Sources of truth (code only, comments ignored):**
> [staff/capability_catalog.py](staff/capability_catalog.py), [staff/module_policy.py](staff/module_policy.py), [staff/permissions.py](staff/permissions.py), [staff/role_catalog.py](staff/role_catalog.py), [staff/department_catalog.py](staff/department_catalog.py), [staff/nav_catalog.py](staff/nav_catalog.py).

---

## 0. Architectural Invariants (must remain)

These are not negotiable and every recommendation below respects them:

| Invariant | Where enforced (code) | Recommendation impact |
| --- | --- | --- |
| Capabilities are the only authority | `HasCapability` in [staff/permissions.py](staff/permissions.py) and per-app permission classes | No new role-slug / tier-`>=` / nav-based gate is proposed. |
| `module_policy.py` is the canonical projection | [staff/module_policy.py](staff/module_policy.py#L487) `resolve_module_policy` | Module/action shape stays as-is. We only change which presets contain which capability slugs. |
| Resolver is additive union | [staff/capability_catalog.py](staff/capability_catalog.py#L1898) `resolve_capabilities` | Only the three preset maps mutate. |
| Fail-closed | [module_policy.py L506-L538](staff/module_policy.py#L506-L538) — unknown caps → False | Preserved. We never bypass `CANONICAL_CAPABILITIES`. |
| `super_user` = full | `is_superuser` short-circuit in `resolve_capabilities` | Preserved. |
| `category.manage` (hotel info) is superuser-only | not in any preset | Preserved (recommendation: document it; do not grant to anyone else). |

---

## 1. Code-Derived Diagnosis (compressed)

Full per-persona evidence is in [RBAC_OPERATIONAL_VISIBILITY_AUDIT.md](RBAC_OPERATIONAL_VISIBILITY_AUDIT.md). Summary of the issues that drive the rebalance plan:

1. **Empty role presets** — 11 canonical role slugs have no entry in `ROLE_PRESET_CAPABILITIES`:
   `front_office_supervisor`, `housekeeper`, `fb_supervisor`, `kitchen_staff`, `kitchen_supervisor`, `kitchen_manager`, `maintenance_staff`, `guest_relations_agent`, `guest_relations_supervisor`, `guest_relations_manager`, `duty_manager`.
2. **Empty department presets** — 3 canonical departments have no entry in `DEPARTMENT_PRESET_CAPABILITIES`: `management`, `administration`, `guest_relations`.
3. **Visible-but-unreadable** — `front_office` dept grants `HOUSEKEEPING_MODULE_VIEW` without `HOUSEKEEPING_TASK_READ`.
4. **Read-but-invisible** — `_STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW` grants `STAFF_MANAGEMENT_STAFF_READ` without `STAFF_MANAGEMENT_MODULE_VIEW`.
5. **Phantom capability** — `maintenance` dept grants `HOUSEKEEPING_ROOM_STATUS_TRANSITION` without `HOUSEKEEPING_MODULE_VIEW`.
6. **Attendance has no supervisory tier** — only `_ATTENDANCE_SELF_SERVICE` and `_ATTENDANCE_MANAGE` (hotel\_manager-only). No `*_manager` / `*_supervisor` can read their dept's roster.
7. **Chat is front-office-only** — `_CHAT_BASE` is in `front_office` dept and `hotel_manager` role only. Duty managers, GR, F&B, kitchen, maintenance, housekeeping cannot see guest chat.
8. **Front office cannot operate room services** — `_ROOM_SERVICE_OPERATE` not in FO dept, FOM, FOS, duty\_manager.
9. **Maintenance reporter is too narrow** — F&B, kitchen, GR cannot file tickets.
10. **Nav vs capability drift** — `TIER_DEFAULT_NAVS['super_staff_admin']` includes nav slugs whose `module.view` capability is not on the SSA tier preset (`chat`, `housekeeping`, `staff_management`, `maintenance`, `hotel_info`, `room_services` write).
11. **Supervisor roles are decorative** — `front_office_supervisor`, `housekeeping_supervisor`*, `fb_supervisor`, `kitchen_supervisor`, `guest_relations_supervisor` are operationally indistinguishable from juniors of the same dept.
    \* `housekeeping_supervisor` actually does have a role preset (`_ROOM_SUPERVISE | _HOUSEKEEPING_SUPERVISE`) — it is the exception.
12. **Role equivalency** — all three `kitchen_*` roles resolve to identical capability sets; all three `guest_relations_*` roles resolve to identical (empty-beyond-tier) sets.

---

## 2. Target Operating Philosophy → Bundle Translation

| Persona band | Operational meaning | Capability shape |
| --- | --- | --- |
| Execution staff (`*_staff`, `housekeeper`, `waiter`, `front_desk_agent`, `kitchen_staff`, `maintenance_staff`, `guest_relations_agent`) | Do the work; coordinate via chat; file tickets. | Department `_OPERATE`/`_BASE` for own module; `_CHAT_BASE` (visibility, send) where guest interaction happens; `_MAINTENANCE_REPORTER`; `_HOTEL_INFO_READ`; `_ATTENDANCE_SELF_SERVICE`. |
| Supervisor (`*_supervisor`) | Lead a shift in own dept; read own dept's roster/logs/dashboards; cross-dept *read* of adjacent operational state. | Own dept `_SUPERVISE`; `_ATTENDANCE_DEPARTMENT_HEAD_READ` (NEW); `_HOTEL_INFO_READ`; `_CHAT_BASE`; cross-dept read of operationally adjacent modules. |
| Department head (`*_manager`) | Manage own department end-to-end; supervise own dept's attendance (write); coordinate with peer departments. | Own dept `_MANAGE` (or `_SUPERVISE` where authority is split with `hotel_manager`); `_ATTENDANCE_DEPARTMENT_HEAD_WRITE` (NEW, scoped); `_STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW` + `STAFF_MANAGEMENT_MODULE_VIEW`; cross-dept read; `_CHAT_BASE`. |
| Cross-department duty (`duty_manager`) | Hold the hotel together for one shift across all departments. | Hotel-wide *read* across all operational modules + `_CHAT_BASE` + `_ATTENDANCE_DEPARTMENT_HEAD_READ`. **No** destructive / config / staff-management authority. |
| Hotel manager (`hotel_manager`) | Already correct. | (no change) |
| Staff-management role personas (`staff_admin`, `super_staff_admin`) | Already correct. | (no change) |

---

## 3. New Bundles Proposed (additive, no slug renames, no slug additions)

All bundles below are unions of **already-canonical** capabilities. None of them introduces a new capability slug.

### 3.1 `_ATTENDANCE_DEPARTMENT_HEAD_READ`

Closes the gap where managers cannot read their own department's attendance.

```
_ATTENDANCE_DEPARTMENT_HEAD_READ =
    _ATTENDANCE_SELF_SERVICE | {
        ATTENDANCE_LOG_READ_ALL,
        ATTENDANCE_SHIFT_READ,
        ATTENDANCE_PERIOD_READ,
        ATTENDANCE_DAILY_PLAN_READ,
        ATTENDANCE_SHIFT_LOCATION_READ,
        ATTENDANCE_ANALYTICS_READ,
        ATTENDANCE_FACE_READ,
    }
```

No write authority. Backend per-row scoping (own department) is already enforced at the view layer in [attendance/views.py](attendance/views.py); this bundle does not change that.

### 3.2 `_ATTENDANCE_DEPARTMENT_HEAD_WRITE`

Department heads compose rosters and approve unrostered logs for their own dept.

```
_ATTENDANCE_DEPARTMENT_HEAD_WRITE =
    _ATTENDANCE_DEPARTMENT_HEAD_READ | {
        ATTENDANCE_LOG_CREATE,
        ATTENDANCE_LOG_UPDATE,
        ATTENDANCE_LOG_APPROVE,
        ATTENDANCE_LOG_REJECT,
        ATTENDANCE_LOG_RELINK,
        ATTENDANCE_SHIFT_CREATE,
        ATTENDANCE_SHIFT_UPDATE,
        ATTENDANCE_SHIFT_DELETE,
        ATTENDANCE_SHIFT_BULK_WRITE,
        ATTENDANCE_SHIFT_COPY,
        ATTENDANCE_SHIFT_EXPORT_PDF,
        ATTENDANCE_DAILY_PLAN_MANAGE,
        ATTENDANCE_DAILY_PLAN_ENTRY_MANAGE,
    }
```

Deliberately excluded (kept on `hotel_manager` only via `_ATTENDANCE_MANAGE`): `ATTENDANCE_PERIOD_CREATE/UPDATE/DELETE/FINALIZE/UNFINALIZE/FORCE_FINALIZE`, `ATTENDANCE_LOG_DELETE`, `ATTENDANCE_SHIFT_LOCATION_MANAGE`, `ATTENDANCE_FACE_REGISTER_OTHER`, `ATTENDANCE_FACE_REVOKE`, `ATTENDANCE_FACE_AUDIT_READ`. Period lifecycle and face-record lifecycle stay hotel-manager-only.

### 3.3 `_GUEST_RELATIONS_OPERATE`

Gives the guest-relations department a real preset.

```
_GUEST_RELATIONS_OPERATE =
    _CHAT_BASE | _GUESTS_OPERATE | _HOTEL_INFO_READ | _BOOKING_READ | _MAINTENANCE_REPORTER | {
        CHAT_GUEST_RESPOND,
        CHAT_CONVERSATION_ASSIGN,
    }
```

`CHAT_GUEST_RESPOND` is added so GR is auto-routed inbound guest pings (currently only front\_office is). `CHAT_CONVERSATION_ASSIGN` lets GR hand a conversation back to front office. No write on bookings, no rooms / housekeeping / maintenance write.

### 3.4 `_DUTY_MANAGER_READ`

Hotel-wide read for the manager-on-duty.

```
_DUTY_MANAGER_READ =
    _ROOM_READ |
    _HOUSEKEEPING_BASE |               # task.read + dashboard.read + history + module.view
    _MAINTENANCE_READ |
    _CHAT_BASE | { CHAT_CONVERSATION_ASSIGN, CHAT_MESSAGE_MODERATE } |
    _GUESTS_READ |
    _HOTEL_INFO_READ |
    _RESTAURANT_BOOKING_BASE |
    _ATTENDANCE_DEPARTMENT_HEAD_READ
```

Plus the booking-supervise tier already gives `_BOOKING_SUPERVISE`. Net result: duty manager can *see* every operational dashboard and override bookings, but cannot manage rosters, edit menus, mutate inventory, or run staff-management.

### 3.5 `_FRONT_OFFICE_COORDINATION`

Patches the four FO contradictions (housekeeping read, RS operate, attendance read, chat already covered by dept).

```
_FRONT_OFFICE_COORDINATION =
    _HOUSEKEEPING_BASE |               # adds TASK_READ + DASHBOARD_READ; module.view already on dept
    _ROOM_SERVICE_OPERATE |
    _ATTENDANCE_DEPARTMENT_HEAD_READ
```

### 3.6 `_KITCHEN_OPERATE_EXTENDED`

```
_KITCHEN_OPERATE_EXTENDED =
    _ROOM_SERVICE_OPERATE | { ROOM_SERVICE_ORDER_FULFILL_KITCHEN } |
    _MAINTENANCE_REPORTER |
    _HOTEL_INFO_READ |
    _CHAT_BASE                        # send-only; no guest_respond routing
```

`_CHAT_BASE` here is contentious — the user-facing decision is whether kitchen line cooks should see the guest-chat module. It is included so a kitchen porter who finds a guest-affecting issue (allergy mix-up) can read a conversation thread, not just file a maintenance ticket. If the product position is "no kitchen on guest chat", drop `_CHAT_BASE` from this bundle — every other recommendation still holds.

### 3.7 `_FB_OPERATE_EXTENDED`

```
_FB_OPERATE_EXTENDED =
    _RESTAURANT_BOOKING_OPERATE |
    _MAINTENANCE_REPORTER |
    _HOTEL_INFO_READ |
    _GUESTS_READ |
    _BOOKING_READ |
    _CHAT_BASE
```

Lets a waiter look up a charge-to-room guest, file a ticket about a broken POS, read the hotel-info menu translations, and see the guest-chat thread for tonight's reservation.

### 3.8 `_STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW` (fix existing bundle)

Add `STAFF_MANAGEMENT_MODULE_VIEW` to the existing bundle so module visibility and module read agree. This is the smallest change in the entire rebalance and is purely a correctness fix for §3.1 of the visibility audit.

```
_STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW =
    _STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW | { STAFF_MANAGEMENT_MODULE_VIEW }
```

### 3.9 `_FRONT_OFFICE_DEPT_FIX` (fix existing dept preset)

Add `HOUSEKEEPING_TASK_READ` and `HOUSEKEEPING_DASHBOARD_READ` to the `front_office` department preset — closes the visible-but-unreadable housekeeping mismatch for the FO supervisor and FO agent. (The FOM is already covered by `_HOUSEKEEPING_SUPERVISE`.)

### 3.10 `_MAINTENANCE_DEPT_FIX` (fix existing dept preset)

Add `HOUSEKEEPING_MODULE_VIEW` to the `maintenance` department preset so the already-granted `HOUSEKEEPING_ROOM_STATUS_TRANSITION` has a UI surface; also add `HOUSEKEEPING_DASHBOARD_READ` and `HOUSEKEEPING_TASK_READ` so technicians can see what room state is live. No write authority added beyond what the dept already has.

---

## 4. Per-Preset Rebalance Plan

This section lists the **proposed** state of each preset map. Additions are marked `+`, no deletions are proposed.

### 4.1 `TIER_DEFAULT_CAPABILITIES`

| Tier | Current bundle | Proposed bundle | Δ |
| --- | --- | --- | --- |
| `super_staff_admin` | `_SUPERVISOR_AUTHORITY \| _BOOKING_SUPERVISE \| _STAFF_CHAT_BASE \| _ATTENDANCE_SELF_SERVICE \| _ROOM_SERVICE_BASE` | (no change) | — |
| `staff_admin` | `_SUPERVISOR_AUTHORITY \| _STAFF_CHAT_BASE \| _ATTENDANCE_SELF_SERVICE \| _ROOM_SERVICE_BASE` | (no change) | — |
| `regular_staff` | `_STAFF_CHAT_BASE \| _ATTENDANCE_SELF_SERVICE \| _ROOM_SERVICE_BASE` | (no change) | — |

**Tier intentionally stays as-is.** All operational gain comes from role + department presets. This preserves the contract "tier is not the permission engine".

### 4.2 `DEPARTMENT_PRESET_CAPABILITIES`

| Department | Current | Proposed additions |
| --- | --- | --- |
| `front_office` | (current) | `+ HOUSEKEEPING_TASK_READ`, `+ HOUSEKEEPING_DASHBOARD_READ` (§3.9) |
| `housekeeping` | `_ROOM_OPERATE \| _HOUSEKEEPING_OPERATE \| _MAINTENANCE_REPORTER` | `+ _CHAT_BASE` (housekeeping ↔ guest "found item / lost item" coordination) |
| `kitchen` | `{ROOM_SERVICE_ORDER_FULFILL_KITCHEN} \| _ROOM_SERVICE_OPERATE` | `+ _MAINTENANCE_REPORTER`, `+ _HOTEL_INFO_READ` (chat decision deferred — see §3.6) |
| `food_beverage` | `_RESTAURANT_BOOKING_OPERATE` | `+ _MAINTENANCE_REPORTER`, `+ _HOTEL_INFO_READ`, `+ _GUESTS_READ`, `+ _BOOKING_READ`, `+ _CHAT_BASE` |
| `maintenance` | (current) | `+ HOUSEKEEPING_MODULE_VIEW`, `+ HOUSEKEEPING_TASK_READ`, `+ HOUSEKEEPING_DASHBOARD_READ`, `+ _CHAT_BASE`, `+ GUEST_RECORD_READ`, `+ BOOKING_RECORD_READ`, `+ BOOKING_MODULE_VIEW` (§3.10 + room context) |
| `guest_relations` | **(empty)** | `_GUEST_RELATIONS_OPERATE` (§3.3) — net new entry |
| `management` | **(empty)** | `_DUTY_MANAGER_READ` (§3.4) — net new entry; covers `duty_manager` and other management-dept personas |
| `administration` | **(empty)** | `_STAFF_MANAGEMENT_BASIC` (lets administration-dept staff see staff-management module by default; staff-admin role persona already grants the same set, so this is a soft floor) |

### 4.3 `ROLE_PRESET_CAPABILITIES`

Existing entries unchanged unless noted. New entries for currently-missing roles.

| Role | Current | Proposed |
| --- | --- | --- |
| `hotel_manager` | full | `+ CHAT_GUEST_RESPOND` (so GM can be auto-routed when on duty); otherwise no change |
| `front_office_manager` | `_BOOKING_MANAGE \| _ROOM_SUPERVISE \| _HOUSEKEEPING_SUPERVISE \| _MAINTENANCE_REPORTER \| _GUESTS_OPERATE \| _HOTEL_INFO_READ \| _STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW` | `+ _ATTENDANCE_DEPARTMENT_HEAD_WRITE`, `+ _ROOM_SERVICE_OPERATE`, `+ _MAINTENANCE_OPERATE` (FOM picks up tickets in absentia of maintenance manager — operate, not manage) |
| `front_office_supervisor` | **(none)** | `_FRONT_OFFICE_COORDINATION \| _ATTENDANCE_DEPARTMENT_HEAD_READ \| _MAINTENANCE_REPORTER` (read-tier coordination; no booking manage, no housekeeping write beyond front-desk transitions which dept already provides) |
| `front_desk_agent` | (current) | `+ _FRONT_OFFICE_COORDINATION` *minus* the attendance read piece (agents do not need to read the team roster) → effectively `+ _HOUSEKEEPING_BASE`, `+ _ROOM_SERVICE_OPERATE` (dept will already cover via §4.2) |
| `housekeeping_manager` | `_ROOM_SUPERVISE \| _HOUSEKEEPING_MANAGE \| _STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW` | `+ _ATTENDANCE_DEPARTMENT_HEAD_WRITE`, `+ _MAINTENANCE_REPORTER`, `+ _CHAT_BASE`, `+ _HOTEL_INFO_READ` |
| `housekeeping_supervisor` | `_ROOM_SUPERVISE \| _HOUSEKEEPING_SUPERVISE` | `+ _ATTENDANCE_DEPARTMENT_HEAD_READ`, `+ _MAINTENANCE_REPORTER`, `+ _CHAT_BASE`, `+ _HOTEL_INFO_READ` |
| `housekeeper` | **(none)** | `+ _MAINTENANCE_REPORTER` (already on dept — keep as no-op safety), `+ _HOTEL_INFO_READ` |
| `maintenance_manager` | `{ROOM_MAINTENANCE_CLEAR, ROOM_OUT_OF_ORDER_SET, HOUSEKEEPING_ROOM_STATUS_OVERRIDE} \| _MAINTENANCE_MANAGE \| _STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW` | `+ _ATTENDANCE_DEPARTMENT_HEAD_WRITE`, `+ _CHAT_BASE`, `+ _HOTEL_INFO_READ` |
| `maintenance_supervisor` | `{ROOM_MAINTENANCE_CLEAR, HOUSEKEEPING_ROOM_STATUS_OVERRIDE} \| _MAINTENANCE_SUPERVISE` | `+ _ATTENDANCE_DEPARTMENT_HEAD_READ`, `+ _CHAT_BASE`, `+ _HOTEL_INFO_READ` |
| `maintenance_staff` | **(none)** | `+ _HOTEL_INFO_READ`, `+ _CHAT_BASE` (read + send for "I am in your room now" context); dept already covers maintenance ops |
| `fnb_manager` | `_RESTAURANT_BOOKING_MANAGE \| _STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW` | `+ _ATTENDANCE_DEPARTMENT_HEAD_WRITE`, `+ _MAINTENANCE_REPORTER`, `+ _BOOKING_READ`, `+ _GUESTS_READ`, `+ _HOTEL_INFO_READ`, `+ _CHAT_BASE` |
| `fb_supervisor` | **(none)** | `_FB_OPERATE_EXTENDED \| _ATTENDANCE_DEPARTMENT_HEAD_READ` |
| `waiter` | `_RESTAURANT_BOOKING_OPERATE` | `+ _FB_OPERATE_EXTENDED` (mostly covered by dept addition above; redundancy is fine — `set` union is idempotent) |
| `kitchen_manager` | **(none)** | `_KITCHEN_OPERATE_EXTENDED \| _ATTENDANCE_DEPARTMENT_HEAD_WRITE \| _STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW \| ROOM_SERVICE_MENU_ITEM_CREATE/UPDATE/IMAGE_MANAGE` (chef edits the menu — but **not** `MENU_ITEM_DELETE`, which stays with hotel\_manager) |
| `kitchen_supervisor` | **(none)** | `_KITCHEN_OPERATE_EXTENDED \| _ATTENDANCE_DEPARTMENT_HEAD_READ` |
| `kitchen_staff` | **(none)** | (none beyond dept additions in §4.2) |
| `guest_relations_manager` | **(none)** | `_GUEST_RELATIONS_OPERATE \| _ATTENDANCE_DEPARTMENT_HEAD_WRITE \| _STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW \| _HOTEL_INFO_MANAGE \| _MAINTENANCE_REPORTER \| GUEST_RECORD_UPDATE \| BOOKING_RECORD_UPDATE \| BOOKING_GUEST_COMMUNICATE` (write authority on guest record + ability to send pre-checkin / survey) |
| `guest_relations_supervisor` | **(none)** | `_GUEST_RELATIONS_OPERATE \| _ATTENDANCE_DEPARTMENT_HEAD_READ \| BOOKING_GUEST_COMMUNICATE` |
| `guest_relations_agent` | **(none)** | `_GUEST_RELATIONS_OPERATE` (covered by dept) — explicit preset for symmetry |
| `duty_manager` | **(none)** | `_DUTY_MANAGER_READ \| _ATTENDANCE_DEPARTMENT_HEAD_READ` (dept covers most; role stamp ensures duty-manager works even if assigned an unusual department) |
| `staff_admin` (role) | `_STAFF_MANAGEMENT_BASIC` | (no change) |
| `super_staff_admin` (role) | `_STAFF_MANAGEMENT_FULL` | (no change) |

### 4.4 `TIER_DEFAULT_NAVS` (and Role.default_navigation_items)

Two consistency fixes:

1. **Drop nav slugs from tier defaults whose `module.view` capability is not on the same tier preset.**
   - `super_staff_admin` tier currently lists nav slugs `chat`, `housekeeping`, `staff_management`, `room_services`, `maintenance`, `hotel_info`, `admin_settings`. None of those `module.view` caps are on the SSA tier capability bundle. Recommended: trim `TIER_DEFAULT_NAVS['super_staff_admin']` to **only** the slugs whose `module.view` capability is contributed by the tier itself (currently: none beyond `home`, `room_bookings` if you accept booking-supervise as visibility-grant). Concretely the proposal is to align tier nav defaults to `{'home'}` for every tier and let role + department presets feed `allowed_navs` via per-role `Role.default_navigation_items` rows that the seeders maintain.
   - This eliminates the "nav slug present but `rbac.<module>.visible=false`" class of bug entirely.

2. **Validator addition** (no code, conceptual): introduce a `validate_nav_capability_consistency()` helper that, for every Role, asserts that every nav slug in `role.default_navigation_items` corresponds to a `MODULE_POLICY[<module>]['view_capability']` that the role's preset bundle contains. Same check for tier defaults. Surface failures via the same management-command path as `validate_preset_maps`.

(*The user explicitly said "do not implement". The above is design-only; a follow-up ticket would write the validator.*)

---

## 5. Visual Matrix — Proposed End State

Notation as in the visibility audit. "✅" means module visible AND read after the rebalance. "○" = read-only. "✏" = operate (write within bucket). "★" = supervise. "◆" = manage. "—" = no module visibility.

| Role \ Module                  | bookings | rooms | housekeeping | maintenance | attendance      | staff\_mgmt | chat | staff\_chat | guests | hotel\_info | room\_svc | restaurant\_bk |
| ------------------------------ | :------: | :---: | :----------: | :---------: | :-------------: | :---------: | :--: | :---------: | :----: | :---------: | :-------: | :------------: |
| `hotel_manager`                |    ◆     |   ◆   |       ◆      |      ◆      |        ◆        |      ◆      |  ✏★  |     ★◆      |   ✏    |      ◆      |    ◆      |       ◆        |
| `front_office_manager`         |    ◆     |   ★   |       ★      |      ✏      |  dept-write     | ○ (head)    |  ✏★  |     ★◆      |   ✏    |      ○      |    ✏      |       —        |
| `front_office_supervisor`      |    ✏     |   ○   |       ○      |      ○ (rep)|  dept-read      |     —       |  ✏   |     ★◆      |   ✏    |      ○      |    ✏      |       —        |
| `front_desk_agent`             |    ✏     |   ○   |       ○      |      ○ (rep)|  self           |     —       |  ✏   |     ✏       |   ✏    |      ○      |    ✏      |       —        |
| `duty_manager`                 |    ★     |   ○   |       ○      |      ○      |  dept-read      |     —       |  ✏★  |     ★◆      |   ○    |      ○      |    ○      |       ○        |
| `housekeeping_manager`         |    —     |   ★   |       ◆      |      ○ (rep)|  dept-write     | ○ (head)    |  ✏   |     ★◆      |   —    |      ○      |    ○      |       —        |
| `housekeeping_supervisor`      |    —     |   ★   |       ★      |      ○ (rep)|  dept-read      |     —       |  ✏   |     ★◆      |   —    |      ○      |    ○      |       —        |
| `housekeeper`                  |    —     |   ✏   |       ✏      |      ○ (rep)|  self           |     —       |  ✏   |     ✏       |   —    |      ○      |    ○      |       —        |
| `maintenance_manager`          |    ○     |   ◆   |       ○      |      ◆      |  dept-write     | ○ (head)    |  ✏   |     ★◆      |   ○    |      ○      |    ○      |       —        |
| `maintenance_supervisor`       |    ○     |   ✏   |       ○      |      ★      |  dept-read      |     —       |  ✏   |     ★◆      |   ○    |      ○      |    ○      |       —        |
| `maintenance_staff`            |    ○     |   ✏   |       ○      |      ✏      |  self           |     —       |  ✏   |     ✏       |   ○    |      ○      |    ○      |       —        |
| `fnb_manager`                  |    ○     |   —   |       —      |      ○ (rep)|  dept-write     | ○ (head)    |  ✏   |     ★◆      |   ○    |      ○      |    ○      |       ◆        |
| `fb_supervisor`                |    ○     |   —   |       —      |      ○ (rep)|  dept-read      |     —       |  ✏   |     ★◆      |   ○    |      ○      |    ○      |       ✏        |
| `waiter`                       |    ○     |   —   |       —      |      ○ (rep)|  self           |     —       |  ✏   |     ✏       |   ○    |      ○      |    ○      |       ✏        |
| `kitchen_manager`              |    —     |   —   |       —      |      ○ (rep)|  dept-write     | ○ (head)    |  ✏\* |     ★◆      |   —    |      ○      |    ✏ menu |       —        |
| `kitchen_supervisor`           |    —     |   —   |       —      |      ○ (rep)|  dept-read      |     —       |  ✏\* |     ★◆      |   —    |      ○      |    ✏      |       —        |
| `kitchen_staff`                |    —     |   —   |       —      |      ○ (rep)|  self           |     —       |  ✏\* |     ✏       |   —    |      ○      |    ✏      |       —        |
| `guest_relations_manager`     |    ✏     |   —   |       —      |      ○ (rep)|  dept-write     | ○ (head)    |  ✏★  |     ★◆      |   ✏    |      ◆      |    ○      |       —        |
| `guest_relations_supervisor`  |    ○     |   —   |       —      |      ○ (rep)|  dept-read      |     —       |  ✏★  |     ★◆      |   ✏    |      ○      |    ○      |       —        |
| `guest_relations_agent`        |    ○     |   —   |       —      |      ○ (rep)|  self           |     —       |  ✏★  |     ✏       |   ✏    |      ○      |    ○      |       —        |
| `staff_admin` (role)           |    —     |   —   |       —      |      —      |  self           |     ✏       |  —   |     ✏       |   —    |      —      |    ○      |       —        |
| `super_staff_admin` (role)     |    —     |   —   |       —      |      —      |  self           |     ◆       |  —   |     ★◆      |   —    |      —      |    ○      |       —        |

\* Kitchen `chat` visibility is the one product call-out (§3.6). If kitchen is to remain off guest chat, drop `_CHAT_BASE` from the kitchen role/department additions; the rest of the matrix is unaffected.

### 5.1 Destructive / sensitive actions blocked for non-`hotel_manager` (verification)

The rebalance keeps these on `hotel_manager` (and `super_user`) only:

| Capability | Stays only on | Rationale |
| --- | --- | --- |
| `BOOKING_CONFIG_MANAGE` | `_BOOKING_MANAGE` ⊂ hotel\_manager | Hotel-wide booking config. |
| `ROOM_INVENTORY_CREATE/UPDATE/DELETE` | `_ROOM_MANAGE` ⊂ hotel\_manager | Room inventory authority. |
| `ROOM_TYPE_MANAGE`, `ROOM_MEDIA_MANAGE`, `ROOM_OUT_OF_ORDER_SET`, `ROOM_CHECKOUT_DESTRUCTIVE` | `_ROOM_MANAGE` ⊂ hotel\_manager (`ROOM_OUT_OF_ORDER_SET` also on `maintenance_manager` — already current). | Destructive room operations. |
| `HOUSEKEEPING_TASK_DELETE` | `_HOUSEKEEPING_MANAGE` ⊂ hotel\_manager + housekeeping\_manager | Already correct. |
| `MAINTENANCE_REQUEST_DELETE`, `MAINTENANCE_REQUEST_CLOSE` | `_MAINTENANCE_MANAGE` ⊂ hotel\_manager + maintenance\_manager | Already correct. |
| `STAFF_MANAGEMENT_AUTHORITY_SUPERVISE`, all `STAFF_MANAGEMENT_*` writes | `_STAFF_MANAGEMENT_MANAGER` (hotel\_manager) and `_STAFF_MANAGEMENT_FULL`/`BASIC` (staff-admin role personas) | Anti-escalation preserved. |
| `ATTENDANCE_PERIOD_CREATE/UPDATE/DELETE/FINALIZE/UNFINALIZE/FORCE_FINALIZE` | `_ATTENDANCE_MANAGE` ⊂ hotel\_manager | Period lifecycle stays centralised. |
| `ATTENDANCE_LOG_DELETE`, `ATTENDANCE_FACE_REGISTER_OTHER`, `ATTENDANCE_FACE_REVOKE`, `ATTENDANCE_FACE_AUDIT_READ`, `ATTENDANCE_SHIFT_LOCATION_MANAGE` | `_ATTENDANCE_MANAGE` only | Privacy + destructive. |
| `HOTEL_INFO_CATEGORY_MANAGE` | superuser only | Platform-level. |
| `RESTAURANT_BOOKING_RESTAURANT_*`, `RESTAURANT_BOOKING_BLUEPRINT_MANAGE`, `RESTAURANT_BOOKING_TABLE_MANAGE`, `RESTAURANT_BOOKING_RECORD_DELETE`, `RESTAURANT_BOOKING_CATEGORY_MANAGE` | `_RESTAURANT_BOOKING_MANAGE` ⊂ hotel\_manager + fnb\_manager | Already correct. |

The new `_ATTENDANCE_DEPARTMENT_HEAD_WRITE` bundle deliberately stops short of period lifecycle, log delete and face authority. The new `_DUTY_MANAGER_READ` bundle is read-only across every operational module.

---

## 6. Phased Implementation Plan

Each phase is independently deployable and independently revertible.

### Phase 1 — Correctness fixes (visible/read mismatches)

Lowest risk. Pure data alignment.

- 1.1 Add `STAFF_MANAGEMENT_MODULE_VIEW` to `_STAFF_MANAGEMENT_DEPARTMENT_HEAD_VIEW` (§3.8).
- 1.2 Add `HOUSEKEEPING_TASK_READ` + `HOUSEKEEPING_DASHBOARD_READ` to the `front_office` dept preset (§3.9).
- 1.3 Add `HOUSEKEEPING_MODULE_VIEW` + `HOUSEKEEPING_DASHBOARD_READ` + `HOUSEKEEPING_TASK_READ` to the `maintenance` dept preset (§3.10).
- 1.4 Trim `TIER_DEFAULT_NAVS` to drop nav slugs whose `module.view` is not on the same tier (§4.4 item 1) — or alternatively (lower-disruption option) keep `TIER_DEFAULT_NAVS` as-is and rely on the frontend already consuming `rbac.<module>.visible`. Pick one.

Acceptance: `validate_module_policy()` still passes; new test asserts that for every preset, if `view_capability` is granted, `read_capability` is granted, and vice versa, when both exist.

### Phase 2 — Attendance supervisory layer

Closes the §3.6 / §4.5 gap.

- 2.1 Introduce `_ATTENDANCE_DEPARTMENT_HEAD_READ` + `_ATTENDANCE_DEPARTMENT_HEAD_WRITE` bundles (§3.1, §3.2).
- 2.2 Add `_ATTENDANCE_DEPARTMENT_HEAD_WRITE` to `front_office_manager`, `housekeeping_manager`, `maintenance_manager`, `fnb_manager`. Add (later) `kitchen_manager`, `guest_relations_manager` once those roles exist.
- 2.3 Add `_ATTENDANCE_DEPARTMENT_HEAD_READ` to `front_office_supervisor`, `housekeeping_supervisor`, `maintenance_supervisor`, `fb_supervisor`, `kitchen_supervisor`, `guest_relations_supervisor`, `duty_manager`.

Acceptance: the four current `*_manager` roles can now hit `/attendance/shifts/`, `/attendance/periods/`, `/attendance/analytics/`, `/attendance/department-status/` for their own department without 403.

### Phase 3 — Department coordination expansions

- 3.1 Fill `guest_relations` department preset with `_GUEST_RELATIONS_OPERATE` (§3.3).
- 3.2 Fill `management` department preset with `_DUTY_MANAGER_READ` (§3.4).
- 3.3 Fill `administration` department preset with `_STAFF_MANAGEMENT_BASIC`.
- 3.4 Add `_MAINTENANCE_REPORTER` + `_HOTEL_INFO_READ` to `kitchen` department.
- 3.5 Add `_MAINTENANCE_REPORTER` + `_HOTEL_INFO_READ` + `_GUESTS_READ` + `_BOOKING_READ` to `food_beverage` department.
- 3.6 Add `_CHAT_BASE` to `housekeeping`, `food_beverage`, `maintenance` departments. (Optional: kitchen — see §3.6 product call-out.)

Acceptance: Duty manager has hotel-wide read; GR agents can read+update guests and chat; F&B / kitchen / housekeeping / maintenance can file maintenance tickets and read hotel info.

### Phase 4 — Role preset coverage for currently-empty roles

- 4.1 Add explicit role presets for `duty_manager`, all three `guest_relations_*`, all three `kitchen_*`, `maintenance_staff`, `fb_supervisor`, `front_office_supervisor`, `housekeeper` (per §4.3).
- 4.2 Extend `front_office_manager` with `_ROOM_SERVICE_OPERATE` + `_MAINTENANCE_OPERATE`.
- 4.3 Extend each `*_manager` with `_CHAT_BASE` + `_HOTEL_INFO_READ` (so a manager always sees those modules regardless of department).
- 4.4 Add `CHAT_GUEST_RESPOND` to `hotel_manager` role preset.

Acceptance: every canonical role slug is present in `ROLE_PRESET_CAPABILITIES` (the test `assert set(CANONICAL_ROLE_SLUGS) == set(ROLE_PRESET_CAPABILITIES)` would pass).

### Phase 5 — Nav / preset consistency hardening

- 5.1 Implement `validate_nav_capability_consistency()` (§4.4 item 2).
- 5.2 Wire it into the same management-check path that calls `validate_preset_maps()` and `validate_module_policy()`.
- 5.3 Re-seed `Role.default_navigation_items` so each role's M2M is exactly the set `{ nav | MODULE_POLICY[nav].view_capability ∈ role_preset(role) ∪ tier(role) ∪ dept(role) }`. (One-shot data migration; not a code change to the resolver.)

Acceptance: no role can have a nav slug whose `module.view` capability is not granted by any of its preset sources.

### Phase 6 — Optional product calls

- 6.1 Decide on kitchen-on-guest-chat (§3.6).
- 6.2 Decide on `HOTEL_INFO_CATEGORY_MANAGE` policy: keep superuser-only (current) or grant to `hotel_manager` (§3.10 of visibility audit).
- 6.3 Decide whether `front_office_manager` should additionally hold `_ROOM_INVENTORY_*` write (currently kept on hotel\_manager only). Recommendation: **no** — preserves the destructive-authority boundary.

Each Phase 6 item is independent of all preceding phases.

---

## 7. Test Strategy (no test code changes; new tests only)

These should accompany the rollout but **are not part of this audit's output**:

1. **Persona snapshot tests.** For each canonical (role, department, tier) tuple, snapshot `rbac` payload and assert against an expected truth-table fixture derived from §5.
2. **No-empty-preset test.** `assert set(CANONICAL_ROLE_SLUGS) ⊆ ROLE_PRESET_CAPABILITIES.keys() ∪ {tier-only roles}`. Same for departments.
3. **View-vs-read coherence test.** For every preset bundle that grants any module's `view_capability`, assert it also grants the same module's `read_capability` (and vice versa), unless the bundle is documented as a routing-only / authority-only preset (e.g. `_SUPERVISOR_AUTHORITY` which adds moderation without visibility).
4. **Destructive-authority lock-in test.** For each capability in §5.1, assert it appears only in the sanctioned bundles.
5. **Nav-capability drift test.** Per §4.4 item 2.

---

## 8. Final Verdict

The audit and rebalance plan above keep every architectural invariant (capability-driven authority, fail-closed projection, no role-slug / tier / nav fallbacks) and rebalance **only** the three preset maps and one nav-default map.

**Net delta of the rebalance**:

| Surface | Files | Change shape |
| --- | --- | --- |
| `TIER_DEFAULT_CAPABILITIES` | `staff/capability_catalog.py` | No change. |
| `DEPARTMENT_PRESET_CAPABILITIES` | `staff/capability_catalog.py` | 5 existing entries gain capabilities; 3 currently-empty entries are populated. |
| `ROLE_PRESET_CAPABILITIES` | `staff/capability_catalog.py` | 8 currently-empty entries are populated; 5 existing entries gain capabilities; `hotel_manager` gains 1 capability. |
| New private bundle constants | `staff/capability_catalog.py` | `_ATTENDANCE_DEPARTMENT_HEAD_READ`, `_ATTENDANCE_DEPARTMENT_HEAD_WRITE`, `_GUEST_RELATIONS_OPERATE`, `_DUTY_MANAGER_READ`, `_FRONT_OFFICE_COORDINATION`, `_KITCHEN_OPERATE_EXTENDED`, `_FB_OPERATE_EXTENDED`. |
| `TIER_DEFAULT_NAVS` | `staff/permissions.py` | Trim or keep, plus optional new validator. |
| `module_policy.py` | (none) | Untouched. |
| `permissions.py` resolvers | (none) | Untouched. |
| Endpoint enforcement | (none) | Untouched. |
| Frontend `can()` / `useCan()` | (none) | Untouched. |
| Capability slugs | (none) | No additions, no renames, no removals. |

**Operational outcome**: every canonical persona ends up with a coherent, realistic capability footprint. The duty manager can coordinate. Guest relations can do guest relations. Department heads can supervise their own department's roster. Front office can run room service. Maintenance can see room context. F&B and kitchen can file tickets. The destructive / config / staff-management authority surface is unchanged.

This is the minimum-refactor path to "operationally realistic" without re-opening any of the security boundaries the current architecture carefully drew.
