"""
Quick restore script - Run with: python manage.py shell < quick_restore_from_september.py
Or copy-paste into Django shell
"""
import json
from decimal import Decimal
from stock_tracker.models import StockItem
from hotel.models import Hotel

# Load backup data
with open('september_closing_stock.json', 'r') as f:
    backup_data = json.load(f)

hotel = Hotel.objects.first()
print(f"Loaded {len(backup_data)} items from backup")

restored_count = 0
skipped_count = 0
not_found_count = 0

for sku, data in backup_data.items():
    try:
        item = StockItem.objects.get(hotel=hotel, sku=sku)
        
        # Check if zeroed
        is_zeroed = (
            item.current_full_units == Decimal('0') and 
            item.current_partial_units == Decimal('0')
        )
        
        if is_zeroed:
            item.current_full_units = Decimal(data['counted_full_units'])
            item.current_partial_units = Decimal(data['counted_partial_units'])
            item.save()
            restored_count += 1
            print(f"✓ {sku}: {item.current_full_units} full, {item.current_partial_units} partial")
        else:
            skipped_count += 1
            
    except StockItem.DoesNotExist:
        not_found_count += 1
        print(f"⚠ Not found: {sku}")

print(f"\n{'='*80}")
print(f"COMPLETE: Restored {restored_count} | Skipped {skipped_count} | Not found {not_found_count}")
print(f"{'='*80}")
