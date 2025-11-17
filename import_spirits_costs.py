"""
Import Spirits unit costs from October Excel
Then recalculate September closing stock values
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockSnapshot, StockPeriod
from hotel.models import Hotel

# Spirits unit costs from October Excel
SPIRITS_COSTS = {
    'S0008': Decimal('12.50'),
    'S0006': Decimal('22.74'),
    'S3214': Decimal('18.33'),
    'S1019': Decimal('17.33'),
    'S0002': Decimal('13.26'),
    'S1401': Decimal('12.84'),
    'S0045': Decimal('24.82'),
    'S29': Decimal('25.44'),
    'S0074': Decimal('16.75'),
    'S2058': Decimal('29.74'),
    'S2033': Decimal('17.83'),
    'S2055': Decimal('38.32'),
    'S0065': Decimal('24.60'),
    'S2148': Decimal('30.83'),
    'S1400': Decimal('19.45'),
    'S0080': Decimal('23.26'),
    'S100': Decimal('26.00'),
    'S0215': Decimal('17.01'),
    'S0162': Decimal('13.07'),
    'S1024': Decimal('16.09'),
    'S0180': Decimal('13.07'),
    'S0190': Decimal('11.96'),
    'S0195': Decimal('16.59'),
    'S5555': Decimal('14.25'),
    'S0009': Decimal('17.17'),
    'S0147': Decimal('29.75'),
    'S0100': Decimal('22.33'),
    'S2314': Decimal('18.67'),
    'S2065': Decimal('30.34'),
    'S0105': Decimal('32.77'),
    'S0027': Decimal('24.78'),
    'S0120': Decimal('17.83'),
    'S0130': Decimal('18.17'),
    'S0135': Decimal('22.92'),
    'S0140': Decimal('23.50'),
    'S0150': Decimal('23.55'),
    'S1203': Decimal('16.75'),
    'S0170': Decimal('23.17'),
    'S0007': Decimal('33.17'),
    'S0205': Decimal('33.18'),
    'S0220': Decimal('17.13'),
    'S3145': Decimal('24.42'),
    'S2369': Decimal('37.50'),
    'S2034': Decimal('20.50'),
    'S_DINGLE_WHISKEY': Decimal('37.50'),
    'S1587': Decimal('19.58'),
    'S0230': Decimal('31.50'),
    'S0026': Decimal('26.66'),
    'S0245': Decimal('20.32'),
    'S0265': Decimal('24.53'),
    'S0014': Decimal('31.09'),
    'S0271': Decimal('38.38'),
    'S0327': Decimal('38.33'),
    'S002': Decimal('25.83'),
    'S0019': Decimal('14.64'),
    'S0306': Decimal('24.88'),
    'S0310': Decimal('31.78'),
    'S1412': Decimal('44.69'),
    'S1258': Decimal('36.17'),
    'S0325': Decimal('10.66'),
    'S0029': Decimal('18.50'),
    'S2156': Decimal('21.35'),
    'S2354': Decimal('31.99'),
    'S1302': Decimal('32.67'),
    'S0335': Decimal('44.06'),
    'S0365': Decimal('22.67'),
    'S0380': Decimal('24.18'),
    'S0385': Decimal('16.92'),
    'S2186': Decimal('31.38'),
    'S0405': Decimal('29.23'),
    'S0255': Decimal('42.01'),
    'S2189': Decimal('31.38'),
    'S0370': Decimal('32.65'),
    'S1002': Decimal('21.05'),
    'S0420': Decimal('13.58'),
    'S1299': Decimal('22.00'),
    'S0021': Decimal('30.50'),
    'S9987': Decimal('22.83'),
    'S1101': Decimal('48.00'),
    'S1205': Decimal('18.95'),
    'S0455': Decimal('13.17'),
    'S2155': Decimal('31.69'),
    'S0699': Decimal('9.72'),
    'S0485': Decimal('9.72'),
    'S2365': Decimal('26.50'),
    'S2349': Decimal('32.92'),
    'S1047': Decimal('25.80'),
    'S0064': Decimal('28.33'),
    'S0530': Decimal('23.67'),
    'S0041': Decimal('15.00'),
    'S24': Decimal('49.97'),
    'S0543': Decimal('12.71'),
    'S0545': Decimal('20.55'),
    'S0550': Decimal('17.50'),
    'S0555': Decimal('32.64'),
    'S2359': Decimal('39.72'),
    'S2241': Decimal('57.33'),
    'S0575': Decimal('46.67'),
    'S1210': Decimal('88.26'),
    'S0585': Decimal('43.06'),
    'S0022': Decimal('30.00'),
    'S2302': Decimal('31.67'),
    'S0605': Decimal('14.29'),
    'S0018': Decimal('16.48'),
    'S_SEADOG': Decimal('17.13'),
    'S2217': Decimal('33.34'),
    'S0001': Decimal('33.83'),
    'S0610': Decimal('21.83'),
    'S0625': Decimal('13.75'),
    'S0010': Decimal('53.03'),
    'S0638': Decimal('22.83'),
    'S0638_00': Decimal('15.00'),
    'S0630': Decimal('17.17'),
    'S2159': Decimal('17.67'),
    'S0012': Decimal('18.17'),
    'S0635': Decimal('20.20'),
    'S1022': Decimal('15.75'),
    'S0640': Decimal('15.33'),
    'S0653': Decimal('13.81'),
    'S3147': Decimal('22.50'),
    'S0647': Decimal('22.57'),
    'S0023': Decimal('12.92'),
    'S0028': Decimal('17.89'),
    'S0017': Decimal('13.89'),
    'S0005': Decimal('13.40'),
    'S2378': Decimal('24.58'),
    'S0071': Decimal('12.42'),
    'S1411': Decimal('61.04'),
}

print(f"\n{'='*80}")
print("IMPORTING SPIRITS UNIT COSTS")
print(f"{'='*80}\n")

hotel = Hotel.objects.first()

# Update items with unit costs
updated_count = 0
not_found = []

for sku, cost in SPIRITS_COSTS.items():
    try:
        item = StockItem.objects.get(hotel=hotel, sku=sku, active=True)
        item.unit_cost = cost
        item.save()
        updated_count += 1
        if updated_count % 20 == 0:
            print(f"Updated {updated_count} spirits...")
    except StockItem.DoesNotExist:
        not_found.append(sku)

print(f"\n{'='*80}")
print(f"✓ Updated {updated_count} spirits with unit costs")
if not_found:
    print(f"⚠ Not found: {len(not_found)} items")
    for sku in not_found:
        print(f"  - {sku}")
print(f"{'='*80}\n")

# Check total items with costs now
total_with_costs = StockItem.objects.filter(
    hotel=hotel, active=True, unit_cost__gt=Decimal('0')
).count()
total_items = StockItem.objects.filter(hotel=hotel, active=True).count()

print(f"Items with unit_cost > 0: {total_with_costs} / {total_items}")
print(f"Items still missing costs: {total_items - total_with_costs}\n")

# Recalculate ALL September closing stock values
print("RECALCULATING ALL SEPTEMBER CLOSING STOCK VALUES")
print(f"{'='*80}\n")

sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)

snapshots = StockSnapshot.objects.filter(
    period=sept_period
).select_related('item', 'item__category')

recalc_count = 0
total_value = Decimal('0')

for snap in snapshots:
    item = snap.item
    cat = item.category.code
    
    # Calculate value based on category
    if cat in ['D', 'B', 'M']:
        # Full units at unit_cost
        full_value = snap.closing_full_units * item.unit_cost
        
        # Partial value calculation
        if cat == 'D':
            # Draught: partial pints
            if item.size_value and item.size_value > 0:
                cost_per_pint = item.unit_cost / Decimal(str(item.size_value))
                partial_value = snap.closing_partial_units * cost_per_pint
            else:
                partial_value = Decimal('0')
        elif cat == 'B':
            # Bottled: partial bottles
            cost_per_bottle = item.unit_cost / Decimal('12')
            partial_value = snap.closing_partial_units * cost_per_bottle
        elif cat == 'M':
            # Minerals: depends on subcategory
            subcategory = item.subcategory
            if subcategory == 'BIB':
                if item.size_value and item.size_value > 0:
                    cost_per_liter = item.unit_cost / Decimal(
                        str(item.size_value)
                    )
                    partial_value = (
                        snap.closing_partial_units * cost_per_liter
                    )
                else:
                    partial_value = Decimal('0')
            elif subcategory in ['SYRUPS', 'BULK_JUICES']:
                partial_value = snap.closing_partial_units * item.unit_cost
            elif subcategory == 'JUICES':
                cost_per_bottle = item.unit_cost / Decimal('12')
                partial_value = snap.closing_partial_units * cost_per_bottle
            else:
                cost_per_bottle = item.unit_cost / Decimal('12')
                partial_value = snap.closing_partial_units * cost_per_bottle
        else:
            partial_value = Decimal('0')
    else:
        # Spirits/Wine: both full and partial at unit_cost per bottle
        full_value = snap.closing_full_units * item.unit_cost
        partial_value = snap.closing_partial_units * item.unit_cost
    
    snap.closing_stock_value = (full_value + partial_value).quantize(
        Decimal('0.01')
    )
    snap.save()
    
    total_value += snap.closing_stock_value
    recalc_count += 1
    
    if recalc_count % 50 == 0:
        print(f"Recalculated {recalc_count} snapshots...")

print(f"\n{'='*80}")
print("COMPLETE - ALL SEPTEMBER CLOSING STOCK VALUES UPDATED")
print(f"{'='*80}")
print(f"✓ Recalculated: {recalc_count} September snapshots")
print(f"✓ Total September closing value: €{total_value:,.2f}")
print(f"{'='*80}\n")

# Show breakdown by category
print("September Closing Stock Value by Category:")
print("-" * 80)

from collections import defaultdict
by_category = defaultdict(lambda: {'count': 0, 'value': Decimal('0')})

for snap in snapshots:
    cat_code = snap.item.category.code
    cat_name = snap.item.category.name
    by_category[cat_code]['name'] = cat_name
    by_category[cat_code]['count'] += 1
    by_category[cat_code]['value'] += snap.closing_stock_value

for cat_code in sorted(by_category.keys()):
    data = by_category[cat_code]
    print(f"{cat_code} - {data['name']:<20} {data['count']:>3} items: "
          f"€{data['value']:>10,.2f}")

print("-" * 80)
print(f"{'TOTAL':<26} {recalc_count:>3} items: €{total_value:>10,.2f}")
print(f"{'='*80}\n")

print("Expected October values from Excel:")
print("-" * 80)
print("Draught Beers:     €5,311.62")
print("Bottled Beers:     €2,288.46")
print("Spirits:          €11,063.66")
print("Minerals/Syrups:   €3,062.43")
print("Wine:              €5,580.35")
print("-" * 80)
print("TOTAL:            €27,306.51")
print(f"{'='*80}\n")
