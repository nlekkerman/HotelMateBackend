"""
FINAL FIX: Populate September closing for Minerals/Syrups.
For BIB/18LT items: Use ONLY the Cases column (Bottles is fractional part or should be ignored when Cases exists).
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockItem
from hotel.models import Hotel

print("=" * 80)
print("FINAL FIX - MINERALS/SYRUPS CLOSING - BIB ITEMS")
print("=" * 80)
print()

# September closing data for BIB items that need fixing
bib_fixes = {
    'M25': {'total_bags': 1.00, 'value': 171.50},  # Cases: 1, ignore Bottles: 1
    'M23': {'total_bags': 1.00, 'value': 173.06},  # Cases: 1, Bottles: 0 ✅
    'M24': {'total_bags': 0.00, 'value': 0.00},    # Cases: 0, Bottles: 0 ✅
}

# Get September stocktake
hotel = Hotel.objects.first()
stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
)

print("Fixing BIB/18LT items:")
print("-" * 80)

for sku, data in bib_fixes.items():
    try:
        item = StockItem.objects.get(hotel=hotel, sku=sku)
        line = StocktakeLine.objects.get(stocktake=stocktake, item=item)
        
        total_bags = Decimal(str(data['total_bags']))
        full_bags = int(total_bags)
        fractional = total_bags - full_bags
        
        # For BIB: full = integer bags, partial = fractional × UOM (servings)
        line.counted_full_units = Decimal(str(full_bags))
        line.counted_partial_units = fractional * item.uom
        line.save()
        
        print(f"✅ {sku:<10} {item.name:<30} Bags: {total_bags:.2f} → "
              f"Full: {line.counted_full_units}, Partial: {line.counted_partial_units:.2f}")
        
    except Exception as e:
        print(f"❌ {sku:<10} ERROR: {e}")

print("-" * 80)
print()
print("Run check_minerals_data.py to verify")
