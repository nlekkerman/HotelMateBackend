"""
Update October Bottled Beer closing stock from Excel data (31-10-25)
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("UPDATING OCTOBER BOTTLED BEER CLOSING STOCK")
print("=" * 100)
print()

hotel = Hotel.objects.first()

oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)

# Excel data for Bottled Beer (31-10-25)
# For Dozen items: full_cases=0, bottles=total bottles
bottled_data = {
    'B0070': {'bottles': Decimal('113.00'), 'value': Decimal('110.65')},
    'B0075': {'bottles': Decimal('121.00'), 'value': Decimal('209.63')},
    'B0085': {'bottles': Decimal('181.00'), 'value': Decimal('416.30')},
    'B0095': {'bottles': Decimal('74.00'), 'value': Decimal('87.44')},
    'B0101': {'bottles': Decimal('85.00'), 'value': Decimal('97.40')},
    'B0012': {'bottles': Decimal('69.00'), 'value': Decimal('81.65')},
    'B1036': {'bottles': Decimal('37.00'), 'value': Decimal('93.98')},
    'B1022': {'bottles': Decimal('26.00'), 'value': Decimal('30.33')},
    'B2055': {'bottles': Decimal('54.00'), 'value': Decimal('45.00')},
    'B0140': {'bottles': Decimal('125.00'), 'value': Decimal('143.23')},
    'B11': {'bottles': Decimal('16.00'), 'value': Decimal('41.23')},
    'B14': {'bottles': Decimal('26.00'), 'value': Decimal('66.99')},
    'B1006': {'bottles': Decimal('190.00'), 'value': Decimal('418.00')},
    'B2308': {'bottles': Decimal('41.00'), 'value': Decimal('82.96')},
    'B0205': {'bottles': Decimal('76.00'), 'value': Decimal('95.00')},
    'B12': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},
    'B2588': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},
    'B2036': {'bottles': Decimal('62.00'), 'value': Decimal('105.92')},
    'B0235': {'bottles': Decimal('65.00'), 'value': Decimal('111.04')},
    'B10': {'bottles': Decimal('29.00'), 'value': Decimal('51.72')},
    'B0254': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},
}

expected_total = Decimal('2288.46')

print(f"Updating {len(bottled_data)} Bottled Beer items...")
print()

updated = 0
not_found = []
calculated_total = Decimal('0.00')

for sku, data in bottled_data.items():
    snapshot = StockSnapshot.objects.filter(
        period=oct_period,
        item__sku=sku
    ).first()
    
    if not snapshot:
        not_found.append(sku)
        print(f"⚠️  {sku} not found in database")
        continue
    
    # For Bottled Beer (Doz): 
    # full_units = 0 (no full cases)
    # partial_units = total bottles
    snapshot.closing_full_units = Decimal('0.00')
    snapshot.closing_partial_units = data['bottles']
    snapshot.closing_stock_value = data['value']
    snapshot.save()
    
    calculated_total += data['value']
    updated += 1
    
    if data['bottles'] > 0:
        print(f"✓ {sku}: {data['bottles']} bottles = €{data['value']}")

print()
print("-" * 100)
print(f"Updated: {updated} items")
print(f"Not found: {len(not_found)} items")
if not_found:
    print(f"Missing SKUs: {', '.join(not_found)}")
print()
print(f"Calculated total: €{calculated_total:.2f}")
print(f"Expected total:   €{expected_total:.2f}")
print(f"Difference:       €{(calculated_total - expected_total):.2f}")
print()

if abs(calculated_total - expected_total) < Decimal('0.10'):
    print("✅ SUCCESS - Bottled Beer category updated and matches Excel!")
else:
    print("⚠️  Total differs from expected")

print()
print("=" * 100)
