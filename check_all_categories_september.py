import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

# September Excel Data
sept_data = {
    'DRAUGHT': {
        'D2133': ('20 Heineken 00%', Decimal('93.85')),
        'D0007': ('30 Beamish', Decimal('126.83')),
        'D1004': ('30 Coors', Decimal('162.12')),
        'D0004': ('30 Heineken', Decimal('162.12')),
        'D0012': ('30 Killarney Blonde', Decimal('164.87')),
        'D0011': ('30 Lagunitas IPA', Decimal('198.53')),
        'D2354': ('30 Moretti', Decimal('183.40')),
        'D1003': ('30 Murphys', Decimal('154.73')),
        'D0008': ('30 Murphys Red', Decimal('157.96')),
        'D1022': ('30 Orchards', Decimal('160.81')),
        'D0006': ('30 OT Wild Orchard', Decimal('160.81')),
        'D1258': ('50 Coors', Decimal('240.72')),
        'D0005': ('50 Guinness', Decimal('228.90')),
        'D0030': ('50 Heineken', Decimal('240.72')),
    },
    'BOTTLED': {
        'B0070': ('Budweiser 33cl', Decimal('31.33')),
        'B0075': ('Bulmers 33cl', Decimal('55.44')),
        'B0085': ('Bulmers Pt Btl', Decimal('73.60')),
        'B0095': ('Coors 330ml', Decimal('37.81')),
        'B0101': ('Corona 33cl', Decimal('36.67')),
        'B0012': ('Cronins 0.0%', Decimal('14.20')),
        'B1036': ('Cronins Cider', Decimal('81.28')),
        'B1022': ('Erdinger Free', Decimal('37.33')),
        'B2055': ('Heineken 0.0% 330ML', Decimal('26.67')),
        'B0140': ('Heineken 330ML', Decimal('36.67')),
        'B11': ('KBC Blond 500ML', Decimal('82.45')),
        'B14': ('KBC Full Circle 500ML', Decimal('82.45')),
        'B1006': ('Kopparberg', Decimal('70.40')),
        'B2308': ('Peroni GF 330ml', Decimal('64.75')),
        'B0205': ('Smirnoff Ice 275ml', Decimal('40.00')),
        'B12': ('Smithwicks 500ML', Decimal('69.60')),
        'B2588': ('Sol L/N', Decimal('31.87')),
        'B2036': ('West C. Cooler. Rose', Decimal('54.67')),
        'B0235': ('West Coast Cooler 275ml', Decimal('54.67')),
        'B10': ('West Coast Sunburst', Decimal('57.07')),
        'B0254': ('WKD. 275ml', Decimal('34.67')),
    },
    'SPIRITS': 128,  # Will check count
    'MINERALS': 46,  # Will check count
    'WINE': 44,  # Will check count
}

sept_totals = {
    'Draught Beer': Decimal('2436.33'),
    'Bottled Beer': Decimal('1097.25'),
    'Spirits': Decimal('11282.39'),
    'Minerals & Syrups': Decimal('2950.86'),
    'Wine': Decimal('1355.87'),
    'GRAND_TOTAL': Decimal('19122.70')
}

print("=" * 100)
print("COMPREHENSIVE COMPARISON: SEPTEMBER EXCEL vs APRIL SYSTEM")
print("=" * 100)

hotel = Hotel.objects.first()
stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).first()

print(f"\nApril Stocktake ID: {stocktake.id}")
print(f"Status: {stocktake.status}")

# Get all categories
categories = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'M': 'Minerals & Syrups',
    'W': 'Wine'
}

print("\n" + "=" * 100)
print("ITEM COUNT COMPARISON")
print("=" * 100)

for code, name in categories.items():
    lines = StocktakeLine.objects.filter(
        stocktake=stocktake,
        item__category__code=code
    )
    april_count = lines.count()
    
    if code == 'D':
        sept_count = len(sept_data['DRAUGHT'])
    elif code == 'B':
        sept_count = len(sept_data['BOTTLED'])
    elif code == 'S':
        sept_count = sept_data['SPIRITS']
    elif code == 'M':
        sept_count = sept_data['MINERALS']
    elif code == 'W':
        sept_count = sept_data['WINE']
    
    match = "✓" if april_count == sept_count else "⚠️"
    print(f"{name:<20} Sept: {sept_count:>3} items  |  April: {april_count:>3} items  {match}")

print("\n" + "=" * 100)
print("VALUE COMPARISON BY CATEGORY")
print("=" * 100)

total_april = Decimal('0')
total_sept = Decimal('0')

for code, name in categories.items():
    lines = StocktakeLine.objects.filter(
        stocktake=stocktake,
        item__category__code=code
    ).select_related('item')
    
    april_value = sum(line.counted_value for line in lines)
    sept_value = sept_totals[name]
    difference = april_value - sept_value
    
    total_april += april_value
    total_sept += sept_value
    
    match = "✓" if abs(difference) < Decimal('0.02') else "⚠️"
    
    print(f"\n{name}")
    print(f"  September Excel:  €{sept_value:>10.2f}")
    print(f"  April System:     €{april_value:>10.2f}")
    print(f"  Difference:       €{difference:>10.2f}  {match}")

print("\n" + "=" * 100)
print("GRAND TOTALS")
print("=" * 100)
print(f"September Excel:  €{total_sept:>10.2f}")
print(f"April System:     €{total_april:>10.2f}")
print(f"Difference:       €{total_april - total_sept:>10.2f}")

grand_diff = total_april - sept_totals['GRAND_TOTAL']
print(f"\nVerification vs Sept Grand Total (€19,122.70): €{grand_diff:>10.2f}")

# Detailed item-level mismatches for Draught
print("\n" + "=" * 100)
print("DRAUGHT BEER - ITEM BY ITEM")
print("=" * 100)

draught_lines = StocktakeLine.objects.filter(
    stocktake=stocktake,
    item__category__code='D'
).select_related('item').order_by('item__sku')

print(f"{'SKU':<10} {'Name':<30} {'Sept Value':>12} {'April Value':>12} {'Diff':>10}")
print("-" * 80)

for line in draught_lines:
    sku = line.item.sku
    if sku in sept_data['DRAUGHT']:
        sept_name, sept_val = sept_data['DRAUGHT'][sku]
        april_val = line.counted_value
        diff = april_val - sept_val
        marker = "⚠️" if abs(diff) > Decimal('0.02') else ""
        print(f"{sku:<10} {sept_name[:29]:<30} €{sept_val:>10.2f} €{april_val:>10.2f} €{diff:>8.2f} {marker}")

# Check for extra items in April not in Sept
print("\n" + "=" * 100)
print("CHECKING FOR EXTRA/MISSING ITEMS")
print("=" * 100)

# Draught
april_draught = set(line.item.sku for line in StocktakeLine.objects.filter(
    stocktake=stocktake, item__category__code='D'))
sept_draught = set(sept_data['DRAUGHT'].keys())

if april_draught - sept_draught:
    print(f"\n⚠️  DRAUGHT items in April but NOT in September:")
    for sku in april_draught - sept_draught:
        print(f"  - {sku}")

if sept_draught - april_draught:
    print(f"\n⚠️  DRAUGHT items in September but NOT in April:")
    for sku in sept_draught - april_draught:
        print(f"  - {sku}")

# Bottled
april_bottled = set(line.item.sku for line in StocktakeLine.objects.filter(
    stocktake=stocktake, item__category__code='B'))
sept_bottled = set(sept_data['BOTTLED'].keys())

if april_bottled - sept_bottled:
    print(f"\n⚠️  BOTTLED items in April but NOT in September:")
    for sku in april_bottled - sept_bottled:
        print(f"  - {sku}")

if sept_bottled - april_bottled:
    print(f"\n⚠️  BOTTLED items in September but NOT in April:")
    for sku in sept_bottled - april_bottled:
        print(f"  - {sku}")

print("\n" + "=" * 100)
