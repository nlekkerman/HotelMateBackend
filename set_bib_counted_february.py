"""
Set BIB counted values to 2.5 boxes for February stocktake
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, Stocktake, StocktakeLine

print("\n" + "="*80)
print("SET BIB COUNTED VALUES - FEBRUARY 2025")
print("="*80)

# Get February stocktake
stocktake = Stocktake.objects.filter(
    hotel_id=2,
    period_start__year=2025,
    period_start__month=2
).first()

if not stocktake:
    print("\n❌ February 2025 stocktake not found!")
    exit(1)

print(f"\nStocktake: {stocktake.id}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print(f"Status: {stocktake.status}")

if stocktake.status == 'closed':
    print("\n⚠️ WARNING: Stocktake is CLOSED!")
    response = input("Continue anyway? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        exit(0)

# Get BIB items
bib_lines = StocktakeLine.objects.filter(
    stocktake=stocktake,
    item__subcategory='BIB'
).select_related('item').order_by('item__sku')

print(f"\nFound {bib_lines.count()} BIB items")
print("\nSetting counted to 2.5 boxes (full=2, partial=0.5)")
print("-"*80)

for line in bib_lines:
    print(f"\n{line.item.sku} - {line.item.name}")
    print(f"  Unit cost: €{line.item.unit_cost}")
    
    # Show before
    before_full = line.counted_full_units or 0
    before_partial = line.counted_partial_units or 0
    before_total = before_full + before_partial
    before_value = line.counted_value
    
    print(f"  BEFORE: {before_total:.2f} boxes = €{before_value:.2f}")
    
    # Set to 2.5 boxes
    line.counted_full_units = 2
    line.counted_partial_units = Decimal('0.5')
    line.save()
    
    # Refresh to get calculated values
    line.refresh_from_db()
    
    # Show after
    after_total = line.counted_full_units + line.counted_partial_units
    after_value = line.counted_value
    
    print(f"  AFTER:  {after_total:.2f} boxes = €{after_value:.2f}")
    
    # Verify calculation
    expected = Decimal('2.5') * line.item.unit_cost
    if abs(after_value - expected) < Decimal('0.01'):
        print(f"  ✅ VERIFIED (2.5 × €{line.item.unit_cost} = €{expected:.2f})")
    else:
        print(f"  ❌ ERROR: Expected €{expected:.2f}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

# Show all BIB lines again
total_value = Decimal('0')
for line in bib_lines:
    line.refresh_from_db()
    total = line.counted_full_units + line.counted_partial_units
    value = line.counted_value
    total_value += value
    print(f"{line.item.sku}: {total:.2f} boxes = €{value:.2f}")

print(f"\nTotal BIB value: €{total_value:.2f}")
print("="*80 + "\n")
