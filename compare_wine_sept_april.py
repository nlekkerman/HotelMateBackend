import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

# September Excel Wine data
sept_wine = {
    'W0040': {'name': '1/4 Jack Rabbit 187Ml', 'value': Decimal('12.15')},
    'W31': {'name': '200ml De Faveri Prosecco', 'value': Decimal('11.31')},
    'W0039': {'name': 'Alvier Chardonny', 'value': Decimal('23.63')},
    'W0019': {'name': 'Chablis Emeraude', 'value': Decimal('65.35')},
    'W0025': {'name': 'Chateau De Domy', 'value': Decimal('57.16')},
    'W0044': {'name': 'Chateau Haut Baradiou', 'value': Decimal('42.21')},
    'W0018': {'name': 'Chateau Pascaud', 'value': Decimal('35.88')},
    'W2108': {'name': 'Cheval Chardonny', 'value': Decimal('23.91')},
    'W0038': {'name': 'Classic South Sauv Blanc', 'value': Decimal('34.41')},
    'W0032': {'name': 'De La Chevaliere Rose', 'value': Decimal('37.91')},
    'W0036': {'name': 'Domaine Petit Chablis', 'value': Decimal('55.41')},
    'W0028': {'name': 'Domiane Fleurie', 'value': Decimal('54.25')},
    'W0023': {'name': 'El Somo Rioja Crianza', 'value': Decimal('28.49')},
    'W0027': {'name': 'Equino Malbec', 'value': Decimal('26.25')},
    'W0043': {'name': 'Fuego Blanco', 'value': Decimal('18.17')},
    'W0031': {'name': 'La Chevaliere Chardonny', 'value': Decimal('29.75')},
    'W0033': {'name': 'Les Jamelles Sauv-Blanc', 'value': Decimal('29.75')},
    'W2102': {'name': 'Les Petits Jamelles Rose', 'value': Decimal('26.74')},
    'W1020': {'name': 'Les Roche Merlot', 'value': Decimal('24.50')},
    'W2589': {'name': 'MarquesPlata Sauv/Blanc', 'value': Decimal('21.60')},
    'W1004': {'name': 'MarquesPlata Temp/Syrah', 'value': Decimal('21.60')},
    'W0024': {'name': 'Moilard Macon Village', 'value': Decimal('54.25')},
    'W_PACSAUD': {'name': 'Pacsaud Bordeaux Superior', 'value': Decimal('0.00')},
    'W1013': {'name': 'Pannier', 'value': Decimal('108.47')},
    'W0021': {'name': 'Pazo Albarino', 'value': Decimal('34.58')},
    'W_PINOT_SNIPES': {'name': 'Pinot Grigio Snipes', 'value': Decimal('0.00')},
    'W0037': {'name': 'Pouilly Tume Lucy', 'value': Decimal('61.25')},
    'W45': {'name': 'Primitivo Giola Colle', 'value': Decimal('40.25')},
    'W_PROSECCO_NA': {'name': 'No Alcohol Prosecco', 'value': Decimal('0.00')},
    'W1019': {'name': 'Prosecco Collie', 'value': Decimal('32.66')},
    'W_MDC_PROSECCO': {'name': 'MDC PROSECCO DOC TRE F 24X20CL', 'value': Decimal('11.31')},
    'W2110': {'name': 'Real Camponia Verdejo', 'value': Decimal('27.86')},
    'W111': {'name': 'Reina 5.5%', 'value': Decimal('14.60')},
    'W1': {'name': 'Rialto Prosecco 750ML', 'value': Decimal('31.26')},
    'W0034': {'name': 'Roquende Cab-Sauv', 'value': Decimal('26.25')},
    'W0041': {'name': 'Roquende Chardonny', 'value': Decimal('36.51')},
    'W0042': {'name': 'Roquende Rose', 'value': Decimal('22.68')},
    'W_OG_SHIRAZ_75': {'name': 'O&G SHIRAZ 6X75CL', 'value': Decimal('29.75')},
    'W_OG_SHIRAZ_187': {'name': 'O&G SHIRAZ 12X187ML', 'value': Decimal('0.00')},
    'W_OG_SAUV_187': {'name': 'O&G SAUVIGNON BLANC 12X187ML', 'value': Decimal('10.50')},
    'W2104': {'name': 'Santa Ana Malbec', 'value': Decimal('24.22')},
    'W0029': {'name': 'Serra d Conte Castelli', 'value': Decimal('34.41')},
    'W0022': {'name': 'Sonnetti Pinot Grigo', 'value': Decimal('23.98')},
    'W0030': {'name': 'Tenuta Barbera dAsti DOCG', 'value': Decimal('50.75')},
}

sept_total = Decimal('1355.87')

# April system data
print("=" * 100)
print("WINE ITEM-BY-ITEM COMPARISON: APRIL SYSTEM vs SEPTEMBER EXCEL")
print("=" * 100)

hotel = Hotel.objects.first()

stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).first()

wine_lines = StocktakeLine.objects.filter(
    stocktake=stocktake,
    item__category__code='W'
).select_related('item').order_by('item__sku')

april_dict = {}
for line in wine_lines:
    april_dict[line.item.sku] = line.counted_value

print(f"\nSeptember Excel items: {len(sept_wine)}")
print(f"April System items: {len(april_dict)}")

# Find differences
differences = []
missing_in_april = []
extra_in_april = []

for sku in sept_wine:
    if sku not in april_dict:
        missing_in_april.append(sku)
    elif abs(april_dict[sku] - sept_wine[sku]['value']) > Decimal('0.02'):
        differences.append({
            'sku': sku,
            'name': sept_wine[sku]['name'],
            'sept': sept_wine[sku]['value'],
            'april': april_dict[sku],
            'diff': april_dict[sku] - sept_wine[sku]['value']
        })

for sku in april_dict:
    if sku not in sept_wine:
        extra_in_april.append(sku)

if missing_in_april:
    print(f"\n⚠️  {len(missing_in_april)} items in September Excel but NOT in April System:")
    print(f"{'SKU':<20} {'Sept Value':>12}")
    print("-" * 35)
    for sku in missing_in_april:
        print(f"{sku:<20} €{sept_wine[sku]['value']:>10.2f}")
    
    missing_total = sum(sept_wine[sku]['value'] for sku in missing_in_april)
    print(f"{'TOTAL MISSING':<20} €{missing_total:>10.2f}")

if differences:
    print(f"\n⚠️  {len(differences)} items with VALUE differences:")
    print(f"{'SKU':<20} {'Name':<35} {'Sept':>10} {'April':>10} {'Diff':>10}")
    print("-" * 90)
    for item in differences:
        print(f"{item['sku']:<20} {item['name'][:35]:<35} "
              f"€{item['sept']:>8.2f} €{item['april']:>8.2f} €{item['diff']:>8.2f}")
    
    diff_total = sum(item['diff'] for item in differences)
    print(f"{'TOTAL DIFF':<20} {'':<35} {'':<10} {'':<10} €{diff_total:>8.2f}")

if extra_in_april:
    print(f"\n⚠️  {len(extra_in_april)} items in April System but NOT in September Excel:")
    for sku in extra_in_april:
        print(f"{sku:<20} €{april_dict[sku]:>10.2f}")

# Calculate totals
april_total = sum(april_dict.values())

print("\n" + "=" * 100)
print(f"SEPTEMBER EXCEL TOTAL:  €{sept_total:>10.2f}")
print(f"APRIL SYSTEM TOTAL:     €{april_total:>10.2f}")
print(f"DIFFERENCE:             €{april_total - sept_total:>10.2f}")
print("=" * 100)
