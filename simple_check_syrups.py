"""
Simple check of syrup data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, Stocktake

february = Stocktake.objects.filter(
    hotel_id=2,
    period_start__month=2,
    period_start__year=2025
).first()

if february:
    syrup_lines = StocktakeLine.objects.filter(
        stocktake=february,
        item__subcategory='SYRUPS'
    ).select_related('item')[:3]
    
    for line in syrup_lines:
        print(f"\nSKU: {line.item.sku}")
        print(f"Name: {line.item.name}")
        print(f"counted_full_units: {line.counted_full_units}")
        print(f"counted_partial_units: {line.counted_partial_units}")
