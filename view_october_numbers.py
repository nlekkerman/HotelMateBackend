"""
View October 2025 Stocktake Line Numbers
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake

# Get October 2025 stocktake (ID 18)
stocktake = Stocktake.objects.get(id=18)

print("=" * 120)
print(f"OCTOBER 2025 STOCKTAKE - ID: {stocktake.id}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print(f"Status: {stocktake.status}")
print("=" * 120)

# Get first 10 lines as sample
lines = stocktake.lines.all().select_related('item', 'item__category')[:10]

for line in lines:
    print(f"\n{line.item.sku} - {line.item.name}")
    print(f"  Category: {line.item.category.code} - {line.item.category.name}")
    print(f"  Size: {line.item.size} | UOM: {line.item.uom}")
    print(f"\n  QUANTITIES (in servings):")
    print(f"    Opening Qty:  {line.opening_qty}")
    print(f"    Purchases:    {line.purchases}")
    print(f"    Expected Qty: {line.expected_qty}")
    print(f"    Counted Qty:  {line.counted_qty}")
    print(f"    Variance:     {line.variance_qty}")
    print(f"\n  COUNTED UNITS:")
    print(f"    Full Units:    {line.counted_full_units}")
    print(f"    Partial Units: {line.counted_partial_units}")
    print(f"\n  COSTS:")
    print(f"    Valuation Cost:  €{line.valuation_cost}")
    print(f"    Expected Value:  €{line.expected_value}")
    print(f"    Counted Value:   €{line.counted_value}")
    print(f"    Variance Value:  €{line.variance_value}")
    print("-" * 120)

print(f"\nTotal Lines in Stocktake: {stocktake.lines.count()}")
print("\nShowing first 10 items only")
