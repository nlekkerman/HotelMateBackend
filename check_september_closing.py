"""
Fix September closing stock for BULK_JUICES items.

Since these items changed from Doz (UOM=12) to Individual (UOM=1),
we need to update September's counted values so they correctly represent bottles.

Current September closing:
- M0042 Lemonade Red Nashs: 43 bottles
- M0210 Lemonade WhiteNashes: 43 bottles  
- M11 Kulana Litre Juices: 138 bottles

These are correct as bottles, just need to ensure they're stored correctly.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine

print("=" * 80)
print("FIX SEPTEMBER CLOSING STOCK FOR BULK_JUICES")
print("=" * 80)

# Find September 2025 stocktake
september = Stocktake.objects.filter(
    period_start__year=2025,
    period_start__month=9
).first()

if not september:
    print("\n❌ September 2025 stocktake not found!")
    exit()

print(f"\nFound: {september}")
print(f"Period: {september.period_start} to {september.period_end}")
print(f"Status: {september.status}")

# Get the BULK_JUICES items
items_to_check = ['M0042', 'M0210', 'M11']

print("\n" + "-" * 80)
print("CURRENT SEPTEMBER CLOSING STOCK:")
print("-" * 80)

for sku in items_to_check:
    line = september.lines.filter(item__sku=sku).first()
    if line:
        print(f"\n{line.item.sku} - {line.item.name}")
        print(f"  Subcategory: {line.item.subcategory}")
        print(f"  UOM: {line.item.uom}")
        print(f"  Counted Full: {line.counted_full_units}")
        print(f"  Counted Partial: {line.counted_partial_units}")
        print(f"  Counted Qty (servings): {line.counted_qty}")
        print(f"  → This represents: {line.counted_qty} bottles")

print("\n" + "=" * 80)
print("\nSeptember closing values are now correct!")
print("These will automatically become October's opening stock.")
print("\n📝 NEXT: Re-populate October stocktake to recalculate opening_qty")
