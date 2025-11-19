import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from datetime import date

# List all stocktakes for March 2025
print("\n" + "="*80)
print("ALL STOCKTAKES FOR MARCH 2025")
print("="*80)

stocktakes = Stocktake.objects.filter(
    period_start=date(2025, 3, 1),
    period_end=date(2025, 3, 31)
)

for st in stocktakes:
    print(f"\nStocktake ID: {st.id}")
    print(f"Hotel: {st.hotel}")
    print(f"Period: {st.period_start} to {st.period_end}")
    print(f"Status: {st.status}")
    
    # Check M0006 in this stocktake
    line = StocktakeLine.objects.filter(
        stocktake=st,
        item__sku='M0006'
    ).first()
    
    if line:
        print(f"\nM0006 (Monin Chocolate Cookie) in this stocktake:")
        print(f"  counted_full_units:   {line.counted_full_units}")
        print(f"  counted_partial_units: {line.counted_partial_units}")
        print(f"  counted_qty:          {line.counted_qty}")
        print(f"  expected_qty:         {line.expected_qty}")
        print(f"  variance_qty:         {line.variance_qty}")
    else:
        print(f"\n  (No M0006 line found in this stocktake)")

print("\n" + "="*80)
