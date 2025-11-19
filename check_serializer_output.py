import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine
from stock_tracker.stock_serializers import StocktakeLineSerializer

# Get the Monin Chocolate Cookie line from March stocktake
from stock_tracker.models import Stocktake
from datetime import date
march_stocktake = Stocktake.objects.filter(
    period_start=date(2025, 3, 1),
    period_end=date(2025, 3, 31)
).first()
if march_stocktake:
    line = StocktakeLine.objects.filter(
        stocktake=march_stocktake,
        item__sku='M0006'
    ).first()
else:
    line = None

if not line:
    print("❌ Line not found")
else:
    print(f"\n{'='*80}")
    print(f"SERIALIZER OUTPUT for {line.item.name} (SKU: {line.item.sku})")
    print(f"{'='*80}")
    
    # Serialize the line
    serializer = StocktakeLineSerializer(line)
    data = serializer.data
    
    # Check the critical fields
    print(f"\nRAW MODEL PROPERTIES:")
    print(f"  counted_full_units (DB):    {line.counted_full_units}")
    print(f"  counted_partial_units (DB): {line.counted_partial_units}")
    print(f"  counted_qty (property):     {line.counted_qty}")
    print(f"  expected_qty (property):    {line.expected_qty}")
    print(f"  variance_qty (property):    {line.variance_qty}")
    
    print(f"\nSERIALIZER OUTPUT:")
    print(f"  counted_qty:                    {data.get('counted_qty')}")
    print(f"  expected_qty:                   {data.get('expected_qty')}")
    print(f"  variance_qty:                   {data.get('variance_qty')}")
    print(f"  variance_display_full_units:    {data.get('variance_display_full_units')}")
    print(f"  variance_display_partial_units: {data.get('variance_display_partial_units')}")
    
    print(f"\nItem Details:")
    print(f"  UOM: {line.item.uom}")
    print(f"  Subcategory: {line.item.subcategory}")
