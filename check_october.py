import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from django.db.models import Sum

# Get October stocktake (ID 18)
stocktake = Stocktake.objects.get(id=18)

print("=" * 80)
print(f"CHECKING OCTOBER STOCKTAKE #{stocktake.id}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print(f"Status: {stocktake.status}")
print("=" * 80)

# Check Wine items
wine_lines = stocktake.lines.filter(item__category__name="Wine")
print(f"\nTotal Wine lines: {wine_lines.count()}")

# Calculate totals
total_expected = sum(line.expected_value for line in wine_lines)
total_counted = sum(line.counted_value for line in wine_lines)
total_variance = sum(line.variance_value for line in wine_lines)

print(f"\nWINE TOTALS:")
print(f"  Expected Value: €{total_expected:,.2f}")
print(f"  Counted Value: €{total_counted:,.2f}")
print(f"  Variance Value: €{total_variance:,.2f}")

# Check if any wine was counted
wine_counted = wine_lines.filter(counted_qty__gt=0)
print(f"\nWine items with counts > 0: {wine_counted.count()}")

if wine_counted.count() > 0:
    print("\n✅ WINE WAS COUNTED IN OCTOBER! Here are examples:")
    for line in wine_counted[:5]:
        print(f"\n  Item: {line.item.name}")
        print(f"    Counted Full: {line.counted_full_units}")
        print(f"    Counted Partial: {line.counted_partial_units}")
        print(f"    Counted Qty: {line.counted_qty}")
        print(f"    Counted Value: €{line.counted_value:,.2f}")
else:
    print("\n❌ Wine was NOT counted in October either")

# Show all categories
print("\n" + "=" * 80)
print("ALL CATEGORIES IN OCTOBER:")
print("=" * 80)
from stock_tracker.models import StockCategory
categories = StockCategory.objects.filter(
    stock_items__stocktake_lines__stocktake=stocktake
).distinct()

for cat in categories:
    cat_lines = stocktake.lines.filter(item__category=cat)
    cat_expected = sum(line.expected_value for line in cat_lines)
    cat_counted = sum(line.counted_value for line in cat_lines)
    cat_variance = sum(line.variance_value for line in cat_lines)
    print(f"\n{cat.name}:")
    print(f"  Expected: €{cat_expected:,.2f}")
    print(f"  Counted: €{cat_counted:,.2f}")
    print(f"  Variance: €{cat_variance:,.2f}")
