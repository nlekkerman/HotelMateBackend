import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockSnapshot

print("=" * 100)
print("FIXING SEPTEMBER COUNTED QTY - SMART UPDATE")
print("=" * 100)

sept_stocktake = Stocktake.objects.get(hotel_id=2, period_start='2025-09-01')
print(f"\n✅ September Stocktake: ID={sept_stocktake.id}")

sept_snapshots = StockSnapshot.objects.filter(
    period__hotel_id=2,
    period__start_date='2025-09-01',
    item__category__code='M'
).select_related('item', 'item__category')

print(f"✅ Found {sept_snapshots.count()} snapshots\n")

print("=" * 100)
print("ANALYZING ITEM TYPES AND UPDATING:")
print("-" * 100)

updated = 0
errors = []

for snap in sept_snapshots:
    try:
        line = StocktakeLine.objects.get(
            stocktake=sept_stocktake,
            item__sku=snap.item.sku
        )
        
        item = snap.item
        size_upper = (item.size or '').upper()
        
        # Determine item type
        is_liter = 'LT' in size_upper and 'ML' not in size_upper
        is_dozen = 'DOZ' in size_upper
        
        # For BIB/Dozen: partial already in servings
        # For Individual: partial in bottles (need to divide by UOM)
        if is_dozen or is_liter:
            # Partial = servings directly
            correct_full = snap.closing_full_units
            correct_partial = snap.closing_partial_units
            item_type = "Doz/BIB"
        else:
            # Partial = bottles (total_servings / UOM)
            total_servings = snap.total_servings
            correct_full = 0
            correct_partial = total_servings / item.uom if item.uom > 0 else Decimal('0')
            item_type = "Individual"
        
        # Update
        line.counted_full_units = correct_full
        line.counted_partial_units = correct_partial
        line.save()
        
        # Verify
        calc_servings = line.counted_qty
        expected_servings = snap.total_servings
        match = abs(calc_servings - expected_servings) < Decimal('0.01')
        
        status = "✅" if match else "❌"
        print(f"{status} {item.sku:<10} {item.name[:25]:<25} {item_type:<12} "
              f"F={correct_full:<6.2f} P={correct_partial:<8.2f} "
              f"Calc={float(calc_servings):<8.2f} Expected={float(expected_servings):<8.2f}")
        
        if not match:
            errors.append(item.sku)
        
        updated += 1
        
    except Exception as e:
        print(f"❌ {snap.item.sku}: Error - {str(e)}")

print("-" * 100)
print(f"Updated: {updated} lines")
if errors:
    print(f"❌ Errors: {', '.join(errors)}")

# Final verification
print("\n" + "=" * 100)
print("FINAL VERIFICATION:")
print("=" * 100)

sept_lines = StocktakeLine.objects.filter(
    stocktake=sept_stocktake,
    item__category__code='M'
).select_related('item')

total = Decimal('0')
for line in sept_lines:
    total += line.counted_qty * line.item.cost_per_serving

print(f"\nSeptember Minerals Counted Total: €{total:,.2f}")
print(f"Expected (from Excel): €4,185.64")
print(f"Difference: €{abs(total - Decimal('4185.64')):,.2f}")

if abs(total - Decimal('4185.64')) < Decimal('1.00'):
    print("\n✅ SUCCESS!")
else:
    print("\n❌ Still incorrect")

print("=" * 100)
