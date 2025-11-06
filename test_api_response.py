"""
Test API response includes calculated serving fields
Run: python test_api_response.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from stock_tracker.stock_serializers import StockItemSerializer
from hotel.models import Hotel
import json


def test_api_response():
    """Test that API serializer returns calculated fields"""
    
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found.")
        return
    
    print("=" * 80)
    print("API RESPONSE TEST - Calculated Serving Fields")
    print("=" * 80)
    
    # Test Spirit
    print("\n🥃 SPIRIT (Gordons Gin):")
    spirit = StockItem.objects.filter(
        hotel=hotel,
        sku='SP0011'
    ).first()
    
    if spirit:
        serializer = StockItemSerializer(spirit)
        data = serializer.data
        print(json.dumps({
            'sku': data['sku'],
            'name': data['name'],
            'product_type': data['product_type'],
            'size_value': data['size_value'],
            'size_unit': data['size_unit'],
            'serving_size': data['serving_size'],
            'shots_per_bottle': data['shots_per_bottle'],
            'pints_per_keg': data['pints_per_keg'],
            'half_pints_per_keg': data['half_pints_per_keg'],
            'servings_per_unit': data['servings_per_unit']
        }, indent=2))
    
    # Test Draught Beer
    print("\n\n🍺 DRAUGHT BEER (Guinness 50L):")
    draught = StockItem.objects.filter(
        hotel=hotel,
        sku='BE0006'
    ).first()
    
    if draught:
        serializer = StockItemSerializer(draught)
        data = serializer.data
        print(json.dumps({
            'sku': data['sku'],
            'name': data['name'],
            'product_type': data['product_type'],
            'size_value': data['size_value'],
            'size_unit': data['size_unit'],
            'serving_size': data['serving_size'],
            'shots_per_bottle': data['shots_per_bottle'],
            'pints_per_keg': data['pints_per_keg'],
            'half_pints_per_keg': data['half_pints_per_keg'],
            'servings_per_unit': data['servings_per_unit']
        }, indent=2))
    
    # Test Wine
    print("\n\n🍷 WINE:")
    wine = StockItem.objects.filter(
        hotel=hotel,
        sku='WI0001'
    ).first()
    
    if wine:
        serializer = StockItemSerializer(wine)
        data = serializer.data
        print(json.dumps({
            'sku': data['sku'],
            'name': data['name'],
            'product_type': data['product_type'],
            'size_value': data['size_value'],
            'size_unit': data['size_unit'],
            'serving_size': data['serving_size'],
            'shots_per_bottle': data['shots_per_bottle'],
            'pints_per_keg': data['pints_per_keg'],
            'half_pints_per_keg': data['half_pints_per_keg'],
            'servings_per_unit': data['servings_per_unit']
        }, indent=2))
    
    print("\n\n✅ All fields are being returned by the API!\n")


if __name__ == '__main__':
    test_api_response()
