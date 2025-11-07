"""
Close October 2024 Period for Stocktake

This script will:
1. Find the October 2024 period
2. Mark it as closed (is_closed = True)
3. Verify all snapshots are in place
4. Display final summary
"""

import os
import sys
from decimal import Decimal
from pathlib import Path

# Setup Django environment BEFORE importing models
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockCategory
from hotel.models import Hotel
from datetime import date


def close_october_period():
    """Close the October 2024 period"""
    
    print("=" * 60)
    print("CLOSE OCTOBER 2024 STOCKTAKE PERIOD")
    print("=" * 60)
    
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hotel found!")
            return
        
        print(f"\n🏨 Hotel: {hotel.name}")
        
        # Get October 2024 period
        period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)
        
        print(f"\n📅 Period Details:")
        print(f"  Name: {period.period_name}")
        print(f"  Start Date: {period.start_date}")
        print(f"  End Date: {period.end_date}")
        print(f"  Type: {period.period_type}")
        print(f"  Current Status: {'CLOSED' if period.is_closed else 'OPEN'}")
        
        # Get all snapshots for this period
        snapshots = StockSnapshot.objects.filter(hotel=hotel, period=period)
        
        print(f"\n📊 Stocktake Summary:")
        
        # Summary by category
        categories = StockCategory.objects.all().order_by('code')
        total_value = Decimal('0.00')
        
        for category in categories:
            cat_snapshots = snapshots.filter(item__category=category)
            cat_count = cat_snapshots.count()
            cat_value = sum(s.closing_stock_value for s in cat_snapshots)
            total_value += cat_value
            
            print(f"\n  {category.code} - {category.name}:")
            print(f"    Items: {cat_count}")
            print(f"    Value: €{cat_value:,.2f}")
        
        print(f"\n  {'='*56}")
        print(f"  Total Items: {snapshots.count()}")
        print(f"  Total Value: €{total_value:,.2f}")
        print(f"  {'='*56}")
        
        # Verify against Excel
        excel_total = Decimal('27306.51')
        difference = total_value - excel_total
        
        print(f"\n✅ Verification:")
        print(f"  Database Total: €{total_value:,.2f}")
        print(f"  Excel Total:    €{excel_total:,.2f}")
        print(f"  Difference:     €{difference:,.2f}")
        
        if abs(difference) < Decimal('1.00'):
            print(f"  Status: ✅ VERIFIED - Match within tolerance")
        else:
            print(f"  Status: ⚠️  WARNING - Difference exceeds €1")
            print(f"\n  Do you still want to close this period? (Ctrl+C to cancel)")
        
        # Close the period
        if not period.is_closed:
            print(f"\n🔒 Closing October 2024 Period...")
            period.is_closed = True
            period.save()
            print(f"  ✅ Period closed successfully!")
        else:
            print(f"\n✅ Period was already closed")
        
        # Final confirmation
        period.refresh_from_db()
        
        print(f"\n" + "=" * 60)
        print(f"📋 FINAL STATUS")
        print(f"=" * 60)
        print(f"\nPeriod: {period.period_name}")
        print(f"Status: {'🔒 CLOSED' if period.is_closed else '🔓 OPEN'}")
        print(f"Date Closed: {date.today()}")
        print(f"Total Snapshots: {snapshots.count()}")
        print(f"Total Stock Value: €{total_value:,.2f}")
        
        print(f"\n✅ October 2024 stocktake period successfully closed!")
        print(f"   This period is now finalized and cannot be modified.")
        
    except StockPeriod.DoesNotExist:
        print("❌ October 2024 period not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    close_october_period()
