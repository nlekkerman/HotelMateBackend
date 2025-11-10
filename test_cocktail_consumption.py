"""
Test script for cocktail consumption calculations
Tests revenue calculations without linking to stocktake
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import CocktailRecipe, CocktailConsumption
from hotel.models import Hotel
from decimal import Decimal


def test_cocktail_consumption_calculations():
    """Test cocktail consumption creation and revenue calculations"""
    
    print("=" * 60)
    print("TESTING COCKTAIL CONSUMPTION CALCULATIONS")
    print("=" * 60)
    
    # Get hotel
    hotel = Hotel.objects.get(id=2)
    print(f"\nUsing Hotel: {hotel.name}")
    
    # Get some cocktails
    cocktails = CocktailRecipe.objects.filter(hotel=hotel)[:5]
    
    print(f"\nFound {cocktails.count()} cocktails to test\n")
    
    test_results = []
    
    for cocktail in cocktails:
        print(f"\n{'='*60}")
        print(f"Testing: {cocktail.name}")
        print(f"Price: €{cocktail.price}")
        print(f"{'='*60}")
        
        # Create consumption
        quantity = 3  # Make 3 cocktails
        
        consumption = CocktailConsumption.objects.create(
            cocktail=cocktail,
            quantity_made=quantity,
            hotel=hotel,
            # Note: NOT linking to stocktake yet
        )
        
        # Verify calculations
        expected_revenue = Decimal(quantity) * cocktail.price
        
        print(f"\n✓ Created consumption #{consumption.id}")
        print(f"  Quantity Made: {consumption.quantity_made}")
        print(f"  Unit Price: €{consumption.unit_price}")
        print(f"  Total Revenue: €{consumption.total_revenue}")
        print(f"  Expected Revenue: €{expected_revenue}")
        print(f"  Stocktake: {consumption.stocktake} (should be None)")
        
        # Validation
        is_correct = True
        errors = []
        
        if consumption.unit_price != cocktail.price:
            is_correct = False
            errors.append(
                f"Unit price mismatch: {consumption.unit_price} != {cocktail.price}"
            )
        
        if consumption.total_revenue != expected_revenue:
            is_correct = False
            errors.append(
                f"Revenue mismatch: {consumption.total_revenue} != {expected_revenue}"
            )
        
        if consumption.stocktake is not None:
            is_correct = False
            errors.append("Stocktake should be None")
        
        if is_correct:
            print(f"\n✅ PASS: All calculations correct!")
        else:
            print(f"\n❌ FAIL: Errors found:")
            for error in errors:
                print(f"  - {error}")
        
        test_results.append({
            'cocktail': cocktail.name,
            'passed': is_correct,
            'consumption_id': consumption.id
        })
    
    # Summary
    print(f"\n\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in test_results if r['passed'])
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    print("\nDetailed Results:")
    for result in test_results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  {status} - {result['cocktail']} (ID: {result['consumption_id']})")
    
    # Query all consumptions
    print(f"\n\n{'='*60}")
    print("QUERY TEST - All Cocktail Consumptions")
    print(f"{'='*60}")
    
    all_consumptions = CocktailConsumption.objects.filter(
        hotel=hotel,
        stocktake__isnull=True  # Only non-stocktake consumptions
    )
    
    total_revenue = sum(c.total_revenue for c in all_consumptions if c.total_revenue)
    total_quantity = sum(c.quantity_made for c in all_consumptions)
    
    print(f"\nTotal Consumptions (not in stocktake): {all_consumptions.count()}")
    print(f"Total Quantity Made: {total_quantity}")
    print(f"Total Revenue: €{total_revenue}")
    
    print("\n✅ Test Complete!")


if __name__ == "__main__":
    test_cocktail_consumption_calculations()
