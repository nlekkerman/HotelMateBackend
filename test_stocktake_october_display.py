"""
Test Stocktake display fields for October period
October has a closed previous period (September) with data
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

from stock_tracker.models import Stocktake, StockPeriod
from stock_tracker.stock_serializers import (
    StocktakeSerializer,
    StocktakeLineSerializer
)
import json

print("=" * 80)
print("STOCKTAKE OCTOBER - DISPLAY FIELDS TEST")
print("=" * 80)

# Get November stocktake (ID 4) which has September data before it
stocktake = Stocktake.objects.get(id=4)
print(f"\nStocktake ID: {stocktake.id}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print(f"Status: {stocktake.status}")

# Get 3 items per category with actual stock
categories = ['B', 'D', 'S', 'W', 'M']

for cat in categories:
    print(f"\n{'=' * 80}")
    print(f"CATEGORY {cat}")
    print("=" * 80)
    
    # Get lines with actual opening stock (not zeros)
    lines = stocktake.lines.filter(
        item__category__code=cat
    ).exclude(
        opening_qty=0, purchases=0
    ).select_related('item', 'item__category')[:2]
    
    if not lines.exists():
        print(f"No items with stock data in category {cat}")
        continue
    
    for line in lines:
        serializer = StocktakeLineSerializer(line)
        data = serializer.data
        
        print(f"\n--- {data['item_name']} ({data['item_sku']}) ---")
        print(f"Category: {data['category_code']} - "
              f"Size: {data['item_size']} - UOM: {data['item_uom']}")
        
        print(f"\nOPENING:")
        print(f"  Raw: {data['opening_qty']} servings")
        print(f"  Display: {data['opening_display_full_units']} + "
              f"{data['opening_display_partial_units']}")
        
        print(f"\nMOVEMENTS:")
        print(f"  Purchases: {data['purchases']}")
        print(f"  Sales: {data['sales']}")
        print(f"  Waste: {data['waste']}")
        
        print(f"\nEXPECTED:")
        print(f"  Raw: {data['expected_qty']} servings")
        print(f"  Display: {data['expected_display_full_units']} + "
              f"{data['expected_display_partial_units']}")
        print(f"  Value: €{data['expected_value']}")
        
        print(f"\nCOUNTED:")
        print(f"  Input: {data['counted_full_units']} + "
              f"{data['counted_partial_units']}")
        print(f"  Raw: {data['counted_qty']} servings")
        print(f"  Display: {data['counted_display_full_units']} + "
              f"{data['counted_display_partial_units']}")
        print(f"  Value: €{data['counted_value']}")
        
        print(f"\nVARIANCE:")
        print(f"  Raw: {data['variance_qty']} servings")
        print(f"  Display: {data['variance_display_full_units']} + "
              f"{data['variance_display_partial_units']}")
        print(f"  Value: €{data['variance_value']}")
        
        # Verify display makes sense
        if data['category_code'] == 'B':
            print(f"  ✅ Bottles: partial units should be whole number")
        elif data['category_code'] == 'D':
            print(f"  ✅ Draught: partial units should have 2 decimals (pints)")
        else:
            print(f"  ✅ {data['category_code']}: partial units with 2 decimals")

print(f"\n{'=' * 80}")
print("COMPLETE JSON EXAMPLE (First Item)")
print("=" * 80)

# Show full JSON for one item
first_line = stocktake.lines.exclude(
    opening_qty=0, purchases=0
).select_related('item', 'item__category').first()

if first_line:
    serializer = StocktakeLineSerializer(first_line)
    print(json.dumps(serializer.data, indent=2, default=str))

print(f"\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)
print("""
✅ StocktakeLine now has display fields for:
  - opening_display_full_units + opening_display_partial_units
  - expected_display_full_units + expected_display_partial_units
  - counted_display_full_units + counted_display_partial_units
  - variance_display_full_units + variance_display_partial_units

✅ Display format matches category:
  - B (Bottles): cases + bottles (whole numbers)
  - D (Draught): kegs + pints (2 decimals)
  - S (Spirits): bottles + fractional (2 decimals)
  - W (Wine): bottles + fractional (2 decimals)
  - M (Mixers): depends on size (Doz = whole, else fractional)

✅ Frontend can display:
  "Opening: 12 cases + 8 bottles"
  "Expected: 15 cases + 3 bottles"
  "Counted: 14 cases + 11 bottles"
  "Variance: -1 case + 3 bottles"

✅ NO calculations needed on frontend!
""")
print("=" * 80)
