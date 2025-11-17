"""
Save September and October closing stock values to JSON files.
This preserves the counted values before any cleanup, so we can repopulate later.
"""
import os
import django
import json
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 100)
print("SAVING SEPTEMBER & OCTOBER CLOSING STOCK")
print("=" * 100)
print()

hotel = Hotel.objects.first()

# Get September stocktake
september = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
).first()

# Get October stocktake
october = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=10
).first()

if not september:
    print("❌ September stocktake not found!")
    exit(1)

if not october:
    print("❌ October stocktake not found!")
    exit(1)

print(f"✅ September stocktake found (ID: {september.id})")
print(f"✅ October stocktake found (ID: {october.id})")
print()

# Save September closing stock
september_data = {}
for line in september.lines.all():
    september_data[line.item.sku] = {
        'sku': line.item.sku,
        'name': line.item.name,
        'category': line.item.category.code,
        'counted_full_units': str(line.counted_full_units),
        'counted_partial_units': str(line.counted_partial_units),
        'counted_qty': str(line.counted_qty),
        'counted_value': str(line.counted_value)
    }

# Save October closing stock
october_data = {}
for line in october.lines.all():
    october_data[line.item.sku] = {
        'sku': line.item.sku,
        'name': line.item.name,
        'category': line.item.category.code,
        'counted_full_units': str(line.counted_full_units),
        'counted_partial_units': str(line.counted_partial_units),
        'counted_qty': str(line.counted_qty),
        'counted_value': str(line.counted_value)
    }

# Write to files
with open('september_closing_stock.json', 'w') as f:
    json.dump(september_data, f, indent=2)

with open('october_closing_stock.json', 'w') as f:
    json.dump(october_data, f, indent=2)

print(f"✅ Saved {len(september_data)} September items to september_closing_stock.json")
print(f"✅ Saved {len(october_data)} October items to october_closing_stock.json")
print()

# Summary by category
print("September totals by category:")
sept_totals = {}
for sku, data in september_data.items():
    cat = data['category']
    if cat not in sept_totals:
        sept_totals[cat] = Decimal('0')
    sept_totals[cat] += Decimal(data['counted_value'])

for cat in sorted(sept_totals.keys()):
    print(f"  {cat}: €{sept_totals[cat]:,.2f}")

print()
print("October totals by category:")
oct_totals = {}
for sku, data in october_data.items():
    cat = data['category']
    if cat not in oct_totals:
        oct_totals[cat] = Decimal('0')
    oct_totals[cat] += Decimal(data['counted_value'])

for cat in sorted(oct_totals.keys()):
    print(f"  {cat}: €{oct_totals[cat]:,.2f}")

print()
print("=" * 100)
print("✅ SAVED! You can now clean/test and later restore with these closing values.")
print("=" * 100)
