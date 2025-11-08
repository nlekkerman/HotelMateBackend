"""
Test what display fields Stocktake Lines should have
Similar to Snapshot display fields
"""
import os
import sys
import django

# Setup Django environment
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

if __name__ == "__main__":
    django.setup()

from stock_tracker.models import (
    Stocktake,
    StocktakeLine,
    StockPeriod,
    StockSnapshot
)
from decimal import Decimal

print("=" * 80)
print("STOCKTAKE LINE DISPLAY FIELDS NEEDED")
print("=" * 80)

# Get stocktake with some data
stocktake = Stocktake.objects.get(id=4)
line = stocktake.lines.select_related('item', 'item__category').first()

print(f"\nLine: {line.item.name} ({line.item.sku})")
print(f"Category: {line.item.category.code}")
print(f"UOM: {line.item.uom}")

# Get corresponding snapshot to compare
period = StockPeriod.objects.get(
    start_date=stocktake.period_start,
    end_date=stocktake.period_end,
    hotel=stocktake.hotel
)
snapshot = period.snapshots.get(item=line.item)

print(f"\n{'=' * 80}")
print("CURRENT STATE - What we have vs what we need")
print("=" * 80)

print("\n--- SNAPSHOT (has display fields) ---")
print(f"Opening Stock:")
print(f"  Raw: {snapshot.opening_full_units} + {snapshot.opening_partial_units}")
print(f"  Display: {snapshot.opening_display_full_units} + "
      f"{snapshot.opening_display_partial_units}")
print(f"Closing Stock:")
print(f"  Raw: {snapshot.closing_full_units} + {snapshot.closing_partial_units}")
print(f"  Display: {snapshot.closing_display_full_units} + "
      f"{snapshot.closing_display_partial_units}")

print("\n--- STOCKTAKE LINE (needs display fields) ---")
print(f"Opening Qty: {line.opening_qty} (raw servings)")
print(f"Expected Qty: {line.expected_qty} (raw servings)")
print(f"Counted: {line.counted_full_units} + {line.counted_partial_units} "
      "(user input)")
print(f"Counted Qty: {line.counted_qty} (raw servings)")
print(f"Variance Qty: {line.variance_qty} (raw servings)")

print(f"\n{'=' * 80}")
print("WHAT WE NEED TO ADD")
print("=" * 80)
print("""
StocktakeLine should have display methods for:

1. Opening Display:
   - opening_display_full_units (e.g., 9 cases, 1 keg)
   - opening_display_partial_units (e.g., 5 bottles, 4.68 pints)

2. Expected Display:
   - expected_display_full_units
   - expected_display_partial_units

3. Counted Display:
   - Already has counted_full_units, counted_partial_units (user input)
   - Convert to display: counted_display_full_units, counted_display_partial

4. Variance Display:
   - variance_display_full_units
   - variance_display_partial_units

WHY?
- Frontend displays "9 cases + 5 bottles", not "113 servings"
- User enters counts as "10 cases + 3 bottles"
- Variance shows as "+1 case + -2 bottles"
- All calculations still in servings (backend)
- Display is just for human readability
""")

print(f"\n{'=' * 80}")
print("EXAMPLE CALCULATION")
print("=" * 80)

# Calculate what display should be
item = line.item
uom = Decimal(str(item.uom))

opening_full = int(line.opening_qty / uom)
opening_partial = line.opening_qty % uom

expected_full = int(line.expected_qty / uom)
expected_partial = line.expected_qty % uom

# For bottles/kegs, round appropriately
if item.category.code in ['B', 'M']:  # Bottles
    opening_partial = int(opening_partial)
    expected_partial = int(expected_partial)
elif item.category.code == 'D':  # Draught (pints)
    opening_partial = round(opening_partial, 2)
    expected_partial = round(expected_partial, 2)
else:  # S, W - fractional
    opening_partial = round(opening_partial, 2)
    expected_partial = round(expected_partial, 2)

print(f"\nItem: {item.name}")
print(f"Category: {item.category.code} (UOM: {uom})")
print(f"\nOpening: {line.opening_qty} servings")
print(f"  Display: {opening_full} + {opening_partial}")
print(f"\nExpected: {line.expected_qty} servings")
print(f"  Display: {expected_full} + {expected_partial}")
print(f"\nCounted: {line.counted_full_units} + {line.counted_partial_units}")
print(f"  (User enters these in display format)")

print(f"\n{'=' * 80}")
print("SERIALIZER FIELDS NEEDED")
print("=" * 80)
print("""
StocktakeLineSerializer should add:

class StocktakeLineSerializer(serializers.ModelSerializer):
    # Existing fields...
    
    # Add display fields
    opening_display_full_units = serializers.SerializerMethodField()
    opening_display_partial_units = serializers.SerializerMethodField()
    expected_display_full_units = serializers.SerializerMethodField()
    expected_display_partial_units = serializers.SerializerMethodField()
    counted_display_full_units = serializers.SerializerMethodField()
    counted_display_partial_units = serializers.SerializerMethodField()
    variance_display_full_units = serializers.SerializerMethodField()
    variance_display_partial_units = serializers.SerializerMethodField()
    
    def get_opening_display_full_units(self, obj):
        # Calculate from opening_qty
        ...
    
    # Similar for other display fields...
""")

print("=" * 80)
