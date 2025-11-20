"""
Fix draught beers that still have 00% - change to Zero
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
import re

# Get draught beers with 00%
draught_beers = StockItem.objects.filter(category_id='D')

print("=" * 80)
print("FIXING DRAUGHT BEERS WITH 00%")
print("=" * 80)

updated = []
for beer in draught_beers:
    old_name = beer.name
    new_name = old_name
    
    # Replace 00% with Zero
    if '00%' in new_name or '0.0%' in new_name:
        new_name = re.sub(r'00%', 'Zero', new_name)
        new_name = re.sub(r'0\.0%', 'Zero', new_name)
        
        if old_name != new_name:
            updated.append({
                'sku': beer.sku,
                'old': old_name,
                'new': new_name,
                'item': beer
            })
            print(f"{beer.sku}: {old_name} → {new_name}")

if not updated:
    print("\n✅ No draught beers need updating!")
else:
    print(f"\n{len(updated)} beers to update")
    response = input("\nProceed? (yes/no): ").strip().lower()
    
    if response == 'yes':
        for item in updated:
            item['item'].name = item['new']
            item['item'].save()
            print(f"✅ Updated: {item['sku']}")
        print(f"\n✅ Updated {len(updated)} beers")
    else:
        print("\n❌ Cancelled")
