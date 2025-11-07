"""
Django management command to recreate October 2025 stock period with fresh data.

This command will:
1. Delete existing October 2025 period and all related data (snapshots, movements)
2. Create a fresh October 2025 period
3. Optionally create snapshots from current stock levels

Usage:
    python manage.py recreate_october_period <hotel_id>
    python manage.py recreate_october_period 1 --create-snapshots
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from stock_tracker.models import StockPeriod, StockSnapshot, StockMovement, Stocktake
from hotel.models import Hotel
from datetime import date


class Command(BaseCommand):
    help = 'Recreate October 2025 stock period with fresh data'

    def add_arguments(self, parser):
        parser.add_argument(
            'hotel_id',
            type=int,
            help='Hotel ID to recreate period for'
        )
        parser.add_argument(
            '--create-snapshots',
            action='store_true',
            help='Create snapshots from current stock levels'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompting'
        )

    def handle(self, *args, **options):
        hotel_id = options['hotel_id']
        create_snapshots = options['create_snapshots']
        confirm = options['confirm']

        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Hotel with ID {hotel_id} does not exist')
            )
            return

        # Find October 2025 period
        october_periods = StockPeriod.objects.filter(
            hotel=hotel,
            year=2025,
            month=10
        )

        if not october_periods.exists():
            self.stdout.write(
                self.style.WARNING('No October 2025 period found.')
            )
            self.stdout.write('Creating new October 2025 period...')
            self._create_october_period(hotel, create_snapshots)
            return

        # Show what will be deleted
        period = october_periods.first()
        snapshot_count = StockSnapshot.objects.filter(period=period).count()
        movement_count = StockMovement.objects.filter(period=period).count()
        stocktake_count = Stocktake.objects.filter(
            hotel=hotel,
            period_start__year=2025,
            period_start__month=10
        ).count()

        self.stdout.write(
            self.style.WARNING(
                f'\n⚠️  Found October 2025 period: {period.period_name}'
            )
        )
        self.stdout.write(f'   - {snapshot_count} snapshots')
        self.stdout.write(f'   - {movement_count} movements')
        self.stdout.write(f'   - {stocktake_count} stocktakes')

        # Confirm deletion
        if not confirm:
            response = input(
                '\n❗ This will DELETE all October 2025 data. Continue? (yes/no): '
            )
            if response.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        # Delete everything in a transaction
        with transaction.atomic():
            self.stdout.write('\n🗑️  Deleting old data...')
            
            # Delete stocktakes (will cascade to stocktake lines)
            deleted_stocktakes = Stocktake.objects.filter(
                hotel=hotel,
                period_start__year=2025,
                period_start__month=10
            ).delete()
            self.stdout.write(
                f'   ✓ Deleted {deleted_stocktakes[0]} stocktakes'
            )

            # Delete snapshots
            deleted_snapshots = StockSnapshot.objects.filter(
                period=period
            ).delete()
            self.stdout.write(
                f'   ✓ Deleted {deleted_snapshots[0]} snapshots'
            )

            # Delete movements
            deleted_movements = StockMovement.objects.filter(
                period=period
            ).delete()
            self.stdout.write(
                f'   ✓ Deleted {deleted_movements[0]} movements'
            )

            # Delete period
            period.delete()
            self.stdout.write('   ✓ Deleted October 2025 period')

            # Create fresh period
            self.stdout.write('\n✨ Creating fresh October 2025 period...')
            self._create_october_period(hotel, create_snapshots)

    def _create_october_period(self, hotel, create_snapshots):
        """Create a fresh October 2025 period"""
        period = StockPeriod.objects.create(
            hotel=hotel,
            period_type=StockPeriod.MONTHLY,
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 31),
            year=2025,
            month=10,
            period_name='October 2025',
            is_closed=False
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Created October 2025 period (ID: {period.id})'
            )
        )

        if create_snapshots:
            self.stdout.write('\n📸 Creating snapshots from current stock...')
            snapshot_count = self._create_snapshots(period)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Created {snapshot_count} snapshots'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 October 2025 period ready!'
            )
        )
        self.stdout.write(f'\nPeriod ID: {period.id}')
        self.stdout.write(f'Period Name: {period.period_name}')
        self.stdout.write(f'Start Date: {period.start_date}')
        self.stdout.write(f'End Date: {period.end_date}')
        self.stdout.write(f'Status: {"Closed" if period.is_closed else "Open"}')

    def _create_snapshots(self, period):
        """Create snapshots from current stock levels"""
        from stock_tracker.models import StockItem

        snapshots_created = 0
        items = StockItem.objects.filter(
            hotel=period.hotel,
            active=True
        )

        for item in items:
            StockSnapshot.objects.create(
                hotel=period.hotel,
                item=item,
                period=period,
                closing_full_units=item.current_full_units,
                closing_partial_units=item.current_partial_units,
                unit_cost=item.unit_cost,
                cost_per_serving=item.cost_per_serving,
                closing_stock_value=item.total_stock_value,
                menu_price=item.menu_price
            )
            snapshots_created += 1

        return snapshots_created
