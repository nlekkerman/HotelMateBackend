"""
Test variance_drink_servings field in API response
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from stock_tracker.stock_serializers import StocktakeLineSerializer

print("\n" + "="*80)
print("TEST: variance_drink_servings API Field")
print("="*80)

# Get February stocktake
stocktake = Stocktake.objects.filter(
    hotel_id=2,
    period_start__year=2025,
    period_start__month=2
).first()

if stocktake:
    # Test different categories
    test_cases = [
        ('M25', 'BIB', 'Should calculate drink servings'),
        ('M03', 'SOFT_DRINKS', 'Should return null'),
        ('M08', 'JUICES', 'Should return null'),
        ('M16', 'SYRUPS', 'Should return null'),
    ]
    
    for sku, expected_subcat, description in test_cases:
        line = StocktakeLine.objects.filter(
            stocktake=stocktake,
            item__sku=sku
        ).select_related('item').first()
        
        if line:
            # Serialize to get API response
            serializer = StocktakeLineSerializer(line)
            data = serializer.data
            
            print(f"\n{'-'*80}")
            print(f"Item: {data['item_sku']} - {data['item_name']}")
            print(f"Subcategory: {data['subcategory']}")
            print(f"{'-'*80}")
            print(f"variance_qty: {data['variance_qty']}")
            print(f"variance_drink_servings: {data['variance_drink_servings']}")
            print(f"Expected: {description}")
            
            # Verify
            if data['subcategory'] == 'BIB':
                if data['variance_drink_servings']:
                    print(f"✅ PASS: Calculated drink servings")
                else:
                    print(f"❌ FAIL: Should have drink servings value")
            else:
                if data['variance_drink_servings'] is None:
                    print(f"✅ PASS: Correctly returns null for non-BIB")
                else:
                    print(f"❌ FAIL: Should return null for non-BIB")

print("\n" + "="*80 + "\n")
