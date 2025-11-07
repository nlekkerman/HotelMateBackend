"""
Management command to create and close October 2025 stocktake.
Uses October snapshots as both opening and closing stock.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from stock_tracker.models import (
    StockPeriod, StockSnapshot, Stocktake, StocktakeLine
)
from hotel.models import Hotel


class Command(BaseCommand):
    help = 'Create and close October 2025 stocktake from snapshots'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the operation'
        )

    def handle(self, *args, **options):
        hotel_id = 2  # Hardcoded for Hotel Killarney
        confirm = options['confirm']

        if not confirm:
            self.stdout.write(
                self.style.WARNING(
                    'This will create October stocktake and approve it.'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Run with --confirm to proceed.'
                )
            )
            return

        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Hotel with ID {hotel_id} not found')
            )
            return

        # Check for October period
        try:
            period = StockPeriod.objects.get(
                hotel=hotel,
                period_type='MONTHLY',
                year=2025,
                month=10
            )
        except StockPeriod.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ October 2025 period not found')
            )
            self.stdout.write(
                'Run: python manage.py close_october_period --confirm'
            )
            return

        if not period.is_closed:
            self.stdout.write(
                self.style.ERROR('❌ October period is not closed')
            )
            self.stdout.write(
                'Run: python manage.py close_october_period --confirm'
            )
            return

        # Check for snapshots
        snapshots = StockSnapshot.objects.filter(
            hotel=hotel,
            period=period
        )

        if not snapshots.exists():
            self.stdout.write(
                self.style.ERROR(
                    '❌ No snapshots found for October period'
                )
            )
            self.stdout.write(
                'Run: python manage.py close_october_period --confirm'
            )
            return

        self.stdout.write(f'Processing hotel: {hotel.name}')
        self.stdout.write(f'Period: {period.period_name}')
        self.stdout.write(f'Snapshots found: {snapshots.count()}')
        self.stdout.write('')

        with transaction.atomic():
            # Create stocktake
            stocktake, created = Stocktake.objects.get_or_create(
                hotel=hotel,
                period_start=period.start_date,
                period_end=period.end_date,
                defaults={
                    'status': Stocktake.DRAFT,
                    'notes': (
                        'October 2025 baseline stocktake (auto-created)'
                    )
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Created stocktake (ID: {stocktake.id})'
                    )
                )
            else:
                # Delete existing lines if recreating
                deleted_count = StocktakeLine.objects.filter(
                    stocktake=stocktake
                ).delete()[0]

                if deleted_count > 0:
                    self.stdout.write(
                        f'🗑️  Deleted {deleted_count} old lines'
                    )

                self.stdout.write(
                    f'� Using existing stocktake (ID: {stocktake.id})'
                )

            # Create stocktake lines from snapshots
            created_lines = 0
            total_value = Decimal('0.00')

            self.stdout.write(
                f'📸 Creating lines from {snapshots.count()} snapshots...'
            )

            for snapshot in snapshots:
                # For October baseline: everything in SERVINGS
                # opening_qty should be total servings (pints/bottles/shots)
                # Use the snapshot's total_servings calculation
                
                opening_qty = snapshot.total_servings

                # Create stocktake line
                line = StocktakeLine.objects.create(
                    stocktake=stocktake,
                    item=snapshot.item,
                    # Opening stock = total servings
                    opening_qty=opening_qty,
                    # No movements in October (baseline)
                    purchases=Decimal('0.0000'),
                    sales=Decimal('0.0000'),
                    waste=Decimal('0.0000'),
                    transfers_in=Decimal('0.0000'),
                    transfers_out=Decimal('0.0000'),
                    adjustments=Decimal('0.0000'),
                    # Counted = same as snapshot closing stock
                    counted_full_units=snapshot.closing_full_units,
                    counted_partial_units=snapshot.closing_partial_units,
                    # Frozen costs
                    valuation_cost=snapshot.cost_per_serving
                )

                total_value += line.counted_value
                created_lines += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Created {created_lines} stocktake lines'
                )
            )

            # Approve the stocktake
            stocktake.status = Stocktake.APPROVED
            stocktake.approved_at = timezone.now()
            stocktake.save()

            self.stdout.write(
                self.style.SUCCESS(
                    '✅ Approved stocktake'
                )
            )

            # Summary
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS('=' * 60)
            )
            self.stdout.write(
                self.style.SUCCESS(
                    '🎉 October 2025 Stocktake Created!'
                )
            )
            self.stdout.write(
                self.style.SUCCESS('=' * 60)
            )
            self.stdout.write(f'Stocktake ID: {stocktake.id}')
            self.stdout.write(
                f'Period: {stocktake.period_start} to '
                f'{stocktake.period_end}'
            )
            self.stdout.write(f'Status: {stocktake.status}')
            self.stdout.write(f'Total Items: {created_lines}')
            self.stdout.write(f'Total Value: €{total_value:,.2f}')
            self.stdout.write('')

            # Calculate variances
            total_variance_qty = sum(
                line.variance_qty
                for line in stocktake.lines.all()
            )
            total_variance_value = sum(
                line.variance_value
                for line in stocktake.lines.all()
            )

            self.stdout.write('Variance Analysis:')
            self.stdout.write(
                f'  Quantity Variance: {total_variance_qty:,.4f}'
            )
            self.stdout.write(
                f'  Value Variance: €{total_variance_value:,.2f}'
            )

            if abs(total_variance_qty) < Decimal('0.01'):
                self.stdout.write(
                    self.style.SUCCESS(
                        '  ✅ Perfect match (expected for baseline)'
                    )
                )

            self.stdout.write('')
            self.stdout.write(
                '✅ This stocktake is now the October 2025 baseline!'
            )
            self.stdout.write(
                '✅ Ready for comparison with future stocktakes!'
            )
            self.stdout.write(self.style.SUCCESS('=' * 60))
