"""
Final test showing proper rounding for all categories
Bottles = whole numbers, Pints = 2 decimals
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod
from stock_tracker.stock_serializers import StockPeriodDetailSerializer
import json

period = StockPeriod.objects.get(id=8)
data = StockPeriodDetailSerializer(period).data

print("=" * 80)
print("FINAL TEST: PROPER ROUNDING FOR ALL CATEGORIES")
print("=" * 80)

categories = {
    'B': 'Bottled Beer (bottles = whole numbers)',
    'D': 'Draught Beer (pints = 2 decimals)',
    'S': 'Spirits (fractional = 2 decimals)',
    'W': 'Wine (fractional = 2 decimals)',
    'M': 'Mixers (bottles = whole numbers)'
}

for cat_code, cat_desc in categories.items():
    print(f"\n{'=' * 80}")
    print(f"{cat_desc}")
    print("=" * 80)
    
    found = False
    for snap in data['snapshots']:
        if snap['item']['category'] == cat_code:
            closing = float(snap['closing_partial_units'])
            if closing > 0:
                print(f"\n{snap['item']['name']} ({snap['item']['sku']})")
                print(f"Size: {snap['item']['size']}")
                print(f"\nCLOSING STOCK:")
                print(f"  Raw: {snap['closing_partial_units']} servings")
                print(f"  Display: {snap['closing_display_full_units']} + "
                      f"{snap['closing_display_partial_units']}")
                
                # Verify rounding
                partial = snap['closing_display_partial_units']
                if cat_code in ['B', 'M'] and 'Doz' in str(snap['item']['size']):
                    if '.' in str(partial):
                        print(f"  ❌ ERROR: Bottles should be whole number!")
                    else:
                        print(f"  ✅ Correct: Bottles are whole numbers")
                elif cat_code == 'D':
                    decimal_places = len(str(partial).split('.')[-1]) if '.' in str(partial) else 0
                    if decimal_places <= 2:
                        print(f"  ✅ Correct: Pints have {decimal_places} decimal places")
                    else:
                        print(f"  ❌ ERROR: Pints should have max 2 decimals!")
                
                found = True
                break
    
    if not found:
        print("\n  No items with stock in this category")

print("\n" + "=" * 80)
print("COMPLETE JSON SAMPLES")
print("=" * 80)

# Get one from each category
samples = {}
for snap in data['snapshots']:
    cat = snap['item']['category']
    if cat not in samples and float(snap['closing_partial_units']) > 0:
        samples[cat] = snap

for cat_code in ['B', 'D', 'S']:
    if cat_code in samples:
        snap = samples[cat_code]
        print(f"\n--- {snap['item']['category_display']} ---")
        print(json.dumps({
            'item': snap['item']['name'],
            'size': snap['item']['size'],
            'opening_display': {
                'full': snap['opening_display_full_units'],
                'partial': snap['opening_display_partial_units']
            },
            'closing_display': {
                'full': snap['closing_display_full_units'],
                'partial': snap['closing_display_partial_units']
            }
        }, indent=2))

print("\n" + "=" * 80)
print("FRONTEND DISPLAY INSTRUCTIONS")
print("=" * 80)
print("""
✅ BOTTLES (Bottled Beer, Mixers with "Doz"):
   Display: {closing_display_full_units} cases + {closing_display_partial_units} bottles
   Example: "12 cases + 8 bottles"
   Partial is ALWAYS a whole number (0-11)

✅ PINTS (Draught Beer):
   Display: {closing_display_full_units} kegs + {closing_display_partial_units} pints
   Example: "5 kegs + 39.90 pints"
   Partial has UP TO 2 decimal places

✅ SPIRITS/WINE (Individual bottles):
   Display: {closing_display_full_units} bottles + {closing_display_partial_units}
   Example: "2 bottles + 0.30"
   Partial has UP TO 2 decimal places

✅ FRONTEND CODE:
   // Just display the values - already pre-calculated!
   `${snap.closing_display_full_units} + ${snap.closing_display_partial_units}`
   
   // No rounding, no calculation needed!
""")

print("=" * 80)
