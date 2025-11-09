import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod

print("\n" + "="*80)
print("CLOSED PERIODS CHECK")
print("="*80 + "\n")

# Get all closed periods
closed_periods = StockPeriod.objects.filter(is_closed=True).order_by('-end_date')

if not closed_periods.exists():
    print("❌ NO CLOSED PERIODS FOUND")
else:
    print(f"✅ Found {closed_periods.count()} closed period(s)\n")
    
    for period in closed_periods:
        print(f"\n{'='*80}")
        print(f"Period ID: {period.id}")
        print(f"Period: {period.start_date} to {period.end_date}")
        print(f"Hotel: {period.hotel.name}")
        print(f"Status: {'🔒 CLOSED' if period.is_closed else '🔓 OPEN'}")
        print(f"-" * 80)
        
        # Closing info
        print(f"Closed At: {period.closed_at}")
        print(f"Closed By: {period.closed_by.user.username if period.closed_by else 'N/A'}")
        
        # Reopening info
        if period.reopened_at:
            print(f"Reopened At: {period.reopened_at}")
            print(f"Reopened By: {period.reopened_by.user.username if period.reopened_by else 'N/A'}")
        else:
            print(f"Reopened At: Never")
            print(f"Reopened By: N/A")
        
        print(f"-" * 80)
        
        # Stocktake info
        try:
            stocktake = period.stocktake
            print(f"Stocktake ID: {stocktake.id}")
            print(f"Stocktake Status: {stocktake.status}")
            print(f"Total Lines: {stocktake.stocktakeline_set.count()}")
            
            # Count items
            counted = stocktake.stocktakeline_set.filter(counted_quantity__gt=0).count()
            zero = stocktake.stocktakeline_set.filter(counted_quantity=0).count()
            
            print(f"Items Counted: {counted}")
            print(f"Items at Zero: {zero}")
            
            # Approval info
            if stocktake.approved_at:
                print(f"Approved At: {stocktake.approved_at}")
                print(f"Approved By: {stocktake.approved_by.user.username if stocktake.approved_by else 'N/A'}")
            else:
                print(f"Approved: Not yet")
            
            # Financial summary
            total_cogs = sum(
                line.counted_quantity * line.ingredient.cost_per_unit 
                for line in stocktake.stocktakeline_set.all()
            )
            
            print(f"-" * 80)
            print(f"💰 Total COGS: €{total_cogs:,.2f}")
            
        except Exception as e:
            print(f"⚠️ No stocktake linked: {e}")

print("\n" + "="*80)
print("END OF REPORT")
print("="*80 + "\n")
