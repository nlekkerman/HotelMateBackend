import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 100)
print("MINERALS/SYRUPS ANALYSIS - FINDING THE €64.42 DIFFERENCE")
print("=" * 100)

hotel = Hotel.objects.first()

stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).first()

minerals_lines = StocktakeLine.objects.filter(
    stocktake=stocktake,
    item__category__code='M'
).select_related('item').order_by('item__sku')

print(f"\nTotal Minerals Items: {minerals_lines.count()}")

items_with_zero_cost = []
grand_total = Decimal('0.00')

print(f"\n{'SKU':<20} {'Name':<40} {'Counted':>10} {'Cost':>12} {'Value':>12}")
print("-" * 100)

for line in minerals_lines:
    grand_total += line.counted_value
    
    if line.item.unit_cost == 0:
        items_with_zero_cost.append(line)
    
    print(f"{line.item.sku:<20} {line.item.name[:40]:<40} {line.counted_qty:>10.2f} "
          f"€{line.item.unit_cost:>10.2f} €{line.counted_value:>10.2f}")

print("\n" + "=" * 100)
print(f"TOTAL MINERALS: €{grand_total:,.2f}")

if items_with_zero_cost:
    print(f"\n⚠️  {len(items_with_zero_cost)} items have ZERO unit cost:")
    for line in items_with_zero_cost:
        print(f"  {line.item.sku} - {line.item.name}")

excel_total = Decimal('2986.95')
print(f"\nExcel expects: €{excel_total:,.2f}")
print(f"System has:    €{grand_total:,.2f}")
print(f"Difference:    €{grand_total - excel_total:+,.2f}")

print("\n" + "=" * 100)
