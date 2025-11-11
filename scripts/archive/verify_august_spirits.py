"""
Verify August spirits closing matches September spirits opening.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from hotel.models import Hotel

print("=" * 80)
print("VERIFY AUGUST SPIRITS vs SEPTEMBER OPENING")
print("=" * 80)
print()

# Get September stocktake
hotel = Hotel.objects.first()
stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
)

spirit_lines = stocktake.lines.filter(
    item__category_id='S'
).order_by('item__sku')

# Calculate opening value for spirits
opening_value = Decimal('0.00')
opening_count = 0

print("September Opening Stock - Spirits:")
print("-" * 80)
print(f"{'SKU':<15} {'Opening Qty':<15} {'Cost/Srv':<12} {'Opening Value':<15} {'Name'}")
print("-" * 80)

for line in spirit_lines:
    if line.opening_qty > 0:
        line_value = line.opening_qty * line.valuation_cost
        opening_value += line_value
        opening_count += 1
        print(f"{line.item.sku:<15} {line.opening_qty:<15.2f} €{line.valuation_cost:<11.4f} €{line_value:<14.2f} {line.item.name[:40]}")

print("-" * 80)
print(f"Total spirits with opening stock: {opening_count}")
print(f"Total opening value: €{opening_value:,.2f}")
print()
print("Expected from Excel: €11,392.07")
print(f"Difference: €{float(opening_value) - 11392.07:,.2f}")
print("=" * 80)
