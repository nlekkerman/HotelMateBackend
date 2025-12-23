from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from hotel.models import Hotel, CancellationPolicy, CancellationPolicyTier


@dataclass(frozen=True)
class TierSeed:
    hours_before_checkin: int
    penalty_type: str
    penalty_amount: Optional[Decimal] = None
    penalty_percentage: Optional[Decimal] = None


@dataclass(frozen=True)
class PolicySeed:
    code: str
    name: str
    template_type: str
    description: str = ""
    free_until_hours: Optional[int] = None
    penalty_type: Optional[str] = None
    penalty_amount: Optional[Decimal] = None
    penalty_percentage: Optional[Decimal] = None
    no_show_penalty_type: str = "FULL_STAY"
    tiers: tuple[TierSeed, ...] = ()


DEFAULT_POLICIES: tuple[PolicySeed, ...] = (
    PolicySeed(
        code="FLEX24",
        name="Flexible 24h (First Night)",
        template_type="FLEXIBLE",
        description="Free cancellation up to 24 hours before check-in. After that, first night is charged.",
        free_until_hours=24,
        penalty_type="FIRST_NIGHT",
        no_show_penalty_type="FULL_STAY",
    ),
    PolicySeed(
        code="FLEX48",
        name="Flexible 48h (First Night)",
        template_type="FLEXIBLE",
        description="Free cancellation up to 48 hours before check-in. After that, first night is charged.",
        free_until_hours=48,
        penalty_type="FIRST_NIGHT",
        no_show_penalty_type="FULL_STAY",
    ),
    PolicySeed(
        code="MOD48_50",
        name="Moderate 48h (50%)",
        template_type="MODERATE",
        description="Free cancellation up to 48 hours before check-in. After that, 50% of total is charged.",
        free_until_hours=48,
        penalty_type="PERCENTAGE",
        penalty_percentage=Decimal("50.00"),
        no_show_penalty_type="FULL_STAY",
    ),
    PolicySeed(
        code="NRF",
        name="Non-Refundable (Full Stay)",
        template_type="NON_REFUNDABLE",
        description="Non-refundable booking. Full stay charged on cancellation or no-show.",
        free_until_hours=0,
        penalty_type="FULL_STAY",
        no_show_penalty_type="FULL_STAY",
    ),
    PolicySeed(
        code="TIERED_STD",
        name="Tiered Standard (72h/48h/24h)",
        template_type="CUSTOM",
        description="Tiered cancellation penalties based on time before check-in.",
        # CUSTOM primarily uses tiers; base fields may be ignored by your serializer validation
        tiers=(
            TierSeed(hours_before_checkin=72, penalty_type="NONE"),
            TierSeed(hours_before_checkin=48, penalty_type="FIRST_NIGHT"),
            TierSeed(hours_before_checkin=24, penalty_type="PERCENTAGE", penalty_percentage=Decimal("50.00")),
            TierSeed(hours_before_checkin=0, penalty_type="FULL_STAY"),
        ),
        no_show_penalty_type="FULL_STAY",
    ),
)


class Command(BaseCommand):
    help = "Seed industry-standard default cancellation policies for one hotel or all hotels (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hotel-slug",
            dest="hotel_slug",
            default=None,
            help="Seed policies for a specific hotel slug only.",
        )
        parser.add_argument(
            "--all-hotels",
            action="store_true",
            help="Seed policies for all hotels.",
        )
        parser.add_argument(
            "--force-update",
            action="store_true",
            help="Update existing policies (matched by code) with the default definitions.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created/updated without writing to the database.",
        )

    def handle(self, *args, **options):
        hotel_slug = options["hotel_slug"]
        all_hotels = options["all_hotels"]
        force_update = options["force_update"]
        dry_run = options["dry_run"]

        if bool(hotel_slug) == bool(all_hotels):
            raise CommandError("Provide exactly one: --hotel-slug <slug> OR --all-hotels")

        hotels: Iterable[Hotel]
        if hotel_slug:
            hotels = Hotel.objects.filter(slug=hotel_slug)
            if not hotels.exists():
                raise CommandError(f"No hotel found with slug '{hotel_slug}'")
        else:
            hotels = Hotel.objects.all()

        created_total = 0
        updated_total = 0
        skipped_total = 0
        tier_created_total = 0
        tier_updated_total = 0

        for hotel in hotels:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\nHotel: {hotel.name} ({hotel.slug})"))

            for seed in DEFAULT_POLICIES:
                existing = CancellationPolicy.objects.filter(hotel=hotel, code=seed.code).first()

                if existing and not force_update:
                    skipped_total += 1
                    self.stdout.write(f"  = SKIP  {seed.code} (already exists)")
                    continue

                if dry_run:
                    action = "UPDATE" if existing else "CREATE"
                    self.stdout.write(f"  ~ {action} {seed.code} — {seed.name}")
                    continue

                with transaction.atomic():
                    policy, created = CancellationPolicy.objects.get_or_create(
                        hotel=hotel,
                        code=seed.code,
                        defaults={
                            "name": seed.name,
                            "description": seed.description,
                            "is_active": True,
                            "template_type": seed.template_type,
                            "free_until_hours": seed.free_until_hours,
                            "penalty_type": seed.penalty_type,
                            "penalty_amount": seed.penalty_amount,
                            "penalty_percentage": seed.penalty_percentage,
                            "no_show_penalty_type": seed.no_show_penalty_type,
                        },
                    )

                    if created:
                        created_total += 1
                        self.stdout.write(self.style.SUCCESS(f"  + CREATE {seed.code} — {seed.name}"))
                    else:
                        # force_update=True path
                        policy.name = seed.name
                        policy.description = seed.description
                        policy.is_active = True
                        policy.template_type = seed.template_type
                        policy.free_until_hours = seed.free_until_hours
                        policy.penalty_type = seed.penalty_type
                        policy.penalty_amount = seed.penalty_amount
                        policy.penalty_percentage = seed.penalty_percentage
                        policy.no_show_penalty_type = seed.no_show_penalty_type
                        policy.save(update_fields=[
                            "name", "description", "is_active", "template_type",
                            "free_until_hours", "penalty_type", "penalty_amount",
                            "penalty_percentage", "no_show_penalty_type",
                        ])
                        updated_total += 1
                        self.stdout.write(self.style.WARNING(f"  ~ UPDATE {seed.code} — {seed.name}"))

                    # Handle tiers only for CUSTOM
                    if seed.template_type == "CUSTOM":
                        # Keep tiers in sync when force_update, else only create missing tiers
                        for t in seed.tiers:
                            tier_qs = CancellationPolicyTier.objects.filter(
                                policy=policy,
                                hours_before_checkin=t.hours_before_checkin,
                            )
                            tier = tier_qs.first()

                            if tier is None:
                                CancellationPolicyTier.objects.create(
                                    policy=policy,
                                    hours_before_checkin=t.hours_before_checkin,
                                    penalty_type=t.penalty_type,
                                    penalty_amount=t.penalty_amount,
                                    penalty_percentage=t.penalty_percentage,
                                )
                                tier_created_total += 1
                                self.stdout.write(f"      + tier {t.hours_before_checkin}h → {t.penalty_type}")
                            elif force_update:
                                tier.penalty_type = t.penalty_type
                                tier.penalty_amount = t.penalty_amount
                                tier.penalty_percentage = t.penalty_percentage
                                tier.save(update_fields=["penalty_type", "penalty_amount", "penalty_percentage"])
                                tier_updated_total += 1
                                self.stdout.write(f"      ~ tier {t.hours_before_checkin}h → {t.penalty_type}")

        if dry_run:
            self.stdout.write(self.style.NOTICE("\nDRY RUN complete (no changes written)."))
            return

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created: {created_total}, Updated: {updated_total}, Skipped: {skipped_total}, "
            f"Tiers created: {tier_created_total}, Tiers updated: {tier_updated_total}"
        ))