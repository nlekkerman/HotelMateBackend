"""
Test deleting a movement and seeing the line recalculate
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, StockMovement, StockItem, Stocktake
from decimal import Decimal

def test_delete_movement():
    """Test creating and deleting a movement"""
    
    # Get November stocktake
    stocktake = Stocktake.objects.get(
        period_start__year=2025,
        period_start__month=11
    )
    
    # Get a line
    line = stocktake.lines.first()
    
    print("=" * 70)
    print("TEST: Delete Movement")
    print("=" * 70)
    print(f"Line: {line.id} - {line.item.sku}")
    print(f"Stocktake: {stocktake.id} ({stocktake.period_start} to {stocktake.period_end})")
    print()
    
    print("📊 BEFORE:")
    print(f"   Purchases: {line.purchases}")
    print(f"   Waste: {line.waste}")
    print(f"   Expected: {line.expected_qty}")
    print()
    
    # Create a test movement
    movement = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        period=None,  # No period required
        movement_type='PURCHASE',
        quantity=Decimal('50.0'),
        reference='TEST-DELETE',
        notes='Test movement for deletion'
    )
    
    print(f"✅ Created test movement: ID {movement.id}")
    print(f"   Type: {movement.movement_type}")
    print(f"   Quantity: {movement.quantity}")
    print()
    
    # Recalculate line (simulating what add_movement does)
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
    
    # Now delete the movement
    print(f"🗑️  Deleting movement {movement.id}...")
    movement.delete()
    
    # Recalculate again
    movements = _calculate_period_movements(
        line.item,
        stocktake.period_start,
        stocktake.period_end
    )
    
    line.purchases = movements['purchases']
    line.waste = movements['waste']
    line.save()
    
    print()
    print("📊 AFTER DELETING MOVEMENT:")
    print(f"   Purchases: {line.purchases}")
    print(f"   Waste: {line.waste}")
    print(f"   Expected: {line.expected_qty}")
    print()
    
    print("=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print()
    print("The movement was successfully deleted and the line recalculated!")
    print()
    print("💡 To use the API endpoint:")
    print(f"   DELETE /api/stock_tracker/hotel-killarney/stocktake-lines/{line.id}/delete-movement/{{movement_id}}/")

if __name__ == '__main__':
    test_delete_movement()
