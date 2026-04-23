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
        'description': (
            'Central hub managing arrivals, departures, guest '
            'communication, reservations, and real-time coordination '
            'across hotel operations.'
        ),
    },
    {
        'slug': 'housekeeping',
        'name': 'Housekeeping',
        'description': (
            'Room attendants and housekeeping supervisors responsible '
            'for room readiness, cleanliness, and housekeeping workflow '
            'execution.'
        ),
    },
    {
        'slug': 'food_beverage',
        'name': 'Food & Beverage',
        'description': (
            'Guest-facing food and beverage operations including '
            'restaurant, bar, room service, and service-floor '
            'coordination.'
        ),
    },
    {
        'slug': 'kitchen',
        'name': 'Kitchen',
        'description': (
            'Back-of-house culinary operations including chefs, line '
            'cooks, prep, and kitchen support staff.'
        ),
    },
    {
        'slug': 'maintenance',
        'name': 'Maintenance',
        'description': (
            'Technical operations, engineering, repairs, inspections, '
            'and maintenance response workflows.'
        ),
    },
    {
        'slug': 'guest_relations',
        'name': 'Guest Relations',
        'description': (
            'Guest experience management including VIP handling, '
            'complaints, special requests, and satisfaction follow-up.'
        ),
    },
    {
        'slug': 'management',
        'name': 'Management',
        'description': (
            'Operational leadership roles responsible for oversight, '
            'escalation handling, and cross-department coordination.'
        ),
    },
    {
        'slug': 'administration',
        'name': 'Administration',
        'description': (
            'Back-office administration including HR, finance, '
            'compliance, and operational support functions.'
        ),
    },
]

# Canonical mapping by slug — convenience lookup for normalization
# logic. Slug is identity; name and description must converge here.
CANONICAL_DEPARTMENT_BY_SLUG = {d['slug']: d for d in CANONICAL_DEPARTMENTS}

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
