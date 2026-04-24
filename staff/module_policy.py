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
