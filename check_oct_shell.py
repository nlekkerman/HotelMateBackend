"""Quick check via Django shell"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel
from decimal import Decimal

hotel = Hotel.objects.first()
print(f"\nHotel: {hotel.name}\n")

# Find October 2024
periods = StockPeriod.objects.filter(hotel=hotel, year=2024, month=10)
if not periods.exists():
    print("No October 2024 period found!")
    for p in StockPeriod.objects.filter(hotel=hotel).order_by('-start_date')[:5]:
        print(f"  - {p.period_name}")
else:
    period = periods.first()
    print(f"Period: {period.period_name}")
    print(f"Status: {'CLOSED' if period.is_closed else 'OPEN'}")
    
    snapshots = StockSnapshot.objects.filter(period=period)
    print(f"Snapshots: {snapshots.count()}\n")
    
    expected = {
        'D': Decimal('5311.62'),
        'B': Decimal('2288.46'),
        'S': Decimal('11063.66'),
        'M': Decimal('3062.43'),
        'W': Decimal('5580.35')
    }
    
    print("=" * 70)
    print(f"{'Cat':<4} {'Database':>12} {'Expected':>12} {'Diff':>12} {'Status'}")
    print("=" * 70)
    
    total_db = Decimal('0.00')
    total_exp = Decimal('0.00')
    
    for cat in ['D', 'B', 'S', 'M', 'W']:
        cat_snaps = snapshots.filter(item__category_id=cat)
        cat_total = sum(s.closing_stock_value for s in cat_snaps)
        total_db += cat_total
        total_exp += expected[cat]
        diff = cat_total - expected[cat]
        status = "MATCH" if abs(diff) < 1 else "DIFF"
        print(f"{cat:<4} €{cat_total:>10.2f} €{expected[cat]:>10.2f} €{diff:>10.2f} {status}")
    
    print("=" * 70)
    total_diff = total_db - total_exp
    status = "MATCH" if abs(total_diff) < 1 else "DIFF"
    print(f"{'TOT':<4} €{total_db:>10.2f} €{total_exp:>10.2f} €{total_diff:>10.2f} {status}")
    print("=" * 70)
