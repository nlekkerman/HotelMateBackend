"""
Check Wine UOM and Cost Settings
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

print("=" * 80)
print("WINE UOM & COST ANALYSIS")
print("=" * 80)

# Check W0023 specifically
wine = StockItem.objects.get(sku='W0023', hotel_id=2)

print(f"\nSKU: {wine.sku}")
print(f"Name: {wine.name}")
print(f"Size: {wine.size} ({wine.size_value}{wine.size_unit})")
print(f"UOM: {wine.uom}")
print(f"Unit Cost: €{wine.unit_cost}")
print(f"Cost per Serving: €{wine.cost_per_serving}")

print(f"\n--- 2.75 BOTTLES CALCULATION ---")
print(f"Total servings: 2.75 bottles × {wine.uom} UOM = {2.75 * float(wine.uom):.2f} servings")
print(f"Value: {2.75 * float(wine.uom):.2f} servings × €{wine.cost_per_serving} = €{2.75 * float(wine.uom) * float(wine.cost_per_serving):.2f}")

print(f"\n--- CORRECT CALCULATION (if UOM should be bottles) ---")
print(f"If UOM = 1 (bottle = 1 unit):")
print(f"Cost per bottle = unit_cost = €{wine.unit_cost}")
print(f"Value: 2.75 bottles × €{wine.unit_cost} = €{2.75 * float(wine.unit_cost):.2f}")

print(f"\n--- CORRECT CALCULATION (if tracking glasses) ---")
# Standard wine bottle = 750ml, standard glass = 175ml
glasses_per_bottle = 750 / 175  # ~4.29 glasses
print(f"If UOM = {glasses_per_bottle:.2f} glasses per bottle:")
print(f"Total glasses: 2.75 bottles × {glasses_per_bottle:.2f} = {2.75 * glasses_per_bottle:.2f} glasses")
print(f"Cost per glass: €{wine.unit_cost} / {glasses_per_bottle:.2f} = €{float(wine.unit_cost) / glasses_per_bottle:.4f}")
print(f"Value: {2.75 * glasses_per_bottle:.2f} glasses × €{float(wine.unit_cost) / glasses_per_bottle:.4f} = €{2.75 * float(wine.unit_cost):.2f}")

print("\n" + "=" * 80)
print("CHECK ALL WINES UOM")
print("=" * 80)

wines = StockItem.objects.filter(hotel_id=2, category_id='W', active=True).order_by('sku')

uom_summary = {}
for wine in wines:
    uom_val = float(wine.uom)
    if uom_val not in uom_summary:
        uom_summary[uom_val] = []
    uom_summary[uom_val].append(wine.sku)

print(f"\nUOM Distribution across {wines.count()} wines:")
for uom_val in sorted(uom_summary.keys()):
    count = len(uom_summary[uom_val])
    print(f"  UOM = {uom_val}: {count} wines")
    if count <= 5:
        print(f"    SKUs: {', '.join(uom_summary[uom_val])}")

print("\n" + "=" * 80)
print("PROBLEM DIAGNOSIS")
print("=" * 80)
print("""
THE ISSUE:
- UOM = 1 means "1 serving per bottle"
- This makes cost_per_serving = unit_cost / 1 = unit_cost (cost per bottle)
- When calculating value: servings × cost_per_serving = bottles × cost_per_bottle ✓
- BUT the calculation is using: (bottles × UOM) × cost_per_serving
- With UOM=1: (2.75 × 1) × cost_per_serving = correct value ✓

WAIT - let me check the actual backend calculation...

The formula in total_stock_in_servings for wine:
  full_servings = current_full_units × uom
  partial_servings = current_partial_units × uom
  total = full_servings + partial_servings

With UOM=1:
  (2 × 1) + (0.75 × 1) = 2.75 servings ✓

Value calculation:
  total_servings × cost_per_serving
  = 2.75 × cost_per_serving

If cost_per_serving = unit_cost (because UOM=1):
  = 2.75 × unit_cost ✓

This should be CORRECT!

Let me check if cost_per_serving is calculated correctly...
""")

print("\n--- CHECKING COST CALCULATIONS ---")
wine = StockItem.objects.get(sku='W0023', hotel_id=2)
print(f"\nW0023 - {wine.name}")
print(f"Unit Cost: €{wine.unit_cost}")
print(f"UOM: {wine.uom}")
print(f"Cost per Serving (property): €{wine.cost_per_serving}")
print(f"Expected (unit_cost / uom): €{float(wine.unit_cost) / float(wine.uom):.4f}")

if wine.cost_per_serving != wine.unit_cost / wine.uom:
    print("⚠️ MISMATCH in cost_per_serving calculation!")
else:
    print("✓ cost_per_serving is correct")

print(f"\nFor 2.75 bottles:")
print(f"Servings: {2.75 * float(wine.uom):.2f}")
print(f"Value: €{2.75 * float(wine.uom) * float(wine.cost_per_serving):.2f}")
