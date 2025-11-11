"""
Update October Spirits closing stock from Excel data (31-10-25)
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("UPDATING OCTOBER SPIRITS CLOSING STOCK")
print("=" * 100)
print()

hotel = Hotel.objects.first()

oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)

# Excel data for Spirits (31-10-25)
# For Spirits: full_bottles, partial (fractional 0.XX)
spirits_data = {
    'S0008': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.00')},
    'S0006': {'full': Decimal('2.00'), 'partial': Decimal('0.30'), 'value': Decimal('52.30')},
    'S3214': {'full': Decimal('2.00'), 'partial': Decimal('0.80'), 'value': Decimal('51.32')},
    'S1019': {'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('15.60')},
    'S0002': {'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('79.56')},
    'S1401': {'full': Decimal('3.00'), 'partial': Decimal('0.10'), 'value': Decimal('39.80')},
    'S0045': {'full': Decimal('5.00'), 'partial': Decimal('0.85'), 'value': Decimal('145.20')},
    'S29': {'full': Decimal('1.00'), 'partial': Decimal('0.60'), 'value': Decimal('40.70')},
    'S0074': {'full': Decimal('7.00'), 'partial': Decimal('0.20'), 'value': Decimal('120.60')},
    'S2058': {'full': Decimal('1.00'), 'partial': Decimal('0.80'), 'value': Decimal('53.53')},
    'S2033': {'full': Decimal('1.00'), 'partial': Decimal('0.45'), 'value': Decimal('25.85')},
    'S2055': {'full': Decimal('2.00'), 'partial': Decimal('0.50'), 'value': Decimal('95.80')},
    'S0065': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('49.20')},
    'S2148': {'full': Decimal('2.00'), 'partial': Decimal('0.55'), 'value': Decimal('78.62')},
    'S1400': {'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('17.51')},
    'S0080': {'full': Decimal('3.00'), 'partial': Decimal('0.45'), 'value': Decimal('80.25')},
    'S100': {'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('104.00')},
    'S0215': {'full': Decimal('2.00'), 'partial': Decimal('0.40'), 'value': Decimal('40.82')},
    'S0162': {'full': Decimal('1.50'), 'partial': Decimal('0.00'), 'value': Decimal('19.61')},
    'S1024': {'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('14.48')},
    'S0180': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('26.14')},
    'S0190': {'full': Decimal('2.00'), 'partial': Decimal('0.10'), 'value': Decimal('25.12')},
    'S0195': {'full': Decimal('1.00'), 'partial': Decimal('0.90'), 'value': Decimal('31.52')},
    'S5555': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('28.50')},
    'S0009': {'full': Decimal('0.50'), 'partial': Decimal('0.00'), 'value': Decimal('8.59')},
    'S0147': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'S0100': {'full': Decimal('1.00'), 'partial': Decimal('0.45'), 'value': Decimal('32.38')},
    'S2314': {'full': Decimal('2.00'), 'partial': Decimal('0.30'), 'value': Decimal('42.94')},
    'S2065': {'full': Decimal('1.00'), 'partial': Decimal('0.25'), 'value': Decimal('37.93')},
    'S0105': {'full': Decimal('3.00'), 'partial': Decimal('0.55'), 'value': Decimal('116.33')},
    'S0027': {'full': Decimal('0.00'), 'partial': Decimal('0.75'), 'value': Decimal('18.59')},
    'S0120': {'full': Decimal('3.00'), 'partial': Decimal('0.90'), 'value': Decimal('69.54')},
    'S0130': {'full': Decimal('2.00'), 'partial': Decimal('0.85'), 'value': Decimal('51.78')},
    'S0135': {'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('91.68')},
    'S0140': {'full': Decimal('4.00'), 'partial': Decimal('0.60'), 'value': Decimal('108.10')},
    'S0150': {'full': Decimal('7.00'), 'partial': Decimal('0.35'), 'value': Decimal('173.09')},
    'S1203': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('33.50')},
    'S0170': {'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('20.85')},
    'S0007': {'full': Decimal('6.00'), 'partial': Decimal('0.20'), 'value': Decimal('205.65')},
    'S0205': {'full': Decimal('2.00'), 'partial': Decimal('0.55'), 'value': Decimal('84.61')},
    'S0220': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'S3145': {'full': Decimal('20.00'), 'partial': Decimal('0.10'), 'value': Decimal('490.84')},
    'S2369': {'full': Decimal('3.00'), 'partial': Decimal('0.35'), 'value': Decimal('125.63')},
    'S2034': {'full': Decimal('13.00'), 'partial': Decimal('0.50'), 'value': Decimal('276.75')},
    'S1587': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('39.16')},
    'S0230': {'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('28.35')},
    'S0026': {'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('79.98')},
    'S0245': {'full': Decimal('2.00'), 'partial': Decimal('0.70'), 'value': Decimal('54.86')},
    'S0265': {'full': Decimal('0.00'), 'partial': Decimal('0.30'), 'value': Decimal('7.36')},
    'S0014': {'full': Decimal('1.00'), 'partial': Decimal('0.30'), 'value': Decimal('40.42')},
    'S0271': {'full': Decimal('1.00'), 'partial': Decimal('0.85'), 'value': Decimal('71.00')},
    'S0327': {'full': Decimal('3.00'), 'partial': Decimal('0.20'), 'value': Decimal('122.66')},
    'S002': {'full': Decimal('7.00'), 'partial': Decimal('0.60'), 'value': Decimal('196.31')},
    'S0019': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'S0306': {'full': Decimal('8.00'), 'partial': Decimal('0.75'), 'value': Decimal('217.70')},
    'S0310': {'full': Decimal('3.00'), 'partial': Decimal('0.95'), 'value': Decimal('125.53')},
    'S1412': {'full': Decimal('15.00'), 'partial': Decimal('0.25'), 'value': Decimal('681.52')},
    'S1258': {'full': Decimal('2.00'), 'partial': Decimal('0.85'), 'value': Decimal('103.08')},
    'S0325': {'full': Decimal('3.00'), 'partial': Decimal('0.10'), 'value': Decimal('33.05')},
    'S0029': {'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('18.50')},
    'S2156': {'full': Decimal('2.00'), 'partial': Decimal('0.95'), 'value': Decimal('62.98')},
    'S2354': {'full': Decimal('1.00'), 'partial': Decimal('0.10'), 'value': Decimal('35.19')},
    'S1302': {'full': Decimal('1.00'), 'partial': Decimal('0.80'), 'value': Decimal('58.81')},
    'S0335': {'full': Decimal('5.00'), 'partial': Decimal('0.90'), 'value': Decimal('259.95')},
    'S0365': {'full': Decimal('2.00'), 'partial': Decimal('0.20'), 'value': Decimal('49.87')},
    'S0380': {'full': Decimal('2.00'), 'partial': Decimal('0.10'), 'value': Decimal('50.78')},
    'S0385': {'full': Decimal('2.00'), 'partial': Decimal('0.70'), 'value': Decimal('45.68')},
    'S2186': {'full': Decimal('2.00'), 'partial': Decimal('0.30'), 'value': Decimal('72.17')},
    'S0405': {'full': Decimal('17.00'), 'partial': Decimal('0.80'), 'value': Decimal('520.29')},
    'S0255': {'full': Decimal('6.00'), 'partial': Decimal('0.85'), 'value': Decimal('287.77')},
    'S2189': {'full': Decimal('3.00'), 'partial': Decimal('0.70'), 'value': Decimal('116.11')},
    'S0370': {'full': Decimal('3.00'), 'partial': Decimal('0.10'), 'value': Decimal('101.22')},
    'S1002': {'full': Decimal('3.00'), 'partial': Decimal('0.50'), 'value': Decimal('73.68')},
    'S0420': {'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('40.74')},
    'S1299': {'full': Decimal('3.00'), 'partial': Decimal('0.40'), 'value': Decimal('74.80')},
    'S0021': {'full': Decimal('1.00'), 'partial': Decimal('0.20'), 'value': Decimal('36.60')},
    'S9987': {'full': Decimal('7.00'), 'partial': Decimal('0.25'), 'value': Decimal('165.52')},
    'S1101': {'full': Decimal('1.00'), 'partial': Decimal('0.15'), 'value': Decimal('55.20')},
    'S1205': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'S0455': {'full': Decimal('3.00'), 'partial': Decimal('0.10'), 'value': Decimal('40.83')},
    'S2155': {'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('31.69')},
    'S0699': {'full': Decimal('6.00'), 'partial': Decimal('0.50'), 'value': Decimal('63.18')},
    'S0485': {'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('29.16')},
    'S2365': {'full': Decimal('1.00'), 'partial': Decimal('0.35'), 'value': Decimal('35.78')},
    'S2349': {'full': Decimal('0.00'), 'partial': Decimal('0.40'), 'value': Decimal('13.17')},
    'S1047': {'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('23.22')},
    'S0064': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('56.66')},
    'S0530': {'full': Decimal('2.00'), 'partial': Decimal('0.30'), 'value': Decimal('54.44')},
    'S0041': {'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('15.00')},
    'S24': {'full': Decimal('1.00'), 'partial': Decimal('0.40'), 'value': Decimal('69.96')},
    'S0543': {'full': Decimal('9.00'), 'partial': Decimal('0.40'), 'value': Decimal('119.47')},
    'S0545': {'full': Decimal('1.00'), 'partial': Decimal('0.90'), 'value': Decimal('39.05')},
    'S0550': {'full': Decimal('0.00'), 'partial': Decimal('0.05'), 'value': Decimal('0.88')},
    'S0555': {'full': Decimal('4.00'), 'partial': Decimal('0.90'), 'value': Decimal('159.94')},
    'S2359': {'full': Decimal('2.00'), 'partial': Decimal('0.10'), 'value': Decimal('83.41')},
    'S2241': {'full': Decimal('1.00'), 'partial': Decimal('0.75'), 'value': Decimal('100.33')},
    'S0575': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('93.34')},
    'S1210': {'full': Decimal('2.00'), 'partial': Decimal('0.70'), 'value': Decimal('238.30')},
    'S0585': {'full': Decimal('2.00'), 'partial': Decimal('0.40'), 'value': Decimal('103.34')},
    'S0022': {'full': Decimal('4.00'), 'partial': Decimal('0.90'), 'value': Decimal('147.00')},
    'S2302': {'full': Decimal('1.00'), 'partial': Decimal('0.30'), 'value': Decimal('41.17')},
    'S0605': {'full': Decimal('1.00'), 'partial': Decimal('0.85'), 'value': Decimal('26.44')},
    'S0018': {'full': Decimal('1.00'), 'partial': Decimal('0.65'), 'value': Decimal('27.19')},
    'S2217': {'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('30.01')},
    'S0001': {'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('101.49')},
    'S0610': {'full': Decimal('41.00'), 'partial': Decimal('0.30'), 'value': Decimal('901.58')},
    'S0625': {'full': Decimal('2.00'), 'partial': Decimal('0.55'), 'value': Decimal('35.06')},
    'S0010': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('106.06')},
    'S0638': {'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('45.66')},
    'S0630': {'full': Decimal('0.00'), 'partial': Decimal('0.05'), 'value': Decimal('0.86')},
    'S2159': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'S0012': {'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('18.17')},
    'S0635': {'full': Decimal('6.00'), 'partial': Decimal('0.60'), 'value': Decimal('133.32')},
    'S1022': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'S0640': {'full': Decimal('6.00'), 'partial': Decimal('0.30'), 'value': Decimal('96.58')},
    'S0653': {'full': Decimal('2.00'), 'partial': Decimal('0.95'), 'value': Decimal('40.74')},
    'S3147': {'full': Decimal('7.00'), 'partial': Decimal('0.15'), 'value': Decimal('160.88')},
    'S0647': {'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('67.71')},
    'S0023': {'full': Decimal('1.00'), 'partial': Decimal('0.90'), 'value': Decimal('24.55')},
    'S0028': {'full': Decimal('1.00'), 'partial': Decimal('0.85'), 'value': Decimal('33.10')},
    'S0017': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'S0005': {'full': Decimal('4.00'), 'partial': Decimal('0.90'), 'value': Decimal('65.66')},
    'S2378': {'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    'S0071': {'full': Decimal('2.00'), 'partial': Decimal('0.50'), 'value': Decimal('31.05')},
    'S1411': {'full': Decimal('2.00'), 'partial': Decimal('0.70'), 'value': Decimal('164.81')},
}

expected_total = Decimal('11063.66')

# Note: Excel has 2 unnamed items (Sea Dog Rum, Dingle Whiskey)
# These will need manual checking if they exist with different SKUs

print(f"Updating {len(spirits_data)} Spirits items...")
print()

updated = 0
not_found = []
calculated_total = Decimal('0.00')

for sku, data in spirits_data.items():
    snapshot = StockSnapshot.objects.filter(
        period=oct_period,
        item__sku=sku
    ).first()
    
    if not snapshot:
        not_found.append(sku)
        print(f"⚠️  {sku} not found in database")
        continue
    
    # For Spirits: full_units = bottles, partial = fractional
    snapshot.closing_full_units = data['full']
    snapshot.closing_partial_units = data['partial']
    snapshot.closing_stock_value = data['value']
    snapshot.save()
    
    calculated_total += data['value']
    updated += 1

print(f"✓ Updated {updated} items")
print()
print("-" * 100)
print(f"Not found: {len(not_found)} items")
if not_found:
    print(f"Missing SKUs: {', '.join(not_found[:10])}")
    if len(not_found) > 10:
        print(f"... and {len(not_found) - 10} more")
print()
print(f"Calculated total: €{calculated_total:.2f}")
print(f"Expected total:   €{expected_total:.2f}")
print(f"Difference:       €{(calculated_total - expected_total):.2f}")
print()

if abs(calculated_total - expected_total) < Decimal('1.00'):
    print("✅ SUCCESS - Spirits category updated and matches Excel!")
else:
    print("⚠️  Total differs from expected")
    print("    (May be due to unnamed items in Excel)")

print()
print("=" * 100)
