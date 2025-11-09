"""
Populate September 2025 - Part 2: Minerals and Wine
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from decimal import Decimal

september = Stocktake.objects.get(id=8)
print(f"\n📅 Populating Part 2: Minerals & Wine")

# Minerals/Syrups data
stock_data_m_w = {
    # Minerals
    'M0140': {'full': Decimal('0.00'), 'partial': Decimal('90.00')},
    'M2107': {'full': Decimal('0.00'), 'partial': Decimal('103.00')},
    'M0320': {'full': Decimal('7.60'), 'partial': Decimal('0.55')},
    'M11': {'full': Decimal('0.00'), 'partial': Decimal('138.00')},
    'M0042': {'full': Decimal('0.00'), 'partial': Decimal('43.00')},
    'M0210': {'full': Decimal('0.00'), 'partial': Decimal('43.00')},
    'M3': {'full': Decimal('3.30'), 'partial': Decimal('0.00')},
    'M0006': {'full': Decimal('3.00'), 'partial': Decimal('0.00')},
    'M13': {'full': Decimal('0.40'), 'partial': Decimal('0.00')},
    'M04': {'full': Decimal('2.40'), 'partial': Decimal('0.00')},
    'M0014': {'full': Decimal('10.70'), 'partial': Decimal('0.00')},
    'M2': {'full': Decimal('11.40'), 'partial': Decimal('0.00')},
    'M03': {'full': Decimal('14.00'), 'partial': Decimal('0.00')},
    'M05': {'full': Decimal('7.30'), 'partial': Decimal('0.00')},
    'M06': {'full': Decimal('17.00'), 'partial': Decimal('0.00')},
    'M1': {'full': Decimal('6.50'), 'partial': Decimal('0.00')},
    'M01': {'full': Decimal('3.00'), 'partial': Decimal('0.00')},
    'M5': {'full': Decimal('2.50'), 'partial': Decimal('0.00')},
    'M9': {'full': Decimal('3.00'), 'partial': Decimal('0.00')},
    'M02': {'full': Decimal('6.00'), 'partial': Decimal('0.00')},
    'M0170': {'full': Decimal('0.00'), 'partial': Decimal('6.00')},
    'M0123': {'full': Decimal('0.00'), 'partial': Decimal('580.00')},
    'M0180': {'full': Decimal('0.00'), 'partial': Decimal('10.00')},
    'M25': {'full': Decimal('1.00'), 'partial': Decimal('1.00')},
    'M23': {'full': Decimal('1.00'), 'partial': Decimal('0.00')},
    'M0050': {'full': Decimal('0.00'), 'partial': Decimal('56.00')},
    'M0040': {'full': Decimal('0.00'), 'partial': Decimal('279.00')},
    'M2105': {'full': Decimal('0.00'), 'partial': Decimal('301.00')},
    'M0004': {'full': Decimal('0.00'), 'partial': Decimal('169.00')},
    'M0034': {'full': Decimal('0.00'), 'partial': Decimal('78.00')},
    'M0070': {'full': Decimal('0.00'), 'partial': Decimal('52.00')},
    'M0135': {'full': Decimal('0.00'), 'partial': Decimal('151.00')},
    'M0315': {'full': Decimal('0.00'), 'partial': Decimal('294.00')},
    'M0016': {'full': Decimal('0.00'), 'partial': Decimal('14.00')},
    'M0255': {'full': Decimal('0.00'), 'partial': Decimal('384.00')},
    'M0122': {'full': Decimal('0.00'), 'partial': Decimal('27.00')},
    'M0200': {'full': Decimal('0.00'), 'partial': Decimal('536.00')},
    'M0312': {'full': Decimal('0.00'), 'partial': Decimal('136.00')},
    'M0012': {'full': Decimal('0.00'), 'partial': Decimal('1.00')},
    
    # Wine
    'W0019': {'full': Decimal('3.00'), 'partial': Decimal('0.00')},
    'W0025': {'full': Decimal('1.00'), 'partial': Decimal('0.00')},
    'W0018': {'full': Decimal('3.00'), 'partial': Decimal('0.00')},
    'W2108': {'full': Decimal('50.80'), 'partial': Decimal('0.00')},
    'W0038': {'full': Decimal('4.00'), 'partial': Decimal('0.00')},
    'W0032': {'full': Decimal('3.00'), 'partial': Decimal('0.00')},
    'W0036': {'full': Decimal('6.00'), 'partial': Decimal('0.00')},
    'W0028': {'full': Decimal('7.00'), 'partial': Decimal('0.00')},
    'W0023': {'full': Decimal('2.00'), 'partial': Decimal('0.00')},
    'W0027': {'full': Decimal('23.00'), 'partial': Decimal('0.00')},
    'W0043': {'full': Decimal('4.10'), 'partial': Decimal('0.00')},
    'W0031': {'full': Decimal('11.00'), 'partial': Decimal('0.00')},
    'W0033': {'full': Decimal('15.00'), 'partial': Decimal('0.00')},
    'W2102': {'full': Decimal('6.00'), 'partial': Decimal('0.00')},
    'W1020': {'full': Decimal('30.00'), 'partial': Decimal('0.00')},
    'W2589': {'full': Decimal('26.40'), 'partial': Decimal('0.00')},
    'W1004': {'full': Decimal('43.50'), 'partial': Decimal('0.00')},
    'W0024': {'full': Decimal('5.00'), 'partial': Decimal('0.00')},
    'W1013': {'full': Decimal('13.00'), 'partial': Decimal('0.00')},
    'W0021': {'full': Decimal('18.00'), 'partial': Decimal('0.00')},
    'W0037': {'full': Decimal('8.00'), 'partial': Decimal('0.00')},
    'S45': {'full': Decimal('7.00'), 'partial': Decimal('0.00')},
    'W1019': {'full': Decimal('0.00'), 'partial': Decimal('0.00')},
    'W31': {'full': Decimal('99.00'), 'partial': Decimal('0.00')},  # 20cl Prosecco
    'W111': {'full': Decimal('18.00'), 'partial': Decimal('0.00')},
    'W1': {'full': Decimal('15.00'), 'partial': Decimal('0.00')},
    'W0041': {'full': Decimal('10.20'), 'partial': Decimal('0.00')},
    'W0042': {'full': Decimal('21.50'), 'partial': Decimal('0.00')},
    'W2104': {'full': Decimal('48.70'), 'partial': Decimal('0.00')},
    'W0029': {'full': Decimal('12.00'), 'partial': Decimal('0.00')},
    'W0022': {'full': Decimal('49.70'), 'partial': Decimal('0.00')},
    'W0030': {'full': Decimal('6.00'), 'partial': Decimal('0.00')},
}

print(f"\n📊 Updating Minerals & Wine counts...")

updated = 0
not_found = []

for sku, values in stock_data_m_w.items():
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

print(f"\n✅ Updated {updated} more stocktake lines")

if not_found:
    print(f"\n⚠️  {len(not_found)} SKUs not found:")
    for sku in not_found[:10]:
        print(f"   - {sku}")

# Final summary
total_lines = september.lines.count()
counted_lines = september.lines.filter(
    counted_full_units__gt=0
).count() + september.lines.filter(
    counted_partial_units__gt=0
).count()

print(f"\n📊 Stock Count Summary:")
print(f"   Total items: {total_lines}")
print(f"   Items with counts: {counted_lines}")
print(f"   Items still at zero: {total_lines - counted_lines}")

print(f"\n💰 Financial Summary:")
print(f"   Total COGS: €{september.total_cogs:,.2f}")
print(f"   Total Revenue: €{september.total_revenue:,.2f}")
if september.gross_profit_percentage:
    print(f"   GP%: {september.gross_profit_percentage}%")

print(f"\n✅ September 2025 fully populated!\n")
