"""
Update Menu Prices and Names for Stock Items

This script updates menu_price and name fields for stock items
based on the menu_prices_by_sku_full.json file.

Run from project root:
    python update_menu_prices.py
"""

import os
import sys
import django
import json
from decimal import Decimal
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from hotel.models import Hotel


def update_prices():
    """Update menu prices and names from JSON file"""
    
    print("=" * 70)
    print("UPDATING MENU PRICES AND NAMES")
    print("=" * 70)
    
    # Load JSON file
    json_file = Path(__file__).parent / 'docs' / 'menu_prices_by_sku_full.json'
    
    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        return
    
    with open(json_file, 'r') as f:
        menu_data = json.load(f)
    
    print(f"\n📄 Loaded {len(menu_data)} menu items from JSON\n")
    
    # Get hotel
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found!")
        return
    
    print(f"🏨 Hotel: {hotel.name}\n")
    
    # Statistics
    updated_count = 0
    not_found_count = 0
    skipped_count = 0
    
    not_found_skus = []
    
    for item_data in menu_data:
        sku = item_data.get('sku')
        menu_name = item_data.get('menu_name')
        sell_price_unit = item_data.get('sell_price_unit')
        sell_price_glass = item_data.get('sell_price_glass')
        sell_price_bottle = item_data.get('sell_price_bottle')
        
        if not sku:
            print(f"⚠️  Skipping item with no SKU")
            skipped_count += 1
            continue
        
        # Try to find stock item
        try:
            stock_item = StockItem.objects.get(hotel=hotel, sku=sku)
            
            # Update menu_price (for spirits, beers, mixers - per unit/serving)
            if sell_price_unit is not None:
                stock_item.menu_price = Decimal(str(sell_price_unit))
            
            # Update menu_price for wines sold by glass
            elif sell_price_glass is not None:
                stock_item.menu_price = Decimal(str(sell_price_glass))
            
            # Update bottle_price for wines
            if sell_price_bottle is not None:
                stock_item.bottle_price = Decimal(str(sell_price_bottle))
                stock_item.available_by_bottle = True
            
            stock_item.save()
            
            # Display update
            price_info = []
            if stock_item.menu_price:
                price_info.append(f"Menu: €{stock_item.menu_price}")
            if stock_item.bottle_price:
                price_info.append(f"Bottle: €{stock_item.bottle_price}")
            
            print(f"✅ {sku}: {stock_item.name}")
            if price_info:
                print(f"   {' | '.join(price_info)}")
            
            updated_count += 1
            
        except StockItem.DoesNotExist:
            print(f"❌ NOT FOUND: {sku} - {menu_name}")
            not_found_skus.append(sku)
            not_found_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ UPDATE COMPLETE!")
    print("=" * 70)
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Updated: {updated_count}")
    print(f"  ❌ Not Found: {not_found_count}")
    print(f"  ⚠️  Skipped: {skipped_count}")
    print(f"  📝 Total in JSON: {len(menu_data)}")
    
    if not_found_skus:
        print(f"\n⚠️  SKUs not found in database:")
        for sku in not_found_skus:
            print(f"     - {sku}")
    
    # Show profitability for updated items
    print("\n" + "=" * 70)
    print("📈 PROFITABILITY PREVIEW (First 10 items)")
    print("=" * 70)
    
    items_with_prices = StockItem.objects.filter(
        hotel=hotel,
        menu_price__isnull=False
    ).order_by('-menu_price')[:10]
    
    print(f"\n{'SKU':<10} {'Name':<30} {'Cost':<8} {'Price':<8} {'GP%':<6}")
    print("-" * 70)
    
    for item in items_with_prices:
        gp = item.gross_profit_percentage or 0
        print(
            f"{item.sku:<10} "
            f"{item.name[:28]:<30} "
            f"€{item.cost_per_serving:<7.2f} "
            f"€{item.menu_price:<7.2f} "
            f"{gp:>5.1f}%"
        )


if __name__ == '__main__':
    update_prices()
