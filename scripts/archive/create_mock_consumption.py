"""
Create mock cocktail consumption data within stocktake period for testing merge.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from django.utils import timezone
from stock_tracker.models import (
    Ingredient,
    CocktailRecipe,
    RecipeIngredient,
    CocktailConsumption,
    StockItem,
    Stocktake
)
from hotel.models import Hotel


def create_mock_consumption():
    """Create cocktail consumption within existing stocktake period"""
    
    print("=" * 70)
    print("  Creating Mock Cocktail Consumption for Testing")
    print("=" * 70)
    
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found!")
        return
    
    print(f"✓ Using hotel: {hotel.name}")
    
    # Get vodka with linked stock item
    vodka = Ingredient.objects.filter(
        hotel=hotel,
        name="Vodka",
        linked_stock_item__isnull=False
    ).first()
    
    if not vodka:
        print("❌ No Vodka ingredient with linked stock item found!")
        print("   Run test_cocktail_consumption.py first")
        return
    
    print(f"✓ Found Vodka linked to: {vodka.linked_stock_item.sku}")
    
    # Get existing stocktake
    stocktake = Stocktake.objects.filter(
        hotel=hotel,
        status='DRAFT'
    ).order_by('-created_at').first()
    
    if not stocktake:
        print("❌ No DRAFT stocktake found!")
        return
    
    print(f"✓ Using stocktake ID: {stocktake.id}")
    print(f"  - Period: {stocktake.period_start} to {stocktake.period_end}")
    
    # Check if stocktake has vodka line
    has_vodka_line = stocktake.lines.filter(
        item=vodka.linked_stock_item
    ).exists()
    
    if not has_vodka_line:
        print("❌ Stocktake doesn't have a line for Vodka stock item!")
        print("   Creating line...")
        from stock_tracker.models import StocktakeLine
        
        line = StocktakeLine.objects.create(
            stocktake=stocktake,
            item=vodka.linked_stock_item,
            opening_qty=Decimal('100'),
            counted_full_units=Decimal('5'),
            counted_partial_units=Decimal('50'),
            valuation_cost=vodka.linked_stock_item.unit_cost
        )
        print(f"✓ Created stocktake line ID: {line.id}")
    else:
        print(f"✓ Stocktake already has vodka line")
    
    # Get or create Cosmopolitan recipe
    cosmopolitan, _ = CocktailRecipe.objects.get_or_create(
        name="Cosmopolitan",
        hotel=hotel,
        defaults={'price': Decimal('12.50')}
    )
    
    # Clear and recreate recipe
    cosmopolitan.ingredients.all().delete()
    
    RecipeIngredient.objects.create(
        cocktail=cosmopolitan,
        ingredient=vodka,
        quantity_per_cocktail=45
    )
    
    print(f"✓ Recipe ready: {cosmopolitan.name} (45ml vodka per cocktail)")
    
    # Calculate date within stocktake period (middle of period)
    from datetime import timedelta
    
    period_start = timezone.make_aware(
        timezone.datetime.combine(stocktake.period_start, timezone.datetime.min.time())
    )
    period_end = timezone.make_aware(
        timezone.datetime.combine(stocktake.period_end, timezone.datetime.min.time())
    )
    
    # Use middle of period
    period_duration = (period_end - period_start).days
    consumption_date = period_start + timedelta(days=period_duration // 2)
    
    print(f"\n✓ Creating consumption on: {consumption_date.date()}")
    
    # Create cocktail consumption
    quantity = 10
    consumption = CocktailConsumption.objects.create(
        cocktail=cosmopolitan,
        quantity_made=quantity,
        hotel=hotel,
        unit_price=cosmopolitan.price
    )
    
    # Update timestamp to be within period
    consumption.timestamp = consumption_date
    consumption.save()
    
    print(f"✓ Created consumption ID: {consumption.id}")
    print(f"  - Cocktails made: {quantity}")
    print(f"  - Timestamp: {consumption.timestamp}")
    
    # Check ingredient consumptions
    ingredient_consumptions = consumption.ingredient_consumptions.all()
    
    print(f"\n✓ Auto-created {ingredient_consumptions.count()} ingredient consumption(s):")
    
    for ic in ingredient_consumptions:
        print(f"  - {ic.ingredient.name}: {ic.quantity_used}ml")
        print(f"    Stock Item: {ic.stock_item.sku if ic.stock_item else 'None'}")
        print(f"    Can merge: {ic.can_be_merged}")
    
    # Verify it's in the stocktake period
    vodka_consumption = ingredient_consumptions.filter(
        stock_item=vodka.linked_stock_item
    ).first()
    
    if vodka_consumption:
        line = stocktake.lines.get(item=vodka.linked_stock_item)
        available = line.get_available_cocktail_consumption()
        
        print(f"\n✓ Stocktake line now has {available.count()} unmerged consumption(s)")
        print(f"  - Total quantity: {sum(c.quantity_used for c in available)}ml")
        
        print("\n" + "=" * 70)
        print("  SUCCESS! Ready to test merge endpoints")
        print("=" * 70)
        print(f"\nRun: python test_merge_endpoints.py")
    else:
        print("\n⚠ Warning: Vodka consumption not linked to stock item")


if __name__ == "__main__":
    try:
        create_mock_consumption()
    except Exception as e:
        print(f"\n❌ Failed:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
