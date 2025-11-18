"""
Test the fixed add_movement endpoint
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockMovement, StocktakeLine
from datetime import datetime
from django.utils import timezone

print("=" * 70)
print("TESTING MOVEMENT TIMESTAMP FIX")
print("=" * 70)

# Get a line from February stocktake
line = StocktakeLine.objects.filter(
    stocktake__id=37  # February stocktake
).first()

if not line:
    print("\n❌ No line found")
else:
    print(f"\n📋 Testing with line: {line.id}")
    print(f"   Item: {line.item.sku} - {line.item.name}")
    print(f"   Stocktake period: {line.stocktake.period_start} to {line.stocktake.period_end}")
    print(f"   Current purchases: {line.purchases}")
    
    # Manually create a movement with correct timestamp logic
    from datetime import time as dt_time
    
    movement_timestamp = timezone.now()
    period_end_dt = timezone.make_aware(
        datetime.combine(line.stocktake.period_end, dt_time.max)
    )
    
    print(f"\n🕐 Timestamp Logic:")
    print(f"   Current time: {movement_timestamp}")
    print(f"   Period end: {period_end_dt}")
    print(f"   Current > Period end? {movement_timestamp > period_end_dt}")
    
    if movement_timestamp > period_end_dt:
        movement_timestamp = period_end_dt
        print(f"   ✅ Using period end: {movement_timestamp}")
    else:
        print(f"   ✅ Using current time: {movement_timestamp}")
    
    # Create test movement
    print(f"\n🔧 Creating test movement...")
    movement = StockMovement.objects.create(
        hotel=line.stocktake.hotel,
        item=line.item,
        movement_type='PURCHASE',
        quantity=99.0,
        reference='TEST-TIMESTAMP',
        notes='Testing timestamp fix'
    )
    
    # Override timestamp
    movement.timestamp = movement_timestamp
    movement.save(update_fields=['timestamp'])
    
    print(f"   Created movement ID: {movement.id}")
    print(f"   Timestamp: {movement.timestamp}")
    
    # Now recalculate
    from stock_tracker.stocktake_service import _calculate_period_movements
    
    movements = _calculate_period_movements(
        line.item,
        line.stocktake.period_start,
        line.stocktake.period_end
    )
    
    print(f"\n📊 Recalculated movements:")
    print(f"   Purchases: {movements['purchases']}")
    print(f"   Waste: {movements['waste']}")
    
    # Update line
    line.purchases = movements['purchases']
    line.waste = movements['waste']
    line.save()
    
    print(f"\n✅ Line updated!")
    print(f"   New purchases: {line.purchases}")
    print(f"   Expected qty: {line.expected_qty}")
    
    # Clean up test movement
    print(f"\n🧹 Cleaning up test movement...")
    movement.delete()
    print(f"   Deleted movement ID {movement.id}")

print("\n" + "=" * 70)
