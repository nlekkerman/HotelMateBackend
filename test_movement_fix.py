"""
Test that movements are properly filtered by datetime conversion

This script tests the fix for the date/datetime comparison issue
in _calculate_period_movements function.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, Stocktake, StockMovement
from stock_tracker.stocktake_service import _calculate_period_movements
from datetime import date

def test_movement_calculation():
    """Test that movements are properly calculated"""
    
    print("=" * 70)
    print("TESTING MOVEMENT CALCULATION FIX")
    print("=" * 70)
    
    # Get a stocktake
    stocktake = Stocktake.objects.filter(status='DRAFT').first()
    
    if not stocktake:
        print("\n❌ No DRAFT stocktake found")
        return
    
    print(f"\n📋 Testing with stocktake: {stocktake.id}")
    print(f"   Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"   Period types: {type(stocktake.period_start).__name__} to {type(stocktake.period_end).__name__}")
    
    # Get an item with movements
    item = StockItem.objects.filter(
        movements__timestamp__gte=stocktake.period_start,
        movements__timestamp__lte=stocktake.period_end
    ).first()
    
    if not item:
        print("\n❌ No item with movements found in this period")
        return
    
    print(f"\n📦 Testing item: {item.sku} - {item.name}")
    
    # Get all movements for this item in period
    movements = StockMovement.objects.filter(
        item=item,
        timestamp__gte=stocktake.period_start,
        timestamp__lte=stocktake.period_end
    )
    
    print(f"\n🔍 Raw query found {movements.count()} movements:")
    for m in movements[:5]:  # Show first 5
        print(f"   - {m.timestamp} | {m.movement_type} | {m.quantity}")
    
    # Test the fixed function
    print(f"\n🔧 Testing _calculate_period_movements function:")
    result = _calculate_period_movements(
        item,
        stocktake.period_start,
        stocktake.period_end
    )
    
    print(f"\n✅ Result:")
    print(f"   Purchases: {result['purchases']}")
    print(f"   Waste: {result['waste']}")
    print(f"   Transfers In: {result['transfers_in']}")
    print(f"   Transfers Out: {result['transfers_out']}")
    print(f"   Adjustments: {result['adjustments']}")
    
    # Verify against manual calculation
    manual_purchases = sum(
        m.quantity for m in movements if m.movement_type == 'PURCHASE'
    )
    manual_waste = sum(
        m.quantity for m in movements if m.movement_type == 'WASTE'
    )
    
    print(f"\n📊 Manual calculation:")
    print(f"   Purchases: {manual_purchases}")
    print(f"   Waste: {manual_waste}")
    
    if result['purchases'] == manual_purchases and result['waste'] == manual_waste:
        print(f"\n✅ SUCCESS! Calculations match!")
    else:
        print(f"\n❌ MISMATCH! Function result doesn't match manual calculation")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_movement_calculation()
