"""
Update beer product names - remove acronyms, abbreviations, and numbers
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

def update_beer_names():
    """Update beer names to remove acronyms, abbreviations, and numbers"""
    
    updates = []
    
    # Bottled Beer updates
    bottled_updates = [
        ('B11', 'KBC Blonde Bottle', 'Killarney Blonde Bottle'),
        ('B14', 'KBC Full Circle Bottle', 'Killarney Full Circle Bottle'),
        ('B2308', 'Peroni GF Bottle', 'Peroni Gluten Free Bottle'),
    ]
    
    # Draught Beer updates - remove (30Lt), (50Lt), (20Lt) and expand acronyms
    draught_updates = [
        ('D0007', 'Beamish Draught', 'Beamish Draught'),  # Already good
        ('D1004', 'Coors Draught', 'Coors Draught'),  # Remove (30Lt)
        ('D1258', 'Coors Draught', 'Coors Draught'),  # Remove (50Lt)
        ('D0005', 'Guinness Draught', 'Guinness Draught'),  # Already good
        ('D0004', 'Heineken Draught', 'Heineken Draught'),  # Remove (30Lt)
        ('D0030', 'Heineken Draught', 'Heineken Draught'),  # Remove (50Lt)
        ('D2133', 'Heineken Zero Draught', 'Heineken Zero Draught'),  # Remove (20Lt)
        ('D0012', 'Killarney Blonde Draught', 'Killarney Blonde Draught'),  # Already good
        ('D0011', 'Lagunitas India Pale Ale Draught', 'Lagunitas India Pale Ale Draught'),  # Expand IPA
        ('D2354', 'Moretti Draught', 'Moretti Draught'),  # Already good
        ('D1003', 'Murphys Draught', 'Murphys Draught'),  # Already good
        ('D0008', 'Murphys Red Draught', 'Murphys Red Draught'),  # Already good
        ('D1022', 'Orchards Draught', 'Orchards Draught'),  # Already good
        ('D0006', 'Orchard Thieves Wild Orchard Draught', 'Orchard Thieves Wild Orchard Draught'),  # Expand OT
    ]
    
    all_updates = bottled_updates + draught_updates
    
    print("=" * 100)
    print("BEER NAME UPDATES - Remove Acronyms, Abbreviations, and Numbers")
    print("=" * 100)
    print(f"\n{'SKU':<15} {'OLD NAME':<50} {'NEW NAME':<50}")
    print("-" * 100)
    
    for sku, old_name, new_name in all_updates:
        try:
            item = StockItem.objects.get(sku=sku)
            current_name = item.name
            
            # Check if update is needed
            if current_name != new_name:
                updates.append({
                    'item': item,
                    'old_name': current_name,
                    'new_name': new_name,
                    'sku': sku
                })
                print(f"{sku:<15} {current_name:<50} {new_name:<50}")
            else:
                print(f"✓ {sku:<15} {current_name:<50} (already correct)")
        except StockItem.DoesNotExist:
            print(f"❌ {sku}: Item not found in database")
    
    print("\n" + "=" * 100)
    print(f"Items needing updates: {len(updates)}")
    print(f"Items already correct: {len(all_updates) - len(updates)}")
    print("=" * 100)
    
    if not updates:
        print("\n✅ No updates needed - all names are already correct!")
        return
    
    # Confirm before updating
    response = input("\nProceed with updates? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Cancelled - no changes made")
        return
    
    # Apply updates
    print("\n" + "=" * 100)
    print("APPLYING UPDATES...")
    print("=" * 100)
    
    for update in updates:
        update['item'].name = update['new_name']
        update['item'].save()
        print(f"✅ {update['sku']}: {update['old_name']} → {update['new_name']}")
    
    print("\n" + "=" * 100)
    print(f"✅ COMPLETED - Updated {len(updates)} items")
    print("=" * 100)

if __name__ == '__main__':
    update_beer_names()
