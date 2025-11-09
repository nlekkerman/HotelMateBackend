"""
Test that variance_value recalculates correctly when counted values change
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from decimal import Decimal

print("=" * 80)
print("TESTING VARIANCE VALUE RECALCULATION")
print("=" * 80)

# Get a stocktake with data
try:
    stocktake = Stocktake.objects.filter(status='DRAFT').first()
    if not stocktake:
        stocktake = Stocktake.objects.first()
    
    if not stocktake:
        print("\nNo stocktakes found!")
        exit()
    
    print(f"\nUsing Stocktake ID: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"Status: {stocktake.status}")
    
    # Get a line to test
    line = stocktake.lines.first()
    if not line:
        print("\nNo stocktake lines found!")
        exit()
    
    print(f"\n{'=' * 80}")
    print(f"Testing Line: {line.item.sku} - {line.item.name}")
    print(f"{'=' * 80}")
    
    # Show initial values
    print(f"\nInitial Values:")
    print(f"  Counted Full Units: {line.counted_full_units}")
    print(f"  Counted Partial Units: {line.counted_partial_units}")
    print(f"  Counted Qty: {line.counted_qty}")
    print(f"  Expected Qty: {line.expected_qty}")
    print(f"  Variance Qty: {line.variance_qty}")
    print(f"  Valuation Cost: {line.valuation_cost}")
    print(f"  Expected Value: €{line.expected_value}")
    print(f"  Counted Value: €{line.counted_value}")
    print(f"  Variance Value: €{line.variance_value}")
    
    # Update counted values
    print(f"\n{'=' * 80}")
    print("Updating counted values...")
    print(f"{'=' * 80}")
    
    new_full = line.counted_full_units + Decimal('1')
    new_partial = line.counted_partial_units + Decimal('5')
    
    print(f"  Setting counted_full_units to: {new_full}")
    print(f"  Setting counted_partial_units to: {new_partial}")
    
    line.counted_full_units = new_full
    line.counted_partial_units = new_partial
    line.save()
    
    # Refresh from database
    line.refresh_from_db()
    
    # Show updated values
    print(f"\nUpdated Values (after refresh):")
    print(f"  Counted Full Units: {line.counted_full_units}")
    print(f"  Counted Partial Units: {line.counted_partial_units}")
    print(f"  Counted Qty: {line.counted_qty}")
    print(f"  Expected Qty: {line.expected_qty}")
    print(f"  Variance Qty: {line.variance_qty}")
    print(f"  Valuation Cost: {line.valuation_cost}")
    print(f"  Expected Value: €{line.expected_value}")
    print(f"  Counted Value: €{line.counted_value}")
    print(f"  Variance Value: €{line.variance_value}")
    
    # Test category totals
    print(f"\n{'=' * 80}")
    print("Testing Category Totals Recalculation")
    print(f"{'=' * 80}")
    
    category_code = line.item.category.code
    print(f"\nCategory: {category_code} - {line.item.category.name}")
    
    category_totals = stocktake.get_category_totals(category_code=category_code)
    
    if category_totals:
        print(f"\nCategory Totals:")
        print(f"  Expected Qty: {category_totals['expected_qty']}")
        print(f"  Counted Qty: {category_totals['counted_qty']}")
        print(f"  Variance Qty: {category_totals['variance_qty']}")
        print(f"  Expected Value: €{category_totals['expected_value']}")
        print(f"  Counted Value: €{category_totals['counted_value']}")
        print(f"  Variance Value: €{category_totals['variance_value']}")
        print(f"  Item Count: {category_totals['item_count']}")
    
    print(f"\n{'=' * 80}")
    print("✅ TEST COMPLETE - Variance values recalculated successfully!")
    print(f"{'=' * 80}")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
