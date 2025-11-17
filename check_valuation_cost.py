"""
Check valuation_cost on stocktake lines
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake

st = Stocktake.objects.filter(
    period_start__year=2025,
    period_start__month=2,
    hotel_id=2
).first()

if not st:
    print("No stocktake found!")
    exit()

lines = st.lines.filter(item__category__code='B').order_by('item__sku')

print("=" * 80)
print("VALUATION COST CHECK")
print("=" * 80)
print(f"{'SKU':<10} {'Name':<25} {'Val Cost':<12} {'Unit Cost':<12} {'CPS':<12}")
print("-" * 80)

for line in lines[:10]:
    print(f"{line.item.sku:<10} {line.item.name[:23]:<25} "
          f"{line.valuation_cost:>10.4f} "
          f"{line.item.unit_cost:>10.4f} "
          f"{line.item.cost_per_serving:>10.4f}")

print("\n" + "=" * 80)
print("CALCULATION CHECK - First item:")
print("=" * 80)

line = lines.first()
counted_servings = (line.counted_full_units * line.item.uom) + line.counted_partial_units

print(f"\nItem: {line.item.name}")
print(f"Counted: {line.counted_full_units} cases + {line.counted_partial_units} bottles")
print(f"Total servings: {counted_servings}")
print(f"\nValuation cost (from line): {line.valuation_cost}")
print(f"Unit cost (from item): {line.item.unit_cost}")
print(f"Cost per serving (from item): {line.item.cost_per_serving}")
print(f"\nMethod 1 (valuation_cost × servings): {counted_servings * line.valuation_cost:.2f}")
print(f"Method 2 (cost_per_serving × servings): {counted_servings * line.item.cost_per_serving:.2f}")
print(f"Expected value: €26.03")

print("\n" + "=" * 80)
