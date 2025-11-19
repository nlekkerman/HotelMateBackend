import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, Stocktake, StocktakeLine
from decimal import Decimal

def test_display_units():
    """Test the new UOM=1 display logic"""
    
    print("\n" + "="*80)
    print("TESTING UOM=1 DISPLAY UNITS (Spirits, Syrups, Wines)")
    print("="*80)
    
    # Get some test items
    spirits = StockItem.objects.filter(category__code='S', uom=1).first()
    syrup = StockItem.objects.filter(subcategory='SYRUPS', uom=1).first()
    wine = StockItem.objects.filter(category__code='W', uom=1).first()
    bib = StockItem.objects.filter(subcategory='BIB', uom=1).first()
    bulk_juice = StockItem.objects.filter(subcategory='BULK_JUICES', uom=1).first()
    
    # Get an item with UOM > 1 for comparison
    bottled_beer = StockItem.objects.filter(category__code='B').first()
    draught = StockItem.objects.filter(category__code='D').first()
    
    test_items = [
        ('Spirit (UOM=1)', spirits),
        ('Syrup (UOM=1)', syrup),
        ('Wine (UOM=1)', wine),
        ('BIB (UOM=1)', bib),
        ('Bulk Juice (UOM=1)', bulk_juice),
        ('Bottled Beer (UOM>1)', bottled_beer),
        ('Draught (UOM>1)', draught),
    ]
    
    # Get latest stocktake with lines
    stocktake = Stocktake.objects.filter(
        status__in=['DRAFT', 'APPROVED']
    ).order_by('-created_at').first()
    
    if not stocktake:
        print("No stocktake found!")
        return
    
    print(f"\nUsing Stocktake ID: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print("="*80)
    
    for label, item in test_items:
        if not item:
            continue
            
        line = StocktakeLine.objects.filter(
            stocktake=stocktake,
            item=item
        ).first()
        
        if not line:
            continue
        
        print(f"\n{label}: {item.name}")
        print(f"  Category: {item.category.code}")
        print(f"  UOM: {item.uom}")
        
        if item.subcategory:
            print(f"  Subcategory: {item.subcategory}")
        
        # Test with expected_qty
        from stock_tracker.stock_serializers import StocktakeLineSerializer
        serializer = StocktakeLineSerializer(line)
        data = serializer.data
        
        print(f"\n  Expected Qty: {line.expected_qty}")
        print(f"  Display Full: {data['expected_display_full_units']}")
        print(f"  Display Partial: {data['expected_display_partial_units']}")
        
        if item.uom == 1:
            print(f"  ✓ EXPECTED: Combined total in full_units, partial=0")
            if data['expected_display_partial_units'] == "0":
                print(f"  ✓ CORRECT: Shows {data['expected_display_full_units']} total")
            else:
                print(f"  ✗ ERROR: Should show 0 in partial, got {data['expected_display_partial_units']}")
        else:
            print(f"  ✓ EXPECTED: Split display (full + partial)")
            print(f"  ✓ Shows {data['expected_display_full_units']} + {data['expected_display_partial_units']}")

if __name__ == '__main__':
    test_display_units()
