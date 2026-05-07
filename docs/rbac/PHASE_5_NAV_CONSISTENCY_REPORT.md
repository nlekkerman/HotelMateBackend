# RBAC Phase 5 — Nav Consistency + Validator Hardening Report

## 1. Files modified

| File | Change |
| --- | --- |
| [staff/nav_catalog.py](staff/nav_catalog.py) | Added `NAV_TO_MODULE_SLUG` projection map and `MODULES_WITHOUT_NAV` set. |
| [staff/capability_catalog.py](staff/capability_catalog.py) | Added `validate_nav_capability_consistency()` and `validate_visibility_read_coherence()` diagnostic validators. |
| [hotel/tests/test_rbac_nav_consistency.py](hotel/tests/test_rbac_nav_consistency.py) | New test module pinning the four validators (preset maps, module policy, nav drift, view/read coherence) and a DB-aware orphan check on `Role.default_navigation_items`. |

No changes to `module_policy.py`, `permissions.py` resolvers, capability slugs, role/department presets, endpoint enforcement classes, or the frontend.

## 2. Validators added

### `validate_nav_capability_consistency(role_default_navs=None)`

Pure data-only validator. Returns drift findings as a list of strings.

Static branch (no DB):
- For every `(tier, nav_slug)` pair in `TIER_DEFAULT_NAVS`:
  - If `nav_slug` projects to a module via `NAV_TO_MODULE_SLUG`, the validator asserts that `MODULE_POLICY[module]['view_capability']` is contained in `TIER_DEFAULT_CAPABILITIES[tier]`. Drift is reported (it is mitigated only when paired with a role/department preset).
  - Stale slugs (not in `CANONICAL_NAV_SLUGS`) are reported.
  - Modules referenced by a nav slug but absent from `MODULE_POLICY` are reported.

DB branch (optional, used by tests):
- Caller supplies a list of `(role_slug, dept_slug, nav_slugs)` snapshots from `Role.default_navigation_items`. The validator computes `regular_staff tier ∪ role preset ∪ canonical-dept preset` and asserts every nav slug projects to a module whose `view_capability` is granted. Orphaned/stale entries are reported.

### `validate_visibility_read_coherence()`

For every preset bundle (`TIER_DEFAULT_CAPABILITIES`, `ROLE_PRESET_CAPABILITIES`, `DEPARTMENT_PRESET_CAPABILITIES`) and every module in `MODULE_POLICY`, asserts that `view_capability` and `read_capability` are either both granted or both absent.

Both validators are diagnostic only. They never mutate data and are not invoked at runtime.

## 3. Wiring into the validation flow

The pre-existing pattern is per-domain `TestCase`s (e.g. `hotel/tests/test_rbac_bookings.py::BookingPolicyRegistryTest`) calling `validate_module_policy()` and `validate_preset_maps()`. Phase 5 extends this exact pattern by adding `hotel/tests/test_rbac_nav_consistency.py::NavCapabilityConsistencyTest`, which executes alongside the per-domain registry tests via `python manage.py test`. No new management command, no `Django.checks` registration, no resolver changes. The architecture for validation is unchanged.

## 4. Nav drift findings

`validate_nav_capability_consistency()` reports **15 tier-level drift entries** and **0 stale-slug** / **0 orphaned-DB-role** entries. All 15 entries have the same shape: a `TIER_DEFAULT_NAVS` slug whose `view_capability` is not on the same tier bundle.

Tier bundle drift (full inventory):

| Tier | Nav slug | Module | View capability not on tier |
| --- | --- | --- | --- |
| `super_staff_admin` | `chat` | `chat` | `chat.module.view` |
| `super_staff_admin` | `hotel_info` | `hotel_info` | `hotel_info.module.view` |
| `super_staff_admin` | `housekeeping` | `housekeeping` | `housekeeping.module.view` |
| `super_staff_admin` | `maintenance` | `maintenance` | `maintenance.module.view` |
| `super_staff_admin` | `restaurant_bookings` | `restaurant_bookings` | `restaurant_booking.module.view` |
| `super_staff_admin` | `rooms` | `rooms` | `room.module.view` |
| `super_staff_admin` | `staff_management` | `staff_management` | `staff_management.module.view` |
| `staff_admin` | `chat` | `chat` | `chat.module.view` |
| `staff_admin` | `hotel_info` | `hotel_info` | `hotel_info.module.view` |
| `staff_admin` | `housekeeping` | `housekeeping` | `housekeeping.module.view` |
| `staff_admin` | `maintenance` | `maintenance` | `maintenance.module.view` |
| `staff_admin` | `restaurant_bookings` | `restaurant_bookings` | `restaurant_booking.module.view` |
| `staff_admin` | `room_bookings` | `bookings` | `booking.module.view` |
| `staff_admin` | `rooms` | `rooms` | `room.module.view` |
| `regular_staff` | `chat` | `chat` | `chat.module.view` |

Live-DB role drift: `Role.default_navigation_items` is empty across all 21 canonical roles in all 3 hotels. No role-level orphan entries.

## 5. Visibility / read mismatch findings

`validate_visibility_read_coherence()` returns **0 mismatches**. Every preset bundle that grants any module's `view_capability` also grants the same module's `read_capability` (and vice versa). This holds for all three preset maps:

- `TIER_DEFAULT_CAPABILITIES` (3 tiers).
- `ROLE_PRESET_CAPABILITIES` (21 canonical roles).
- `DEPARTMENT_PRESET_CAPABILITIES` (8 canonical departments).

## 6. Tier nav mismatch findings

The 15 entries in §4 are all tier-level. For each `(tier, slug)` row, the slug is only reachable in `allowed_navs` for a staff member who carries the tier. Whether the corresponding module renders is independently gated by `rbac.<module>.visible`, which is computed from the resolved capability bundle (tier ∪ role ∪ department). For every canonical persona currently produced by Phase 4 presets, the role and/or department preset grants the missing `view_capability`:

- `front_desk_agent` (front_office dept) → carries `chat.module.view` via `_CHAT_BASE` and `housekeeping.module.view` via the front_office dept preset.
- All `*_manager` roles on `super_staff_admin` tier → carry `_CHAT_BASE`, `_HOTEL_INFO_READ`, plus their domain-specific `*.module.view`.
- All `*_supervisor` roles on `staff_admin` tier → carry `_HOTEL_INFO_READ` and their domain-specific `*.module.view`.
- `duty_manager` / management dept → carries `_CHAT_BASE` (chat) plus housekeeping/maintenance/rooms read bundles.

Personas where tier nav drift would expose a slug whose module renders hidden: a hypothetical `super_staff_admin` or `staff_admin` user with **no role and no department** assigned. This is an unsupported configuration in the current schema (`Staff.clean` rejects cross-tenant role/department, and seeders provision both). The frontend contract (`allowed_navs.includes(slug) && rbac[module].visible`) closes the loop even if such a user existed — the nav button is suppressed because `rbac.<module>.visible` is false.

## 7. Supervisor-authority findings

`_SUPERVISOR_AUTHORITY` (granted to `super_staff_admin` and `staff_admin` tiers) contains:

```
{CHAT_MESSAGE_MODERATE, CHAT_CONVERSATION_ASSIGN,
 STAFF_CHAT_CONVERSATION_MODERATE, STAFF_CHAT_CONVERSATION_DELETE}
```

It does **not** carry `chat.module.view` / `chat.conversation.read`. The audit asked whether this creates a functional authorization inconsistency.

**Verification:**

- Backend endpoint chain: `chat/views.py::delete_message` and the hard-delete path declare `permission_classes = [IsAuthenticated, IsStaffMember, CanViewChatModule]` and only then check `has_capability(user, 'chat.message.moderate')` inside the body. `CanViewChatModule` enforces `chat.module.view` with `safe_methods_bypass = False`. A staff_admin tier user without `chat.module.view` (no role/dept providing `_CHAT_BASE`) is rejected at `CanViewChatModule` before the moderate check runs.
- `staff_chat` is identical: `STAFF_CHAT_MODULE_VIEW` is granted to every tier through `_STAFF_CHAT_BASE`, so every authenticated staff already sees the staff_chat module. Moderation/delete authority on top of that is the actual additional grant.
- Frontend exposure: `rbac.chat.visible` is `false` for a tier-only-supervisor (no chat caps in role/dept), so the chat module and any moderation controls under it never render. Even if the controls were rendered, the backend rejects.

**Conclusion:** the asymmetry is intentional and architecturally safe — `_SUPERVISOR_AUTHORITY` carries authority capabilities (moderate, assign, delete) without carrying module-visibility. Module visibility is the responsibility of `_CHAT_BASE` / `_STAFF_CHAT_BASE`, which are layered onto roles/departments/tier separately. **No code change applied.**

`validate_visibility_read_coherence()` returns 0 because `_SUPERVISOR_AUTHORITY` carries neither `view_capability` nor `read_capability` for chat — the bundle is "authority-only" relative to the chat module and remains coherent.

## 8. Backend nav cleanup decision

**Path chosen: Option B — frontend-authoritative.**

Rationale:

- Trimming `TIER_DEFAULT_NAVS` to remove the 15 drift entries would hide nav buttons from operationally correct personas (`super_staff_admin` tier paired with `hotel_manager` role, etc.) unless we simultaneously seed `Role.default_navigation_items` for every canonical role × hotel combination. That is a non-trivial data migration and is outside the stated Phase 5 minimal-risk scope.
- The frontend contract already gates each rendered nav on both `allowed_navs.includes(slug)` AND `rbac[module].visible` (per `RBAC_OPERATIONAL_REBALANCE_AUDIT.md` §4.4 item 1). The 15 drift entries are absorbed at the rendering layer with zero behavioural change.
- Keeping the tier defaults as-is preserves backward compatibility: every staff member who currently sees a given nav button will continue to see it; no role's effective surface narrows or widens.

The new validators surface drift at test-time. If a future preset change introduces an additional nav slug whose `view_capability` is on no preset (i.e. truly unreachable), `test_nav_capability_drift_matches_documented_set` fails until the change is reviewed.

## 9. Remaining frontend expectations

- Continue to render a nav button only when `allowed_navs.includes(slug) && (NAV_TO_MODULE_SLUG[slug] === undefined || rbac[NAV_TO_MODULE_SLUG[slug]].visible)`. The `home` and `admin_settings` slugs have no module entry — render unconditionally based on `allowed_navs`.
- Do not derive moderation / authority controls from `allowed_navs` alone; gate moderation buttons on `rbac.<module>.actions.<action>` (e.g. `rbac.chat.actions.message_moderate`). This already matches the `useCan` / `can` contract.

## 10. Validation results

```
$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py test hotel.tests.test_rbac_nav_consistency -v 2
test_canonical_role_default_navs_have_no_orphans ... ok
test_module_policy_self_consistent ... ok
test_nav_capability_drift_matches_documented_set ... ok
test_preset_maps_self_consistent ... ok
test_visibility_read_coherence ... ok
Ran 5 tests in 0.017s
OK
```

Direct shell invocations:

```
validate_module_policy()                  -> []
validate_preset_maps()                    -> []
validate_visibility_read_coherence()      -> []
validate_nav_capability_consistency()     -> 15 documented tier-drift entries (matches EXPECTED_TIER_NAV_DRIFT)
```

### Acceptance verifications

1. **Every canonical role has a preset entry.**
   `set(CANONICAL_ROLE_SLUGS) ⊆ ROLE_PRESET_CAPABILITIES.keys()` — verified in Phase 4.
2. **Every canonical department has a preset entry.**
   `set(CANONICAL_DEPARTMENT_SLUGS) ⊆ DEPARTMENT_PRESET_CAPABILITIES.keys()` — verified in Phase 4.
3. **Every visible module has readable module state.** `validate_visibility_read_coherence()` → `[]`.
4. **Every readable module has visible module state.** Same validator covers both directions.
5. **Guest chat exposure** (verified by direct probe of `resolve_capabilities`):
   - Allowed (chat.module.view AND chat.conversation.read AND chat.message.send all granted at department + regular_staff tier with no role): `front_office`, `guest_relations`, `management`. ✅
   - `duty_manager` role / management dept on super_staff_admin tier: `chat.module.view = True`, `chat.guest.respond = True`. ✅
   - `hotel_manager` role / management dept on super_staff_admin tier: `chat.module.view = True`, `chat.guest.respond = True`. ✅
   - Blocked: `kitchen`, `maintenance`, `housekeeping`, `food_beverage` — all four return `chat.module.view = False`, `chat.message.send = False`, `chat.guest.respond = False`. ✅
6. **Destructive authorities unchanged.** Probe of `TIER_DEFAULT_CAPABILITIES`, `ROLE_PRESET_CAPABILITIES`, `DEPARTMENT_PRESET_CAPABILITIES` for the destructive set:
   - `booking.config.manage` → `hotel_manager`, `front_office_manager` (existing).
   - `room.inventory.delete` → `hotel_manager` only.
   - `room.type.manage` → `hotel_manager` only.
   - `room.checkout.destructive` → `hotel_manager` only.
   - `housekeeping.task.delete` → `hotel_manager`, `housekeeping_manager`.
   - `maintenance.request.delete` → `hotel_manager`, `maintenance_manager`.
   - `attendance.period.delete` → `hotel_manager` only.
   - `attendance.period.force_finalize` → `hotel_manager` only.
   - `restaurant_booking.record.delete` → `hotel_manager`, `fnb_manager`.
   - `hotel_info.category.manage` → no preset (superuser only).

## 11. Remaining intentional exceptions

| Item | Why it is intentional | Where surfaced |
| --- | --- | --- |
| Tier nav drift (15 entries in §4) | Tier defaults expose nav slugs whose visibility is closed by role / department presets in every supported persona. Frontend layered gate (`allowed_navs && rbac[module].visible`) closes any residual gap. | `EXPECTED_TIER_NAV_DRIFT` in `test_rbac_nav_consistency.py` |
| `_SUPERVISOR_AUTHORITY` carries `chat.message.moderate` / `chat.conversation.assign` / `staff_chat.conversation.moderate` / `staff_chat.conversation.delete` without `chat.module.view` / `chat.conversation.read` | Authority bundle, not visibility bundle. Module visibility is a separate `_CHAT_BASE` / `_STAFF_CHAT_BASE` grant. Backend chains `CanViewChatModule` before any moderation check, so unreachable. | §7 above |
| `front_office_manager` carries `_BOOKING_MANAGE` (which includes `booking.config.manage`) | Documented since Phase 6A — operational requirement for a front office manager to administer rate plans / cancellation policies in absentia of `hotel_manager`. | `RBAC_OPERATIONAL_REBALANCE_AUDIT.md` §4.3 |
| `hotel_info.category.manage` lives on no preset | Superuser-only by design (platform-level authority). | `RBAC_OPERATIONAL_REBALANCE_AUDIT.md` §5.1 |
| `home` and `admin_settings` nav slugs have no module entry in `MODULE_POLICY` | UX-only containers; not gated by module visibility. | `MODULES_WITHOUT_NAV` doc in `nav_catalog.py` |
| `guests` and `staff_chat` modules have no top-level nav slug | Surfaced inline within other modules (chat thread context, profile drawers). | `MODULES_WITHOUT_NAV` constant in `nav_catalog.py` |
| `Role.default_navigation_items` is empty across all canonical roles | Phase 5 chose Option B (frontend-authoritative); per-role nav seeding deferred. The orphan validator runs against this DB state and passes trivially. | §6 / §8 above |

## 12. Final RBAC architecture status

- Capability-driven: ✅. No new role-slug gates, tier-slug gates, or nav-slug fallbacks introduced.
- Fail-closed: ✅. Validators are diagnostic only; runtime resolvers (`resolve_capabilities`, `resolve_module_policy`) continue to filter against `CANONICAL_CAPABILITIES`.
- Module-policy projected: ✅. `rbac.<module>.visible` and `rbac.<module>.read` continue to be derived solely from `MODULE_POLICY[module]['view_capability']` / `['read_capability']` against the resolved capability set. Frontend stays the single rendering authority.
- No endpoint enforcement, capability slugs, module policy structure, or preset distributions changed in this phase.
- New diagnostic validators in place to detect future drift in nav coverage and visible/read coherence at test-time.
