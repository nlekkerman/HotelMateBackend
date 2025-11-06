"""
Test serving calculations for stock items
Run: python test_serving_calculations.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from hotel.models import Hotel


def test_serving_calculations():
    """Test that serving calculations are working correctly"""
    
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hotel found.")
            return
        print(f"✅ Using hotel: {hotel.name}\n")
    except Exception as e:
        print(f"❌ Error getting hotel: {e}")
        return
    
    print("=" * 80)
    print("TESTING SERVING CALCULATIONS")
    print("=" * 80)
    
    # Test 1: Spirits - Shots per bottle
    print("\n🥃 TEST 1: SPIRITS - Shots Per Bottle")
    print("-" * 80)
    spirits = StockItem.objects.filter(
        hotel=hotel,
        sku__startswith='SP'
    )[:5]
    
    for item in spirits:
        print(f"\n{item.sku} - {item.name}")
        print(f"  Category: {item.category.name if item.category else 'N/A'}")
        print(f"  Product Type: {item.product_type}")
        print(f"  Size: {item.size_value}{item.size_unit}")
        print(f"  Serving Size: {item.serving_size}ml")
        print(f"  ➡️  Shots Per Bottle: {item.shots_per_bottle}")
        
        # Manual calculation for verification
        if item.size_value and item.serving_size:
            from decimal import Decimal
            size_ml = item.size_value * Decimal('10') if item.size_unit == 'cl' else item.size_value
            expected = round(size_ml / item.serving_size, 1)
            status = "✅" if item.shots_per_bottle == expected else "❌"
            print(f"  Expected: {expected} {status}")
    
    # Test 2: Draught Beer - Pints per keg
    print("\n\n🍺 TEST 2: DRAUGHT BEER - Pints Per Keg")
    print("-" * 80)
    draught = StockItem.objects.filter(
        hotel=hotel,
        size__icontains='Keg'
    )[:5]
    
    for item in draught:
        print(f"\n{item.sku} - {item.name}")
        print(f"  Product Type: {item.product_type}")
        print(f"  Size: {item.size_value}{item.size_unit}")
        print(f"  ➡️  Pints Per Keg: {item.pints_per_keg}")
        print(f"  ➡️  Half-Pints Per Keg: {item.half_pints_per_keg}")
        
        # Manual calculation for verification
        if item.size_value:
            from decimal import Decimal
            size_ml = item.size_value * Decimal('1000')  # L to ml
            expected_pints = round(size_ml / Decimal('568'), 1)
            expected_half_pints = round(expected_pints * 2, 1)
            status_pints = "✅" if item.pints_per_keg == expected_pints else "❌"
            status_half = "✅" if item.half_pints_per_keg == expected_half_pints else "❌"
            print(f"  Expected Pints: {expected_pints} {status_pints}")
            print(f"  Expected Half-Pints: {expected_half_pints} {status_half}")
    
    # Test 3: Wines - Servings per unit
    print("\n\n🍷 TEST 3: WINES - Servings Per Unit")
    print("-" * 80)
    wines = StockItem.objects.filter(
        hotel=hotel,
        sku__startswith='WI'
    )[:5]
    
    for item in wines:
        print(f"\n{item.sku} - {item.name}")
        print(f"  Product Type: {item.product_type}")
        print(f"  Size: {item.size_value}{item.size_unit}")
        print(f"  Serving Size: {item.serving_size}ml")
        print(f"  ➡️  Servings Per Unit: {item.servings_per_unit}")
        
        # Manual calculation for verification
        if item.size_value and item.serving_size:
            from decimal import Decimal
            size_ml = item.size_value * Decimal('10') if item.size_unit == 'cl' else item.size_value
            expected = round(size_ml / item.serving_size, 2)
            status = "✅" if item.servings_per_unit == expected else "❌"
            print(f"  Expected: {expected} {status}")
    
    # Test 4: Liqueurs - Shots per bottle
    print("\n\n🍸 TEST 4: LIQUEURS - Shots Per Bottle")
    print("-" * 80)
    liqueurs = StockItem.objects.filter(
        hotel=hotel,
        sku__startswith='LI'
    )[:3]
    
    for item in liqueurs:
        print(f"\n{item.sku} - {item.name}")
        print(f"  Category: {item.category.name if item.category else 'N/A'}")
        print(f"  Product Type: {item.product_type}")
        print(f"  Size: {item.size_value}{item.size_unit}")
        print(f"  Serving Size: {item.serving_size}ml")
        print(f"  ➡️  Shots Per Bottle: {item.shots_per_bottle}")
    
    # Test 5: Aperitifs - Shots per bottle
    print("\n\n🍹 TEST 5: APERITIFS - Shots Per Bottle")
    print("-" * 80)
    aperitifs = StockItem.objects.filter(
        hotel=hotel,
        sku__startswith='AP'
    )[:3]
    
    for item in aperitifs:
        print(f"\n{item.sku} - {item.name}")
        print(f"  Category: {item.category.name if item.category else 'N/A'}")
        print(f"  Product Type: {item.product_type}")
        print(f"  Size: {item.size_value}{item.size_unit}")
        print(f"  Serving Size: {item.serving_size}ml")
        print(f"  ➡️  Shots Per Bottle: {item.shots_per_bottle}")
    
    # Test 6: Fortified - Shots per bottle
    print("\n\n🥃 TEST 6: FORTIFIED - Shots Per Bottle")
    print("-" * 80)
    fortified = StockItem.objects.filter(
        hotel=hotel,
        sku__startswith='FO'
    )[:3]
    
    for item in fortified:
        print(f"\n{item.sku} - {item.name}")
        print(f"  Category: {item.category.name if item.category else 'N/A'}")
        print(f"  Product Type: {item.product_type}")
        print(f"  Size: {item.size_value}{item.size_unit}")
        print(f"  Serving Size: {item.serving_size}ml")
        print(f"  ➡️  Shots Per Bottle: {item.shots_per_bottle}")
    
    # Summary
    print("\n\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    total_items = StockItem.objects.filter(hotel=hotel).count()
    spirits_with_shots = StockItem.objects.filter(
        hotel=hotel,
        shots_per_bottle__isnull=False
    ).count()
    draughts_with_pints = StockItem.objects.filter(
        hotel=hotel,
        pints_per_keg__isnull=False
    ).count()
    wines_with_servings = StockItem.objects.filter(
        hotel=hotel,
        servings_per_unit__isnull=False
    ).count()
    
    print(f"\nTotal Items: {total_items}")
    print(f"Items with shots_per_bottle calculated: {spirits_with_shots}")
    print(f"Items with pints_per_keg calculated: {draughts_with_pints}")
    print(f"Items with servings_per_unit calculated: {wines_with_servings}")
    
    print("\n✅ Test completed!\n")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🧪 Stock Item Serving Calculations Test")
    print("="*80 + "\n")
    test_serving_calculations()
