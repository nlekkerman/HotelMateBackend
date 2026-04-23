# HotelMates Backend Authorization Contract v1.1

**Status:** Architecture contract — Phase 1 lock (v1.1 tightened)
**Scope:** Backend authentication & authorization model for all staff-facing operations
**Author intent:** Source-of-truth document. Implementation tasks must conform to this contract without re-deciding core definitions.

**v1.1 changes over v1:**
- Locked the relationship between `allowed_navs` and capabilities (separate resolved surface, backend-generated).
- Locked tier → default capability bundle behavior (tier grants baseline bundles; runtime still checks the resolved capability list).
- Locked department reach per tier with hard rules (regular/staff_admin/super_staff_admin/super_user).
- Added the single-primary-capability rule for non-safe endpoints.
- Locked the capability naming convention: `domain.resource.action`.

---

## 1. Purpose of this contract

HotelMates has outgrown its current permission model. Authorization decisions are currently spread across role-name checks, navigation slugs, ad-hoc tier comparisons, and scattered per-view logic. The result is:

- The same permission question gets answered differently in different places.
- Adding a new role forces code changes across backend views and frontend guards.
- "Can this user do X?" has no single authoritative answer.
- Frontend and backend disagree on what a user is allowed to do.
- Navigation access is being (mis)used as if it were action authorization.

This contract exists to end that drift **before** any refactor begins. The target model is **capability-first**: every protected action maps to a named capability, and role/tier/department exist to organize and grant those capabilities — not to replace them.

Why capability-first:

- Actions are stable; role names are not.
- Capabilities are enumerable, auditable, and testable.
- Backend and frontend can agree on a single permission vocabulary.
- Adding a new role becomes a data change, not a code change.

This contract must exist before implementation because once capability checks are wired into endpoints, their meaning must already be settled. Otherwise we rebuild the same mess with new vocabulary.

---

## 2. Final authorization model overview

The final model has six distinct concepts. Each has a single, non-overlapping job.

| Concept | Role in the system | Layer |
|---|---|---|
| **Tier** | Broad authority envelope (regular staff → super user) | Security core (coarse) |
| **Capability** | Exact, named action permission | Security core (fine) — **final backend check** |
| **Department** | Operational grouping of staff and presets | Organizational structure |
| **Role** | Human-readable title + preset capability bundle | Display / preset layer |
| **Hotel scope** | Mandatory tenant boundary | Security core (mandatory) |
| **Navigation / module visibility** | Which modules/pages a user can see | Derived frontend surface |

Plain-English definitions:

- **Tier** — How much authority this account carries in general. A `super_staff_admin` can do things a `regular_staff` cannot, regardless of department. Tier answers: *"How powerful is this account?"*
- **Capability** — A named permission like `room_service.menu.create` or `housekeeping.task.reassign`. Capability answers: *"Is this specific action allowed?"*
- **Department** — Which operational unit the staff member belongs to (e.g. `housekeeping`, `kitchen`). Department answers: *"Where in the hotel does this person work?"*
- **Role** — A labeled preset like `Waiter`, `Porter`, `Chef de Partie`. A role belongs to a department and carries a default capability bundle. Role answers: *"What is this person's job title?"*
- **Hotel scope** — The hotel this account is bound to. Every staff action must be scoped to the acting user's hotel. Hotel scope answers: *"Whose data can this account touch?"*
- **Navigation / module visibility** — Which modules appear in the UI. Answers: *"What pages should I render?"* — and nothing more.

Classification:

- **Security core (enforced):** Tier, Capability, Hotel scope.
- **Organizational structure:** Department.
- **Display / preset layer:** Role.
- **Derived frontend surface:** Navigation / module visibility.

---

## 3. Canonical decision rules

These read as architectural laws. They are not suggestions.

1. **Tier is not the same as capability.** Tier bounds authority; capabilities grant actions. Two users at the same tier may have different capability sets.
2. **Role is not the enforcement source.** No backend check may read `role.name == "Waiter"` or equivalent. Roles only exist to carry preset capability bundles and to display a title.
3. **Department is not the final permission key.** Department narrows *context* (e.g. "only housekeeping staff see housekeeping tasks"), but permission to *act* comes from capabilities.
4. **Capability is the final action-level permission source.** Every write/action endpoint must map to one or more capabilities and enforce them.
5. **Hotel scoping is mandatory on all staff operations.** Every staff query, mutation, and retrieval must be constrained to the acting user's hotel. Cross-hotel access is only available to `super_user` and only via explicit, audited pathways.
6. **Navigation visibility is not sufficient authorization.** Being able to see a module never implies permission to perform actions in it. The backend must re-verify capability on every action, regardless of whether the UI exposed it.
7. **Frontend consumes permission truth; it does not invent it.** The backend emits the effective-access payload. The frontend may only hide/show/disable based on that payload. Any frontend-only permission rule is a bug.
8. **A denied capability on the backend must not be overridable by a visible nav entry.** Nav and capability are separate surfaces.
9. **Legacy role-name branches are prohibited in the target model.** Migration may tolerate them temporarily; the destination state does not.
10. **Single source of truth.** There is exactly one effective-access resolver. Views, serializers, and the frontend consume its output. They do not re-derive permission from raw role/department fields.
11. **Tier grants baseline capability bundles; it does not bypass capability checks.** The resolver layers tier baseline + role preset + per-user adjustments into a single `allowed_capabilities` list. Runtime checks read only that resolved list.
12. **`allowed_navs` is a separately resolved backend surface**, generated by backend rules (not hand-managed, not frontend-derived, not a projection of capabilities). See §9.
13. **Tier reach is fixed.** `regular_staff` = own domain, `staff_admin` = department-wide, `super_staff_admin` = hotel-wide, `super_user` = platform-wide. No ambient broadening.
14. **Single primary capability per non-safe endpoint.** Every mutating/non-safe staff endpoint declares exactly one canonical primary capability. Additional guards (tier minimum, department scope, secondary capabilities) may layer on.
15. **Capabilities follow `domain.resource.action` naming.** No other formats are valid. See §5.

---

## 4. What Tier decides

Tier is the **authority envelope**. It is coarse-grained and answers "how high up the ladder is this account?"

Tier governs:

- **Authority breadth** — how far across the hotel the account's actions can reach (own scope vs. department vs. hotel-wide).
- **Escalation rights** — ability to override, reassign, or approve on behalf of others.
- **Supervision / admin level** — ability to manage other staff accounts, shifts, schedules.
- **Access to sensitive management / configuration areas** — settings, billing, policies, integrations.
- **Eligibility for dangerous capabilities** — certain capabilities (delete, refund, reassign hotel-wide, modify permissions) are only grantable at or above a minimum tier.
- **Cross-department or hotel-wide management power** — only `staff_admin` and above may act outside their own department. Only `super_user` may act outside their own hotel.

Target tiers and their **locked reach**:

| Tier | Reach | Meaning |
|---|---|---|
| `regular_staff` | **Own domain / assigned work** | Normal operational staff. Acts only on their own tasks, shift, assigned resources. |
| `staff_admin` | **Department-wide (within hotel)** | Supervises one department. May act across all staff and resources of their department. Not hotel-wide. |
| `super_staff_admin` | **Hotel-wide** | Full authority within one hotel. Cross-department. Manages hotel staff, settings, configuration. |
| `super_user` | **Platform-wide** | Cross-hotel, system administration. Not a day-to-day operational account. |

These reach definitions are hard rules, not defaults. A `staff_admin` is a department-admin — never ambient hotel-wide authority. Cross-department reach requires `super_staff_admin` or above. Cross-hotel reach requires `super_user`.

### Tier and default capability bundles

Tier **does** grant a baseline default capability bundle. This is how the system stays sane without manually assigning every capability to every user:

- Each tier carries a **default baseline bundle** appropriate to its reach (e.g. `staff_admin` gets baseline department-management capabilities).
- Each role carries a **role preset bundle** layered on top of the tier baseline.
- Per-user grants/revocations may further adjust the resolved set.
- **The runtime check is always against the final resolved `allowed_capabilities` list** — never against the tier directly.

In other words: tier *contributes* capabilities via the resolver; it does not *bypass* capability checks. A capability absent from the resolved list is denied, regardless of tier.

Tier does **not** decide:

- Which specific endpoints a user may call — capabilities do that.
- Which department context a user belongs to — department does that.
- Which UI modules appear — nav visibility does that (resolved separately, see §9).
- Whether a specific button is enabled — capability does that.

A high tier never bypasses a missing capability in routine checks. Tier unlocks *eligibility* for sensitive capabilities and *contributes* baseline bundles via the resolver; the capability itself must still be present in the resolved list at runtime.

---

## 5. What Capability decides

Capability is the **final backend action check**. Every protected operation must gate on a capability.

Capability governs:

- **Exact CRUD / action rights** — `resource.action` granularity (e.g. `room_service.order.update_status`, `housekeeping.task.create`).
- **Exact endpoint authorization** — each protected view resolves to a required capability (or set).
- **Exact button / form / section visibility on the frontend** — the UI enables controls strictly based on the capability list in the effective-access payload.
- **Exact operational behavior per module** — e.g. within the same room service page, one user may only update order status while another may also create menu items.

Rules:

- **Capability is the last word on "may this action proceed?"** Tier, role, and department may have gated *how* the capability was granted, but the runtime check is the capability.
- **Capabilities are named, enumerated, and versioned.** They live in a canonical catalog (to be produced in follow-up work) and are never free-form strings scattered across views.
- **Capabilities are hotel-scoped implicitly.** A capability grants an action within the user's hotel; it never implies cross-hotel reach.
- **Every action endpoint declares its required capability explicitly.** No implicit inheritance from "the user is staff" or "the user sees this module."
- **Every non-safe staff endpoint must declare exactly one canonical primary capability**, even if additional tier or scope checks apply. Secondary capabilities, tier minimums, or department guards may layer on top, but there is always one — and only one — primary capability that answers "which action is this?" Safe (idempotent read) endpoints may share a view-level capability or omit the primary when access is coarsely tier-gated by design.

### Capability naming convention

Capabilities use a **three-segment, lowercase, dot-separated** format:

```
domain.resource.action
```

- `domain` — the module/bounded context (e.g. `room_service`, `housekeeping`, `staff`, `bookings`).
- `resource` — the entity being acted on (e.g. `order`, `menu`, `task`, `account`).
- `action` — the verb or fine-grained operation (e.g. `read`, `create`, `update`, `update_status`, `assign`, `delete`).

Examples:

- `room_service.order.read`
- `room_service.order.update_status`
- `room_service.menu.create`
- `housekeeping.task.assign`
- `staff.account.update`

Rules:

- Lowercase, `snake_case` segments, dots between segments. No camelCase, no hyphens, no four-segment variants.
- Exactly three segments. If you reach for a fourth segment, the resource or action is wrong.
- Actions are verbs or verb phrases (`read`, `create`, `update`, `update_status`, `reassign`, `delete`). Never nouns.
- Names are stable. Renaming a capability is a migration, not a refactor.
- The canonical catalog (Phase 2) is the only source of truth for valid names. Free-form strings in views are prohibited.

---

## 6. What Department means

Department is an **operational grouping**. It organizes staff by functional area.

Canonical departments:

- `front_office`
- `housekeeping`
- `food_beverage` — guest-facing FOH / service side (waiters, bar, restaurant floor)
- `kitchen` — BOH / preparation / production side (chefs, line cooks, kitchen porters)
- `maintenance`
- `guest_relations`
- `management`
- `administration`

The `food_beverage` vs `kitchen` split is intentional. They share a domain but have different workflows, tools, and permission surfaces:

- `food_beverage` sees guest orders, table state, billing handoff.
- `kitchen` sees ticket queue, prep state, stock consumption.
- A Chef should not inherit FOH capabilities by default, and a Waiter should not inherit kitchen prep capabilities.

Department is used to:

- Group staff for scheduling, reporting, and rostering.
- Anchor role presets (a role belongs to a department; its preset capabilities reflect that department's work).
- Filter context (a housekeeping staff member sees housekeeping tasks by default).
- Drive default module visibility.

Department does **not**:

- Authorize actions on its own. Being in `food_beverage` does not grant `room_service.menu.create`; only a capability does.
- Replace capability checks in views.
- Serve as a shortcut for permission logic (`if user.department == "kitchen"` is prohibited as an authorization rule).

---

## 7. What Role means

Role is a **human-readable preset**. It is a label with an attached capability bundle.

A role has:

- A **normalized slug** (e.g. `waiter`, `head_chef`, `front_desk_agent`) — stable, lowercase, underscore-separated. This is the machine identifier.
- A **display name** (e.g. "Waiter", "Head Chef") — shown in UI.
- An **associated department** — every role belongs to exactly one canonical department.
- A **mapped preset of capabilities** — the default capability bundle assigned when this role is applied.
- An **implied tier** or **tier compatibility** — e.g. "Head Chef" is typically `staff_admin` within `kitchen`.

Rules for roles in the final model:

- **Roles are never used directly in permission checks.** No `role.name == ...` or `role.slug == ...` in authorization code.
- **Assigning a role applies its preset capabilities** to the staff account (as data), but the account's effective capabilities are the authoritative list going forward. A role change updates the capability set; runtime checks read capabilities, not the role.
- **Roles can be customized per staff member.** A Waiter at one property may have an extra capability granted on top of the Waiter preset. The role label does not change; the capability list does.
- **Role is a display and onboarding convenience.** It makes the admin UI humane. It is not a security primitive.

---

## 8. Final enforcement model

Every protected staff endpoint must enforce this check order:

1. **Authenticated user** — request carries a valid session/token.
2. **Valid staff identity** — the account is a staff account (not guest, not anonymous) and is active.
3. **Same hotel scope** — the target resource belongs to the acting user's hotel. Cross-hotel is rejected unless the caller is `super_user` on an explicit cross-hotel pathway.
4. **Module visibility (when relevant)** — if the endpoint belongs to a module, the user must have visibility to that module. This is a sanity gate, not a substitute for capability.
5. **Required capability** — the specific capability for this action is present on the user's effective-access payload.
6. **Required minimum tier (for sensitive actions)** — where the capability is classified as dangerous/management/config, the user's tier must meet the declared minimum.

Why this order:

- **Cheap checks first, expensive checks last.** Auth and identity are local; capability and tier resolution may hit cache/DB.
- **Tenant isolation before anything else.** A request that touches the wrong hotel must fail before any capability is consulted — capability presence does not cross hotel boundaries.
- **Module visibility before capability** — allows early rejection for users completely outside the module's domain, and keeps the capability layer focused on action-grained decisions.
- **Capability before tier** — capability is the action-level truth. Tier acts as an additional guard for sensitive actions, layered on top; it is never the primary gate.

All six steps are enforced on the backend. The frontend mirrors steps 4–6 for UX only.

---

## 9. Module visibility vs action authority

Module visibility and capability are two different surfaces and must stay separate.

- **Module visibility** answers: *"Should this page appear in the user's navigation?"* It is coarse. Multiple unrelated users may share access to the same module.
- **Capability** answers: *"May this user perform this specific action?"* It is fine-grained. Users who share a module may have very different capability sets inside it.

### Locked rule: how `allowed_navs` is produced

`allowed_navs` is a **separate resolved surface**, not a derived projection of `allowed_capabilities`, and not a hand-managed security field.

Concretely:

- The backend resolver produces `allowed_navs` using **backend rules** that take tier, department, role, and (optionally) capability signals as inputs.
- `allowed_navs` is **not** computed by the frontend. The frontend consumes it verbatim.
- `allowed_navs` is **not** treated as action authority. It is a UX routing surface plus a coarse backend sanity gate (step 4 in §8).
- A capability present in `allowed_capabilities` without the corresponding module in `allowed_navs` is still enforceable at the endpoint — missing nav does not remove capability authority; it only hides the UI entry point.
- A module present in `allowed_navs` without any matching capabilities means the user can open a read-only/empty page but cannot act. That is valid and expected.
- Nav rules live in code/config on the backend. They are **not** edited per-user as a security primitive. Customizing a user's reach means adjusting capabilities or role, not hand-editing their nav list.

Concrete example — **Room Service module**:

All of the following users may have the room service module visible:

- A **Waiter** (front-of-house, `food_beverage`) — needs to see active orders, mark them delivered, take new orders from a table.
- A **Kitchen line cook** (`kitchen`) — needs to see the ticket queue, mark items as ready.
- A **Restaurant Manager** (`food_beverage`, `staff_admin`) — needs everything above plus menu management, pricing, availability toggles.
- A **Hotel Manager** (`management`, `super_staff_admin`) — needs full configuration, reporting, and audit access.

Inside that single module, capabilities differ sharply:

| Capability | Waiter | Line cook | Restaurant Mgr | Hotel Mgr |
|---|---|---|---|---|
| `room_service.order.view` | ✓ | ✓ | ✓ | ✓ |
| `room_service.order.create` | ✓ | — | ✓ | ✓ |
| `room_service.order.update_status` | ✓ | ✓ | ✓ | ✓ |
| `room_service.menu.view` | ✓ | ✓ | ✓ | ✓ |
| `room_service.menu.create` | — | — | ✓ | ✓ |
| `room_service.menu.update_price` | — | — | ✓ | ✓ |
| `room_service.settings.manage` | — | — | — | ✓ |

The module being visible never implies any of these capabilities. The backend must check the specific capability for every action, regardless of whether the user arrived via a visible menu item.

**Rule:** Visibility is UX routing. Capability is authorization. Never collapse the two.

---

## 10. Canonical backend payload contract

The backend exposes the user's effective access via a single resolver endpoint (conceptually `/auth/effective-access` or equivalent). The payload is the single source of truth consumed by the frontend and by server-side checks that need to emit UI hints.

Minimum payload shape:

```json
{
  "hotel_slug": "string",
  "tier": "regular_staff | staff_admin | super_staff_admin | super_user",
  "department_slug": "front_office | housekeeping | food_beverage | kitchen | maintenance | guest_relations | management | administration",
  "role_slug": "string",
  "role_display_name": "string",
  "allowed_capabilities": ["resource.action", "..."],
  "allowed_navs": ["module_slug", "..."]
}
```

Field meanings and trust levels:

| Field | Meaning | Enforcement or UI? |
|---|---|---|
| `hotel_slug` | The hotel this account is bound to. | **Enforcement** — all requests are scoped to this hotel. |
| `tier` | Authority envelope. | **Enforcement** — gates sensitive actions and cross-department reach. |
| `department_slug` | Operational grouping. | **Enforcement for context filtering**; never used as standalone action authority. |
| `role_slug` | Normalized role identifier. | **Display / audit only.** Never used in authorization checks. |
| `role_display_name` | Human-readable label. | **UI only.** |
| `allowed_capabilities` | The user's full, resolved capability list. | **Enforcement** — the definitive action-authority list. Also drives UI enable/disable. |
| `allowed_navs` | Modules the user may see. | **UI routing.** Backend also uses it as the module-visibility gate (step 4 in §8). Does not imply any capability. |

Additional rules:

- The payload is **resolved server-side**. The frontend never computes it.
- `allowed_capabilities` is the **authoritative** list. If a capability is not in it, the action is not permitted, regardless of role, department, or nav.
- The payload is **hotel-specific**. Switching hotel context (for `super_user`) produces a new payload.
- Clients must treat the payload as **opaque truth**: hide UI for missing capabilities, never fabricate capabilities, never infer capabilities from role slugs.

---

## 11. No-legacy policy

The target state is single-truth. The following patterns must be removed from the final implementation:

- **Raw role-name permission logic** — any branch of the form `if role.name == "X"`, `if user.role.slug == "Y"`, or string-matching role display names to decide authorization.
- **Frontend permission logic based on role display names** — the UI must not switch behavior on "Waiter" vs "Porter" as strings. It switches on capabilities.
- **Nav slugs acting as the only security truth** — no endpoint may accept a request solely because the user can see the module. Capability check is required.
- **Duplicate permission paths** — one capability, one check site per action. No "permission class A rejects it but middleware B allows it."
- **Stale fallback systems kept indefinitely** — temporary compatibility shims during migration are acceptable; they must carry a removal plan and a deprecation timestamp.
- **Per-view inline permission logic** that bypasses the capability catalog.
- **Implicit `super_user` bypasses scattered across views** — any bypass must go through the declared enforcement order.

Migration may be phased. The destination must be single-truth, no-legacy, capability-first. A phased migration is not an excuse to leave legacy branches in the final code.

---

## 12. What stays from the current backend

Concepts worth preserving conceptually (not necessarily their current code):

- **Tier / access-level concept.** The idea of a broad authority envelope is correct and survives. Only its meaning is being sharpened (see §4).
- **Hotel scoping.** Tenant isolation is already treated seriously in parts of the system. This stays and becomes universally enforced at the framework level.
- **Effective-access resolver concept.** The idea of a single place that computes "what can this user do right now?" is the right direction. It becomes the authoritative capability resolver (see §10).
- **Module visibility as a separate surface.** Keeping nav/module visibility as its own concept is correct. It just stops being the security core and returns to being UX routing + a coarse sanity gate.

This section does not audit specific code. It states which *ideas* carry into the new model.

---

## 13. What changes in the new backend

The architectural shifts are:

- **Action authority moves to capabilities.** The backend's final check on every protected action is a capability check, backed by a canonical catalog.
- **Departments become first-class organizational structure.** They are modeled explicitly with canonical slugs, anchor role presets, and drive context filtering — but never stand in for capabilities.
- **Roles become presets and labels.** A role is a department-bound bundle of capabilities plus a display name. It is not consulted at runtime for authorization.
- **Navigation stops being the security core.** Nav is demoted to UX routing + a coarse visibility gate. It is no longer synonymous with "allowed to act."
- **Frontend becomes a consumer of backend permission truth.** The UI hides, shows, enables, and disables based on `allowed_capabilities` and `allowed_navs` from the server. It does not compute permissions locally.
- **Tier is formalized.** The four-tier ladder (`regular_staff`, `staff_admin`, `super_staff_admin`, `super_user`) becomes the single authority envelope, with a clear definition of what it gates (see §4).
- **Single effective-access resolver.** One server-side function produces the payload in §10. All checks and all UI hints derive from it.

---

## 14. Open follow-up work after this contract

These items are **not** part of this task. They are the implementation design steps that follow once this contract is locked:

1. **Create the canonical capability catalog** — enumerate every capability with stable names, descriptions, and classifications.
2. **Group capabilities by module** — align capabilities with existing and planned modules (room service, housekeeping, maintenance, etc.).
3. **Classify capabilities into operational / management / config** — mark which require elevated tier.
4. **Define role presets per department** — for each canonical department, produce the default role set and each role's capability bundle.
5. **Design the capability model / storage** — DB schema, caching strategy, invalidation, assignment model (role-derived vs per-user overrides).
6. **Extend the effective-access resolver** — produce the §10 payload, with hotel-scoped resolution and cache semantics.
7. **Refactor permission classes** — replace role/tier-name checks with capability and tier-envelope checks; declare required capabilities per endpoint.
8. **Clean up legacy paths** — remove role-name branches, duplicate permission logic, and nav-as-security shortcuts per §11.
9. **Align frontend contract** — consume `allowed_capabilities` and `allowed_navs` as the only sources of permission truth in the UI.

---

## 15. Final summary

> **Build permissions around capabilities, use tier as authority envelope, use departments for structure, and reduce roles to clean presets — then remove every legacy path that contradicts that model.**

Capabilities are the final backend check. Tier bounds how far an account can reach. Departments organize people and anchor presets. Roles are human labels that apply preset capability bundles. Hotel scope is always enforced. Navigation is UX, not security. The frontend consumes; it does not invent.

This is the contract. Implementation follows.
