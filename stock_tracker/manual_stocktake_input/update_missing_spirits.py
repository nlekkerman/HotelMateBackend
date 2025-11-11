"""
Update the 2 unnamed Spirits items with their SKUs
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("UPDATING MISSING SPIRITS ITEMS")
print("=" * 100)
print()

hotel = Hotel.objects.first()

oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)

# The 2 unnamed items from Excel
missing_spirits = {
    'S_SEADOG': {
        'full': Decimal('3.00'),
        'partial': Decimal('0.90'),
        'value': Decimal('66.81'),
        'name': 'Sea Dog Rum'
    },
    'S_DINGLE_WHISKEY': {
        'full': Decimal('4.00'),
        'partial': Decimal('0.00'),
        'value': Decimal('150.00'),
        'name': 'Dingle Whiskey'
    },
}

updated = 0
not_found = []
calculated_total = Decimal('0.00')

for sku, data in missing_spirits.items():
    snapshot = StockSnapshot.objects.filter(
        period=oct_period,
        item__sku=sku
    ).first()
    
    if not snapshot:
        not_found.append(sku)
        print(f"⚠️  {sku} ({data['name']}) not found in database")
        continue
    
    # For Spirits: full_units = bottles, partial = fractional
    snapshot.closing_full_units = data['full']
    snapshot.closing_partial_units = data['partial']
    snapshot.closing_stock_value = data['value']
    snapshot.save()
    
    calculated_total += data['value']
    updated += 1
    print(f"✓ {sku}: {data['full']} + {data['partial']} = €{data['value']} "
          f"({data['name']})")

print()
print("-" * 100)
print(f"Updated: {updated} items")
print(f"Not found: {len(not_found)} items")
if not_found:
    print(f"Missing SKUs: {', '.join(not_found)}")
print()
print(f"Additional total: €{calculated_total:.2f}")
print()

if updated == 2:
    print("✅ SUCCESS - Both unnamed spirits updated!")
    print("   Total spirits should now match €11,063.66")
else:
    print("⚠️  Some items not found - check SKU codes")

print()
print("=" * 100)
