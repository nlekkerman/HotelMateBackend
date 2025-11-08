"""
Test October period to see opening vs closing stock differences
October has September before and November after
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod
from stock_tracker.stock_serializers import StockPeriodDetailSerializer
import json

print("=" * 80)
print("OCTOBER 2024 TEST - Opening vs Closing Stock")
print("=" * 80)

period = StockPeriod.objects.get(id=8)
data = StockPeriodDetailSerializer(period).data

print(f"\nPeriod: {data['period_name']}")
print(f"Dates: {data['start_date']} to {data['end_date']}")
print(f"Total Items: {data['total_items']}")
print(f"Total Value: €{data['total_value']}")

# Get first few items with stock
print("\n" + "=" * 80)
print("ITEMS WITH OPENING AND CLOSING STOCK")
print("=" * 80)

count = 0
for snap in data['snapshots']:
    opening = float(snap['opening_partial_units'])
    closing = float(snap['closing_partial_units'])
    
    # Show items where opening != closing
    if opening > 0 or closing > 0:
        print(f"\n--- {snap['item']['name']} ({snap['item']['sku']}) ---")
        print(f"Category: {snap['item']['category']} - {snap['item']['category_display']}")
        print(f"Size: {snap['item']['size']}")
        
        print("\nOPENING STOCK (from September's closing):")
        print(f"  Raw: {snap['opening_full_units']} full + {snap['opening_partial_units']} partial")
        print(f"  Display: {snap['opening_display_full_units']} + {snap['opening_display_partial_units']}")
        print(f"  Value: €{snap['opening_stock_value']}")
        
        print("\nCLOSING STOCK (counted at end of October):")
        print(f"  Raw: {snap['closing_full_units']} full + {snap['closing_partial_units']} partial")
        print(f"  Display: {snap['closing_display_full_units']} + {snap['closing_display_partial_units']}")
        print(f"  Value: €{snap['closing_stock_value']}")
        
        if opening != closing:
            diff = closing - opening
            print(f"\n  📊 DIFFERENCE: {diff:+.2f} (Closing - Opening)")
            if diff > 0:
                print(f"     ↗️ Stock INCREASED by {abs(diff):.2f}")
            elif diff < 0:
                print(f"     ↘️ Stock DECREASED by {abs(diff):.2f}")
        else:
            print(f"\n  ⚖️ No change (Opening = Closing)")
        
        count += 1
        if count >= 10:
            break

print("\n" + "=" * 80)
print("COMPLETE JSON FOR FIRST ITEM")
print("=" * 80)
print(json.dumps(data['snapshots'][0], indent=2, default=str))

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("\n✅ WHAT FRONTEND RECEIVES:")
print("  • opening_full_units, opening_partial_units (raw)")
print("  • opening_display_full_units, opening_display_partial_units (formatted)")
print("  • opening_stock_value")
print("  • closing_full_units, closing_partial_units (raw)")
print("  • closing_display_full_units, closing_display_partial_units (formatted)")
print("  • closing_stock_value")
print("\n✅ ALL PRE-CALCULATED - Frontend just displays!")
print("=" * 80)
