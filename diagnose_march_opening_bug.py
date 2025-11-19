import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_porter.settings')
django.setup()

from bar_app.models import StockSnapshot, StockItem, Stocktake, StocktakeLine

# Get February closing snapshot
feb_snapshots = StockSnapshot.objects.filter(
    period__start_date__year=2025,
    period__start_date__month=2
).select_related('stock_item', 'period')

print("=" * 80)
print("FEBRUARY CLOSING SNAPSHOTS (Correct)")
print("=" * 80)

# Check syrups
syrup_snapshot = feb_snapshots.filter(stock_item__sku='M3').first()
if syrup_snapshot:
    print(f"\nMonin Agave Syrup (M3):")
    print(f"  SKU: {syrup_snapshot.stock_item.sku}")
    print(f"  Category: {syrup_snapshot.stock_item.category.name}")
    print(f"  UOM: {syrup_snapshot.stock_item.unit_of_measurement}")
    print(f"  Size: {syrup_snapshot.stock_item.size}")
    print(f"  Closing Primary: {syrup_snapshot.closing_primary_quantity}")
    print(f"  Closing Secondary: {syrup_snapshot.closing_secondary_quantity}")
    print(f"  Closing Value: €{syrup_snapshot.closing_stock_value}")
    print(f"  Servings/Bottles: {syrup_snapshot.closing_primary_quantity} bottles + {syrup_snapshot.closing_secondary_quantity} partial")

# Check spirits
spirit_snapshot = feb_snapshots.filter(stock_item__sku='S0008').first()
if spirit_snapshot:
    print(f"\n1827 Osborne Port (S0008):")
    print(f"  SKU: {spirit_snapshot.stock_item.sku}")
    print(f"  Category: {spirit_snapshot.stock_item.category.name}")
    print(f"  UOM: {spirit_snapshot.stock_item.unit_of_measurement}")
    print(f"  Size: {spirit_snapshot.stock_item.size}")
    print(f"  Closing Primary: {spirit_snapshot.closing_primary_quantity}")
    print(f"  Closing Secondary: {spirit_snapshot.closing_secondary_quantity}")
    print(f"  Closing Value: €{spirit_snapshot.closing_stock_value}")

print("\n" + "=" * 80)
print("MARCH OPENING STOCKTAKE (WRONG)")
print("=" * 80)

# Get March stocktake
march_stocktake = Stocktake.objects.filter(
    period__start_date__year=2025,
    period__start_date__month=3
).first()

if march_stocktake:
    print(f"\nMarch Stocktake ID: {march_stocktake.id}")
    print(f"Period: {march_stocktake.period}")
    
    # Check syrup line
    syrup_line = StocktakeLine.objects.filter(
        stocktake=march_stocktake,
        stock_item__sku='M3'
    ).select_related('stock_item').first()
    
    if syrup_line:
        print(f"\nMonin Agave Syrup Line:")
        print(f"  UOM: {syrup_line.stock_item.unit_of_measurement}")
        print(f"  Size: {syrup_line.stock_item.size}")
        print(f"  Opening Primary: {syrup_line.opening_primary_quantity}")
        print(f"  Opening Secondary: {syrup_line.opening_secondary_quantity}")
        print(f"  Opening Value: €{syrup_line.opening_stock_value}")
        print(f"  PRIMARY_UNIT: {syrup_line.primary_unit}")
        print(f"  SECONDARY_UNIT: {syrup_line.secondary_unit}")
        
        # Calculate what it SHOULD be
        expected = syrup_snapshot.closing_primary_quantity + (syrup_snapshot.closing_secondary_quantity / 100)
        actual = syrup_line.opening_primary_quantity + (syrup_line.opening_secondary_quantity / 100)
        print(f"\n  Expected opening: {expected} bottles")
        print(f"  Actual opening: {actual} bottles")
        print(f"  ERROR MULTIPLIER: {actual / expected if expected > 0 else 0}x")
    
    # Check spirit line
    spirit_line = StocktakeLine.objects.filter(
        stocktake=march_stocktake,
        stock_item__sku='S0008'
    ).select_related('stock_item').first()
    
    if spirit_line:
        print(f"\n1827 Osborne Port Line:")
        print(f"  UOM: {spirit_line.stock_item.unit_of_measurement}")
        print(f"  Size: {spirit_line.stock_item.size}")
        print(f"  Opening Primary: {spirit_line.opening_primary_quantity}")
        print(f"  Opening Secondary: {spirit_line.opening_secondary_quantity}")
        print(f"  Opening Value: €{spirit_line.opening_stock_value}")
        print(f"  PRIMARY_UNIT: {spirit_line.primary_unit}")
        print(f"  SECONDARY_UNIT: {spirit_line.secondary_unit}")

print("\n" + "=" * 80)
print("CHECKING STOCK ITEM UOM")
print("=" * 80)

# Check if UOM is wrong
syrup_item = StockItem.objects.filter(sku='M3').first()
if syrup_item:
    print(f"\nMonin Agave (M3) Stock Item:")
    print(f"  UOM: '{syrup_item.unit_of_measurement}'")
    print(f"  Size: {syrup_item.size}ml")
    print(f"  Serving Size: {syrup_item.serving_size_ml}ml")
    print(f"  Servings per Unit: {syrup_item.servings_per_unit}")

spirit_item = StockItem.objects.filter(sku='S0008').first()
if spirit_item:
    print(f"\n1827 Osborne Port (S0008) Stock Item:")
    print(f"  UOM: '{spirit_item.unit_of_measurement}'")
    print(f"  Size: {spirit_item.size}ml")
    print(f"  Serving Size: {spirit_item.serving_size_ml}ml")
    print(f"  Servings per Unit: {spirit_item.servings_per_unit}")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
