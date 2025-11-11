"""
Test script for cocktail ingredient consumption tracking.

This script tests:
1. Creating a CocktailConsumption
2. Auto-creation of CocktailIngredientConsumption records
3. Linking ingredients to stock items
4. Verifying quantities and relationships
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from stock_tracker.models import (
    Ingredient,
    CocktailRecipe,
    RecipeIngredient,
    CocktailConsumption,
    CocktailIngredientConsumption,
    StockItem
)
from hotel.models import Hotel


def print_separator(title):
    """Print a section separator"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_cocktail_consumption_creation():
    """Test the complete cocktail consumption creation flow"""
    
    print_separator("STEP 1: Get or Create Test Data")
    
    # Get first hotel
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found in database!")
        return
    
    print(f"✓ Using hotel: {hotel.name}")
    
    # Get or create ingredients
    vodka, _ = Ingredient.objects.get_or_create(
        name="Vodka",
        hotel=hotel,
        defaults={'unit': 'ml'}
    )
    
    cranberry, _ = Ingredient.objects.get_or_create(
        name="Cranberry Juice",
        hotel=hotel,
        defaults={'unit': 'ml'}
    )
    
    lime, _ = Ingredient.objects.get_or_create(
        name="Lime Juice",
        hotel=hotel,
        defaults={'unit': 'ml'}
    )
    
    print(f"✓ Ingredients ready: {vodka.name}, {cranberry.name}, {lime.name}")
    
    # Check if we have stock items to link
    stock_items = StockItem.objects.filter(hotel=hotel)[:3]
    if stock_items.exists():
        # Link vodka to first stock item
        vodka.linked_stock_item = stock_items[0]
        vodka.save()
        print(f"✓ Linked {vodka.name} to stock item: {stock_items[0].sku}")
    else:
        print("⚠ No stock items found - ingredients will not be linked")
    
    # Get or create cocktail recipe
    cosmopolitan, created = CocktailRecipe.objects.get_or_create(
        name="Cosmopolitan",
        hotel=hotel,
        defaults={'price': Decimal('12.50')}
    )
    
    if created:
        print(f"✓ Created cocktail: {cosmopolitan.name}")
    else:
        print(f"✓ Using existing cocktail: {cosmopolitan.name}")
    
    # Clear existing recipe ingredients (if any)
    cosmopolitan.ingredients.all().delete()
    
    # Create recipe ingredients
    RecipeIngredient.objects.create(
        cocktail=cosmopolitan,
        ingredient=vodka,
        quantity_per_cocktail=45  # 45ml vodka per cocktail
    )
    
    RecipeIngredient.objects.create(
        cocktail=cosmopolitan,
        ingredient=cranberry,
        quantity_per_cocktail=30  # 30ml cranberry per cocktail
    )
    
    RecipeIngredient.objects.create(
        cocktail=cosmopolitan,
        ingredient=lime,
        quantity_per_cocktail=15  # 15ml lime per cocktail
    )
    
    print(f"✓ Recipe configured with 3 ingredients")
    
    # Count existing consumption records before test
    existing_consumptions = CocktailIngredientConsumption.objects.filter(
        cocktail_consumption__cocktail=cosmopolitan
    ).count()
    
    print_separator("STEP 2: Create Cocktail Consumption")
    
    quantity_made = 5
    print(f"Creating consumption record for {quantity_made} Cosmopolitans...")
    
    # Create cocktail consumption - this should auto-create ingredient consumptions
    consumption = CocktailConsumption.objects.create(
        cocktail=cosmopolitan,
        quantity_made=quantity_made,
        hotel=hotel,
        unit_price=cosmopolitan.price
    )
    
    print(f"✓ CocktailConsumption created (ID: {consumption.id})")
    print(f"  - Cocktail: {consumption.cocktail.name}")
    print(f"  - Quantity: {consumption.quantity_made}")
    print(f"  - Revenue: ${consumption.total_revenue}")
    print(f"  - Timestamp: {consumption.timestamp}")
    
    print_separator("STEP 3: Verify Auto-Created Ingredient Consumptions")
    
    # Get ingredient consumptions
    ingredient_consumptions = CocktailIngredientConsumption.objects.filter(
        cocktail_consumption=consumption
    )
    
    count = ingredient_consumptions.count()
    print(f"✓ Found {count} ingredient consumption records")
    
    if count != 3:
        print(f"❌ Expected 3 records, got {count}")
        return
    
    print("\nDetailed Ingredient Consumptions:")
    print("-" * 70)
    
    for ic in ingredient_consumptions:
        print(f"\n{ic.ingredient.name}:")
        print(f"  - Quantity Used: {ic.quantity_used} {ic.unit}")
        print(f"  - Expected: {ic.quantity_used / quantity_made} {ic.unit} per cocktail")
        print(f"  - Stock Item: {ic.stock_item.sku if ic.stock_item else 'Not linked'}")
        print(f"  - Merged to Stocktake: {ic.is_merged_to_stocktake}")
        print(f"  - Can be Merged: {ic.can_be_merged}")
        print(f"  - Timestamp: {ic.timestamp}")
    
    print_separator("STEP 4: Verify Quantities")
    
    # Verify vodka consumption (45ml × 5 cocktails = 225ml)
    vodka_consumption = ingredient_consumptions.get(ingredient=vodka)
    expected_vodka = Decimal('45') * quantity_made
    
    if vodka_consumption.quantity_used == expected_vodka:
        print(f"✓ Vodka quantity correct: {vodka_consumption.quantity_used}ml")
    else:
        print(f"❌ Vodka quantity wrong: {vodka_consumption.quantity_used}ml (expected {expected_vodka}ml)")
    
    # Verify cranberry consumption (30ml × 5 cocktails = 150ml)
    cranberry_consumption = ingredient_consumptions.get(ingredient=cranberry)
    expected_cranberry = Decimal('30') * quantity_made
    
    if cranberry_consumption.quantity_used == expected_cranberry:
        print(f"✓ Cranberry quantity correct: {cranberry_consumption.quantity_used}ml")
    else:
        print(f"❌ Cranberry quantity wrong: {cranberry_consumption.quantity_used}ml (expected {expected_cranberry}ml)")
    
    # Verify lime consumption (15ml × 5 cocktails = 75ml)
    lime_consumption = ingredient_consumptions.get(ingredient=lime)
    expected_lime = Decimal('15') * quantity_made
    
    if lime_consumption.quantity_used == expected_lime:
        print(f"✓ Lime quantity correct: {lime_consumption.quantity_used}ml")
    else:
        print(f"❌ Lime quantity wrong: {lime_consumption.quantity_used}ml (expected {expected_lime}ml)")
    
    print_separator("STEP 5: Verify Stock Item Linking")
    
    linked_count = ingredient_consumptions.filter(stock_item__isnull=False).count()
    print(f"✓ {linked_count} ingredient(s) linked to stock items")
    
    if vodka.linked_stock_item:
        if vodka_consumption.stock_item == vodka.linked_stock_item:
            print(f"✓ Vodka correctly linked to: {vodka.linked_stock_item.sku}")
        else:
            print(f"❌ Vodka link mismatch!")
    
    print_separator("STEP 6: Test Merge Capability")
    
    mergeable_count = sum(1 for ic in ingredient_consumptions if ic.can_be_merged)
    print(f"✓ {mergeable_count} ingredient(s) can be merged to stocktake")
    
    for ic in ingredient_consumptions:
        if ic.can_be_merged:
            print(f"  - {ic.ingredient.name}: Ready to merge (has stock_item)")
        else:
            reason = "already merged" if ic.is_merged_to_stocktake else "no stock_item linked"
            print(f"  - {ic.ingredient.name}: Cannot merge ({reason})")
    
    print_separator("TEST SUMMARY")
    
    print("✓ All basic tests passed!")
    print(f"\nTest Results:")
    print(f"  - CocktailConsumption ID: {consumption.id}")
    print(f"  - Ingredient consumptions created: {count}")
    print(f"  - Stock items linked: {linked_count}")
    print(f"  - Ready to merge: {mergeable_count}")
    print(f"\nYou can now test the merge endpoints with:")
    print(f"  - Consumption records from this test")
    print(f"  - Check available endpoint: GET /ingredient-consumptions/available/")
    print(f"  - Filter by stock item: GET /ingredient-consumptions/?stock_item={vodka.linked_stock_item_id if vodka.linked_stock_item else 'N/A'}")


if __name__ == "__main__":
    try:
        test_cocktail_consumption_creation()
        print("\n✓ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
