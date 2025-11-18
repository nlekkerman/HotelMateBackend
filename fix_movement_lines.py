"""
Fix the stocktake lines that have movements but show 0 purchases
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockMovement, StocktakeLine, Stocktake
from stock_tracker.stocktake_service import _calculate_period_movements

print("=" * 70)
print("FIXING STOCKTAKE LINES WITH MOVEMENTS")
print("=" * 70)

# Get recent movements
movements = StockMovement.objects.order_by('-timestamp')[:10]

print(f"\n📋 Recent Movements:")
for m in movements:
    print(f"\nMovement ID {m.id}:")
    print(f"  Item: {m.item.sku} - {m.item.name}")
    print(f"  Type: {m.movement_type}, Qty: {m.quantity}")
    print(f"  Timestamp: {m.timestamp}")
    print(f"  Reference: {m.reference}")
    
    # Find stocktake from reference
    if 'Stocktake-' in m.reference:
        stocktake_id = m.reference.split('-')[1]
        try:
            stocktake = Stocktake.objects.get(id=stocktake_id)
            print(f"  Stocktake: {stocktake.id} ({stocktake.period_start} to {stocktake.period_end})")
            
            # Find the line for this item
            try:
                line = StocktakeLine.objects.get(
                    stocktake=stocktake,
                    item=m.item
                )
                print(f"  Line ID: {line.id}")
                print(f"  Current purchases on line: {line.purchases}")
                print(f"  Current waste on line: {line.waste}")
                
                # Recalculate
                print(f"\n  🔧 Recalculating...")
                movements_calc = _calculate_period_movements(
                    line.item,
                    stocktake.period_start,
                    stocktake.period_end
                )
                
                print(f"  Calculated purchases: {movements_calc['purchases']}")
                print(f"  Calculated waste: {movements_calc['waste']}")
                
                # Update line
                line.purchases = movements_calc['purchases']
                line.waste = movements_calc['waste']
                line.save()
                
                print(f"  ✅ Line updated!")
                print(f"  New purchases: {line.purchases}")
                print(f"  Expected qty: {line.expected_qty}")
                
            except StocktakeLine.DoesNotExist:
                print(f"  ⚠️ No line found for this item in this stocktake")
                
        except Stocktake.DoesNotExist:
            print(f"  ⚠️ Stocktake {stocktake_id} not found")

print("\n" + "=" * 70)
print("✅ DONE - Check the stocktake lines now!")
print("=" * 70)
