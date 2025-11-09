import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake

print("\n" + "="*80)
print("ALL PERIODS CHECK")
print("="*80 + "\n")

# Get all periods
all_periods = StockPeriod.objects.all().order_by('-end_date')

if not all_periods.exists():
    print("❌ NO PERIODS FOUND AT ALL")
else:
    print(f"✅ Found {all_periods.count()} period(s) total\n")
    
    for period in all_periods:
        print(f"\n{'='*80}")
        print(f"Period ID: {period.id}")
        print(f"Name: {period.period_name}")
        print(f"Period: {period.start_date} to {period.end_date}")
        print(f"Hotel: {period.hotel.name}")
        print(f"Type: {period.period_type}")
        print(f"Status: {'🔒 CLOSED' if period.is_closed else '🔓 OPEN'}")
        print(f"-" * 80)
        
        # Closing info
        if period.closed_at:
            print(f"Closed At: {period.closed_at}")
            print(f"Closed By: {period.closed_by.user.username if period.closed_by else 'N/A'}")
        else:
            print(f"Never Closed")
        
        # Reopening info
        if period.reopened_at:
            print(f"Reopened At: {period.reopened_at}")
            reopened_by_name = period.reopened_by.user.username if period.reopened_by else 'N/A'
            print(f"Reopened By: {reopened_by_name}")
        
        print(f"-" * 80)
        
        # Stocktake info
        try:
            stocktake = Stocktake.objects.get(
                hotel=period.hotel,
                period_start=period.start_date,
                period_end=period.end_date
            )
            print(f"✅ Stocktake ID: {stocktake.id}")
            print(f"   Status: {stocktake.status}")
            print(f"   Total Lines: {stocktake.stocktakeline_set.count()}")
            
            # Count items
            lines = stocktake.stocktakeline_set.all()
            counted = sum(1 for line in lines if line.counted_quantity > 0)
            zero = sum(1 for line in lines if line.counted_quantity == 0)
            
            print(f"   Items Counted: {counted}")
            print(f"   Items at Zero: {zero}")
            
            # Approval info
            if stocktake.approved_at:
                print(f"   Approved At: {stocktake.approved_at}")
                approved_by = stocktake.approved_by.user.username if stocktake.approved_by else 'N/A'
                print(f"   Approved By: {approved_by}")
            else:
                print(f"   Approved: Not yet")
            
            # Financial summary
            total_cogs = sum(
                line.counted_quantity * line.ingredient.cost_per_unit 
                for line in lines
            )
            
            print(f"   💰 Total COGS: €{total_cogs:,.2f}")
            
        except Stocktake.DoesNotExist:
            print(f"⚠️ No stocktake found for this period")
        except Exception as e:
            print(f"⚠️ Error loading stocktake: {e}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
open_count = all_periods.filter(is_closed=False).count()
closed_count = all_periods.filter(is_closed=True).count()
print(f"🔓 Open Periods: {open_count}")
print(f"🔒 Closed Periods: {closed_count}")
print(f"📊 Total Periods: {all_periods.count()}")
print("="*80 + "\n")
