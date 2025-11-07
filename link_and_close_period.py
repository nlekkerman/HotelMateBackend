"""
Link all existing snapshots to October 2024 period and close it
"""

import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockCategory
from hotel.models import Hotel


def link_and_close():
    """Link snapshots to period and close it"""
    
    print("=" * 60)
    print("LINK SNAPSHOTS & CLOSE OCTOBER 2024 PERIOD")
    print("=" * 60)
    
    hotel = Hotel.objects.first()
    print(f"\n🏨 Hotel: {hotel.name}")
    
    # Get the October 2024 period
    period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)
    print(f"📅 Period: {period.period_name}")
    
    # Find all snapshots without a period or with old period
    all_snapshots = StockSnapshot.objects.filter(hotel=hotel)
    print(f"\n📊 Total snapshots in database: {all_snapshots.count()}")
    
    # Update all snapshots to link to this period
    print(f"\n🔗 Linking snapshots to {period.period_name}...")
    updated = all_snapshots.update(period=period)
    print(f"  ✅ Updated {updated} snapshots")
    
    # Verify snapshots are now linked
    period_snapshots = StockSnapshot.objects.filter(hotel=hotel, period=period)
    print(f"\n✅ Verification: {period_snapshots.count()} snapshots linked to period")
    
    # Calculate totals by category
    print(f"\n📊 Stocktake Summary:")
    
    categories = StockCategory.objects.all().order_by('code')
    total_value = Decimal('0.00')
    
    for category in categories:
        cat_snapshots = period_snapshots.filter(item__category=category)
        cat_count = cat_snapshots.count()
        cat_value = sum(s.closing_stock_value for s in cat_snapshots)
        total_value += cat_value
        
        if cat_count > 0:
            print(f"\n  {category.code} - {category.name}:")
            print(f"    Items: {cat_count}")
            print(f"    Value: €{cat_value:,.2f}")
    
    print(f"\n  {'='*56}")
    print(f"  Total Items: {period_snapshots.count()}")
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
    if not period.is_closed:
        print(f"\n🔒 Closing October 2024 Period...")
        period.is_closed = True
        period.save()
        print(f"  ✅ Period closed successfully!")
    else:
        print(f"\n✅ Period was already closed")
    
    # Final status
    period.refresh_from_db()
    
    print(f"\n" + "=" * 60)
    print(f"📋 FINAL STATUS")
    print(f"=" * 60)
    print(f"\nPeriod: {period.period_name} (ID: {period.id})")
    print(f"Status: {'🔒 CLOSED' if period.is_closed else '🔓 OPEN'}")
    print(f"Date Range: {period.start_date} to {period.end_date}")
    print(f"Snapshots: {period_snapshots.count()} items")
    print(f"Total Value: €{total_value:,.2f}")
    
    print(f"\n🎉 October 2024 stocktake successfully finalized!")
    print(f"   All stock data is now locked and ready for reporting.")


if __name__ == '__main__':
    link_and_close()
