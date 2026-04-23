"""
Canonical department catalog for HotelMate.

This module is the SINGLE SOURCE OF TRUTH for:
- CANONICAL_DEPARTMENTS: the 8 canonical departments every hotel must have
- CANONICAL_DEPARTMENT_SLUGS: the set of valid canonical department slugs
- DEPARTMENT_SLUG_ALIASES: legacy (kebab-case) → canonical (snake_case)

All consumers (seeders, migrations, validators, permission code) MUST import
from here. Do NOT redefine these constants elsewhere.

Canonical roles live in staff/role_catalog.py.

Source: hotelmates_auth_contract_v1.md and Phase 3 role migration audit.
"""

# ---------------------------------------------------------------------------
# Canonical departments (8). Every hotel must have all of these, even if
# some are unused. Zero-department hotels block the whole RBAC model.
# ---------------------------------------------------------------------------

CANONICAL_DEPARTMENTS = [
    {
        'slug': 'front_office',
        'name': 'Front Office',
        'description': 'Reception, porters, night audit, concierge.',
    },
    {
        'slug': 'housekeeping',
        'name': 'Housekeeping',
        'description': 'Room attendants, housekeeping supervisors.',
    },
    {
        'slug': 'food_beverage',
        'name': 'Food & Beverage',
        'description': (
            'Guest-facing FOH / service side: waiters, bar, restaurant floor.'
        ),
    },
    {
        'slug': 'kitchen',
        'name': 'Kitchen',
        'description': 'BOH culinary: chefs, line cooks, kitchen porters.',
    },
    {
        'slug': 'maintenance',
        'name': 'Maintenance',
        'description': 'Technical, engineering, repairs.',
    },
    {
        'slug': 'guest_relations',
        'name': 'Guest Relations',
        'description': 'Guest experience, VIP handling, complaints.',
    },
    {
        'slug': 'management',
        'name': 'Management',
        'description': 'Department managers and GMs.',
    },
    {
        'slug': 'administration',
        'name': 'Administration',
        'description': 'Back office: HR, finance, admin.',
    },
]

CANONICAL_DEPARTMENT_SLUGS = frozenset(
    d['slug'] for d in CANONICAL_DEPARTMENTS
)

# ---------------------------------------------------------------------------
# Legacy kebab-case → canonical snake_case slug aliases.
# Used by the normalization migration and by any runtime lookup that must
# tolerate pre-normalization data while it's being rolled out.
# ---------------------------------------------------------------------------

DEPARTMENT_SLUG_ALIASES = {
    'food-and-beverage': 'food_beverage',
    'front-office': 'front_office',
}


def canonicalize_department_slug(slug: str) -> str:
    """Return the canonical slug for a (possibly legacy) department slug."""
    if not slug:
        return slug
    return DEPARTMENT_SLUG_ALIASES.get(slug, slug)
