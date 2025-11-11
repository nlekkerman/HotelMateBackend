"""
Delete all stock periods, stocktakes, and snapshots to start fresh
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake, StocktakeLine, StockSnapshot
from hotel.models import Hotel

print("=" * 80)
print("DELETE ALL STOCK DATA")
print("=" * 80)
print()

hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"🏨 Hotel: {hotel.name}")
print()

# Count existing data
periods_count = StockPeriod.objects.filter(hotel=hotel).count()
stocktakes_count = Stocktake.objects.filter(hotel=hotel).count()
lines_count = StocktakeLine.objects.filter(stocktake__hotel=hotel).count()
snapshots_count = StockSnapshot.objects.filter(hotel=hotel).count()

print("Current Data:")
print(f"  Periods: {periods_count}")
print(f"  Stocktakes: {stocktakes_count}")
print(f"  Stocktake Lines: {lines_count}")
print(f"  Stock Snapshots: {snapshots_count}")
print()

if periods_count == 0 and stocktakes_count == 0 and snapshots_count == 0:
    print("✅ No data to delete!")
    exit(0)

print("⚠️  WARNING: This will delete ALL stock tracking data!")
print()
print("Deleting in order:")
print("  1. Stocktake Lines")
print("  2. Stocktakes")
print("  3. Stock Snapshots")
print("  4. Stock Periods")
print()

# Delete in correct order to avoid foreign key issues
print("🗑️  Deleting stocktake lines...")
deleted_lines = StocktakeLine.objects.filter(stocktake__hotel=hotel).delete()[0]
print(f"   ✓ Deleted {deleted_lines} stocktake lines")

print("🗑️  Deleting stocktakes...")
deleted_stocktakes = Stocktake.objects.filter(hotel=hotel).delete()[0]
print(f"   ✓ Deleted {deleted_stocktakes} stocktakes")

print("🗑️  Deleting stock snapshots...")
deleted_snapshots = StockSnapshot.objects.filter(hotel=hotel).delete()[0]
print(f"   ✓ Deleted {deleted_snapshots} stock snapshots")

print("🗑️  Deleting stock periods...")
deleted_periods = StockPeriod.objects.filter(hotel=hotel).delete()[0]
print(f"   ✓ Deleted {deleted_periods} stock periods")

print()
print("=" * 80)
print("✅ ALL STOCK DATA DELETED!")
print("=" * 80)
print()
print("You can now start fresh:")
print("  1. Create October 2025 period as baseline")
print("  2. Create November 2025 period")
print("  3. And so on...")
print("=" * 80)
