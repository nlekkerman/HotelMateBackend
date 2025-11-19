import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from stock_tracker.stock_serializers import StocktakeLineSerializer

def check_all_variance_fields():
    """Check ALL fields the backend sends for variance"""
    
    stocktake = Stocktake.objects.filter(
        period_start='2025-03-01',
        period_end='2025-03-31'
    ).first()
    
    syrup_line = stocktake.lines.filter(
        item__subcategory='SYRUPS'
    ).first()
    
    print(f"\nSYRUP: {syrup_line.item.name}")
    print("="*80)
    
    serializer = StocktakeLineSerializer(syrup_line)
    data = serializer.data
    
    # Print ALL fields that contain 'variance'
    print("\nALL VARIANCE-RELATED FIELDS:")
    for key, value in sorted(data.items()):
        if 'variance' in key.lower():
            print(f"  {key}: {value}")
    
    print("\n" + "="*80)
    print("FULL SERIALIZED DATA (JSON):")
    print("="*80)
    print(json.dumps(data, indent=2, default=str))

if __name__ == '__main__':
    check_all_variance_fields()
