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

# --- Room bookings (Phase 6A) ---
# Module policy shape for bookings (see staff/module_policy.py):
#   visible  → BOOKING_MODULE_VIEW
#   read     → BOOKING_RECORD_READ
#   actions  → the remaining slugs below, grouped into operate / supervise /
#              manage buckets.
#
# Granularity rule (Phase 6A): read does not imply operate, operate does not
# imply supervise, supervise does not imply manage. Each bucket is an
# additive escalation expressed through preset maps.

BOOKING_MODULE_VIEW = 'booking.module.view'
"""See the room-bookings module (navigation + module-level reads)."""

BOOKING_RECORD_READ = 'booking.record.read'
"""Read booking records (list/detail/available-rooms/overstay status)."""

BOOKING_RECORD_UPDATE = 'booking.record.update'
"""Update booking records (mark seen, confirm, party/guest-facing info)."""

BOOKING_RECORD_CANCEL = 'booking.record.cancel'
"""Cancel / decline bookings."""

BOOKING_ROOM_ASSIGN = 'booking.room.assign'
"""Assign, unassign, and move rooms on a booking."""

BOOKING_STAY_CHECKIN = 'booking.stay.checkin'
"""Check a booking in (arrival flow)."""

BOOKING_STAY_CHECKOUT = 'booking.stay.checkout'
"""Check a booking out (departure flow)."""

BOOKING_GUEST_COMMUNICATE = 'booking.guest.communicate'
"""Trigger guest-facing communications (pre-check-in link, survey link)."""

BOOKING_OVERRIDE_SUPERVISE = 'booking.override.supervise'
"""Supervisor overrides: acknowledge overstay, force check-in / check-out,
override conflicts, modify locked bookings."""

BOOKING_CONFIG_MANAGE = 'booking.config.manage'
"""Manage booking rules / hotel-level booking configuration."""


# --- Rooms (Phase 6B.1) ---
# Every capability below is backed by at least one currently live endpoint
# mounted under /api/staff/hotel/{slug}/. `room.qr.generate` is NOT modelled
# because no rooms QR-generation endpoint exists after Phase 6B.0 cleanup.

ROOM_MODULE_VIEW = 'room.module.view'
"""See the rooms module (navigation + module-level visibility)."""

ROOM_INVENTORY_READ = 'room.inventory.read'
"""Read room inventory (list/detail of Room rows)."""

ROOM_INVENTORY_CREATE = 'room.inventory.create'
"""Create room inventory rows (single + bulk)."""

ROOM_INVENTORY_UPDATE = 'room.inventory.update'
"""Update room inventory rows (non out-of-order fields)."""

ROOM_INVENTORY_DELETE = 'room.inventory.delete'
"""Delete room inventory rows."""

ROOM_TYPE_READ = 'room.type.read'
"""Read room-type rows (marketing / pricing surface)."""

ROOM_TYPE_MANAGE = 'room.type.manage'
"""Create / update / delete room types and upload room-type media."""

ROOM_MEDIA_READ = 'room.media.read'
"""Read the room-image gallery."""

ROOM_MEDIA_MANAGE = 'room.media.manage'
"""Create / update / delete / reorder / set-cover room-image gallery rows."""

ROOM_STATUS_READ = 'room.status.read'
"""Read turnover dashboard rooms and stats."""

ROOM_STATUS_TRANSITION = 'room.status.transition'
"""Perform day-to-day turnover transitions (start cleaning, mark cleaned)."""

ROOM_INSPECTION_PERFORM = 'room.inspection.perform'
"""Perform an inspection pass/fail decision after cleaning."""

ROOM_MAINTENANCE_FLAG = 'room.maintenance.flag'
"""Flag a room as MAINTENANCE_REQUIRED."""

ROOM_MAINTENANCE_CLEAR = 'room.maintenance.clear'
"""Clear a MAINTENANCE_REQUIRED flag (back to dirty or ready)."""

ROOM_OUT_OF_ORDER_SET = 'room.out_of_order.set'
"""Set or clear the `is_out_of_order` override flag on a room."""

ROOM_CHECKOUT_BULK = 'room.checkout.bulk'
"""Bulk non-destructive checkout across multiple rooms."""

ROOM_CHECKOUT_DESTRUCTIVE = 'room.checkout.destructive'
"""Destructive bulk checkout (deletes guests, conversations, orders)."""


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
    # Bookings (Phase 6A)
    BOOKING_MODULE_VIEW,
    BOOKING_RECORD_READ,
    BOOKING_RECORD_UPDATE,
    BOOKING_RECORD_CANCEL,
    BOOKING_ROOM_ASSIGN,
    BOOKING_STAY_CHECKIN,
    BOOKING_STAY_CHECKOUT,
    BOOKING_GUEST_COMMUNICATE,
    BOOKING_OVERRIDE_SUPERVISE,
    BOOKING_CONFIG_MANAGE,
    # Rooms (Phase 6B.1)
    ROOM_MODULE_VIEW,
    ROOM_INVENTORY_READ,
    ROOM_INVENTORY_CREATE,
    ROOM_INVENTORY_UPDATE,
    ROOM_INVENTORY_DELETE,
    ROOM_TYPE_READ,
    ROOM_TYPE_MANAGE,
    ROOM_MEDIA_READ,
    ROOM_MEDIA_MANAGE,
    ROOM_STATUS_READ,
    ROOM_STATUS_TRANSITION,
    ROOM_INSPECTION_PERFORM,
    ROOM_MAINTENANCE_FLAG,
    ROOM_MAINTENANCE_CLEAR,
    ROOM_OUT_OF_ORDER_SET,
    ROOM_CHECKOUT_BULK,
    ROOM_CHECKOUT_DESTRUCTIVE,
})


# ---------------------------------------------------------------------------
# Booking preset bundles (Phase 6A)
# ---------------------------------------------------------------------------

# Read bucket — visibility + read, nothing more.
_BOOKING_READ: frozenset[str] = frozenset({
    BOOKING_MODULE_VIEW,
    BOOKING_RECORD_READ,
})

# Operate bucket — day-to-day front-desk work.
_BOOKING_OPERATE: frozenset[str] = _BOOKING_READ | frozenset({
    BOOKING_RECORD_UPDATE,
    BOOKING_RECORD_CANCEL,
    BOOKING_ROOM_ASSIGN,
    BOOKING_STAY_CHECKIN,
    BOOKING_STAY_CHECKOUT,
    BOOKING_GUEST_COMMUNICATE,
})

# Supervise bucket — adds override authority on top of operate.
_BOOKING_SUPERVISE: frozenset[str] = _BOOKING_OPERATE | frozenset({
    BOOKING_OVERRIDE_SUPERVISE,
})

# Manage bucket — full booking authority including config.
_BOOKING_MANAGE: frozenset[str] = _BOOKING_SUPERVISE | frozenset({
    BOOKING_CONFIG_MANAGE,
})


# ---------------------------------------------------------------------------
# Room preset bundles (Phase 6B.1)
#
# Nested buckets (mirrors bookings model): manage ⊃ supervise ⊃ operate ⊃ read.
# Nesting is a preset convenience; registry tests verify bucket escalation
# matches the endpoint enforcement chain.
# ---------------------------------------------------------------------------

_ROOM_READ: frozenset[str] = frozenset({
    ROOM_MODULE_VIEW,
    ROOM_INVENTORY_READ,
    ROOM_TYPE_READ,
    ROOM_MEDIA_READ,
    ROOM_STATUS_READ,
})

_ROOM_OPERATE: frozenset[str] = _ROOM_READ | frozenset({
    ROOM_STATUS_TRANSITION,
    ROOM_MAINTENANCE_FLAG,
})

_ROOM_SUPERVISE: frozenset[str] = _ROOM_OPERATE | frozenset({
    ROOM_INSPECTION_PERFORM,
    ROOM_MAINTENANCE_CLEAR,
    ROOM_CHECKOUT_BULK,
})

_ROOM_MANAGE: frozenset[str] = _ROOM_SUPERVISE | frozenset({
    ROOM_INVENTORY_CREATE,
    ROOM_INVENTORY_UPDATE,
    ROOM_INVENTORY_DELETE,
    ROOM_TYPE_MANAGE,
    ROOM_MEDIA_MANAGE,
    ROOM_OUT_OF_ORDER_SET,
    ROOM_CHECKOUT_DESTRUCTIVE,
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
    # Phase 6A.2: tier carries only cross-cutting supervisor authority.
    # Booking operate/manage live on department/role presets so tier is
    # NOT the permission engine.
    #   super_staff_admin → supervisor authority + booking supervise (overrides)
    #   staff_admin       → supervisor authority only (no booking caps)
    #   regular_staff     → no tier-level caps (role/dept presets only)
    'super_staff_admin': _SUPERVISOR_AUTHORITY | _BOOKING_SUPERVISE,
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
    # operations_admin replaces the legacy `admin` role: full supervisor
    # authority regardless of tier, plus booking supervise (overrides).
    # Phase 6A.2: downgraded from MANAGE → SUPERVISE; config manage is
    # reserved for hotel_manager / front_office_manager role presets.
    # Phase 6B.1: adds room supervise + out-of-order + destructive checkout.
    'operations_admin': (
        _SUPERVISOR_AUTHORITY
        | _BOOKING_SUPERVISE
        | _ROOM_SUPERVISE
        | frozenset({ROOM_OUT_OF_ORDER_SET, ROOM_CHECKOUT_DESTRUCTIVE})
    ),
    # Phase 6A.2: manage-bucket role presets. Tier no longer grants
    # BOOKING_CONFIG_MANAGE, so managing rate plans / cancellation
    # policies / precheckin / survey config requires one of these roles.
    # Phase 6B.1: hotel_manager carries the full rooms manage bundle.
    'hotel_manager': _BOOKING_MANAGE | _ROOM_MANAGE,
    'front_office_manager': _BOOKING_MANAGE | _ROOM_SUPERVISE,
    'front_desk_agent': frozenset({
        ROOM_SERVICE_ORDER_FULFILL_PORTER,
    }),
    # Phase 6B.1: housekeeping authority roles. Supervisor/manager must
    # carry HOUSEKEEPING_ROOM_STATUS_OVERRIDE so complete_maintenance
    # (MAINTENANCE_REQUIRED → CHECKOUT_DIRTY / READY_FOR_GUEST) succeeds
    # at the housekeeping state-machine layer.
    'housekeeping_supervisor': _ROOM_SUPERVISE | frozenset({
        HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    }),
    'housekeeping_manager': _ROOM_SUPERVISE | frozenset({
        HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    }),
    # Phase 6B.1: maintenance authority roles carry clear-only (and,
    # for maintenance_manager, out-of-order) on top of the dept preset.
    # OVERRIDE is required so complete_maintenance can flip the room out
    # of MAINTENANCE_REQUIRED via the canonical housekeeping service.
    'maintenance_supervisor': frozenset({
        ROOM_MAINTENANCE_CLEAR,
        HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    }),
    'maintenance_manager': frozenset({
        ROOM_MAINTENANCE_CLEAR,
        ROOM_OUT_OF_ORDER_SET,
        HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
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
    # Phase 6A.2: front_office department carries booking READ + OPERATE.
    # This is the fix for "front_office regular_staff cannot operate
    # bookings" — operate authority lives on department, not on tier.
    # Phase 6B.1: front_office carries room READ only. Front-desk does
    # NOT operate the turnover state machine.
    'front_office': frozenset({
        CHAT_GUEST_RESPOND,
        HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
    }) | _BOOKING_READ | _BOOKING_OPERATE | _ROOM_READ,
    # Phase 6B.1: housekeeping department gets full room OPERATE.
    'housekeeping': frozenset({
        HOUSEKEEPING_ROOM_STATUS_TRANSITION,
    }) | _ROOM_OPERATE,
    'kitchen': frozenset({
        ROOM_SERVICE_ORDER_FULFILL_KITCHEN,
    }),
    # Phase 6B.1: maintenance department gets room READ + flag.
    # HOUSEKEEPING_ROOM_STATUS_TRANSITION is required so mark_maintenance
    # can actually flip the room to MAINTENANCE_REQUIRED via the canonical
    # housekeeping service (which gates on that capability).
    'maintenance': _ROOM_READ | frozenset({
        ROOM_MAINTENANCE_FLAG,
        HOUSEKEEPING_ROOM_STATUS_TRANSITION,
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
