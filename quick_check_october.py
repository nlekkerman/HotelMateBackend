"""Quick check of October 2025 stocktake totals"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}\n")

# Find October 2025
periods = StockPeriod.objects.filter(hotel=hotel, year=2025, month=10)
if not periods.exists():
    print("❌ No October 2025 period found!")
    print("\nAvailable periods:")
    for p in StockPeriod.objects.filter(hotel=hotel).order_by('-start_date')[:5]:
        print(f"  - {p.period_name} (ID: {p.id})")
else:
    period = periods.first()
    print(f"✓ Found: {period.period_name}")
    print(f"  Status: {'CLOSED' if period.is_closed else 'OPEN'}")
    
    snapshots = StockSnapshot.objects.filter(period=period)
    print(f"  Snapshots: {snapshots.count()}\n")
    
    # Expected values
    expected = {
        'D': Decimal('5311.62'),
        'B': Decimal('2288.46'),
        'S': Decimal('11063.66'),
        'M': Decimal('3062.43'),
        'W': Decimal('5580.35')
    }
    
    print("Category Totals:")
    print("-" * 60)
    total_db = Decimal('0.00')
    total_exp = Decimal('0.00')
    
    for cat in ['D', 'B', 'S', 'M', 'W']:
        cat_snaps = snapshots.filter(item__category_id=cat)
        cat_total = sum(s.closing_stock_value for s in cat_snaps)
        total_db += cat_total
        total_exp += expected[cat]
        diff = cat_total - expected[cat]
        status = "✅" if abs(diff) < 1 else "❌"
        print(f"{status} {cat}: €{cat_total:>10.2f}  (expected: €{expected[cat]:>10.2f}, diff: €{diff:>8.2f})")
    
    print("-" * 60)
    total_diff = total_db - total_exp
    status = "✅" if abs(total_diff) < 1 else "❌"
    print(f"{status} TOTAL: €{total_db:>10.2f}  (expected: €{total_exp:>10.2f}, diff: €{total_diff:>8.2f})")
