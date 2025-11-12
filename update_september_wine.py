"""
Update September 2025 Wine closing stock from Excel data
This will update the Wine category which currently shows €0.00
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 100)
print("UPDATING SEPTEMBER WINE CLOSING STOCK")
print("=" * 100)
print()

hotel = Hotel.objects.first()

# Get September period and stocktake
sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)
print(f"Found period: {sept_period}")

sept_stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
)
print(f"Found stocktake: #{sept_stocktake.id}")
print()

# Wine data from Excel - Closing Stock
# Format: SKU: {bottles: count, value: stock_value}
wine_data = {
    'W0040': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},
    'W31': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},
    'W0039': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},
    'W0019': {'bottles': Decimal('3.00'), 'value': Decimal('56.01')},
    'W0025': {'bottles': Decimal('1.00'), 'value': Decimal('16.33')},
    'W0044': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},
    'W0018': {'bottles': Decimal('3.00'), 'value': Decimal('30.75')},
    'W2108': {'bottles': Decimal('50.80'), 'value': Decimal('346.96')},
    'W0038': {'bottles': Decimal('4.00'), 'value': Decimal('39.32')},
    'W0032': {'bottles': Decimal('3.00'), 'value': Decimal('32.49')},
    'W0036': {'bottles': Decimal('6.00'), 'value': Decimal('94.98')},
    'W0028': {'bottles': Decimal('7.00'), 'value': Decimal('108.50')},
    'W0023': {'bottles': Decimal('2.00'), 'value': Decimal('16.28')},
    'W0027': {'bottles': Decimal('23.00'), 'value': Decimal('172.50')},
    'W0043': {'bottles': Decimal('4.10'), 'value': Decimal('21.28')},
    'W0031': {'bottles': Decimal('11.00'), 'value': Decimal('93.50')},
    'W0033': {'bottles': Decimal('15.00'), 'value': Decimal('127.50')},
    'W2102': {'bottles': Decimal('6.00'), 'value': Decimal('45.84')},
    'W1020': {'bottles': Decimal('30.00'), 'value': Decimal('210.00')},
    'W2589': {'bottles': Decimal('26.40'), 'value': Decimal('162.89')},
    'W1004': {'bottles': Decimal('43.50'), 'value': Decimal('268.40')},
    'W0024': {'bottles': Decimal('5.00'), 'value': Decimal('77.50')},
    'W_PACSAUD': {'bottles': Decimal('8.00'), 'value': Decimal('0.00')},  # Pacsaud Bordeaux Superior
    'W1013': {'bottles': Decimal('13.00'), 'value': Decimal('402.87')},
    'W0021': {'bottles': Decimal('18.00'), 'value': Decimal('177.84')},
    'W_PINOT_SNIPES': {'bottles': Decimal('36.00'), 'value': Decimal('0.00')},  # Pinot Grigio Snipes
    'W0037': {'bottles': Decimal('8.00'), 'value': Decimal('140.00')},
    'W45': {'bottles': Decimal('7.00'), 'value': Decimal('80.50')},
    'W_PROSECCO_NA': {'bottles': Decimal('10.00'), 'value': Decimal('0.00')},  # No Alcohol Prosecco
    'W1019': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},
    'W_MDC_PROSECCO': {'bottles': Decimal('99.00'), 'value': Decimal('319.77')},
    'W2110': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},
    'W111': {'bottles': Decimal('18.00'), 'value': Decimal('75.06')},
    'W1': {'bottles': Decimal('15.00'), 'value': Decimal('133.95')},
    'W0034': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},
    'W0041': {'bottles': Decimal('10.20'), 'value': Decimal('106.39')},
    'W0042': {'bottles': Decimal('21.50'), 'value': Decimal('139.32')},
    'W_OG_SHIRAZ_75': {'bottles': Decimal('6.00'), 'value': Decimal('51.00')},  # O&G SHIRAZ 6X75CL
    'W_OG_SHIRAZ_187': {'bottles': Decimal('0.00'), 'value': Decimal('0.00')},  # O&G SHIRAZ 12X187ML
    'W_OG_SAUV_187': {'bottles': Decimal('12.00'), 'value': Decimal('36.00')},  # O&G SAUVIGNON BLANC 12X187ML
    'W2104': {'bottles': Decimal('48.70'), 'value': Decimal('337.00')},
    'W0029': {'bottles': Decimal('12.00'), 'value': Decimal('117.96')},
    'W0022': {'bottles': Decimal('49.70'), 'value': Decimal('340.45')},
    'W0030': {'bottles': Decimal('6.00'), 'value': Decimal('87.00')},
}

print("Updating StockSnapshot (closing stock for period)...")
snapshot_updated = 0
snapshot_not_found = []
snapshot_total = Decimal('0.00')

for sku, data in wine_data.items():
    snapshot = StockSnapshot.objects.filter(
        period=sept_period,
        item__sku=sku
    ).first()
    
    if not snapshot:
        snapshot_not_found.append(sku)
        print(f"⚠️  Snapshot for {sku} not found")
        continue
    
    snapshot.closing_full_units = data['bottles']
    snapshot.closing_partial_units = Decimal('0.00')
    snapshot.closing_stock_value = data['value']
    snapshot.save()
    
    snapshot_total += data['value']
    snapshot_updated += 1
    
    if data['bottles'] > 0:
        print(f"✓ {sku}: {data['bottles']} bottles = €{data['value']}")

print()
print("Updating StocktakeLine (counted stock for stocktake)...")
line_updated = 0
line_not_found = []
line_total = Decimal('0.00')

for sku, data in wine_data.items():
    line = StocktakeLine.objects.filter(
        stocktake=sept_stocktake,
        item__sku=sku
    ).first()
    
    if not line:
        line_not_found.append(sku)
        print(f"⚠️  Line for {sku} not found")
        continue
    
    # Update counted values
    line.counted_full_units = data['bottles']
    line.counted_partial_units = Decimal('0.00')
    line.save()
    
    line_updated += 1
    line_total += data['value']

print()
print("-" * 100)
print("SNAPSHOT RESULTS:")
print(f"  Updated: {snapshot_updated} items")
print(f"  Not found: {len(snapshot_not_found)} items")
if snapshot_not_found:
    print(f"  Missing: {', '.join(snapshot_not_found)}")
print(f"  Total value: €{snapshot_total:.2f}")
print()

print("STOCKTAKE LINE RESULTS:")
print(f"  Updated: {line_updated} items")
print(f"  Not found: {len(line_not_found)} items")
if line_not_found:
    print(f"  Missing: {', '.join(line_not_found)}")
print(f"  Total value: €{line_total:.2f}")
print()

print("EXPECTED FROM EXCEL:")
print(f"  Total: €4,466.13")
difference = snapshot_total - Decimal('4466.13')
print(f"  Difference: €{difference:.2f}")
print()

if abs(difference) < Decimal('0.10'):
    print("✅ Total matches expected!")
elif abs(difference) < Decimal('1.00'):
    print("✅ Total matches within rounding tolerance!")
else:
    print("⚠️  Total differs from expected")

print()
print("=" * 100)
print("NEXT STEP: Generate September PDF again to see updated Wine values")
print("=" * 100)
