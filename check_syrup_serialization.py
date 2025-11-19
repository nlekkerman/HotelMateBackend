import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from stock_tracker.stock_serializers import StocktakeLineSerializer

def check_syrup_serialization():
    """Check what the backend is sending for syrups"""
    
    # Get March stocktake
    stocktake = Stocktake.objects.filter(
        period_start='2025-03-01',
        period_end='2025-03-31'
    ).first()
    
    if not stocktake:
        print("March stocktake not found!")
        return
    
    # Get a syrup line
    syrup_line = stocktake.lines.filter(
        item__subcategory='SYRUPS'
    ).first()
    
    if not syrup_line:
        print("No syrup line found!")
        return
    
    print(f"\n{'='*80}")
    print(f"SYRUP: {syrup_line.item.name}")
    print(f"{'='*80}")
    
    # Raw database values
    print("\nRAW DATABASE VALUES:")
    print(f"  counted_full_units: {syrup_line.counted_full_units}")
    print(f"  counted_partial_units: {syrup_line.counted_partial_units}")
    print(f"  opening_qty: {syrup_line.opening_qty}")
    print(f"  purchases: {syrup_line.purchases}")
    print(f"  waste: {syrup_line.waste}")
    
    # Calculated properties
    print("\nCALCULATED PROPERTIES:")
    print(f"  counted_qty: {syrup_line.counted_qty}")
    print(f"  expected_qty: {syrup_line.expected_qty}")
    print(f"  variance_qty: {syrup_line.variance_qty}")
    
    # Serialized data (what frontend receives)
    serializer = StocktakeLineSerializer(syrup_line)
    data = serializer.data
    
    print("\nSERIALIZED DATA (sent to frontend):")
    print(f"  counted_display_full_units: {data.get('counted_display_full_units')}")
    print(f"  counted_display_partial_units: {data.get('counted_display_partial_units')}")
    print(f"  counted_qty: {data.get('counted_qty')}")
    print(f"  opening_display_full_units: {data.get('opening_display_full_units')}")
    print(f"  opening_display_partial_units: {data.get('opening_display_partial_units')}")
    print(f"  expected_display_full_units: {data.get('expected_display_full_units')}")
    print(f"  expected_display_partial_units: {data.get('expected_display_partial_units')}")
    print(f"  variance_display_full_units: {data.get('variance_display_full_units')}")
    print(f"  variance_display_partial_units: {data.get('variance_display_partial_units')}")
    print(f"  variance_qty: {data.get('variance_qty')}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    check_syrup_serialization()
