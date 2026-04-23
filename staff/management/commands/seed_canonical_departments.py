"""
Seed canonical departments (all 8) for every hotel, idempotently.

Usage:
    python manage.py seed_canonical_departments
    python manage.py seed_canonical_departments --hotel <slug>
    python manage.py seed_canonical_departments --dry-run

The canonical list lives in staff.department_catalog.CANONICAL_DEPARTMENTS
and is the single source of truth.

Phase 4B.1 cleanup:
- Creates missing rows per (hotel, slug)
- Normalizes name/description to canonical values when they drift
- Detects and reports duplicate (hotel, slug) rows (does not destructively
  merge them; out of scope here)
- Idempotent: after one converging run, subsequent runs are no-ops
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from hotel.models import Hotel
from staff.department_catalog import CANONICAL_DEPARTMENTS
from staff.models import Department


class Command(BaseCommand):
    help = (
        "Seed and normalize all 8 canonical departments for every hotel "
        "(idempotent). Canonical name/description are enforced per slug."
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
            help='Report what would change without writing.',
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
        updated_total = 0
        unchanged_total = 0
        duplicate_total = 0
        hotels_touched = 0

        for hotel in hotels_qs.iterator():
            hotels_touched += 1
            created_here = 0
            updated_here = 0
            unchanged_here = 0
            duplicates_here = []

            with transaction.atomic():
                # Detect duplicates for this hotel up-front so we don't
                # silently operate on ambiguous rows.
                dup_rows = (
                    Department.objects
                    .filter(hotel=hotel)
                    .values('slug')
                    .annotate(n=Count('id'))
                    .filter(n__gt=1)
                )
                dup_slugs = {row['slug'] for row in dup_rows}

                for spec in CANONICAL_DEPARTMENTS:
                    slug = spec['slug']
                    canonical_name = spec['name']
                    canonical_desc = spec.get('description', '') or ''

                    if slug in dup_slugs:
                        duplicates_here.append(slug)
                        continue

                    existing = Department.objects.filter(
                        hotel=hotel, slug=slug
                    ).first()

                    if existing is None:
                        if dry_run:
                            created_here += 1
                        else:
                            Department.objects.create(
                                hotel=hotel,
                                slug=slug,
                                name=canonical_name,
                                description=canonical_desc,
                            )
                            created_here += 1
                        continue

                    needs_update = (
                        existing.name != canonical_name
                        or (existing.description or '') != canonical_desc
                    )
                    if not needs_update:
                        unchanged_here += 1
                        continue

                    if dry_run:
                        self.stdout.write(
                            f'[{hotel.slug}] WOULD normalize {slug}: '
                            f'name={existing.name!r} -> {canonical_name!r}'
                        )
                        updated_here += 1
                        continue

                    existing.name = canonical_name
                    existing.description = canonical_desc
                    existing.save(update_fields=['name', 'description'])
                    updated_here += 1

            created_total += created_here
            updated_total += updated_here
            unchanged_total += unchanged_here
            duplicate_total += len(duplicates_here)

            line = (
                f'[{hotel.slug}] created={created_here} '
                f'updated={updated_here} unchanged={unchanged_here}'
            )
            if duplicates_here:
                line += f' duplicates={sorted(duplicates_here)}'
            self.stdout.write(line)

        verb_created = 'would create' if dry_run else 'created'
        verb_updated = 'would update' if dry_run else 'updated'
        self.stdout.write(self.style.SUCCESS(
            f'Done. hotels={hotels_touched} '
            f'{verb_created}={created_total} '
            f'{verb_updated}={updated_total} '
            f'unchanged={unchanged_total} '
            f'duplicate_slugs={duplicate_total}'
        ))
        if duplicate_total:
            self.stdout.write(self.style.WARNING(
                'Duplicate (hotel, slug) rows detected. These were NOT '
                'modified. Resolve them manually before re-running.'
            ))
