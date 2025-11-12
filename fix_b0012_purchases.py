"""
Fix B0012 November purchases by recalculating from movements
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockItem, StocktakeLine, Stocktake, StockPeriod
)
from stock_tracker.stocktake_service import _calculate_period_movements
from hotel.models import Hotel

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print("=" * 80)

# Find item B0012
item = StockItem.objects.filter(hotel=hotel, sku='B0012').first()
if not item:
    print("❌ Item B0012 not found!")
    exit()

print(f"\nItem: {item.sku} - {item.name}")

# Get November stocktake
nov_period = StockPeriod.objects.filter(
    hotel=hotel, year=2025, month=11
).first()
nov_stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start=nov_period.start_date,
    period_end=nov_period.end_date
).first()

print(f"Stocktake: {nov_stocktake.id} ({nov_stocktake.status})")
print("=" * 80)

# Get the stocktake line
line = StocktakeLine.objects.filter(
    stocktake=nov_stocktake,
    item=item
).first()

if not line:
    print("❌ No stocktake line found for B0012")
    exit()

print(f"\nBEFORE RECALCULATION:")
print(f"  Opening Qty: {line.opening_qty}")
print(f"  Purchases: {line.purchases}")
print(f"  Waste: {line.waste}")
print(f"  Expected Qty: {line.expected_qty}")
print(f"  Purchases Value: €{line.purchases_value}")
print()

# Recalculate movements from database
print("Recalculating from current movements...")
movements = _calculate_period_movements(
    line.item,
    line.stocktake.period_start,
    line.stocktake.period_end
)

print(f"Calculated movements:")
print(f"  Purchases: {movements['purchases']}")
print(f"  Waste: {movements['waste']}")
print()

# Update the line
line.purchases = movements['purchases']
line.waste = movements['waste']
line.save()

# Reload to verify
line.refresh_from_db()

print(f"AFTER RECALCULATION:")
print(f"  Opening Qty: {line.opening_qty}")
print(f"  Purchases: {line.purchases}")
print(f"  Waste: {line.waste}")
print(f"  Expected Qty: {line.expected_qty}")
print(f"  Purchases Value: €{line.purchases_value}")
print()

print("=" * 80)
print("✅ B0012 purchases field has been recalculated!")
print("=" * 80)
