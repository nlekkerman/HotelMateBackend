from django.core.management.base import BaseCommand
from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel
from datetime import date
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create October 2025 stocktake period (closed)'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("CREATE OCTOBER 2025 STOCKTAKE (CLOSED)")
        self.stdout.write("=" * 60)
        
        hotel = Hotel.objects.first()
        self.stdout.write(f"\n🏨 Hotel: {hotel.name}\n")
        
        # Create October 2025 period
        self.stdout.write("📅 Creating October 2025 Period...")
        period, created = StockPeriod.objects.get_or_create(
            hotel=hotel,
            period_type='MONTHLY',
            year=2025,
            month=10,
            defaults={
                'is_closed': True,
                'start_date': date(2025, 10, 1),
                'end_date': date(2025, 10, 31),
                'period_name': 'October 2025'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Created: October 2025 (ID: {period.id})")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Already exists (ID: {period.id})")
            )
        
        # Get all stock items
        items = StockItem.objects.filter(hotel=hotel)
        total_items = items.count()
        
        self.stdout.write(f"\n📦 Found {total_items} stock items")
        self.stdout.write("🔄 Creating snapshots...\n")
        
        created_count = 0
        updated_count = 0
        
        for item in items:
            snapshot, was_created = StockSnapshot.objects.update_or_create(
                hotel=hotel,
                item=item,
                period=period,
                defaults={
                    'closing_full_units': item.current_full_units or Decimal('0'),
                    'closing_partial_units': item.current_partial_units or Decimal('0'),
                    'unit_cost': item.unit_cost,
                    'cost_per_serving': item.cost_per_serving,
                    'closing_stock_value': item.total_stock_value
                }
            )
            
            if was_created:
                created_count += 1
            else:
                updated_count += 1
            
            if (created_count + updated_count) % 50 == 0:
                self.stdout.write(f"  Processed {created_count + updated_count}/{total_items}...")
        
        snapshots = StockSnapshot.objects.filter(period=period)
        total_value = sum(s.closing_stock_value for s in snapshots)
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ OCTOBER 2025 CREATED"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"""
Period ID: {period.id}
Month: {period.period_name}
Status: {"Closed" if period.is_closed else "Open"}
Date Range: {period.start_date} to {period.end_date}

Snapshots Created: {created_count}
Snapshots Updated: {updated_count}
Total Items: {total_items}
Total Stock Value: €{total_value:,.2f}
""")
