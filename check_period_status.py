"""
Check October 2024 Period Status and W45 Snapshot
"""

import os
import sys
import django
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockSnapshot, StockPeriod
from hotel.models import Hotel


def main():
    print("=" * 60)
    print("OCTOBER 2024 PERIOD STATUS CHECK")
    print("=" * 60)
    
    hotel = Hotel.objects.first()
    period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)
    
    print(f"\n📅 Period: {period.period_name}")
    print(f"   ID: {period.id}")
    print(f"   Status: {'🔒 CLOSED' if period.is_closed else '🔓 OPEN'}")
    print(f"   Date Range: {period.start_date} to {period.end_date}")
    
    # Check W45
    try:
        item = StockItem.objects.get(hotel=hotel, sku='W45')
        snapshot = StockSnapshot.objects.get(hotel=hotel, item=item, period=period)
        
        print(f"\n✅ W45 - {item.name}")
        print(f"   Category: {item.category.code} - {item.category.name}")
        print(f"   Snapshot Value: €{snapshot.closing_stock_value}")
        print(f"   Full Units: {snapshot.closing_full_units}")
        print(f"   Partial Units: {snapshot.closing_partial_units}")
        
    except StockItem.DoesNotExist:
        print(f"\n❌ W45 not found in database")
    except StockSnapshot.DoesNotExist:
        print(f"\n❌ W45 snapshot not found for October 2024")
    
    # Calculate category totals
    spirits_snapshots = StockSnapshot.objects.filter(
        hotel=hotel, 
        period=period, 
        item__category__code='S'
    )
    wines_snapshots = StockSnapshot.objects.filter(
        hotel=hotel, 
        period=period, 
        item__category__code='W'
    )
    
    spirits_total = sum(s.closing_stock_value for s in spirits_snapshots)
    wines_total = sum(s.closing_stock_value for s in wines_snapshots)
    
    print(f"\n📊 Category Totals in Closed Period:")
    print(f"   Spirits (S): {spirits_snapshots.count()} items = €{spirits_total:,.2f}")
    print(f"   Wines (W): {wines_snapshots.count()} items = €{wines_total:,.2f}")
    
    # Grand total
    all_snapshots = StockSnapshot.objects.filter(hotel=hotel, period=period)
    grand_total = sum(s.closing_stock_value for s in all_snapshots)
    
    print(f"\n💰 Grand Total: {all_snapshots.count()} items = €{grand_total:,.2f}")
    print(f"   Excel Target: €27,306.51")
    from decimal import Decimal
    diff = grand_total - Decimal('27306.51')
    print(f"   Difference: €{diff:.2f}")
    
    print("\n" + "=" * 60)
    if period.is_closed:
        print("✅ Period is CLOSED - Stocktake is finalized!")
    else:
        print("⚠️  Period is OPEN - Need to close it!")
    print("=" * 60)


if __name__ == '__main__':
    main()
