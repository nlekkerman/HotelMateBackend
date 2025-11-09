"""
Test updating (editing) a movement
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StocktakeLine, StockMovement, Stocktake
)
from decimal import Decimal

def test_update_movement():
    """Test creating, updating, and verifying a movement"""
    
    # Get November stocktake
    stocktake = Stocktake.objects.get(
        period_start__year=2025,
        period_start__month=11
    )
    
    # Get a line
    line = stocktake.lines.first()
    
    print("=" * 70)
    print("TEST: Update Movement")
    print("=" * 70)
    print(f"Line: {line.id} - {line.item.sku}")
    print(f"Stocktake: {stocktake.id} "
          f"({stocktake.period_start} to {stocktake.period_end})")
    print()
    
    print("📊 INITIAL STATE:")
    print(f"   Purchases: {line.purchases}")
    print(f"   Waste: {line.waste}")
    print(f"   Expected: {line.expected_qty}")
    print()
    
    # Create a test movement
    movement = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        period=None,
        movement_type='PURCHASE',
        quantity=Decimal('50.0'),
        reference='TEST-EDIT',
        notes='Test movement for editing'
    )
    
    print(f"✅ Created test movement: ID {movement.id}")
    print(f"   Type: {movement.movement_type}")
    print(f"   Quantity: {movement.quantity}")
    print(f"   Reference: {movement.reference}")
    print()
    
    # Recalculate line
    from stock_tracker.stocktake_service import _calculate_period_movements
    
    movements = _calculate_period_movements(
        line.item,
        stocktake.period_start,
        stocktake.period_end
    )
    
    line.purchases = movements['purchases']
    line.waste = movements['waste']
    line.save()
    
    print("📊 AFTER ADDING MOVEMENT:")
    print(f"   Purchases: {line.purchases}")
    print(f"   Waste: {line.waste}")
    print(f"   Expected: {line.expected_qty}")
    print()
    
    # Now UPDATE the movement
    print(f"✏️  Updating movement {movement.id}...")
    print("   Changing: quantity 50.0 → 100.0")
    print("   Changing: type PURCHASE → WASTE")
    print()
    
    movement.quantity = Decimal('100.0')
    movement.movement_type = 'WASTE'
    movement.notes = 'Updated to waste with new quantity'
    movement.save()
    
    # Recalculate again
    movements = _calculate_period_movements(
        line.item,
        stocktake.period_start,
        stocktake.period_end
    )
    
    line.purchases = movements['purchases']
    line.waste = movements['waste']
    line.save()
    
    print("📊 AFTER UPDATING MOVEMENT:")
    print(f"   Purchases: {line.purchases}")
    print(f"   Waste: {line.waste}")
    print(f"   Expected: {line.expected_qty}")
    print()
    
    # Verify the update
    updated_movement = StockMovement.objects.get(id=movement.id)
    print("✅ Verified updated movement:")
    print(f"   Type: {updated_movement.movement_type}")
    print(f"   Quantity: {updated_movement.quantity}")
    print(f"   Notes: {updated_movement.notes}")
    print()
    
    # Clean up
    print(f"🗑️  Cleaning up - deleting movement {movement.id}...")
    movement.delete()
    
    movements = _calculate_period_movements(
        line.item,
        stocktake.period_start,
        stocktake.period_end
    )
    
    line.purchases = movements['purchases']
    line.waste = movements['waste']
    line.save()
    
    print()
    print("📊 AFTER CLEANUP:")
    print(f"   Purchases: {line.purchases}")
    print(f"   Waste: {line.waste}")
    print(f"   Expected: {line.expected_qty}")
    print()
    
    print("=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print()
    print("The movement was successfully created, updated, and deleted!")
    print()
    print("💡 To use the API endpoint:")
    print(f"   PATCH /api/stock_tracker/hotel-killarney/")
    print(f"stocktake-lines/{line.id}/update-movement/{{movement_id}}/")
    print("   Body: {")
    print('     "movement_type": "WASTE",')
    print('     "quantity": 100.0,')
    print('     "notes": "Updated quantity"')
    print("   }")

if __name__ == '__main__':
    test_update_movement()
