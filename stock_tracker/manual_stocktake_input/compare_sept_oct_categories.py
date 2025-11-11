"""
Compare September closing vs October closing stock by categories
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("SEPTEMBER vs OCTOBER CLOSING STOCK COMPARISON BY CATEGORY")
print("=" * 100)
print()

hotel = Hotel.objects.first()

sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)

oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)

categories = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals/Syrups'
}

print(f"{'Category':<20} {'Sept Closing':<15} {'Oct Closing':<15} {'Difference':<15} {'Change %':<10}")
print("-" * 100)

grand_total_sept = Decimal('0.00')
grand_total_oct = Decimal('0.00')

for code, name in categories.items():
    # September closing
    sept_snapshots = StockSnapshot.objects.filter(
        period=sept_period,
        item__category=code
    )
    sept_total = sum(
        snap.closing_stock_value for snap in sept_snapshots
    )
    
    # October closing
    oct_snapshots = StockSnapshot.objects.filter(
        period=oct_period,
        item__category=code
    )
    oct_total = sum(
        snap.closing_stock_value for snap in oct_snapshots
    )
    
    difference = oct_total - sept_total
    change_pct = (difference / sept_total * 100) if sept_total > 0 else Decimal('0.00')
    
    grand_total_sept += sept_total
    grand_total_oct += oct_total
    
    sign = '+' if difference >= 0 else ''
    print(f"{name:<20} €{sept_total:>12,.2f} €{oct_total:>12,.2f} {sign}€{difference:>11,.2f} {change_pct:>8.1f}%")

print("-" * 100)
difference = grand_total_oct - grand_total_sept
change_pct = (difference / grand_total_sept * 100) if grand_total_sept > 0 else Decimal('0.00')
sign = '+' if difference >= 0 else ''
print(f"{'GRAND TOTAL':<20} €{grand_total_sept:>12,.2f} €{grand_total_oct:>12,.2f} {sign}€{difference:>11,.2f} {change_pct:>8.1f}%")

print()
print("=" * 100)

# Detailed breakdown
print()
print("DETAILED ITEM COUNT BY CATEGORY")
print("=" * 100)
print()

for code, name in categories.items():
    sept_count = StockSnapshot.objects.filter(
        period=sept_period,
        item__category=code
    ).count()
    
    oct_count = StockSnapshot.objects.filter(
        period=oct_period,
        item__category=code
    ).count()
    
    print(f"{name:<20} Sept: {sept_count:>3} items  |  Oct: {oct_count:>3} items")

print()
print("=" * 100)
