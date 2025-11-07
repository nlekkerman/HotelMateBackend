"""
Management command to close October 2025 period and create snapshots.
This sets the baseline for future stocktakes.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel


class Command(BaseCommand):
    help = 'Close October 2025 period and create snapshots from current stock'

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
                    'This will close October 2025 period and create snapshots.'
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

        self.stdout.write(f'Processing hotel: {hotel.name}')

        with transaction.atomic():
            # Get or create October 2025 period
            period, created = StockPeriod.objects.get_or_create(
                hotel=hotel,
                period_type='MONTHLY',
                year=2025,
                month=10,
                defaults={
                    'start_date': '2025-10-01',
                    'end_date': '2025-10-31',
                    'period_name': 'October 2025',
                    'is_closed': False
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Created October 2025 period (ID: {period.id})'
                    )
                )
            else:
                self.stdout.write(
                    f'📋 Found existing October 2025 period (ID: {period.id})'
                )

            # Delete existing snapshots for this period
            deleted_count = StockSnapshot.objects.filter(
                hotel=hotel,
                period=period
            ).delete()[0]

            if deleted_count > 0:
                self.stdout.write(
                    f'🗑️  Deleted {deleted_count} old snapshots'
                )

            # Get all active stock items
            items = StockItem.objects.filter(
                hotel=hotel,
                active=True
            ).select_related('category')

            self.stdout.write(
                f'📸 Creating snapshots for {items.count()} items...'
            )

            created_snapshots = 0

            for item in items:
                # Create snapshot with current stock as closing stock
                StockSnapshot.objects.create(
                    hotel=hotel,
                    item=item,
                    period=period,
                    closing_full_units=item.current_full_units,
                    closing_partial_units=item.current_partial_units,
                    unit_cost=item.unit_cost,
                    cost_per_serving=item.cost_per_serving,
                    closing_stock_value=item.total_stock_value,
                    menu_price=item.menu_price or Decimal('0.00')
                )
                created_snapshots += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Created {created_snapshots} snapshots'
                )
            )

            # Close the period
            period.is_closed = True
            period.save()

            self.stdout.write(
                self.style.SUCCESS(
                    '✅ Closed October 2025 period'
                )
            )

            # Summary
            total_value = sum(
                snapshot.closing_stock_value
                for snapshot in StockSnapshot.objects.filter(period=period)
            )

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(
                self.style.SUCCESS('🎉 October 2025 Period Closed!')
            )
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(f'Period ID: {period.id}')
            self.stdout.write(f'Period: {period.period_name}')
            self.stdout.write(
                f'Dates: {period.start_date} to {period.end_date}'
            )
            self.stdout.write(f'Total Items: {created_snapshots}')
            self.stdout.write(f'Total Value: €{total_value:,.2f}')
            self.stdout.write('Status: CLOSED ✓')
            self.stdout.write('')
            self.stdout.write(
                '✅ This period is now the baseline for future stocktakes!'
            )
            self.stdout.write(
                '✅ November stocktakes will use these as opening values!'
            )
            self.stdout.write(self.style.SUCCESS('=' * 60))

