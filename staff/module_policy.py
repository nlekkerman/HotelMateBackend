"""
Canonical module policy registry (Phase 6A).

SINGLE SOURCE OF TRUTH for the normalized RBAC policy shape exposed to the
frontend. Maps each module to:

    visible  → capability gating module-level visibility
    read     → capability gating read access to module data
    actions  → dict of action slug → required capability slug

The frontend consumes ``rbac[module]`` to decide which modules, pages, and
action buttons to render. The backend must enforce the exact same
capabilities at endpoint level so the two surfaces never disagree.

Rules (contract):
- No role slug, no nav slug, no tier name appears in this file. Only
  canonical capability slugs from ``staff.capability_catalog``.
- Every capability referenced here MUST be in ``CANONICAL_CAPABILITIES``
  (validated by ``validate_module_policy``). Drift fails closed.
- Actions are mapped to buckets (read / operate / supervise / manage) by
  which capability preset grants them (see ``capability_catalog``), not by
  literal bucket names — frontend reads booleans, not tiers.

Phase 6A scope: ``bookings`` only. Rooms / housekeeping / room_services /
staff / attendance / hotel land in subsequent passes following this same
shape.
"""
from __future__ import annotations

from typing import Iterable, Mapping

from staff.capability_catalog import (
    BOOKING_CONFIG_MANAGE,
    BOOKING_GUEST_COMMUNICATE,
    BOOKING_MODULE_VIEW,
    BOOKING_OVERRIDE_SUPERVISE,
    BOOKING_RECORD_CANCEL,
    BOOKING_RECORD_READ,
    BOOKING_RECORD_UPDATE,
    BOOKING_ROOM_ASSIGN,
    BOOKING_STAY_CHECKIN,
    BOOKING_STAY_CHECKOUT,
    CANONICAL_CAPABILITIES,
    CHAT_ATTACHMENT_DELETE,
    CHAT_ATTACHMENT_UPLOAD,
    CHAT_CONVERSATION_ASSIGN,
    CHAT_CONVERSATION_READ,
    CHAT_GUEST_RESPOND,
    CHAT_MESSAGE_MODERATE,
    CHAT_MESSAGE_SEND,
    CHAT_MODULE_VIEW,
    GUEST_RECORD_READ,
    GUEST_RECORD_UPDATE,
    HOTEL_INFO_CATEGORY_MANAGE,
    HOTEL_INFO_CATEGORY_READ,
    HOTEL_INFO_ENTRY_CREATE,
    HOTEL_INFO_ENTRY_DELETE,
    HOTEL_INFO_ENTRY_READ,
    HOTEL_INFO_ENTRY_UPDATE,
    HOTEL_INFO_MODULE_VIEW,
    HOTEL_INFO_QR_GENERATE,
    HOTEL_INFO_QR_READ,
    HOUSEKEEPING_DASHBOARD_READ,
    HOUSEKEEPING_MODULE_VIEW,
    HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
    HOUSEKEEPING_ROOM_STATUS_HISTORY_READ,
    HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    HOUSEKEEPING_ROOM_STATUS_TRANSITION,
    HOUSEKEEPING_TASK_ASSIGN,
    HOUSEKEEPING_TASK_CANCEL,
    HOUSEKEEPING_TASK_CREATE,
    HOUSEKEEPING_TASK_DELETE,
    HOUSEKEEPING_TASK_EXECUTE,
    HOUSEKEEPING_TASK_READ,
    HOUSEKEEPING_TASK_UPDATE,
    MAINTENANCE_COMMENT_CREATE,
    MAINTENANCE_COMMENT_MODERATE,
    MAINTENANCE_MODULE_VIEW,
    MAINTENANCE_PHOTO_DELETE,
    MAINTENANCE_PHOTO_UPLOAD,
    MAINTENANCE_REQUEST_ACCEPT,
    MAINTENANCE_REQUEST_CLOSE,
    MAINTENANCE_REQUEST_CREATE,
    MAINTENANCE_REQUEST_DELETE,
    MAINTENANCE_REQUEST_READ,
    MAINTENANCE_REQUEST_REASSIGN,
    MAINTENANCE_REQUEST_REOPEN,
    MAINTENANCE_REQUEST_RESOLVE,
    MAINTENANCE_REQUEST_UPDATE,
    ROOM_CHECKOUT_BULK,
    ROOM_CHECKOUT_DESTRUCTIVE,
    ROOM_INSPECTION_PERFORM,
    ROOM_INVENTORY_CREATE,
    ROOM_INVENTORY_DELETE,
    ROOM_INVENTORY_UPDATE,
    ROOM_MAINTENANCE_CLEAR,
    ROOM_MAINTENANCE_FLAG,
    ROOM_MEDIA_MANAGE,
    ROOM_MODULE_VIEW,
    ROOM_OUT_OF_ORDER_SET,
    ROOM_INVENTORY_READ,
    ROOM_STATUS_READ,
    ROOM_STATUS_TRANSITION,
    ROOM_TYPE_MANAGE,
    STAFF_CHAT_ATTACHMENT_DELETE,
    STAFF_CHAT_ATTACHMENT_UPLOAD,
    STAFF_CHAT_CONVERSATION_CREATE,
    STAFF_CHAT_CONVERSATION_DELETE,
    STAFF_CHAT_CONVERSATION_MODERATE,
    STAFF_CHAT_CONVERSATION_READ,
    STAFF_CHAT_MESSAGE_SEND,
    STAFF_CHAT_MODULE_VIEW,
    STAFF_CHAT_REACTION_MANAGE,
    STAFF_MANAGEMENT_AUTHORITY_ACCESS_LEVEL_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_DEPARTMENT_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_NAV_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_ROLE_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_SUPERVISE,
    STAFF_MANAGEMENT_AUTHORITY_VIEW,
    STAFF_MANAGEMENT_DEPARTMENT_MANAGE,
    STAFF_MANAGEMENT_DEPARTMENT_READ,
    STAFF_MANAGEMENT_MODULE_VIEW,
    STAFF_MANAGEMENT_PENDING_REGISTRATION_READ,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_CREATE,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_EMAIL,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_PRINT,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_READ,
    STAFF_MANAGEMENT_ROLE_MANAGE,
    STAFF_MANAGEMENT_ROLE_READ,
    STAFF_MANAGEMENT_STAFF_CREATE,
    STAFF_MANAGEMENT_STAFF_DEACTIVATE,
    STAFF_MANAGEMENT_STAFF_DELETE,
    STAFF_MANAGEMENT_STAFF_READ,
    STAFF_MANAGEMENT_STAFF_UPDATE_PROFILE,
    STAFF_MANAGEMENT_USER_READ,
)


# ---------------------------------------------------------------------------
# Module → policy shape
# ---------------------------------------------------------------------------

BOOKINGS_ACTIONS: dict[str, str] = {
    # Operate bucket
    'update': BOOKING_RECORD_UPDATE,
    'cancel': BOOKING_RECORD_CANCEL,
    'assign_room': BOOKING_ROOM_ASSIGN,
    'checkin': BOOKING_STAY_CHECKIN,
    'checkout': BOOKING_STAY_CHECKOUT,
    'communicate': BOOKING_GUEST_COMMUNICATE,
    # Supervise bucket — all override-style actions share one capability.
    'override_conflicts': BOOKING_OVERRIDE_SUPERVISE,
    'force_checkin': BOOKING_OVERRIDE_SUPERVISE,
    'force_checkout': BOOKING_OVERRIDE_SUPERVISE,
    'resolve_overstay': BOOKING_OVERRIDE_SUPERVISE,
    'modify_locked': BOOKING_OVERRIDE_SUPERVISE,
    'extend': BOOKING_OVERRIDE_SUPERVISE,
    # Manage bucket
    'manage_rules': BOOKING_CONFIG_MANAGE,
}

MODULE_POLICY: dict[str, dict] = {
    'bookings': {
        'view_capability': BOOKING_MODULE_VIEW,
        'read_capability': BOOKING_RECORD_READ,
        'actions': BOOKINGS_ACTIONS,
    },
    'chat': {
        'view_capability': CHAT_MODULE_VIEW,
        'read_capability': CHAT_CONVERSATION_READ,
        'actions': {
            'conversation_read': CHAT_CONVERSATION_READ,
            'message_send': CHAT_MESSAGE_SEND,
            'message_moderate': CHAT_MESSAGE_MODERATE,
            'attachment_upload': CHAT_ATTACHMENT_UPLOAD,
            'attachment_delete': CHAT_ATTACHMENT_DELETE,
            'conversation_assign': CHAT_CONVERSATION_ASSIGN,
            'guest_respond': CHAT_GUEST_RESPOND,
        },
    },
    'guests': {
        'view_capability': GUEST_RECORD_READ,
        'read_capability': GUEST_RECORD_READ,
        'actions': {
            'update': GUEST_RECORD_UPDATE,
        },
    },
    'hotel_info': {
        'view_capability': HOTEL_INFO_MODULE_VIEW,
        'read_capability': HOTEL_INFO_ENTRY_READ,
        'actions': {
            'entry_read': HOTEL_INFO_ENTRY_READ,
            'entry_create': HOTEL_INFO_ENTRY_CREATE,
            'entry_update': HOTEL_INFO_ENTRY_UPDATE,
            'entry_delete': HOTEL_INFO_ENTRY_DELETE,
            'category_read': HOTEL_INFO_CATEGORY_READ,
            'category_manage': HOTEL_INFO_CATEGORY_MANAGE,
            'qr_read': HOTEL_INFO_QR_READ,
            'qr_generate': HOTEL_INFO_QR_GENERATE,
        },
    },
    'rooms': {
        'view_capability': ROOM_MODULE_VIEW,
        'read_capability': ROOM_INVENTORY_READ,
        'actions': {
            # Manage bucket
            'inventory_create': ROOM_INVENTORY_CREATE,
            'inventory_update': ROOM_INVENTORY_UPDATE,
            'inventory_delete': ROOM_INVENTORY_DELETE,
            'type_manage': ROOM_TYPE_MANAGE,
            'media_manage': ROOM_MEDIA_MANAGE,
            'out_of_order_set': ROOM_OUT_OF_ORDER_SET,
            'checkout_destructive': ROOM_CHECKOUT_DESTRUCTIVE,
            # Operate bucket
            'status_transition': ROOM_STATUS_TRANSITION,
            'maintenance_flag': ROOM_MAINTENANCE_FLAG,
            # Supervise bucket
            'inspect': ROOM_INSPECTION_PERFORM,
            'maintenance_clear': ROOM_MAINTENANCE_CLEAR,
            'checkout_bulk': ROOM_CHECKOUT_BULK,
        },
    },
    'staff_chat': {
        'view_capability': STAFF_CHAT_MODULE_VIEW,
        'read_capability': STAFF_CHAT_CONVERSATION_READ,
        'actions': {
            'conversation_read': STAFF_CHAT_CONVERSATION_READ,
            'conversation_create': STAFF_CHAT_CONVERSATION_CREATE,
            'conversation_delete': STAFF_CHAT_CONVERSATION_DELETE,
            'message_send': STAFF_CHAT_MESSAGE_SEND,
            'message_moderate': STAFF_CHAT_CONVERSATION_MODERATE,
            'attachment_upload': STAFF_CHAT_ATTACHMENT_UPLOAD,
            'attachment_delete': STAFF_CHAT_ATTACHMENT_DELETE,
            'reaction_manage': STAFF_CHAT_REACTION_MANAGE,
        },
    },
    'housekeeping': {
        'view_capability': HOUSEKEEPING_MODULE_VIEW,
        'read_capability': HOUSEKEEPING_TASK_READ,
        'actions': {
            'dashboard_read': HOUSEKEEPING_DASHBOARD_READ,
            'task_create': HOUSEKEEPING_TASK_CREATE,
            'task_update': HOUSEKEEPING_TASK_UPDATE,
            'task_delete': HOUSEKEEPING_TASK_DELETE,
            'task_assign': HOUSEKEEPING_TASK_ASSIGN,
            'task_execute': HOUSEKEEPING_TASK_EXECUTE,
            'task_cancel': HOUSEKEEPING_TASK_CANCEL,
            'status_transition': HOUSEKEEPING_ROOM_STATUS_TRANSITION,
            'status_front_desk': HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
            'status_override': HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
            'status_history_read': HOUSEKEEPING_ROOM_STATUS_HISTORY_READ,
        },
    },
    'maintenance': {
        'view_capability': MAINTENANCE_MODULE_VIEW,
        'read_capability': MAINTENANCE_REQUEST_READ,
        'actions': {
            'request_create': MAINTENANCE_REQUEST_CREATE,
            'request_accept': MAINTENANCE_REQUEST_ACCEPT,
            'request_resolve': MAINTENANCE_REQUEST_RESOLVE,
            'request_update': MAINTENANCE_REQUEST_UPDATE,
            'request_reassign': MAINTENANCE_REQUEST_REASSIGN,
            'request_reopen': MAINTENANCE_REQUEST_REOPEN,
            'request_close': MAINTENANCE_REQUEST_CLOSE,
            'request_delete': MAINTENANCE_REQUEST_DELETE,
            'comment_create': MAINTENANCE_COMMENT_CREATE,
            'comment_moderate': MAINTENANCE_COMMENT_MODERATE,
            'photo_upload': MAINTENANCE_PHOTO_UPLOAD,
            'photo_delete': MAINTENANCE_PHOTO_DELETE,
        },
    },
    'staff_management': {
        'view_capability': STAFF_MANAGEMENT_MODULE_VIEW,
        'read_capability': STAFF_MANAGEMENT_STAFF_READ,
        'actions': {
            'staff_read': STAFF_MANAGEMENT_STAFF_READ,
            'user_read': STAFF_MANAGEMENT_USER_READ,
            'pending_registration_read': (
                STAFF_MANAGEMENT_PENDING_REGISTRATION_READ
            ),

            'staff_create': STAFF_MANAGEMENT_STAFF_CREATE,
            'staff_update_profile': STAFF_MANAGEMENT_STAFF_UPDATE_PROFILE,
            'staff_deactivate': STAFF_MANAGEMENT_STAFF_DEACTIVATE,
            'staff_delete': STAFF_MANAGEMENT_STAFF_DELETE,

            'authority_view': STAFF_MANAGEMENT_AUTHORITY_VIEW,
            'authority_role_assign': (
                STAFF_MANAGEMENT_AUTHORITY_ROLE_ASSIGN
            ),
            'authority_department_assign': (
                STAFF_MANAGEMENT_AUTHORITY_DEPARTMENT_ASSIGN
            ),
            'authority_access_level_assign': (
                STAFF_MANAGEMENT_AUTHORITY_ACCESS_LEVEL_ASSIGN
            ),
            'authority_nav_assign': STAFF_MANAGEMENT_AUTHORITY_NAV_ASSIGN,
            'authority_supervise': STAFF_MANAGEMENT_AUTHORITY_SUPERVISE,

            'role_read': STAFF_MANAGEMENT_ROLE_READ,
            'role_manage': STAFF_MANAGEMENT_ROLE_MANAGE,
            'department_read': STAFF_MANAGEMENT_DEPARTMENT_READ,
            'department_manage': STAFF_MANAGEMENT_DEPARTMENT_MANAGE,

            'registration_package_read': (
                STAFF_MANAGEMENT_REGISTRATION_PACKAGE_READ
            ),
            'registration_package_create': (
                STAFF_MANAGEMENT_REGISTRATION_PACKAGE_CREATE
            ),
            'registration_package_email': (
                STAFF_MANAGEMENT_REGISTRATION_PACKAGE_EMAIL
            ),
            'registration_package_print': (
                STAFF_MANAGEMENT_REGISTRATION_PACKAGE_PRINT
            ),
        },
    },
}


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

def resolve_module_policy(
    allowed_capabilities: Iterable[str] | None,
) -> dict:
    """
    Compute the normalized RBAC policy object from a resolved capability set.

    Input is the ``allowed_capabilities`` list emitted by
    ``resolve_effective_access``. Output shape:

        {
          "bookings": {
            "visible": bool,
            "read": bool,
            "actions": {
              "<action>": bool,
              ...
            }
          },
          ...
        }

    Fail-closed:
    - ``None`` / empty input → every flag is ``False``.
    - Actions whose capability isn't in ``CANONICAL_CAPABILITIES`` are
      emitted as ``False`` (drift protection).
    """
    caps = set(allowed_capabilities or [])
    out: dict[str, dict] = {}

    for module, policy in MODULE_POLICY.items():
        view_cap = policy['view_capability']
        read_cap = policy['read_capability']
        actions_map: Mapping[str, str] = policy['actions']

        actions = {
            action: (
                cap in caps and cap in CANONICAL_CAPABILITIES
            )
            for action, cap in actions_map.items()
        }

        out[module] = {
            'visible': (
                view_cap in caps and view_cap in CANONICAL_CAPABILITIES
            ),
            'read': (
                read_cap in caps and read_cap in CANONICAL_CAPABILITIES
            ),
            'actions': actions,
        }

    return out


def validate_module_policy() -> list[str]:
    """
    Return a list of validation errors in the module policy registry.

    Empty list means every capability referenced by the registry is
    canonical. Used by tests / management checks.
    """
    errors: list[str] = []
    for module, policy in MODULE_POLICY.items():
        for key in ('view_capability', 'read_capability'):
            cap = policy.get(key)
            if cap and cap not in CANONICAL_CAPABILITIES:
                errors.append(
                    f"MODULE_POLICY[{module!r}].{key} references unknown "
                    f"capability {cap!r}"
                )
        for action, cap in policy.get('actions', {}).items():
            if cap not in CANONICAL_CAPABILITIES:
                errors.append(
                    f"MODULE_POLICY[{module!r}].actions[{action!r}] "
                    f"references unknown capability {cap!r}"
                )
    return errors
