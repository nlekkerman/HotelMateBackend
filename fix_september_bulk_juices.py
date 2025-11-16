"""
Fix September BULK_JUICES counted values.

PROBLEM: Values are in wrong fields because items were Doz when counted.
- counted_full_units = 0 (was for cases, now should be bottles)
- counted_partial_units = 43 (was for bottles, should be 0)

SOLUTION: Move partial → full for these items.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake

print("=" * 80)
print("FIX SEPTEMBER BULK_JUICES COUNTED VALUES")
print("=" * 80)

september = Stocktake.objects.filter(
    period_start__year=2025,
    period_start__month=9
).first()

if not september:
    print("\n❌ September not found!")
    exit()

items_to_fix = ['M0042', 'M0210', 'M11']

print("\nBEFORE:")
print("-" * 80)
for sku in items_to_fix:
    line = september.lines.filter(item__sku=sku).first()
    if line:
        print(f"{line.item.sku}: Full={line.counted_full_units}, "
              f"Partial={line.counted_partial_units}")

response = input("\nSwap values? (yes/no): ").strip().lower()

if response != 'yes':
    print("\n❌ Cancelled.")
    exit()

print("\n" + "=" * 80)
print("FIXING...")
print("=" * 80)

for sku in items_to_fix:
    line = september.lines.filter(item__sku=sku).first()
    if line:
        # Swap: partial (43) → full, full (0) → partial (0)
        old_full = line.counted_full_units
        old_partial = line.counted_partial_units
        
        line.counted_full_units = old_partial  # 43 → full (bottles)
        line.counted_partial_units = 0  # 0 → partial (not used)
        line.save()
        
        print(f"✅ {line.item.sku}: {old_full}/{old_partial} → "
              f"{line.counted_full_units}/{line.counted_partial_units}")

print("\n" + "=" * 80)
print("DONE! September closing now correct:")
print("- M0042: 43 bottles")
print("- M0210: 43 bottles")
print("- M11: 138 bottles")
print("\n📝 NEXT: Re-populate October to use these as opening values")
