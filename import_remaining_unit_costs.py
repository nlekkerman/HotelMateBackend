"""
Import remaining unit costs (Minerals, Wine) from October Excel
Then recalculate September closing stock values
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockSnapshot, StockPeriod
from hotel.models import Hotel

# Minerals & Syrups unit costs from October Excel
MINERALS_COSTS = {
    'M2236': Decimal('12.95'),
    'M0195': Decimal('5.13'),
    'M0140': Decimal('17.00'),
    'M2107': Decimal('12.52'),
    'M0320': Decimal('6.16'),
    'M11': Decimal('1.00'),
    'M0042': Decimal('12.15'),
    'M0210': Decimal('13.05'),
    'M0008': Decimal('5.88'),
    'M0009': Decimal('5.88'),
    'M3': Decimal('9.98'),
    'M0006': Decimal('9.33'),
    'M13': Decimal('9.15'),
    'M04': Decimal('10.38'),
    'M0014': Decimal('10.25'),
    'M2': Decimal('15.37'),
    'M03': Decimal('9.15'),
    'M05': Decimal('10.25'),
    'M06': Decimal('14.64'),
    'M1': Decimal('12.13'),
    'M5': Decimal('10.31'),
    'M9': Decimal('8.83'),
    'M02': Decimal('8.95'),
    'M0170': Decimal('11.13'),
    'M0123': Decimal('19.35'),
    'M0180': Decimal('5.18'),
    'M25': Decimal('171.16'),
    'M24': Decimal('182.64'),
    'M23': Decimal('173.06'),
    'M0050': Decimal('6.35'),
    'M0003': Decimal('6.35'),
    'M0040': Decimal('7.00'),
    'M0013': Decimal('14.52'),
    'M2105': Decimal('6.60'),
    'M0004': Decimal('5.75'),
    'M0034': Decimal('5.75'),
    'M0070': Decimal('7.16'),
    'M0135': Decimal('8.80'),
    'M0315': Decimal('5.10'),
    'M0016': Decimal('10.24'),
    'M0255': Decimal('6.88'),
    'M0122': Decimal('6.50'),
    'M0200': Decimal('5.60'),
    'M0312': Decimal('8.40'),
    'M0012': Decimal('8.67'),
    'M0011': Decimal('0.00'),
}

# Wine unit costs from October Excel
WINE_COSTS = {
    'W0040': Decimal('3.47'),
    'W31': Decimal('3.23'),
    'W0039': Decimal('6.75'),
    'W0019': Decimal('18.67'),
    'W0025': Decimal('16.33'),
    'W0044': Decimal('12.06'),
    'W0018': Decimal('10.25'),
    'W2108': Decimal('6.83'),
    'W0038': Decimal('9.83'),
    'W0032': Decimal('10.83'),
    'W0036': Decimal('15.83'),
    'W0028': Decimal('15.50'),
    'W0023': Decimal('8.14'),
    'W0027': Decimal('7.50'),
    'W0043': Decimal('5.19'),
    'W0031': Decimal('8.50'),
    'W0033': Decimal('8.50'),
    'W2102': Decimal('7.64'),
    'W1020': Decimal('7.00'),
    'W2589': Decimal('6.17'),
    'W1004': Decimal('6.17'),
    'W0024': Decimal('15.50'),
    'W1013': Decimal('30.99'),
    'W0021': Decimal('9.88'),
    'W0037': Decimal('17.50'),
    'W45': Decimal('11.50'),  # Primitivo Giola Colle
    'W1019': Decimal('9.33'),
    'W_MDC_PROSECCO': Decimal('3.23'),
    'W2110': Decimal('7.96'),
    'W111': Decimal('4.17'),
    'W1': Decimal('8.93'),
    'W0034': Decimal('7.50'),
    'W0041': Decimal('10.43'),
    'W0042': Decimal('6.48'),
    'W_OG_SHIRAZ_75': Decimal('8.50'),
    'W_OG_SHIRAZ_187': Decimal('8.50'),
    'W_OG_SAUV_187': Decimal('3.00'),
    'W2104': Decimal('6.92'),
    'W0029': Decimal('9.83'),
    'W0022': Decimal('6.85'),
    'W0030': Decimal('14.50'),
}

print(f"\n{'='*80}")
print("IMPORTING MINERALS & WINE UNIT COSTS")
print(f"{'='*80}\n")

hotel = Hotel.objects.first()

# Combine all new costs
ALL_COSTS = {**MINERALS_COSTS, **WINE_COSTS}

# Update items with unit costs
updated_count = 0
not_found = []

for sku, cost in ALL_COSTS.items():
    try:
        item = StockItem.objects.get(hotel=hotel, sku=sku, active=True)
        item.unit_cost = cost
        item.save()
        updated_count += 1
        if updated_count % 10 == 0:
            print(f"Updated {updated_count} items...")
    except StockItem.DoesNotExist:
        not_found.append(sku)
        print(f"✗ {sku:<20} NOT FOUND")

print(f"\n{'='*80}")
print(f"✓ Updated {updated_count} items with unit costs")
if not_found:
    print(f"⚠ Not found: {len(not_found)} items")
    print(f"  {', '.join(not_found)}")
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
            # Draught: partial pints, cost per pint
            if item.size_value and item.size_value > 0:
                cost_per_pint = item.unit_cost / Decimal(str(item.size_value))
                partial_value = snap.closing_partial_units * cost_per_pint
            else:
                partial_value = Decimal('0')
        elif cat == 'B':
            # Bottled: partial bottles, cost per bottle = unit_cost / 12
            cost_per_bottle = item.unit_cost / Decimal('12')
            partial_value = snap.closing_partial_units * cost_per_bottle
        elif cat == 'M':
            # Minerals: depends on subcategory
            subcategory = item.subcategory
            if subcategory == 'BIB':
                # BIB: 18L containers, partial in liters
                if item.size_value and item.size_value > 0:
                    cost_per_liter = item.unit_cost / Decimal(str(item.size_value))
                    partial_value = snap.closing_partial_units * cost_per_liter
                else:
                    partial_value = Decimal('0')
            elif subcategory in ['SYRUPS', 'BULK_JUICES']:
                # Syrups/Juices: individual bottles
                partial_value = snap.closing_partial_units * item.unit_cost
            elif subcategory == 'JUICES':
                # Juices in cases: partial bottles
                cost_per_bottle = item.unit_cost / Decimal('12')
                partial_value = snap.closing_partial_units * cost_per_bottle
            else:
                # Soft drinks in cases: partial bottles
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
print("COMPLETE")
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
