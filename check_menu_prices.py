"""
Check how many saved stock items have correct prices matching the JSON file
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

# Create lookup dict by SKU
price_lookup = {}
for item in json_data:
    sku = item['sku']
    price_lookup[sku] = {
        'menu_name': item['menu_name'],
        'sell_price_unit': Decimal(str(item.get('sell_price_unit', 0))),
        'sell_price_bottle': Decimal(str(item.get('sell_price_bottle', 0))) if item.get('sell_price_bottle') else None,
        'sell_price_glass': Decimal(str(item.get('sell_price_glass', 0))) if item.get('sell_price_glass') else None,
    }

# Get all stock items
all_items = StockItem.objects.all()
total_items = all_items.count()

# Track results
matching_skus = []
matching_prices = []
mismatched_prices = []
missing_in_db = []
extra_in_db = []

print("=" * 80)
print("MENU PRICE COMPARISON REPORT")
print("=" * 80)
print()

# Check items in database
for item in all_items:
    if item.sku in price_lookup:
        matching_skus.append(item.sku)
        json_item = price_lookup[item.sku]
        
        # Check price matching based on item type
        price_matches = False
        db_price = None
        json_price = None
        
        # For spirits (S), draught (D), bottled (B), minerals (M) - check unit price
        if item.category_id in ['S', 'D', 'B', 'M']:
            db_price = item.menu_price if item.menu_price else Decimal('0')
            json_price = json_item['sell_price_unit']
            price_matches = db_price == json_price
        
        # For wine (W) - check both bottle and glass prices if available
        elif item.category_id == 'W':
            bottle_match = True
            glass_match = True
            
            if json_item['sell_price_bottle']:
                db_bottle = item.bottle_price if item.bottle_price else Decimal('0')
                bottle_match = db_bottle == json_item['sell_price_bottle']
            
            if json_item['sell_price_glass']:
                db_glass = item.menu_price if item.menu_price else Decimal('0')
                glass_match = db_glass == json_item['sell_price_glass']
            
            price_matches = bottle_match and glass_match
            db_price = f"Bottle: {item.bottle_price or 0}, Glass: {item.menu_price or 0}"
            json_price = f"Bottle: {json_item['sell_price_bottle'] or 0}, Glass: {json_item['sell_price_glass'] or 0}"
        
        if price_matches:
            matching_prices.append({
                'sku': item.sku,
                'name': item.name,
                'price': db_price
            })
        else:
            mismatched_prices.append({
                'sku': item.sku,
                'name': item.name,
                'db_price': db_price,
                'json_price': json_price,
                'category': item.category_id
            })
    else:
        extra_in_db.append({
            'sku': item.sku,
            'name': item.name
        })

# Check for items in JSON but not in database
for sku in price_lookup.keys():
    if not all_items.filter(sku=sku).exists():
        missing_in_db.append({
            'sku': sku,
            'name': price_lookup[sku]['menu_name']
        })

# Print Summary
print(f"📊 SUMMARY")
print(f"-" * 80)
print(f"Total items in database:     {total_items}")
print(f"Total items in JSON:         {len(price_lookup)}")
print(f"SKUs found in both:          {len(matching_skus)}")
print(f"Prices matching:             {len(matching_prices)} ✅")
print(f"Prices mismatched:           {len(mismatched_prices)} ⚠️")
print(f"Items in JSON but not DB:    {len(missing_in_db)} ❌")
print(f"Items in DB but not JSON:    {len(extra_in_db)} ℹ️")
print()

# Calculate percentage
if len(matching_skus) > 0:
    match_percentage = (len(matching_prices) / len(matching_skus)) * 100
    print(f"✨ Price Match Rate: {match_percentage:.1f}%")
    print()

# Detailed Reports
if mismatched_prices:
    print("=" * 80)
    print("⚠️  PRICE MISMATCHES")
    print("=" * 80)
    for item in mismatched_prices:
        print(f"\nSKU: {item['sku']} - {item['name']} ({item['category']})")
        print(f"  DB Price:   {item['db_price']}")
        print(f"  JSON Price: {item['json_price']}")

if missing_in_db:
    print("\n" + "=" * 80)
    print("❌ ITEMS IN JSON BUT NOT IN DATABASE")
    print("=" * 80)
    for item in missing_in_db:
        print(f"  {item['sku']} - {item['name']}")

if extra_in_db:
    print("\n" + "=" * 80)
    print("ℹ️  ITEMS IN DATABASE BUT NOT IN JSON")
    print("=" * 80)
    for item in extra_in_db:
        print(f"  {item['sku']} - {item['name']}")

if matching_prices:
    print("\n" + "=" * 80)
    print(f"✅ CORRECTLY PRICED ITEMS ({len(matching_prices)} items)")
    print("=" * 80)
    for item in matching_prices[:10]:  # Show first 10
        print(f"  {item['sku']} - {item['name']}: €{item['price']}")
    if len(matching_prices) > 10:
        print(f"  ... and {len(matching_prices) - 10} more items")

print("\n" + "=" * 80)
print("END OF REPORT")
print("=" * 80)
