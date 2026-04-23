"""
Canonical capability catalog for HotelMate RBAC (Phase 5).

This module is the SINGLE SOURCE OF TRUTH for:
- CANONICAL_CAPABILITIES: every named action permission the backend enforces
- TIER_DEFAULT_CAPABILITIES: baseline capability bundle granted by tier
- ROLE_PRESET_CAPABILITIES: capability bundle granted by a staff's role slug
- DEPARTMENT_PRESET_CAPABILITIES: capability bundle granted by department slug
- resolve_capabilities(): deterministic union of tier + role + department presets

CONTRACT RULES (hotelmates_auth_contract_v1.md):
- Capabilities follow the `domain.resource.action` naming convention.
- Role and department are preset sources; they are NOT enforcement keys.
  Enforcement reads only the resolved `allowed_capabilities` list.
- Tier contributes a baseline bundle; tier does not bypass capability checks.
- `super_user` (Django superuser) receives every capability.

PHASE 5a SCOPE:
This catalog is the MINIMUM set needed to replace the legacy role-slug and
department-slug checks identified in the RBAC audit at:
  - staff_chat/permissions.py (is_chat_manager)
  - staff_chat/views_messages.py, staff_chat/views_attachments.py
  - chat/views.py (receptionist routing, manager/admin hard-delete)
  - housekeeping/policy.py (is_manager, is_housekeeping, front desk)
  - notifications/notification_manager.py (porter/receptionist/kitchen routing)

Phase 5b rewires those callsites to read capabilities.
Phase 5c retires legacy role slugs and keys role presets on the canonical
role catalog (staff/role_catalog.py).

PHASE 5a DOES NOT:
- Introduce a per-staff capability override surface (DB field). That is a
  future phase; this catalog is already sufficient to preserve the exact
  access granted by the legacy checks.
- Wire capabilities into any endpoint. `HasCapability` exists for 5b.
"""
from __future__ import annotations

from typing import Iterable


# ---------------------------------------------------------------------------
# Canonical capability slugs.
#
# Naming: domain.resource.action
#
# When adding a new capability:
#   1. Add it here.
#   2. Add it to at least one of the preset maps below so *some* staff can
#      receive it (otherwise it is a dead capability).
#   3. Enforce it at the endpoint via HasCapability.
# ---------------------------------------------------------------------------

# --- Guest chat (chat app) ---
CHAT_MESSAGE_MODERATE = 'chat.message.moderate'
"""Hard-delete guest-chat messages authored by other senders (moderation)."""

CHAT_GUEST_RESPOND = 'chat.guest.respond'
"""Eligible to be routed inbound guest-chat traffic and to act on it.

Used by notification routing to decide who receives guest-chat pings, and
by any future staff-reply eligibility check. Historically carried by
`receptionist` role with a `front_office` department fallback.
"""

# --- Staff-to-staff chat ---
STAFF_CHAT_CONVERSATION_MODERATE = 'staff_chat.conversation.moderate'
"""Moderate staff-chat conversations (hard-delete others' messages and
attachments, manage any conversation as non-creator)."""

# --- Housekeeping ---
HOUSEKEEPING_ROOM_STATUS_TRANSITION = 'housekeeping.room_status.transition'
"""Perform normal housekeeping-workflow room status transitions
(CHECKOUT_DIRTY → CLEANING_IN_PROGRESS → CLEANED_UNINSPECTED → READY_FOR_GUEST,
plus rollback and MAINTENANCE_REQUIRED flagging from any status)."""

HOUSEKEEPING_ROOM_STATUS_OVERRIDE = 'housekeeping.room_status.override'
"""Force any valid room status transition as a manager override
(requires a note when source == 'MANAGER_OVERRIDE')."""

HOUSEKEEPING_ROOM_STATUS_FRONT_DESK = 'housekeeping.room_status.front_desk'
"""Perform the limited set of front-desk-permitted room status changes
(e.g. OCCUPIED → CHECKOUT_DIRTY, any → MAINTENANCE_REQUIRED)."""

HOUSEKEEPING_TASK_ASSIGN = 'housekeeping.task.assign'
"""Assign housekeeping tasks to staff members."""

# --- Room service ---
ROOM_SERVICE_ORDER_FULFILL_PORTER = 'room_service.order.fulfill_porter'
"""Eligible to receive porter-routed room-service order notifications.

Historically carried by the `porter` role slug. This is a routing /
eligibility capability, not authority — it says 'send me these pings',
not 'you may mutate these orders'.
"""

ROOM_SERVICE_ORDER_FULFILL_KITCHEN = 'room_service.order.fulfill_kitchen'
"""Eligible to receive kitchen-routed room-service order notifications.

Historically carried by staff in the `kitchen` department.
"""


CANONICAL_CAPABILITIES: frozenset[str] = frozenset({
    CHAT_MESSAGE_MODERATE,
    CHAT_GUEST_RESPOND,
    STAFF_CHAT_CONVERSATION_MODERATE,
    HOUSEKEEPING_ROOM_STATUS_TRANSITION,
    HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
    HOUSEKEEPING_TASK_ASSIGN,
    ROOM_SERVICE_ORDER_FULFILL_PORTER,
    ROOM_SERVICE_ORDER_FULFILL_KITCHEN,
})


# ---------------------------------------------------------------------------
# Tier baseline bundles.
#
# Contract §4: "Tier grants baseline capability bundles; it does not bypass
# capability checks." The runtime check is always against the resolved
# `allowed_capabilities` list.
#
# super_user (Django superuser) is handled separately in resolve_capabilities
# and receives every capability.
# ---------------------------------------------------------------------------

_SUPERVISOR_AUTHORITY: frozenset[str] = frozenset({
    CHAT_MESSAGE_MODERATE,
    STAFF_CHAT_CONVERSATION_MODERATE,
    HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    HOUSEKEEPING_ROOM_STATUS_TRANSITION,
    HOUSEKEEPING_TASK_ASSIGN,
})

TIER_DEFAULT_CAPABILITIES: dict[str, frozenset[str]] = {
    'super_staff_admin': _SUPERVISOR_AUTHORITY,
    'staff_admin': _SUPERVISOR_AUTHORITY,
    'regular_staff': frozenset(),
}


# ---------------------------------------------------------------------------
# Role preset bundles.
#
# Keyed by canonical `role.slug` (staff/role_catalog.py::CANONICAL_ROLE_SLUGS).
# These are additive on top of tier and department presets.
#
# Design notes:
#   - Manager-level canonical roles (front_office_manager, hotel_manager,
#     fnb_manager, …) are expected to run on super_staff_admin tier, which
#     already carries the full supervisor authority bundle via tier preset.
#     Role presets for them would be redundant.
#   - operations_admin is the only non-management role that inherits the
#     full supervisor authority bundle regardless of tier — it replaces the
#     legacy `admin` role.
#   - front_desk_agent carries the porter-routing capability so the room
#     service porter notifications target front desk staff. The broader
#     CHAT_GUEST_RESPOND + HOUSEKEEPING_ROOM_STATUS_FRONT_DESK capabilities
#     are granted by the front_office department preset below (so any
#     front-office role picks them up, not just agents).
# ---------------------------------------------------------------------------

ROLE_PRESET_CAPABILITIES: dict[str, frozenset[str]] = {
    'operations_admin': _SUPERVISOR_AUTHORITY,
    'front_desk_agent': frozenset({
        ROOM_SERVICE_ORDER_FULFILL_PORTER,
    }),
}


# ---------------------------------------------------------------------------
# Department preset bundles.
#
# Keyed by `department.slug`. Departments define contextual eligibility
# — for example, the `front_office` fallback used by chat/views.py when no
# staff carries the `receptionist` role.
#
# Only canonical department slugs (staff/department_catalog.py) appear here.
# ---------------------------------------------------------------------------

DEPARTMENT_PRESET_CAPABILITIES: dict[str, frozenset[str]] = {
    'front_office': frozenset({
        CHAT_GUEST_RESPOND,
        HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
    }),
    'housekeeping': frozenset({
        HOUSEKEEPING_ROOM_STATUS_TRANSITION,
    }),
    'kitchen': frozenset({
        ROOM_SERVICE_ORDER_FULFILL_KITCHEN,
    }),
}


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

def resolve_capabilities(
    tier: str | None,
    role_slug: str | None,
    department_slug: str | None,
    *,
    is_superuser: bool = False,
) -> list[str]:
    """
    Compute the resolved capability list for a staff member.

    Inputs are already-extracted primitives (not ORM objects) so this
    function is pure and easy to unit-test.

    Precedence (additive union):
        super_user  → every canonical capability
        otherwise   → tier baseline ∪ role preset ∪ department preset

    Returns a sorted list of capability slugs. Unknown/empty inputs
    contribute nothing and never raise.
    """
    if is_superuser:
        return sorted(CANONICAL_CAPABILITIES)

    bundle: set[str] = set()

    if tier:
        bundle |= TIER_DEFAULT_CAPABILITIES.get(tier, frozenset())

    if role_slug:
        bundle |= ROLE_PRESET_CAPABILITIES.get(role_slug, frozenset())

    if department_slug:
        bundle |= DEPARTMENT_PRESET_CAPABILITIES.get(
            department_slug, frozenset()
        )

    # Filter against the canonical set so a preset cannot smuggle in an
    # unknown capability if one of the preset maps drifts.
    return sorted(bundle & CANONICAL_CAPABILITIES)


def validate_preset_maps() -> list[str]:
    """
    Return a list of validation errors in the preset maps.

    Used by tests / management checks. An empty list means the maps are
    self-consistent: every preset capability is declared canonical.
    """
    errors: list[str] = []

    def _check(name: str, mapping: dict[str, Iterable[str]]) -> None:
        for key, caps in mapping.items():
            for cap in caps:
                if cap not in CANONICAL_CAPABILITIES:
                    errors.append(
                        f"{name}[{key!r}] contains unknown capability "
                        f"{cap!r}"
                    )

    _check('TIER_DEFAULT_CAPABILITIES', TIER_DEFAULT_CAPABILITIES)
    _check('ROLE_PRESET_CAPABILITIES', ROLE_PRESET_CAPABILITIES)
    _check('DEPARTMENT_PRESET_CAPABILITIES', DEPARTMENT_PRESET_CAPABILITIES)

    return errors
