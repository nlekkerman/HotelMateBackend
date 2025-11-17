import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from datetime import date

# Delete October stocktake
oct_stocktake = Stocktake.objects.filter(
    hotel__name='Hotel Killarney',
    period_start__year=2025,
    period_start__month=10
).first()

if oct_stocktake:
    lines_count = oct_stocktake.lines.count()
    print(f"Found October stocktake: ID {oct_stocktake.id}, Status: {oct_stocktake.status}, Lines: {lines_count}")
    oct_stocktake.delete()
    print(f"✅ October stocktake deleted")
else:
    print("No October stocktake found")

# Set September opening stock to 0
sept_stocktake = Stocktake.objects.filter(
    hotel__name='Hotel Killarney',
    period_start__year=2025,
    period_start__month=9
).first()

if sept_stocktake:
    print(f"\nFound September stocktake: ID {sept_stocktake.id}, Status: {sept_stocktake.status}")
    lines = StocktakeLine.objects.filter(stocktake=sept_stocktake)
    print(f"Total lines: {lines.count()}")
    
    # Update opening_qty to 0 for all lines
    updated = lines.update(opening_qty=0)
    print(f"✅ Set opening_qty to 0 for {updated} lines")
    
    # Show sample
    sample_lines = StocktakeLine.objects.filter(stocktake=sept_stocktake).select_related('item')[:5]
    print("\nSample lines after update:")
    for line in sample_lines:
        print(f"  {line.item.sku}: opening_qty={line.opening_qty}, counted={line.counted_full_units}+{line.counted_partial_units}")
else:
    print("No September stocktake found")
