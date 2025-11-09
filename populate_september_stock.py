"""
Populate September 2025 Stocktake with actual counted stock data
Using data from the Bar Valuation spreadsheet dated 30-09-25
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockItem
from decimal import Decimal

# Get September stocktake
september = Stocktake.objects.get(id=8)
print(f"\n📅 Populating: {september.period_start} to {september.period_end}")

# Counted stock data from spreadsheet (30-09-25)
stock_data = {
    # Draught Beers
    'D2133': {'full': Decimal('0.00'), 'partial': Decimal('26.25')},
    'D0007': {'full': Decimal('0.00'), 'partial': Decimal('17.67')},
    'D1004': {'full': Decimal('3.00'), 'partial': Decimal('26.50')},
    'D0004': {'full': Decimal('2.00'), 'partial': Decimal('26.50')},
    'D0012': {'full': Decimal('0.00'), 'partial': Decimal('0.00')},
    'D0011': {'full': Decimal('1.00'), 'partial': Decimal('26.50')},
    'D2354': {'full': Decimal('2.00'), 'partial': Decimal('13.25')},
    'D1003': {'full': Decimal('2.00'), 'partial': Decimal('26.50')},
    'D0008': {'full': Decimal('1.00'), 'partial': Decimal('26.50')},
    'D1022': {'full': Decimal('4.00'), 'partial': Decimal('0.00')},
    'D0006': {'full': Decimal('2.00'), 'partial': Decimal('0.00')},
    'D1258': {'full': Decimal('6.00'), 'partial': Decimal('39.75')},
    'D0005': {'full': Decimal('3.00'), 'partial': Decimal('22.00')},
    'D0030': {'full': Decimal('5.00'), 'partial': Decimal('0.00')},
    
    # Bottled Beers (partial = loose bottles)
    'B0070': {'full': Decimal('0.00'), 'partial': Decimal('145.00')},
    'B0075': {'full': Decimal('0.00'), 'partial': Decimal('82.00')},
    'B0085': {'full': Decimal('0.00'), 'partial': Decimal('267.00')},
    'B0095': {'full': Decimal('0.00'), 'partial': Decimal('139.00')},
    'B0101': {'full': Decimal('0.00'), 'partial': Decimal('135.00')},
    'B0012': {'full': Decimal('0.00'), 'partial': Decimal('16.00')},
    'B1036': {'full': Decimal('0.00'), 'partial': Decimal('32.00')},
    'B1022': {'full': Decimal('0.00'), 'partial': Decimal('38.00')},
    'B2055': {'full': Decimal('0.00'), 'partial': Decimal('87.00')},
    'B0140': {'full': Decimal('0.00'), 'partial': Decimal('144.00')},
    'B11': {'full': Decimal('0.00'), 'partial': Decimal('69.00')},
    'B14': {'full': Decimal('0.00'), 'partial': Decimal('24.00')},
    'B1006': {'full': Decimal('0.00'), 'partial': Decimal('233.00')},
    'B2308': {'full': Decimal('0.00'), 'partial': Decimal('67.00')},
    'B0205': {'full': Decimal('0.00'), 'partial': Decimal('96.00')},
    'B12': {'full': Decimal('0.00'), 'partial': Decimal('8.00')},
    'B2588': {'full': Decimal('0.00'), 'partial': Decimal('0.00')},
    'B2036': {'full': Decimal('0.00'), 'partial': Decimal('65.00')},
    'B0235': {'full': Decimal('0.00'), 'partial': Decimal('69.00')},
    'B10': {'full': Decimal('0.00'), 'partial': Decimal('44.00')},
    'B0254': {'full': Decimal('0.00'), 'partial': Decimal('136.00')},
    
    # Spirits (partial = fraction of bottle)
    'S0008': {'full': Decimal('2.00'), 'partial': Decimal('0.00')},
    'S0006': {'full': Decimal('2.00'), 'partial': Decimal('0.25')},
    'S3214': {'full': Decimal('6.00'), 'partial': Decimal('0.30')},
    'S1019': {'full': Decimal('2.00'), 'partial': Decimal('0.60')},
    'S0002': {'full': Decimal('8.00'), 'partial': Decimal('0.80')},
    'S1401': {'full': Decimal('3.00'), 'partial': Decimal('0.50')},
    'S0045': {'full': Decimal('7.00'), 'partial': Decimal('0.05')},
    'S29': {'full': Decimal('0.00'), 'partial': Decimal('0.70')},
    'S0074': {'full': Decimal('12.00'), 'partial': Decimal('0.90')},
    'S2058': {'full': Decimal('0.00'), 'partial': Decimal('0.95')},
    'S2033': {'full': Decimal('2.00'), 'partial': Decimal('0.40')},
    'S2055': {'full': Decimal('2.00'), 'partial': Decimal('0.50')},
    'S0065': {'full': Decimal('1.00'), 'partial': Decimal('0.90')},
    'S2148': {'full': Decimal('2.00'), 'partial': Decimal('0.50')},
    'S1400': {'full': Decimal('0.00'), 'partial': Decimal('0.90')},
    'S0080': {'full': Decimal('0.00'), 'partial': Decimal('0.90')},
    'S100': {'full': Decimal('5.00'), 'partial': Decimal('0.05')},
    'S0215': {'full': Decimal('2.50'), 'partial': Decimal('0.00')},
    'S0162': {'full': Decimal('1.50'), 'partial': Decimal('0.00')},
    'S0180': {'full': Decimal('0.40'), 'partial': Decimal('0.00')},
    'S0190': {'full': Decimal('2.00'), 'partial': Decimal('0.10')},
    'S0195': {'full': Decimal('2.00'), 'partial': Decimal('0.00')},
    'S5555': {'full': Decimal('2.00'), 'partial': Decimal('0.00')},
    'S0147': {'full': Decimal('0.00'), 'partial': Decimal('0.90')},
    'S0100': {'full': Decimal('2.00'), 'partial': Decimal('0.00')},
    'S2314': {'full': Decimal('2.00'), 'partial': Decimal('0.50')},
    'S2065': {'full': Decimal('0.00'), 'partial': Decimal('0.35')},
    'S0105': {'full': Decimal('3.00'), 'partial': Decimal('0.55')},
    'S0027': {'full': Decimal('0.00'), 'partial': Decimal('0.85')},
    'S0120': {'full': Decimal('6.00'), 'partial': Decimal('0.85')},
    'S0130': {'full': Decimal('3.00'), 'partial': Decimal('0.70')},
    'S0135': {'full': Decimal('4.00'), 'partial': Decimal('0.05')},
    'S0140': {'full': Decimal('2.00'), 'partial': Decimal('0.60')},
    'S0150': {'full': Decimal('5.00'), 'partial': Decimal('0.70')},
    'S1203': {'full': Decimal('2.00'), 'partial': Decimal('0.20')},
    'S0170': {'full': Decimal('1.00'), 'partial': Decimal('0.70')},
    'S0007': {'full': Decimal('6.00'), 'partial': Decimal('0.40')},
    'S0205': {'full': Decimal('0.00'), 'partial': Decimal('0.60')},
    'S0220': {'full': Decimal('3.00'), 'partial': Decimal('0.90')},
    'S3145': {'full': Decimal('26.00'), 'partial': Decimal('0.70')},
    'S2369': {'full': Decimal('4.00'), 'partial': Decimal('0.00')},
    'S2034': {'full': Decimal('9.00'), 'partial': Decimal('0.70')},
    'S0230': {'full': Decimal('0.00'), 'partial': Decimal('0.10')},
    'S0026': {'full': Decimal('3.00'), 'partial': Decimal('0.65')},
    'S0245': {'full': Decimal('3.00'), 'partial': Decimal('0.30')},
    'S0014': {'full': Decimal('2.00'), 'partial': Decimal('0.10')},
    'S0271': {'full': Decimal('1.00'), 'partial': Decimal('0.85')},
    'S0327': {'full': Decimal('1.00'), 'partial': Decimal('0.20')},
    'S002': {'full': Decimal('5.00'), 'partial': Decimal('0.90')},
    'S0306': {'full': Decimal('7.00'), 'partial': Decimal('0.15')},
    'S0310': {'full': Decimal('3.00'), 'partial': Decimal('0.95')},
    'S1412': {'full': Decimal('10.00'), 'partial': Decimal('0.30')},
    'S1258': {'full': Decimal('0.00'), 'partial': Decimal('0.85')},
    'S0325': {'full': Decimal('3.00'), 'partial': Decimal('0.20')},
    'S0029': {'full': Decimal('1.00'), 'partial': Decimal('0.90')},
    'S2156': {'full': Decimal('2.00'), 'partial': Decimal('0.30')},
    'S2354': {'full': Decimal('1.00'), 'partial': Decimal('0.00')},
    'S1302': {'full': Decimal('2.00'), 'partial': Decimal('0.30')},
    'S0335': {'full': Decimal('3.00'), 'partial': Decimal('0.50')},
    'S0365': {'full': Decimal('2.00'), 'partial': Decimal('0.40')},
    'S0380': {'full': Decimal('4.00'), 'partial': Decimal('0.40')},
    'S0385': {'full': Decimal('3.00'), 'partial': Decimal('0.50')},
    'S2186': {'full': Decimal('2.00'), 'partial': Decimal('0.20')},
    'S0405': {'full': Decimal('8.00'), 'partial': Decimal('0.15')},
    'S0255': {'full': Decimal('1.00'), 'partial': Decimal('0.95')},
    'S2189': {'full': Decimal('1.00'), 'partial': Decimal('0.70')},
    'S0370': {'full': Decimal('2.00'), 'partial': Decimal('0.75')},
    'S1002': {'full': Decimal('3.00'), 'partial': Decimal('0.50')},
    'S0420': {'full': Decimal('5.00'), 'partial': Decimal('0.95')},
    'S1299': {'full': Decimal('1.00'), 'partial': Decimal('0.95')},
    'S0021': {'full': Decimal('2.00'), 'partial': Decimal('0.30')},
    'S9987': {'full': Decimal('7.00'), 'partial': Decimal('0.35')},
    'S1101': {'full': Decimal('2.00'), 'partial': Decimal('0.15')},
    'S0455': {'full': Decimal('1.00'), 'partial': Decimal('0.90')},
    'S2155': {'full': Decimal('2.00'), 'partial': Decimal('0.00')},
    'S0699': {'full': Decimal('5.00'), 'partial': Decimal('0.60')},
    'S0485': {'full': Decimal('2.00'), 'partial': Decimal('0.70')},
    'S2365': {'full': Decimal('1.00'), 'partial': Decimal('0.35')},
    'S2349': {'full': Decimal('0.00'), 'partial': Decimal('0.60')},
    'S1047': {'full': Decimal('1.00'), 'partial': Decimal('0.05')},
    'S0064': {'full': Decimal('2.00'), 'partial': Decimal('0.20')},
    'S0530': {'full': Decimal('4.00'), 'partial': Decimal('0.70')},
    'S0041': {'full': Decimal('4.00'), 'partial': Decimal('0.00')},
    'S24': {'full': Decimal('1.00'), 'partial': Decimal('0.50')},
    'S0543': {'full': Decimal('10.00'), 'partial': Decimal('0.55')},
    'S0545': {'full': Decimal('1.00'), 'partial': Decimal('0.00')},
    'S0550': {'full': Decimal('0.00'), 'partial': Decimal('0.05')},
    'S0555': {'full': Decimal('3.00'), 'partial': Decimal('0.25')},
    'S2359': {'full': Decimal('2.00'), 'partial': Decimal('0.10')},
    'S2241': {'full': Decimal('1.00'), 'partial': Decimal('0.75')},
    'S0575': {'full': Decimal('0.00'), 'partial': Decimal('0.60')},
    'S1210': {'full': Decimal('3.00'), 'partial': Decimal('0.05')},
    'S0585': {'full': Decimal('2.00'), 'partial': Decimal('0.20')},
    'S0022': {'full': Decimal('4.00'), 'partial': Decimal('0.90')},
    'S2302': {'full': Decimal('1.00'), 'partial': Decimal('0.60')},
    'S0605': {'full': Decimal('2.00'), 'partial': Decimal('0.20')},
    'S0018': {'full': Decimal('2.00'), 'partial': Decimal('0.15')},
    'S2217': {'full': Decimal('0.00'), 'partial': Decimal('0.90')},
    'S0001': {'full': Decimal('2.00'), 'partial': Decimal('0.70')},
    'S0610': {'full': Decimal('45.00'), 'partial': Decimal('0.80')},
    'S0625': {'full': Decimal('2.00'), 'partial': Decimal('0.80')},
    'S0010': {'full': Decimal('2.00'), 'partial': Decimal('0.00')},
    'S0638': {'full': Decimal('1.00'), 'partial': Decimal('0.40')},
    'S0630': {'full': Decimal('0.00'), 'partial': Decimal('0.05')},
    'S0012': {'full': Decimal('1.00'), 'partial': Decimal('0.00')},
    'S0635': {'full': Decimal('6.00'), 'partial': Decimal('0.95')},
    'S0640': {'full': Decimal('6.00'), 'partial': Decimal('0.50')},
    'S0653': {'full': Decimal('2.00'), 'partial': Decimal('0.95')},
    'S3147': {'full': Decimal('7.00'), 'partial': Decimal('0.15')},
    'S0647': {'full': Decimal('3.00'), 'partial': Decimal('0.00')},
    'S0023': {'full': Decimal('1.90'), 'partial': Decimal('0.00')},
    'S0028': {'full': Decimal('2.00'), 'partial': Decimal('0.00')},
    'S0017': {'full': Decimal('1.00'), 'partial': Decimal('0.10')},
    'S0005': {'full': Decimal('2.00'), 'partial': Decimal('0.00')},
    'S2378': {'full': Decimal('1.00'), 'partial': Decimal('0.90')},
    'S0071': {'full': Decimal('0.00'), 'partial': Decimal('0.80')},
    'S1411': {'full': Decimal('1.80'), 'partial': Decimal('0.85')},
}

# Continue with more items...
print(f"\n📊 Updating stock counts...")

updated = 0
not_found = []

for sku, values in stock_data.items():
    try:
        line = september.lines.get(item__sku=sku)
        line.counted_full_units = values['full']
        line.counted_partial_units = values['partial']
        line.save()
        updated += 1
        if updated % 20 == 0:
            print(f"   Updated {updated} items...")
    except StocktakeLine.DoesNotExist:
        not_found.append(sku)

print(f"\n✅ Updated {updated} stocktake lines")

if not_found:
    print(f"\n⚠️  {len(not_found)} SKUs not found:")
    for sku in not_found[:10]:
        print(f"   - {sku}")
    if len(not_found) > 10:
        print(f"   ... and {len(not_found) - 10} more")

print(f"\n💰 Financial Summary:")
print(f"   Total COGS: €{september.total_cogs:,.2f}")
print(f"   Total Revenue: €{september.total_revenue:,.2f}")
if september.gross_profit_percentage:
    print(f"   GP%: {september.gross_profit_percentage}%")

print(f"\n✅ September 2025 populated with counted stock!\n")
