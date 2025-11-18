"""
Check what movements exist in the database
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockMovement, StocktakeLine
from django.db.models import Count, Sum

print("=" * 70)
print("CHECKING MOVEMENTS IN DATABASE")
print("=" * 70)

# Total movements
total = StockMovement.objects.count()
print(f"\n📊 Total Movements: {total}")

if total == 0:
    print("\n❌ No movements found in database!")
else:
    # By type
    print(f"\n📋 By Type:")
    by_type = StockMovement.objects.values('movement_type').annotate(
        count=Count('id'),
        total_qty=Sum('quantity')
    ).order_by('-count')
    
    for m in by_type:
        print(f"   {m['movement_type']}: {m['count']} movements, {m['total_qty']} total qty")
    
    # Recent movements
    print(f"\n🕐 5 Most Recent Movements:")
    recent = StockMovement.objects.select_related('item').order_by('-timestamp')[:5]
    for m in recent:
        print(f"   ID {m.id}: {m.timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"      Item: {m.item.sku} - {m.item.name}")
        print(f"      Type: {m.movement_type}, Qty: {m.quantity}")
        print(f"      Reference: {m.reference}")
        print()
    
    # Check if any stocktake lines have purchases/waste
    print(f"\n📦 Stocktake Lines with Purchases/Waste:")
    lines_with_purchases = StocktakeLine.objects.filter(
        purchases__gt=0
    ).select_related('item', 'stocktake')[:5]
    
    for line in lines_with_purchases:
        print(f"   Line {line.id}: {line.item.sku}")
        print(f"      Stocktake: {line.stocktake.id}")
        print(f"      Period: {line.stocktake.period_start} to {line.stocktake.period_end}")
        print(f"      Purchases: {line.purchases}")
        print(f"      Waste: {line.waste}")
        
        # Check movements for this item in period
        from datetime import datetime, time
        from django.utils import timezone
        
        start_dt = timezone.make_aware(
            datetime.combine(line.stocktake.period_start, time.min)
        )
        end_dt = timezone.make_aware(
            datetime.combine(line.stocktake.period_end, time.max)
        )
        
        item_movements = StockMovement.objects.filter(
            item=line.item,
            timestamp__gte=start_dt,
            timestamp__lte=end_dt
        )
        
        print(f"      Movements in period: {item_movements.count()}")
        for mv in item_movements:
            print(f"         - {mv.movement_type}: {mv.quantity} on {mv.timestamp.strftime('%Y-%m-%d')}")
        print()

print("=" * 70)
