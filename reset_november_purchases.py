"""
Reset purchases and waste to zero for November 2025 stocktake
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, Stocktake
from datetime import date
from decimal import Decimal

# November 2025 stocktake period
period_start = date(2025, 11, 1)
period_end = date(2025, 11, 30)

print("Finding November 2025 stocktake...")
print("=" * 60)

# Get the November stocktake
stocktake = Stocktake.objects.filter(
    period_start=period_start,
    period_end=period_end,
    hotel__slug='hotel-killarney'
).first()

if not stocktake:
    print("❌ November stocktake not found!")
    exit()

print(f"✅ Found: {stocktake}")
print(f"   Lines: {stocktake.lines.count()}")
print()

# Find lines with purchases > 0
lines_with_purchases = stocktake.lines.filter(
    purchases__gt=0
).order_by('-purchases')

print(f"Lines with purchases > 0: {lines_with_purchases.count()}")
print("-" * 60)
for line in lines_with_purchases[:20]:  # Show first 20
    print(f"{line.item.sku:15} {line.item.name:35} {line.purchases:>10}")

if lines_with_purchases.count() > 20:
    print(f"... and {lines_with_purchases.count() - 20} more")

print()
print("=" * 60)

# Ask for confirmation
response = input(
    "\n⚠️  Reset ALL purchases and waste to 0? (yes/no): "
).strip().lower()

if response == 'yes':
    # Reset all lines
    updated = stocktake.lines.update(
        purchases=Decimal('0'),
        waste=Decimal('0')
    )
    
    print(f"\n✅ Reset {updated} stocktake lines")
    print("   - purchases = 0")
    print("   - waste = 0")
    print("\n✨ Done!")
    
else:
    print("\n❌ Cancelled - no changes made")
