"""
Test all StocktakeLineSerializer methods with real data
Verifies that serializer output matches expected API response format
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from stock_tracker.stock_serializers import StocktakeLineSerializer
from decimal import Decimal

def test_serializer_methods():
    """Test all serializer methods with 5 examples from each category"""
    
    print("=" * 80)
    print("TESTING STOCKTAKELINE SERIALIZER METHODS")
    print("=" * 80)
    
    # Get October stocktake
    october = Stocktake.objects.get(id=18)
    print(f"Testing with: October 2025 Stocktake (ID: {october.id})")
    print()
    
    # Get 5 examples from each category
    categories = {
        'B': 'Bottled Beer',
        'D': 'Draught Beer', 
        'S': 'Spirits',
        'W': 'Wine',
        'M': 'Minerals'
    }
    
    for cat_code, cat_name in categories.items():
        print("=" * 80)
        print(f"CATEGORY: {cat_name} ({cat_code})")
        print("=" * 80)
        
        # Get 5 items from this category
        lines = StocktakeLine.objects.filter(
            stocktake=october,
            item__category__code=cat_code
        ).select_related('item', 'item__category')[:5]
        
        if not lines:
            print(f"⚠️  No items found for category {cat_code}")
            print()
            continue
        
        for idx, line in enumerate(lines, 1):
            print(f"\n{idx}. {line.item.sku} - {line.item.name}")
            print("-" * 80)
            
            # Serialize the line
            serializer = StocktakeLineSerializer(line)
            data = serializer.data
            
            # Test IDENTIFICATION fields
            print("\n📋 IDENTIFICATION:")
            print(f"   id: {data['id']}")
            print(f"   stocktake: {data['stocktake']}")
            print(f"   item: {data['item']}")
            print(f"   item_sku: {data['item_sku']}")
            print(f"   item_name: {data['item_name']}")
            print(f"   category_code: {data['category_code']}")
            print(f"   category_name: {data['category_name']}")
            print(f"   item_size: {data['item_size']}")
            print(f"   item_uom: {data['item_uom']}")
            
            # Test RAW QUANTITIES
            print("\n📊 RAW QUANTITIES (Servings):")
            print(f"   opening_qty: {data['opening_qty']}")
            print(f"   purchases: {data['purchases']}")
            print(f"   sales_qty: {data['sales_qty']}")
            print(f"   waste: {data['waste']}")
            print(f"   transfers_in: {data['transfers_in']}")
            print(f"   transfers_out: {data['transfers_out']}")
            print(f"   adjustments: {data['adjustments']}")
            
            # Test MANUAL OVERRIDES
            print("\n🔧 MANUAL OVERRIDES:")
            print(f"   manual_purchases_value: {data['manual_purchases_value']}")
            print(f"   manual_waste_value: {data['manual_waste_value']}")
            print(f"   manual_sales_value: {data['manual_sales_value']}")
            
            # Test USER INPUT FIELDS
            print("\n✏️  USER INPUT FIELDS:")
            print(f"   counted_full_units: {data['counted_full_units']}")
            print(f"   counted_partial_units: {data['counted_partial_units']}")
            
            # Test CALCULATED QUANTITIES
            print("\n🧮 CALCULATED QUANTITIES:")
            print(f"   expected_qty: {data['expected_qty']}")
            print(f"   counted_qty: {data['counted_qty']}")
            print(f"   variance_qty: {data['variance_qty']}")
            
            # Verify calculations manually
            expected_manual = (
                Decimal(data['opening_qty']) + 
                Decimal(data['purchases']) - 
                Decimal(data['waste'])
            )
            counted_manual = Decimal(data['counted_qty'])
            variance_manual = counted_manual - expected_manual
            
            expected_match = abs(Decimal(data['expected_qty']) - expected_manual) < Decimal('0.01')
            variance_match = abs(Decimal(data['variance_qty']) - variance_manual) < Decimal('0.01')
            
            print(f"   ✅ expected_qty calculation: {'MATCH' if expected_match else 'MISMATCH'}")
            print(f"   ✅ variance_qty calculation: {'MATCH' if variance_match else 'MISMATCH'}")
            
            # Test DISPLAY UNITS
            print("\n📺 DISPLAY UNITS:")
            print(f"   opening_display_full_units: {data['opening_display_full_units']}")
            print(f"   opening_display_partial_units: {data['opening_display_partial_units']}")
            print(f"   expected_display_full_units: {data['expected_display_full_units']}")
            print(f"   expected_display_partial_units: {data['expected_display_partial_units']}")
            print(f"   counted_display_full_units: {data['counted_display_full_units']}")
            print(f"   counted_display_partial_units: {data['counted_display_partial_units']}")
            print(f"   variance_display_full_units: {data['variance_display_full_units']}")
            print(f"   variance_display_partial_units: {data['variance_display_partial_units']}")
            
            # Verify display unit conversion manually
            uom = Decimal(data['item_uom'])
            expected_qty = Decimal(data['expected_qty'])
            expected_full_manual = int(expected_qty / uom)
            expected_partial_manual = expected_qty % uom
            
            # Apply category-specific rounding
            if cat_code == 'B' or (cat_code == 'M' and 'Doz' in data['item_size']):
                expected_partial_manual_str = str(int(round(float(expected_partial_manual))))
            else:
                expected_partial_manual_str = str(expected_partial_manual.quantize(Decimal('0.01')))
            
            display_match = (
                data['expected_display_full_units'] == str(expected_full_manual) and
                data['expected_display_partial_units'] == expected_partial_manual_str
            )
            print(f"   ✅ display units conversion: {'MATCH' if display_match else 'MISMATCH'}")
            
            # Test VALUES
            print("\n💰 VALUES:")
            print(f"   valuation_cost: {data['valuation_cost']}")
            print(f"   expected_value: {data['expected_value']}")
            print(f"   counted_value: {data['counted_value']}")
            print(f"   variance_value: {data['variance_value']}")
            
            # Verify value calculations
            expected_value_manual = expected_manual * Decimal(data['valuation_cost'])
            counted_value_manual = counted_manual * Decimal(data['valuation_cost'])
            variance_value_manual = counted_value_manual - expected_value_manual
            
            expected_value_match = abs(Decimal(data['expected_value']) - expected_value_manual) < Decimal('0.01')
            variance_value_match = abs(Decimal(data['variance_value']) - variance_value_manual) < Decimal('0.01')
            
            print(f"   ✅ expected_value calculation: {'MATCH' if expected_value_match else 'MISMATCH'}")
            print(f"   ✅ variance_value calculation: {'MATCH' if variance_value_match else 'MISMATCH'}")
            
            # Test COCKTAIL CONSUMPTION
            print("\n🍹 COCKTAIL CONSUMPTION:")
            print(f"   available_cocktail_consumption_qty: {data['available_cocktail_consumption_qty']}")
            print(f"   merged_cocktail_consumption_qty: {data['merged_cocktail_consumption_qty']}")
            print(f"   available_cocktail_consumption_value: {data['available_cocktail_consumption_value']}")
            print(f"   merged_cocktail_consumption_value: {data['merged_cocktail_consumption_value']}")
            print(f"   can_merge_cocktails: {data['can_merge_cocktails']}")
            
            # Overall verification
            print("\n" + "=" * 80)
            all_match = (
                expected_match and variance_match and 
                display_match and expected_value_match and 
                variance_value_match
            )
            
            if all_match:
                print(f"✅ ALL CHECKS PASSED for {line.item.sku}")
            else:
                print(f"⚠️  SOME CHECKS FAILED for {line.item.sku}")
            print("=" * 80)
    
    print("\n" + "=" * 80)
    print("SERIALIZER METHOD TESTING COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    test_serializer_methods()
