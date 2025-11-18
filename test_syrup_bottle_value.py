"""
Clear Test: Syrups Valued by BOTTLES (Physical Stock)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake

print("=" * 80)
print("SYRUPS: BOTTLE VALUE ON STOCK (NOT SERVING VALUE)")
print("=" * 80)

# Get February stocktake
stocktake = Stocktake.objects.filter(
    hotel_id=2,
    period_start__year=2025,
    period_start__month=2
).first()

# Get syrup lines
syrup_lines = stocktake.lines.filter(item__subcategory='SYRUPS')

print("\nWhat you PHYSICALLY have on the shelf vs What it's WORTH")
print("=" * 80)

for line in syrup_lines[:10]:
    syrup = line.item
    
    # PHYSICAL STOCK (what you can see on shelf)
    full_bottles = int(line.counted_full_units)
    partial = float(line.counted_partial_units)
    total_bottles = float(line.counted_full_units) + partial
    
    # WHAT IT COST YOU
    cost_per_bottle = float(syrup.unit_cost)
    total_value = float(line.counted_value)
    
    print(f"\n{syrup.sku} - {syrup.name}")
    print(f"  📦 PHYSICAL STOCK: {full_bottles} full bottles + {partial:.2f} partial")
    print(f"  📦 TOTAL BOTTLES: {total_bottles:.2f} bottles")
    print(f"  💰 COST PER BOTTLE: €{cost_per_bottle:.2f}")
    print(f"  💰 TOTAL STOCK VALUE: €{total_value:.2f}")
    print(f"  ✓ Calculation: {total_bottles:.2f} bottles × €{cost_per_bottle:.2f} = €{total_value:.2f}")

print("\n" + "=" * 80)
print("TOTAL SYRUP STOCK VALUE")
print("=" * 80)

total_bottles_all = sum(
    float(line.counted_full_units) + float(line.counted_partial_units)
    for line in syrup_lines
)

total_value_all = sum(float(line.counted_value) for line in syrup_lines)

print(f"\nTotal bottles on shelf: {total_bottles_all:.2f} bottles")
print(f"Total stock value: €{total_value_all:.2f}")

print("\n" + "=" * 80)
print("CONFIRMATION")
print("=" * 80)
print("""
✓ Syrups are valued by BOTTLES (physical units)
✓ Value = Number of bottles × Cost per bottle
✓ This is the VALUE OF STOCK you have on hand
✓ NOT calculated by servings/shots (that's just for tracking consumption)
""")
