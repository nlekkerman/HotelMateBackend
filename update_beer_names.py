"""
Update beer names:
1. Draught (D): Remove keg volume numbers (20, 30, 50) and add "Draught"
2. Bottled (B): Add "Bottle" (or keep "Pint Bottle" if already there)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

def update_beer_names():
    """Update draught and bottled beer names"""
    import re
    
    print("=" * 120)
    print("UPDATING BEER NAMES")
    print("=" * 120)
    
    # Get all draught beers
    draught_beers = StockItem.objects.filter(
        category_id='D'
    ).order_by('name')
    
    print(f"\n{'='*120}")
    print(f"DRAUGHT BEERS (Category D) - {draught_beers.count()} items")
    print(f"{'='*120}")
    print(f"{'SKU':<15} {'OLD NAME':<50} {'NEW NAME':<50}")
    print("-" * 120)
    
    draught_updates = []
    for beer in draught_beers:
        old_name = beer.name
        
        # Skip test items
        if 'test' in old_name.lower():
            continue
        
        new_name = old_name
        
        # Remove keg volume numbers (20, 30, 50) from the beginning
        if new_name.startswith('20 '):
            new_name = new_name[3:]  # Remove "20 "
        elif new_name.startswith('30 '):
            new_name = new_name[3:]  # Remove "30 "
        elif new_name.startswith('50 '):
            new_name = new_name[3:]  # Remove "50 "
        
        # Replace 0.0% with Zero
        new_name = re.sub(r'0\.0%?', 'Zero', new_name, flags=re.IGNORECASE)
        # Fix spelling: Blond → Blonde
        new_name = re.sub(r'\bBlond\b', 'Blonde', new_name)
        # Remove periods
        new_name = new_name.replace('.', '')
        
        # Add "Draught" if not already present
        if 'Draught' not in new_name and 'draught' not in new_name.lower():
            new_name = f"{new_name} Draught"
        
        if old_name != new_name:
            draught_updates.append({
                'item': beer,
                'old_name': old_name,
                'new_name': new_name
            })
            print(f"{beer.sku:<15} {old_name:<50} {new_name:<50}")
    
    # Get all bottled beers
    bottled_beers = StockItem.objects.filter(
        category_id='B'
    ).order_by('name')
    
    print(f"\n{'='*120}")
    print(f"BOTTLED BEERS (Category B) - {bottled_beers.count()} items")
    print(f"{'='*120}")
    print(f"{'SKU':<15} {'OLD NAME':<50} {'NEW NAME':<50}")
    print("-" * 120)
    
    bottled_updates = []
    for beer in bottled_beers:
        old_name = beer.name
        
        # Skip test items
        if 'test' in old_name.lower():
            continue
        
        new_name = old_name
        
        # Check if it's a pint bottle
        is_pint = ('Pt Btl' in new_name or 'Pint Btl' in new_name or
                   'Pint Bottle' in new_name)
        
        if is_pint:
            # Extract brand name before the size info
            for term in ['Pt Btl', 'Pint Btl', 'Pint Bottle']:
                if term in new_name:
                    new_name = new_name.split(term)[0].strip()
                    break
            # Replace 0.0% with Zero
            new_name = re.sub(r'0\.0%?', 'Zero', new_name, flags=re.IGNORECASE)
            # Remove all numbers and size units (but not after replacing 0.0)
            new_name = re.sub(r'\s*\d+\s*(ml|cl|ML|CL|L)?\s*', ' ', new_name)
            new_name = ' '.join(new_name.split())
            new_name = f"{new_name} Pint Bottle"
        else:
            # Regular bottle
            # Replace 0.0% with Zero first
            new_name = re.sub(r'0\.0%?', 'Zero', new_name, flags=re.IGNORECASE)
            # Fix spelling: Blond → Blonde
            new_name = re.sub(r'\bBlond\b', 'Blonde', new_name)
            # Remove periods
            new_name = new_name.replace('.', '')
            # Remove patterns like "330ml", "33cl", "275ml", "500ML"
            new_name = re.sub(r'\s*\d+\s*(ml|cl|ML|CL|L)?\s*', ' ', new_name)
            # Remove standalone numbers
            new_name = re.sub(r'\s+\d+\s+', ' ', new_name)
            # Remove "Btl", "Case", "L/N" if present
            new_name = re.sub(r'\s*Btl\s*', ' ', new_name)
            new_name = re.sub(r'\s*Case\s*', ' ', new_name, flags=re.IGNORECASE)
            new_name = re.sub(r'\s*L/N\s*', ' ', new_name)
            # Clean up extra spaces
            new_name = ' '.join(new_name.split())
            # Add "Bottle" if not already present
            if 'Bottle' not in new_name and 'bottle' not in new_name.lower():
                new_name = f"{new_name} Bottle"
        
        if old_name != new_name:
            bottled_updates.append({
                'item': beer,
                'old_name': old_name,
                'new_name': new_name
            })
            print(f"{beer.sku:<15} {old_name:<50} {new_name:<50}")
    
    # Summary
    print("\n" + "=" * 120)
    print("SUMMARY")
    print("=" * 120)
    print(f"Draught beers to update: {len(draught_updates)}")
    print(f"Bottled beers to update: {len(bottled_updates)}")
    print(f"Total updates: {len(draught_updates) + len(bottled_updates)}")
    
    if not draught_updates and not bottled_updates:
        print("\n✅ No updates needed - all beer names are already correct!")
        return
    
    # Confirm
    print("\n" + "=" * 120)
    response = input("Proceed with updates? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Cancelled - no changes made")
        return
    
    # Apply updates
    print("\n" + "=" * 120)
    print("APPLYING UPDATES...")
    print("=" * 120)
    
    updated_count = 0
    
    for update in draught_updates:
        update['item'].name = update['new_name']
        update['item'].save()
        updated_count += 1
        print(f"✅ {update['item'].sku}: {update['old_name']} → {update['new_name']}")
    
    for update in bottled_updates:
        update['item'].name = update['new_name']
        update['item'].save()
        updated_count += 1
        print(f"✅ {update['item'].sku}: {update['old_name']} → {update['new_name']}")
    
    print("\n" + "=" * 120)
    print(f"✅ COMPLETED - Updated {updated_count} beer names")
    print("=" * 120)


if __name__ == '__main__':
    update_beer_names()
