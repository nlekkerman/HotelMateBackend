import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from datetime import date
from decimal import Decimal

# Get March 2025 stocktake
march_stocktake = Stocktake.objects.filter(
    period_start=date(2025, 3, 1),
    period_end=date(2025, 3, 31)
).first()

if not march_stocktake:
    print("❌ March 2025 stocktake not found")
    exit()

print("\n" + "="*80)
print("FIXING WINE VARIANCE - Adding purchases to level variance to 0")
print("="*80)

# Get all wine lines with variance +4.50
wine_lines = StocktakeLine.objects.filter(
    stocktake=march_stocktake,
    item__category__code='W'
)

fixed_count = 0
skipped_count = 0

for line in wine_lines:
    variance = float(line.variance_qty)
    
    # Check if variance is approximately +4.50
    if abs(variance - 4.5) < 0.01:
        # Add 4.50 bottles as purchases (in servings, which is bottles for Wine)
        line.purchases = Decimal('4.50')
        line.save()
        
        # Recalculate to verify
        line.refresh_from_db()
        new_variance = float(line.variance_qty)
        
        print(f"\n✅ {line.item.sku} - {line.item.name}")
        print(f"   Opening: {line.opening_qty} | Purchases: {line.purchases}")
        print(f"   Expected: {line.expected_qty} | Counted: {line.counted_qty}")
        print(f"   Old Variance: +4.50 → New Variance: {new_variance:.2f}")
        
        fixed_count += 1
    else:
        skipped_count += 1

print("\n" + "="*80)
print(f"SUMMARY:")
print(f"  Fixed: {fixed_count} items")
print(f"  Skipped: {skipped_count} items (variance not +4.50)")
print("="*80)
