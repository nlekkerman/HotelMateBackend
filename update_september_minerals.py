import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod, StockItem

print("=" * 100)
print("UPDATING SEPTEMBER MINERALS/SYRUPS SNAPSHOTS WITH CORRECT VALUES")
print("=" * 100)

# Get September period
september_period = StockPeriod.objects.get(
    hotel_id=2,
    start_date='2025-09-01',
    end_date='2025-09-30'
)
print(f"\n✅ Found September period: {september_period.period_name}")

# Correct September closing values from Excel (in bottles/servings)
# Format: 'SKU': (closing_qty_in_servings, closing_value)
correct_september_values = {
    'M2236': (0, Decimal('0.00')),
    'M0195': (0, Decimal('0.00')),
    'M0140': (90, Decimal('127.50')),
    'M2107': (103, Decimal('107.46')),
    'M0320': (150.37, Decimal('46.99')),  # 7.60 cases * 19.7 + 0.55 = 150.37 servings
    'M11': (138, Decimal('138.00')),
    'M0042': (43, Decimal('43.54')),
    'M0210': (43, Decimal('46.76')),
    'M0008': (0, Decimal('0.00')),
    'M0009': (0, Decimal('0.00')),
    'M3': (3.30, Decimal('32.93')),
    'M0006': (3.00, Decimal('27.99')),
    'M13': (0.40, Decimal('3.66')),
    'M04': (2.40, Decimal('24.91')),
    'M0014': (10.70, Decimal('109.68')),
    'M2': (11.40, Decimal('175.22')),
    'M03': (275.80, Decimal('128.10')),  # 14.00 * 19.7 = 275.80 servings
    'M05': (7.30, Decimal('74.83')),
    'M06': (17.00, Decimal('248.88')),
    'M1': (6.50, Decimal('78.85')),
    'M01': (3.00, Decimal('30.93')),
    'M5': (2.50, Decimal('25.78')),
    'M9': (3.00, Decimal('26.49')),
    'M02': (6.00, Decimal('53.70')),
    'M0170': (6, Decimal('5.57')),
    'M0123': (580, Decimal('935.25')),
    'M0180': (10, Decimal('4.32')),
    'M25': (500.00 + 1.00, Decimal('171.50')),  # 1 case + 1 bottle
    'M24': (0, Decimal('0.00')),
    'M23': (500.00, Decimal('173.06')),  # 1 case
    'M0050': (56, Decimal('29.63')),
    'M0003': (0, Decimal('0.00')),
    'M0040': (279, Decimal('162.75')),
    'M0013': (0, Decimal('0.00')),
    'M2105': (301, Decimal('165.55')),
    'M0004': (169, Decimal('80.98')),
    'M0034': (78, Decimal('37.38')),
    'M0070': (52, Decimal('31.03')),
    'M0135': (151, Decimal('110.73')),
    'M0315': (294, Decimal('124.95')),
    'M0016': (14, Decimal('11.95')),
    'M0255': (384, Decimal('220.16')),
    'M0122': (27, Decimal('14.63')),
    'M0200': (536, Decimal('250.13')),
    'M0312': (136, Decimal('95.20')),
    'M0012': (1, Decimal('8.67')),
    'M0011': (0, Decimal('0.00')),
}

print(f"\n📊 Excel September Total: €{sum(v[1] for v in correct_september_values.values()):.2f}")

# Get current September snapshots
current_snapshots = StockSnapshot.objects.filter(
    period=september_period,
    item__category__code='M'
).select_related('item')

current_total = sum(s.closing_stock_value for s in current_snapshots)
print(f"💾 Current Database Total: €{current_total:.2f}")

print("\n" + "=" * 100)
print("UPDATING SNAPSHOTS:")
print("-" * 100)

updated_count = 0
missing_items = []
errors = []

for sku, (correct_qty, correct_value) in correct_september_values.items():
    try:
        # Find the item
        item = StockItem.objects.get(hotel_id=2, sku=sku)
        
        # Find or get the snapshot
        snapshot, created = StockSnapshot.objects.get_or_create(
            period=september_period,
            item=item,
            hotel_id=2,
            defaults={
                'closing_full_units': 0,
                'closing_partial_units': correct_qty,
                'unit_cost': item.unit_cost,
                'cost_per_serving': item.cost_per_serving,
                'closing_stock_value': correct_value
            }
        )
        
        if not created:
            # Update existing snapshot
            old_value = snapshot.closing_stock_value
            snapshot.closing_full_units = 0  # Reset to 0, all qty in partial
            snapshot.closing_partial_units = correct_qty
            snapshot.closing_stock_value = correct_value
            snapshot.unit_cost = item.unit_cost
            snapshot.cost_per_serving = item.cost_per_serving
            snapshot.save()
            
            print(f"✅ {sku:<10} {item.name[:30]:<30} €{old_value:<10.2f} → €{correct_value:<10.2f}")
        else:
            print(f"➕ {sku:<10} {item.name[:30]:<30} CREATED with €{correct_value:.2f}")
        
        updated_count += 1
        
    except StockItem.DoesNotExist:
        missing_items.append(sku)
        print(f"❌ {sku:<10} Item not found in database")
    except Exception as e:
        errors.append((sku, str(e)))
        print(f"❌ {sku:<10} Error: {str(e)}")

print("-" * 100)
print(f"Updated: {updated_count} items")

if missing_items:
    print(f"\n⚠️ Missing items in database: {', '.join(missing_items)}")

if errors:
    print(f"\n❌ Errors encountered:")
    for sku, error in errors:
        print(f"  {sku}: {error}")

# Verify new total
new_snapshots = StockSnapshot.objects.filter(
    period=september_period,
    item__category__code='M'
)
new_total = sum(s.closing_stock_value for s in new_snapshots)

print("\n" + "=" * 100)
print("VERIFICATION:")
print("-" * 100)
print(f"Excel Target:     €{sum(v[1] for v in correct_september_values.values()):.2f}")
print(f"Old Database:     €{current_total:.2f}")
print(f"New Database:     €{new_total:.2f}")
print(f"Difference:       €{new_total - sum(v[1] for v in correct_september_values.values()):.2f}")

if abs(new_total - Decimal('4185.61')) < Decimal('0.50'):
    print("\n✅ SUCCESS! September Minerals/Syrups snapshots updated correctly!")
else:
    print(f"\n⚠️ WARNING: Total doesn't match exactly. Expected €4,185.61, got €{new_total:.2f}")

print("=" * 100)
