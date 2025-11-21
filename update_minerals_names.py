"""
Update Minerals & Syrups product names - remove "Split" prefix and clean up
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem


def update_minerals_names():
    """Update minerals/syrups names - remove Split prefix and clean up"""
    
    updates = []
    
    # Remove "Split" prefix and clean up names
    minerals_updates = [
        # Split removals - just remove "Split " prefix
        ('M0050', 'Split 7up', 'Seven Up'),
        ('M0003', 'Split 7UP Diet', 'Seven Up Diet'),
        ('M0040', 'Split Coke', 'Coca Cola'),
        ('M0013', 'Split Coke 330ML', 'Coca Cola'),
        ('M2105', 'Split Coke Diet', 'Coca Cola Diet'),
        ('M0004', 'Split Fanta Lemon', 'Fanta Lemon'),
        ('M0034', 'Split Fanta Orange', 'Fanta Orange'),
        ('M0070', 'Split Friuce Juices', 'Friuce Juices'),
        ('M0135', 'Split Lucozade', 'Lucozade'),
        ('M0315', 'Split Pepsi', 'Pepsi'),
        ('M0016', 'Split Poachers Ginger Beer', 'Poachers Ginger Beer'),
        ('M0255', 'Split Sch', 'Schweppes'),
        ('M0122', 'Split Sch Elderflower', 'Schweppes Elderflower'),
        ('M0200', 'Split Sprite/Zero', 'Sprite Zero'),
        ('M0312', 'Splits Britvic Juices', 'Britvic Juices'),
        
        # Baby SCH expansion
        ('M0195', 'Baby SCH Mims', 'Baby Schweppes Miniatures'),
        
        # Remove size info from Monin products
        ('M0320', 'Mixer Lemon Juice 700ML', 'Mixer Lemon Juice'),
        ('M0009', 'Mixer Lime Juice 700ML', 'Mixer Lime Juice'),
        ('M3', 'Monin Agave Syrup 700ml', 'Monin Agave Syrup'),
        ('M0006', 'Monin Chocolate Cookie LTR', 'Monin Chocolate Cookie'),
        ('M13', 'Monin Coconut Syrup 700ML', 'Monin Coconut Syrup'),
        ('M04', 'Monin Elderflower Syrup 700ML', 'Monin Elderflower Syrup'),
        ('M0014', 'Monin Passionfruit Puree Ltr', 'Monin Passionfruit Puree'),
        ('M03', 'Monin Passionfruit Syrup 700ML', 'Monin Passionfruit Syrup'),
        ('M05', 'Monin Pink Grapefruit 700ML', 'Monin Pink Grapefruit'),
        ('M06', 'Monin Puree Coconut LTR', 'Monin Coconut Puree'),
        ('M1', 'Monin Strawberry Puree Ltr', 'Monin Strawberry Puree'),
        ('M5', 'Monin Strawberry Syrup 700ml', 'Monin Strawberry Syrup'),
        ('M9', 'Monin Vanilla Syrup Ltr', 'Monin Vanilla Syrup'),
        ('M02', 'Monin Watermelon Syrup 700ML', 'Monin Watermelon Syrup'),
        
        # Remove size from other items
        ('M0123', 'Riverrock 750ml', 'Riverrock Water'),
        ('M25', 'Splash Cola 18LTR', 'Splash Cola Bag in Box'),
        ('M24', 'Splash Energy18LTR', 'Splash Energy Bag in Box'),
        ('M23', 'Splash White18LTR', 'Splash White Lemonade Bag in Box'),
    ]
    
    print("=" * 100)
    print("MINERALS & SYRUPS NAME UPDATES - Remove 'Split' and Size Info")
    print("=" * 100)
    print(f"\n{'SKU':<15} {'OLD NAME':<50} {'NEW NAME':<50}")
    print("-" * 100)
    
    for sku, old_name, new_name in minerals_updates:
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
    print(f"Items already correct: {len(minerals_updates) - len(updates)}")
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
    update_minerals_names()
