"""
Examine Wine items to identify the UOM and display issue
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StocktakeLine, Stocktake

print("=" * 120)
print("EXAMINING WINE ITEMS - UOM vs DISPLAY ISSUE")
print("=" * 120)
print()

# Get all wine items
wines = StockItem.objects.filter(category_id='W', active=True).order_by('sku')

print(f"Total Wine Items: {wines.count()}\n")

print("WINE ITEM DETAILS:")
print("-" * 120)
print(f"{'SKU':<15} {'Name':<50} {'Size':<10} {'UOM':<10} {'Unit Cost':<12}")
print("-" * 120)

uom_groups = {}
for wine in wines:
    print(f"{wine.sku:<15} {wine.name[:50]:<50} {wine.size:<10} {wine.uom:<10} €{wine.unit_cost:<11.4f}")
    
    # Group by UOM
    uom_key = float(wine.uom)
    if uom_key not in uom_groups:
        uom_groups[uom_key] = []
    uom_groups[uom_key].append(wine)

print()
print("=" * 120)
print("UOM DISTRIBUTION:")
print("=" * 120)
for uom, items in sorted(uom_groups.items()):
    print(f"\nUOM = {uom} ({len(items)} items)")
    if uom == 1.0:
        print("  → Calculation: 1 serving per bottle (CORRECT for bottle-sold wine)")
    elif uom == 1.25:
        print("  → Calculation: 1.25 glasses per bottle (187ml ÷ 150ml)")
    elif uom == 5.0:
        print("  → Calculation: 5 glasses per bottle (750ml ÷ 150ml)")
    elif uom == 4.0:
        print("  → Calculation: 4 glasses per bottle (750ml ÷ 175ml)")
    else:
        print(f"  → UNEXPECTED UOM VALUE!")

print()
print("=" * 120)
print("THE ISSUE:")
print("=" * 120)
print("""
PROBLEM IDENTIFIED:
-------------------
Wine items have different UOM values (1.0, 1.25, 4.0, 5.0) which represent:
- UOM = 1.0: Wine sold by bottle (correct - 1 serving = 1 bottle)
- UOM = 4.0 or 5.0: Wine sold by glass (glasses per bottle)
- UOM = 1.25: Small bottles (187ml) sold by glass

CURRENT SYSTEM BEHAVIOR:
------------------------
1. Stock calculation: Uses UOM to convert bottles → glasses
   - 12 bottles × UOM (5 glasses) = 60 servings (glasses)

2. Display: Shows "bottles + fractional"
   - Shows: "12.5 bottles"

FRONTEND DISPLAY ISSUE:
-----------------------
If wine UOM = 5.0 (glasses per bottle):
- User counts: 12 bottles + 0.5 fractional
- System calculates: (12 × 5) + (0.5 × 5) = 62.5 glasses (servings)
- Display converts back: 62.5 servings ÷ 5 = 12.5 bottles ✓ CORRECT

BUT if display shows "glasses" instead of "bottles":
- Opening: 62.5 glasses
- Expected: 62.5 glasses
- Counted: 62.5 glasses
This is confusing because users count BOTTLES not GLASSES!

CORRECT BEHAVIOR:
-----------------
Wine should ALWAYS display in BOTTLES regardless of UOM:
- UOM = 1.0: Sold by bottle → display bottles ✓
- UOM = 5.0: Sold by glass → but COUNTED by bottle → display bottles ✓
""")

print()
print("=" * 120)
print("CHECKING RECENT STOCKTAKE LINES:")
print("=" * 120)

# Get most recent stocktake
latest_stocktake = Stocktake.objects.filter(
    hotel__id=2
).order_by('-date_conducted').first()

if latest_stocktake:
    print(f"\nStocktake: {latest_stocktake.id} - {latest_stocktake.date_conducted}")
    print(f"Period: {latest_stocktake.period}")
    
    wine_lines = StocktakeLine.objects.filter(
        stocktake=latest_stocktake,
        item__category_id='W'
    ).select_related('item')[:10]
    
    print(f"\nSample Wine Lines ({wine_lines.count()} shown):")
    print("-" * 120)
    print(f"{'SKU':<12} {'Name':<40} {'UOM':<8} {'Full':<10} {'Partial':<10} {'Counted Qty':<12}")
    print("-" * 120)
    
    for line in wine_lines:
        print(f"{line.item.sku:<12} {line.item.name[:40]:<40} "
              f"{line.item.uom:<8} {line.counted_full_units:<10} "
              f"{line.counted_partial_units:<10} {line.counted_qty:<12.2f}")
    
    print()
    print("INTERPRETATION:")
    print("---------------")
    print("counted_full_units = number of BOTTLES")
    print("counted_partial_units = fractional bottle (0.00-0.99)")
    print("counted_qty = SERVINGS (bottles × UOM + fractional × UOM)")
    print()
    print("If UOM = 5.0 and counted = 2 bottles + 0.5:")
    print("  → counted_full_units = 2")
    print("  → counted_partial_units = 0.5")
    print("  → counted_qty = (2 × 5) + (0.5 × 5) = 12.5 glasses")
    print("  → Display should show: '2.5 bottles' (NOT '12.5 glasses')")

print()
print("=" * 120)
print("RECOMMENDATION:")
print("=" * 120)
print("""
✅ WINE COUNTING IS CORRECT!

The system is working as designed:
1. Users count BOTTLES (e.g., 12 bottles + 0.5)
2. System converts to servings using UOM (e.g., 12.5 × 5 = 62.5 glasses)
3. Display shows BOTTLES (12.5 bottles)

The UOM field represents:
- For wine sold by BOTTLE: UOM = 1.0
- For wine sold by GLASS: UOM = glasses per bottle (4 or 5)

But DISPLAY should always show BOTTLES because that's what staff count!

If frontend is showing "glasses" for display_unit:
→ This is the BUG - should show "bottles" instead

CHECK: stock_serializers.py display_unit field for Wine category
""")

print()
