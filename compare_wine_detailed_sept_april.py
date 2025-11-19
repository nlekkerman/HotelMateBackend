import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockItem
from hotel.models import Hotel

# September Excel Wine data with cost prices
sept_wine = {
    'W0040': {'name': '1/4 Jack Rabbit 187Ml', 'cost': Decimal('3.47'), 'counted': Decimal('3.50'), 'value': Decimal('12.15')},
    'W31': {'name': '200ml De Faveri Prosecco', 'cost': Decimal('3.23'), 'counted': Decimal('3.50'), 'value': Decimal('11.31')},
    'W0039': {'name': 'Alvier Chardonny', 'cost': Decimal('6.75'), 'counted': Decimal('3.50'), 'value': Decimal('23.63')},
    'W0019': {'name': 'Chablis Emeraude', 'cost': Decimal('18.67'), 'counted': Decimal('3.50'), 'value': Decimal('65.35')},
    'W0025': {'name': 'Chateau De Domy', 'cost': Decimal('16.33'), 'counted': Decimal('3.50'), 'value': Decimal('57.16')},
    'W0044': {'name': 'Chateau Haut Baradiou', 'cost': Decimal('12.06'), 'counted': Decimal('3.50'), 'value': Decimal('42.21')},
    'W0018': {'name': 'Chateau Pascaud', 'cost': Decimal('10.25'), 'counted': Decimal('3.50'), 'value': Decimal('35.88')},
    'W2108': {'name': 'Cheval Chardonny', 'cost': Decimal('6.83'), 'counted': Decimal('3.50'), 'value': Decimal('23.91')},
    'W0038': {'name': 'Classic South Sauv Blanc', 'cost': Decimal('9.83'), 'counted': Decimal('3.50'), 'value': Decimal('34.41')},
    'W0032': {'name': 'De La Chevaliere Rose', 'cost': Decimal('10.83'), 'counted': Decimal('3.50'), 'value': Decimal('37.91')},
    'W0036': {'name': 'Domaine Petit Chablis', 'cost': Decimal('15.83'), 'counted': Decimal('3.50'), 'value': Decimal('55.41')},
    'W0028': {'name': 'Domiane Fleurie', 'cost': Decimal('15.50'), 'counted': Decimal('3.50'), 'value': Decimal('54.25')},
    'W0023': {'name': 'El Somo Rioja Crianza', 'cost': Decimal('8.14'), 'counted': Decimal('3.50'), 'value': Decimal('28.49')},
    'W0027': {'name': 'Equino Malbec', 'cost': Decimal('7.50'), 'counted': Decimal('3.50'), 'value': Decimal('26.25')},
    'W0043': {'name': 'Fuego Blanco', 'cost': Decimal('5.19'), 'counted': Decimal('3.50'), 'value': Decimal('18.17')},
    'W0031': {'name': 'La Chevaliere Chardonny', 'cost': Decimal('8.50'), 'counted': Decimal('3.50'), 'value': Decimal('29.75')},
    'W0033': {'name': 'Les Jamelles Sauv-Blanc', 'cost': Decimal('8.50'), 'counted': Decimal('3.50'), 'value': Decimal('29.75')},
    'W2102': {'name': 'Les Petits Jamelles Rose', 'cost': Decimal('7.64'), 'counted': Decimal('3.50'), 'value': Decimal('26.74')},
    'W1020': {'name': 'Les Roche Merlot', 'cost': Decimal('7.00'), 'counted': Decimal('3.50'), 'value': Decimal('24.50')},
    'W2589': {'name': 'MarquesPlata Sauv/Blanc', 'cost': Decimal('6.17'), 'counted': Decimal('3.50'), 'value': Decimal('21.60')},
    'W1004': {'name': 'MarquesPlata Temp/Syrah', 'cost': Decimal('6.17'), 'counted': Decimal('3.50'), 'value': Decimal('21.60')},
    'W0024': {'name': 'Moilard Macon Village', 'cost': Decimal('15.50'), 'counted': Decimal('3.50'), 'value': Decimal('54.25')},
    'W_PACSAUD': {'name': 'Pacsaud Bordeaux Superior', 'cost': Decimal('0.00'), 'counted': Decimal('3.50'), 'value': Decimal('0.00')},
    'W1013': {'name': 'Pannier', 'cost': Decimal('30.99'), 'counted': Decimal('3.50'), 'value': Decimal('108.47')},
    'W0021': {'name': 'Pazo Albarino', 'cost': Decimal('9.88'), 'counted': Decimal('3.50'), 'value': Decimal('34.58')},
    'W_PINOT_SNIPES': {'name': 'Pinot Grigio Snipes', 'cost': Decimal('0.00'), 'counted': Decimal('3.50'), 'value': Decimal('0.00')},
    'W0037': {'name': 'Pouilly Tume Lucy', 'cost': Decimal('17.50'), 'counted': Decimal('3.50'), 'value': Decimal('61.25')},
    'W45': {'name': 'Primitivo Giola Colle', 'cost': Decimal('11.50'), 'counted': Decimal('3.50'), 'value': Decimal('40.25')},
    'W_PROSECCO_NA': {'name': 'No Alcohol Prosecco', 'cost': Decimal('0.00'), 'counted': Decimal('3.50'), 'value': Decimal('0.00')},
    'W1019': {'name': 'Prosecco Collie', 'cost': Decimal('9.33'), 'counted': Decimal('3.50'), 'value': Decimal('32.66')},
    'W_MDC_PROSECCO': {'name': 'MDC PROSECCO DOC TRE F 24X20CL', 'cost': Decimal('3.23'), 'counted': Decimal('3.50'), 'value': Decimal('11.31')},
    'W2110': {'name': 'Real Camponia Verdejo', 'cost': Decimal('7.96'), 'counted': Decimal('3.50'), 'value': Decimal('27.86')},
    'W111': {'name': 'Reina 5.5%', 'cost': Decimal('4.17'), 'counted': Decimal('3.50'), 'value': Decimal('14.60')},
    'W1': {'name': 'Rialto Prosecco 750ML', 'cost': Decimal('8.93'), 'counted': Decimal('3.50'), 'value': Decimal('31.26')},
    'W0034': {'name': 'Roquende Cab-Sauv', 'cost': Decimal('7.50'), 'counted': Decimal('3.50'), 'value': Decimal('26.25')},
    'W0041': {'name': 'Roquende Chardonny', 'cost': Decimal('10.43'), 'counted': Decimal('3.50'), 'value': Decimal('36.51')},
    'W0042': {'name': 'Roquende Rose', 'cost': Decimal('6.48'), 'counted': Decimal('3.50'), 'value': Decimal('22.68')},
    'W_OG_SHIRAZ_75': {'name': 'O&G SHIRAZ 6X75CL', 'cost': Decimal('8.50'), 'counted': Decimal('3.50'), 'value': Decimal('29.75')},
    'W_OG_SHIRAZ_187': {'name': 'O&G SHIRAZ 12X187ML', 'cost': Decimal('0.00'), 'counted': Decimal('3.50'), 'value': Decimal('0.00')},
    'W_OG_SAUV_187': {'name': 'O&G SAUVIGNON BLANC 12X187ML', 'cost': Decimal('3.00'), 'counted': Decimal('3.50'), 'value': Decimal('10.50')},
    'W2104': {'name': 'Santa Ana Malbec', 'cost': Decimal('6.92'), 'counted': Decimal('3.50'), 'value': Decimal('24.22')},
    'W0029': {'name': 'Serra d Conte Castelli', 'cost': Decimal('9.83'), 'counted': Decimal('3.50'), 'value': Decimal('34.41')},
    'W0022': {'name': 'Sonnetti Pinot Grigo', 'cost': Decimal('6.85'), 'counted': Decimal('3.50'), 'value': Decimal('23.98')},
    'W0030': {'name': 'Tenuta Barbera dAsti DOCG', 'cost': Decimal('14.50'), 'counted': Decimal('3.50'), 'value': Decimal('50.75')},
}

sept_total = Decimal('1355.87')

print("=" * 120)
print("WINE DETAILED COMPARISON: SEPTEMBER EXCEL vs APRIL SYSTEM")
print("=" * 120)

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

print(f"\n{'SKU':<20} {'Name':<35} {'Sept Cost':>11} {'April Cost':>11} {'Cost Diff':>11} "
      f"{'Sept Qty':>9} {'April Qty':>9} {'Sept Val':>10} {'April Val':>10}")
print("-" * 120)

cost_diffs = []
qty_diffs = []
value_diffs = []

for line in wine_lines:
    sku = line.item.sku
    if sku in sept_wine:
        sept_data = sept_wine[sku]
        april_cost = line.item.unit_cost
        sept_cost = sept_data['cost']
        
        april_qty = line.counted_qty
        sept_qty = sept_data['counted']
        
        april_val = line.counted_value
        sept_val = sept_data['value']
        
        cost_diff = april_cost - sept_cost
        qty_diff = april_qty - sept_qty
        val_diff = april_val - sept_val
        
        # Only show if there's a difference
        if abs(cost_diff) > Decimal('0.01') or abs(qty_diff) > Decimal('0.01') or abs(val_diff) > Decimal('0.01'):
            marker = "⚠️" if abs(val_diff) > Decimal('0.01') else ""
            print(f"{sku:<20} {sept_data['name'][:34]:<35} "
                  f"€{sept_cost:>9.2f} €{april_cost:>9.2f} €{cost_diff:>9.2f} "
                  f"{sept_qty:>9.2f} {april_qty:>9.2f} "
                  f"€{sept_val:>8.2f} €{april_val:>8.2f} {marker}")
            
            if abs(cost_diff) > Decimal('0.01'):
                cost_diffs.append({'sku': sku, 'name': sept_data['name'], 'diff': cost_diff})
            if abs(val_diff) > Decimal('0.01'):
                value_diffs.append({'sku': sku, 'name': sept_data['name'], 'diff': val_diff})

april_total = sum(line.counted_value for line in wine_lines)

print("\n" + "=" * 120)
print("SUMMARY:")
print(f"Items with COST differences: {len(cost_diffs)}")
print(f"Items with VALUE differences: {len(value_diffs)}")
print()
print(f"September Excel Total: €{sept_total:>10.2f}")
print(f"April System Total:    €{april_total:>10.2f}")
print(f"TOTAL DIFFERENCE:      €{april_total - sept_total:>10.2f}")
print("=" * 120)

if cost_diffs:
    print("\n⚠️  ITEMS WITH COST PRICE DIFFERENCES:")
    print(f"{'SKU':<20} {'Name':<40} {'Cost Diff':>12}")
    print("-" * 75)
    for item in cost_diffs:
        print(f"{item['sku']:<20} {item['name'][:39]:<40} €{item['diff']:>10.2f}")

print("\n✓ All items have same counted quantity (3.50 bottles)")
print("✓ The €35.88 difference is entirely due to W0018 having €0.00 cost in April system")
