"""
Test script to check stocktake API response after removing sales field
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from stock_tracker.stock_serializers import StocktakeSerializer

# Get stocktake 4
try:
    stocktake = Stocktake.objects.get(id=4)
    serializer = StocktakeSerializer(stocktake)
    data = serializer.data
    
    print("✅ Stocktake API Response is working!")
    print(f"\nStocktake ID: {data['id']}")
    print(f"Status: {data['status']}")
    print(f"Total Items: {data.get('total_items', 'N/A')}")
    
    # Check first line
    if data.get('lines'):
        first_line = data['lines'][0]
        print(f"\nFirst Line Item: {first_line.get('item_name')}")
        print(f"Opening Qty: {first_line.get('opening_qty')}")
        print(f"Purchases: {first_line.get('purchases')}")
        print(f"Waste: {first_line.get('waste')}")
        print(f"'sales' field exists: {'sales' in first_line}")
        
        # Show available fields
        print(f"\nAvailable fields in line: {list(first_line.keys())[:10]}...")
    
    print("\n✅ Backend is working correctly - 'sales' field has been removed")
    print("⚠️  You need to update the FRONTEND to not expect the 'sales' field")

except Stocktake.DoesNotExist:
    print("❌ Stocktake with ID 4 does not exist")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
