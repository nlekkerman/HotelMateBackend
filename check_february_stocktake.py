"""
Check February stocktake line calculations
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine

# Find February stocktake
st = Stocktake.objects.filter(
    period_start__year=2025,
    period_start__month=2,
    hotel_id=2
).first()

if not st:
    print("No February stocktake found!")
    exit()

print("=" * 80)
print(f"FEBRUARY STOCKTAKE - ID: {st.id}")
print(f"Status: {st.status}")
print("=" * 80)

# Get bottled beer lines
lines = st.lines.filter(item__category__code='B')
print(f"\nBottled beer lines: {lines.count()}\n")

total_counted_value = Decimal('0')
total_opening_value = Decimal('0')

print("Sample items:")
print("-" * 80)

for line in lines[:5]:
    # Calculate counted value
    counted_servings = (line.counted_full_units * line.item.uom) + line.counted_partial_units
    cost_per = line.item.cost_per_serving or Decimal('0')
    counted_value = counted_servings * cost_per
    
    # Calculate opening value
    opening_value = line.opening_qty * cost_per
    
    total_counted_value += counted_value
    total_opening_value += opening_value
    
    print(f"\n{line.item.sku} - {line.item.name}")
    print(f"  Opening: {line.opening_qty} servings = €{opening_value:.2f}")
    print(f"  Counted: {line.counted_full_units} cases + {line.counted_partial_units} bottles = {counted_servings} servings")
    print(f"  Cost per serving: €{cost_per:.4f}")
    print(f"  Counted value: €{counted_value:.2f}")
    print(f"  Variance: €{counted_value - opening_value:.2f}")

print("\n" + "=" * 80)
print("ALL BOTTLED BEERS TOTALS:")
print("=" * 80)

# Calculate full totals
total_counted_value = Decimal('0')
total_opening_value = Decimal('0')

for line in lines:
    counted_servings = (line.counted_full_units * line.item.uom) + line.counted_partial_units
    cost_per = line.item.cost_per_serving or Decimal('0')
    counted_value = counted_servings * cost_per
    opening_value = line.opening_qty * cost_per
    
    total_counted_value += counted_value
    total_opening_value += opening_value

variance = total_counted_value - total_opening_value

print(f"Opening stock value:  €{total_opening_value:.2f}")
print(f"Counted stock value:  €{total_counted_value:.2f}")
print(f"Variance:             €{variance:.2f}")
print(f"\nExpected (Excel):     €754.36")
print(f"UI showing:           €989.26")
print(f"Difference:           €{Decimal('989.26') - Decimal('754.36'):.2f}")

print("\n" + "=" * 80)
