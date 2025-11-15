"""
Test script for Minerals & Syrups subcategory implementation.
Tests all 5 subcategories with exact calculations per specification.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StocktakeLine, Stocktake
from stock_tracker.models import (
    SYRUP_SERVING_SIZE,
    JUICE_SERVING_SIZE,
    BIB_SERVING_SIZE
)
from decimal import Decimal

print("=" * 100)
print("MINERALS & SYRUPS SUBCATEGORY IMPLEMENTATION TEST")
print("=" * 100)

# Test 1: SOFT_DRINKS (Coca Cola)
print("\n" + "=" * 100)
print("TEST 1: SOFT_DRINKS - Coca Cola 24 Doz")
print("=" * 100)
soft_drink = StockItem.objects.filter(
    category_id='M',
    subcategory='SOFT_DRINKS'
).first()

if soft_drink:
    print(f"\nItem: {soft_drink.sku} - {soft_drink.name}")
    print(f"Subcategory: {soft_drink.subcategory}")
    print(f"Size: {soft_drink.size} | UOM: {soft_drink.uom} bottles/case")
    print(f"Current Stock: {soft_drink.current_full_units} cases + {soft_drink.current_partial_units} bottles")
    
    # Formula: (cases × 12) + bottles = bottles
    expected_servings = (soft_drink.current_full_units * soft_drink.uom) + soft_drink.current_partial_units
    actual_servings = soft_drink.total_stock_in_servings
    
    print(f"\nExpected Servings: {expected_servings:.2f} bottles")
    print(f"Actual Servings: {actual_servings:.2f} bottles")
    print(f"✓ PASS" if expected_servings == actual_servings else f"✗ FAIL")
else:
    print("⚠ No SOFT_DRINKS items found")

# Test 2: SYRUPS (Monin)
print("\n" + "=" * 100)
print("TEST 2: SYRUPS - Monin Syrup 700ml")
print("=" * 100)
syrup = StockItem.objects.filter(
    category_id='M',
    subcategory='SYRUPS'
).first()

if syrup:
    print(f"\nItem: {syrup.sku} - {syrup.name}")
    print(f"Subcategory: {syrup.subcategory}")
    print(f"Size: {syrup.size} | UOM: {syrup.uom} ml/bottle")
    print(f"Current Stock: {syrup.current_full_units} bottles + {syrup.current_partial_units} ml")
    print(f"Serving Size: {SYRUP_SERVING_SIZE}ml")
    
    # Formula: ((bottles × 700ml) + ml) / 25ml = servings
    full_ml = syrup.current_full_units * syrup.uom
    total_ml = full_ml + syrup.current_partial_units
    expected_servings = total_ml / SYRUP_SERVING_SIZE
    actual_servings = syrup.total_stock_in_servings
    
    print(f"\nTotal ml: {total_ml:.2f} ml")
    print(f"Expected Servings: {expected_servings:.2f} servings (25ml each)")
    print(f"Actual Servings: {actual_servings:.2f} servings")
    print(f"✓ PASS" if expected_servings == actual_servings else f"✗ FAIL")
else:
    print("⚠ No SYRUPS items found")

# Test 3: JUICES (Kulana)
print("\n" + "=" * 100)
print("TEST 3: JUICES - Kulana 1L Juice")
print("=" * 100)
juice = StockItem.objects.filter(
    category_id='M',
    subcategory='JUICES'
).first()

if juice:
    print(f"\nItem: {juice.sku} - {juice.name}")
    print(f"Subcategory: {juice.subcategory}")
    print(f"Size: {juice.size} | UOM: {juice.uom} ml/bottle")
    print(f"Current Stock: {juice.current_full_units} bottles + {juice.current_partial_units} ml")
    print(f"Serving Size: {JUICE_SERVING_SIZE}ml")
    
    # Formula: ((bottles × 1000ml) + ml) / 200ml = servings
    full_ml = juice.current_full_units * juice.uom
    total_ml = full_ml + juice.current_partial_units
    expected_servings = total_ml / JUICE_SERVING_SIZE
    actual_servings = juice.total_stock_in_servings
    
    print(f"\nTotal ml: {total_ml:.2f} ml")
    print(f"Expected Servings: {expected_servings:.2f} servings (200ml each)")
    print(f"Actual Servings: {actual_servings:.2f} servings")
    print(f"✓ PASS" if expected_servings == actual_servings else f"✗ FAIL")
else:
    print("⚠ No JUICES items found")

# Test 4: CORDIALS (Miwadi)
print("\n" + "=" * 100)
print("TEST 4: CORDIALS - Miwadi Cordial")
print("=" * 100)
cordial = StockItem.objects.filter(
    category_id='M',
    subcategory='CORDIALS'
).first()

if cordial:
    print(f"\nItem: {cordial.sku} - {cordial.name}")
    print(f"Subcategory: {cordial.subcategory}")
    print(f"Size: {cordial.size} | UOM: {cordial.uom} bottles/case")
    print(f"Current Stock: {cordial.current_full_units} cases + {cordial.current_partial_units} bottles")
    print(f"Serving Size: NONE (tracked by bottle count only)")
    
    # Formula: (cases × 12) + bottles = bottles (no serving conversion)
    expected_servings = (cordial.current_full_units * cordial.uom) + cordial.current_partial_units
    actual_servings = cordial.total_stock_in_servings
    
    print(f"\nExpected Bottles: {expected_servings:.2f} bottles")
    print(f"Actual Bottles: {actual_servings:.2f} bottles")
    print(f"✓ PASS" if expected_servings == actual_servings else f"✗ FAIL")
else:
    print("⚠ No CORDIALS items found")

# Test 5: BIB (Splash Cola)
print("\n" + "=" * 100)
print("TEST 5: BIB - Splash Cola 18L")
print("=" * 100)
bib = StockItem.objects.filter(
    category_id='M',
    subcategory='BIB'
).first()

if bib:
    print(f"\nItem: {bib.sku} - {bib.name}")
    print(f"Subcategory: {bib.subcategory}")
    print(f"Size: {bib.size} | UOM: {bib.uom} liters/box")
    print(f"Current Stock: {bib.current_full_units} boxes + {bib.current_partial_units} liters")
    print(f"Serving Size: {BIB_SERVING_SIZE} liters (200ml)")
    
    # Formula: ((boxes × 18L) + liters) / 0.2L = servings
    full_liters = bib.current_full_units * bib.uom
    total_liters = full_liters + bib.current_partial_units
    expected_servings = total_liters / BIB_SERVING_SIZE
    actual_servings = bib.total_stock_in_servings
    
    print(f"\nTotal liters: {total_liters:.2f} L")
    print(f"Expected Servings: {expected_servings:.2f} servings (200ml each)")
    print(f"Actual Servings: {actual_servings:.2f} servings")
    print(f"✓ PASS" if expected_servings == actual_servings else f"✗ FAIL")
else:
    print("⚠ No BIB items found")

# Test 6: StocktakeLine counted_qty logic
print("\n" + "=" * 100)
print("TEST 6: StocktakeLine.counted_qty - October Stocktake")
print("=" * 100)

try:
    stocktake = Stocktake.objects.get(id=18)  # October stocktake
    print(f"\nStocktake: {stocktake.period_start} to {stocktake.period_end}")
    
    # Test each subcategory in stocktake
    for subcat_code, subcat_name in [
        ('SOFT_DRINKS', 'Soft Drinks'),
        ('SYRUPS', 'Syrups'),
        ('JUICES', 'Juices'),
        ('CORDIALS', 'Cordials'),
        ('BIB', 'BIB')
    ]:
        line = stocktake.lines.filter(
            item__subcategory=subcat_code
        ).first()
        
        if line:
            print(f"\n{subcat_name}: {line.item.sku} - {line.item.name}")
            print(f"  Counted: {line.counted_full_units} + {line.counted_partial_units}")
            print(f"  Counted Qty: {line.counted_qty:.2f} servings")
            print(f"  Expected Qty: {line.expected_qty:.2f} servings")
            print(f"  Variance: {line.variance_qty:.2f} servings")
except Stocktake.DoesNotExist:
    print("⚠ October stocktake (ID=18) not found")

# Summary
print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)

all_minerals = StockItem.objects.filter(category_id='M')
total_minerals = all_minerals.count()

categorized_counts = {
    'SOFT_DRINKS': all_minerals.filter(subcategory='SOFT_DRINKS').count(),
    'SYRUPS': all_minerals.filter(subcategory='SYRUPS').count(),
    'JUICES': all_minerals.filter(subcategory='JUICES').count(),
    'CORDIALS': all_minerals.filter(subcategory='CORDIALS').count(),
    'BIB': all_minerals.filter(subcategory='BIB').count(),
}
uncategorized = all_minerals.filter(subcategory__isnull=True).count()

print(f"\nTotal Minerals Items: {total_minerals}")
print(f"\nCategorized:")
for subcat, count in categorized_counts.items():
    print(f"  {subcat:15s}: {count:3d} items")
print(f"\nUncategorized: {uncategorized} items")

if uncategorized > 0:
    print("\n⚠ WARNING: Some items need manual subcategory assignment!")
    uncategorized_items = all_minerals.filter(subcategory__isnull=True)
    for item in uncategorized_items[:5]:
        print(f"  - {item.sku}: {item.name} (Size: {item.size})")

print("\n" + "=" * 100)
print("✅ TEST COMPLETE")
print("=" * 100)
