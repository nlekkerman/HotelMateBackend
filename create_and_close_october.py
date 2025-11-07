"""
Create and Close October 2024 Stocktake Period

This script will:
1. Create October 2024 period
2. Verify all stock snapshots are linked to it
3. Close the period
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
from datetime import date


def create_and_close_october():
    """Create October 2024 period and close it"""
    
    print("=" * 60)
    print("CREATE & CLOSE OCTOBER 2024 STOCKTAKE PERIOD")
    print("=" * 60)
    
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hotel found!")
            return
        
        print(f"\n🏨 Hotel: {hotel.name}")
        
        # Create October 2024 period
        print(f"\n📅 Creating October 2024 Period...")
        period, created = StockPeriod.create_monthly_period(hotel, 2024, 10)
        
        if created:
            print(f"  ✅ Created: {period.period_name}")
        else:
            print(f"  ℹ️  Already exists: {period.period_name}")
        
        print(f"\n  Period Details:")
        print(f"  - Start Date: {period.start_date}")
        print(f"  - End Date: {period.end_date}")
        print(f"  - Type: {period.period_type}")
        print(f"  - Status: {'CLOSED' if period.is_closed else 'OPEN'}")
        
        # Check if snapshots exist for this period
        existing_snapshots = StockSnapshot.objects.filter(hotel=hotel, period=period)
        
        if existing_snapshots.exists():
            print(f"\n✅ Found {existing_snapshots.count()} existing snapshots")
        else:
            print(f"\n⚠️  No snapshots found for this period!")
            print(f"   You may need to run the upload scripts first.")
            return
        
        # Display summary by category
        print(f"\n📊 Stocktake Summary:")
        
        categories = StockCategory.objects.all().order_by('code')
        total_value = Decimal('0.00')
        
        for category in categories:
            cat_snapshots = existing_snapshots.filter(item__category=category)
            cat_count = cat_snapshots.count()
            cat_value = sum(s.closing_stock_value for s in cat_snapshots)
            total_value += cat_value
            
            if cat_count > 0:
                print(f"\n  {category.code} - {category.name}:")
                print(f"    Items: {cat_count}")
                print(f"    Value: €{cat_value:,.2f}")
        
        print(f"\n  {'='*56}")
        print(f"  Total Items: {existing_snapshots.count()}")
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
        print(f"Date: {date.today()}")
        print(f"Total Snapshots: {existing_snapshots.count()}")
        print(f"Total Stock Value: €{total_value:,.2f}")
        
        print(f"\n🎉 October 2024 stocktake period successfully finalized!")
        print(f"   This period is now closed and ready for reporting.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    create_and_close_october()
