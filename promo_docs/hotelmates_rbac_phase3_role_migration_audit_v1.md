# HotelMates RBAC Phase 3 — Role & Department Migration Audit

**Status:** Phase 3 — audit & mapping only. **No role creation. No schema change. No code change.**
**Depends on:**
- [hotelmates_auth_contract_v1.md](hotelmates_auth_contract_v1.md) (v1.1) — the authorization model
- [hotelmates_capability_catalog_v1.md](hotelmates_capability_catalog_v1.md) — the canonical capability slugs
**Purpose:** Inspect the real current state of `Role`, `Department`, `Staff.access_level`, and nav assignments in the database, and map every existing row to the target model so the eventual migration path is a data-shaped decision, not a greenfield rewrite.

---

## 0. Scope & method

This document:

- reads the **live database** (not theory, not seed files) for the authoritative list of today's roles / departments / access levels / nav assignments;
- reads the **code** for all hardcoded `role.slug` / `department.slug` / `access_level` checks that will constrain the migration;
- classifies every existing row into one of four migration verdicts: **keep**, **normalize**, **merge**, **deprecate**;
- proposes the target canonical department, target tier, target role slug, and default capability bundle for each preserved row.

This document does **not**:

- create, rename, or delete any `Role`, `Department`, or `Staff` row;
- modify any model, migration, serializer, or view;
- finalize the canonical department taxonomy or role preset catalog (that is Phase 4, driven by the decisions in this doc).

Data snapshot captured from production DB (`DATABASE_URL` configured in `HotelMateBackend/settings.py`) via `manage.py shell`. Date of snapshot: current.

---

## 1. Current-state snapshot

### 1.1 Hotels (3)

| id | slug | name |
|---|---|---|
| 156 | `no-way-hotel` | No Way Hotel |
| 199 | `armitrage` | Armitrage |
| 207 | `the-old-new` | The Old New |

### 1.2 Departments (2 rows, only on `no-way-hotel`)

| id | hotel | name | slug |
|---|---|---|---|
| 15 | `no-way-hotel` | Food and Beverage | `food-and-beverage` |
| 69 | `no-way-hotel` | Front Office | `front-office` |

**Observations:**
- `armitrage` and `the-old-new` have **zero** `Department` rows. Their staff and roles cannot be department-scoped at all today.
- Department slugs are **kebab-case** (`food-and-beverage`, `front-office`).
- The capability catalog uses **snake_case** canonical slugs (`food_beverage`, `front_office`). This is a normalization gap.

### 1.3 Roles (3 rows, all on `no-way-hotel`)

| id | hotel | name | slug | department | `default_navigation_items` | staff count |
|---|---|---|---|---|---|---|
| 93 | `no-way-hotel` | Waiter | `waiter` | `food-and-beverage` | ∅ | 1 |
| 136 | `no-way-hotel` | Manager | `manager` | `food-and-beverage` | ∅ | 2 |
| 167 | `no-way-hotel` | porter | `""` (empty) | `null` | ∅ | 1 |

**Observations:**
- Only **3 roles exist in total** across the whole platform. The role layer is effectively empty.
- **None** of the 3 roles has any `default_navigation_items` assigned. The M2M exists in the schema but carries no data. Today all staff nav access comes from per-staff overrides and tier defaults.
- Role #167 (`porter`) has an **empty `slug`**. This is a data-integrity defect — `Role.slug` is a `SlugField` but was stored as `""`. Any `role__slug` lookup for this row returns empty string.
- Role #167 has **no department** (`department_id IS NULL`). `porter` is a classic housekeeping / guest-services role in the catalog.
- Role name casing is inconsistent: `Waiter` (Title), `Manager` (Title), `porter` (lower). This is a display concern but reflects absence of a naming convention.

### 1.4 Staff rows — tier distribution

| `access_level` | count |
|---|---|
| `super_staff_admin` | 3 |
| `regular_staff` | 1 |
| `staff_admin` | 0 |

Plus Django superusers (not reflected on `Staff.access_level`, synthesized at resolve time from `user.is_superuser`).

**Observations:**
- The `staff_admin` tier is **unused** in real data. Every non-super admin is `super_staff_admin`. This is consistent with the current code habit of collapsing "admin tier" via the misleading `IsSuperUser` class that allows `staff_admin` and `super_staff_admin` together.
- The single `regular_staff` row is the `porter` on `no-way-hotel`.

### 1.5 Staff → role assignment

| hotel | role slug | count |
|---|---|---|
| `no-way-hotel` | `""` (empty — porter) | 1 |
| `no-way-hotel` | `manager` | 1 |
| `no-way-hotel` | `waiter` | 1 |
| `the-old-new` | `manager` | 1 |

**Critical finding — cross-tenant FK leak:**

One staff member on `the-old-new` holds `role_id = 136`, which is the `Manager` role that belongs to hotel `no-way-hotel`. Because `Role` has a hotel FK and `Staff.role` is a plain `ForeignKey(Role, on_delete=SET_NULL)` without a hotel-matching constraint, a role from one tenant has been assigned to a staff member of another tenant. This violates the hotel-scope invariant from the auth contract §3.4.

This must be resolved in the migration (detach and reassign, or null-out) before any capability bundle is computed from `staff.role`.

### 1.6 Navigation assignment today

- Canonical nav catalog (`staff/nav_catalog.py::CANONICAL_NAV_SLUGS`): 12 slugs — `home`, `chat`, `rooms`, `room_bookings`, `restaurant_bookings`, `housekeeping`, `maintenance`, `attendance`, `staff_management`, `room_services`, `hotel_info`, `admin_settings`.
- Nav visibility source today: **only** `Staff.allowed_navigation_items` (per-user M2M). No role defaults are populated.
- `Role.default_navigation_items` M2M **exists on the model but is empty for every role**.
- Seed command `staff/management/commands/seed_navigation_items.py` only creates `NavigationItem` rows per hotel; it does not touch roles.

---

## 2. Hardcoded constraints the migration must respect

The mapping below cannot invent arbitrary slugs because the live code still branches on specific `role.slug` / `department.slug` / `access_level` literals. Any renames must preserve or explicitly retire these.

| File | Literal | Meaning today |
|---|---|---|
| `chat/views.py:279` | `role__slug="receptionist"` | Target receptionists as notification recipients for guest chat. |
| `chat/views.py:864` | `role.slug in ['manager', 'admin']` | Chat moderation authority. |
| `staff_chat/permissions.py:12` | `role.slug in ('manager', 'admin')` | `is_chat_manager(staff)`. |
| `staff_chat/views_messages.py:482,491` | `role.slug in ['manager', 'admin']` | Hard-delete messages. |
| `staff_chat/views_attachments.py:285` | `role.slug in ['manager', 'admin']` | Delete attachments. |
| `housekeeping/policy.py:54` | `role.slug == 'housekeeping'` OR `department.slug == 'housekeeping'` | `is_housekeeping(staff)` branch used by room-status transition policy. |
| `notifications/notification_manager.py` | `role__slug='porter'` (3 occurrences), `role__slug='receptionist'` (2 occurrences) | Notification routing only — not an authorization gate. |

**Implication for the mapping:** The target role slugs we propose must keep `manager`, `porter`, `receptionist`, and `housekeeping` as **reserved semantic slugs** until every one of those code sites has been replaced with a capability check. Renaming `porter` → `bellhop` right now would silently break notification routing.

---

## 3. Target canonical taxonomy (reference, from the capability catalog)

Pulled from `hotelmates_capability_catalog_v1.md`. This is the target vocabulary the mapping in §4 and §5 is aiming at — we are **not inventing it here**.

### 3.1 Canonical departments (snake_case)

`front_office`, `guest_relations`, `housekeeping`, `maintenance`, `food_beverage`, `kitchen`, `administration`, `management`.

The catalog treats `*` (all departments) as a marker for cross-cutting capabilities (e.g. `maintenance.ticket.create`), not a real department row.

### 3.2 Canonical tiers

`regular_staff` < `staff_admin` < `super_staff_admin` < `super_user` (Django `is_superuser`).

### 3.3 Expected canonical role slugs per department (not yet seeded)

This is the **proposed target** role surface we expect Phase 4 to seed. It is listed here only so the §4 mapping has something stable to point at.

| Canonical department | Proposed preset role slugs |
|---|---|
| `front_office` | `front_office_manager`, `receptionist`, `night_auditor`, `porter` |
| `guest_relations` | `guest_relations_manager`, `guest_relations_agent` |
| `housekeeping` | `housekeeping_manager`, `housekeeping_supervisor`, `housekeeper` |
| `maintenance` | `maintenance_manager`, `maintenance_technician` |
| `food_beverage` | `fnb_manager`, `waiter`, `bartender` |
| `kitchen` | `head_chef`, `chef`, `kitchen_assistant` |
| `administration` | `hotel_admin`, `accountant` |
| `management` | `general_manager` |

Role slug rule (tightened here): `snake_case`, lowercase, stable, department-qualified where the role's scope is ambiguous across departments (`fnb_manager`, not bare `manager`).

---

## 4. Per-role migration mapping

For every **existing** `Role` row. One decision per row. No new rows are created in this document.

### 4.1 Role #93 — `Waiter` (`waiter`)

| Field | Current | Proposed |
|---|---|---|
| Name | `Waiter` | `Waiter` |
| Slug | `waiter` | `waiter` |
| Hotel scope | `no-way-hotel` | `no-way-hotel` |
| Department | `food-and-beverage` (kebab-case) | `food_beverage` (canonical) |
| `default_navigation_items` | ∅ | `home`, `chat`, `room_services` (preset) |
| Target tier | — (not yet enforced) | `regular_staff` |
| Target preset role slug | — | `waiter` |
| Default capability bundle | — | `room_services.order.read`, `room_services.order.create`, `room_services.order.update_status`, `room_services.menu.read`, `staff_chat.channel.read`, `staff_chat.message.send`, `attendance.self.clock`, `reports.dashboard.read` |

**Verdict: keep, normalize.** Slug already matches the target. Only the department FK needs to be re-pointed from `food-and-beverage` (kebab) to the canonical `food_beverage` row (once it exists). No rename, no merge.

### 4.2 Role #136 — `Manager` (`manager`)

This row is the most ambiguous in the catalog and is **not** safe to keep as-is.

| Field | Current | Proposed |
|---|---|---|
| Name | `Manager` | `F&B Manager` *(display)* |
| Slug | `manager` | `fnb_manager` |
| Hotel scope | `no-way-hotel` | `no-way-hotel` |
| Department | `food-and-beverage` | `food_beverage` |
| `default_navigation_items` | ∅ | `home`, `chat`, `rooms`, `room_services`, `hotel_info` |
| Target tier | — | `staff_admin` |
| Target preset role slug | — | `fnb_manager` |
| Default capability bundle | — | full `room_services.*` (read/create/update_status/reassign/comp/menu.read/menu.toggle_availability), `bookings.booking.read`, `rooms.room.read`, `staff_chat.*` (manager subset), `reports.department.read`, `attendance.self.clock` |

**Verdict: rename (normalize) + re-point department.**

Rationale:
- The bare slug `manager` is the **single most dangerous legacy string** in the codebase. It is hardcoded in `staff_chat/permissions.py`, `staff_chat/views_messages.py`, `staff_chat/views_attachments.py`, and `chat/views.py` as a generic "this user can moderate chat" flag. Keeping `slug='manager'` on a concrete F&B role means that any future `housekeeping_manager` or `front_office_manager` either (a) also has to use slug `manager` — breaking uniqueness within a department — or (b) loses chat-moderation power that the code currently grants via the literal string.
- The correct fix is to migrate `manager` → `fnb_manager` on this row **and** replace every `role.slug in ['manager', 'admin']` check with a capability check (`staff_chat.message.delete_any`, etc.) in Phase 5. Until that capability replacement ships, the legacy slug `manager` must be treated as a reserved alias (see §7).

### 4.3 Role #167 — `porter` (slug `""`)

| Field | Current | Proposed |
|---|---|---|
| Name | `porter` | `Porter` *(display, Title Case)* |
| Slug | `""` (EMPTY — integrity defect) | `porter` |
| Hotel scope | `no-way-hotel` | `no-way-hotel` |
| Department | `null` | `front_office` |
| `default_navigation_items` | ∅ | `home`, `chat`, `rooms`, `housekeeping` |
| Target tier | — | `regular_staff` |
| Target preset role slug | — | `porter` |
| Default capability bundle | — | `rooms.room.read`, `housekeeping.task.read`, `housekeeping.task.update_status`, `maintenance.ticket.create`, `staff_chat.channel.read`, `staff_chat.message.send`, `attendance.self.clock` |

**Verdict: keep (semantic) + repair.** The role itself is valid and the slug `porter` is a reserved literal used by `notifications/notification_manager.py` for push targeting — it **must not** be renamed.

Two repairs required:
1. Fix the empty-slug defect: set `slug = 'porter'`. Enforce a `CheckConstraint` or form-level `MinLengthValidator(1)` so `Role.slug == ""` is impossible going forward (tracked for Phase 4; out of scope for this audit).
2. Assign a canonical department. The catalog places `porter`-equivalent operational capabilities under `front_office` (bag service, room escort) with a secondary `housekeeping` overlap. Attach the FK to the `front_office` department once that row exists for this hotel.

### 4.4 Staff row referencing a cross-tenant role

One staff on `the-old-new` points to `role_id=136` (`Manager` on `no-way-hotel`). This is **not a role to migrate** — it is a **staff-row integrity defect** surfaced by the role audit.

**Verdict: unassign and re-issue.**
- During Phase 4 migration: set `staff.role_id = NULL` for this row, then re-assign once `the-old-new` has its own seeded role set.
- Document this in the migration script so the intent is preserved (this staff member currently acts as "manager" authority on that hotel).

---

## 5. Per-department migration mapping

### 5.1 Department #15 — `Food and Beverage` (`food-and-beverage`)

| Field | Current | Proposed |
|---|---|---|
| Name | `Food and Beverage` | `Food & Beverage` |
| Slug | `food-and-beverage` (kebab) | `food_beverage` (canonical snake_case) |
| Hotel | `no-way-hotel` | `no-way-hotel` |

**Verdict: keep, normalize slug.** Slug migration is a simple `UPDATE`. No FK re-pointing needed — the `Role → Department` FK is by `id`, not slug.

### 5.2 Department #69 — `Front Office` (`front-office`)

| Field | Current | Proposed |
|---|---|---|
| Name | `Front Office` | `Front Office` |
| Slug | `front-office` (kebab) | `front_office` (canonical snake_case) |
| Hotel | `no-way-hotel` | `no-way-hotel` |

**Verdict: keep, normalize slug.**

### 5.3 Departments missing on `armitrage` and `the-old-new`

Neither hotel has any `Department` row. The migration will need a **per-hotel canonical department seeder** (deferred to Phase 4) that creates the 8 canonical departments for every hotel, matching what should have happened in `hotel/signals.py` / `hotel/provisioning.py` but never did.

**Verdict: create in Phase 4 (out of scope here).** Not an audit finding about existing data, but a migration prerequisite that follows from this audit.

---

## 6. Tier (`access_level`) audit

| Canonical tier | Current usage | Verdict |
|---|---|---|
| `super_user` | Synthesized from `User.is_superuser`. Unchanged. | Keep as-is. |
| `super_staff_admin` | 3 staff. The de-facto "admin". | Keep. |
| `staff_admin` | **0 staff.** Declared in `ACCESS_LEVEL_CHOICES` but no row holds this value. | Keep the enum value. Do not delete it. It is required by the contract's 4-tier hierarchy (regular / staff_admin / super_staff_admin / super_user) and by the catalog's min-tier invariants for `management`-class capabilities. |
| `regular_staff` | 1 staff (the porter). | Keep. |

**No tier enum change is needed or proposed.** The migration path is purely: populate the currently-empty `staff_admin` tier by assigning it to mid-level managers (e.g. the F&B Manager role's future staff) during Phase 4.

---

## 7. Legacy-slug reservation table

Because the code still matches on these literals, the migration must treat them as reserved across the entire transition window. They cannot be deleted or repurposed until every listed callsite has switched to capability checks.

| Reserved literal | Kind | Held by (today) | Blocking code | Release condition |
|---|---|---|---|---|
| `'manager'` | role slug | Role #136 | `staff_chat/permissions.py`, `staff_chat/views_messages.py`, `staff_chat/views_attachments.py`, `chat/views.py` | All 4 callsites migrated to capability checks (`staff_chat.message.delete_any`, `guest_chat.message.delete`, etc.). |
| `'admin'` | role slug | *(no current row)* | Same 4 callsites as above — it is half of the `['manager','admin']` disjunction. | Same as above. |
| `'housekeeping'` | role slug AND department slug | *(no current role row; no current dept row with that slug — nearest is `front-office`)* | `housekeeping/policy.py::is_housekeeping()` | Capability check `housekeeping.task.update_status` replaces the branch. |
| `'receptionist'` | role slug | *(no current row)* | `chat/views.py:279`, `notifications/notification_manager.py` (2x) | Replaced by capability targeting (`guest_chat.thread.read` subscribers) + notification preference layer. |
| `'porter'` | role slug | Role #167 | `notifications/notification_manager.py` (3x) | Replaced by notification preference layer (not a security gate, but a routing gate — still blocks rename). |

**Rule for Phase 4 seeders:** never create a role with one of these slugs on a NEW row for a NEW purpose. Reuse only the existing defective rows or wait until the literal is released.

---

## 8. Summary verdict table

| Entity | Current identity | Verdict | Target identity | Blocker? |
|---|---|---|---|---|
| Dept #15 | `food-and-beverage` / `no-way-hotel` | Keep, normalize slug | `food_beverage` / `no-way-hotel` | No |
| Dept #69 | `front-office` / `no-way-hotel` | Keep, normalize slug | `front_office` / `no-way-hotel` | No |
| Role #93 | `waiter` / F&B / `no-way-hotel` | Keep, re-point department | `waiter` / `food_beverage` / `no-way-hotel` | No |
| Role #136 | `manager` / F&B / `no-way-hotel` | Rename (normalize) | `fnb_manager` / `food_beverage` / `no-way-hotel` | **Yes** — legacy `'manager'` literal reserved until 4 chat callsites migrated to capabilities. |
| Role #167 | `porter` / slug=`""` / dept=null / `no-way-hotel` | Keep, repair slug, assign dept | `porter` / `front_office` / `no-way-hotel` | **Yes** — notification manager targets `role__slug='porter'`. Slug rename of this row is forbidden; only repair is to set the empty slug to `'porter'`. |
| Staff on `the-old-new` → Role #136 | Cross-tenant leak | Unassign (`role=NULL`), reassign after tenant gets its own role set | — | Data-integrity issue. |
| Hotels `armitrage`, `the-old-new` | No departments, no roles | Create canonical department set in Phase 4 | 8 canonical departments per hotel | No (deferred). |
| Tier `staff_admin` | Declared, unused | Keep; populate during Phase 4 role assignment | — | No |
| `Role.default_navigation_items` | Empty on every row | Populate during Phase 4 preset seeding | Per-role preset nav list | No |

Totals: **3 roles total, 2 departments total, 4 staff rows total, 1 cross-tenant FK leak, 1 empty-slug defect, 2 slug normalizations, 5 reserved legacy literals, 0 roles deprecated, 0 roles merged, 0 roles to create in this phase.**

---

## 9. Open questions (require a decision before Phase 4 starts)

1. **`fnb_manager` rename timing.** Do we rename Role #136's slug in the same migration that introduces capability checks for chat moderation, or do we ship capability checks first, let `'manager'` stop being a security literal, and only then rename? Recommendation: the latter — rename is the **last** step, after the literal is fully dead.
2. **`the-old-new` staff reassignment.** When we null-out `staff.role` for the cross-tenant leak, does that staff keep their current `access_level='super_staff_admin'` tier in the interim, or do we freeze their account pending reassignment? Recommendation: keep the tier — tier is the security floor, role is a preset; losing the role only strips future capability presets, not existing authority.
3. **Canonical department seeding.** Should the Phase 4 seeder create all 8 canonical departments for every hotel, or only the ones the hotel actually staffs? Recommendation: create all 8. Cost is ~24 rows across 3 hotels; benefit is a stable lookup for capability bundles regardless of staffing state.
4. **Legacy slug aliasing.** For the reserved literals in §7, do we add a temporary `Role.legacy_slug` alias field, or do we just freeze the slug on the existing row until the literal is retired? Recommendation: freeze the row — no schema change — and track the release in this document.
5. **Empty-slug defect enforcement.** Should `Role.slug` gain a DB-level `CheckConstraint(length(slug) > 0)` as part of the repair, or is model-level `validators=[MinLengthValidator(1)]` sufficient? Recommendation: DB constraint. The Role #167 case proved the ORM layer does not prevent it.

---

## 10. What Phase 4 will do (preview, not part of this audit)

This audit does not implement anything. Its output is the input to Phase 4, which will:

1. **Normalize department slugs** on `no-way-hotel`: `food-and-beverage` → `food_beverage`, `front-office` → `front_office`.
2. **Seed the 8 canonical departments** for every hotel (deferred to a dedicated management command, guided by §3.1 and §5.3).
3. **Repair Role #167** (`porter`): set `slug='porter'`, set `department=front_office` on `no-way-hotel`.
4. **Re-point Role #93** (`waiter`) department FK to the new canonical `food_beverage` row on `no-way-hotel`.
5. **Null-out** the cross-tenant `staff.role` reference on `the-old-new` (§4.4).
6. **Introduce the canonical role preset catalog** per §3.3 (seed per hotel, not in this audit).
7. **Populate `Role.default_navigation_items`** for each preset role per §4.
8. **Keep `Role #136` (`manager`) unchanged** until all 5 reserved legacy literals (§7) are retired by capability replacement in Phase 5. Only then rename to `fnb_manager`.

No role is deprecated in Phase 4. No role is merged in Phase 4. Every existing row survives migration with either no change, a slug repair, or a department re-point. That is the point of having done this audit.

---

*End of Phase 3 audit. Awaiting decisions on §9 open questions before Phase 4 implementation begins.*
