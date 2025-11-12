import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod

print("=" * 100)
print("COMPARING EXCEL OCTOBER CLOSING WITH DATABASE OCTOBER CLOSING")
print("=" * 100)

# Excel October closing data
excel_october = {
    'M2236': {'name': 'Appletisier Apple', 'value': Decimal('0.00')},
    'M0195': {'name': 'Baby SCH Mims', 'value': Decimal('0.00')},
    'M0140': {'name': 'Cordials Miwadi', 'value': Decimal('194.08')},
    'M2107': {'name': 'Fevertree Tonics', 'value': Decimal('43.82')},
    'M0320': {'name': 'Grenadine Syrup', 'value': Decimal('18.48')},
    'M11': {'name': 'Kulana Litre Juices', 'value': Decimal('117.00')},
    'M0042': {'name': 'Lemonade Red Nashs', 'value': Decimal('40.50')},
    'M0210': {'name': 'Lemonade WhiteNashes', 'value': Decimal('52.20')},
    'M0008': {'name': 'Mixer Lemon Juice 700ML', 'value': Decimal('105.84')},
    'M0009': {'name': 'Mixer Lime Juice 700ML', 'value': Decimal('70.56')},
    'M3': {'name': 'Monin Agave Syrup 700ml', 'value': Decimal('26.95')},
    'M0006': {'name': 'Monin Chocolate Cookie LTR', 'value': Decimal('20.53')},
    'M13': {'name': 'Monin Coconut Syrup 700ML', 'value': Decimal('143.66')},
    'M04': {'name': 'Monin Elderflower Syrup 700M', 'value': Decimal('46.71')},
    'M0014': {'name': 'Monin Ginger Syrup', 'value': Decimal('86.10')},
    'M2': {'name': 'Monin Passionfruit Puree Ltr', 'value': Decimal('99.91')},
    'M03': {'name': 'Monin Passionfruit Syrup 700M70cl', 'value': Decimal('122.61')},
    'M05': {'name': 'Monin Pink Grapefruit 700ML', 'value': Decimal('55.35')},
    'M06': {'name': 'Monin Puree Coconut LTR', 'value': Decimal('0.00')},
    'M1': {'name': 'Monin Strawberry Puree Ltr', 'value': Decimal('121.30')},
    'M01': {'name': 'Monin Strawberry Syrup 700ml', 'value': Decimal('61.86')},
    'M5': {'name': 'Monin Strawberry Syrup Ltr', 'value': Decimal('0.00')},
    'M9': {'name': 'Monin Vanilla Syrup Ltr', 'value': Decimal('26.49')},
    'M02': {'name': 'Monin Watermelon Syrup 700M', 'value': Decimal('45.65')},
    'M0170': {'name': 'Red Bull Cans', 'value': Decimal('59.36')},
    'M0123': {'name': 'Riverrock 750ml', 'value': Decimal('56.44')},
    'M0180': {'name': 'RiverRock Spark/Still', 'value': Decimal('167.49')},
    'M25': {'name': 'Splash Cola 18LTR', 'value': Decimal('171.50')},
    'M24': {'name': 'Splash Energy18LTR', 'value': Decimal('0.00')},
    'M23': {'name': 'Splash White18LTR', 'value': Decimal('173.06')},
    'M0050': {'name': 'Split 7up', 'value': Decimal('152.40')},
    'M0003': {'name': 'Split 7UP Diet', 'value': Decimal('0.00')},
    'M0040': {'name': 'Split Coke', 'value': Decimal('5.83')},
    'M0013': {'name': 'Split Coke 330ML', 'value': Decimal('0.00')},
    'M2105': {'name': 'Split Coke Diet', 'value': Decimal('105.05')},
    'M0004': {'name': 'Split Fanta Lemon', 'value': Decimal('55.58')},
    'M0034': {'name': 'Split Fanta Orange', 'value': Decimal('40.73')},
    'M0070': {'name': 'Split Friuce Juices', 'value': Decimal('0.00')},
    'M0135': {'name': 'Split Lucozade', 'value': Decimal('27.87')},
    'M0315': {'name': 'Split Pepsi', 'value': Decimal('37.83')},
    'M0016': {'name': 'Split Poachers Ginger Beer', 'value': Decimal('25.60')},
    'M0255': {'name': 'Split Sch', 'value': Decimal('272.33')},
    'M0122': {'name': 'Split Sch Elderflower', 'value': Decimal('0.54')},
    'M0200': {'name': 'Split Sprite/Zero', 'value': Decimal('82.60')},
    'M0312': {'name': 'Splits Britvic Juices', 'value': Decimal('111.30')},
    'M0012': {'name': 'Teisseire Bubble Gum', 'value': Decimal('17.34')},
    'M0011': {'name': 'Three Cents Pink Grapefruit', 'value': Decimal('0.00')},
}

excel_total = sum(item['value'] for item in excel_october.values())
print(f"\n📊 Excel October Total: €{excel_total:.2f}")

# Get database October snapshots
october_period = StockPeriod.objects.get(hotel_id=2, start_date='2025-10-01')
db_snapshots = StockSnapshot.objects.filter(
    period=october_period,
    item__category__code='M'
).select_related('item')

db_dict = {snap.item.sku: snap for snap in db_snapshots}
db_total = sum(snap.closing_stock_value for snap in db_snapshots)
print(f"💾 Database October Total: €{db_total:.2f}")
print(f"❌ Difference: €{db_total - excel_total:.2f}")

print("\n" + "=" * 100)
print("ITEM-BY-ITEM COMPARISON:")
print("-" * 100)
print(f"{'SKU':<10} {'Name':<30} {'Excel':<15} {'Database':<15} {'Diff':<15} {'Status'}")
print("-" * 100)

mismatches = []
for sku, excel_data in excel_october.items():
    excel_val = excel_data['value']
    db_snap = db_dict.get(sku)
    
    if db_snap:
        db_val = db_snap.closing_stock_value
    else:
        db_val = Decimal('0.00')
        print(f"{sku:<10} {excel_data['name'][:30]:<30} €{excel_val:<14.2f} MISSING!        €{excel_val:<14.2f} ❌")
        mismatches.append(sku)
        continue
    
    diff = db_val - excel_val
    match = abs(diff) < Decimal('0.02')
    status = "✅" if match else "❌"
    
    if not match:
        mismatches.append(sku)
    
    print(f"{sku:<10} {excel_data['name'][:30]:<30} €{excel_val:<14.2f} €{db_val:<14.2f} €{diff:<14.2f} {status}")

print("-" * 100)
print(f"{'TOTAL':<10} {'':<30} €{excel_total:<14.2f} €{db_total:<14.2f} €{db_total - excel_total:<14.2f}")
print("=" * 100)

print(f"\n📊 SUMMARY:")
print(f"  Total items in Excel: {len(excel_october)}")
print(f"  Total items in DB: {len(db_dict)}")
print(f"  Mismatches: {len(mismatches)}")
print(f"  Match rate: {((len(excel_october) - len(mismatches)) / len(excel_october) * 100):.1f}%")

if mismatches:
    print(f"\n❌ Items with differences:")
    for sku in mismatches[:10]:  # Show first 10
        excel_val = excel_october[sku]['value']
        db_snap = db_dict.get(sku)
        db_val = db_snap.closing_stock_value if db_snap else Decimal('0')
        print(f"  {sku}: Excel €{excel_val:.2f} vs DB €{db_val:.2f} (diff: €{db_val - excel_val:.2f})")
else:
    print("\n✅ All items match!")

print("\n" + "=" * 100)
