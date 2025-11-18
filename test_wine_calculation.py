"""
Test Wine calculation logic
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

# Get a wine item
wine = StockItem.objects.filter(category_id='W', active=True).first()

if wine:
    print(f"Wine Item: {wine.sku} - {wine.name}")
    print(f"UOM: {wine.uom} (glasses per bottle)")
    print(f"Unit Cost: €{wine.unit_cost}")
    print()
    
    print("=" * 80)
    print("CURRENT CALCULATION (INCORRECT):")
    print("=" * 80)
    print(f"User counts: 10 bottles + 0.5 fractional")
    print(f"  current_full_units = 10 (bottles)")
    print(f"  current_partial_units = 0.5 (fractional bottle)")
    print()
    print(f"Calculation with UOM = {wine.uom}:")
    print(f"  Servings = (10 × {wine.uom}) + (0.5 × {wine.uom})")
    uom_val = float(wine.uom)
    print(f"  Servings = {10 * uom_val} + {0.5 * uom_val}")
    print(f"  Servings = {10 * uom_val + 0.5 * uom_val} glasses")
    print()
    print("❌ PROBLEM: System calculates in GLASSES (servings)")
    print()
    
    print("=" * 80)
    print("CORRECT CALCULATION (SHOULD BE):")
    print("=" * 80)
    print(f"User counts: 10 bottles + 0.5 fractional")
    print(f"  current_full_units = 10 (bottles)")
    print(f"  current_partial_units = 0.5 (fractional bottle)")
    print()
    print(f"Calculation should be:")
    print(f"  Servings = 10 + 0.5 = 10.5 BOTTLES")
    print(f"  (UOM should NOT multiply the partial units)")
    print()
    print("✅ SOLUTION: Wine should use UOM = 1.0 (bottles)")
    print()
    
    print("=" * 80)
    print("WHY THIS MATTERS:")
    print("=" * 80)
    print("Spirits: UOM = shots per bottle (e.g., 20)")
    print("  - 10 bottles + 0.5 = (10×20) + (0.5×20) = 210 shots ✓")
    print("  - This is correct because 0.5 = half a bottle = 10 shots")
    print()
    print("Wine: Currently UOM = glasses per bottle (e.g., 5)")
    print("  - 10 bottles + 0.5 = (10×5) + (0.5×5) = 52.5 glasses ❌")
    print("  - This is WRONG because 0.5 = half a bottle, not 2.5 glasses!")
    print()
    print("Wine: Should be UOM = 1.0 (bottle = 1 serving)")
    print("  - 10 bottles + 0.5 = (10×1) + (0.5×1) = 10.5 bottles ✓")
    print("  - This is correct because we track wine by BOTTLE, not glass")
