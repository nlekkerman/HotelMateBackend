"""
Test the approve_and_close endpoint locally
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake
from staff.models import Staff

print("\n" + "="*80)
print("TESTING APPROVE_AND_CLOSE FIX")
print("="*80 + "\n")

# Get October 2025 period (should be closed now)
try:
    period = StockPeriod.objects.get(period_name="October 2025")
    print(f"✅ Found period: {period.period_name}")
    print(f"   Status: {'CLOSED' if period.is_closed else 'OPEN'}")
    
    # Check stocktake
    stocktake = Stocktake.objects.get(
        hotel=period.hotel,
        period_start=period.start_date,
        period_end=period.end_date
    )
    print(f"✅ Found stocktake: ID={stocktake.id}")
    print(f"   Status: {stocktake.status}")
    
    print("\n" + "="*80)
    print("BROADCAST FUNCTION SIGNATURE CHECK")
    print("="*80 + "\n")
    
    from stock_tracker.pusher_utils import broadcast_stocktake_status_changed
    import inspect
    
    sig = inspect.signature(broadcast_stocktake_status_changed)
    print(f"Function signature:")
    print(f"  broadcast_stocktake_status_changed{sig}")
    
    print(f"\nParameters:")
    for param_name, param in sig.parameters.items():
        print(f"  - {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")
    
    print("\n✅ The fix should use:")
    print("   broadcast_stocktake_status_changed(")
    print("       hotel_identifier,  # NOT hotel=")
    print("       stocktake_id,")
    print("       stocktake_data_dict")
    print("   )")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80)
print("END OF TEST")
print("="*80 + "\n")
