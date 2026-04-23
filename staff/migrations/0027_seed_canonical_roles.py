"""
Phase 5c — seed canonical roles, reassign staff off legacy slugs,
delete legacy role rows.

Runs against the live Role / Staff tables using historical models:

1. Seed the canonical role set (staff/role_catalog.py::CANONICAL_ROLES)
   for every hotel that has canonical departments. Idempotent; existing
   canonical rows are left untouched.

2. Reassign every Staff.role currently pointing at a legacy role slug
   (manager, admin, receptionist, porter, housekeeping) to the canonical
   target (role_catalog.LEGACY_ROLE_REMAP + resolve_legacy_manager_target).
   Creates the canonical role for the staff's hotel if missing.

3. Delete legacy role rows once no Staff references them.

NOTE: This migration cannot import staff.models (the live model) because
Django data migrations must use apps.get_model. The canonical catalog
constants are imported directly from staff.role_catalog — they are pure
Python data and safe to import.
"""
from django.db import migrations

from staff.role_catalog import (
    CANONICAL_ROLES,
    LEGACY_ROLE_SLUGS,
    resolve_legacy_remap,
)


CANONICAL_BY_SLUG = {r['slug']: r for r in CANONICAL_ROLES}


def _get_or_create_canonical_role(Role, Department, hotel_id, slug):
    """Return the canonical Role row for (hotel, slug), creating it along
    with a (department, name, description) triple sourced from the
    canonical catalog. Returns None if the slug is not canonical or the
    hotel is missing its canonical department."""
    spec = CANONICAL_BY_SLUG.get(slug)
    if spec is None:
        return None

    existing = Role.objects.filter(hotel_id=hotel_id, slug=slug).first()
    if existing is not None:
        return existing

    dept = Department.objects.filter(
        hotel_id=hotel_id, slug=spec['department_slug']
    ).first()
    if dept is None:
        # Hotel is missing the canonical department. The 0025 migration
        # seeded these, so this should not happen — but stay defensive.
        return None

    return Role.objects.create(
        hotel_id=hotel_id,
        department=dept,
        slug=slug,
        name=spec['name'],
        description=spec.get('description', '') or '',
    )


def forwards(apps, schema_editor):
    Hotel = apps.get_model('hotel', 'Hotel')
    Department = apps.get_model('staff', 'Department')
    Role = apps.get_model('staff', 'Role')
    Staff = apps.get_model('staff', 'Staff')

    # ---- Step 1: seed canonical roles for every hotel ----------------
    for hotel in Hotel.objects.all().iterator():
        for spec in CANONICAL_ROLES:
            _get_or_create_canonical_role(
                Role, Department, hotel.id, spec['slug']
            )

    # ---- Step 2: reassign staff off legacy roles ---------------------
    legacy_roles = list(Role.objects.filter(slug__in=LEGACY_ROLE_SLUGS))

    for legacy in legacy_roles:
        dept_slug = legacy.department.slug if legacy.department_id else None
        target_slug = resolve_legacy_remap(legacy.slug, dept_slug)
        if not target_slug:
            continue

        # Figure out which staff rows are pointing at this legacy role.
        affected = Staff.objects.filter(role_id=legacy.id)
        if not affected.exists():
            continue

        # Reassign per-staff: the canonical role must exist on the staff's
        # own hotel (roles are hotel-scoped).
        for staff in affected.iterator():
            canonical = _get_or_create_canonical_role(
                Role, Department, staff.hotel_id, target_slug
            )
            if canonical is None:
                # Hotel is missing canonical department — fall back to
                # hotel_manager for manager-class legacy rows; for others
                # clear the role so the legacy row can be deleted cleanly.
                if legacy.slug == 'manager':
                    canonical = _get_or_create_canonical_role(
                        Role, Department, staff.hotel_id, 'hotel_manager'
                    )
                if canonical is None:
                    Staff.objects.filter(pk=staff.pk).update(role=None)
                    continue

            Staff.objects.filter(pk=staff.pk).update(role=canonical)

    # ---- Step 3: delete legacy role rows (only if orphaned) ----------
    for legacy in Role.objects.filter(slug__in=LEGACY_ROLE_SLUGS):
        if Staff.objects.filter(role_id=legacy.id).exists():
            # Should not happen after Step 2 — leave as-is rather than
            # cascade-deleting staff rows. Surfaces as a failed post-check.
            continue
        legacy.delete()


def backwards(apps, schema_editor):
    # Non-reversible: legacy role slugs are forbidden by the live
    # Role.clean() policy. Re-creating them would violate the canonical
    # catalog. This is a data-only migration; rollback means restoring
    # from backup.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0026_add_slug_not_empty_constraints'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
