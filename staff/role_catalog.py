"""
Canonical role catalog for HotelMate (Phase 5c).

This module is the SINGLE SOURCE OF TRUTH for:
- CANONICAL_ROLES: the complete canonical role set every hotel must have
- CANONICAL_ROLE_SLUGS: whitelist of allowed role slugs
- ROLE_DEPARTMENT_SLUG: role.slug -> department.slug mapping
- LEGACY_ROLE_REMAP: legacy role.slug -> canonical role.slug reassignment
- SLUG_PATTERN: regex enforced in Role.clean()

Roles are **pure preset data**. They do not drive enforcement — the
capability catalog does. See staff/capability_catalog.py.

All consumers (seeders, migrations, validators, Role.clean) MUST import
from here. Do NOT redefine these constants elsewhere.
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Canonical roles. Tier alignment is semantic only:
#   staff      -> regular_staff
#   supervisor -> staff_admin
#   manager    -> super_staff_admin
# ---------------------------------------------------------------------------

CANONICAL_ROLES: list[dict[str, str]] = [
    # Front Office
    {'slug': 'front_desk_agent', 'name': 'Front Desk Agent',
     'department_slug': 'front_office',
     'description': 'Front desk check-in/out, guest requests, room status (FOH).'},
    {'slug': 'front_office_supervisor', 'name': 'Front Office Supervisor',
     'department_slug': 'front_office',
     'description': 'Shift lead over front desk agents.'},
    {'slug': 'front_office_manager', 'name': 'Front Office Manager',
     'department_slug': 'front_office',
     'description': 'Manages front office operations.'},

    # Housekeeping
    {'slug': 'housekeeper', 'name': 'Housekeeper',
     'department_slug': 'housekeeping',
     'description': 'Room attendant; executes housekeeping room workflow.'},
    {'slug': 'housekeeping_supervisor', 'name': 'Housekeeping Supervisor',
     'department_slug': 'housekeeping',
     'description': 'Inspects rooms and supervises housekeepers.'},
    {'slug': 'housekeeping_manager', 'name': 'Housekeeping Manager',
     'department_slug': 'housekeeping',
     'description': 'Manages housekeeping operations.'},

    # Food & Beverage
    {'slug': 'waiter', 'name': 'Waiter',
     'department_slug': 'food_beverage',
     'description': 'Restaurant / bar floor service.'},
    {'slug': 'fb_supervisor', 'name': 'F&B Supervisor',
     'department_slug': 'food_beverage',
     'description': 'Shift lead over the F&B floor.'},
    {'slug': 'fnb_manager', 'name': 'F&B Manager',
     'department_slug': 'food_beverage',
     'description': 'Manages F&B operations.'},

    # Kitchen
    {'slug': 'kitchen_staff', 'name': 'Kitchen Staff',
     'department_slug': 'kitchen',
     'description': 'Line cooks, prep, kitchen porters.'},
    {'slug': 'kitchen_supervisor', 'name': 'Kitchen Supervisor',
     'department_slug': 'kitchen',
     'description': 'Sous chef / shift lead over kitchen staff.'},
    {'slug': 'kitchen_manager', 'name': 'Kitchen Manager',
     'department_slug': 'kitchen',
     'description': 'Head chef / kitchen manager.'},

    # Maintenance
    {'slug': 'maintenance_staff', 'name': 'Maintenance Staff',
     'department_slug': 'maintenance',
     'description': 'Technicians and repairs.'},
    {'slug': 'maintenance_supervisor', 'name': 'Maintenance Supervisor',
     'department_slug': 'maintenance',
     'description': 'Shift lead over maintenance staff.'},
    {'slug': 'maintenance_manager', 'name': 'Maintenance Manager',
     'department_slug': 'maintenance',
     'description': 'Manages maintenance operations.'},

    # Guest Relations
    {'slug': 'guest_relations_agent', 'name': 'Guest Relations Agent',
     'department_slug': 'guest_relations',
     'description': 'Guest experience, VIP handling, complaints.'},
    {'slug': 'guest_relations_supervisor', 'name': 'Guest Relations Supervisor',
     'department_slug': 'guest_relations',
     'description': 'Shift lead over guest relations agents.'},
    {'slug': 'guest_relations_manager', 'name': 'Guest Relations Manager',
     'department_slug': 'guest_relations',
     'description': 'Manages guest relations operations.'},

    # Management
    {'slug': 'duty_manager', 'name': 'Duty Manager',
     'department_slug': 'management',
     'description': 'Manager on duty across departments.'},
    {'slug': 'hotel_manager', 'name': 'Hotel Manager',
     'department_slug': 'management',
     'description': 'Hotel general manager.'},

    # Administration
    {'slug': 'operations_admin', 'name': 'Operations Admin',
     'department_slug': 'administration',
     'description': 'Back office operations administrator.'},
]

CANONICAL_ROLE_SLUGS: frozenset[str] = frozenset(
    r['slug'] for r in CANONICAL_ROLES
)

ROLE_DEPARTMENT_SLUG: dict[str, str] = {
    r['slug']: r['department_slug'] for r in CANONICAL_ROLES
}


# ---------------------------------------------------------------------------
# Slug policy.
#
# Allowed shapes:
#   - hotel_manager          (special-case flat slug)
#   - <department>_<role>    (snake_case, underscore-separated, 2+ tokens)
#
# Rejected:
#   - manager
#   - admin
#   - random / single-token slugs
#   - kebab-case or mixed case
#
# The Role.clean() method enforces this pattern AND requires the slug to be
# a member of CANONICAL_ROLE_SLUGS (strict whitelist). The regex is kept as
# a second layer so accidental data loads that bypass the whitelist at the
# very least fail on shape.
# ---------------------------------------------------------------------------

SLUG_PATTERN = re.compile(r'^(?:hotel_manager|[a-z]+(?:_[a-z]+)+)$')


# ---------------------------------------------------------------------------
# Legacy role slug remap.
#
# Used by the data migration to reassign Staff.role before legacy rows are
# deleted. For `manager`, the canonical replacement depends on the current
# department — see resolve_legacy_manager_target().
# ---------------------------------------------------------------------------

LEGACY_ROLE_SLUGS: frozenset[str] = frozenset({
    'manager',
    'admin',
    'receptionist',
    'porter',
    'housekeeping',
})

# Flat 1:1 remaps (department-independent).
LEGACY_ROLE_REMAP: dict[str, str] = {
    'admin': 'operations_admin',
    'receptionist': 'front_desk_agent',
    'porter': 'front_desk_agent',
    'housekeeping': 'housekeeper',
}

# manager -> department-scoped manager canonical slug.
_MANAGER_BY_DEPT: dict[str, str] = {
    'front_office': 'front_office_manager',
    'housekeeping': 'housekeeping_manager',
    'food_beverage': 'fnb_manager',
    'kitchen': 'kitchen_manager',
    'maintenance': 'maintenance_manager',
    'guest_relations': 'guest_relations_manager',
    'management': 'hotel_manager',
    'administration': 'operations_admin',
}


def resolve_legacy_manager_target(department_slug: str | None) -> str:
    """Return the canonical role slug that replaces a legacy `manager` role
    given the legacy role's department slug. Falls back to `hotel_manager`
    when the department is missing or unmapped."""
    if not department_slug:
        return 'hotel_manager'
    return _MANAGER_BY_DEPT.get(department_slug, 'hotel_manager')


def resolve_legacy_remap(
    legacy_slug: str,
    department_slug: str | None,
) -> str | None:
    """Return the canonical role slug that should replace `legacy_slug`,
    or None if the slug is not a known legacy slug."""
    if legacy_slug == 'manager':
        return resolve_legacy_manager_target(department_slug)
    return LEGACY_ROLE_REMAP.get(legacy_slug)
