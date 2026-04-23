"""
Seed canonical departments (all 8) for every hotel, idempotently.

Usage:
    python manage.py seed_canonical_departments
    python manage.py seed_canonical_departments --hotel <slug>
    python manage.py seed_canonical_departments --dry-run

The canonical list lives in staff.department_catalog.CANONICAL_DEPARTMENTS
and is the single source of truth.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from hotel.models import Hotel
from staff.department_catalog import CANONICAL_DEPARTMENTS
from staff.models import Department


class Command(BaseCommand):
    help = (
        "Seed all 8 canonical departments for every hotel (idempotent). "
        "Existing departments are left untouched."
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
        hotels_touched = 0

        for hotel in hotels_qs.iterator():
            hotels_touched += 1
            created_here = 0
            existing_here = 0
            with transaction.atomic():
                for spec in CANONICAL_DEPARTMENTS:
                    slug = spec['slug']
                    existing = Department.objects.filter(
                        hotel=hotel, slug=slug
                    ).first()
                    if existing:
                        existing_here += 1
                        continue
                    if dry_run:
                        created_here += 1
                        continue
                    Department.objects.create(
                        hotel=hotel,
                        slug=slug,
                        name=spec['name'],
                        description=spec.get('description', '') or '',
                    )
                    created_here += 1

            created_total += created_here
            existing_total += existing_here
            self.stdout.write(
                f'[{hotel.slug}] created={created_here} '
                f'existing={existing_here}'
            )

        verb = 'would create' if dry_run else 'created'
        self.stdout.write(self.style.SUCCESS(
            f'Done. hotels={hotels_touched} {verb}={created_total} '
            f'already_present={existing_total}'
        ))
