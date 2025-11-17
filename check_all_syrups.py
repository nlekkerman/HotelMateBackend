"""
Check all syrup stocktake lines in February
"""
import os
import sys
import django

# Django setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, Stocktake

# Get February stocktake
february = Stocktake.objects.filter(
    hotel_id=2,
    period_start__month=2,
    period_start__year=2025
).first()

if not february:
    print("❌ No February stocktake found")
else:
    print(f"📋 Stocktake #{february.id}")
    print("=" * 80)
    
    # Get ALL syrup lines
    syrup_lines = StocktakeLine.objects.filter(
        stocktake=february,
        item__subcategory='SYRUPS'
    ).select_related('item')
    
    print(f"\nFound {syrup_lines.count()} SYRUP lines\n")
    print("=" * 80)
    
    for line in syrup_lines:
        print(f"{line.item.sku:<10} {line.item.name:<40} "
              f"Full: {line.counted_full_units:>8.2f}  "
              f"Partial: {line.counted_partial_units:>8.2f}  "
              f"UOM: {line.item.uom:>6.0f}ml")
