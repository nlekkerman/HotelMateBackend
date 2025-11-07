from django.core.management.base import BaseCommand
from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel


class Command(BaseCommand):
    help = 'Fetch and display October 2025 stocktake data'

    def handle(self, *args, **options):
        hotel = Hotel.objects.first()
        
        self.stdout.write("=" * 60)
        self.stdout.write("FETCHING OCTOBER 2025 STOCKTAKE")
        self.stdout.write("=" * 60)
        
        # Get October 2025 period
        try:
            period = StockPeriod.objects.get(
                hotel=hotel,
                year=2025,
                month=10
            )
        except StockPeriod.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ October 2025 period not found!"))
            return
        
        self.stdout.write(f"\n✅ Found Period:")
        self.stdout.write(f"  ID: {period.id}")
        self.stdout.write(f"  Name: {period.period_name}")
        self.stdout.write(f"  Type: {period.period_type}")
        self.stdout.write(f"  Status: {'Closed' if period.is_closed else 'Open'}")
        self.stdout.write(f"  Dates: {period.start_date} to {period.end_date}")
        
        # Get snapshots
        snapshots = StockSnapshot.objects.filter(period=period)
        snapshot_count = snapshots.count()
        
        self.stdout.write(f"\n📦 Snapshots: {snapshot_count}")
        
        # Calculate total value
        total_value = sum(s.closing_stock_value for s in snapshots)
        self.stdout.write(f"💰 Total Value: €{total_value:,.2f}")
        
        # Show first 5 items
        self.stdout.write("\n📋 Sample Items (first 5):")
        self.stdout.write("-" * 60)
        
        for snapshot in snapshots[:5]:
            full = snapshot.closing_full_units
            partial = snapshot.closing_partial_units
            total = full + partial
            value = snapshot.closing_stock_value
            
            self.stdout.write(
                f"  {snapshot.item.sku}: {snapshot.item.name}"
            )
            self.stdout.write(
                f"    Stock: {full} full + {partial} partial = {total}"
            )
            self.stdout.write(f"    Value: €{value:.2f}")
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ FETCH COMPLETE"))
        self.stdout.write("=" * 60)
