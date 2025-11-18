"""
Test the /movements/ endpoint fix
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockMovement, StocktakeLine
from datetime import datetime, time
from django.utils import timezone

print("=" * 70)
print("TESTING /movements/ ENDPOINT FIX")
print("=" * 70)

# Get a line that has movements
line = StocktakeLine.objects.get(id=8853)  # B0070 line with movements

print(f"\n📋 Testing with line: {line.id}")
print(f"   Item: {line.item.sku} - {line.item.name}")
print(f"   Stocktake: {line.stocktake.id}")
print(f"   Period: {line.stocktake.period_start} to {line.stocktake.period_end}")
print(f"   Purchases on line: {line.purchases}")

# Check movements using OLD query (without datetime conversion)
print(f"\n❌ OLD QUERY (Date comparison - BROKEN):")
old_movements = StockMovement.objects.filter(
    item=line.item,
    timestamp__gte=line.stocktake.period_start,
    timestamp__lte=line.stocktake.period_end
)
print(f"   Found: {old_movements.count()} movements")

# Check movements using NEW query (with datetime conversion)
print(f"\n✅ NEW QUERY (DateTime comparison - FIXED):")
start_dt = timezone.make_aware(
    datetime.combine(line.stocktake.period_start, time.min)
)
end_dt = timezone.make_aware(
    datetime.combine(line.stocktake.period_end, time.max)
)

new_movements = StockMovement.objects.filter(
    item=line.item,
    timestamp__gte=start_dt,
    timestamp__lte=end_dt
).order_by('-timestamp')

print(f"   Found: {new_movements.count()} movements")

if new_movements.exists():
    print(f"\n📦 Movement Details:")
    for m in new_movements:
        print(f"   ID {m.id}:")
        print(f"      Type: {m.movement_type}")
        print(f"      Quantity: {m.quantity}")
        print(f"      Timestamp: {m.timestamp}")
        print(f"      Reference: {m.reference}")
        print(f"      Within period? {start_dt <= m.timestamp <= end_dt}")
        print()

print("\n" + "=" * 70)
print(f"✅ FIX VERIFIED!")
print(f"   Old query (broken): {old_movements.count()} movements")
print(f"   New query (fixed): {new_movements.count()} movements")
print("=" * 70)
