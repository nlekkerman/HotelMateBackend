"""
Remove mock purchase data from November 2025 Stocktake.
This will reset all movements to zero so stocktake shows real data only.
Opening stock will remain (from October), but Expected will equal Opening.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockMovement

print("=" * 80)
print("REMOVE MOCK DATA FROM NOVEMBER 2025 STOCKTAKE")
print("=" * 80)
print()

# Get November stocktake
nov_stocktake = Stocktake.objects.get(id=4)
print(f"November Stocktake (ID: {nov_stocktake.id})")
print(f"Period: {nov_stocktake.period_start} to {nov_stocktake.period_end}")
print(f"Lines: {nov_stocktake.lines.count()}")
print()

# Check current state
lines_with_purchases = nov_stocktake.lines.filter(purchases__gt=0).count()
lines_with_sales = nov_stocktake.lines.filter(sales__gt=0).count()
lines_with_waste = nov_stocktake.lines.filter(waste__gt=0).count()

print("CURRENT STATE:")
print(f"  Lines with purchases: {lines_with_purchases}")
print(f"  Lines with sales: {lines_with_sales}")
print(f"  Lines with waste: {lines_with_waste}")
print()

# Delete any StockMovement records for November period
movements = StockMovement.objects.filter(
    hotel=nov_stocktake.hotel,
    timestamp__gte=nov_stocktake.period_start,
    timestamp__lte=nov_stocktake.period_end
)
movement_count = movements.count()
if movement_count > 0:
    print(f"Deleting {movement_count} stock movement records...")
    movements.delete()
    print(f"  Deleted {movement_count} movements")
print()

# Zero out all movements in stocktake lines
print("Resetting all stocktake line movements to zero...")
updated = 0
for line in nov_stocktake.lines.all():
    line.purchases = 0
    line.sales = 0
    line.waste = 0
    line.transfers_in = 0
    line.transfers_out = 0
    line.adjustments = 0
    line.save()
    updated += 1
    
    if updated % 50 == 0:
        print(f"  Updated {updated} lines...")

print(f"Updated {updated} lines")
print()

# Verify
print("=" * 80)
print("VERIFICATION")
print("=" * 80)
print()

from stock_tracker.stock_serializers import StocktakeLineSerializer

# Check a few sample items
sample_skus = ['B0070', 'D0005', 'S0001']
for sku in sample_skus:
    line = nov_stocktake.lines.filter(item__sku=sku).first()
    if line:
        data = StocktakeLineSerializer(line).data
        print(f"{data['item_name']} ({sku}):")
        print(f"  Opening: {data['opening_display_full_units']} + "
              f"{data['opening_display_partial_units']}")
        print(f"  Purchases: {data['purchases']}")
        print(f"  Sales: {data['sales']}")
        print(f"  Expected: {data['expected_display_full_units']} + "
              f"{data['expected_display_partial_units']}")
        
        if data['opening_qty'] == data['expected_qty']:
            print(f"  Status: OK - Opening equals Expected")
        else:
            print(f"  Status: ERROR - Opening != Expected")
        print()

# Summary
lines_with_movements = nov_stocktake.lines.filter(
    purchases__gt=0
).count() + nov_stocktake.lines.filter(
    sales__gt=0
).count()

print("=" * 80)
if lines_with_movements == 0:
    print("SUCCESS! All mock data removed.")
    print()
    print("November stocktake now shows:")
    print("  - Opening stock from October (preserved)")
    print("  - Expected stock = Opening stock (no movements)")
    print("  - Ready for real purchase/sales data entry")
else:
    print(f"WARNING: {lines_with_movements} lines still have movements")
print("=" * 80)
