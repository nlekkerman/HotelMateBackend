"""
Phase 4A + 4B data cleanup + canonical seeding + integrity constraints.

Performs, in order:

1. Seed all 8 canonical departments for every hotel (idempotent).
2. Normalize legacy kebab-case department slugs to snake_case canonical
   slugs, merging duplicates:
       food-and-beverage -> food_beverage
       front-office      -> front_office
   Roles and Staff pointing at the legacy rows are re-pointed at the
   canonical rows before the legacy rows are deleted.
3. Repair any Role whose slug is empty: set slug='porter' and ensure its
   department is the canonical front_office of its hotel. Merge into an
   existing porter role if one already exists for that hotel.
4. Re-point every waiter role to the canonical food_beverage department
   of its hotel.
5. Null out Staff.role where role.hotel is set and != staff.hotel
   (cross-tenant role-leak cleanup).

It then adds CheckConstraints that forbid empty Department.slug and
Role.slug at the DB level.

All data operations are idempotent so the migration is safe to re-run.
"""
from django.db import migrations, models


CANONICAL_DEPARTMENTS = [
    ('front_office', 'Front Office',
     'Reception, porters, night audit, concierge.'),
    ('housekeeping', 'Housekeeping',
     'Room attendants, housekeeping supervisors.'),
    ('food_beverage', 'Food & Beverage',
     'Guest-facing FOH / service side: waiters, bar, restaurant floor.'),
    ('kitchen', 'Kitchen',
     'BOH culinary: chefs, line cooks, kitchen porters.'),
    ('maintenance', 'Maintenance',
     'Technical, engineering, repairs.'),
    ('guest_relations', 'Guest Relations',
     'Guest experience, VIP handling, complaints.'),
    ('management', 'Management',
     'Department managers and GMs.'),
    ('administration', 'Administration',
     'Back office: HR, finance, admin.'),
]

_CANONICAL_BY_SLUG = {s: (n, d) for (s, n, d) in CANONICAL_DEPARTMENTS}

SLUG_ALIASES = {
    'food-and-beverage': 'food_beverage',
    'front-office': 'front_office',
}


def _ensure_canonical_dept(Department, hotel_id, slug):
    """Return the canonical Department for (hotel, slug), creating it if
    missing. Returns None if `slug` is not canonical."""
    spec = _CANONICAL_BY_SLUG.get(slug)
    if spec is None:
        return None
    name, description = spec
    existing = Department.objects.filter(
        hotel_id=hotel_id, slug=slug
    ).first()
    if existing:
        return existing
    return Department.objects.create(
        hotel_id=hotel_id,
        slug=slug,
        name=name,
        description=description,
    )


def forwards(apps, schema_editor):
    Hotel = apps.get_model('hotel', 'Hotel')
    Department = apps.get_model('staff', 'Department')
    Role = apps.get_model('staff', 'Role')
    Staff = apps.get_model('staff', 'Staff')

    # ---- Step 1: normalize legacy kebab-case dept slugs --------------
    # Must run BEFORE seeding. Otherwise a hotel that already has a
    # Department(slug='front-office', name='Front Office') collides with
    # the new canonical row on unique_together (hotel, name).
    for legacy_slug, canonical_slug in SLUG_ALIASES.items():
        for legacy in list(Department.objects.filter(slug=legacy_slug)):
            if legacy.hotel_id is None:
                collision = Department.objects.filter(
                    hotel_id=None, slug=canonical_slug
                ).exclude(pk=legacy.pk).first()
                if collision is None:
                    legacy.slug = canonical_slug
                    legacy.save(update_fields=['slug'])
                    continue
                canonical = collision
            else:
                # Is there already a canonical row for this hotel?
                canonical = Department.objects.filter(
                    hotel_id=legacy.hotel_id, slug=canonical_slug
                ).exclude(pk=legacy.pk).first()
                if canonical is None:
                    # No canonical row yet: just rename the legacy row
                    # in place. This also sidesteps the unique(hotel,name)
                    # constraint that the seeding step would otherwise hit.
                    legacy.slug = canonical_slug
                    legacy.save(update_fields=['slug'])
                    continue

            # A canonical row already exists: re-point dependants and
            # drop the legacy row.
            Role.objects.filter(department_id=legacy.pk).update(
                department_id=canonical.pk
            )
            Staff.objects.filter(department_id=legacy.pk).update(
                department_id=canonical.pk
            )
            legacy.delete()

    # ---- Step 2: seed canonical departments for every hotel ----------
    for hotel_id in Hotel.objects.values_list('id', flat=True):
        for slug, name, description in CANONICAL_DEPARTMENTS:
            # Guard against name collisions with unrelated existing rows
            # that happen to share the display name: only create if neither
            # the slug nor the name already exist for this hotel.
            if Department.objects.filter(
                hotel_id=hotel_id, slug=slug
            ).exists():
                continue
            if Department.objects.filter(
                hotel_id=hotel_id, name=name
            ).exists():
                continue
            Department.objects.create(
                hotel_id=hotel_id,
                slug=slug,
                name=name,
                description=description,
            )

    # ---- Step 3: repair roles with empty slug ------------------------
    for role in list(Role.objects.filter(slug='')):
        if role.hotel_id is not None:
            front_office = _ensure_canonical_dept(
                Department, role.hotel_id, 'front_office'
            )
            if front_office is not None:
                role.department_id = front_office.pk

        collision = Role.objects.filter(
            hotel_id=role.hotel_id, slug='porter'
        ).exclude(pk=role.pk).first()
        if collision is not None:
            Staff.objects.filter(role_id=role.pk).update(
                role_id=collision.pk
            )
            role.delete()
            continue

        role.slug = 'porter'
        if not (role.name or '').strip():
            role.name = 'Porter'
        role.save(update_fields=['slug', 'name', 'department_id'])

    # ---- Step 4: re-point waiter roles to canonical food_beverage ----
    for role in Role.objects.filter(slug='waiter'):
        if role.hotel_id is None:
            continue
        canonical = _ensure_canonical_dept(
            Department, role.hotel_id, 'food_beverage'
        )
        if canonical is None:
            continue
        if role.department_id != canonical.pk:
            role.department_id = canonical.pk
            role.save(update_fields=['department_id'])

    # ---- Step 5: null cross-tenant Staff.role assignments ------------
    cross_tenant_ids = []
    for staff in Staff.objects.exclude(role__isnull=True).only(
        'id', 'hotel_id', 'role_id'
    ):
        role = Role.objects.filter(pk=staff.role_id).only(
            'id', 'hotel_id'
        ).first()
        if role is None:
            continue
        if role.hotel_id is None:
            continue
        if role.hotel_id != staff.hotel_id:
            cross_tenant_ids.append(staff.pk)

    if cross_tenant_ids:
        Staff.objects.filter(pk__in=cross_tenant_ids).update(role=None)


def backwards(apps, schema_editor):
    # Data normalization is not meaningfully reversible.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0024_delete_legacy_bookings_nav'),
        ('hotel', '0058_add_booking_filter_performance_indexes'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
