"""
Update October Draught Beer closing stock from Excel data (31-10-25)
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("UPDATING OCTOBER DRAUGHT BEER CLOSING STOCK")
print("=" * 100)
print()

hotel = Hotel.objects.first()

oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)

# Excel data for Draught Beer (31-10-25)
draught_data = {
    'D2133': {'full_kegs': Decimal('0.00'), 'pints': Decimal('40.00'), 'value': Decimal('68.25')},
    'D0007': {'full_kegs': Decimal('0.00'), 'pints': Decimal('79.00'), 'value': Decimal('137.25')},
    'D1004': {'full_kegs': Decimal('0.00'), 'pints': Decimal('0.00'), 'value': Decimal('0.00')},
    'D0004': {'full_kegs': Decimal('0.00'), 'pints': Decimal('0.00'), 'value': Decimal('0.00')},
    'D0012': {'full_kegs': Decimal('0.00'), 'pints': Decimal('0.00'), 'value': Decimal('0.00')},
    'D0011': {'full_kegs': Decimal('0.00'), 'pints': Decimal('5.00'), 'value': Decimal('13.60')},
    'D2354': {'full_kegs': Decimal('0.00'), 'pints': Decimal('304.00'), 'value': Decimal('763.73')},
    'D1003': {'full_kegs': Decimal('0.00'), 'pints': Decimal('198.00'), 'value': Decimal('419.69')},
    'D0008': {'full_kegs': Decimal('0.00'), 'pints': Decimal('26.50'), 'value': Decimal('57.34')},
    'D1022': {'full_kegs': Decimal('0.00'), 'pints': Decimal('296.00'), 'value': Decimal('652.04')},
    'D0006': {'full_kegs': Decimal('0.00'), 'pints': Decimal('93.00'), 'value': Decimal('204.86')},
    'D1258': {'full_kegs': Decimal('6.00'), 'pints': Decimal('39.75'), 'value': Decimal('1265.44')},
    'D0005': {'full_kegs': Decimal('0.00'), 'pints': Decimal('246.00'), 'value': Decimal('521.38')},
    'D0030': {'full_kegs': Decimal('0.00'), 'pints': Decimal('542.00'), 'value': Decimal('1208.04')},
}

expected_total = Decimal('5311.62')

print(f"Updating {len(draught_data)} Draught Beer items...")
print()

updated = 0
not_found = []
calculated_total = Decimal('0.00')

for sku, data in draught_data.items():
    snapshot = StockSnapshot.objects.filter(
        period=oct_period,
        item__sku=sku
    ).first()
    
    if not snapshot:
        not_found.append(sku)
        print(f"⚠️  {sku} not found in database")
        continue
    
    # For Draught: full_units = kegs, partial_units = pints (servings)
    snapshot.closing_full_units = data['full_kegs']
    snapshot.closing_partial_units = data['pints']
    snapshot.closing_stock_value = data['value']
    snapshot.save()
    
    calculated_total += data['value']
    updated += 1
    print(f"✓ {sku}: {data['full_kegs']} kegs + {data['pints']} pints = €{data['value']}")

print()
print("-" * 100)
print(f"Updated: {updated} items")
print(f"Not found: {len(not_found)} items")
print()
print(f"Calculated total: €{calculated_total:.2f}")
print(f"Expected total:   €{expected_total:.2f}")
print(f"Difference:       €{(calculated_total - expected_total):.2f}")
print()

if abs(calculated_total - expected_total) < Decimal('0.10'):
    print("✅ SUCCESS - Draught Beer category updated and matches Excel!")
else:
    print("⚠️  Total differs from expected")

print()
print("=" * 100)
