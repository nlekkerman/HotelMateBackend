import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockSnapshot, StockPeriod

print("=" * 100)
print("EXAMINING MINERALS/SYRUPS CATEGORY (M)")
print("=" * 100)

# Get periods
october_period = StockPeriod.objects.get(hotel_id=2, start_date='2025-10-01')
september_period = StockPeriod.objects.get(hotel_id=2, start_date='2025-09-01')

# Get all Minerals items
minerals_items = StockItem.objects.filter(
    hotel_id=2,
    category__code='M'
).order_by('sku')

print(f"\n📦 Found {minerals_items.count()} items in Minerals/Syrups category")
print("\n" + "=" * 100)
print("ITEM DETAILS:")
print("-" * 100)
print(f"{'SKU':<10} {'Name':<30} {'Size':<10} {'UOM':<10} {'Serv/Unit':<12} {'Cost/Serv':<12}")
print("-" * 100)

for item in minerals_items:
    print(f"{item.sku:<10} {item.name[:30]:<30} {item.size:<10} {item.uom:<10} "
          f"{float(item.uom):<12.2f} €{float(item.cost_per_serving):<11.4f}")

print("-" * 100)

# Check snapshots for September
print("\n" + "=" * 100)
print("SEPTEMBER SNAPSHOTS:")
print("-" * 100)
print(f"{'SKU':<10} {'Name':<30} {'Closing Qty':<15} {'Value':<12}")
print("-" * 100)

sept_snapshots = StockSnapshot.objects.filter(
    period=september_period,
    item__category__code='M'
).select_related('item')

sept_total = Decimal('0')
for snap in sept_snapshots:
    print(f"{snap.item.sku:<10} {snap.item.name[:30]:<30} "
          f"{snap.closing_partial_units:<15.4f} €{snap.closing_stock_value:<11.2f}")
    sept_total += snap.closing_stock_value

print("-" * 100)
print(f"{'TOTAL':<10} {'':<30} {'':<15} €{sept_total:<11.2f}")
print("-" * 100)

# Check snapshots for October
print("\n" + "=" * 100)
print("OCTOBER SNAPSHOTS:")
print("-" * 100)
print(f"{'SKU':<10} {'Name':<30} {'Closing Qty':<15} {'Value':<12}")
print("-" * 100)

oct_snapshots = StockSnapshot.objects.filter(
    period=october_period,
    item__category__code='M'
).select_related('item')

oct_total = Decimal('0')
for snap in oct_snapshots:
    print(f"{snap.item.sku:<10} {snap.item.name[:30]:<30} "
          f"{snap.closing_partial_units:<15.4f} €{snap.closing_stock_value:<11.2f}")
    oct_total += snap.closing_stock_value

print("-" * 100)
print(f"{'TOTAL':<10} {'':<30} {'':<15} €{oct_total:<11.2f}")
print("-" * 100)

# Compare side by side
print("\n" + "=" * 100)
print("SIDE-BY-SIDE COMPARISON:")
print("-" * 100)
print(f"{'SKU':<10} {'Name':<30} {'Sept Value':<15} {'Oct Value':<15} {'Change':<15}")
print("-" * 100)

# Create dict for easy lookup
sept_dict = {s.item.sku: s for s in sept_snapshots}
oct_dict = {s.item.sku: s for s in oct_snapshots}

all_skus = set(sept_dict.keys()) | set(oct_dict.keys())

for sku in sorted(all_skus):
    sept_snap = sept_dict.get(sku)
    oct_snap = oct_dict.get(sku)
    
    sept_val = sept_snap.closing_stock_value if sept_snap else Decimal('0')
    oct_val = oct_snap.closing_stock_value if oct_snap else Decimal('0')
    change = oct_val - sept_val
    
    name = sept_snap.item.name if sept_snap else oct_snap.item.name
    
    status = "=" if abs(change) < 0.01 else ("↑" if change > 0 else "↓")
    
    print(f"{sku:<10} {name[:30]:<30} €{sept_val:<14.2f} €{oct_val:<14.2f} €{change:<14.2f} {status}")

print("-" * 100)
print(f"{'TOTAL':<10} {'':<30} €{sept_total:<14.2f} €{oct_total:<14.2f} €{oct_total - sept_total:<14.2f}")
print("=" * 100)

# Check for unusual UOM or servings
print("\n" + "=" * 100)
print("CHECKING FOR UNUSUAL CONFIGURATIONS:")
print("-" * 100)

unusual = []
for item in minerals_items:
    issues = []
    
    # Check if UOM is unusual
    if item.uom > 100:
        issues.append(f"Large UOM: {item.uom}")
    
    # Check if servings per unit is unusual
    if item.servings_per_unit > 100:
        issues.append(f"Large servings: {item.servings_per_unit}")
    
    # Check if cost per serving is very small
    if item.cost_per_serving < Decimal('0.01'):
        issues.append(f"Tiny cost/serving: €{item.cost_per_serving}")
    
    # Check if cost per serving is very large
    if item.cost_per_serving > Decimal('10.00'):
        issues.append(f"Large cost/serving: €{item.cost_per_serving}")
    
    if issues:
        unusual.append({
            'item': item,
            'issues': issues
        })

if unusual:
    print(f"\n⚠️ Found {len(unusual)} items with unusual configurations:")
    for u in unusual:
        print(f"\n{u['item'].sku} - {u['item'].name}")
        print(f"  Size: {u['item'].size}, UOM: {u['item'].uom}, Servings/Unit: {u['item'].servings_per_unit}")
        print(f"  Cost/Unit: €{u['item'].unit_cost}, Cost/Serving: €{u['item'].cost_per_serving}")
        for issue in u['issues']:
            print(f"  ⚠️ {issue}")
else:
    print("\n✅ No unusual configurations found")

print("\n" + "=" * 100)
print("SUMMARY:")
print("-" * 100)
print(f"Excel September: €4,185.61")
print(f"DB September:    €{sept_total:.2f}")
print(f"Difference:      €{Decimal('4185.61') - sept_total:.2f}")
print()
print(f"Excel October:   €3,062.43")
print(f"DB October:      €{oct_total:.2f}")
print(f"Difference:      €{Decimal('3062.43') - oct_total:.2f}")
print("=" * 100)
