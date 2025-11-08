"""
Test multiple items per category in stocktake
Check if all have zeros or if some have data
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

from stock_tracker.models import Stocktake, StocktakeLine
from stock_tracker.stock_serializers import StocktakeLineSerializer

print("=" * 80)
print("TEST MULTIPLE ITEMS PER CATEGORY IN STOCKTAKE")
print("=" * 80)

# Get stocktake
stocktake = Stocktake.objects.get(id=4)
print(f"\nStocktake ID: {stocktake.id}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print(f"Status: {stocktake.status}")
print(f"Total Lines: {stocktake.lines.count()}")

# Get 3 items from each category
categories = ['B', 'D', 'S', 'W', 'M']

for cat in categories:
    print(f"\n{'=' * 80}")
    print(f"CATEGORY {cat}")
    print("=" * 80)
    
    lines = stocktake.lines.filter(
        item__category__code=cat
    ).select_related('item', 'item__category')[:3]
    
    if not lines.exists():
        print(f"No items found for category {cat}")
        continue
    
    for line in lines:
        serializer = StocktakeLineSerializer(line)
        data = serializer.data
        
        print(f"\n--- {data['item_name']} ({data['item_sku']}) ---")
        print(f"Opening: {data['opening_qty']}")
        print(f"Purchases: {data['purchases']}")
        print(f"Sales: {data['sales']}")
        print(f"Waste: {data['waste']}")
        print(f"Expected: {data['expected_qty']}")
        print(f"Counted: {data['counted_full_units']} full + "
              f"{data['counted_partial_units']} partial = "
              f"{data['counted_qty']} total")
        print(f"Variance: {data['variance_qty']}")
        print(f"Expected Value: €{data['expected_value']}")
        print(f"Counted Value: €{data['counted_value']}")
        
        # Check if ALL zeros
        if (float(data['opening_qty']) == 0 and 
            float(data['purchases']) == 0 and 
            float(data['sales']) == 0 and 
            float(data['expected_qty']) == 0 and 
            float(data['counted_qty']) == 0):
            print("⚠️  ALL ZEROS - No stock activity")
        elif float(data['counted_qty']) == 0:
            print("⚠️  NOT COUNTED YET (but has expected stock)")
        else:
            print("✅ HAS DATA")

print(f"\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)

# Count how many lines have data
total = stocktake.lines.count()
zeros = stocktake.lines.filter(
    opening_qty=0,
    purchases=0,
    sales=0,
    expected_qty=0
).count()
not_counted = stocktake.lines.filter(
    counted_full_units=0,
    counted_partial_units=0
).count()
has_data = total - zeros

print(f"\nTotal Items: {total}")
print(f"Items with ALL zeros: {zeros} ({zeros/total*100:.1f}%)")
print(f"Items NOT counted yet: {not_counted} ({not_counted/total*100:.1f}%)")
print(f"Items with stock data: {has_data} ({has_data/total*100:.1f}%)")

print(f"\n{'=' * 80}")
print("ITEMS WITH STOCK (showing first 10)")
print("=" * 80)

lines_with_stock = stocktake.lines.exclude(
    opening_qty=0,
    purchases=0,
    sales=0,
    expected_qty=0
).select_related('item', 'item__category')[:10]

for line in lines_with_stock:
    serializer = StocktakeLineSerializer(line)
    data = serializer.data
    print(f"\n{data['item_name']} ({data['item_sku']}) - {data['category_code']}")
    print(f"  Opening: {data['opening_qty']}")
    print(f"  Expected: {data['expected_qty']}")
    print(f"  Counted: {data['counted_qty']}")
    print(f"  Variance: {data['variance_qty']}")

print("\n" + "=" * 80)
