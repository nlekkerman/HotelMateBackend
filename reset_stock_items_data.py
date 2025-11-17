import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal


def reset_stock_items_data():
    """Reset all stock item measurements to zero/null"""
    
    stock_items = StockItem.objects.all()
    
    print(f"\n{'='*80}")
    print(f"RESETTING DATA FOR {stock_items.count()} STOCK ITEMS")
    print(f"Keeping: name, sku, category, subcategory, hotel")
    print(f"Resetting: all measurements, costs, quantities, prices")
    print(f"{'='*80}\n")
    
    confirmation = input("Are you sure you want to reset all data? (yes/no): ")
    
    if confirmation.lower() != 'yes':
        print("\nOperation cancelled.")
        return
    
    reset_count = 0
    
    for item in stock_items:
     
        item.current_full_units = Decimal('0.00')
        item.current_partial_units = Decimal('0.0000')
       
        
        # Save the item
        item.save()
        reset_count += 1
        
        if reset_count % 10 == 0:
            print(f"Reset {reset_count} items...")
    
    print(f"\n{'='*80}")
    print(f"COMPLETED: Reset {reset_count} stock items")
    print(f"Preserved: name, sku, category, subcategory, hotel")
    print(f"{'='*80}\n")
    
    # Show sample of reset items
    print("Sample of reset items:")
    print("-" * 80)
    for item in stock_items[:5]:
        print(f"ID: {item.id} | SKU: {item.sku} | Name: {item.name}")
        print(f"  Size: {item.size} | UoM: {item.uom} | Cost: {item.unit_cost}")
        print()


if __name__ == '__main__':
    reset_stock_items_data()
