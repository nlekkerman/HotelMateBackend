"""
Create October 2025 Stocktake Period (Closed)
Uses existing StockItem data to create snapshots
"""
import os
import sys
import django
from pathlib import Path
from datetime import date
from decimal import Decimal

sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel


def main():
    print("=" * 60)
    print("CREATE OCTOBER 2025 STOCKTAKE (CLOSED)")
    print("=" * 60)
    
    hotel = Hotel.objects.first()
    print(f"\n🏨 Hotel: {hotel.name}\n")
    
    # Create October 2025 period
    print("📅 Creating October 2025 Period...")
    period, created = StockPeriod.objects.get_or_create(
        hotel=hotel,
        month="October",
        year=2025,
        defaults={
            'status': 'closed',
            'start_date': date(2025, 10, 1),
            'end_date': date(2025, 10, 31)
        }
    )
    
    if created:
        print(f"✅ Created: October 2025 (ID: {period.id})")
    else:
        print(f"⚠️  Already exists: October 2025 (ID: {period.id})")
        print(f"   Status: {period.status}")
    
    # Get all stock items
    items = StockItem.objects.filter(hotel=hotel)
    total_items = items.count()
    
    print(f"\n📦 Found {total_items} stock items")
    print("\n🔄 Creating snapshots...\n")
    
    created_count = 0
    updated_count = 0
    total_value = Decimal('0.00')
    
    for item in items:
        # Use current stock as October closing stock
        # (In real scenario, this would be actual counted values)
        snapshot, was_created = StockSnapshot.objects.update_or_create(
            hotel=hotel,
            item=item,
            period=period,
            defaults={
                'closing_full_units': item.current_full_units or Decimal('0'),
                'closing_partial_units': item.current_partial_units or Decimal('0'),
                'unit_cost': item.unit_cost,
                'cost_per_serving': item.cost_per_serving,
                'closing_stock_value': item.total_stock_value
            }
        )
        
        if was_created:
            created_count += 1
        else:
            updated_count += 1
        
        total_value += snapshot.closing_stock_value
        
        # Show progress every 50 items
        if (created_count + updated_count) % 50 == 0:
            print(f"  Processed {created_count + updated_count}/{total_items}...")
    
    print("\n" + "=" * 60)
    print("✅ OCTOBER 2025 STOCKTAKE CREATED")
    print("=" * 60)
    print(f"""
Period ID: {period.id}
Month: {period.month} {period.year}
Status: {period.status}
Date Range: {period.start_date} to {period.end_date}

Snapshots Created: {created_count}
Snapshots Updated: {updated_count}
Total Items: {total_items}
Total Stock Value: €{total_value:,.2f}

This period is now CLOSED and ready to use as reference for November 2025.
""")


if __name__ == '__main__':
    main()
