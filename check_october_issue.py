import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake

print("\n" + "="*80)
print("OCTOBER 2025 PERIOD CHECK")
print("="*80 + "\n")

# Get October 2025 period
try:
    period = StockPeriod.objects.get(period_name="October 2025")
    
    print(f"Period ID: {period.id}")
    print(f"Name: {period.period_name}")
    print(f"Period: {period.start_date} to {period.end_date}")
    print(f"Hotel: {period.hotel.name}")
    print(f"-" * 80)
    
    print(f"\n📊 STATUS:")
    print(f"  is_closed: {period.is_closed}")
    print(f"  closed_at: {period.closed_at}")
    print(f"  closed_by: {period.closed_by}")
    print(f"  reopened_at: {period.reopened_at}")
    print(f"  reopened_by: {period.reopened_by}")
    
    print(f"\n⚠️ ISSUE DETECTED:")
    if period.reopened_at and not period.closed_at:
        print("  ❌ Period has reopened_at but NO closed_at!")
        print("  ❌ This is inconsistent - can't reopen what was never closed")
        print("\n💡 RECOMMENDATION:")
        print("  This period was never properly closed.")
        print("  The reopened_at/reopened_by should be cleared.")
    
    # Check stocktake
    print(f"\n" + "-" * 80)
    print("STOCKTAKE INFO:")
    try:
        stocktake = Stocktake.objects.get(
            hotel=period.hotel,
            period_start=period.start_date,
            period_end=period.end_date
        )
        print(f"  Stocktake ID: {stocktake.id}")
        print(f"  Status: {stocktake.status}")
        print(f"  Lines: {stocktake.stocktakeline_set.count()}")
        print(f"  Approved at: {stocktake.approved_at}")
        print(f"  Approved by: {stocktake.approved_by}")
    except Stocktake.DoesNotExist:
        print("  ❌ No stocktake found")
        
except StockPeriod.DoesNotExist:
    print("❌ October 2025 period not found")

print("\n" + "="*80)
print("FIX RECOMMENDATION")
print("="*80)
print("Option 1: Clear reopened_at and reopened_by (period was never closed)")
print("Option 2: Set closed_at and closed_by (if period should be closed)")
print("="*80 + "\n")
