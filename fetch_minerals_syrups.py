"""
Fetch minerals and syrups details to discuss serving size logic
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StocktakeLine, Stocktake
from decimal import Decimal

print("=" * 120)
print("MINERALS & SYRUPS - SERVING SIZE ANALYSIS")
print("=" * 120)

# Get October stocktake
stocktake = Stocktake.objects.get(id=18)

# Get all minerals/syrups
minerals = StockItem.objects.filter(
    category_id='M'
).order_by('name')

print(f'\nTotal Minerals/Syrups Items: {minerals.count()}')
print("\n" + "=" * 120)

# Group by size pattern
dozen_items = []
liter_items = []
individual_items = []

for item in minerals:
    size = item.size or ''
    size_upper = size.upper()
    
    if 'DOZ' in size_upper:
        dozen_items.append(item)
    elif 'LT' in size_upper and 'ML' not in size_upper:
        liter_items.append(item)
    elif 'LITER' in size_upper or 'LITRE' in size_upper:
        liter_items.append(item)
    else:
        individual_items.append(item)

print(f"\nDOZEN ITEMS (Cases + Bottles): {len(dozen_items)}")
print("-" * 120)
for item in dozen_items[:10]:  # Show first 10
    print(f"{item.sku:10s} | {item.name:50s} | Size: {item.size:15s} | UOM: {item.uom:6.2f}")
    print(f"           | Current: {item.current_full_units} cases + {item.current_partial_units} bottles")
    print(f"           | Unit Cost: €{item.unit_cost:.4f}/case | Servings: {item.total_stock_in_servings:.2f} bottles")
    print()

print(f"\nLITER/BIB ITEMS (Boxes + Liters): {len(liter_items)}")
print("-" * 120)
for item in liter_items[:10]:  # Show first 10
    print(f"{item.sku:10s} | {item.name:50s} | Size: {item.size:15s} | UOM: {item.uom:6.2f}")
    print(f"           | Current: {item.current_full_units} boxes + {item.current_partial_units} liters")
    print(f"           | Unit Cost: €{item.unit_cost:.4f}/box | Servings: {item.total_stock_in_servings:.2f} liters")
    print()

print(f"\nINDIVIDUAL ITEMS (Bottles + Fractional): {len(individual_items)}")
print("-" * 120)
for item in individual_items[:10]:  # Show first 10
    print(f"{item.sku:10s} | {item.name:50s} | Size: {item.size:15s} | UOM: {item.uom:6.2f}")
    print(f"           | Current: {item.current_full_units} bottles + {item.current_partial_units:.2f} fractional")
    print(f"           | Unit Cost: €{item.unit_cost:.4f}/bottle | Servings: {item.total_stock_in_servings:.2f}")
    print()

# Now check October stocktake lines
print("\n" + "=" * 120)
print("OCTOBER STOCKTAKE - MINERALS/SYRUPS LINES")
print("=" * 120)

mineral_lines = stocktake.lines.filter(
    item__category_id='M'
).select_related('item').order_by('item__size', 'item__name')

print(f'\nTotal Lines: {mineral_lines.count()}')

# Show some examples from each type
print("\n\nDOZEN EXAMPLES:")
print("-" * 120)
dozen_lines = mineral_lines.filter(item__size__icontains='Doz')[:5]
for line in dozen_lines:
    print(f"\n{line.item.sku} - {line.item.name}")
    print(f"  Size: {line.item.size} | UOM: {line.item.uom} bottles/case")
    print(f"  Counted: {line.counted_full_units} cases + {line.counted_partial_units} bottles")
    print(f"  Counted Qty: {line.counted_qty:.2f} bottles")
    print(f"  Expected: {line.expected_qty:.2f} bottles")
    print(f"  Variance: {line.variance_qty:.2f} bottles")

print("\n\nLITER/BIB EXAMPLES:")
print("-" * 120)
liter_lines = [line for line in mineral_lines if 'LT' in line.item.size.upper() and 'ML' not in line.item.size.upper()][:5]
for line in liter_lines:
    print(f"\n{line.item.sku} - {line.item.name}")
    print(f"  Size: {line.item.size} | UOM: {line.item.uom} liters/box")
    print(f"  Counted: {line.counted_full_units} boxes + {line.counted_partial_units} liters")
    print(f"  Counted Qty: {line.counted_qty:.2f} liters")
    print(f"  Expected: {line.expected_qty:.2f} liters")
    print(f"  Variance: {line.variance_qty:.2f} liters")

print("\n\nINDIVIDUAL BOTTLE EXAMPLES:")
print("-" * 120)
individual_lines = [line for line in mineral_lines 
                   if 'DOZ' not in line.item.size.upper() 
                   and 'LT' not in line.item.size.upper()][:5]
for line in individual_lines:
    print(f"\n{line.item.sku} - {line.item.name}")
    print(f"  Size: {line.item.size} | UOM: {line.item.uom} servings/bottle")
    print(f"  Counted: {line.counted_full_units} bottles + {line.counted_partial_units:.2f} fractional")
    print(f"  Counted Qty: {line.counted_qty:.2f} servings")
    print(f"  Expected: {line.expected_qty:.2f} servings")
    print(f"  Variance: {line.variance_qty:.2f} servings")

print("\n" + "=" * 120)
print("KEY SERVING SIZE QUESTIONS:")
print("=" * 120)
print("""
1. DOZEN ITEMS (e.g., Coca Cola 24 Doz):
   - UOM = 24 bottles per case
   - Partial units = individual bottles (0-23)
   - Serving size = 1 bottle
   - Question: Is this the right serving unit? Or should we track by ml?

2. LITER/BIB ITEMS (e.g., Pepsi 18Lt BIB):
   - UOM = 18 liters per box
   - Partial units = individual liters
   - Serving size = ?
   - Question: What is one "serving" of a BIB? 
     - Is it 200ml (standard soft drink)?
     - Is it just tracked in liters?

3. INDIVIDUAL BOTTLES (e.g., Red Bull 250ml):
   - UOM = servings per bottle
   - Partial units = fractional bottle
   - Serving size = ?
   - Question: Is 1 bottle = 1 serving? Or multiple servings per bottle?

4. SYRUPS (e.g., Monin Syrup 700ml):
   - UOM = servings per bottle
   - Partial units = fractional bottle
   - Serving size = ?
   - Question: What is one serving of syrup? 25ml? 30ml?

CURRENT LOGIC:
- Category M is treated like bottles with Doz special case
- BIB (LT) follows draught logic: partial = servings (liters)
- Everything else: partial = fractional bottle

DECISION NEEDED:
- What is the ACTUAL serving size we want to track?
- Should BIB be tracked by liters or by servings (drinks)?
- Should syrups have a defined ml per serving?
""")

print("\n" + "=" * 120)
