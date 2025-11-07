"""
Clean up October 2025 data to prepare for fresh upload

This script deletes:
1. October 2025 StockPeriod (cascades to snapshots and stocktakes)
2. All StockItem entries
3. Leaves StockCategory entries intact

Run from project root:
    python cleanup_october_data.py
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockItem, StockSnapshot, Stocktake
from hotel.models import Hotel


def main():
    """Main execution"""
    print("=" * 60)
    print("CLEANUP OCTOBER 2025 DATA")
    print("=" * 60)
    
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hotel found in database!")
            return
        print(f"\n🏨 Hotel: {hotel.name}")
    except Exception as e:
        print(f"❌ Error getting hotel: {e}")
        return
    
    # Check current state
    print("\n📊 Current State:")
    
    periods = StockPeriod.objects.filter(hotel=hotel, period_name="October 2025")
    period_count = periods.count()
    print(f"  October 2025 Periods: {period_count}")
    
    if period_count > 0:
        period = periods.first()
        snapshot_count = StockSnapshot.objects.filter(
            hotel=hotel, period=period
        ).count()
        stocktake_count = Stocktake.objects.filter(
            hotel=hotel,
            period_start=period.start_date,
            period_end=period.end_date
        ).count()
        print(f"  Snapshots: {snapshot_count}")
        print(f"  Stocktakes: {stocktake_count}")
    
    item_count = StockItem.objects.filter(hotel=hotel).count()
    print(f"  Stock Items: {item_count}")
    
    # Confirm deletion
    print("\n⚠️  WARNING: This will delete:")
    print("  - October 2025 period")
    print("  - All associated snapshots")
    print("  - All associated stocktakes")
    print(f"  - All {item_count} stock items")
    print("\n  Stock Categories will be preserved.")
    
    response = input("\n❓ Type 'YES' to proceed with deletion: ")
    
    if response.strip().upper() != 'YES':
        print("\n❌ Cleanup cancelled.")
        return
    
    # Perform deletion
    print("\n🗑️  Deleting data...")
    
    # Delete October 2025 period (cascades to snapshots and stocktakes)
    if period_count > 0:
        deleted_periods, details = periods.delete()
        print(f"  ✓ Deleted October 2025 period")
        print(f"    - Periods: {details.get('stock_tracker.StockPeriod', 0)}")
        print(f"    - Snapshots: {details.get('stock_tracker.StockSnapshot', 0)}")
        print(f"    - Stocktakes: {details.get('stock_tracker.Stocktake', 0)}")
        print(f"    - Stocktake Lines: {details.get('stock_tracker.StocktakeLine', 0)}")
    
    # Delete all stock items
    deleted_items, item_details = StockItem.objects.filter(hotel=hotel).delete()
    print(f"  ✓ Deleted {item_details.get('stock_tracker.StockItem', 0)} stock items")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("  1. Run: python upload_october_stock.py")
    print("  2. Run: python manage.py close_october_period --confirm")
    print("  3. Run: python manage.py create_october_stocktake --confirm")
    print("  4. Verify: python manage.py check_october_period")


if __name__ == '__main__':
    main()
