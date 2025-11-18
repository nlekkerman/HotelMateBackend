#!/usr/bin/env python3
"""
Test script to verify delete and update endpoints now work with datetime fix.
Tests movement 4593 on line 8853.
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, StockMovement
from django.utils import timezone
from datetime import datetime, time

def test_movement_query():
    """Test that we can find movement 4593 with datetime conversion."""
    print("Testing movement query with datetime fix...")
    
    try:
        line = StocktakeLine.objects.get(id=8853)
        print(f"✓ Found line {line.id} for item {line.item.name}")
        print(f"  Stocktake period: {line.stocktake.period_start} to {line.stocktake.period_end}")
        
        # OLD BROKEN QUERY (what delete/update used before)
        print("\n1. Testing OLD query (date comparison):")
        try:
            movement_old = StockMovement.objects.get(
                id=4593,
                item=line.item,
                timestamp__gte=line.stocktake.period_start,
                timestamp__lte=line.stocktake.period_end
            )
            print(f"  ✓ Found movement {movement_old.id}")
        except StockMovement.DoesNotExist:
            print(f"  ✗ Movement 4593 NOT FOUND (expected - this is the bug)")
        
        # NEW FIXED QUERY (what delete/update use now)
        print("\n2. Testing NEW query (datetime conversion):")
        start_dt = timezone.make_aware(
            datetime.combine(line.stocktake.period_start, time.min)
        )
        end_dt = timezone.make_aware(
            datetime.combine(line.stocktake.period_end, time.max)
        )
        
        try:
            movement_new = StockMovement.objects.get(
                id=4593,
                item=line.item,
                timestamp__gte=start_dt,
                timestamp__lte=end_dt
            )
            print(f"  ✓ Found movement {movement_new.id}")
            print(f"    Type: {movement_new.movement_type}")
            print(f"    Quantity: {movement_new.quantity}")
            print(f"    Timestamp: {movement_new.timestamp}")
            print(f"    Timestamp type: {type(movement_new.timestamp)}")
            print(f"\n  ✓ NEW QUERY WORKS - endpoints should now work!")
        except StockMovement.DoesNotExist:
            print(f"  ✗ Movement 4593 NOT FOUND (unexpected!)")
            
    except StocktakeLine.DoesNotExist:
        print(f"✗ Line 8853 not found")
        return
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_movement_query()
