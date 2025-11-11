"""
Debug script to check why consumption records aren't found in the period.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    CocktailIngredientConsumption,
    Stocktake,
    StocktakeLine,
    Ingredient
)
from hotel.models import Hotel

hotel = Hotel.objects.first()
vodka = Ingredient.objects.filter(
    hotel=hotel,
    name="Vodka",
    linked_stock_item__isnull=False
).first()

if vodka:
    print(f"Vodka linked to: {vodka.linked_stock_item.sku}")
    
    # Get all unmerged consumption
    all_consumption = CocktailIngredientConsumption.objects.filter(
        stock_item=vodka.linked_stock_item,
        is_merged_to_stocktake=False
    )
    
    print(f"\nTotal unmerged consumption for {vodka.linked_stock_item.sku}: {all_consumption.count()}")
    
    for c in all_consumption:
        print(f"  ID: {c.id}")
        print(f"  Timestamp: {c.timestamp}")
        print(f"  Timestamp type: {type(c.timestamp)}")
        print(f"  Quantity: {c.quantity_used}ml")
        print()
    
    # Get stocktake
    stocktake = Stocktake.objects.filter(
        hotel=hotel,
        status='DRAFT'
    ).first()
    
    if stocktake:
        print(f"Stocktake ID: {stocktake.id}")
        print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
        print(f"Period start type: {type(stocktake.period_start)}")
        print(f"Period end type: {type(stocktake.period_end)}")
        
        # Try the query manually
        from django.utils import timezone
        from datetime import datetime
        
        # Convert dates to datetime with timezone
        start_dt = timezone.make_aware(
            datetime.combine(stocktake.period_start, datetime.min.time())
        )
        end_dt = timezone.make_aware(
            datetime.combine(stocktake.period_end, datetime.max.time())
        )
        
        print(f"\nConverted to datetime:")
        print(f"Start: {start_dt}")
        print(f"End: {end_dt}")
        
        # Query with datetime range
        found = CocktailIngredientConsumption.objects.filter(
            stock_item=vodka.linked_stock_item,
            is_merged_to_stocktake=False,
            timestamp__gte=start_dt,
            timestamp__lte=end_dt
        )
        
        print(f"\nFound with datetime range: {found.count()}")
        
        # Get the line
        line = stocktake.lines.filter(item=vodka.linked_stock_item).first()
        if line:
            print(f"\nLine ID: {line.id}")
            available = line.get_available_cocktail_consumption()
            print(f"Available via line method: {available.count()}")
