"""
Script to check all stock items in database.
Run: python check_stock_items.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockCategory
from hotel.models import Hotel


def check_stock_items():
    print("=" * 80)
    print("STOCK ITEMS DATABASE CHECK")
    print("=" * 80)
    
    # Check hotels
    hotels = Hotel.objects.all()
    print(f"\n📍 HOTELS: {hotels.count()}")
    for hotel in hotels:
        print(f"   - {hotel.name} (ID: {hotel.id})")
    
    # Check categories
    categories = StockCategory.objects.all()
    print(f"\n📁 STOCK CATEGORIES: {categories.count()}")
    for cat in categories:
        item_count = cat.items.count()
        print(f"   - {cat.name} ({cat.hotel.name}) - {item_count} items")
    
    # Check all stock items
    items = StockItem.objects.all().select_related('hotel', 'category')
    print(f"\n📦 TOTAL STOCK ITEMS: {items.count()}")
    
    if items.count() == 0:
        print("\n❌ No stock items in database")
        return
    
    print("\n" + "=" * 80)
    print("STOCK ITEM DETAILS")
    print("=" * 80)
    
    for idx, item in enumerate(items, 1):
        print(f"\n[{idx}] {item.name}")
        print(f"    SKU: {item.sku}")
        print(f"    Hotel: {item.hotel.name}")
        print(f"    Category: {item.category.name if item.category else 'None'}")
        print(f"    Size: {item.size}")
        print(f"    UOM: {item.uom}")
        print(f"    Base Unit: {item.base_unit}")
        print(f"    Unit Cost: £{item.unit_cost}")
        print(f"    Current Stock: {item.current_qty} {item.base_unit}")
        print(f"    Par Level: {item.par_level} {item.base_unit}")
        print(f"    Active: {'Yes' if item.active else 'No'}")
        
        # Check movements
        movement_count = item.movements.count()
        print(f"    Stock Movements: {movement_count}")
        
        # Check stocktake lines
        line_count = item.stocktake_lines.count()
        print(f"    Stocktake Lines: {line_count}")
    
    # Summary by hotel
    print("\n" + "=" * 80)
    print("SUMMARY BY HOTEL")
    print("=" * 80)
    for hotel in hotels:
        hotel_items = items.filter(hotel=hotel)
        print(f"\n{hotel.name}: {hotel_items.count()} items")
        
        if hotel_items.count() > 0:
            active_count = hotel_items.filter(active=True).count()
            inactive_count = hotel_items.filter(active=False).count()
            print(f"  - Active: {active_count}")
            print(f"  - Inactive: {inactive_count}")
            
            # Group by category
            for cat in categories.filter(hotel=hotel):
                cat_items = hotel_items.filter(category=cat)
                if cat_items.count() > 0:
                    print(f"  - {cat.name}: {cat_items.count()}")


if __name__ == "__main__":
    try:
        check_stock_items()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
