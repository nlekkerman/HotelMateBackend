"""
Import unit costs from October Excel data
Then recalculate September closing stock values
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockSnapshot, StockPeriod
from hotel.models import Hotel

# Unit costs from October Excel
UNIT_COSTS = {
    # Draught Beer
    'D2133': Decimal('59.72'),
    'D0007': Decimal('92.08'),
    'D1004': Decimal('117.70'),
    'D0004': Decimal('117.70'),
    'D0012': Decimal('119.70'),
    'D0011': Decimal('144.14'),
    'D2354': Decimal('133.15'),
    'D1003': Decimal('112.34'),
    'D0008': Decimal('114.68'),
    'D1022': Decimal('116.75'),
    'D0006': Decimal('116.75'),
    'D1258': Decimal('196.14'),
    'D0005': Decimal('186.51'),
    'D0030': Decimal('196.14'),
    
    # Bottled Beer
    'B0070': Decimal('11.75'),
    'B0075': Decimal('20.79'),
    'B0085': Decimal('27.60'),
    'B0095': Decimal('14.18'),
    'B0101': Decimal('13.75'),
    'B0012': Decimal('14.20'),
    'B1036': Decimal('30.48'),
    'B1022': Decimal('14.00'),
    'B2055': Decimal('10.00'),
    'B0140': Decimal('13.75'),
    'B11': Decimal('30.92'),
    'B14': Decimal('30.92'),
    'B1006': Decimal('26.40'),
    'B2308': Decimal('24.28'),
    'B0205': Decimal('15.00'),
    'B12': Decimal('26.10'),
    'B2588': Decimal('11.95'),
    'B2036': Decimal('20.50'),
    'B0235': Decimal('20.50'),
    'B10': Decimal('21.40'),
    'B0254': Decimal('13.00'),
}

print(f"\n{'='*80}")
print("IMPORTING UNIT COSTS FROM OCTOBER EXCEL")
print(f"{'='*80}\n")

hotel = Hotel.objects.first()

# Update items with unit costs
updated_count = 0
not_found = []

for sku, cost in UNIT_COSTS.items():
    try:
        item = StockItem.objects.get(hotel=hotel, sku=sku, active=True)
        item.unit_cost = cost
        item.save()
        updated_count += 1
        print(f"✓ {sku:<10} unit_cost = €{cost}")
    except StockItem.DoesNotExist:
        not_found.append(sku)
        print(f"✗ {sku:<10} NOT FOUND")

print(f"\n{'='*80}")
print(f"Updated {updated_count} items")
if not_found:
    print(f"Not found: {len(not_found)} items - {', '.join(not_found)}")
print(f"{'='*80}\n")

# Now recalculate September closing stock values
print("RECALCULATING SEPTEMBER CLOSING STOCK VALUES")
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
        # For kegs/cases: full units at unit_cost, partial at cost_per_bottle
        full_value = snap.closing_full_units * item.unit_cost
        
        # Partial value calculation
        if cat == 'D':
            # Draught: partial pints, cost per pint = unit_cost / pints_per_keg
            if item.size_value and item.size_value > 0:
                cost_per_pint = item.unit_cost / Decimal(str(item.size_value))
                partial_value = snap.closing_partial_units * cost_per_pint
            else:
                partial_value = Decimal('0')
        elif cat == 'B':
            # Bottled: partial bottles, cost per bottle = unit_cost / 12
            cost_per_bottle = item.unit_cost / Decimal('12')
            partial_value = snap.closing_partial_units * cost_per_bottle
        else:  # M
            # Minerals: depends on subcategory
            partial_value = Decimal('0')
    else:
        # Spirits/Wine: both full and partial at unit_cost
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

# Show samples with values
print("Sample September closing stock (with values):")
print("-" * 80)

samples = snapshots.filter(
    item__sku__in=['B0070', 'B0085', 'D0004', 'D2354', 'D1258']
)

for snap in samples:
    item = snap.item
    print(f"{item.sku:<10} {item.name:<40}")
    print(f"  [{item.category.code}] {snap.closing_full_units} full, "
          f"{snap.closing_partial_units} partial")
    print(f"  unit_cost: €{item.unit_cost}, value: €{snap.closing_stock_value}\n")

print(f"{'='*80}\n")
