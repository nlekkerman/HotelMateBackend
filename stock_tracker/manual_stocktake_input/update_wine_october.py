"""
Update October 2025 Wine closing stock from Excel data
Bar Valuation 31-10-25
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("UPDATING OCTOBER WINE CLOSING STOCK")
print("=" * 100)
print()

hotel = Hotel.objects.first()

oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)

# Wine data from Excel (Bar Valuation 31-10-25)
# Format: SKU: {full: bottles, partial: fractional, value: stock_value}
wine_data = {
    'W0040': {'full': Decimal('36.00'), 'partial': Decimal('0.00'), 'value': Decimal('124.92')},
    'W31': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'W0039': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'W0019': {'full': Decimal('10.00'), 'partial': Decimal('0.00'), 'value': Decimal('186.70')},
    'W0025': {'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('97.98')},
    'W0044': {'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('36.18')},
    'W0018': {'full': Decimal('11.00'), 'partial': Decimal('0.00'), 'value': Decimal('112.75')},
    'W2108': {'full': Decimal('24.00'), 'partial': Decimal('0.00'), 'value': Decimal('163.92')},
    'W0038': {'full': Decimal('5.00'), 'partial': Decimal('0.00'), 'value': Decimal('49.15')},
    'W0032': {'full': Decimal('3.80'), 'partial': Decimal('0.00'), 'value': Decimal('41.15')},
    'W0036': {'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('63.32')},
    'W0028': {'full': Decimal('11.00'), 'partial': Decimal('0.00'), 'value': Decimal('170.50')},
    'W0023': {'full': Decimal('23.00'), 'partial': Decimal('0.00'), 'value': Decimal('187.22')},
    'W0027': {'full': Decimal('32.00'), 'partial': Decimal('0.00'), 'value': Decimal('240.00')},
    'W0043': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('10.38')},
    'W0031': {'full': Decimal('13.00'), 'partial': Decimal('0.00'), 'value': Decimal('110.50')},
    'W0033': {'full': Decimal('15.60'), 'partial': Decimal('0.00'), 'value': Decimal('132.60')},
    'W2102': {'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('61.12')},
    'W1020': {'full': Decimal('32.00'), 'partial': Decimal('0.00'), 'value': Decimal('224.00')},
    'W2589': {'full': Decimal('50.60'), 'partial': Decimal('0.00'), 'value': Decimal('312.20')},
    'W1004': {'full': Decimal('76.10'), 'partial': Decimal('0.00'), 'value': Decimal('469.54')},
    'W0024': {'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('124.00')},
    'W1013': {'full': Decimal('12.00'), 'partial': Decimal('0.00'), 'value': Decimal('371.88')},
    'W0021': {'full': Decimal('20.00'), 'partial': Decimal('0.00'), 'value': Decimal('197.60')},
    'W0037': {'full': Decimal('10.00'), 'partial': Decimal('0.00'), 'value': Decimal('175.00')},
    'W45': {'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('92.00')},  # Was S45 in Excel
    'W1019': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'W_MDC_PROSECCO': {'full': Decimal('99.00'), 'partial': Decimal('0.00'), 'value': Decimal('319.77')},
    'W_PACSAUD': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'W_PINOT_SNIPES': {'full': Decimal('36.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'W_PROSECCO_NA': {'full': Decimal('21.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'W_OG_SHIRAZ_75': {'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('51.00')},
    'W_OG_SHIRAZ_187': {'full': Decimal('36.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'W_OG_SAUV_187': {'full': Decimal('12.00'), 'partial': Decimal('0.00'), 'value': Decimal('36.00')},
    'W2110': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'W111': {'full': Decimal('13.00'), 'partial': Decimal('0.00'), 'value': Decimal('54.21')},
    'W1': {'full': Decimal('16.00'), 'partial': Decimal('0.00'), 'value': Decimal('142.88')},
    'W0034': {'full': Decimal('12.00'), 'partial': Decimal('0.00'), 'value': Decimal('90.00')},
    'W0041': {'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('62.58')},
    'W0042': {'full': Decimal('16.00'), 'partial': Decimal('0.00'), 'value': Decimal('103.68')},
    'W2104': {'full': Decimal('59.60'), 'partial': Decimal('0.00'), 'value': Decimal('412.43')},
    'W0029': {'full': Decimal('13.00'), 'partial': Decimal('0.00'), 'value': Decimal('127.79')},
    'W0022': {'full': Decimal('49.40'), 'partial': Decimal('0.00'), 'value': Decimal('338.39')},
    'W0030': {'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('87.00')},
}

# Note: All items mapped to database SKUs
# - S45 in Excel is W45 (Primitivo Giola Colle)
# - MDC PROSECCO = W_MDC_PROSECCO
# - O&G items = W_OG_SHIRAZ_75, W_OG_SHIRAZ_187, W_OG_SAUV_187
# - Other unnamed items = W_PACSAUD, W_PINOT_SNIPES, W_PROSECCO_NA

updated = 0
not_found = []
calculated_total = Decimal('0.00')

for sku, data in wine_data.items():
    snapshot = StockSnapshot.objects.filter(
        period=oct_period,
        item__sku=sku
    ).first()
    
    if not snapshot:
        not_found.append(sku)
        print(f"⚠️  {sku} not found in database")
        continue
    
    # For Wine: full_units = bottles, partial = fractional (0.XX)
    # Note: All items in this batch have 0.00 partial
    snapshot.closing_full_units = data['full']
    snapshot.closing_partial_units = data['partial']
    snapshot.closing_stock_value = data['value']
    snapshot.save()
    
    calculated_total += data['value']
    updated += 1
    
    if data['full'] > 0 or data['value'] > 0:
        print(f"✓ {sku}: {data['full']} bottles = €{data['value']}")

print()
print("-" * 100)
print(f"Updated: {updated} items")
print(f"Not found: {len(not_found)} items")
if not_found:
    print(f"Missing SKUs: {', '.join(not_found)}")
print()
print(f"Calculated total: €{calculated_total:.2f}")
print("Expected total: €5,580.35")
difference = calculated_total - Decimal('5580.35')
print(f"Difference: €{difference:.2f}")
print()

if abs(difference) < Decimal('0.10'):
    print("✅ Total matches expected!")
elif abs(difference) < Decimal('1.00'):
    print("✅ Total matches within rounding tolerance!")
else:
    print("⚠️  Total differs from expected")

print()
print("=" * 100)
