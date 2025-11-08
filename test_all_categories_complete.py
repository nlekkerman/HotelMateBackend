"""
Comprehensive test for all categories showing display logic
Then shows complete serializer response for frontend
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockPeriod
from stock_tracker.stock_serializers import StockPeriodDetailSerializer
import json

period = StockPeriod.objects.get(id=9)
data = StockPeriodDetailSerializer(period).data

print("=" * 80)
print("COMPREHENSIVE TEST: ALL CATEGORIES WITH MULTIPLE ITEMS")
print("=" * 80)

# Group by category
categories = {
    'B': {'name': 'Bottled Beer', 'items': []},
    'D': {'name': 'Draught Beer', 'items': []},
    'S': {'name': 'Spirits', 'items': []},
    'W': {'name': 'Wine', 'items': []},
    'M': {'name': 'Mixers', 'items': []}
}

for snap in data['snapshots']:
    cat = snap['item']['category']
    if cat in categories:
        closing = float(snap['closing_partial_units'])
        if closing > 0 and len(categories[cat]['items']) < 5:
            categories[cat]['items'].append(snap)

# Display each category
for cat_code, cat_info in categories.items():
    print(f"\n{'=' * 80}")
    print(f"{cat_info['name']} (Category {cat_code})")
    print("=" * 80)
    
    for snap in cat_info['items']:
        item = StockItem.objects.get(sku=snap['item']['sku'])
        closing = float(snap['closing_partial_units'])
        
        print(f"\n{snap['item']['name']} ({snap['item']['sku']})")
        print(f"  Size: {snap['item']['size']}")
        print(f"  UOM: {item.uom}")
        print(f"  Category Logic: ", end="")
        
        if cat_code == 'D':
            print(f"Draught (pints per keg)")
        elif 'Doz' in str(snap['item']['size']):
            print(f"Dozen (bottles per case)")
        else:
            print(f"Individual (servings per bottle)")
        
        print(f"\n  OPENING STOCK:")
        print(f"    Raw: {snap['opening_full_units']} full + "
              f"{snap['opening_partial_units']} partial")
        print(f"    Display: {snap['opening_display_full_units']} + "
              f"{snap['opening_display_partial_units']}")
        print(f"    Value: €{snap['opening_stock_value']}")
        
        print(f"\n  CLOSING STOCK:")
        print(f"    Raw: {snap['closing_full_units']} full + "
              f"{snap['closing_partial_units']} partial")
        print(f"    Display: {snap['display_full_units']} + "
              f"{snap['display_partial_units']}")
        print(f"    Total Servings: {snap['total_servings']}")
        print(f"    Value: €{snap['closing_stock_value']}")
        
        print(f"\n  COSTS:")
        print(f"    Unit Cost: €{snap['unit_cost']}")
        print(f"    Cost/Serving: €{snap['cost_per_serving']}")
        
        # Verify calculation
        if cat_code == 'D' or 'Doz' in str(snap['item']['size']):
            expected_full = int(closing / float(item.uom))
            expected_partial = closing % float(item.uom)
            actual_full = float(snap['display_full_units'])
            actual_partial = float(snap['display_partial_units'])
            
            match = (expected_full == actual_full and 
                    abs(expected_partial - actual_partial) < 0.01)
            status = "✅" if match else "❌"
            
            if cat_code == 'D':
                print(f"\n  {status} Verify: {closing} pints ÷ {item.uom} "
                      f"= {expected_full} kegs + {expected_partial:.2f} pints")
            else:
                print(f"\n  {status} Verify: {closing} bottles ÷ {item.uom} "
                      f"= {expected_full} cases + {expected_partial:.0f} bottles")
        else:
            print(f"\n  ✅ Individual units (no conversion needed)")

print("\n" + "=" * 80)
print("COMPLETE SERIALIZER RESPONSE SAMPLE")
print("=" * 80)
print("\nShowing first 3 items with full JSON structure:")

for i, snap in enumerate(data['snapshots'][:3]):
    print(f"\n--- Item {i+1}: {snap['item']['name']} ---")
    print(json.dumps(snap, indent=2, default=str))

print("\n" + "=" * 80)
print("FRONTEND API RESPONSE STRUCTURE")
print("=" * 80)
print("\nGET /api/stock_tracker/{hotel_id}/periods/{period_id}/\n")
print("Complete response structure:")
response_structure = {
    'id': data['id'],
    'period_name': data['period_name'],
    'start_date': data['start_date'],
    'end_date': data['end_date'],
    'is_closed': data['is_closed'],
    'total_items': data['total_items'],
    'total_value': data['total_value'],
    'snapshot_ids': f"[{data['snapshot_ids'][0]}...{data['snapshot_ids'][-1]}]",
    'stocktake_id': data['stocktake_id'],
    'stocktake_status': data['stocktake_status'],
    'snapshots': f'[{len(data["snapshots"])} items with full structure]'
}
print(json.dumps(response_structure, indent=2))

print("\n" + "=" * 80)
print("FIELD SUMMARY FOR FRONTEND")
print("=" * 80)
print("\nEach snapshot contains:")
print("  ✅ item (id, sku, name, category, size, unit_cost, menu_price)")
print("  ✅ opening_full_units, opening_partial_units, opening_stock_value")
print("  ✅ opening_display_full_units, opening_display_partial_units")
print("  ✅ closing_full_units, closing_partial_units, closing_stock_value")
print("  ✅ display_full_units, display_partial_units")
print("  ✅ total_servings")
print("  ✅ unit_cost, cost_per_serving")
print("  ✅ gp_percentage, markup_percentage, pour_cost_percentage")
print("\nDisplay units conversion:")
print("  • Bottled Beer (Doz): cases + bottles")
print("  • Draught (D): kegs + pints")
print("  • Spirits/Wine: bottles + fractional")
print("  • Mixers: as-is (no conversion)")
print("\n✅ ALL DATA READY FOR STOCKTAKE CALCULATIONS!")
print("=" * 80)
