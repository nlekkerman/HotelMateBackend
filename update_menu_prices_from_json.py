"""
Update menu prices in database from JSON file
"""
import os
import sys
import django
import json
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

# Load JSON data
json_file = 'docs/menu_prices_by_sku_full.json'
with open(json_file, 'r') as f:
    json_data = json.load(f)

print("=" * 80)
print("UPDATING MENU PRICES FROM JSON")
print("=" * 80)
print()

updated_count = 0
not_found_count = 0
error_count = 0

for item_data in json_data:
    sku = item_data['sku']
    menu_name = item_data['menu_name']
    
    try:
        # Find the item in database
        stock_item = StockItem.objects.filter(sku=sku).first()
        
        if not stock_item:
            print(f"❌ SKU not found in DB: {sku} - {menu_name}")
            not_found_count += 1
            continue
        
        # Determine category and update appropriate price fields
        category = stock_item.category_id
        updated_fields = []
        
        # For spirits (S), draught (D), bottled (B), minerals (M)
        if category in ['S', 'D', 'B', 'M']:
            if 'sell_price_unit' in item_data:
                old_price = stock_item.menu_price
                new_price = Decimal(str(item_data['sell_price_unit']))
                stock_item.menu_price = new_price
                updated_fields.append(
                    f"menu_price: {old_price or 0} → €{new_price}"
                )
        
        # For wine (W) - handle bottle and glass prices
        elif category == 'W':
            if 'sell_price_bottle' in item_data:
                old_bottle = stock_item.bottle_price
                new_bottle = Decimal(str(item_data['sell_price_bottle']))
                stock_item.bottle_price = new_bottle
                updated_fields.append(
                    f"bottle_price: {old_bottle or 0} → €{new_bottle}"
                )
            
            if 'sell_price_glass' in item_data:
                old_glass = stock_item.menu_price
                new_glass = Decimal(str(item_data['sell_price_glass']))
                stock_item.menu_price = new_glass
                updated_fields.append(
                    f"menu_price (glass): {old_glass or 0} → €{new_glass}"
                )
        
        # Save if any fields were updated
        if updated_fields:
            stock_item.save()
            print(f"✅ {sku} - {stock_item.name}")
            for field_update in updated_fields:
                print(f"   {field_update}")
            updated_count += 1
        else:
            print(f"⚠️  {sku} - No price data in JSON")
    
    except Exception as e:
        print(f"❌ Error updating {sku}: {str(e)}")
        error_count += 1

print()
print("=" * 80)
print("UPDATE SUMMARY")
print("=" * 80)
print(f"Total items in JSON:        {len(json_data)}")
print(f"Successfully updated:       {updated_count} ✅")
print(f"Not found in database:      {not_found_count} ❌")
print(f"Errors:                     {error_count} ⚠️")
print()

if updated_count > 0:
    print("🎉 Menu prices have been updated successfully!")
    print()
    print("You can verify by running: python check_menu_prices.py")
else:
    print("⚠️  No items were updated. Please check the data.")

print("=" * 80)
