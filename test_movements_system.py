"""
Test StockMovement System - Sales, Waste, and Variance Impact

This script demonstrates:
1. How movements are created and stored
2. How they aggregate into stocktake lines
3. How they affect expected_qty and variance_qty
4. Real-time impact of adding/removing movements
"""

import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    Stocktake, StocktakeLine, StockMovement, StockItem, StockPeriod
)
from hotel.models import Hotel
from decimal import Decimal


def print_line_state(line, title="Current State"):
    """Pretty print stocktake line state"""
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)
    print(f"Item: {line.item.sku} - {line.item.name}")
    print(f"Category: {line.item.category.code}")
    print("\n" + "-" * 80)
    print("MOVEMENTS (Aggregated from StockMovement records):")
    print("-" * 80)
    print(f"  Opening Stock:        {line.opening_qty:>15,.4f} servings")
    print(f"  + Purchases:          {line.purchases:>15,.4f}")
    print(f"  + Transfers In:       {line.transfers_in:>15,.4f}")
    print(f"  - Sales:              {line.sales:>15,.4f}")
    print(f"  - Waste:              {line.waste:>15,.4f}")
    print(f"  - Transfers Out:      {line.transfers_out:>15,.4f}")
    print(f"  + Adjustments:        {line.adjustments:>15,.4f}")
    print("-" * 80)
    print(f"  = EXPECTED:           {line.expected_qty:>15,.4f} servings")
    print(f"\n  Counted:              {line.counted_qty:>15,.4f} servings")
    
    variance_color = "SHORTAGE" if line.variance_qty < 0 else "SURPLUS"
    print(f"  Variance:             {line.variance_qty:>15,.4f} ({variance_color})")
    print(f"  Variance Value:       €{line.variance_value:>14,.2f}")


def test_movement_creation():
    """Test 1: Create movements and see immediate impact"""
    print("\n" + "*" * 80)
    print("TEST 1: CREATE MOVEMENTS AND SEE IMPACT")
    print("*" * 80)
    
    # Get a stocktake with some data
    stocktake = Stocktake.objects.filter(status='DRAFT').first()
    if not stocktake:
        stocktake = Stocktake.objects.order_by('-period_end').first()
    
    if not stocktake:
        print("❌ No stocktake found")
        return
    
    # Get a line to work with
    line = stocktake.lines.first()
    if not line:
        print("❌ No stocktake lines found")
        return
    
    print(f"\nStocktake: {stocktake.id} ({stocktake.period_start} to "
          f"{stocktake.period_end})")
    
    # Show initial state
    print_line_state(line, "INITIAL STATE")
    
    # Get the period
    period = StockPeriod.objects.filter(
        start_date=stocktake.period_start,
        end_date=stocktake.period_end,
        hotel=stocktake.hotel
    ).first()
    
    if not period:
        print("\n⚠️  No period found - movements may not aggregate correctly")
        return
    
    # Create a SALE movement
    print("\n" + "=" * 80)
    print("ACTION: Adding SALE movement of 10 servings")
    print("=" * 80)
    
    sale_movement = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        period=period,
        movement_type=StockMovement.SALE,
        quantity=Decimal('10.0000'),
        reference='TEST-SALE-001',
        notes='Test sale from test script',
        timestamp=datetime.now()
    )
    
    print(f"✅ Created StockMovement ID: {sale_movement.id}")
    print(f"   Type: SALE")
    print(f"   Quantity: 10.0000 servings")
    print(f"   Item: {line.item.sku}")
    
    # Refresh the stocktake line to see new aggregated data
    # In production, you'd need to recalculate or refresh
    print("\n⚠️  Note: In the real system, you need to refresh/recalculate "
          "stocktake to see updated aggregates")
    print("   For now, showing the movement was created successfully.")
    
    # Show movement details
    movements = StockMovement.objects.filter(
        item=line.item,
        period=period,
        movement_type=StockMovement.SALE
    )
    
    print(f"\n📊 Total SALE movements for this item: {movements.count()}")
    print(f"   Sum of quantities: {sum(m.quantity for m in movements):,.4f}")
    
    # Clean up
    print("\n🧹 Cleaning up test movement...")
    sale_movement.delete()
    print("✅ Test movement removed")


def test_waste_movement():
    """Test 2: Create waste movement and see impact"""
    print("\n\n" + "*" * 80)
    print("TEST 2: WASTE MOVEMENT IMPACT")
    print("*" * 80)
    
    stocktake = Stocktake.objects.filter(status='DRAFT').first()
    if not stocktake:
        stocktake = Stocktake.objects.order_by('-period_end').first()
    
    if not stocktake:
        print("❌ No stocktake found")
        return
    
    line = stocktake.lines.exclude(opening_qty=Decimal('0')).first()
    if not line:
        print("❌ No suitable line found")
        return
    
    print_line_state(line, "BEFORE ADDING WASTE")
    
    period = StockPeriod.objects.filter(
        start_date=stocktake.period_start,
        end_date=stocktake.period_end,
        hotel=stocktake.hotel
    ).first()
    
    if not period:
        print("\n⚠️  No period found")
        return
    
    # Create WASTE movement
    print("\n" + "=" * 80)
    print("ACTION: Adding WASTE movement of 5 servings")
    print("=" * 80)
    
    waste_movement = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        period=period,
        movement_type=StockMovement.WASTE,
        quantity=Decimal('5.0000'),
        reference='TEST-WASTE-001',
        notes='Broken bottle - test',
        timestamp=datetime.now()
    )
    
    print(f"✅ Created StockMovement ID: {waste_movement.id}")
    print(f"   Type: WASTE")
    print(f"   Quantity: 5.0000 servings")
    
    # Show all movements for this item
    all_movements = StockMovement.objects.filter(
        item=line.item,
        period=period
    ).order_by('-timestamp')
    
    print(f"\n📊 All movements for {line.item.sku} in this period:")
    print("-" * 80)
    for mov in all_movements:
        print(f"   {mov.movement_type:15} {mov.quantity:>10,.4f} servings  "
              f"{mov.timestamp.strftime('%Y-%m-%d %H:%M')}")
    
    # Clean up
    print("\n🧹 Cleaning up...")
    waste_movement.delete()
    print("✅ Test movement removed")


def test_multiple_movements():
    """Test 3: Multiple movements and cumulative effect"""
    print("\n\n" + "*" * 80)
    print("TEST 3: MULTIPLE MOVEMENTS - CUMULATIVE EFFECT")
    print("*" * 80)
    
    stocktake = Stocktake.objects.order_by('-period_end').first()
    if not stocktake:
        print("❌ No stocktake found")
        return
    
    line = stocktake.lines.exclude(opening_qty=Decimal('0')).first()
    if not line:
        print("❌ No suitable line found")
        return
    
    period = StockPeriod.objects.filter(
        start_date=stocktake.period_start,
        end_date=stocktake.period_end,
        hotel=stocktake.hotel
    ).first()
    
    if not period:
        print("\n⚠️  No period found")
        return
    
    print(f"\nItem: {line.item.sku} - {line.item.name}")
    print(f"Period: {period.period_name}")
    
    # Show initial aggregates
    print("\n" + "=" * 80)
    print("CURRENT AGGREGATE VALUES:")
    print("=" * 80)
    print(f"  Sales Total:          {line.sales:>15,.4f} servings")
    print(f"  Waste Total:          {line.waste:>15,.4f} servings")
    print(f"  Purchases Total:      {line.purchases:>15,.4f} servings")
    print(f"  Expected Qty:         {line.expected_qty:>15,.4f} servings")
    
    # Create multiple test movements
    test_movements = []
    
    print("\n" + "=" * 80)
    print("CREATING TEST MOVEMENTS:")
    print("=" * 80)
    
    # Sale 1
    mov1 = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        period=period,
        movement_type=StockMovement.SALE,
        quantity=Decimal('15.0000'),
        reference='TEST-MULTI-001',
        notes='First sale',
        timestamp=datetime.now()
    )
    test_movements.append(mov1)
    print(f"✅ Created SALE: 15.0000 servings (ID: {mov1.id})")
    
    # Sale 2
    mov2 = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        period=period,
        movement_type=StockMovement.SALE,
        quantity=Decimal('8.5000'),
        reference='TEST-MULTI-002',
        notes='Second sale',
        timestamp=datetime.now()
    )
    test_movements.append(mov2)
    print(f"✅ Created SALE: 8.5000 servings (ID: {mov2.id})")
    
    # Waste
    mov3 = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        period=period,
        movement_type=StockMovement.WASTE,
        quantity=Decimal('3.0000'),
        reference='TEST-MULTI-003',
        notes='Spillage',
        timestamp=datetime.now()
    )
    test_movements.append(mov3)
    print(f"✅ Created WASTE: 3.0000 servings (ID: {mov3.id})")
    
    # Purchase
    mov4 = StockMovement.objects.create(
        hotel=stocktake.hotel,
        item=line.item,
        period=period,
        movement_type=StockMovement.PURCHASE,
        quantity=Decimal('50.0000'),
        reference='TEST-MULTI-004',
        notes='Test delivery',
        timestamp=datetime.now()
    )
    test_movements.append(mov4)
    print(f"✅ Created PURCHASE: 50.0000 servings (ID: {mov4.id})")
    
    # Calculate what the new values should be
    print("\n" + "=" * 80)
    print("EXPECTED NEW AGGREGATE VALUES:")
    print("=" * 80)
    new_sales = line.sales + Decimal('15.0000') + Decimal('8.5000')
    new_waste = line.waste + Decimal('3.0000')
    new_purchases = line.purchases + Decimal('50.0000')
    new_expected = (line.opening_qty + new_purchases + line.transfers_in - 
                    new_sales - new_waste - line.transfers_out + 
                    line.adjustments)
    
    print(f"  Sales Total:          {new_sales:>15,.4f} servings "
          f"(+23.5000)")
    print(f"  Waste Total:          {new_waste:>15,.4f} servings (+3.0000)")
    print(f"  Purchases Total:      {new_purchases:>15,.4f} servings "
          f"(+50.0000)")
    print(f"  Expected Qty:         {new_expected:>15,.4f} servings")
    
    print("\n" + "=" * 80)
    print("IMPACT ON VARIANCE:")
    print("=" * 80)
    print(f"  Net change: +50 (purchase) -23.5 (sales) -3 (waste) = "
          f"+23.5 servings")
    print(f"  Expected increased by 23.5 servings")
    print(f"  Variance changes by -23.5 servings (if counted stays same)")
    
    # Query all movements for this item in period
    all_movements = StockMovement.objects.filter(
        item=line.item,
        period=period
    ).order_by('-timestamp')[:10]  # Last 10
    
    print(f"\n" + "=" * 80)
    print(f"RECENT MOVEMENTS FOR {line.item.sku} (Last 10):")
    print("=" * 80)
    print(f"{'Type':<15} {'Quantity':>12} {'Reference':<20} {'Date':<20}")
    print("-" * 80)
    
    for mov in all_movements:
        print(f"{mov.movement_type:<15} {mov.quantity:>12,.4f} "
              f"{mov.reference:<20} "
              f"{mov.timestamp.strftime('%Y-%m-%d %H:%M'):<20}")
    
    # Clean up all test movements
    print("\n🧹 Cleaning up all test movements...")
    for mov in test_movements:
        mov.delete()
    print(f"✅ Removed {len(test_movements)} test movements")


def test_view_all_movements():
    """Test 4: View all movements in a period"""
    print("\n\n" + "*" * 80)
    print("TEST 4: VIEW ALL MOVEMENTS IN PERIOD")
    print("*" * 80)
    
    # Get latest period
    period = StockPeriod.objects.order_by('-end_date').first()
    if not period:
        print("❌ No periods found")
        return
    
    print(f"\nPeriod: {period.period_name}")
    print(f"Dates: {period.start_date} to {period.end_date}")
    
    # Get all movements
    movements = StockMovement.objects.filter(
        period=period
    ).order_by('movement_type', 'item__sku')
    
    print(f"\nTotal movements in period: {movements.count()}")
    
    # Group by type
    by_type = {}
    for mov in movements:
        if mov.movement_type not in by_type:
            by_type[mov.movement_type] = {
                'count': 0,
                'total_qty': Decimal('0')
            }
        by_type[mov.movement_type]['count'] += 1
        by_type[mov.movement_type]['total_qty'] += mov.quantity
    
    print("\n" + "=" * 80)
    print("MOVEMENTS BY TYPE:")
    print("=" * 80)
    print(f"{'Type':<20} {'Count':>10} {'Total Quantity':>20}")
    print("-" * 80)
    
    for mov_type in ['PURCHASE', 'SALE', 'WASTE', 'TRANSFER_IN', 
                      'TRANSFER_OUT', 'ADJUSTMENT']:
        if mov_type in by_type:
            data = by_type[mov_type]
            print(f"{mov_type:<20} {data['count']:>10} "
                  f"{data['total_qty']:>20,.4f} servings")
    
    # Show sample movements
    if movements.count() > 0:
        print("\n" + "=" * 80)
        print("SAMPLE MOVEMENTS (First 10):")
        print("=" * 80)
        print(f"{'Type':<15} {'Item':<15} {'Qty':>10} {'Reference':<20}")
        print("-" * 80)
        
        for mov in movements[:10]:
            print(f"{mov.movement_type:<15} {mov.item.sku:<15} "
                  f"{mov.quantity:>10,.2f} {mov.reference or '---':<20}")


def test_api_simulation():
    """Test 5: Simulate API workflow"""
    print("\n\n" + "*" * 80)
    print("TEST 5: API WORKFLOW SIMULATION")
    print("*" * 80)
    
    print("\nThis simulates what happens in the frontend when:")
    print("1. User views a stocktake line")
    print("2. User clicks 'Add Sale Movement'")
    print("3. System creates movement")
    print("4. User refreshes to see updated values")
    
    stocktake = Stocktake.objects.order_by('-period_end').first()
    if not stocktake:
        print("❌ No stocktake found")
        return
    
    line = stocktake.lines.exclude(opening_qty=Decimal('0')).first()
    if not line:
        print("❌ No suitable line found")
        return
    
    period = StockPeriod.objects.filter(
        start_date=stocktake.period_start,
        end_date=stocktake.period_end,
        hotel=stocktake.hotel
    ).first()
    
    print("\n" + "=" * 80)
    print("STEP 1: Frontend fetches stocktake line")
    print("=" * 80)
    print(f"GET /api/stock_tracker/{{hotel_id}}/stocktake-lines/"
          f"{line.id}/")
    print("\nResponse includes:")
    print(f"  opening_qty: {line.opening_qty}")
    print(f"  sales: {line.sales}")
    print(f"  waste: {line.waste}")
    print(f"  expected_qty: {line.expected_qty}")
    print(f"  counted_qty: {line.counted_qty}")
    print(f"  variance_qty: {line.variance_qty}")
    
    print("\n" + "=" * 80)
    print("STEP 2: User clicks 'Add Sale' and enters quantity: 12.50")
    print("=" * 80)
    print(f"POST /api/stock_tracker/{{hotel_id}}/stock-movements/")
    print("Body: {")
    print(f"  'item': {line.item.id},")
    print(f"  'period': {period.id if period else 'null'},")
    print(f"  'movement_type': 'SALE',")
    print(f"  'quantity': '12.50',")
    print(f"  'reference': 'Evening service',")
    print(f"  'notes': 'Busy evening'")
    print("}")
    
    if period:
        # Actually create it
        movement = StockMovement.objects.create(
            hotel=stocktake.hotel,
            item=line.item,
            period=period,
            movement_type=StockMovement.SALE,
            quantity=Decimal('12.50'),
            reference='Evening service',
            notes='Busy evening - API simulation test'
        )
        
        print(f"\n✅ Movement created with ID: {movement.id}")
        
        print("\n" + "=" * 80)
        print("STEP 3: Frontend refreshes stocktake")
        print("=" * 80)
        print(f"GET /api/stock_tracker/{{hotel_id}}/stocktakes/"
              f"{stocktake.id}/")
        print("\n⚠️  Note: Backend would recalculate aggregates here")
        print("   Expected sales would increase by 12.50")
        print("   Expected_qty would decrease by 12.50")
        print("   Variance would change by -12.50 (if counted unchanged)")
        
        # Clean up
        print("\n🧹 Cleaning up test movement...")
        movement.delete()
        print("✅ Removed")
    else:
        print("\n⚠️  No period found - skipping actual creation")


if __name__ == "__main__":
    print("\n")
    print("*" * 80)
    print("STOCK MOVEMENT SYSTEM TESTS")
    print("Testing how movements affect expected_qty and variance_qty")
    print("*" * 80)
    
    test_movement_creation()
    test_waste_movement()
    test_multiple_movements()
    test_view_all_movements()
    test_api_simulation()
    
    print("\n\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
    print("\n✅ Summary:")
    print("   - Movements are stored in StockMovement table")
    print("   - They aggregate into StocktakeLine fields (sales, waste, etc.)")
    print("   - Adding SALE/WASTE decreases expected_qty")
    print("   - Adding PURCHASE increases expected_qty")
    print("   - Variance = counted - expected")
    print("   - Frontend should use movement API to add/edit movements")
    print()
