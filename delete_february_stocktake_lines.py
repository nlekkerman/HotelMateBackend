"""
Delete February 2025 stocktake lines so it can be repopulated with the fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from datetime import date

print(f"\n{'='*80}")
print("DELETE FEBRUARY 2025 STOCKTAKE LINES")
print(f"{'='*80}\n")

# Find February 2025 stocktake
try:
    feb_stocktake = Stocktake.objects.get(
        period_start=date(2025, 2, 1),
        period_end=date(2025, 2, 28)
    )
    
    lines_count = feb_stocktake.lines.count()
    
    print(f"Found February 2025 stocktake:")
    print(f"  ID: {feb_stocktake.id}")
    print(f"  Status: {feb_stocktake.status}")
    print(f"  Total lines: {lines_count}\n")
    
    if lines_count == 0:
        print("✓ No lines to delete - stocktake is already empty")
    else:
        # Delete all lines
        feb_stocktake.lines.all().delete()
        print(f"✅ Deleted {lines_count} stocktake lines")
        print(f"\nYou can now repopulate the stocktake to see the fix in action!")
    
except Stocktake.DoesNotExist:
    print("❌ February 2025 stocktake not found")
    print("You may need to create it first via the API or frontend")

print(f"\n{'='*80}\n")
