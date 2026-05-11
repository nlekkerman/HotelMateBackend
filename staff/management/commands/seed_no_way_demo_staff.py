"""
Seed a small portfolio/demo set of staff users for the existing
``no-way-hotel`` hotel. Idempotent — safe to run multiple times.

Usage:
    python manage.py seed_no_way_demo_staff
    python manage.py seed_no_way_demo_staff --reset-passwords

Optional environment variable for password override:
    DEMO_STAFF_PASSWORD="SomethingElse123!" \\
        python manage.py seed_no_way_demo_staff --reset-passwords

The command:
- looks up Hotel by slug (does NOT create the hotel);
- looks up canonical Role/Department rows scoped to that hotel
  (does NOT create new roles or departments);
- finds-or-creates a Django User per demo person (email = stable id);
- finds-or-creates the linked Staff row;
- only resets passwords on first creation OR when --reset-passwords
  is passed.
"""
from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from hotel.models import Hotel
from staff.models import Department, Role, Staff


User = get_user_model()

HOTEL_SLUG = 'no-way-hotel'
DEFAULT_PASSWORD = 'PortfolioTest123!'


# ``access_level`` ∈ Staff.ACCESS_LEVEL_CHOICES
# ``role_slug`` / ``department_slug`` are looked up against the hotel.
DEMO_STAFF: list[dict] = [
    {
        'first_name': 'Nora', 'last_name': 'King',
        'email': 'nora.king.demo@noway.test',
        'access_level': 'super_staff_admin',
        'role_slug': 'front_office_manager',
        'department_slug': 'front_office',
    },
    {
        'first_name': 'Henry', 'last_name': 'Walsh',
        'email': 'henry.walsh.demo@noway.test',
        'access_level': 'staff_admin',
        'role_slug': 'hotel_manager',
        'department_slug': 'management',
    },
    {
        'first_name': 'Fiona', 'last_name': 'Brooks',
        'email': 'fiona.brooks.demo@noway.test',
        'access_level': 'regular_staff',
        'role_slug': 'front_office_manager',
        'department_slug': 'front_office',
    },
    {
        'first_name': 'Maya', 'last_name': 'Reed',
        'email': 'maya.reed.demo@noway.test',
        'access_level': 'regular_staff',
        'role_slug': 'housekeeping_manager',
        'department_slug': 'housekeeping',
    },
    {
        'first_name': 'Liam', 'last_name': 'Stone',
        'email': 'liam.stone.demo@noway.test',
        'access_level': 'regular_staff',
        'role_slug': 'front_office_supervisor',
        'department_slug': 'front_office',
    },
    {
        'first_name': 'Ava', 'last_name': 'Doyle',
        'email': 'ava.doyle.demo@noway.test',
        'access_level': 'regular_staff',
        'role_slug': 'housekeeper',
        'department_slug': 'housekeeping',
    },
    {
        'first_name': 'Omar', 'last_name': 'Price',
        'email': 'omar.price.demo@noway.test',
        'access_level': 'regular_staff',
        'role_slug': 'waiter',
        'department_slug': 'food_beverage',
    },
    {
        'first_name': 'Kate', 'last_name': 'Nolan',
        'email': 'kate.nolan.demo@noway.test',
        'access_level': 'regular_staff',
        'role_slug': 'maintenance_staff',
        'department_slug': 'maintenance',
    },
    {
        'first_name': 'Zoe', 'last_name': 'Hart',
        'email': 'zoe.hart.demo@noway.test',
        'access_level': 'regular_staff',
        'role_slug': 'front_desk_agent',
        'department_slug': 'front_office',
    },
]


def _username_from_email(email: str) -> str:
    """Stable username derived from the email local part.

    Default Django User has ``username`` (unique, max 150). We use
    the full email as the username so it stays unique across demo
    re-runs and matches the existing project convention of using
    email-as-username for staff (StaffSerializer.create() in the
    real flow also uses email as username).
    """
    return email[:150]


class Command(BaseCommand):
    help = (
        "Seed portfolio/demo staff users for the existing "
        f"'{HOTEL_SLUG}' hotel (idempotent)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            dest='reset_passwords',
            default=False,
            help=(
                'Reset passwords on existing demo users to the demo '
                'password. New users always get the password set.'
            ),
        )

    def handle(self, *args, **options):
        reset_passwords: bool = options['reset_passwords']
        password = os.environ.get('DEMO_STAFF_PASSWORD', DEFAULT_PASSWORD)

        # --- 1. Hotel must exist (we never create it) --------------------
        try:
            hotel = Hotel.objects.get(slug=HOTEL_SLUG)
        except Hotel.DoesNotExist as exc:
            raise CommandError(
                f"Hotel with slug '{HOTEL_SLUG}' does not exist. "
                "Aborting."
            ) from exc

        # --- 2. Resolve every role + department slug up-front. -----------
        #     Abort BEFORE any user creation if anything is missing.
        needed_roles = sorted({p['role_slug'] for p in DEMO_STAFF})
        needed_depts = sorted({p['department_slug'] for p in DEMO_STAFF})

        roles_by_slug = {
            r.slug: r for r in Role.objects.filter(
                hotel=hotel, slug__in=needed_roles,
            )
        }
        depts_by_slug = {
            d.slug: d for d in Department.objects.filter(
                hotel=hotel, slug__in=needed_depts,
            )
        }

        missing_roles = [s for s in needed_roles if s not in roles_by_slug]
        missing_depts = [s for s in needed_depts if s not in depts_by_slug]
        if missing_roles or missing_depts:
            lines = [
                'Cannot seed demo staff — missing canonical rows for '
                f"hotel '{HOTEL_SLUG}':"
            ]
            if missing_roles:
                lines.append(f"  missing roles:       {missing_roles}")
            if missing_depts:
                lines.append(f"  missing departments: {missing_depts}")
            lines.append(
                "Run 'seed_canonical_departments' and "
                "'seed_canonical_roles' first."
            )
            raise CommandError('\n'.join(lines))

        # --- 3. Create / update each demo user. --------------------------
        results: list[dict] = []
        with transaction.atomic():
            for spec in DEMO_STAFF:
                results.append(self._upsert_one(
                    spec=spec,
                    hotel=hotel,
                    role=roles_by_slug[spec['role_slug']],
                    department=depts_by_slug[spec['department_slug']],
                    password=password,
                    reset_passwords=reset_passwords,
                ))

        # --- 4. Pretty-print summary table. ------------------------------
        self._print_table(results)

        # --- 5. Capability summary (best-effort). ------------------------
        self._print_capability_summary(results)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f"Password: {password}"
        ))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _upsert_one(
        self,
        *,
        spec: dict,
        hotel: Hotel,
        role: Role,
        department: Department,
        password: str,
        reset_passwords: bool,
    ) -> dict:
        email = spec['email']
        username = _username_from_email(email)

        # --- User --------------------------------------------------------
        user, user_created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'first_name': spec['first_name'],
                'last_name': spec['last_name'],
                'is_active': True,
            },
        )

        # Update intended demo fields only.
        dirty = False
        if user.username != username:
            user.username = username
            dirty = True
        if user.first_name != spec['first_name']:
            user.first_name = spec['first_name']
            dirty = True
        if user.last_name != spec['last_name']:
            user.last_name = spec['last_name']
            dirty = True
        if not user.is_active:
            user.is_active = True
            dirty = True

        if user_created or reset_passwords:
            user.set_password(password)
            dirty = True

        if dirty:
            user.save()

        # --- Staff -------------------------------------------------------
        staff, staff_created = Staff.objects.get_or_create(
            user=user,
            defaults={
                'hotel': hotel,
                'department': department,
                'role': role,
                'access_level': spec['access_level'],
                'first_name': spec['first_name'],
                'last_name': spec['last_name'],
                'email': email,
                'is_active': True,
            },
        )

        # Update intended demo fields only.
        s_dirty = False
        if staff.hotel_id != hotel.id:
            staff.hotel = hotel
            s_dirty = True
        if staff.department_id != department.id:
            staff.department = department
            s_dirty = True
        if staff.role_id != role.id:
            staff.role = role
            s_dirty = True
        if staff.access_level != spec['access_level']:
            staff.access_level = spec['access_level']
            s_dirty = True
        if staff.first_name != spec['first_name']:
            staff.first_name = spec['first_name']
            s_dirty = True
        if staff.last_name != spec['last_name']:
            staff.last_name = spec['last_name']
            s_dirty = True
        if staff.email != email:
            staff.email = email
            s_dirty = True
        if not staff.is_active:
            staff.is_active = True
            s_dirty = True

        if s_dirty:
            staff.save()

        return {
            'spec': spec,
            'user': user,
            'staff': staff,
            'user_created': user_created,
            'staff_created': staff_created,
        }

    def _print_table(self, results: list[dict]) -> None:
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f"Created/Updated {HOTEL_SLUG} demo staff:"
        ))
        self.stdout.write('')

        header = (
            f"{'Email':<32} {'Name':<14} {'Tier':<20} "
            f"{'Role':<26} {'Department':<14} {'Status':<10}"
        )
        self.stdout.write(header)
        self.stdout.write('-' * len(header))

        for r in results:
            spec = r['spec']
            name = f"{spec['first_name']} {spec['last_name']}"
            if r['user_created'] or r['staff_created']:
                stat = 'created'
            else:
                stat = 'updated'
            self.stdout.write(
                f"{spec['email']:<32} {name:<14} "
                f"{spec['access_level']:<20} "
                f"{spec['role_slug']:<26} "
                f"{spec['department_slug']:<14} {stat:<10}"
            )

    def _print_capability_summary(self, results: list[dict]) -> None:
        try:
            from staff.capability_catalog import resolve_capabilities
        except Exception as exc:  # pragma: no cover — defensive
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                f"Skipping capability summary (resolver unavailable: "
                f"{exc})."
            ))
            return

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Capability summary:'))
        for r in results:
            spec = r['spec']
            try:
                caps = resolve_capabilities(
                    spec['access_level'],
                    spec['role_slug'],
                    spec['department_slug'],
                )
                count = len(caps)
            except Exception as exc:  # pragma: no cover — defensive
                count_str = f"<error: {exc}>"
            else:
                count_str = f"{count} capabilities"

            name = f"{spec['first_name']} {spec['last_name']}"
            self.stdout.write(
                f"  {name:<14} {spec['access_level']:<20} "
                f"/ {spec['role_slug']:<26} {count_str}"
            )
