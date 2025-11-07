"""
Management command to check October 2025 period status.
"""
from django.core.management.base import BaseCommand
from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel


class Command(BaseCommand):
    help = 'Check October 2025 period status'

    def handle(self, *args, **options):
        hotel_id = 2  # Hardcoded for Hotel Killarney
        
        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Hotel with ID {hotel_id} not found')
            )
            return

        self.stdout.write(f'Checking hotel: {hotel.name}')
        self.stdout.write('')

        # Check for October 2025 period
        try:
            period = StockPeriod.objects.get(
                hotel=hotel,
                period_type='MONTHLY',
                year=2025,
                month=10
            )
            
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('✅ October 2025 Period Found'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(f'Period ID: {period.id}')
            self.stdout.write(f'Period Name: {period.period_name}')
            self.stdout.write(f'Start Date: {period.start_date}')
            self.stdout.write(f'End Date: {period.end_date}')
            self.stdout.write(f'Period Type: {period.period_type}')
            self.stdout.write(f'Status: {"CLOSED ✓" if period.is_closed else "OPEN"}')
            
            if period.closed_at:
                self.stdout.write(f'Closed At: {period.closed_at}')
            
            # Check snapshots
            snapshots = StockSnapshot.objects.filter(
                hotel=hotel,
                period=period
            )
            
            snapshot_count = snapshots.count()
            self.stdout.write('')
            self.stdout.write(f'Snapshots: {snapshot_count}')
            
            if snapshot_count > 0:
                total_value = sum(
                    snapshot.closing_stock_value
                    for snapshot in snapshots
                )
                self.stdout.write(f'Total Stock Value: €{total_value:,.2f}')
                
                # Category breakdown
                from django.db.models import Count, Sum
                category_breakdown = snapshots.values(
                    'item__category__code',
                    'item__category__name'
                ).annotate(
                    count=Count('id'),
                    total=Sum('closing_stock_value')
                ).order_by('item__category__code')
                
                self.stdout.write('')
                self.stdout.write('Category Breakdown:')
                for cat in category_breakdown:
                    self.stdout.write(
                        f"  {cat['item__category__code']} - "
                        f"{cat['item__category__name']}: "
                        f"{cat['count']} items, "
                        f"€{cat['total']:,.2f}"
                    )
            
            self.stdout.write(self.style.SUCCESS('=' * 60))
            
            if period.is_closed and snapshot_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        '✅ Period is ready for stocktake creation!'
                    )
                )
            elif not period.is_closed:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️  Period is not closed yet. Run close_october_period first.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️  No snapshots found. Run close_october_period first.'
                    )
                )
            
        except StockPeriod.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ October 2025 period not found')
            )
            self.stdout.write('')
            self.stdout.write(
                'Run this command to create it:'
            )
            self.stdout.write(
                '  python manage.py close_october_period --confirm'
            )
