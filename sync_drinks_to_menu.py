#!/usr/bin/env python
"""
Sync Drinks from Stock Items to Menu Items
==========================================

This script:
1. Checks existing drinks in menu items (Room Service & Breakfast)  
2. Checks drinks in stock inventory
3. Finds missing drinks that exist in stock but not in menu items
4. Creates missing drinks in both Room Service and Breakfast menus

Usage:
    python sync_drinks_to_menu.py
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import transaction
from hotel.models import Hotel
from stock_tracker.models import StockItem
from room_services.models import RoomServiceItem, BreakfastItem
from decimal import Decimal


def print_separator(title):
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)


def get_existing_drinks_in_menus(hotel):
    """Get existing drinks from both menu types"""
    
    # Room Service drinks
    room_service_drinks = RoomServiceItem.objects.filter(
        hotel=hotel,
        category='Drinks'
    ).values_list('name', flat=True)
    
    # Breakfast drinks  
    breakfast_drinks = BreakfastItem.objects.filter(
        hotel=hotel,
        category='Drinks'
    ).values_list('name', flat=True)
    
    # Combine both lists (remove duplicates)
    all_menu_drinks = set(list(room_service_drinks) + list(breakfast_drinks))
    
    return {
        'room_service': list(room_service_drinks),
        'breakfast': list(breakfast_drinks), 
        'all': list(all_menu_drinks)
    }


def get_drinks_from_stock(hotel):
    """Get drinks from stock inventory"""
    
    # Get all stock items that are drinks/beverages
    # Category 'M' = Minerals/Syrups which includes drinks
    stock_drinks = StockItem.objects.filter(
        hotel=hotel,
        category_id='M',  # Minerals category
        available_on_menu=True  # Only items available for sale
    ).filter(
        # Drink subcategories
        subcategory__in=[
            'SOFT_DRINKS',    # Coca Cola, Pepsi, etc.
            'JUICES',         # Orange juice, Apple juice, etc. 
            'CORDIALS',       # Cordial drinks
            'BIB'            # Bag-in-Box beverages
        ]
    )
    
    drinks_info = []
    for item in stock_drinks:
        drinks_info.append({
            'name': item.name,
            'sku': item.sku,
            'subcategory': item.subcategory,
            'size': item.size,
            'menu_price': item.menu_price,
            'available': item.available_on_menu and item.active
        })
    
    return drinks_info


def estimate_drink_price(stock_item_info):
    """Estimate menu price for drinks based on stock item"""
    
    # If stock item has menu_price, use it
    if stock_item_info.get('menu_price'):
        return stock_item_info['menu_price']
    
    # Default prices by subcategory
    subcategory = stock_item_info.get('subcategory', '')
    
    if subcategory == 'SOFT_DRINKS':
        return Decimal('3.50')  # Standard soft drink price
    elif subcategory == 'JUICES':
        return Decimal('4.00')  # Fresh juice price
    elif subcategory == 'CORDIALS':
        return Decimal('3.00')  # Cordial price
    elif subcategory == 'BIB':
        return Decimal('2.50')  # Bag-in-Box beverages
    else:
        return Decimal('3.00')  # Default price


def create_description_for_drink(stock_item_info):
    """Generate description based on drink info"""
    
    name = stock_item_info['name']
    size = stock_item_info.get('size', '')
    subcategory = stock_item_info.get('subcategory', '')
    
    if subcategory == 'SOFT_DRINKS':
        return f"Refreshing {name} soft drink. Served chilled. {size}"
    elif subcategory == 'JUICES':
        return f"Fresh {name}. Natural and refreshing. {size}"
    elif subcategory == 'CORDIALS':
        return f"{name} cordial drink. Sweet and flavorful. {size}"
    elif subcategory == 'BIB':
        return f"{name} beverage. Quality drink served fresh. {size}"
    else:
        return f"{name} - Quality beverage served fresh. {size}"


def sync_drinks_for_hotel(hotel):
    """Main sync function for a hotel"""
    
    print_separator(f"SYNCING DRINKS FOR: {hotel.name}")
    
    # Step 1: Get existing drinks in menus
    print("\n🔍 STEP 1: Checking existing drinks in menus...")
    menu_drinks = get_existing_drinks_in_menus(hotel)
    
    print(f"  Room Service drinks: {len(menu_drinks['room_service'])}")
    for drink in menu_drinks['room_service'][:5]:  # Show first 5
        print(f"    - {drink}")
    if len(menu_drinks['room_service']) > 5:
        print(f"    ... and {len(menu_drinks['room_service']) - 5} more")
        
    print(f"  Breakfast drinks: {len(menu_drinks['breakfast'])}")
    for drink in menu_drinks['breakfast'][:5]:  # Show first 5
        print(f"    - {drink}")
    if len(menu_drinks['breakfast']) > 5:
        print(f"    ... and {len(menu_drinks['breakfast']) - 5} more")
    
    # Step 2: Get drinks from stock
    print(f"\n🏪 STEP 2: Checking drinks in stock inventory...")
    stock_drinks = get_drinks_from_stock(hotel)
    
    print(f"  Stock drinks found: {len(stock_drinks)}")
    for drink in stock_drinks[:10]:  # Show first 10
        print(f"    - {drink['name']} ({drink['subcategory']}) - {drink['sku']}")
    if len(stock_drinks) > 10:
        print(f"    ... and {len(stock_drinks) - 10} more")
    
    # Step 3: Find missing drinks
    print(f"\n🔍 STEP 3: Finding missing drinks...")
    stock_drink_names = [drink['name'] for drink in stock_drinks if drink['available']]
    missing_drinks = []
    
    for stock_drink in stock_drinks:
        if stock_drink['available'] and stock_drink['name'] not in menu_drinks['all']:
            missing_drinks.append(stock_drink)
    
    print(f"  Missing drinks to add: {len(missing_drinks)}")
    for drink in missing_drinks:
        print(f"    - {drink['name']} ({drink['subcategory']})")
    
    if not missing_drinks:
        print("  ✅ All stock drinks already exist in menus!")
        return
    
    # Step 4: Create missing drinks in menus
    print(f"\n✨ STEP 4: Creating missing drinks in menus...")
    
    created_room_service = 0
    created_breakfast = 0
    
    with transaction.atomic():
        for drink_info in missing_drinks:
            price = estimate_drink_price(drink_info)
            description = create_description_for_drink(drink_info)
            
            # Create in Room Service menu
            room_service_item, created = RoomServiceItem.objects.get_or_create(
                hotel=hotel,
                name=drink_info['name'],
                defaults={
                    'price': price,
                    'description': description,
                    'category': 'Drinks',
                    'is_on_stock': True
                }
            )
            if created:
                created_room_service += 1
                print(f"    ✅ Room Service: {drink_info['name']} - €{price}")
            
            # Create in Breakfast menu (no price needed)
            breakfast_item, created = BreakfastItem.objects.get_or_create(
                hotel=hotel,
                name=drink_info['name'],
                defaults={
                    'description': description,
                    'category': 'Drinks',
                    'quantity': 1,
                    'is_on_stock': True
                }
            )
            if created:
                created_breakfast += 1
                print(f"    ✅ Breakfast: {drink_info['name']}")
    
    print(f"\n🎉 SYNC COMPLETE!")
    print(f"  Created {created_room_service} Room Service drinks")
    print(f"  Created {created_breakfast} Breakfast drinks")


def main():
    """Main execution function"""
    
    print_separator("DRINK SYNC UTILITY")
    print("Syncing drinks from stock inventory to menu items...")
    
    # Get all hotels or specific hotel
    hotels = Hotel.objects.all()
    
    if not hotels.exists():
        print("❌ No hotels found!")
        return
    
    print(f"Found {hotels.count()} hotel(s)")
    
    # Process each hotel
    for hotel in hotels:
        try:
            sync_drinks_for_hotel(hotel)
            print(f"\n✅ Completed sync for {hotel.name}")
            
        except Exception as e:
            print(f"\n❌ Error syncing {hotel.name}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print_separator("ALL HOTELS PROCESSED")


if __name__ == '__main__':
    main()