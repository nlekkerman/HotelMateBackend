"""
Fix SYRUPS counted_partial_units in February stocktake.

Problem: Syrups have counted_partial_units set to ml values (350, 500, etc.)
         instead of decimal fractions (0.5, 0.7, etc.)

Solution: Convert ml values back to decimal bottle fractions.
         Example: 350ml on a 700ml bottle = 0.5 bottles
                  500ml on a 1000ml bottle = 0.5 bottles
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, Stocktake
from decimal import Decimal

# Get February stocktake
february = Stocktake.objects.filter(
    hotel_id=2,
    period_start__month=2,
    period_start__year=2025
).first()

if not february:
    print("❌ February stocktake not found")
    exit()

print("=" * 80)
print(f"FIXING SYRUPS IN STOCKTAKE #{february.id}")
print("=" * 80)

# Get all syrup lines
syrup_lines = StocktakeLine.objects.filter(
    stocktake=february,
    item__subcategory='SYRUPS'
).select_related('item')

print(f"\nFound {syrup_lines.count()} syrup lines\n")

fixed_count = 0
skip_count = 0

for line in syrup_lines:
    bottle_size_ml = line.item.uom
    current_partial = line.counted_partial_units
    
    # Check if value needs fixing (if it's > 1, it's probably ml not decimal)
    if current_partial > Decimal('1.0'):
        # Convert ml to decimal fraction
        # Example: 350ml / 700ml bottle = 0.5 bottles
        decimal_fraction = current_partial / bottle_size_ml
        
        print(f"✏️  {line.item.sku:<10} {line.item.name:<45}")
        print(f"    Bottle size: {bottle_size_ml}ml")
        print(f"    OLD: {line.counted_full_units} bottles + {current_partial}ml")
        print(f"    NEW: {line.counted_full_units} bottles + {decimal_fraction:.2f} (decimal)")
        
        # Update
        line.counted_partial_units = decimal_fraction
        line.save()
        
        fixed_count += 1
        print(f"    ✅ Fixed!\n")
    else:
        skip_count += 1
        print(f"⏭️  {line.item.sku:<10} {line.item.name:<45} - already correct ({current_partial})")

print("\n" + "=" * 80)
print(f"✅ Fixed {fixed_count} syrup lines")
print(f"⏭️  Skipped {skip_count} lines (already correct)")
print("=" * 80)
