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

# --- Housekeeping (Phase 6C) ---
HOUSEKEEPING_MODULE_VIEW = 'housekeeping.module.view'
"""See the housekeeping module (navigation + module-level visibility)."""

HOUSEKEEPING_DASHBOARD_READ = 'housekeeping.dashboard.read'
"""Read the housekeeping dashboard payload (counts, rooms-by-status,
self-assigned tasks, and — when also holding task.assign — hotel-wide
open tasks)."""

HOUSEKEEPING_TASK_READ = 'housekeeping.task.read'
"""List / retrieve housekeeping tasks scoped to the current hotel."""

HOUSEKEEPING_TASK_CREATE = 'housekeeping.task.create'
"""Create a housekeeping task."""

HOUSEKEEPING_TASK_UPDATE = 'housekeeping.task.update'
"""Update non-action fields of a housekeeping task (note, priority,
type, room, booking). Does NOT cover assignment, execution, or
cancellation — each of those has a dedicated capability."""

HOUSEKEEPING_TASK_DELETE = 'housekeeping.task.delete'
"""Delete a housekeeping task row."""

HOUSEKEEPING_TASK_EXECUTE = 'housekeeping.task.execute'
"""Start / complete a housekeeping task assigned to self (or grab an
unassigned task by starting it). Self-ownership remains an inline
business rule on top of this capability."""

HOUSEKEEPING_TASK_CANCEL = 'housekeeping.task.cancel'
"""Transition a housekeeping task to CANCELLED."""

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

HOUSEKEEPING_ROOM_STATUS_HISTORY_READ = (
    'housekeeping.room_status.history.read'
)
"""Read the per-room RoomStatusEvent audit log."""

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


# --- Maintenance (Phase 6D.1) ---
# Module policy shape (see staff/module_policy.py):
#   visible  → MAINTENANCE_MODULE_VIEW
#   read     → MAINTENANCE_REQUEST_READ
#   actions  → the slugs below.
#
# These slugs are deliberately distinct from the `room.maintenance.*`
# namespace (which lives in the rooms module and gates Room.maintenance_*
# fields). The Maintenance app does NOT mutate Room state.

MAINTENANCE_MODULE_VIEW = 'maintenance.module.view'
"""See the maintenance module (navigation + module-level visibility)."""

MAINTENANCE_REQUEST_READ = 'maintenance.request.read'
"""List / retrieve maintenance requests, comments and photos scoped to
the current hotel."""

MAINTENANCE_REQUEST_CREATE = 'maintenance.request.create'
"""File a new maintenance request."""

MAINTENANCE_REQUEST_ACCEPT = 'maintenance.request.accept'
"""Self-claim an open request: status open → in_progress and stamp
accepted_by to the requesting staff."""

MAINTENANCE_REQUEST_RESOLVE = 'maintenance.request.resolve'
"""Mark an in-progress request resolved."""

MAINTENANCE_REQUEST_UPDATE = 'maintenance.request.update'
"""Edit metadata fields of a maintenance request (room, location_note,
title, description). Does NOT cover status changes or accepted_by
reassignment — each of those has its own capability."""

MAINTENANCE_REQUEST_REASSIGN = 'maintenance.request.reassign'
"""Set or change the accepted_by technician on a maintenance request
to a same-hotel staff member."""

MAINTENANCE_REQUEST_REOPEN = 'maintenance.request.reopen'
"""Move a resolved/closed request back to open (clears accepted_by)."""

MAINTENANCE_REQUEST_CLOSE = 'maintenance.request.close'
"""Close out a resolved/in-progress request (status → closed)."""

MAINTENANCE_REQUEST_DELETE = 'maintenance.request.delete'
"""Delete a maintenance request (cascades to comments and photos)."""

MAINTENANCE_COMMENT_CREATE = 'maintenance.comment.create'
"""Add a comment to a same-hotel maintenance request. Authors may also
edit / delete their OWN comment with this capability."""

MAINTENANCE_COMMENT_MODERATE = 'maintenance.comment.moderate'
"""Edit or delete comments authored by another staff member."""

MAINTENANCE_PHOTO_UPLOAD = 'maintenance.photo.upload'
"""Upload one or more photos onto a same-hotel maintenance request."""

MAINTENANCE_PHOTO_DELETE = 'maintenance.photo.delete'
"""Delete a maintenance photo (also gates PUT/PATCH on photo rows)."""


# --- Staff Management (Phase 6E.1) ---
# Module policy shape (see staff/module_policy.py):
#   visible  → STAFF_MANAGEMENT_MODULE_VIEW
#   read     → STAFF_MANAGEMENT_STAFF_READ
#   actions  → the slugs below.
#
# Tier intentionally never carries any staff_management.* capability —
# staff-management authority is granted exclusively via role presets so
# tier never doubles as the permission engine (same contract as
# Bookings / Rooms / Housekeeping / Maintenance).

STAFF_MANAGEMENT_MODULE_VIEW = 'staff_management.module.view'
"""See the staff management module (navigation + module-level visibility)."""

STAFF_MANAGEMENT_STAFF_READ = 'staff_management.staff.read'
"""List / retrieve Staff rows (module `/me`, metadata, by_department,
by_hotel, attendance-summary) scoped to the current hotel."""

STAFF_MANAGEMENT_USER_READ = 'staff_management.user.read'
"""List / retrieve User rows tied to the requester's hotel registration
codes. Dangerous cross-hotel surface — granted only to supervise-level
personas."""

STAFF_MANAGEMENT_PENDING_REGISTRATION_READ = (
    'staff_management.pending_registration.read'
)
"""Read pending staff registrations (users who consumed a code but have
no Staff row yet)."""

STAFF_MANAGEMENT_STAFF_CREATE = 'staff_management.staff.create'
"""Create a Staff row (from a user who has consumed a registration code
for the URL hotel). Authority-field assignments remain subject to
anti-escalation rules."""

STAFF_MANAGEMENT_STAFF_UPDATE_PROFILE = 'staff_management.staff.update_profile'
"""Update non-authority profile fields on a Staff row
(first_name / last_name / email / phone_number / profile_image /
duty_status / is_on_duty). Never covers access_level / role /
department / hotel / is_active / allowed_navigation_items /
has_registered_face."""

STAFF_MANAGEMENT_STAFF_DEACTIVATE = 'staff_management.staff.deactivate'
"""Flip Staff.is_active = False via the dedicated deactivate action.
Self-deactivation is always rejected at the view layer."""

STAFF_MANAGEMENT_STAFF_DELETE = 'staff_management.staff.delete'
"""Hard-delete a Staff row. Self-delete is always rejected at the view
layer."""

STAFF_MANAGEMENT_AUTHORITY_VIEW = 'staff_management.authority.view'
"""Read the canonical navigation-permissions view for another staff
member (GET /<staff_id>/permissions/)."""

STAFF_MANAGEMENT_AUTHORITY_ROLE_ASSIGN = (
    'staff_management.authority.role.assign'
)
"""Assign Staff.role. Role queryset is scoped to the URL hotel and
role-preset-capability ceiling is enforced unless the requester holds
STAFF_MANAGEMENT_AUTHORITY_SUPERVISE."""

STAFF_MANAGEMENT_AUTHORITY_DEPARTMENT_ASSIGN = (
    'staff_management.authority.department.assign'
)
"""Assign Staff.department. Department queryset is scoped to the URL
hotel and department-preset-capability ceiling is enforced unless the
requester holds STAFF_MANAGEMENT_AUTHORITY_SUPERVISE."""

STAFF_MANAGEMENT_AUTHORITY_ACCESS_LEVEL_ASSIGN = (
    'staff_management.authority.access_level.assign'
)
"""Assign Staff.access_level. Without
STAFF_MANAGEMENT_AUTHORITY_SUPERVISE, the assigned level must be
strictly below the requester's own level."""

STAFF_MANAGEMENT_AUTHORITY_NAV_ASSIGN = (
    'staff_management.authority.nav.assign'
)
"""Assign Staff.allowed_navigation_items. Without
STAFF_MANAGEMENT_AUTHORITY_SUPERVISE, assigned slugs must be a subset of
the requester's own effective navs."""

STAFF_MANAGEMENT_AUTHORITY_SUPERVISE = 'staff_management.authority.supervise'
"""Meta-capability lifting the anti-escalation ceilings on role /
department / access-level / nav assignment. Reserved for the
hotel_manager role preset."""

STAFF_MANAGEMENT_ROLE_READ = 'staff_management.role.read'
"""List / retrieve Role rows scoped to the current hotel."""

STAFF_MANAGEMENT_ROLE_MANAGE = 'staff_management.role.manage'
"""Create / update / delete Role rows scoped to the current hotel."""

STAFF_MANAGEMENT_DEPARTMENT_READ = 'staff_management.department.read'
"""List / retrieve Department rows scoped to the current hotel."""

STAFF_MANAGEMENT_DEPARTMENT_MANAGE = 'staff_management.department.manage'
"""Create / update / delete Department rows scoped to the current hotel."""

STAFF_MANAGEMENT_REGISTRATION_PACKAGE_READ = (
    'staff_management.registration_package.read'
)
"""List registration packages for the current hotel."""

STAFF_MANAGEMENT_REGISTRATION_PACKAGE_CREATE = (
    'staff_management.registration_package.create'
)
"""Mint new registration packages for the current hotel."""

STAFF_MANAGEMENT_REGISTRATION_PACKAGE_EMAIL = (
    'staff_management.registration_package.email'
)
"""Email an existing registration package to a recipient."""

STAFF_MANAGEMENT_REGISTRATION_PACKAGE_PRINT = (
    'staff_management.registration_package.print'
)
"""Render the printable / QR payload for an existing registration
package."""


# --- Guests (Wave 1) ---
GUEST_RECORD_READ = 'guest.record.read'
"""Read in-house guest records scoped to the current hotel."""

GUEST_RECORD_UPDATE = 'guest.record.update'
"""Update in-house guest records scoped to the current hotel."""


# --- Hotel Info (Wave 1) ---
HOTEL_INFO_MODULE_VIEW = 'hotel_info.module.view'
"""See the hotel-info module (navigation + module-level visibility)."""

HOTEL_INFO_ENTRY_READ = 'hotel_info.entry.read'
"""Read hotel-info entries scoped to the current hotel."""

HOTEL_INFO_ENTRY_CREATE = 'hotel_info.entry.create'
"""Create hotel-info entries for the current hotel."""

HOTEL_INFO_ENTRY_UPDATE = 'hotel_info.entry.update'
"""Update hotel-info entries scoped to the current hotel."""

HOTEL_INFO_ENTRY_DELETE = 'hotel_info.entry.delete'
"""Delete hotel-info entries scoped to the current hotel."""

HOTEL_INFO_CATEGORY_READ = 'hotel_info.category.read'
"""Read global HotelInfoCategory rows."""

HOTEL_INFO_CATEGORY_MANAGE = 'hotel_info.category.manage'
"""Mutate global HotelInfoCategory rows. Platform/superuser-only."""

HOTEL_INFO_QR_READ = 'hotel_info.qr.read'
"""Read CategoryQRCode records scoped to the current hotel."""

HOTEL_INFO_QR_GENERATE = 'hotel_info.qr.generate'
"""Generate / regenerate CategoryQRCode records for the current hotel."""


CANONICAL_CAPABILITIES: frozenset[str] = frozenset({
    CHAT_MESSAGE_MODERATE,
    CHAT_GUEST_RESPOND,
    STAFF_CHAT_CONVERSATION_MODERATE,
    # Housekeeping (Phase 6C)
    HOUSEKEEPING_MODULE_VIEW,
    HOUSEKEEPING_DASHBOARD_READ,
    HOUSEKEEPING_TASK_READ,
    HOUSEKEEPING_TASK_CREATE,
    HOUSEKEEPING_TASK_UPDATE,
    HOUSEKEEPING_TASK_DELETE,
    HOUSEKEEPING_TASK_EXECUTE,
    HOUSEKEEPING_TASK_CANCEL,
    HOUSEKEEPING_ROOM_STATUS_TRANSITION,
    HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
    HOUSEKEEPING_ROOM_STATUS_HISTORY_READ,
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
    # Maintenance (Phase 6D.1)
    MAINTENANCE_MODULE_VIEW,
    MAINTENANCE_REQUEST_READ,
    MAINTENANCE_REQUEST_CREATE,
    MAINTENANCE_REQUEST_ACCEPT,
    MAINTENANCE_REQUEST_RESOLVE,
    MAINTENANCE_REQUEST_UPDATE,
    MAINTENANCE_REQUEST_REASSIGN,
    MAINTENANCE_REQUEST_REOPEN,
    MAINTENANCE_REQUEST_CLOSE,
    MAINTENANCE_REQUEST_DELETE,
    MAINTENANCE_COMMENT_CREATE,
    MAINTENANCE_COMMENT_MODERATE,
    MAINTENANCE_PHOTO_UPLOAD,
    MAINTENANCE_PHOTO_DELETE,
    # Staff Management (Phase 6E.1)
    STAFF_MANAGEMENT_MODULE_VIEW,
    STAFF_MANAGEMENT_STAFF_READ,
    STAFF_MANAGEMENT_USER_READ,
    STAFF_MANAGEMENT_PENDING_REGISTRATION_READ,
    STAFF_MANAGEMENT_STAFF_CREATE,
    STAFF_MANAGEMENT_STAFF_UPDATE_PROFILE,
    STAFF_MANAGEMENT_STAFF_DEACTIVATE,
    STAFF_MANAGEMENT_STAFF_DELETE,
    STAFF_MANAGEMENT_AUTHORITY_VIEW,
    STAFF_MANAGEMENT_AUTHORITY_ROLE_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_DEPARTMENT_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_ACCESS_LEVEL_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_NAV_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_SUPERVISE,
    STAFF_MANAGEMENT_ROLE_READ,
    STAFF_MANAGEMENT_ROLE_MANAGE,
    STAFF_MANAGEMENT_DEPARTMENT_READ,
    STAFF_MANAGEMENT_DEPARTMENT_MANAGE,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_READ,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_CREATE,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_EMAIL,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_PRINT,
    # Guests (Wave 1)
    GUEST_RECORD_READ,
    GUEST_RECORD_UPDATE,
    # Hotel Info (Wave 1)
    HOTEL_INFO_MODULE_VIEW,
    HOTEL_INFO_ENTRY_READ,
    HOTEL_INFO_ENTRY_CREATE,
    HOTEL_INFO_ENTRY_UPDATE,
    HOTEL_INFO_ENTRY_DELETE,
    HOTEL_INFO_CATEGORY_READ,
    HOTEL_INFO_CATEGORY_MANAGE,
    HOTEL_INFO_QR_READ,
    HOTEL_INFO_QR_GENERATE,
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

# Phase 6C: housekeeping caps removed from the cross-cutting tier bundle.
# Housekeeping authority is granted exclusively via role / department
# presets so tier never doubles as the housekeeping permission engine.
_SUPERVISOR_AUTHORITY: frozenset[str] = frozenset({
    CHAT_MESSAGE_MODERATE,
    STAFF_CHAT_CONVERSATION_MODERATE,
})


# ---------------------------------------------------------------------------
# Housekeeping preset bundles (Phase 6C)
#
# Mirrors bookings/rooms shape: manage ⊃ supervise ⊃ operate ⊃ base.
# Tier intentionally never carries any of these — see the rule above.
# ---------------------------------------------------------------------------

_HOUSEKEEPING_BASE: frozenset[str] = frozenset({
    HOUSEKEEPING_MODULE_VIEW,
    HOUSEKEEPING_DASHBOARD_READ,
    HOUSEKEEPING_TASK_READ,
    HOUSEKEEPING_ROOM_STATUS_HISTORY_READ,
})

_HOUSEKEEPING_OPERATE: frozenset[str] = _HOUSEKEEPING_BASE | frozenset({
    HOUSEKEEPING_TASK_EXECUTE,
    HOUSEKEEPING_ROOM_STATUS_TRANSITION,
})

_HOUSEKEEPING_SUPERVISE: frozenset[str] = _HOUSEKEEPING_OPERATE | frozenset({
    HOUSEKEEPING_TASK_CREATE,
    HOUSEKEEPING_TASK_UPDATE,
    HOUSEKEEPING_TASK_ASSIGN,
    HOUSEKEEPING_TASK_CANCEL,
    HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
})

_HOUSEKEEPING_MANAGE: frozenset[str] = _HOUSEKEEPING_SUPERVISE | frozenset({
    HOUSEKEEPING_TASK_DELETE,
})


# ---------------------------------------------------------------------------
# Maintenance preset bundles (Phase 6D.1)
#
# Mirrors bookings/rooms/housekeeping shape: manage ⊃ supervise ⊃ operate
# ⊃ base ⊃ reporter. Tier intentionally never carries any of these — see
# the rule above.
#
# The `maintenance.*` namespace is strictly disjoint from the
# `room.maintenance.*` namespace (rooms module). Maintenance does not
# mutate Room state; cross-module authority must be granted explicitly
# via the rooms / housekeeping presets, not smuggled in here.
# ---------------------------------------------------------------------------

# Reporter bucket — non-maintenance staff who only need to file tickets.
_MAINTENANCE_REPORTER: frozenset[str] = frozenset({
    MAINTENANCE_MODULE_VIEW,
    MAINTENANCE_REQUEST_READ,
    MAINTENANCE_REQUEST_CREATE,
})

# Base read bundle (visibility + read), no write authority.
_MAINTENANCE_READ: frozenset[str] = frozenset({
    MAINTENANCE_MODULE_VIEW,
    MAINTENANCE_REQUEST_READ,
})

# Operate bucket — line technician self-service.
_MAINTENANCE_OPERATE: frozenset[str] = _MAINTENANCE_READ | frozenset({
    MAINTENANCE_REQUEST_CREATE,
    MAINTENANCE_REQUEST_ACCEPT,
    MAINTENANCE_REQUEST_RESOLVE,
    MAINTENANCE_COMMENT_CREATE,
    MAINTENANCE_PHOTO_UPLOAD,
})

# Supervise bucket — shift lead authority.
_MAINTENANCE_SUPERVISE: frozenset[str] = _MAINTENANCE_OPERATE | frozenset({
    MAINTENANCE_REQUEST_UPDATE,
    MAINTENANCE_REQUEST_REASSIGN,
    MAINTENANCE_REQUEST_REOPEN,
    MAINTENANCE_COMMENT_MODERATE,
    MAINTENANCE_PHOTO_DELETE,
})

# Manage bucket — destructive lifecycle authority.
_MAINTENANCE_MANAGE: frozenset[str] = _MAINTENANCE_SUPERVISE | frozenset({
    MAINTENANCE_REQUEST_CLOSE,
    MAINTENANCE_REQUEST_DELETE,
})


# ---------------------------------------------------------------------------
# Staff Management preset bundles (Phase 6E.1)
#
# Three escalating bundles:
#   BASIC   — module.view + read surfaces + basic staff CRUD + registration
#             packages + role/department read. No authority assignment,
#             no delete, no supervise. This is the "staff_admin role"
#             persona.
#   FULL    — BASIC + authority.view + authority.{role,department,
#             access_level,nav}.assign + role/department.manage +
#             staff.delete. This is the "super_staff_admin role" persona;
#             anti-escalation rules still apply because the supervise
#             capability is NOT included.
#   MANAGER — FULL + authority.supervise. Lifts anti-escalation ceilings
#             within the same hotel. Reserved for the hotel_manager
#             role preset.
#
# Tier intentionally never carries any staff_management.* capability
# (see the contract rule at the top of this file and the preset
# distribution tests).
# ---------------------------------------------------------------------------

_STAFF_MANAGEMENT_BASIC: frozenset[str] = frozenset({
    STAFF_MANAGEMENT_MODULE_VIEW,
    STAFF_MANAGEMENT_STAFF_READ,
    STAFF_MANAGEMENT_PENDING_REGISTRATION_READ,
    STAFF_MANAGEMENT_STAFF_CREATE,
    STAFF_MANAGEMENT_STAFF_UPDATE_PROFILE,
    STAFF_MANAGEMENT_STAFF_DEACTIVATE,
    STAFF_MANAGEMENT_ROLE_READ,
    STAFF_MANAGEMENT_DEPARTMENT_READ,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_READ,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_CREATE,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_EMAIL,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_PRINT,
})

_STAFF_MANAGEMENT_FULL: frozenset[str] = _STAFF_MANAGEMENT_BASIC | frozenset({
    STAFF_MANAGEMENT_USER_READ,
    STAFF_MANAGEMENT_AUTHORITY_VIEW,
    STAFF_MANAGEMENT_AUTHORITY_ROLE_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_DEPARTMENT_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_ACCESS_LEVEL_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_NAV_ASSIGN,
    STAFF_MANAGEMENT_ROLE_MANAGE,
    STAFF_MANAGEMENT_DEPARTMENT_MANAGE,
    STAFF_MANAGEMENT_STAFF_DELETE,
})

_STAFF_MANAGEMENT_MANAGER: frozenset[str] = (
    _STAFF_MANAGEMENT_FULL | frozenset({
        STAFF_MANAGEMENT_AUTHORITY_SUPERVISE,
    })
)


# ---------------------------------------------------------------------------
# Guests preset bundles (Wave 1)
#
# Read+update kept tight to front-office personas (reception-style roles
# manage in-house guest records). hotel_manager picks up the same bundle
# via role preset. category.manage is intentionally excluded from every
# preset for the hotel_info module (platform/superuser only).
# ---------------------------------------------------------------------------

_GUESTS_READ: frozenset[str] = frozenset({
    GUEST_RECORD_READ,
})

_GUESTS_OPERATE: frozenset[str] = _GUESTS_READ | frozenset({
    GUEST_RECORD_UPDATE,
})


# ---------------------------------------------------------------------------
# Hotel Info preset bundles (Wave 1)
#
# manage ⊃ read. category.manage is NOT included — that capability is
# platform/superuser-only and is granted exclusively via the
# Django-superuser all-capabilities path in resolve_capabilities.
# ---------------------------------------------------------------------------

_HOTEL_INFO_READ: frozenset[str] = frozenset({
    HOTEL_INFO_MODULE_VIEW,
    HOTEL_INFO_ENTRY_READ,
    HOTEL_INFO_CATEGORY_READ,
    HOTEL_INFO_QR_READ,
})

_HOTEL_INFO_MANAGE: frozenset[str] = _HOTEL_INFO_READ | frozenset({
    HOTEL_INFO_ENTRY_CREATE,
    HOTEL_INFO_ENTRY_UPDATE,
    HOTEL_INFO_ENTRY_DELETE,
    HOTEL_INFO_QR_GENERATE,
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
#   - front_desk_agent carries the porter-routing capability so the room
#     service porter notifications target front desk staff. The broader
#     CHAT_GUEST_RESPOND + HOUSEKEEPING_ROOM_STATUS_FRONT_DESK capabilities
#     are granted by the front_office department preset below (so any
#     front-office role picks them up, not just agents).
# ---------------------------------------------------------------------------

ROLE_PRESET_CAPABILITIES: dict[str, frozenset[str]] = {
    # Phase 6E.1: staff-management-only role personas. They carry the
    # staff_management.* bundle and nothing else — the canonical way for
    # a hotel to grant "staff_admin role" / "super_staff_admin role"
    # authority without tier leakage. Not to be confused with the
    # Staff.access_level tier choices of the same name.
    'staff_admin': _STAFF_MANAGEMENT_BASIC,
    'super_staff_admin': _STAFF_MANAGEMENT_FULL,
    # Phase 6A.2: manage-bucket role presets. Tier no longer grants
    # BOOKING_CONFIG_MANAGE, so managing rate plans / cancellation
    # policies / precheckin / survey config requires one of these roles.
    # Phase 6B.1: hotel_manager carries the full rooms manage bundle.
    # Phase 6C: hotel_manager carries the full housekeeping manage bundle.
    # Phase 6D.1: hotel_manager carries the full maintenance manage bundle.
    # Phase 6E.1: carries full staff-management manager bundle (supervise).
    'hotel_manager': (
        _BOOKING_MANAGE | _ROOM_MANAGE | _HOUSEKEEPING_MANAGE
        | _MAINTENANCE_MANAGE | _STAFF_MANAGEMENT_MANAGER
        | _GUESTS_OPERATE | _HOTEL_INFO_MANAGE
    ),
    'front_office_manager': (
        _BOOKING_MANAGE | _ROOM_SUPERVISE | _HOUSEKEEPING_SUPERVISE
        | _MAINTENANCE_REPORTER | _GUESTS_OPERATE | _HOTEL_INFO_READ
    ),
    'front_desk_agent': frozenset({
        ROOM_SERVICE_ORDER_FULFILL_PORTER,
    }) | _MAINTENANCE_REPORTER | _GUESTS_OPERATE | _HOTEL_INFO_READ,
    # Phase 6B.1 / 6C: housekeeping authority roles. Supervisor and
    # manager bundles include HOUSEKEEPING_ROOM_STATUS_OVERRIDE which is
    # also required by the state-machine layer so complete_maintenance
    # (MAINTENANCE_REQUIRED → CHECKOUT_DIRTY / READY_FOR_GUEST) succeeds.
    'housekeeping_supervisor': (
        _ROOM_SUPERVISE | _HOUSEKEEPING_SUPERVISE
    ),
    'housekeeping_manager': (
        _ROOM_SUPERVISE | _HOUSEKEEPING_MANAGE
    ),
    # Phase 6B.1: maintenance authority roles carry clear-only (and,
    # for maintenance_manager, out-of-order) on top of the dept preset.
    # OVERRIDE is required so complete_maintenance can flip the room out
    # of MAINTENANCE_REQUIRED via the canonical housekeeping service.
    'maintenance_supervisor': frozenset({
        ROOM_MAINTENANCE_CLEAR,
        HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    }) | _MAINTENANCE_SUPERVISE,
    'maintenance_manager': frozenset({
        ROOM_MAINTENANCE_CLEAR,
        ROOM_OUT_OF_ORDER_SET,
        HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    }) | _MAINTENANCE_MANAGE,
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
        HOUSEKEEPING_MODULE_VIEW,
        HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
        HOUSEKEEPING_ROOM_STATUS_HISTORY_READ,
    }) | _BOOKING_READ | _BOOKING_OPERATE | _ROOM_READ | _MAINTENANCE_REPORTER,
    # Phase 6B.1 / 6C: housekeeping department gets full room OPERATE
    # plus the housekeeping operate bundle (read + execute + transition
    # + history read).
    # Phase 6D.1: housekeepers can file maintenance tickets they discover
    # mid-turnover (reporter bundle only — they cannot action tickets).
    'housekeeping': (
        _ROOM_OPERATE | _HOUSEKEEPING_OPERATE | _MAINTENANCE_REPORTER
    ),
    'kitchen': frozenset({
        ROOM_SERVICE_ORDER_FULFILL_KITCHEN,
    }),
    # Phase 6B.1: maintenance department gets room READ + flag.
    # HOUSEKEEPING_ROOM_STATUS_TRANSITION is required so mark_maintenance
    # can actually flip the room to MAINTENANCE_REQUIRED via the canonical
    # housekeeping service (which gates on that capability).
    # Phase 6D.1: maintenance department carries the full operate bundle
    # for the maintenance.* namespace (read + create + accept + resolve
    # + comment.create + photo.upload). Supervise / manage authority
    # remain role-gated.
    'maintenance': _ROOM_READ | frozenset({
        ROOM_MAINTENANCE_FLAG,
        HOUSEKEEPING_ROOM_STATUS_TRANSITION,
    }) | _MAINTENANCE_OPERATE,
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
