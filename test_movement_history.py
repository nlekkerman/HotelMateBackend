"""
Test movement history functionality
Demonstrates how to retrieve and display movement history for a stocktake line
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StocktakeLine, StockMovement, Stocktake
)
from stock_tracker.stock_serializers import StockMovementSerializer
from decimal import Decimal
from datetime import datetime

def test_movement_history():
    """Test retrieving movement history for a line"""
    
    # Get November stocktake
    stocktake = Stocktake.objects.get(
        period_start__year=2025,
        period_start__month=11
    )
    
    # Get a line
    line = stocktake.lines.first()
    
    print("=" * 70)
    print("TEST: Movement History")
    print("=" * 70)
    print(f"Line: {line.id} - {line.item.sku} ({line.item.name})")
    print(f"Stocktake: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print()
    
    print("📊 CURRENT LINE STATE:")
    print(f"   Opening: {line.opening_qty}")
    print(f"   Purchases: {line.purchases}")
    print(f"   Waste: {line.waste}")
    print(f"   Expected: {line.expected_qty}")
    print()
    
    # Get existing movements
    existing_movements = StockMovement.objects.filter(
        item=line.item,
        timestamp__gte=line.stocktake.period_start,
        timestamp__lte=line.stocktake.period_end
    ).order_by('-timestamp')
    
    print(f"📜 EXISTING MOVEMENTS: {existing_movements.count()}")
    for i, mov in enumerate(existing_movements, 1):
        print(f"   {i}. [{mov.movement_type}] {mov.quantity} "
              f"@ {mov.timestamp.strftime('%Y-%m-%d %H:%M')} "
              f"- {mov.notes or 'No notes'}")
    print()
    
    # Create some test movements to demonstrate history
    print("✨ Creating test movements to demonstrate history...")
    print()
    
    movements_created = []
    
    # Movement 1: Purchase
    mov1 = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        movement_type='PURCHASE',
        quantity=Decimal('88.0'),
        unit_cost=Decimal('2.50'),
        reference='TEST-INV-001',
        notes='Test delivery - 1 keg'
    )
    movements_created.append(mov1)
    print(f"✅ Created PURCHASE: {mov1.quantity} servings")
    print(f"   ID: {mov1.id}")
    print(f"   Reference: {mov1.reference}")
    print(f"   Timestamp: {mov1.timestamp}")
    print()
    
    # Movement 2: Waste
    mov2 = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        movement_type='WASTE',
        quantity=Decimal('5.0'),
        reference='WASTE-001',
        notes='Spillage during busy night'
    )
    movements_created.append(mov2)
    print(f"✅ Created WASTE: {mov2.quantity} servings")
    print(f"   ID: {mov2.id}")
    print(f"   Reference: {mov2.reference}")
    print(f"   Timestamp: {mov2.timestamp}")
    print()
    
    # Movement 3: Another Purchase
    mov3 = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        movement_type='PURCHASE',
        quantity=Decimal('176.0'),
        unit_cost=Decimal('2.55'),
        reference='TEST-INV-002',
        notes='Test delivery - 2 kegs'
    )
    movements_created.append(mov3)
    print(f"✅ Created PURCHASE: {mov3.quantity} servings")
    print(f"   ID: {mov3.id}")
    print(f"   Reference: {mov3.reference}")
    print(f"   Timestamp: {mov3.timestamp}")
    print()
    
    # Recalculate line
    from stock_tracker.stocktake_service import _calculate_period_movements
    
    movements = _calculate_period_movements(
        line.item,
        line.stocktake.period_start,
        line.stocktake.period_end
    )
    
    line.purchases = movements['purchases']
    line.waste = movements['waste']
    line.save()
    
    print("📊 UPDATED LINE STATE:")
    print(f"   Opening: {line.opening_qty}")
    print(f"   Purchases: {line.purchases} (+{movements['purchases']})")
    print(f"   Waste: {line.waste} (+{movements['waste']})")
    print(f"   Expected: {line.expected_qty}")
    print()
    
    # Now retrieve movement history (simulating API call)
    print("=" * 70)
    print("📜 MOVEMENT HISTORY (API Response Simulation)")
    print("=" * 70)
    
    all_movements = StockMovement.objects.filter(
        item=line.item,
        timestamp__gte=line.stocktake.period_start,
        timestamp__lte=line.stocktake.period_end
    ).order_by('-timestamp')
    
    serializer = StockMovementSerializer(all_movements, many=True)
    
    print(f"\nTotal Movements: {all_movements.count()}")
    print()
    
    for i, movement_data in enumerate(serializer.data, 1):
        print(f"{i}. Movement ID: {movement_data['id']}")
        print(f"   Type: {movement_data['movement_type']}")
        print(f"   Quantity: {movement_data['quantity']} servings")
        print(f"   Unit Cost: €{movement_data['unit_cost'] or '0.00'}")
        print(f"   Reference: {movement_data['reference'] or 'N/A'}")
        print(f"   Notes: {movement_data['notes'] or 'No notes'}")
        print(f"   Timestamp: {movement_data['timestamp']}")
        print(f"   Staff: {movement_data['staff_name'] or 'System'}")
        print()
    
    # Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    purchases_total = sum(
        Decimal(m['quantity']) 
        for m in serializer.data 
        if m['movement_type'] == 'PURCHASE'
    )
    waste_total = sum(
        Decimal(m['quantity']) 
        for m in serializer.data 
        if m['movement_type'] == 'WASTE'
    )
    
    print(f"Total Purchases: {purchases_total} servings")
    print(f"Total Waste: {waste_total} servings")
    print(f"Line Purchases: {line.purchases}")
    print(f"Line Waste: {line.waste}")
    print()
    
    # Clean up test movements
    print("🧹 Cleaning up test movements...")
    for mov in movements_created:
        mov.delete()
    
    # Recalculate line back to original state
    movements = _calculate_period_movements(
        line.item,
        line.stocktake.period_start,
        line.stocktake.period_end
    )
    
    line.purchases = movements['purchases']
    line.waste = movements['waste']
    line.save()
    
    print("✅ Test movements deleted")
    print()
    print("📊 RESTORED LINE STATE:")
    print(f"   Purchases: {line.purchases}")
    print(f"   Waste: {line.waste}")
    print(f"   Expected: {line.expected_qty}")
    print()
    
    print("=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print()
    print("💡 API Endpoint:")
    print(f"   GET /api/stock_tracker/hotel-killarney/stocktake-lines/{line.id}/movements/")
    print()
    print("📦 Response Format:")
    print("   {")
    print('     "movements": [')
    print('       {')
    print('         "id": 123,')
    print('         "movement_type": "PURCHASE",')
    print('         "quantity": "88.0000",')
    print('         "unit_cost": "2.5000",')
    print('         "reference": "INV-001",')
    print('         "notes": "Delivery",')
    print('         "timestamp": "2025-11-09T10:30:00Z",')
    print('         "staff_name": "John Doe",')
    print('         "item_sku": "BEER_DRAUGHT_GUIN",')
    print('         "item_name": "Guinness Keg"')
    print('       },')
    print('       ...')
    print('     ],')
    print('     "summary": {')
    print('       "total_purchases": "264.0000",')
    print('       "total_waste": "10.0000",')
    print('       "movement_count": 5')
    print('     }')
    print('   }')

if __name__ == '__main__':
    test_movement_history()
