import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

# Excel data - item by item
excel_items = {
    'M2236': {'value': Decimal('34.53')},
    'M0195': {'value': Decimal('13.68')},
    'M0140': {'value': Decimal('45.33')},
    'M2107': {'value': Decimal('33.39')},
    'M0320': {'value': Decimal('21.56')},
    'M11': {'value': Decimal('20.50')},
    'M0042': {'value': Decimal('249.08')},
    'M0210': {'value': Decimal('267.53')},
    'M0008': {'value': Decimal('20.58')},
    'M0009': {'value': Decimal('20.58')},
    'M3': {'value': Decimal('34.93')},
    'M0006': {'value': Decimal('32.66')},
    'M13': {'value': Decimal('32.03')},
    'M04': {'value': Decimal('36.33')},
    'M0014': {'value': Decimal('35.88')},
    'M2': {'value': Decimal('53.80')},
    'M03': {'value': Decimal('32.03')},
    'M05': {'value': Decimal('35.88')},
    'M06': {'value': Decimal('51.24')},
    'M1': {'value': Decimal('42.46')},
    'M01': {'value': Decimal('36.09')},
    'M9': {'value': Decimal('30.91')},
    'M02': {'value': Decimal('31.33')},
    'M0170': {'value': Decimal('29.68')},
    'M0123': {'value': Decimal('51.60')},
    'M0180': {'value': Decimal('13.81')},
    'M25': {'value': Decimal('427.90')},
    'M24': {'value': Decimal('456.60')},
    'M23': {'value': Decimal('432.65')},
    'M0050': {'value': Decimal('16.93')},
    'M0003': {'value': Decimal('16.93')},
    'M0040': {'value': Decimal('18.67')},
    'M0013': {'value': Decimal('38.72')},
    'M2105': {'value': Decimal('17.60')},
    'M0004': {'value': Decimal('15.33')},
    'M0034': {'value': Decimal('15.33')},
    'M0070': {'value': Decimal('19.09')},
    'M0135': {'value': Decimal('23.47')},
    'M0315': {'value': Decimal('13.60')},
    'M0016': {'value': Decimal('27.31')},
    'M0255': {'value': Decimal('18.35')},
    'M0122': {'value': Decimal('17.33')},
    'M0200': {'value': Decimal('14.93')},
    'M0312': {'value': Decimal('22.40')},
    'M0012': {'value': Decimal('30.35')},
    'M0011': {'value': Decimal('0.00')},
}

excel_total = Decimal('2950.86')

print("=" * 100)
print("ITEM-BY-ITEM COMPARISON: SYSTEM vs EXCEL")
print("=" * 100)

hotel = Hotel.objects.first()

stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).first()

minerals_lines = StocktakeLine.objects.filter(
    stocktake=stocktake,
    item__category__code='M'
).select_related('item').order_by('item__sku')

system_dict = {}
for line in minerals_lines:
    system_dict[line.item.sku] = line.counted_value

print(f"\nExcel items: {len(excel_items)}")
print(f"System items: {len(system_dict)}")

# Find differences
differences = []
missing_in_system = []
extra_in_system = []

for sku in excel_items:
    if sku not in system_dict:
        missing_in_system.append(sku)
    elif abs(system_dict[sku] - excel_items[sku]['value']) > Decimal('0.02'):
        differences.append({
            'sku': sku,
            'excel': excel_items[sku]['value'],
            'system': system_dict[sku],
            'diff': system_dict[sku] - excel_items[sku]['value']
        })

for sku in system_dict:
    if sku not in excel_items:
        extra_in_system.append(sku)

if missing_in_system:
    print(f"\n⚠️  {len(missing_in_system)} items in Excel but NOT in System:")
    print(f"{'SKU':<15} {'Excel Value':>12}")
    print("-" * 30)
    for sku in missing_in_system:
        print(f"{sku:<15} €{excel_items[sku]['value']:>10.2f}")
    
    missing_total = sum(excel_items[sku]['value'] for sku in missing_in_system)
    print(f"{'TOTAL MISSING':<15} €{missing_total:>10.2f}")

if differences:
    print(f"\n⚠️  {len(differences)} items with VALUE differences:")
    print(f"{'SKU':<15} {'Excel':>12} {'System':>12} {'Difference':>12}")
    print("-" * 55)
    for item in differences:
        print(f"{item['sku']:<15} €{item['excel']:>10.2f} "
              f"€{item['system']:>10.2f} €{item['diff']:>10.2f}")
    
    diff_total = sum(item['diff'] for item in differences)
    print(f"{'TOTAL DIFF':<15} {'':<12} {'':<12} €{diff_total:>10.2f}")

if extra_in_system:
    print(f"\n⚠️  {len(extra_in_system)} items in System but NOT in Excel:")
    for sku in extra_in_system:
        print(f"{sku:<15} €{system_dict[sku]:>10.2f}")

# Calculate totals
system_total = sum(system_dict.values())

print("\n" + "=" * 100)
print(f"EXCEL TOTAL:  €{excel_total:>10.2f}")
print(f"SYSTEM TOTAL: €{system_total:>10.2f}")
print(f"DIFFERENCE:   €{system_total - excel_total:>10.2f}")
print("=" * 100)
