import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

# Excel data with expected costs
excel_data = {
    'M2236': {'name': 'Appletisier Apple', 'cost': Decimal('12.95')},
    'M0195': {'name': 'Baby SCH Mims', 'cost': Decimal('5.13')},
    'M0140': {'name': 'Cordials  Miwadi', 'cost': Decimal('17.00')},
    'M2107': {'name': 'Fevertree Tonics', 'cost': Decimal('12.52')},
    'M0320': {'name': 'Grenadine Syrup', 'cost': Decimal('6.16')},
    'M11': {'name': 'Kulana Litre Juices', 'cost': Decimal('1.00')},
    'M0042': {'name': 'Lemonade Red Nashs', 'cost': Decimal('12.15')},
    'M0210': {'name': 'Lemonade WhiteNashes', 'cost': Decimal('13.05')},
    'M0008': {'name': 'Mixer Lemon Juice 700ML', 'cost': Decimal('5.88')},
    'M0009': {'name': 'Mixer Lime Juice 700ML', 'cost': Decimal('5.88')},
    'M3': {'name': 'Monin Agave Syrup 700ml', 'cost': Decimal('9.98')},
    'M0006': {'name': 'Monin Chocolate Cookie LTR', 'cost': Decimal('9.33')},
    'M13': {'name': 'Monin Coconut Syrup 700ML', 'cost': Decimal('9.15')},
    'M04': {'name': 'Monin Elderflower Syrup 700M', 'cost': Decimal('10.38')},
    'M0014': {'name': 'Monin Ginger Syrup', 'cost': Decimal('10.25')},
    'M2': {'name': 'Monin Passionfruit Puree Ltr', 'cost': Decimal('15.37')},
    'M03': {'name': 'Monin Passionfruit Syrup 700M', 'cost': Decimal('9.15')},
    'M05': {'name': 'Monin Pink Grapefruit 700ML', 'cost': Decimal('10.25')},
    'M06': {'name': 'Monin Puree Coconut LTR', 'cost': Decimal('14.64')},
    'M1': {'name': 'Monin Strawberry Puree Ltr', 'cost': Decimal('12.13')},
    'M01': {'name': 'Monin Strawberry Syrup 700ml', 'cost': Decimal('10.31')},
    'M5': {'name': 'Monin Strawberry Syrup Ltr', 'cost': Decimal('10.31')},
    'M9': {'name': 'Monin Vanilla Syrup Ltr', 'cost': Decimal('8.83')},
    'M02': {'name': 'Monin Watermelon Syrup 700M', 'cost': Decimal('8.95')},
    'M0170': {'name': 'Red Bull Cans', 'cost': Decimal('11.13')},
    'M0123': {'name': 'Riverrock 750ml', 'cost': Decimal('19.35')},
    'M0180': {'name': 'RiverRock Spark/Still', 'cost': Decimal('5.18')},
    'M25': {'name': 'Splash Cola 18LTR', 'cost': Decimal('171.16')},
    'M24': {'name': 'Splash Energy18LTR', 'cost': Decimal('182.64')},
    'M23': {'name': 'Splash White18LTR', 'cost': Decimal('173.06')},
    'M0050': {'name': 'Split 7up', 'cost': Decimal('6.35')},
    'M0003': {'name': 'Split 7UP Diet', 'cost': Decimal('6.35')},
    'M0040': {'name': 'Split Coke', 'cost': Decimal('7.00')},
    'M0013': {'name': 'Split Coke 330ML', 'cost': Decimal('14.52')},
    'M2105': {'name': 'Split Coke Diet', 'cost': Decimal('6.60')},
    'M0004': {'name': 'Split Fanta Lemon', 'cost': Decimal('5.75')},
    'M0034': {'name': 'Split Fanta Orange', 'cost': Decimal('5.75')},
    'M0070': {'name': 'Split Friuce Juices', 'cost': Decimal('7.16')},
    'M0135': {'name': 'Split Lucozade', 'cost': Decimal('8.80')},
    'M0315': {'name': 'Split Pepsi', 'cost': Decimal('5.10')},
    'M0016': {'name': 'Split Poachers Ginger Beer', 'cost': Decimal('10.24')},
    'M0255': {'name': 'Split Sch', 'cost': Decimal('6.88')},
    'M0122': {'name': 'Split Sch Elderflower', 'cost': Decimal('6.50')},
    'M0200': {'name': 'Split Sprite/Zero', 'cost': Decimal('5.60')},
    'M0312': {'name': 'Splits Britvic Juices', 'cost': Decimal('8.40')},
    'M0012': {'name': 'Teisseire Bubble Gum', 'cost': Decimal('8.67')},
    'M0011': {'name': 'Three Cents Pink Grapefruit', 'cost': Decimal('0.00')},
}

print("=" * 100)
print("COMPARING MINERALS ITEMS - SYSTEM vs EXCEL")
print("=" * 100)

print(f"\nExcel has {len(excel_data)} items")

# Check system items
system_items = StockItem.objects.filter(
    category__code='M',
    sku__in=excel_data.keys()
).values_list('sku', 'unit_cost')

system_dict = {sku: cost for sku, cost in system_items}

print(f"System has {len(system_dict)} matching items")

# Find differences
differences = []
missing_in_system = []

for sku, excel_info in excel_data.items():
    if sku not in system_dict:
        missing_in_system.append(sku)
    elif system_dict[sku] != excel_info['cost']:
        differences.append({
            'sku': sku,
            'name': excel_info['name'],
            'excel_cost': excel_info['cost'],
            'system_cost': system_dict[sku],
            'diff': system_dict[sku] - excel_info['cost']
        })

if differences:
    print(f"\n⚠️  {len(differences)} items have DIFFERENT costs:")
    print(f"{'SKU':<15} {'Name':<35} {'Excel':>10} {'System':>10} {'Diff':>10}")
    print("-" * 85)
    for item in differences:
        print(f"{item['sku']:<15} {item['name'][:35]:<35} "
              f"€{item['excel_cost']:>8.2f} €{item['system_cost']:>8.2f} "
              f"€{item['diff']:>8.2f}")

if missing_in_system:
    print(f"\n⚠️  {len(missing_in_system)} items in Excel NOT in system:")
    for sku in missing_in_system:
        print(f"  {sku} - {excel_data[sku]['name']}")

# Now check if system has items NOT in Excel
all_system_minerals = StockItem.objects.filter(
    category__code='M'
).values_list('sku', flat=True)

extra_in_system = [sku for sku in all_system_minerals if sku not in excel_data]

if extra_in_system:
    print(f"\n⚠️  {len(extra_in_system)} items in System NOT in Excel:")
    for sku in extra_in_system:
        item = StockItem.objects.get(sku=sku)
        print(f"  {sku} - {item.name}")

print("\n" + "=" * 100)
