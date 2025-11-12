import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod, Stocktake, StocktakeLine

print("=" * 100)
print("UPDATING OCTOBER OPENING WITH SEPTEMBER CLOSING")
print("=" * 100)

# Get periods
september_period = StockPeriod.objects.get(hotel_id=2, start_date='2025-09-01')
october_period = StockPeriod.objects.get(hotel_id=2, start_date='2025-10-01')

print(f"\n✅ September period: {september_period.period_name}")
print(f"✅ October period: {october_period.period_name}")

# Get September snapshots (closing stock)
sept_snapshots = StockSnapshot.objects.filter(
    period=september_period,
    item__category__code='M'
).select_related('item')

print(f"\n📦 Found {sept_snapshots.count()} September snapshots for Minerals")

# Get October stocktake
try:
    october_stocktake = Stocktake.objects.get(
        hotel_id=2,
        period_start='2025-10-01',
        period_end='2025-10-31'
    )
    print(f"✅ October stocktake found: ID={october_stocktake.id}, Status={october_stocktake.status}")
except Stocktake.DoesNotExist:
    print("❌ October stocktake NOT FOUND")
    exit(1)

print("\n" + "=" * 100)
print("UPDATING OCTOBER OPENING BALANCES:")
print("-" * 100)
print(f"{'SKU':<10} {'Name':<30} {'Sept Close':<15} {'Oct Open OLD':<15} {'Oct Open NEW':<15}")
print("-" * 100)

updated_count = 0
errors = []

for sept_snap in sept_snapshots:
    try:
        # Get the October stocktake line for this item
        oct_line = StocktakeLine.objects.get(
            stocktake=october_stocktake,
            item=sept_snap.item
        )
        
        old_opening = oct_line.opening_qty
        new_opening = sept_snap.closing_partial_units
        
        # Update opening qty
        oct_line.opening_qty = new_opening
        oct_line.save()
        
        print(f"{sept_snap.item.sku:<10} {sept_snap.item.name[:30]:<30} "
              f"{sept_snap.closing_partial_units:<15.2f} "
              f"{old_opening:<15.2f} "
              f"{new_opening:<15.2f}")
        
        updated_count += 1
        
    except StocktakeLine.DoesNotExist:
        errors.append(f"{sept_snap.item.sku}: No October stocktake line found")
    except Exception as e:
        errors.append(f"{sept_snap.item.sku}: {str(e)}")

print("-" * 100)
print(f"Updated: {updated_count} lines")

if errors:
    print(f"\n❌ Errors: {len(errors)}")
    for error in errors[:5]:
        print(f"  {error}")

print("\n" + "=" * 100)
print("VERIFICATION - COMPARING SEPTEMBER CLOSING VS OCTOBER OPENING:")
print("-" * 100)
print(f"{'SKU':<10} {'Name':<30} {'Sept Closing':<15} {'Oct Opening':<15} {'Match':<10}")
print("-" * 100)

match_count = 0
mismatch_count = 0

for sept_snap in sept_snapshots:
    try:
        oct_line = StocktakeLine.objects.get(
            stocktake=october_stocktake,
            item=sept_snap.item
        )
        
        sept_close = float(sept_snap.closing_partial_units)
        oct_open = float(oct_line.opening_qty)
        
        match = abs(sept_close - oct_open) < 0.01
        status = "✅" if match else "❌"
        
        if match:
            match_count += 1
        else:
            mismatch_count += 1
            print(f"{sept_snap.item.sku:<10} {sept_snap.item.name[:30]:<30} "
                  f"{sept_close:<15.2f} {oct_open:<15.2f} {status}")
        
    except StocktakeLine.DoesNotExist:
        pass

print("-" * 100)
print(f"Matches: {match_count}")
print(f"Mismatches: {mismatch_count}")

if mismatch_count == 0:
    print("\n✅ SUCCESS! All October opening balances match September closing!")
else:
    print(f"\n⚠️ WARNING: {mismatch_count} items don't match")

# Calculate totals
sept_total = sum(s.closing_stock_value for s in sept_snapshots)
print(f"\nSeptember Minerals Total: €{sept_total:.2f}")

# Get October lines and calculate opening value
oct_lines = StocktakeLine.objects.filter(
    stocktake=october_stocktake,
    item__category__code='M'
).select_related('item')

oct_opening_total = Decimal('0')
for line in oct_lines:
    oct_opening_total += line.opening_qty * line.item.cost_per_serving

print(f"October Opening Total: €{oct_opening_total:.2f}")
print(f"Difference: €{abs(sept_total - oct_opening_total):.2f}")

print("=" * 100)
