"""
Seed canonical roles for every hotel, idempotently.

Usage:
    python manage.py seed_canonical_roles
    python manage.py seed_canonical_roles --hotel <slug>
    python manage.py seed_canonical_roles --dry-run

The canonical list lives in staff.role_catalog.CANONICAL_ROLES and is the
single source of truth. Each role is linked to the canonical Department
of the same hotel (see staff.department_catalog).

Existing canonical roles are left untouched. Legacy role slugs
(manager, admin, receptionist, porter, housekeeping) are handled by the
0027 data migration — this command does NOT reassign or delete legacy
rows.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from hotel.models import Hotel
from staff.models import Department, Role
from staff.role_catalog import CANONICAL_ROLES


class Command(BaseCommand):
    help = (
        "Seed all canonical roles for every hotel (idempotent). "
        "Existing roles are left untouched."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel',
            dest='hotel_slug',
            default=None,
            help='Restrict seeding to a single hotel slug.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Report what would be created without writing changes.',
        )

    def handle(self, *args, **options):
        hotel_slug = options.get('hotel_slug')
        dry_run = options.get('dry_run', False)

        hotels_qs = Hotel.objects.all()
        if hotel_slug:
            hotels_qs = hotels_qs.filter(slug=hotel_slug)

        if not hotels_qs.exists():
            self.stdout.write(self.style.WARNING(
                f'No hotels matched (slug={hotel_slug!r}).'
            ))
            return

        created_total = 0
        existing_total = 0
        skipped_total = 0
        hotels_touched = 0

        for hotel in hotels_qs.iterator():
            hotels_touched += 1
            created_here = 0
            existing_here = 0
            skipped_here = 0

            with transaction.atomic():
                for spec in CANONICAL_ROLES:
                    slug = spec['slug']
                    if Role.objects.filter(
                        hotel=hotel, slug=slug
                    ).exists():
                        existing_here += 1
                        continue

                    dept = Department.objects.filter(
                        hotel=hotel, slug=spec['department_slug']
                    ).first()
                    if dept is None:
                        # Missing canonical department — run
                        # seed_canonical_departments first.
                        self.stdout.write(self.style.WARNING(
                            f'[{hotel.slug}] missing department '
                            f"'{spec['department_slug']}' — skipping "
                            f"role '{slug}'"
                        ))
                        skipped_here += 1
                        continue

                    if dry_run:
                        created_here += 1
                        continue

                    Role.objects.create(
                        hotel=hotel,
                        department=dept,
                        slug=slug,
                        name=spec['name'],
                        description=spec.get('description', '') or '',
                    )
                    created_here += 1

            created_total += created_here
            existing_total += existing_here
            skipped_total += skipped_here
            self.stdout.write(
                f'[{hotel.slug}] created={created_here} '
                f'existing={existing_here} skipped={skipped_here}'
            )

        verb = 'would create' if dry_run else 'created'
        self.stdout.write(self.style.SUCCESS(
            f'Done. hotels={hotels_touched} {verb}={created_total} '
            f'already_present={existing_total} '
            f'skipped={skipped_total}'
        ))
