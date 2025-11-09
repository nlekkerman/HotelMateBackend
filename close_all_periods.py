import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake
from staff.models import Staff

print("\n" + "="*80)
print("CLOSING ALL PERIODS AND APPROVING ALL STOCKTAKES")
print("="*80 + "\n")

# Get the staff member (Nikola)
try:
    staff = Staff.objects.get(user__username='nikola')
    print(f"✅ Using staff: {staff.user.username}\n")
except Staff.DoesNotExist:
    print("❌ Staff 'nikola' not found. Using first available staff.")
    staff = Staff.objects.first()
    if staff:
        print(f"✅ Using staff: {staff.user.username}\n")
    else:
        print("❌ No staff found in system!")
        exit(1)

# Get all open periods
open_periods = StockPeriod.objects.filter(is_closed=False)

print(f"Found {open_periods.count()} open period(s)\n")
print("="*80)

for period in open_periods:
    print(f"\n📅 Period: {period.period_name}")
    print(f"   Dates: {period.start_date} to {period.end_date}")
    print(f"   Hotel: {period.hotel.name}")
    
    # Close the period
    period.is_closed = True
    period.closed_at = timezone.now()
    period.closed_by = staff
    period.save()
    print(f"   ✅ Period CLOSED")
    
    # Find and approve stocktake
    try:
        stocktake = Stocktake.objects.get(
            hotel=period.hotel,
            period_start=period.start_date,
            period_end=period.end_date
        )
        
        print(f"   📦 Stocktake ID: {stocktake.id}")
        print(f"      Current Status: {stocktake.status}")
        
        if stocktake.status != 'APPROVED':
            stocktake.status = 'APPROVED'
            stocktake.approved_at = timezone.now()
            stocktake.approved_by = staff
            stocktake.save()
            print(f"      ✅ Stocktake APPROVED")
        else:
            print(f"      ℹ️ Already approved")
            
    except Stocktake.DoesNotExist:
        print(f"   ⚠️ No stocktake found for this period")
    
    print(f"   " + "-"*76)

print("\n" + "="*80)
print("SUMMARY - AFTER CLOSING")
print("="*80 + "\n")

all_periods = StockPeriod.objects.all()
closed_count = all_periods.filter(is_closed=True).count()
open_count = all_periods.filter(is_closed=False).count()

print(f"🔒 Closed Periods: {closed_count}")
print(f"🔓 Open Periods: {open_count}")
print(f"📊 Total Periods: {all_periods.count()}")

all_stocktakes = Stocktake.objects.all()
approved_count = all_stocktakes.filter(status='APPROVED').count()
draft_count = all_stocktakes.filter(status='DRAFT').count()

print(f"\n✅ Approved Stocktakes: {approved_count}")
print(f"📝 Draft Stocktakes: {draft_count}")
print(f"📦 Total Stocktakes: {all_stocktakes.count()}")

print("\n" + "="*80)
print("✅ ALL PERIODS AND STOCKTAKES CLOSED/APPROVED")
print("="*80 + "\n")
