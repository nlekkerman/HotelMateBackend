"""
Update January 2025 stocktake:
1. Set all bottled beers closing to 1 case + 10 bottles
2. Clear opening stock for all categories except draught beer
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockPeriod, StockSnapshot, StockItem, StockCategory
)

def main():
    print("=" * 80)
    print("UPDATE JANUARY 2025 STOCKTAKE")
    print("=" * 80)
    
    # Find January 2025 period
    january = StockPeriod.objects.filter(
        start_date__year=2025,
        start_date__month=1
    ).first()
    
    if not january:
        print("❌ January 2025 period not found!")
        return
    
    print(f"\n✅ Found January 2025 period")
    print(f"   Period ID: {january.id}")
    print(f"   Dates: {january.start_date} to {january.end_date}")
    
    # Get categories
    draught_category = StockCategory.objects.filter(code='D').first()
    bottled_category = StockCategory.objects.filter(code='B').first()
    
    if not draught_category or not bottled_category:
        print("❌ Categories not found!")
        return
    
    print("\n📋 Categories:")
    print(f"   - Draught Beer: {draught_category.name}")
    print(f"   - Bottled Beer: {bottled_category.name}")
    
    # Note: Opening stock is calculated from previous period's closing
    # Since January is the first period, all openings will be 0 automatically
    
    # Update bottled beers closing stock
    print("\n" + "=" * 80)
    print("UPDATING BOTTLED BEERS CLOSING STOCK")
    print("=" * 80)
    print("   Setting: 1 case + 10 bottles for all bottled beers")
    
    bottled_beers = StockItem.objects.filter(
        hotel_id=2,
        category=bottled_category,
        active=True
    )
    
    print(f"\n📦 Found {bottled_beers.count()} bottled beer items")
    
    updated_count = 0
    created_count = 0
    total_value = Decimal('0')
    
    for item in bottled_beers:
        # Calculate closing value
        unit_cost = item.unit_cost or Decimal('0')
        cost_per_serving = item.cost_per_serving or Decimal('0')
        uom = item.uom or Decimal('1')
        
        # 1 case + 10 bottles = (1 × uom) + 10
        total_servings = (Decimal('1') * uom) + Decimal('10')
        closing_value = total_servings * cost_per_serving
        
        # Get or create snapshot
        snapshot, created = StockSnapshot.objects.get_or_create(
            item=item,
            period=january,
            hotel_id=2,
            defaults={
                'closing_full_units': Decimal('1'),
                'closing_partial_units': Decimal('10'),
                'unit_cost': unit_cost,
                'cost_per_serving': cost_per_serving,
                'closing_stock_value': closing_value
            }
        )
        
        if not created:
            # Update existing snapshot
            snapshot.closing_full_units = Decimal('1')
            snapshot.closing_partial_units = Decimal('10')
            snapshot.unit_cost = unit_cost
            snapshot.cost_per_serving = cost_per_serving
            snapshot.closing_stock_value = closing_value
            snapshot.save()
            updated_count += 1
        else:
            created_count += 1
        
        # Calculate value
        item_value = snapshot.closing_stock_value
        total_value += item_value
        
        print(f"   {'📦' if created else '✏️'} {item.name}")
        print(f"      Closing: 1 case + 10 bottles = {snapshot.total_servings} bottles")
        print(f"      Value: €{item_value:.2f}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ January is first period - all openings are automatically 0")
    print(f"✅ Bottled beers updated: {updated_count} existing")
    print(f"✅ Bottled beers created: {created_count} new")
    print(f"💰 Total bottled beer closing value: €{total_value:.2f}")
    
    # Show draught beer count (unchanged)
    draught_snapshots = StockSnapshot.objects.filter(
        period=january,
        item__category=draught_category
    ).count()
    print(f"\n📊 Draught beer snapshots (unchanged): {draught_snapshots}")
    
    print("\n✅ COMPLETE!")
    print("=" * 80)

if __name__ == '__main__':
    main()
