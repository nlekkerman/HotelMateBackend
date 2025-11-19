import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine

# Excel data: code -> cost_price mapping
excel_data = {
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
    'S2217': Decimal('33.34'),
    'S0001': Decimal('33.83'),
    'S0610': Decimal('21.83'),
    'S0625': Decimal('13.75'),
    'S0010': Decimal('53.03'),
    'S0638': Decimal('22.83'),
    'S0638_00': Decimal('15.00'),  # Tanquery 0.0%
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
    'S_SEADOG': Decimal('17.13'),  # Sea Dog Rum
    'S_DINGLE_WHISKEY': Decimal('37.50'),  # Dingle Whiskey
}

excel_total = Decimal('11229.89')
excel_count = 129

print("=" * 80)
print("SPIRITS COMPARISON: SYSTEM vs EXCEL")
print("=" * 80)

# Get April 2025 stocktake
from hotel.models import Hotel
hotel = Hotel.objects.first()

stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).first()

if not stocktake:
    print("❌ No April 2025 stocktake found!")
    exit()

print(f"\nStocktake: {stocktake.period_start.strftime('%B %Y')}")
print(f"Status: {stocktake.status}")

# Get all Spirits stocktake lines
spirits_lines = StocktakeLine.objects.filter(
    stocktake=stocktake,
    item__category__code='S'
).select_related('item', 'item__category')

system_count = spirits_lines.count()
system_total = sum(line.counted_value for line in spirits_lines)

print(f"\n{'SUMMARY':-^80}")
print(f"Excel Items:  {excel_count}")
print(f"System Items: {system_count}")
print(f"Difference:   {system_count - excel_count:+d}")
print()
print(f"Excel Total:  €{excel_total:,.2f}")
print(f"System Total: €{system_total:,.2f}")
print(f"Difference:   €{system_total - excel_total:+,.2f}")

# Compare individual items
print(f"\n{'INDIVIDUAL ITEM COMPARISON':-^80}")
print(f"{'Code':<15} {'Name':<30} {'Excel €':<10} {'System €':<10} {'Diff €':<10}")
print("-" * 80)

system_codes = set()
price_mismatches = []
perfect_matches = 0
matched_items = 0

for line in spirits_lines.order_by('item__sku'):
    code = line.item.sku
    system_codes.add(code)
    
    if code in excel_data:
        matched_items += 1
        excel_price = excel_data[code]
        # System price is the unit_cost from StockItem
        system_price = line.item.unit_cost
        excel_expected_value = excel_price * Decimal('3.50')
        
        diff = line.counted_value - excel_expected_value
        
        if abs(diff) < Decimal('0.02'):  # Within 2 cents (rounding)
            perfect_matches += 1
        else:
            price_mismatches.append({
                'code': code,
                'name': line.item.name[:30],
                'excel_price': excel_price,
                'system_price': system_price,
                'excel_value': excel_expected_value,
                'system_value': line.counted_value,
                'diff': diff
            })
            print(f"{code:<15} {line.item.name[:30]:<30} "
                  f"€{excel_expected_value:>8.2f} €{line.counted_value:>8.2f} "
                  f"€{diff:>+8.2f}")

# Check for items in Excel but not in system
excel_codes = set(excel_data.keys())
missing_in_system = excel_codes - system_codes

print(f"\nExcel has {len(excel_codes)} unique codes")
print(f"System has {len(system_codes)} unique codes")
print(f"Missing from system: {len(missing_in_system)}")

if missing_in_system:
    print(f"\n{'ITEMS IN EXCEL BUT NOT IN SYSTEM':-^80}")
    for code in sorted(missing_in_system):
        unit_cost = excel_data[code]
        expected_value = unit_cost * Decimal('3.50')
        print(f"❌ {code:<15} Unit Cost: €{unit_cost:>8.2f}  "
              f"Expected Value (3.5 btls): €{expected_value:>8.2f}")
else:
    print("\n✓ All Excel items found in system")

# Check for items in system but not in Excel
extra_in_system = system_codes - excel_codes

if extra_in_system:
    print(f"\n{'ITEMS IN SYSTEM BUT NOT IN EXCEL':-^80}")
    for code in sorted(extra_in_system):
        line = spirits_lines.get(item__sku=code)
        print(f"{code:<15} {line.item.name[:30]:<30} €{line.counted_value:>8.2f}")

print(f"\n{'ANALYSIS':-^80}")
print(f"Matched items:                    {matched_items}")
print(f"Perfect matches (within 2 cents): {perfect_matches}")
print(f"Price mismatches:                 {len(price_mismatches)}")
print(f"Missing in system:                {len(missing_in_system)}")
print(f"Extra in system:                  {len(extra_in_system)}")

if price_mismatches:
    print(f"\n{'TOP PRICE MISMATCHES':-^80}")
    sorted_mismatches = sorted(price_mismatches, key=lambda x: abs(x['diff']), reverse=True)[:10]
    for m in sorted_mismatches:
        print(f"{m['code']:<15} {m['name']:<30}")
        print(f"  Excel unit cost: €{m['excel_price']:>8.2f}  System unit cost: €{m['system_price']:>8.2f}")
        print(f"  Excel value:     €{m['excel_value']:>8.2f}  System value:     €{m['system_value']:>8.2f}")
        print(f"  Difference:      €{m['diff']:>+8.2f}")
        print()

print("\n" + "=" * 80)
