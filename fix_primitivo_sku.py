"""
Fix S45 -> W45 (Primitivo Giola Colle)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from decimal import Decimal

september = Stocktake.objects.get(id=8)

print(f"\n🔧 Fixing Primitivo wine SKU...")

# Update W45 with the correct data
try:
    line = september.lines.get(item__sku='W45')
    line.counted_full_units = Decimal('7.00')
    line.counted_partial_units = Decimal('0.00')
    line.save()
    print(f"✅ Updated W45 - {line.item.name}")
    print(f"   Counted: 7.00 bottles")
except StocktakeLine.DoesNotExist:
    print(f"⚠️  W45 not found in stocktake lines")
    print(f"   Checking if item exists in system...")
    from stock_tracker.models import StockItem
    try:
        item = StockItem.objects.get(sku='W45')
        print(f"   Found item: {item.name}")
        print(f"   Category: {item.category.code}")
    except StockItem.DoesNotExist:
        print(f"   ❌ W45 item doesn't exist in the system")

# Final check
total_lines = september.lines.count()
counted_lines = september.lines.exclude(
    counted_full_units=0,
    counted_partial_units=0
).count()

print(f"\n📊 Updated Stock Count:")
print(f"   Total items: {total_lines}")
print(f"   Items with counts: {counted_lines}")
print(f"   Items at zero: {total_lines - counted_lines}")

print(f"\n✅ Fix complete!\n")
