"""
Create StockSnapshots from StockItems for October 2024 period
"""

import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem, StockCategory
from hotel.models import Hotel


def create_snapshots():
    """Create snapshots from current stock items"""
    
    print("=" * 60)
    print("CREATE OCTOBER 2024 STOCK SNAPSHOTS")
    print("=" * 60)
    
    hotel = Hotel.objects.first()
    print(f"\n🏨 Hotel: {hotel.name}")
    
    # Get the October 2024 period
    period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)
    print(f"📅 Period: {period.period_name}")
    
    # Get all stock items
    items = StockItem.objects.filter(hotel=hotel).select_related('category')
    print(f"\n📦 Found {items.count()} stock items")
    
    # Delete any existing snapshots for this period (cleanup)
    existing = StockSnapshot.objects.filter(hotel=hotel, period=period)
    if existing.exists():
        print(f"  🗑️  Deleting {existing.count()} existing snapshots...")
        existing.delete()
    
    # Create snapshots from items
    print(f"\n📸 Creating snapshots...")
    
    snapshots_created = 0
    total_value = Decimal('0.00')
    
    categories_summary = {}
    
    for item in items:
        # Create snapshot using current stock values
        # These were set by our update scripts
        snapshot = StockSnapshot.objects.create(
            hotel=hotel,
            period=period,
            item=item,
            closing_full_units=item.current_full_units or 0,
            closing_partial_units=item.current_partial_units or Decimal('0.00'),
            unit_cost=item.unit_cost,
            cost_per_serving=item.cost_per_serving,
            closing_stock_value=item.total_stock_value or Decimal('0.00'),
            menu_price=item.menu_price
        )
        
        snapshots_created += 1
        total_value += snapshot.closing_stock_value
        
        # Track by category
        cat_code = item.category.code
        if cat_code not in categories_summary:
            categories_summary[cat_code] = {
                'name': item.category.name,
                'count': 0,
                'value': Decimal('0.00')
            }
        
        categories_summary[cat_code]['count'] += 1
        categories_summary[cat_code]['value'] += snapshot.closing_stock_value
    
    print(f"  ✅ Created {snapshots_created} snapshots")
    
    # Display summary by category
    print(f"\n📊 Stocktake Summary by Category:")
    
    for cat_code in sorted(categories_summary.keys()):
        cat = categories_summary[cat_code]
        print(f"\n  {cat_code} - {cat['name']}:")
        print(f"    Items: {cat['count']}")
        print(f"    Value: €{cat['value']:,.2f}")
    
    print(f"\n  {'='*56}")
    print(f"  Total Items: {snapshots_created}")
    print(f"  Total Value: €{total_value:,.2f}")
    print(f"  {'='*56}")
    
    # Verify against Excel
    excel_total = Decimal('27306.51')
    difference = total_value - excel_total
    
    print(f"\n✅ Verification Against Excel:")
    print(f"  Database Total: €{total_value:,.2f}")
    print(f"  Excel Total:    €{excel_total:,.2f}")
    print(f"  Difference:     €{difference:,.2f}")
    
    if abs(difference) < Decimal('1.00'):
        print(f"  Status: ✅ VERIFIED")
    else:
        print(f"  Status: ⚠️  WARNING - Check values")
    
    # Close the period
    print(f"\n🔒 Closing October 2024 Period...")
    period.is_closed = True
    period.save()
    print(f"  ✅ Period closed successfully!")
    
    # Final status
    print(f"\n" + "=" * 60)
    print(f"📋 FINAL STATUS")
    print(f"=" * 60)
    print(f"\nPeriod: {period.period_name} (ID: {period.id})")
    print(f"Status: 🔒 CLOSED")
    print(f"Date Range: {period.start_date} to {period.end_date}")
    print(f"Snapshots: {snapshots_created} items")
    print(f"Total Value: €{total_value:,.2f}")
    
    print(f"\n🎉 October 2024 stocktake successfully finalized!")
    print(f"   All stock data is now locked and ready for reporting.")


if __name__ == '__main__':
    create_snapshots()
