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
    ATTENDANCE_ANALYTICS_READ,
    ATTENDANCE_BREAK_TOGGLE,
    ATTENDANCE_CLOCK_IN_OUT,
    ATTENDANCE_DAILY_PLAN_ENTRY_MANAGE,
    ATTENDANCE_DAILY_PLAN_MANAGE,
    ATTENDANCE_DAILY_PLAN_READ,
    ATTENDANCE_FACE_AUDIT_READ,
    ATTENDANCE_FACE_READ,
    ATTENDANCE_FACE_REGISTER_OTHER,
    ATTENDANCE_FACE_REGISTER_SELF,
    ATTENDANCE_FACE_REVOKE,
    ATTENDANCE_LOG_APPROVE,
    ATTENDANCE_LOG_CREATE,
    ATTENDANCE_LOG_DELETE,
    ATTENDANCE_LOG_READ_ALL,
    ATTENDANCE_LOG_READ_SELF,
    ATTENDANCE_LOG_REJECT,
    ATTENDANCE_LOG_RELINK,
    ATTENDANCE_LOG_UPDATE,
    ATTENDANCE_MODULE_VIEW,
    ATTENDANCE_PERIOD_CREATE,
    ATTENDANCE_PERIOD_DELETE,
    ATTENDANCE_PERIOD_FINALIZE,
    ATTENDANCE_PERIOD_FORCE_FINALIZE,
    ATTENDANCE_PERIOD_READ,
    ATTENDANCE_PERIOD_UNFINALIZE,
    ATTENDANCE_PERIOD_UPDATE,
    ATTENDANCE_ROSTER_READ_SELF,
    ATTENDANCE_SHIFT_BULK_WRITE,
    ATTENDANCE_SHIFT_COPY,
    ATTENDANCE_SHIFT_CREATE,
    ATTENDANCE_SHIFT_DELETE,
    ATTENDANCE_SHIFT_EXPORT_PDF,
    ATTENDANCE_SHIFT_LOCATION_MANAGE,
    ATTENDANCE_SHIFT_LOCATION_READ,
    ATTENDANCE_SHIFT_READ,
    ATTENDANCE_SHIFT_UPDATE,
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
    ROOM_SERVICE_BREAKFAST_ORDER_ACCEPT,
    ROOM_SERVICE_BREAKFAST_ORDER_COMPLETE,
    ROOM_SERVICE_BREAKFAST_ORDER_CREATE,
    ROOM_SERVICE_BREAKFAST_ORDER_DELETE,
    ROOM_SERVICE_BREAKFAST_ORDER_READ,
    ROOM_SERVICE_BREAKFAST_ORDER_UPDATE,
    ROOM_SERVICE_MENU_ITEM_CREATE,
    ROOM_SERVICE_MENU_ITEM_DELETE,
    ROOM_SERVICE_MENU_ITEM_IMAGE_MANAGE,
    ROOM_SERVICE_MENU_ITEM_UPDATE,
    ROOM_SERVICE_MENU_READ,
    ROOM_SERVICE_MODULE_VIEW,
    ROOM_SERVICE_ORDER_ACCEPT,
    ROOM_SERVICE_ORDER_COMPLETE,
    ROOM_SERVICE_ORDER_CREATE,
    ROOM_SERVICE_ORDER_DELETE,
    ROOM_SERVICE_ORDER_READ,
    ROOM_SERVICE_ORDER_UPDATE,
    RESTAURANT_BOOKING_ASSIGNMENT_ASSIGN,
    RESTAURANT_BOOKING_ASSIGNMENT_UNSEAT,
    RESTAURANT_BOOKING_BLUEPRINT_MANAGE,
    RESTAURANT_BOOKING_BLUEPRINT_READ,
    RESTAURANT_BOOKING_CATEGORY_MANAGE,
    RESTAURANT_BOOKING_CATEGORY_READ,
    RESTAURANT_BOOKING_MODULE_VIEW,
    RESTAURANT_BOOKING_RECORD_CREATE,
    RESTAURANT_BOOKING_RECORD_DELETE,
    RESTAURANT_BOOKING_RECORD_MARK_SEEN,
    RESTAURANT_BOOKING_RECORD_READ,
    RESTAURANT_BOOKING_RECORD_UPDATE,
    RESTAURANT_BOOKING_RESTAURANT_CREATE,
    RESTAURANT_BOOKING_RESTAURANT_DELETE,
    RESTAURANT_BOOKING_RESTAURANT_READ,
    RESTAURANT_BOOKING_RESTAURANT_UPDATE,
    RESTAURANT_BOOKING_TABLE_MANAGE,
    RESTAURANT_BOOKING_TABLE_READ,
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
    'attendance': {
        'view_capability': ATTENDANCE_MODULE_VIEW,
        'read_capability': ATTENDANCE_LOG_READ_SELF,
        'actions': {
            'clock_in_out': ATTENDANCE_CLOCK_IN_OUT,
            'break_toggle': ATTENDANCE_BREAK_TOGGLE,
            'log_read_self': ATTENDANCE_LOG_READ_SELF,
            'log_read_all': ATTENDANCE_LOG_READ_ALL,
            'log_create': ATTENDANCE_LOG_CREATE,
            'log_update': ATTENDANCE_LOG_UPDATE,
            'log_delete': ATTENDANCE_LOG_DELETE,
            'log_approve': ATTENDANCE_LOG_APPROVE,
            'log_reject': ATTENDANCE_LOG_REJECT,
            'log_relink': ATTENDANCE_LOG_RELINK,
            'analytics_read': ATTENDANCE_ANALYTICS_READ,
            'period_read': ATTENDANCE_PERIOD_READ,
            'period_create': ATTENDANCE_PERIOD_CREATE,
            'period_update': ATTENDANCE_PERIOD_UPDATE,
            'period_delete': ATTENDANCE_PERIOD_DELETE,
            'period_finalize': ATTENDANCE_PERIOD_FINALIZE,
            'period_unfinalize': ATTENDANCE_PERIOD_UNFINALIZE,
            'period_force_finalize': ATTENDANCE_PERIOD_FORCE_FINALIZE,
            'shift_read': ATTENDANCE_SHIFT_READ,
            'shift_create': ATTENDANCE_SHIFT_CREATE,
            'shift_update': ATTENDANCE_SHIFT_UPDATE,
            'shift_delete': ATTENDANCE_SHIFT_DELETE,
            'shift_bulk_write': ATTENDANCE_SHIFT_BULK_WRITE,
            'shift_copy': ATTENDANCE_SHIFT_COPY,
            'shift_export_pdf': ATTENDANCE_SHIFT_EXPORT_PDF,
            'shift_location_read': ATTENDANCE_SHIFT_LOCATION_READ,
            'shift_location_manage': ATTENDANCE_SHIFT_LOCATION_MANAGE,
            'daily_plan_read': ATTENDANCE_DAILY_PLAN_READ,
            'daily_plan_manage': ATTENDANCE_DAILY_PLAN_MANAGE,
            'daily_plan_entry_manage': ATTENDANCE_DAILY_PLAN_ENTRY_MANAGE,
            'face_read': ATTENDANCE_FACE_READ,
            'face_register_self': ATTENDANCE_FACE_REGISTER_SELF,
            'face_register_other': ATTENDANCE_FACE_REGISTER_OTHER,
            'face_revoke': ATTENDANCE_FACE_REVOKE,
            'face_audit_read': ATTENDANCE_FACE_AUDIT_READ,
            'roster_read_self': ATTENDANCE_ROSTER_READ_SELF,
        },
    },
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
    'room_services': {
        'view_capability': ROOM_SERVICE_MODULE_VIEW,
        'read_capability': ROOM_SERVICE_ORDER_READ,
        'actions': {
            # Menu (catalog) bucket
            'menu_read': ROOM_SERVICE_MENU_READ,
            'menu_item_create': ROOM_SERVICE_MENU_ITEM_CREATE,
            'menu_item_update': ROOM_SERVICE_MENU_ITEM_UPDATE,
            'menu_item_delete': ROOM_SERVICE_MENU_ITEM_DELETE,
            'menu_item_image_manage': ROOM_SERVICE_MENU_ITEM_IMAGE_MANAGE,
            # Order bucket
            'order_read': ROOM_SERVICE_ORDER_READ,
            'order_create': ROOM_SERVICE_ORDER_CREATE,
            'order_update': ROOM_SERVICE_ORDER_UPDATE,
            'order_delete': ROOM_SERVICE_ORDER_DELETE,
            'order_accept': ROOM_SERVICE_ORDER_ACCEPT,
            'order_complete': ROOM_SERVICE_ORDER_COMPLETE,
            # Breakfast order bucket
            'breakfast_order_read': ROOM_SERVICE_BREAKFAST_ORDER_READ,
            'breakfast_order_create': ROOM_SERVICE_BREAKFAST_ORDER_CREATE,
            'breakfast_order_update': ROOM_SERVICE_BREAKFAST_ORDER_UPDATE,
            'breakfast_order_delete': ROOM_SERVICE_BREAKFAST_ORDER_DELETE,
            'breakfast_order_accept': ROOM_SERVICE_BREAKFAST_ORDER_ACCEPT,
            'breakfast_order_complete': (
                ROOM_SERVICE_BREAKFAST_ORDER_COMPLETE
            ),
        },
    },
    'restaurant_bookings': {
        'view_capability': RESTAURANT_BOOKING_MODULE_VIEW,
        'read_capability': RESTAURANT_BOOKING_RECORD_READ,
        'actions': {
            # Restaurant catalog
            'restaurant_read': RESTAURANT_BOOKING_RESTAURANT_READ,
            'restaurant_create': RESTAURANT_BOOKING_RESTAURANT_CREATE,
            'restaurant_update': RESTAURANT_BOOKING_RESTAURANT_UPDATE,
            'restaurant_delete': RESTAURANT_BOOKING_RESTAURANT_DELETE,
            # Booking categories
            'category_read': RESTAURANT_BOOKING_CATEGORY_READ,
            'category_manage': RESTAURANT_BOOKING_CATEGORY_MANAGE,
            # Booking records
            'record_read': RESTAURANT_BOOKING_RECORD_READ,
            'record_create': RESTAURANT_BOOKING_RECORD_CREATE,
            'record_update': RESTAURANT_BOOKING_RECORD_UPDATE,
            'record_delete': RESTAURANT_BOOKING_RECORD_DELETE,
            'record_mark_seen': RESTAURANT_BOOKING_RECORD_MARK_SEEN,
            # Dining tables
            'table_read': RESTAURANT_BOOKING_TABLE_READ,
            'table_manage': RESTAURANT_BOOKING_TABLE_MANAGE,
            # Restaurant blueprints
            'blueprint_read': RESTAURANT_BOOKING_BLUEPRINT_READ,
            'blueprint_manage': RESTAURANT_BOOKING_BLUEPRINT_MANAGE,
            # Booking-to-table assignments
            'assignment_assign': RESTAURANT_BOOKING_ASSIGNMENT_ASSIGN,
            'assignment_unseat': RESTAURANT_BOOKING_ASSIGNMENT_UNSEAT,
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
