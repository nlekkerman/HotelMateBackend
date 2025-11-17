import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StocktakeLine

def compare_model_fields():
    """Compare field names between StockItem and StocktakeLine"""
    
    # Get StockItem fields
    stock_item_fields = [f.name for f in StockItem._meta.get_fields()]
    
    # Get StocktakeLine fields
    stocktake_line_fields = [f.name for f in StocktakeLine._meta.get_fields()]
    
    print("\n" + "="*80)
    print("STOCKITEM FIELDS:")
    print("="*80)
    for field in sorted(stock_item_fields):
        print(f"  {field}")
    
    print("\n" + "="*80)
    print("STOCKTAKELINE FIELDS:")
    print("="*80)
    for field in sorted(stocktake_line_fields):
        print(f"  {field}")
    
    # Find common field names
    common_fields = set(stock_item_fields) & set(stocktake_line_fields)
    
    print("\n" + "="*80)
    print("COMMON FIELD NAMES (in both models):")
    print("="*80)
    for field in sorted(common_fields):
        print(f"  {field}")
    
    # Fields unique to each
    print("\n" + "="*80)
    print("UNIQUE TO STOCKITEM:")
    print("="*80)
    unique_stock = set(stock_item_fields) - set(stocktake_line_fields)
    for field in sorted(unique_stock):
        print(f"  {field}")
    
    print("\n" + "="*80)
    print("UNIQUE TO STOCKTAKELINE:")
    print("="*80)
    unique_line = set(stocktake_line_fields) - set(stock_item_fields)
    for field in sorted(unique_line):
        print(f"  {field}")


if __name__ == '__main__':
    compare_model_fields()
