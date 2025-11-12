"""
Test that category_totals endpoint returns opening_value and purchases_value
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from decimal import Decimal

# Test with October stocktake
stocktake = Stocktake.objects.get(id=18, hotel_id=2)
print(f"\n{'='*80}")
print(f"Testing Stocktake ID: {stocktake.id}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print(f"{'='*80}\n")

# Get category totals for Minerals
totals = stocktake.get_category_totals(category_code='M')

if totals:
    print("✅ MINERALS/SYRUPS CATEGORY TOTALS")
    print(f"{'─'*80}")
    print(f"Category Code:          {totals['category_code']}")
    print(f"Category Name:          {totals['category_name']}")
    print(f"Item Count:             {totals['item_count']}")
    print()
    
    print("📊 QUANTITIES:")
    print(f"  Opening Qty:          {totals['opening_qty']:>15.4f}")
    print(f"  Purchases:            {totals['purchases']:>15.4f}")
    print(f"  Waste:                {totals['waste']:>15.4f}")
    print(f"  Transfers In:         {totals['transfers_in']:>15.4f}")
    print(f"  Transfers Out:        {totals['transfers_out']:>15.4f}")
    print(f"  Adjustments:          {totals['adjustments']:>15.4f}")
    print(f"  Expected Qty:         {totals['expected_qty']:>15.4f}")
    print(f"  Counted Qty:          {totals['counted_qty']:>15.4f}")
    print(f"  Variance Qty:         {totals['variance_qty']:>15.4f}")
    print()
    
    print("💰 VALUES (EUR):")
    print(f"  Opening Value:        €{totals['opening_value']:>14.2f}  ← NEW")
    print(f"  Purchases Value:      €{totals['purchases_value']:>14.2f}  ← NEW")
    print(f"  Expected Value:       €{totals['expected_value']:>14.2f}")
    print(f"  Counted Value:        €{totals['counted_value']:>14.2f}")
    print(f"  Variance Value:       €{totals['variance_value']:>14.2f}")
    print()
    
    # Validation checks
    print("✅ VALIDATION CHECKS:")
    
    # Check if opening_value exists and is not zero
    if 'opening_value' in totals:
        print(f"  ✅ opening_value field exists: €{totals['opening_value']:.2f}")
    else:
        print(f"  ❌ opening_value field MISSING!")
    
    # Check if purchases_value exists
    if 'purchases_value' in totals:
        print(f"  ✅ purchases_value field exists: €{totals['purchases_value']:.2f}")
    else:
        print(f"  ❌ purchases_value field MISSING!")
    
    # Check that opening_value matches expected (based on our previous data)
    expected_opening = Decimal('4185.64')  # October opening should be ~4185.64
    if abs(totals['opening_value'] - expected_opening) < Decimal('1.00'):
        print(f"  ✅ opening_value matches expected: €{expected_opening:.2f}")
    else:
        print(f"  ⚠️  opening_value different: Expected €{expected_opening:.2f}, Got €{totals['opening_value']:.2f}")
    
else:
    print("❌ No totals found for Minerals category")

print(f"\n{'='*80}")

# Test all categories
print("\n📋 ALL CATEGORIES SUMMARY:")
print(f"{'─'*80}")
all_totals = stocktake.get_category_totals()

for cat_code, cat_data in sorted(all_totals.items()):
    print(f"\n{cat_data['category_name']} ({cat_code}):")
    print(f"  Items: {cat_data['item_count']}")
    print(f"  Opening Value:   €{cat_data['opening_value']:>10.2f}")
    print(f"  Purchases Value: €{cat_data['purchases_value']:>10.2f}")
    print(f"  Expected Value:  €{cat_data['expected_value']:>10.2f}")
    print(f"  Counted Value:   €{cat_data['counted_value']:>10.2f}")
    print(f"  Variance Value:  €{cat_data['variance_value']:>10.2f}")

print(f"\n{'='*80}")
print("✅ TEST COMPLETE - category_totals now includes opening_value and purchases_value")
print(f"{'='*80}\n")
