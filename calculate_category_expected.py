"""
Calculate Expected Quantity for Complete Categories

This script demonstrates how to calculate the expected_qty formula
for entire categories in a stocktake.

Formula: expected = opening + purchases + transfers_in - sales - waste - transfers_out + adjustments
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from hotel.models import Hotel


def display_category_totals(stocktake_id, hotel_id=1):
    """
    Display category-level expected quantity calculations.
    """
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        stocktake = Stocktake.objects.get(id=stocktake_id, hotel=hotel)
    except (Hotel.DoesNotExist, Stocktake.DoesNotExist) as e:
        print(f"❌ Error: {e}")
        return

    print("=" * 80)
    print(f"STOCKTAKE CATEGORY TOTALS")
    print(f"Stocktake ID: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"Status: {stocktake.status}")
    print("=" * 80)
    print()

    # Get totals for all categories
    categories = stocktake.get_category_totals()

    if not categories:
        print("No stocktake lines found.")
        return

    # Display each category
    for cat_code, totals in categories.items():
        print(f"{'=' * 80}")
        print(f"CATEGORY: {totals['category_code']} - {totals['category_name']}")
        print(f"Items: {totals['item_count']}")
        print(f"{'=' * 80}")
        print()
        
        print("QUANTITY BREAKDOWN (in servings):")
        print("-" * 80)
        print(f"  Opening Stock:        {totals['opening_qty']:>15,.4f}")
        print(f"  + Purchases:          {totals['purchases']:>15,.4f}")
        print(f"  + Transfers In:       {totals['transfers_in']:>15,.4f}")
        print(f"  - Sales:              {totals['sales']:>15,.4f}")
        print(f"  - Waste:              {totals['waste']:>15,.4f}")
        print(f"  - Transfers Out:      {totals['transfers_out']:>15,.4f}")
        print(f"  + Adjustments:        {totals['adjustments']:>15,.4f}")
        print("-" * 80)
        print(f"  = EXPECTED:           {totals['expected_qty']:>15,.4f}")
        print(f"  Counted:              {totals['counted_qty']:>15,.4f}")
        print(f"  Variance:             {totals['variance_qty']:>15,.4f}")
        print()
        
        print("VALUE BREAKDOWN (in €):")
        print("-" * 80)
        print(f"  Expected Value:       €{totals['expected_value']:>14,.2f}")
        print(f"  Counted Value:        €{totals['counted_value']:>14,.2f}")
        print(f"  Variance Value:       €{totals['variance_value']:>14,.2f}")
        print()
        
        # Show manual overrides if present
        if totals['manual_purchases_value'] > 0 or totals['manual_sales_profit'] > 0:
            print("MANUAL OVERRIDES:")
            print("-" * 80)
            if totals['manual_purchases_value'] > 0:
                print(f"  Manual Purchases:     €{totals['manual_purchases_value']:>14,.2f}")
            if totals['manual_sales_profit'] > 0:
                print(f"  Manual Sales Profit:  €{totals['manual_sales_profit']:>14,.2f}")
            print()
        
        # Calculate variance percentage
        if totals['expected_qty'] != 0:
            variance_pct = (totals['variance_qty'] / totals['expected_qty']) * 100
            print(f"Variance: {variance_pct:+.2f}%")
        
        print()


def display_single_category(stocktake_id, category_code, hotel_id=1):
    """
    Display totals for a single category.
    """
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        stocktake = Stocktake.objects.get(id=stocktake_id, hotel=hotel)
    except (Hotel.DoesNotExist, Stocktake.DoesNotExist) as e:
        print(f"❌ Error: {e}")
        return

    totals = stocktake.get_category_totals(category_code=category_code)
    
    if not totals:
        print(f"❌ No data found for category {category_code}")
        return

    print("=" * 80)
    print(f"CATEGORY: {totals['category_code']} - {totals['category_name']}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print("=" * 80)
    print()
    
    print("EXPECTED QUANTITY CALCULATION:")
    print("-" * 80)
    print(f"  Opening:          {totals['opening_qty']:>12,.4f}")
    print(f"  + Purchases:      {totals['purchases']:>12,.4f}")
    print(f"  + Transfers In:   {totals['transfers_in']:>12,.4f}")
    print(f"  - Sales:          {totals['sales']:>12,.4f}")
    print(f"  - Waste:          {totals['waste']:>12,.4f}")
    print(f"  - Transfers Out:  {totals['transfers_out']:>12,.4f}")
    print(f"  + Adjustments:    {totals['adjustments']:>12,.4f}")
    print("-" * 80)
    print(f"  = EXPECTED:       {totals['expected_qty']:>12,.4f} servings")
    print()
    print(f"  Counted:          {totals['counted_qty']:>12,.4f} servings")
    print(f"  Variance:         {totals['variance_qty']:>12,.4f} servings")
    print()
    print(f"  Expected Value:   €{totals['expected_value']:>11,.2f}")
    print(f"  Counted Value:    €{totals['counted_value']:>11,.2f}")
    print(f"  Variance Value:   €{totals['variance_value']:>11,.2f}")
    print()


if __name__ == "__main__":
    import sys
    
    print()
    print("STOCKTAKE CATEGORY CALCULATOR")
    print()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python calculate_category_expected.py <stocktake_id>")
        print("  python calculate_category_expected.py <stocktake_id> <category_code>")
        print()
        print("Examples:")
        print("  python calculate_category_expected.py 4")
        print("  python calculate_category_expected.py 4 D")
        print("  python calculate_category_expected.py 4 S")
        print()
        print("Categories: D=Draught, B=Bottled, S=Spirits, W=Wine, M=Mixers")
        sys.exit(1)
    
    stocktake_id = int(sys.argv[1])
    
    if len(sys.argv) >= 3:
        category_code = sys.argv[2].upper()
        display_single_category(stocktake_id, category_code)
    else:
        display_category_totals(stocktake_id)
