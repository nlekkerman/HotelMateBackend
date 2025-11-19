import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 100)
print("WINE ANALYSIS - FINDING THE €29.74 DIFFERENCE")
print("=" * 100)

hotel = Hotel.objects.first()

stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).first()

wine_lines = StocktakeLine.objects.filter(
    stocktake=stocktake,
    item__category__code='W'
).select_related('item').order_by('item__sku')

print(f"\nTotal Wine Items: {wine_lines.count()}")

total_value = Decimal('0.00')
items_with_zero_cost = []

print(f"\n{'SKU':<20} {'Name':<40} {'Counted':>10} {'Unit Cost':>12} {'Value':>12}")
print("-" * 100)

for line in wine_lines:
    total_value += line.counted_value
    
    if line.item.unit_cost == 0:
        items_with_zero_cost.append(line)
    
    print(f"{line.item.sku:<20} {line.item.name[:40]:<40} {line.counted_qty:>10.2f} €{line.item.unit_cost:>10.2f} €{line.counted_value:>10.2f}")

print("-" * 100)
print(f"{'TOTAL':<20} {'':<40} {'':<10} {'':<12} €{total_value:>10.2f}")

if items_with_zero_cost:
    print(f"\n⚠️  WARNING: {len(items_with_zero_cost)} items have ZERO unit cost:")
    for line in items_with_zero_cost:
        print(f"  {line.item.sku} - {line.item.name}")

print(f"\nExcel expects: €1,355.87")
print(f"System has:    €{total_value:,.2f}")
print(f"Difference:    €{total_value - Decimal('1355.87'):+,.2f}")

print("\n" + "=" * 100)
